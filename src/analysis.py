"""
analysis.py
-----------
Statistical analysis helpers for the berm-outcomes project.

Sections
--------
1. Outcome analysis        – chi-square, pairwise z/Fisher, FDR, analyze_outcome
2. Predictor ranking (GLM) – pseudo-R², Tjur R², LRT, CV AUC via logistic regression
3. Random-forest fitting   – fit_rf_binary with permutation importance
4. SI table formatting     – PRETTY_LABELS, _clean_predictor_name, _format_ranking_for_si
"""

import numpy as np
import pandas as pd
from itertools import combinations
from scipy.stats import chi2_contingency, fisher_exact, norm, chi2

from sklearn.model_selection import (
    StratifiedKFold, train_test_split, cross_validate,
)
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.cross_decomposition import PLSRegression
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    roc_auc_score, confusion_matrix, matthews_corrcoef,
    brier_score_loss, log_loss, average_precision_score,
    accuracy_score, balanced_accuracy_score, precision_score,
    recall_score, f1_score
)
from sklearn.inspection import permutation_importance

import statsmodels.api as sm


# ============================================================================
# 1. Outcome analysis
# ============================================================================

def _auto_positive(series, outcome_name):
    """Guess the 'positive' class label for a binary outcome series."""
    # Import here to avoid circular reference; constants module is lightweight
    try:
        from src.constants import LBL_EFFECTIVE
    except ImportError:
        LBL_EFFECTIVE = "Effective"

    v = pd.Series(series.dropna().unique())
    if series.dtype == bool or set(v) <= {True, False}:
        return True
    if set(v) <= {0, 1}:
        return 1
    if outcome_name.lower().startswith("effect"):
        for cand in [LBL_EFFECTIVE, "Effective", "effective", "Yes", "yes", "Positive"]:
            if cand in set(v):
                return cand
    if outcome_name.lower().startswith("intact"):
        for cand in ["Intact", "intact", "Yes", "yes", "Positive"]:
            if cand in set(v):
                return cand
    return v.iloc[0]


def chi2_with_cramers_v(ct: pd.DataFrame):
    """Chi-square test plus Cramér's V effect size."""
    chi2_stat, p, dof, expected = chi2_contingency(ct)
    n = ct.values.sum()
    r, k = ct.shape
    V = np.sqrt(chi2_stat / (n * (min(r, k) - 1)))
    return chi2_stat, p, dof, V, expected


def _two_prop_z(count1, n1, count2, n2):
    """Two-proportion z-test. Returns (z, p, difference)."""
    p1, p2 = count1 / n1, count2 / n2
    p_pool = (count1 + count2) / (n1 + n2)
    se = np.sqrt(p_pool * (1 - p_pool) * (1 / n1 + 1 / n2))
    if se == 0:
        return 0.0, 1.0, p1 - p2
    z = (p1 - p2) / se
    p = 2 * norm.sf(abs(z))
    return z, p, p1 - p2


def _bh_adjust(pvals):
    """Benjamini–Hochberg FDR correction. Returns q-values same length as pvals."""
    pvals = np.asarray(pvals, dtype=float)
    m = len(pvals)
    order = np.argsort(pvals)
    ranked = pvals[order]
    q = ranked * m / (np.arange(1, m + 1))
    q = np.minimum.accumulate(q[::-1])[::-1]
    q = np.minimum(q, 1.0)
    out = np.empty_like(q)
    out[order.argsort()] = q
    return out


def pairwise_by_group(df, group_col, outcome_col, positive=None, fdr_alpha=0.05):
    """
    All pairwise comparisons between groups on a binary outcome.

    Returns
    -------
    (results_df, proportions_series)
    """
    d = df[[group_col, outcome_col]].dropna()
    if positive is None:
        positive = _auto_positive(d[outcome_col], outcome_col)
    groups = d[group_col].value_counts().index.tolist()
    pos = d.groupby(group_col)[outcome_col].apply(lambda x: (x == positive).sum())
    n = d.groupby(group_col)[outcome_col].size()
    props = (pos / n).rename("proportion").sort_values(ascending=False)

    pairs, p_raw, pinfo = [], [], []
    for a, b in combinations(groups, 2):
        table = np.array([
            [pos[a], n[a] - pos[a]],
            [pos[b], n[b] - pos[b]],
        ])
        use_fisher = (table < 5).any()
        if use_fisher:
            _, p = fisher_exact(table, alternative="two-sided")
            diff = pos[a] / n[a] - pos[b] / n[b]
            test = "Fisher"
        else:
            _, p, diff = _two_prop_z(pos[a], n[a], pos[b], n[b])
            test = "z"
        pairs.append((a, b))
        p_raw.append(p)
        pinfo.append((diff, test))

    q = _bh_adjust(p_raw) if p_raw else []
    res = pd.DataFrame({
        "group_a": [a for a, _ in pairs],
        "group_b": [b for _, b in pairs],
        "prop_a": [pos[a] / n[a] for a, _ in pairs],
        "prop_b": [pos[b] / n[b] for _, b in pairs],
        "diff_a_minus_b": [di for di, _ in pinfo],
        "test": [te for _, te in pinfo],
        "p_raw": p_raw,
        "q_fdr": q,
    }).assign(significant=lambda d: d["q_fdr"] < fdr_alpha).sort_values("q_fdr")
    return res, props


def analyze_outcome(df, group_col, outcome_col, positive=None, fdr_alpha=0.05):
    """
    Chi-square global test + pairwise FDR-adjusted comparisons for one outcome.

    Returns
    -------
    dict with keys: global, pairwise, proportions
    """
    ct = pd.crosstab(df[group_col], df[outcome_col])
    chi2_stat, p, dof, V, expected = chi2_with_cramers_v(ct)
    res_pairs, props = pairwise_by_group(df, group_col, outcome_col, positive, fdr_alpha)
    return {
        "global": {"chi2": chi2_stat, "p_value": p, "dof": dof, "cramers_v": V},
        "pairwise": res_pairs,
        "proportions": props,
    }


# ============================================================================
# 2. Predictor ranking (GLM)
# ============================================================================

def _coerce_binary(y):
    """Return y as 0/1 numeric; drop anything else as NaN."""
    y = y.copy()
    if y.dropna().isin([0, 1]).all():
        return y.astype(float)
    if y.dropna().isin([True, False]).all():
        return y.astype(int).astype(float)
    if y.dtype == object:
        m = {
            "0": 0, "1": 1,
            "false": 0, "true": 1,
            "no": 0, "yes": 1,
            "ineffective": 0, "effective": 1,
            "no vegetation response": 0, "vegetation response": 1,
            "intact": 1, "degraded": 0,
        }
        yy = y.astype(str).str.strip().str.lower().map(m)
        return yy.astype(float)
    return pd.to_numeric(y, errors="coerce")


def _collapse_rare_levels(s, min_level_n=5, max_levels=40):
    """Collapse rare categories into 'Other'. If still too many levels, return None."""
    s = s.astype("object").copy()
    vc = s.value_counts(dropna=False)
    rare = vc[vc < min_level_n].index
    s = s.where(~s.isin(rare), other="Other")
    if s.nunique(dropna=True) > max_levels:
        return None
    return s


def _is_categorical(series, cat_unique_threshold=8):
    """Return True if series should be treated as categorical."""
    return (
        series.dtype == object
        or str(series.dtype).startswith("category")
        or series.nunique(dropna=True) <= cat_unique_threshold
    )


def _fit_glm_pseudoR2(
    df, y, x,
    treat_as=None,
    cat_unique_threshold=8,
    min_level_n=5,
    max_levels=40,
):
    """
    Fit a binomial GLM and return McFadden R², Tjur R², LRT p-value, and AIC.

    Returns None if the outcome is not binary in this subset, or a dict with
    skip=True if the fit is not possible.
    """
    sub = df[[y, x]].dropna().copy()
    sub[y] = _coerce_binary(sub[y])
    sub = sub.dropna(subset=[y])

    if sub[y].nunique() != 2:
        return None

    x_series = sub[x]
    is_cat = (treat_as == "categorical") or (
        _is_categorical(x_series, cat_unique_threshold) and treat_as != "numeric"
    )

    if is_cat:
        collapsed = _collapse_rare_levels(x_series, min_level_n=min_level_n, max_levels=max_levels)
        if collapsed is None:
            return {"skip": True, "reason": f"too many levels (> {max_levels}) after collapsing rares"}
        sub[x] = collapsed
        rhs = f'C(Q("{x}"))'
        n_levels = sub[x].nunique(dropna=True)
    else:
        sub[x] = pd.to_numeric(sub[x], errors="coerce")
        sub = sub.dropna(subset=[x])
        rhs = f'Q("{x}")'
        n_levels = np.nan

    f_null = f'Q("{y}") ~ 1'
    f_mod = f'Q("{y}") ~ {rhs}'

    try:
        null = sm.GLM.from_formula(f_null, data=sub, family=sm.families.Binomial()).fit()
        mod = sm.GLM.from_formula(f_mod, data=sub, family=sm.families.Binomial()).fit()
    except Exception as e:
        return {"skip": True, "reason": f"fit failed: {e}"}

    ll_null = null.llf
    ll_mod = mod.llf

    mcfadden_r2 = 1.0 - (ll_mod / ll_null) if ll_null != 0 else np.nan

    lr = 2.0 * (ll_mod - ll_null)
    df_diff = int(round(mod.df_model - null.df_model))
    p_lrt = chi2.sf(lr, df_diff) if df_diff > 0 else np.nan

    p_hat = mod.predict(sub)
    tjur_r2 = float(p_hat[sub[y] == 1].mean() - p_hat[sub[y] == 0].mean())

    return {
        "predictor": x,
        "type": "categorical" if is_cat else "numeric",
        "n": int(len(sub)),
        "n_levels": (int(n_levels) if is_cat else np.nan),
        "mcfadden_r2": float(mcfadden_r2),
        "tjur_r2": float(tjur_r2),
        "lrt_p": float(p_lrt),
        "aic": float(mod.aic),
        "df_model": float(mod.df_model),
        "skip": False,
    }


def _cv_auc(
    df, y, x,
    treat_as=None,
    cat_unique_threshold=8,
    min_level_n=5,
    max_levels=40,
    n_splits=5,
    random_state=0,
):
    """Cross-validated AUC via logistic regression."""
    sub = df[[y, x]].dropna().copy()
    sub[y] = _coerce_binary(sub[y])
    sub = sub.dropna(subset=[y])

    if sub[y].nunique() != 2:
        return np.nan

    x_series = sub[x]
    is_cat = (treat_as == "categorical") or (
        _is_categorical(x_series, cat_unique_threshold) and treat_as != "numeric"
    )

    if is_cat:
        collapsed = _collapse_rare_levels(x_series, min_level_n=min_level_n, max_levels=max_levels)
        if collapsed is None:
            return np.nan
        sub[x] = collapsed
        pre = ColumnTransformer(
            transformers=[("cat", OneHotEncoder(handle_unknown="ignore"), [x])],
            remainder="drop",
        )
    else:
        sub[x] = pd.to_numeric(sub[x], errors="coerce")
        sub = sub.dropna(subset=[x])
        pre = ColumnTransformer(
            transformers=[("num", StandardScaler(), [x])],
            remainder="drop",
        )

    X = sub[[x]]
    yv = sub[y].astype(int).values

    clf = Pipeline(steps=[
        ("pre", pre),
        ("lr", LogisticRegression(max_iter=2000, solver="lbfgs")),
    ])

    cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=random_state)
    aucs = []
    for tr, te in cv.split(X, yv):
        clf.fit(X.iloc[tr], yv[tr])
        p = clf.predict_proba(X.iloc[te])[:, 1]
        aucs.append(roc_auc_score(yv[te], p))
    return float(np.mean(aucs))


def rank_predictors(
    df,
    y="Effective",
    predictors=None,
    treat_as=None,
    cat_unique_threshold=8,
    min_level_n=5,
    max_levels=40,
    cv_splits=5,
    random_state=0,
):
    """
    Rank predictors by GLM pseudo-R² (and optionally CV AUC).

    Parameters
    ----------
    df : pd.DataFrame
    y : str
        Binary outcome column name.
    predictors : list[str]
        Columns to evaluate.
    treat_as : dict, optional
        Override variable type per predictor: {"col": "categorical"|"numeric"}.

    Returns
    -------
    pd.DataFrame sorted by cv_auc (descending), then mcfadden_r2.
    """
    if predictors is None:
        raise ValueError("predictors must be a list of column names")
    rows = []
    for x in predictors:
        ta = None if treat_as is None else treat_as.get(x, None)
        r = _fit_glm_pseudoR2(
            df, y, x, treat_as=ta,
            cat_unique_threshold=cat_unique_threshold,
            min_level_n=min_level_n,
            max_levels=max_levels,
        )
        if r is None:
            continue
        if r.get("skip"):
            rows.append({"predictor": x, "skip": True, "reason": r.get("reason", "")})
            continue
        r["cv_auc"] = _cv_auc(
            df, y, x, treat_as=ta,
            cat_unique_threshold=cat_unique_threshold,
            min_level_n=min_level_n,
            max_levels=max_levels,
            n_splits=cv_splits,
            random_state=random_state,
        )
        rows.append(r)

    out = pd.DataFrame(rows)
    if "cv_auc" in out.columns:
        out = out.sort_values(["skip", "cv_auc", "mcfadden_r2"], ascending=[True, False, False])
    else:
        out = out.sort_values(["skip", "mcfadden_r2"], ascending=[True, False])
    return out


def prepare_pls_inputs(
    df,
    num_predictors,
    cat_predictors,
    target_mode="intact",
    top_n_textures=3,
    texture_col="Texture",
    pretty_labels=None,
):
    """
    Prepare standardized X, binary y, and display labels for PLS workflows.

    Parameters
    ----------
    df : pd.DataFrame
    num_predictors : list[str]
    cat_predictors : list[str]
    target_mode : {'intact', 'effective'}
        - 'intact' uses Intact as binary outcome.
        - 'effective' uses effect_percent > 7 as binary outcome.
    top_n_textures : int
        Keep only the top-N most frequent texture categories.
    texture_col : str
    pretty_labels : dict, optional

    Returns
    -------
    dict
        Keys: X_scaled, y, feat_labels, n, p, top_textures,
        target_label, target_note
    """
    if pretty_labels is None:
        pretty_labels = PRETTY_LABELS

    pls_cols = list(num_predictors) + list(cat_predictors)

    if target_mode == "intact":
        work = df.dropna(subset=pls_cols + ["Intact"]).copy()
        y = work["Intact"].astype(float).values
        target_label = "Condition (Intactness)"
        target_note = None
    elif target_mode == "effective":
        work = df.dropna(subset=pls_cols + ["effect_percent"]).copy()
        y = (work["effect_percent"] > 7).astype(float).values
        target_label = "Vegetation response"
        target_note = f"Effective = effect_percent > 7% ({int(y.sum())} / {len(y)} berms)"
    else:
        raise ValueError(f"Unknown target_mode: {target_mode}")

    tex_counts = work[texture_col].value_counts()
    top_textures = tex_counts.nlargest(top_n_textures).index.tolist()
    work = work[work[texture_col].isin(top_textures)].copy()

    if target_mode == "intact":
        y = work["Intact"].astype(float).values
    else:
        y = (work["effect_percent"] > 7).astype(float).values
        target_note = f"Effective = effect_percent > 7% ({int(y.sum())} / {len(y)} berms)"

    X_num = work[list(num_predictors)].astype(float)
    X_cat = pd.get_dummies(work[list(cat_predictors)], drop_first=True).astype(float)
    X = pd.concat([X_num, X_cat], axis=1).fillna(0)
    feat_names = list(X.columns)

    feat_labels = []
    for fn in feat_names:
        matched = False
        for prefix in cat_predictors:
            if fn.startswith(prefix + "_"):
                cat_val = fn[len(prefix) + 1:]
                pretty_prefix = pretty_labels.get(prefix, prefix)
                feat_labels.append(f"{pretty_prefix}: {cat_val}")
                matched = True
                break
        if not matched:
            feat_labels.append(pretty_labels.get(fn, fn))

    X_scaled = StandardScaler().fit_transform(X)
    return {
        "X_scaled": X_scaled,
        "y": y,
        "feat_labels": feat_labels,
        "n": int(X_scaled.shape[0]),
        "p": int(X_scaled.shape[1]),
        "top_textures": top_textures,
        "target_label": target_label,
        "target_note": target_note,
    }


def fit_pls_vip(X_scaled, y, n_components=2):
    """
    Fit PLS and compute VIP scores and standardized coefficients.

    Returns
    -------
    dict
        Keys: vip_sorted, coef_sorted, sort_ord, pls, n_comp
    """
    pls = PLSRegression(n_components=n_components, scale=False)
    pls.fit(X_scaled, y)

    W = pls.x_weights_
    T = pls.x_scores_
    Q = pls.y_loadings_
    p_feat = X_scaled.shape[1]

    SS = np.array([np.sum((T[:, a] * Q[0, a]) ** 2) for a in range(n_components)])
    vip = np.sqrt(p_feat * np.sum(SS * W**2, axis=1) / np.sum(SS))
    coefs = pls.coef_.ravel()

    sort_ord = np.argsort(vip)[::-1]
    return {
        "vip_sorted": vip[sort_ord],
        "coef_sorted": coefs[sort_ord],
        "sort_ord": sort_ord,
        "pls": pls,
        "n_comp": int(n_components),
    }


# ============================================================================
# 3. Random-forest fitting
# ============================================================================

# ── Scoring helpers ────────────────────────────────────────────────────────
def _specificity(y_true, y_pred):
    """Calculate specificity (True Negative Rate)."""
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    return tn / (tn + fp) if (tn + fp) else np.nan


def spec_scorer(estimator, X, y):
    """Scorer: specificity."""
    return _specificity(y, estimator.predict(X))


def mcc_scorer(estimator, X, y):
    """Scorer: Matthews Correlation Coefficient."""
    return matthews_corrcoef(y, estimator.predict(X))


def neg_brier_scorer(estimator, X, y):
    """Scorer: negative Brier score (higher is better)."""
    p = estimator.predict_proba(X)[:, 1]
    return -brier_score_loss(y, p)


def neg_logloss_scorer(estimator, X, y):
    """Scorer: negative log-loss (higher is better)."""
    p2 = estimator.predict_proba(X)  # (n,2)
    return -log_loss(y, p2, labels=[0, 1])


# ── Helper functions ──────────────────────────────────────────────────────
def _is_cat_col(series, treat_as_val=None, max_unique=20):
    """Local helper: True if series should be treated as categorical."""
    if treat_as_val == "categorical":
        return True
    if treat_as_val == "numeric":
        return False
    return series.dtype == object or series.dtype.name == "category" or series.nunique() <= max_unique


def _unique_preserve(lst):
    """Remove duplicates from a list while preserving order."""
    seen = set()
    out = []
    for x in lst:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def fit_rf_binary(
    df,
    y,
    predictors,
    treat_as=None,
    test_size=0.25,
    random_state=0,
    n_estimators=100,
    min_samples_leaf=2,
):
    """
    Fit a Random Forest classifier for a binary outcome.

    Returns
    -------
    (model, metrics_dict, permutation_importance_series)
    """
    treat_as = treat_as or {}

    sub = df[predictors + [y]].copy()
    sub[y] = _coerce_binary(sub[y])
    sub = sub.dropna(subset=[y])

    if sub[y].nunique() != 2:
        raise ValueError(
            f"{y}: need exactly 2 classes after coercion; got {sub[y].unique()}"
        )

    X = sub[predictors].copy()
    yv = sub[y].astype(int)

    cat_cols, num_cols = [], []
    for c in predictors:
        if treat_as.get(c) == "categorical":
            cat_cols.append(c)
        elif treat_as.get(c) == "numeric":
            num_cols.append(c)
        else:
            if X[c].dtype == object or str(X[c].dtype).startswith("category"):
                cat_cols.append(c)
            else:
                num_cols.append(c)

    pre = ColumnTransformer(
        transformers=[
            ("num", Pipeline([("impute", SimpleImputer(strategy="median"))]), num_cols),
            ("cat", Pipeline([
                ("impute", SimpleImputer(strategy="most_frequent")),
                ("onehot", OneHotEncoder(handle_unknown="ignore")),
            ]), cat_cols),
        ],
        remainder="drop",
    )

    rf = RandomForestClassifier(
        n_estimators=n_estimators,
        min_samples_leaf=min_samples_leaf,
        random_state=random_state,
        n_jobs=-1,
        class_weight="balanced",
    )

    model = Pipeline([("pre", pre), ("rf", rf)])

    X_tr, X_te, y_tr, y_te = train_test_split(
        X, yv, test_size=test_size, stratify=yv, random_state=random_state
    )
    model.fit(X_tr, y_tr)
    p_te = model.predict_proba(X_te)[:, 1]
    holdout_auc = roc_auc_score(y_te, p_te)

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=random_state)
    cv_scores = cross_validate(
        model, X, yv, cv=cv,
        scoring={"auc": "roc_auc", "bal_acc": "balanced_accuracy", "f1": "f1"},
        n_jobs=-1,
        return_train_score=False,
    )
    cv_summary = {
        k.replace("test_", ""): (float(np.mean(v)), float(np.std(v)))
        for k, v in cv_scores.items()
        if k.startswith("test_")
    }

    pi = permutation_importance(
        model, X_te, y_te,
        scoring="roc_auc",
        n_repeats=30,
        random_state=random_state,
        n_jobs=-1,
    )
    pi_series = pd.Series(pi.importances_mean, index=predictors).sort_values(ascending=False)  # type: ignore[union-attr]

    metrics = {
        "cv": cv_summary,
        "holdout": {"auc": float(holdout_auc)},
        "n": int(len(X)),
    }
    return model, metrics, pi_series


# ============================================================================
# 4. SI table formatting
# ============================================================================

PRETTY_LABELS = {
    "slope_200":          "Hillslope gradient",
    "slope_100":          "Hillslope gradient",
    "Shape_Leng":         "Berm length",
    "FA_30_max":          "Flow accumulation",
    "Landform":           "Landform",
    "Texture":            "Soil texture",
    "ParentMaterial":     "Parent material",
    "Soil_Development":   "Soil development",
    "Berm_Length_Class":  "Berm length class",
    "TypicalProfile":     "Typical soil profile",
    "claytotal_r":        "Clay content (r-horizon, %)",
    "sandtotal_r":        "Sand content (r-horizon, %)",
    "silttotal_r":        "Silt content (r-horizon, %)",
    "surf_claybg":        "Surface clay (%)",
    "surf_sandbg":        "Surface sand (%)",
    "surfsoc_background": "Surface organic carbon",
    "High_Clay":          "High clay",
    "channel_200m":       "Channel distance (200 m)",
    "channel_500m":       "Channel distance (500 m)",
    "channel_1000m":      "Channel distance (1000 m)",
    "effect_percent":     "Effectiveness (%)",
    "Intact":             "Intact",
}


def _clean_predictor_name(name, pretty=PRETTY_LABELS):
    """Return a pretty label; fall back to title-cased, underscore-free name."""
    if name in pretty:
        return pretty[name]
    return name.replace("_", " ").title()


def _format_ranking_for_si(ranked_df, pretty=PRETTY_LABELS, decimals=3):
    """
    Prepare a predictor-ranking DataFrame for SI export.

    - Apply pretty labels to the 'predictor' column.
    - Drop type, n, skip, reason, and other helper columns.
    - Round all numeric columns to *decimals* decimal places.
    """
    out = ranked_df.copy()

    if "predictor" in out.columns:
        out["predictor"] = out["predictor"].map(
            lambda x: _clean_predictor_name(x, pretty)
        )

    for col in ["type", "n", "skip", "reason"]:
        if col in out.columns:
            out = out.drop(columns=[col])

    num_cols = out.select_dtypes(include="number").columns
    out[num_cols] = out[num_cols].round(decimals)

    return out
