
"""One shard of the coupon explorer v2 sensitivity sweep.

    python sa_worker.py <shard> <n_shards>

Reads sa_design.csv, runs every design point whose index is congruent to <shard>
mod <n_shards>, writes sa_results_<shard>.csv. Separate PROCESSES, not threads:
the reactor RHS is pure Python so LSODA holds the GIL and threads give no speedup
(measured 3.93 s/run on 8 threads vs 4.43 s/run on one).
"""
import os, sys, time
import numpy as np, pandas as pd, yaml

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from reactor_v2 import RBCReactor
import area as AR

CAT = pd.read_csv(os.path.join(HERE, "geometry_catalogue.csv"))
IB  = pd.read_csv(os.path.join(HERE, "irradiance_bins.csv"))
PAR = yaml.safe_load(open(os.path.join(HERE, "params_v2.yaml")))["parameters"]
XMAX = {"FAB": 91.16, "STL": 3.27, "GRA": 3.27, "PE": 6.19}
FLAT = {"FAB": "Flat sheet"}
DAYS, TEMP, NOUT, SUBSTEP = 60.0, 15.0, 241, 240.0
BAND_R_OVER_R, D_DISC_M, VIEW_FACTOR = 0.95, 2.0, 0.90   # fixed by the band-mounted rig

PARAM_COLS = ["k_att", "K_comp", "X_cap", "rN_ref", "k_det", "D_O2_eff", "S_O_bulk",
              "b_p", "K_I", "I0", "K_P_p", "Y_O2_p", "theta_p", "theta_h"]


def run_point(row):
    mat = row["material"]
    geo = FLAT.get(mat, "Flat plate")
    g = CAT[(CAT.material == mat) & (CAT.geometry == geo)].iloc[0]
    b = IB[(IB.material == mat) & (IB.geometry == geo)].sort_values("bin")
    pp = dict(PAR)
    for c in PARAM_COLS:
        pp[c] = float(row[c])
    r = RBCReactor(pp, b.area_fraction.values, b.rel_irradiance.values,
                   a_v=g.a_geo_m2_m3,
                   attach=(XMAX[mat] / XMAX["PE"]) * AR.attachment_roughness_factor(mat),
                   bulk_mode="fixed",
                   feed=dict(Snh=30.0, Sno=0.0, Sp=4.0, Sb=float(row["Sb"])),
                   graphene=(mat == "GRA"),
                   rpm=float(row["rpm"]), r_over_R=BAND_R_OVER_R, D_disc_m=D_DISC_M,
                   n_shear=float(row["n_shear"]), phi_shear=float(row["shelter"]),
                   view_factor=VIEW_FACTOR)
    t, y, deliv = r.simulate_rbc(DAYS, timer_h=float(row["timer_h"]), T=TEMP,
                                 n_out=NOUT, substep_min=SUBSTEP)
    d = r.unpack(y); w = r.w
    Xp, Xn, Xh = (np.einsum("tb,b->t", d[k], w) for k in ("Xp", "Xn", "Xh"))
    Xt = Xp + Xn + Xh
    Lf = 1e3 * r.film_thickness(Xt)
    JA = np.array([r.areal_rate(rw, T=TEMP) for rw in y])
    i5  = int(np.argmin(abs(t - 5.0)))
    i10, i60 = int(np.argmin(abs(t - 10.0))), int(np.argmin(abs(t - 60.0)))
    duty = r.duty()
    return dict(
        JA_d60=float(JA[i60]), JA_d10=float(JA[i10]), JA_d5=float(JA[i5]),
        X_d60=float(Xt[i60]), X_d10=float(Xt[i10]), X_d5=float(Xt[i5]),
        Xp_d60=float(Xp[i60]), Xn_d60=float(Xn[i60]), Xh_d60=float(Xh[i60]),
        Lf_d60=float(Lf[i60]),
        f_wet=float(duty["f_wet"]), delivered_h=float(deliv),
        tau_Pa=float(duty["tau_Pa"]), k_det_eff=float(duty["k_det"]),
        finite=bool(np.all(np.isfinite(y))))


def main():
    """sa_worker.py <shard> <n_shards> [<sub> <n_sub>]

    The optional sub-split exists because a worker occasionally dies silently under
    memory pressure (5 python processes, each ~400 MB, on a 16 GiB box with ~3 GiB
    free). Re-running one lost shard serially costs an hour; splitting it four ways
    costs a quarter of that, and the Morris trajectories need EVERY point -- one
    missing design point invalidates its whole trajectory.
    """
    shard, nsh = int(sys.argv[1]), int(sys.argv[2])
    sub, nsub = (int(sys.argv[3]), int(sys.argv[4])) if len(sys.argv) > 4 else (0, 1)
    tag = f"{shard}" if nsub == 1 else f"{shard}s{sub}"
    d = pd.read_csv(os.path.join(HERE, "sa_design.csv"))
    mine = d[d.run_id % nsh == shard]
    if nsub > 1:
        mine = mine.iloc[sub::nsub]
    # The worker writes its OWN log rather than relying on Start-Process redirection:
    # launching several processes in a tight loop with -RedirectStandardOutput silently
    # produced zero-byte stdout AND stderr for some of them, i.e. they never ran a line.
    logf = os.path.join(HERE, f"sa_run_{tag}.log")
    def log(msg):
        with open(logf, "a", encoding="utf-8") as fh:
            fh.write(msg + "\n")
    log(f"shard {tag}: {len(mine)} runs, started {time.strftime('%H:%M:%S')}")
    out, t0 = [], time.time()
    for n, (_, row) in enumerate(mine.iterrows(), 1):
        try:
            res = run_point(row)
        except Exception as e:
            res = dict(finite=False, error=f"{type(e).__name__}: {e}"[:120])
        out.append(dict(run_id=int(row.run_id), **res))
        if n % 50 == 0:
            pd.DataFrame(out).to_csv(
                os.path.join(HERE, f"sa_results_{tag}.csv"), index=False)
            log(f"shard {tag}: {n}/{len(mine)}  {time.time()-t0:.0f}s")
    pd.DataFrame(out).to_csv(os.path.join(HERE, f"sa_results_{tag}.csv"), index=False)
    log(f"shard {tag} DONE {len(out)} runs in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
