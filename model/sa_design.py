
"""Build the sampling design for the coupon explorer v2 sensitivity tab.

Two designs, written to one file so they can be sharded across worker processes:

  kind = "qmc"    4096-point scrambled Sobol' sequence over all 20 inputs. Feeds the
                  gradient-boosted surrogate, the SHAP attribution and the
                  surrogate-based Sobol' variance decomposition.
  kind = "morris" 20 trajectories x 20 points over the 19 CONTINUOUS inputs with
                  material fixed at PE. Elementary effects are taken on the ODE
                  itself, so this is the model-truth check on the surrogate ranking.

REVISED 4 Nov 2026 for the band-mounted rig. Mount radius is NO LONGER an input: the
coupons sit in divots on steel bands at a hardware-fixed r/R = 0.95, so f_wet is a
constant 0.4469 and cannot be varied. Its slot is taken by the divot shelter factor
phi_shear, which the new mounting introduces and which nothing measures.

f_wet is likewise NOT sampled: RBCReactor derives it from radius and submergence, so a
sampled value would be overwritten.
"""
import os, numpy as np, pandas as pd
from scipy.stats import qmc

HERE = os.path.dirname(os.path.abspath(__file__))

# ---- inputs -------------------------------------------------------------------
# log-uniform physical parameters, ranges from ensemble.SAMPLED (coupon_model_decisions)
LOGU = {
    "k_att":    (0.3, 3.0),      "K_comp":  (2.0, 10.0),   "X_cap":    (32.0, 88.0),
    "rN_ref":   (2.96, 5.45),    "k_det":   (0.01, 0.15),  "D_O2_eff": (0.54e-4, 2.16e-4),
    "S_O_bulk": (6.5, 9.1),      "b_p":     (0.09, 0.17),  "K_I":      (25.0, 100.0),
    "I0":       (80.0, 150.0),   "K_P_p":   (0.005, 0.1),  "Y_O2_p":   (1.0, 1.6),
    "theta_p":  (1.03, 1.10),    "theta_h": (1.03, 1.10),
}
# uniform design / operating factors the team can actually set
UNIF = {
    "shelter":  (0.3, 1.0),      # divot shelter phi_shear on wall shear; 1.0 = flush
    "rpm":      (0.5, 4.0),      # wheel speed (4.0 = as found; slower = proposed)
    "n_shear":  (0.0, 1.0),      # shear exponent on detachment, literature disagreement
    "timer_h":  (8.87, 15.50),   # lamp timer hours, Rapid City winter->summer solstice
    "Sb":       (72.0, 120.0),   # first-stage readily biodegradable COD, g m-3
}
MATERIALS = ["PE", "STL", "GRA", "FAB"]
CONT = list(LOGU) + list(UNIF)            # 19 continuous
FEATURES = CONT + ["material"]            # 20 total


def unit_to_real(U):
    """U: (n, 19) in [0,1] -> DataFrame of real continuous values."""
    out = {}
    for j, n in enumerate(CONT):
        if n in LOGU:
            lo, hi = LOGU[n]
            out[n] = np.exp(np.log(lo) + U[:, j] * (np.log(hi) - np.log(lo)))
        else:
            lo, hi = UNIF[n]
            out[n] = lo + U[:, j] * (hi - lo)
    return pd.DataFrame(out)


def qmc_design(n_pow=12, seed=20261104):
    n = 2 ** n_pow
    s = qmc.Sobol(d=len(CONT) + 1, scramble=True, seed=seed)
    U = s.random(n)
    df = unit_to_real(U[:, :len(CONT)])
    df["material"] = [MATERIALS[min(int(u * 4), 3)] for u in U[:, -1]]
    df.insert(0, "kind", "qmc"); df.insert(1, "traj", -1); df.insert(2, "step", -1)
    df.insert(3, "varied", "")
    return df


def morris_design(r=20, levels=4, seed=11):
    """Standard Morris one-at-a-time trajectories in unit space, material fixed PE."""
    k = len(CONT)
    delta = levels / (2.0 * (levels - 1))
    rng = np.random.default_rng(seed)
    rows, meta = [], []
    for t in range(r):
        u = np.clip(rng.integers(0, levels, k) / (levels - 1), 0, 1 - delta)
        rows.append(u.copy()); meta.append((t, 0, ""))
        for s, j in enumerate(rng.permutation(k), start=1):
            u = u.copy(); u[j] = min(1.0, u[j] + delta)
            rows.append(u.copy()); meta.append((t, s, CONT[j]))
    df = unit_to_real(np.array(rows))
    df["material"] = "PE"
    df.insert(0, "kind", "morris")
    df.insert(1, "traj", [m[0] for m in meta])
    df.insert(2, "step", [m[1] for m in meta])
    df.insert(3, "varied", [m[2] for m in meta])
    return df, delta


if __name__ == "__main__":
    q = qmc_design()
    m, delta = morris_design()
    d = pd.concat([q, m], ignore_index=True)
    d.insert(0, "run_id", np.arange(len(d)))
    d.to_csv(os.path.join(HERE, "sa_design.csv"), index=False)
    print(f"qmc {len(q)} + morris {len(m)} = {len(d)} runs; morris delta={delta:.4f}")
    print(f"{len(FEATURES)} features: {FEATURES}")
