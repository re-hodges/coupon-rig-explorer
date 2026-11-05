"""Model-truth input ranking from runs ALREADY ON DISK. No surrogate, no new runs.

Every index here is computed from the 4,096-point QMC block of sa_design.csv joined to
the sa_results_*.csv set -- i.e. from evaluations of the differential equations
themselves. Nothing is fitted to approximate the model.

Five families, each answering a slightly different question:

  SRC / SRRC  Standardised (rank) regression coefficients. Signed, and they come with
              the regression's own R2, which is the honest goodness-of-fit number for
              this model: it says what fraction of the model's output variance a linear
              (or monotone) description captures. The convention in the wastewater
              literature is that an SRC ranking is trustworthy when that R2 is around
              0.7 or better; below that the model is too non-linear for regression
              ranking and the moment-independent measures should be read instead.

  PRCC        Partial rank correlation: the monotone association of each input with the
              output once every other input is partialled out. Signed. Standard for
              biological ODE models.

  delta       Borgonovo's moment-independent importance -- how much the whole output
              DISTRIBUTION shifts when an input is fixed, not just its variance. Robust
              to the skew in J_A. Returns a first-order S1 alongside it.

  PAWN        CDF-based importance. Like delta it makes no linearity or variance
              assumption; cheap and stable at this sample size.

  RBD-FAST    First-order Sobol' indices recovered from an arbitrary sample by a
              frequency-domain trick -- a variance decomposition WITHOUT the Saltelli
              design or a surrogate.

MATERIAL is categorical. It enters the regression methods as dummy variables and is
handled by STRATIFICATION for the distribution-based methods, which are run within each
material and averaged. Feeding a material index to a method that treats it as a
continuous axis is the exact mistake that produced the original TreeExplainer bug.
"""
import os, sys, glob, json
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sa_design as SD

TARGETS = {"JA_d60": "day-60 areal removal flux",
           "X_d60": "day-60 total biofilm",
           "Xp_d60": "day-60 phototrophs",
           "Xn_d60": "day-60 nitrifiers",
           "Xh_d60": "day-60 heterotrophs"}


def load():
    des = pd.read_csv(os.path.join(HERE, "sa_design.csv"))
    res = pd.concat([pd.read_csv(f) for f in
                     sorted(glob.glob(os.path.join(HERE, "sa_results_*.csv")))])
    d = des[des.kind == "qmc"].merge(res, on="run_id")
    assert d.finite.all(), "non-finite runs in the QMC block"
    return d


def design_matrix(d):
    """log for the log-uniform inputs, raw for the uniform ones."""
    X = pd.DataFrame(index=d.index)
    for n in SD.CONT:
        X[n] = np.log(d[n]) if n in SD.LOGU else d[n].astype(float)
    return X


def src(X, y, rank=False):
    """Standardised (rank) regression coefficients + the model R2."""
    A = X.rank() if rank else X.copy()
    b = pd.Series(y).rank().values if rank else np.asarray(y, float)
    A = (A - A.mean()) / A.std(ddof=1)
    b = (b - b.mean()) / b.std(ddof=1)
    M = np.column_stack([np.ones(len(A)), A.values])
    coef, *_ = np.linalg.lstsq(M, b, rcond=None)
    pred = M @ coef
    r2 = 1.0 - ((b - pred) ** 2).sum() / ((b - b.mean()) ** 2).sum()
    return pd.Series(coef[1:], index=A.columns), float(r2)


def prcc(X, y):
    """Partial rank correlation of each input with the output."""
    R = np.column_stack([X.rank().values, pd.Series(y).rank().values])
    R = (R - R.mean(0)) / R.std(0, ddof=1)
    C = np.corrcoef(R, rowvar=False)
    P = np.linalg.pinv(C)
    k = X.shape[1]
    out = [-P[i, k] / np.sqrt(P[i, i] * P[k, k]) for i in range(k)]
    return pd.Series(out, index=X.columns)


def distribution_methods(X, y, seed=3, num_resamples=10):
    """num_resamples is deliberately low: delta's bootstrap is the expensive part and
    we use the point estimate for ranking, not its confidence interval. The confidence
    intervals that carry weight in the report come from the Sobol' run on the ODE."""
    from SALib.analyze import delta as D_, pawn as P_, rbd_fast as R_
    prob = {"num_vars": X.shape[1], "names": list(X.columns),
            "bounds": [[float(X[c].min()), float(X[c].max())] for c in X.columns]}
    Xv, yv = X.values, np.asarray(y, float)
    out = {}
    dd = D_.analyze(prob, Xv, yv, num_resamples=num_resamples, seed=seed, method="all")
    out["delta"] = pd.Series(dd["delta_raw"], index=prob["names"])
    out["delta_S1"] = pd.Series(dd["S1"], index=prob["names"])
    pw = P_.analyze(prob, Xv, yv, S=10, seed=seed)
    pwdf = pd.DataFrame({k: v for k, v in pw.items() if k != "names"},
                        index=pw["names"])
    col = "median" if "median" in pwdf.columns else pwdf.columns[0]
    out["pawn"] = pwdf[col]
    rb = R_.analyze(prob, Xv, yv, M=10, num_resamples=50, seed=seed)
    out["rbd_S1"] = pd.Series(rb["S1"], index=prob["names"])
    return out


def run():
    d = load()
    X = design_matrix(d)
    mats = sorted(d.material.unique())
    rows, meta = [], []
    for tgt in TARGETS:
        y = d[tgt].values
        # ---- regression family: pooled, material as dummies
        Xd = X.copy()
        for m in mats[1:]:
            Xd[f"material[{m}]"] = (d.material == m).astype(float).values
        s_src, r2_src = src(Xd, y)
        s_srr, r2_srr = src(Xd, y, rank=True)
        for n in Xd.columns:
            rows.append(dict(target=tgt, parameter=n, method="SRC", value=s_src[n]))
            rows.append(dict(target=tgt, parameter=n, method="SRRC", value=s_srr[n]))
        # ---- distribution family + PRCC: stratified by material, then averaged
        per = {k: [] for k in ("PRCC", "delta", "delta_S1", "pawn", "rbd_S1")}
        for m in mats:
            sel = (d.material == m).values
            Xm, ym = X[sel], y[sel]
            per["PRCC"].append(prcc(Xm, ym))
            dm = distribution_methods(Xm, ym)
            for k in ("delta", "delta_S1", "pawn", "rbd_S1"):
                per[k].append(dm[k])
        for k, lst in per.items():
            M = pd.concat(lst, axis=1)
            for n in M.index:
                rows.append(dict(target=tgt, parameter=n, method=k,
                                 value=float(M.loc[n].mean()),
                                 spread=float(M.loc[n].std(ddof=1))))
        meta.append(dict(target=tgt, label=TARGETS[tgt], n=int(len(d)),
                         R2_SRC=r2_src, R2_SRRC=r2_srr,
                         src_valid=bool(r2_src >= 0.7), srrc_valid=bool(r2_srr >= 0.7)))
        print(f"{tgt:8s}  R2(SRC) {r2_src:.3f}   R2(SRRC) {r2_srr:.3f}")
    G = pd.DataFrame(rows)
    G.to_csv(os.path.join(HERE, "sa_givendata.csv"), index=False)
    pd.DataFrame(meta).to_csv(os.path.join(HERE, "sa_givendata_meta.csv"), index=False)
    return G, pd.DataFrame(meta)


if __name__ == "__main__":
    G, M = run()
    print()
    W = (G[(G.target == "JA_d60")]
         .pivot_table(index="parameter", columns="method", values="value")
         .reindex(columns=["SRC", "SRRC", "PRCC", "delta", "delta_S1", "pawn", "rbd_S1"]))
    W["rank_|PRCC|"] = W.PRCC.abs().rank(ascending=False)
    print(W.sort_values("delta", ascending=False).round(4).to_string())
    print(f"\nwrote sa_givendata.csv ({len(G)} rows) and sa_givendata_meta.csv")
