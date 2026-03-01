from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Callable, Iterable, Iterator

import pandas as pd
import requests


SDA_URL = "https://sdmdataaccess.sc.egov.usda.gov/Tabular/post.rest"


def norm_landform(value) -> str:
  if value is None:
    return "unknown"
  s = str(value).strip().lower()
  s = re.sub(r"\s+", " ", s)
  return s if s else "unknown"


def sda_post(sql: str, *, timeout: int = 90, url: str = SDA_URL) -> dict:
    payload = {"query": sql, "format": "JSON"}
    response = requests.post(
        url,
        data=json.dumps(payload),
        headers={"Content-Type": "application/json"},
        timeout=timeout,
    )
    response.raise_for_status()

    txt = response.text or ""
    if len(txt.strip()) == 0:
        raise RuntimeError(
            "SDA returned an empty response body (timeout/limits). Try again or simplify query."
        )
    if txt.lstrip().startswith("<"):
        raise RuntimeError(
            f"SDA returned non-JSON (starts with '<'). First 400 chars:\n{txt[:400]}"
        )

    return response.json()


def sda_to_df(resp: dict) -> pd.DataFrame:
    table_key = next((k for k, v in resp.items() if isinstance(v, list)), None)
    if table_key is None:
        raise RuntimeError(f"Unexpected SDA JSON keys: {list(resp.keys())}")
    return pd.DataFrame(resp[table_key])


def chunked(seq: list[str], size: int) -> Iterator[list[str]]:
    if size <= 0:
        raise ValueError("size must be > 0")
    for i in range(0, len(seq), size):
        yield seq[i : i + size]


def run_batched(
    mukeys: list[str],
    *,
    batch_size: int,
    fetch_batch: Callable[[list[str]], pd.DataFrame],
) -> pd.DataFrame:
    parts: list[pd.DataFrame] = []
    for batch in chunked(mukeys, batch_size):
        parts.append(fetch_batch(batch))
    if len(parts) == 0:
        return pd.DataFrame()
    return pd.concat(parts, ignore_index=True)


def _in_list(mukeys: list[str]) -> str:
    return ",".join(f"'{m}'" for m in mukeys)


def fetch_landforms_df(mukeys: list[str], *, batch_size: int = 150) -> pd.DataFrame:
    def fetch_batch(batch_mukeys: list[str]) -> pd.DataFrame:
        in_list = _in_list(batch_mukeys)
        sql = f"""
        WITH dom AS (
          SELECT
            c.mukey, c.cokey, c.compname, c.comppct_r,
            ROW_NUMBER() OVER (PARTITION BY c.mukey ORDER BY c.comppct_r DESC) AS rn
          FROM component c
          WHERE c.mukey IN ({in_list})
        )
        SELECT
          m.mukey,
          l.areasymbol,
          m.musym,
          m.muname,
          d.compname,
          d.comppct_r,
          cg.geomfname AS landform
        FROM mapunit m
        JOIN legend l ON l.lkey = m.lkey
        JOIN dom d ON d.mukey = m.mukey AND d.rn = 1
        LEFT JOIN cogeomordesc cg
          ON cg.cokey = d.cokey
         AND cg.geomftname = 'Landform'
         AND cg.rvindicator = 'yes'
        ORDER BY m.mukey;
        """
        resp = sda_post(sql)
        dfb = sda_to_df(resp).rename(
            columns={
                0: "mukey",
                1: "areasymbol",
                2: "musym",
                3: "muname",
                4: "compname",
                5: "comppct_r",
                6: "landform",
            }
        )
        dfb["mukey"] = dfb["mukey"].astype(str)
        return dfb

    return run_batched(mukeys, batch_size=batch_size, fetch_batch=fetch_batch)


def fetch_landforms_texture_df(mukeys: list[str], *, batch_size: int = 150) -> pd.DataFrame:
    def fetch_batch(batch_mukeys: list[str]) -> pd.DataFrame:
        in_list = _in_list(batch_mukeys)

        sql = f"""
        WITH dom AS (
          SELECT
            c.mukey, c.cokey, c.compname, c.comppct_r,
            ROW_NUMBER() OVER (PARTITION BY c.mukey ORDER BY c.comppct_r DESC) AS rn
          FROM component c
          WHERE c.mukey IN ({in_list})
        ),
        surf_hz AS (
          -- pick the topmost horizon for the dominant component
          SELECT
            ch.cokey, ch.chkey, ch.hzdept_r, ch.hzdepb_r,
            ch.sandtotal_r, ch.silttotal_r, ch.claytotal_r,
            ROW_NUMBER() OVER (
              PARTITION BY ch.cokey
              ORDER BY
                CASE WHEN ch.hzdept_r = 0 THEN 0 ELSE 1 END,
                ch.hzdept_r
            ) AS rn
          FROM chorizon ch
          JOIN dom d ON d.cokey = ch.cokey AND d.rn = 1
          WHERE ch.hzdept_r IS NOT NULL
            AND ch.hzdepb_r IS NOT NULL
            AND ch.hzdepb_r > 0
        ),
        tex AS (
          -- representative texture class for that surface horizon
          SELECT
            t0.chkey,
            t0.texcl
          FROM (
            SELECT
              chtg.chkey,
              ct.texcl,
              ROW_NUMBER() OVER (
                PARTITION BY chtg.chkey
                ORDER BY
                  CASE WHEN chtg.rvindicator = 'yes' THEN 0 ELSE 1 END,
                  ct.texcl
              ) AS rn
            FROM chtexturegrp chtg
            JOIN chtexture ct ON ct.chtgkey = chtg.chtgkey
          ) t0
          WHERE t0.rn = 1
        )
        SELECT
          m.mukey,
          l.areasymbol,
          m.musym,
          m.muname,
          d.compname,
          d.comppct_r,
          cg.geomfname AS landform,
          hz.sandtotal_r,
          hz.silttotal_r,
          hz.claytotal_r,
          tx.texcl
        FROM mapunit m
        JOIN legend l ON l.lkey = m.lkey
        JOIN dom d ON d.mukey = m.mukey AND d.rn = 1
        LEFT JOIN cogeomordesc cg
          ON cg.cokey = d.cokey
         AND cg.geomftname = 'Landform'
         AND cg.rvindicator = 'yes'
        LEFT JOIN surf_hz hz
          ON hz.cokey = d.cokey AND hz.rn = 1
        LEFT JOIN tex tx
          ON tx.chkey = hz.chkey
        ORDER BY m.mukey;
        """

        resp = sda_post(sql)
        dfb = sda_to_df(resp).rename(
            columns={
                0: "mukey",
                1: "areasymbol",
                2: "musym",
                3: "muname",
                4: "compname",
                5: "comppct_r",
                6: "landform",
                7: "sandtotal_r",
                8: "silttotal_r",
                9: "claytotal_r",
                10: "texcl",
            }
        )
        dfb["mukey"] = dfb["mukey"].astype(str)
        return dfb

    return run_batched(mukeys, batch_size=batch_size, fetch_batch=fetch_batch)
