"""Sobol' indices and EXACT Shapley values, both computed on the differential equations.

Consumes sa_ode2_design.csv + sa_ode2_results_*.csv (written by sa_ode_worker.py).
No surrogate is fitted anywhere in this file.

1. SOBOL'. The Saltelli block is handed to SALib in its sampled order, giving first-order
   S1 and total-order S_T with bootstrap confidence intervals. This replaces the indices
   that were previously read off a gradient-boosted surrogate.

2. EXACT SHAPLEY. For each arm, all 2^k coalitions of the k explained inputs were
   evaluated on the ODE, so the Shapley value

       phi_i = SUM over S subset of N\\{i} of  |S|!(k-|S|-1)!/k! * [v(S+i) - v(S)]

   is computed by complete enumeration. No sampling, no approximation, and the
   efficiency property sum(phi) = v(full) - v(empty) holds to machine precision rather
   than being asserted by a test. That identity is checked anyway, because the whole
   reason the previous surrogate SHAP was wrong is that nobody checked it.
"""
import os, sys, glob
from math import factorial
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sa_design as SD
import sa_ode_design as OD

TARGET = "JA_d60"


def load():
    des = pd.read_csv(os.path.join(HERE, "sa_ode2_design.csv"))
    res = pd.concat([pd.read_csv(f) for f in
                     sorted(glob.glob(os.path.join(HERE, "sa_ode2_results_*.csv")))])
    res = res.drop_duplicates("run_id", keep="last")
    d = des.merge(res, on="run_id", how="left", suffixes=("", "_r"))
    return d


def sobol_indices(d, target=TARGET):
    from SALib.analyze import sobol as S_
    b = d[d.block == "sobol"].sort_values("run_id")
    miss = int(b[target].isna().sum())
    if miss:
        raise RuntimeError(f"sobol block incomplete: {miss} of {len(b)} runs missing")
    names = SD.CONT + ["material_u"]
    problem = {"num_vars": len(names), "names": names,
               "bounds": [[0.0, 1.0]] * len(names)}
    Si = S_.analyze(problem, b[target].values, calc_second_order=False,
                    num_resamples=200, seed=11)
    out = pd.DataFrame({"parameter": names,
                        "S1": Si["S1"], "S1_conf": Si["S1_conf"],
                        "ST": Si["ST"], "ST_conf": Si["ST_conf"]})
    out["parameter"] = out.parameter.replace({"material_u": "material"})
    return out.sort_values("ST", ascending=False), len(b)


def exact_shapley(d, block, feats, target=TARGET):
    """Complete-enumeration Shapley values, one row per (arm, feature)."""
    k = len(feats)
    w = np.array([factorial(s) * factorial(k - s - 1) / factorial(k)
                  for s in range(k)])
    rows, checks = [], []
    b = d[d.block == block]
    for arm, g in b.groupby("arm"):
        g = g.sort_values("coalition")
        if len(g) != 2 ** k or g[target].isna().any():
            raise RuntimeError(f"{block} arm {arm}: {len(g)} rows, "
                               f"{int(g[target].isna().sum())} missing")
        v = g.set_index("coalition")[target].to_dict()
        phi = np.zeros(k)
        for i in range(k):
            bit = 1 << i
            for mask in range(2 ** k):
                if mask & bit:
                    continue
                s = bin(mask).count("1")
                phi[i] += w[s] * (v[mask | bit] - v[mask])
        total = v[2 ** k - 1] - v[0]
        checks.append(abs(phi.sum() - total))
        for i, f in enumerate(feats):
            rows.append(dict(arm=int(arm), parameter=f, phi=float(phi[i]),
                             material=g.material.iloc[0],
                             v_full=v[2 ** k - 1], v_empty=v[0], total=total))
    err = float(np.max(checks))
    if err > 1e-9:
        raise RuntimeError(f"Shapley efficiency violated in {block}: max |sum(phi) "
                           f"- (v_full - v_empty)| = {err:.3e}")
    return pd.DataFrame(rows), err


def run():
    d = load()
    done = int(d[TARGET].notna().sum())
    print(f"runs available: {done} of {len(d)}")

    SB, n_sob = sobol_indices(d)
    SB.to_csv(os.path.join(HERE, "sa_sobol_ode.csv"), index=False)
    print(f"\nSOBOL' on the ODE (n = {n_sob} runs, no surrogate)")
    print(SB.round(4).to_string(index=False))

    SH, err8 = exact_shapley(d, "shap8", OD.TOP8)
    SH.to_csv(os.path.join(HERE, "sa_shapley_exact.csv"), index=False)
    print(f"\nEXACT SHAPLEY, {len(OD.TOP8)} inputs, "
          f"{SH.arm.nunique()} arms, full 2^{len(OD.TOP8)} enumeration")
    print(f"  efficiency check  max |sum(phi) - (v_full - v_empty)| = {err8:.3e}")
    agg = (SH.groupby("parameter")
             .agg(mean_abs_phi=("phi", lambda s: s.abs().mean()),
                  mean_phi=("phi", "mean"))
             .sort_values("mean_abs_phi", ascending=False))
    print(agg.round(5).to_string())

    gnames = list(OD.GROUPS)
    SG, errg = exact_shapley(d, "shapgrp", gnames)
    SG.to_csv(os.path.join(HERE, "sa_shapley_grouped.csv"), index=False)
    print(f"\nEXACT GROUPED SHAPLEY ({', '.join(gnames)})")
    print(f"  efficiency check = {errg:.3e}")
    print(SG.groupby("parameter").phi.agg(["mean", "std"]).round(5).to_string())
    return SB, SH, SG


if __name__ == "__main__":
    run()
