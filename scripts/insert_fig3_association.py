#!/usr/bin/env python3
"""Insert the predictor-association figure as Figure 3 in the manuscript.

Shifts all figN (N>=3) -> fig(N+1) in draft/local/main.tex (\\ref + \\label),
converts the two hard-coded "Figure 5/6" mentions to \\ref, and inserts a new
fig3 block immediately before the PCA figure block.

Only draft/local/main.tex is modified; draft/overleaf/main.tex is left as the
read-only baseline for latexdiff.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEX = ROOT / "draft" / "local" / "main.tex"

NEW_FIG3_BLOCK = r"""\begin{figure}[htb!]
\centering
\includegraphics[width=0.85\textwidth]{fig3_predictor_association.png}
\caption{Pairwise association among the six candidate predictors and the two binary outcomes (berm structural condition and vegetation response), computed on the same predictor set and top-three-texture sample as the PCA (Figure~\ref{fig:fig4}; $n = 630$ berms). Because Spearman's $\rho$ is appropriate only for ordered numeric variables, association is quantified with a measure matched to each pair type, all bounded on $[0,1]$: $|$Spearman $\rho|$ for numeric--numeric pairs, the Bergsma--Wicher bias-corrected Cram\'er's $V$ for categorical--categorical pairs, and the correlation ratio $\eta$ for mixed numeric--categorical pairs. The all-ones diagonal is masked. Landform, soil texture, and soil development are strongly inter-associated ($V = 0.89$--$0.97$), whereas both outcomes are only weakly associated with the predictors and with each other, motivating the controlled multivariate analyses below.}
\label{fig:fig3}
\end{figure}
"""


def _shift(m):
    cmd, n = m.group(1), int(m.group(2))
    return f"\\{cmd}{{fig:fig{n + 1}}}" if n >= 3 else m.group(0)


def main():
    text = TEX.read_text(encoding="utf-8")
    orig = text

    # 1. Shift \ref{fig:figN} and \label{fig:figN} for N >= 3 (atomic single pass)
    text = re.sub(r"\\(ref|label)\{fig:fig(\d+)\}", _shift, text)

    # 2. Convert the two hard-coded figure mentions to robust \ref
    #    (post-shift: controlled-predictors = fig:fig7, vegetation-response = fig:fig6)
    text = text.replace("(see Figure 6;", "(see Figure~\\ref{fig:fig7};")
    text = text.replace("(see Figure 5).", "(see Figure~\\ref{fig:fig6}).")

    # 3. Insert the new fig3 block immediately before the PCA figure block
    anchor = "\\begin{figure}[htb!]\n\\centering\n\\includegraphics[width=\\textwidth]{fig4_pca_biplot.png}"
    if anchor in text:
        text = text.replace(anchor, NEW_FIG3_BLOCK + anchor, 1)
    else:
        raise SystemExit("ERROR: could not find PCA figure block anchor")

    if text == orig:
        print("no changes")
        return
    TEX.write_text(text, encoding="utf-8")
    n_ref = len(re.findall(r"\\ref\{fig:fig[4-9]\}", text))
    n_lab = len(re.findall(r"\\label\{fig:fig[4-9]\}", text))
    print(f"updated {TEX.relative_to(ROOT)}: {n_ref} shifted refs, {n_lab} shifted labels, fig3 inserted")


if __name__ == "__main__":
    main()
