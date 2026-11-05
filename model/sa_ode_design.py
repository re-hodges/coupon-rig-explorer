"""Build the SURROGATE-FREE sampling design for the coupon explorer v2 sensitivity tab.

Everything here is evaluated on the differential equations themselves. Nothing in this
file fits, trains or explains an approximation of the model.

Three blocks, written to one design file so they shard across worker processes:

  block = "sobol"    Saltelli design over all 20 inputs (19 continuous + material as a
                     4-level discrete input). N=256, calc_second_order=False, so
                     N*(D+2) = 5,632 runs. Replaces the Sobol' indices that were
                     previously read off a gradient-boosted surrogate.

  block = "shap8"    EXACT Shapley values on the ODE. For each of 24 representative
                     arms, all 2^8 = 256 coalitions of the 8 highest-Morris inputs are
                     evaluated: a member of the coalition takes the arm's value, a
                     non-member takes the baseline value. Because every coalition is
                     enumerated, the Shapley value is exact -- there is no sampling
                     error and additivity holds by construction rather than by test.
                     6,144 runs.

  block = "shapgrp"  Exact GROUPED Shapley over the three-domain taxonomy used in this
                     project (surface properties / environmental and physiological /
                     biological). 2^3 = 8 coalitions per arm, 192 runs. Material is a
                     member of the surface-properties group, so it toggles here.

BASELINE. The reference point the Shapley decomposition explains deviation FROM:
params_v2.yaml nominals for the 14 physical parameters, the wheel at its as-found
4 rpm, the shear exponent and divot shelter at the midpoints of their disputed ranges,
the lamp timer at the equinox-equivalent midpoint, and feed BOD at the technical
memorandum's ~100 g/m3. In the shap8 block the arm's own material is held in the
baseline too, so that block explains parameters at fixed material; material enters
only in shapgrp.

ARMS. The 24 explained arms are drawn from the existing 4,096-point QMC design, six per
material, spread across the day-60 flux range by quantile so the waterfalls span weak
and strong arms rather than clustering at the median.
"""
import os, sys, itertools
import numpy as np, pandas as pd, yaml

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sa_design as SD

PAR = yaml.safe_load(open(os.path.join(HERE, "params_v2.yaml"), encoding="utf-8"))["parameters"]

# the 8 highest-mu* inputs from the Morris screening taken on the ODE (sa_morris.csv)
TOP8 = ["K_comp", "X_cap", "rN_ref", "rpm", "n_shear", "k_det", "shelter", "k_att"]

# three-domain grouping requested for this project
GROUPS = {
    "surface":       ["k_att", "X_cap", "material"],
    "environmental": ["rpm", "n_shear", "shelter", "timer_h", "Sb", "S_O_bulk", "I0", "D_O2_eff"],
    "biological":    ["K_comp", "rN_ref", "k_det", "b_p", "K_I", "K_P_p", "Y_O2_p",
                      "theta_p", "theta_h"],
}

BASE = {n: float(PAR[n]) for n in SD.LOGU}
BASE.update(dict(rpm=4.0,                       # as found on the wheel
                 n_shear=0.5,                   # midpoint of the Rittmann/Peyton dispute
                 shelter=0.65,                  # midpoint of the unmeasured divot range
                 timer_h=(8.87 + 15.50) / 2.0,  # midpoint of the two solstice photoperiods
                 Sb=100.0,                      # technical memorandum, BOD onto the RBCs
                 material="PE"))

ALLCOLS = SD.CONT + ["material"]


def _rows_to_frame(rows, block):
    d = pd.DataFrame(rows)
    d.insert(0, "block", block)
    return d


def sobol_block(N=256):
    """Saltelli design on the ODE. Material is the 20th input, uniform over 4 levels."""
    from SALib.sample import sobol as sobol_sample
    names = SD.CONT + ["material_u"]
    problem = {"num_vars": len(names), "names": names,
               "bounds": [[0.0, 1.0]] * len(names)}
    U = sobol_sample.sample(problem, N, calc_second_order=False)
    df = SD.unit_to_real(U[:, :len(SD.CONT)])
    df["material"] = [SD.MATERIALS[min(int(u * 4), 3)] for u in U[:, -1]]
    df["material_u"] = U[:, -1]
    df.insert(0, "coalition", -1)
    df.insert(0, "arm", -1)
    return _rows_to_frame(df.to_dict("records"), "sobol"), problem, N


def pick_arms(n_per_material=6):
    """Six QMC points per material, spread over the day-60 flux range by quantile."""
    import glob
    des = pd.read_csv(os.path.join(HERE, "sa_design.csv"))
    res = pd.concat([pd.read_csv(f) for f in
                     sorted(glob.glob(os.path.join(HERE, "sa_results_*.csv")))])
    m = des[des.kind == "qmc"].merge(res[["run_id", "JA_d60"]], on="run_id")
    out = []
    qs = np.linspace(0.05, 0.95, n_per_material)
    for mat in SD.MATERIALS:
        sub = m[m.material == mat].sort_values("JA_d60")
        idx = (qs * (len(sub) - 1)).round().astype(int)
        out.append(sub.iloc[idx])
    arms = pd.concat(out, ignore_index=True)
    arms.insert(0, "arm", np.arange(len(arms)))
    return arms


def shapley_block(arms, feats=TOP8):
    """All 2^k coalitions per arm. Member -> arm value, non-member -> baseline."""
    rows = []
    k = len(feats)
    for _, a in arms.iterrows():
        for mask in range(2 ** k):
            r = dict(BASE)
            r["material"] = a["material"]          # material fixed per arm in this block
            for j, f in enumerate(feats):
                if mask >> j & 1:
                    r[f] = float(a[f])
            r["arm"] = int(a["arm"]); r["coalition"] = mask
            rows.append(r)
    return _rows_to_frame(rows, "shap8")


def grouped_block(arms, groups=GROUPS):
    """Exact Shapley over groups; material toggles with the surface group."""
    rows, gnames = [], list(groups)
    for _, a in arms.iterrows():
        for mask in range(2 ** len(gnames)):
            r = dict(BASE)
            for j, g in enumerate(gnames):
                if mask >> j & 1:
                    for f in groups[g]:
                        r[f] = a[f] if f == "material" else float(a[f])
            r["arm"] = int(a["arm"]); r["coalition"] = mask
            rows.append(r)
    return _rows_to_frame(rows, "shapgrp")


if __name__ == "__main__":
    sob, problem, N = sobol_block()
    arms = pick_arms()
    sh8 = shapley_block(arms)
    shg = grouped_block(arms)
    d = pd.concat([sob, sh8, shg], ignore_index=True)
    d.insert(0, "run_id", np.arange(len(d)))
    for c in ALLCOLS:
        assert c in d.columns, f"missing input column {c}"
    d.to_csv(os.path.join(HERE, "sa_ode2_design.csv"), index=False)
    arms.to_csv(os.path.join(HERE, "sa_ode2_arms.csv"), index=False)
    pd.Series(problem["names"]).to_csv(os.path.join(HERE, "sa_ode2_sobol_names.csv"),
                                       index=False, header=["name"])
    print(f"sobol {len(sob)} (N={N}, D={problem['num_vars']})  "
          f"shap8 {len(sh8)}  shapgrp {len(shg)}  total {len(d)}")
    print(f"arms {len(arms)}; TOP8 {TOP8}")
    print("estimated wall at 1.91 s/run over 4 workers: "
          f"{len(d) * 1.91 / 4 / 3600:.2f} h")
