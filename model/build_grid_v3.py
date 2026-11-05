"""Precompute the coupon explorer parameter grid for the BAND-MOUNTED rig (v3).

    python build_grid_v3.py <shard> <n_shards>     # one shard, writes grid_v3_part<shard>.json
    python build_grid_v3.py merge                  # combines parts -> grid_v3.json + .csv

WHAT CHANGED FROM v2 (4 Nov 2026, Anthony's rig description)
------------------------------------------------------------
Mount radius RETIRES as a design axis. The coupons no longer sit on boards that could
be bolted at a chosen radius; they sit in divots on two steel bands that run between
the end plates, so the radius is fixed by hardware at r/R = 0.95. That axis was the
largest single design effect in the v2 grid -- J_A rose monotonically with radius in
all 288 arm sets, 2.43x from r/R 0.25 to 0.85 -- and the band sits at the top of that
range, i.e. the most-submerged, least-lit, highest-flux station on the wheel.

The freed axis is spent on DIVOT SHELTER phi_shear, which the new mounting introduces
and which nothing measures. A coupon recessed in a divot feels less than the free-
stream wall shear; phi_shear = 1 is flush, 0.3 is well sheltered.

Everything else holds: 60-day horizon (kept at the user's direction so the graphene
arm can be read past its onset), flat coupons only, bulk fixed by the plant.
"""
from __future__ import annotations
import os, sys, json, time, itertools, glob
import numpy as np, pandas as pd, yaml

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

MAT   = ["PE", "STL", "GRA", "FAB"]
PHOT  = [("summer", 15.50), ("winter", 8.87)]      # Rapid City solstices, TIMER hours
RPM   = [0.5, 1.0, 1.5, 2.0, 2.5, 4.0]
NSH   = [0.0, 0.5, 1.0]                             # shear exponent, sampled not fixed
SHELT = [0.3, 0.5, 1.0]                             # divot shelter phi_shear, UNSOURCED
LOAD  = [("low",  dict(Snh=30.0, Sno=0.0, Sp=4.0, Sb=72.0)),
         ("high", dict(Snh=30.0, Sno=0.0, Sp=4.0, Sb=120.0))]

BAND_R_OVER_R = 0.95      # fixed by the steel band
D_DISC_M      = 2.0       # placeholder
VIEW_FACTOR   = 0.90      # divot dimming, placeholder
DAYS, TEMP, NOUT, SUBSTEP = 60.0, 15.0, 241, 240.0   # 0.25 d grid: days 5/7/10 land exactly
HARVEST = {"d5": 5, "d7": 7, "d10": 10, "d60": 60}
XMAX = {"FAB": 91.16, "STL": 3.27, "GRA": 3.27, "PE": 6.19}   # Gross 2016 7-day biomass
FLAT = {"FAB": "Flat sheet"}
def flat_of(mat): return FLAT.get(mat, "Flat plate")

_CAT = pd.read_csv(os.path.join(HERE, "geometry_catalogue.csv"))
_IB  = pd.read_csv(os.path.join(HERE, "irradiance_bins.csv"))
_PAR = yaml.safe_load(open(os.path.join(HERE, "params_v2.yaml")))["parameters"]


def _arm(a):
    try:
        return _arm_inner(a)
    except Exception as e:
        mat, (pname, _), rpm, nsh, sh, (lname, _f) = a
        return dict(key=f"{mat}|{pname}|{rpm}|{nsh}|{sh}|{lname}", material=mat,
                    finite=False, error=f"{type(e).__name__}: {e}")


def _arm_inner(a):
    from reactor_v2 import RBCReactor
    import area as AR
    mat, (pname, timer), rpm, nsh, sh, (lname, feed) = a
    geo = flat_of(mat)
    g = _CAT[(_CAT.material == mat) & (_CAT.geometry == geo)].iloc[0]
    b = _IB[(_IB.material == mat) & (_IB.geometry == geo)].sort_values("bin")
    r = RBCReactor(dict(_PAR), b.area_fraction.values, b.rel_irradiance.values,
                   a_v=g.a_geo_m2_m3,
                   attach=(XMAX[mat] / XMAX["PE"]) * AR.attachment_roughness_factor(mat),
                   bulk_mode="fixed", feed=feed, graphene=(mat == "GRA"),
                   rpm=rpm, r_over_R=BAND_R_OVER_R, D_disc_m=D_DISC_M,
                   n_shear=nsh, phi_shear=sh, view_factor=VIEW_FACTOR)
    t, y, deliv = r.simulate_rbc(DAYS, timer_h=timer, T=TEMP, n_out=NOUT, substep_min=SUBSTEP)
    d = r.unpack(y); w = r.w
    Xp, Xn, Xh = (np.einsum("tb,b->t", d[k], w) for k in ("Xp", "Xn", "Xh"))
    Xt = Xp + Xn + Xh
    Lf = 1e3 * r.film_thickness(Xt)                      # mm
    JA = np.array([r.areal_rate(row, T=TEMP) for row in y])   # g N m-2 d-1
    duty = r.duty()
    ix = {lab: int(np.argmin(abs(t - dd))) for lab, dd in HARVEST.items()}
    keep = slice(None, None, 4)                          # report on a 1 d grid
    return dict(
        key=f"{mat}|{pname}|{rpm}|{nsh}|{sh}|{lname}",
        material=mat, photoperiod=pname, timer_h=timer, delivered_h=round(float(deliv), 3),
        rpm=rpm, n_shear=nsh, shelter=sh, load=lname,
        r_over_R=BAND_R_OVER_R,
        f_wet=round(duty["f_wet"], 4), period_s=round(duty["period_s"], 2),
        submerged_s=round(duty["submerged_s"], 2), emergent_s=round(duty["emergent_s"], 2),
        tau_Pa=round(float(duty["tau_Pa"]), 5),
        tau_free_Pa=round(float(duty["tau_free_Pa"]), 5),
        I0=round(float(duty["I0"]), 2),
        k_det=round(float(duty["k_det"]), 5),
        laminar_ok=bool(duty["laminar_ok"]), Re=round(float(duty["Re"]), 0),
        o2_um=round(float(duty["o2_penetration_um"]), 1),
        t=[round(float(v), 3) for v in t[keep]],
        Xp=[round(float(v), 4) for v in Xp[keep]], Xn=[round(float(v), 4) for v in Xn[keep]],
        Xh=[round(float(v), 4) for v in Xh[keep]], Lf=[round(float(v), 5) for v in Lf[keep]],
        JA=[round(float(v), 5) for v in JA[keep]],
        harvest_mg={k: round(AR.harvestable_mg(Xt[i], n_coupons=AR.COUPONS_PER_HARVEST), 4)
                    for k, i in ix.items()},
        harvest_mg_1={k: round(AR.harvestable_mg(Xt[i]), 4) for k, i in ix.items()},
        JA_at={k: round(float(JA[i]), 5) for k, i in ix.items()},
        X_at={k: round(float(Xt[i]), 4) for k, i in ix.items()},
        Lf_at={k: round(float(Lf[i]), 5) for k, i in ix.items()},
        finite=bool(np.all(np.isfinite(y))),
    )


def all_arms():
    return list(itertools.product(MAT, PHOT, RPM, NSH, SHELT, LOAD))


def merge():
    out = []
    for f in sorted(glob.glob(os.path.join(HERE, "grid_v3_part*.json"))):
        out.extend(json.load(open(f)))
    bad = [(o["key"], o.get("error", "non-finite")) for o in out if not o["finite"]]
    out = [o for o in out if o["finite"]]
    print(f"merged {len(out)} arms; non-finite: {len(bad)}")
    if bad:
        print("  FAILED:", bad[:10])
    json.dump(out, open(os.path.join(HERE, "grid_v3.json"), "w"), separators=(",", ":"))
    cols = ["key","material","photoperiod","timer_h","delivered_h","rpm","n_shear","shelter",
            "load","r_over_R","f_wet","period_s","submerged_s","emergent_s","tau_Pa",
            "tau_free_Pa","I0","k_det","laminar_ok","Re","o2_um","finite"]
    df = pd.DataFrame([{**{c: o[c] for c in cols},
                        **{f"X_{k}": o["X_at"][k] for k in HARVEST},
                        **{f"JA_{k}": o["JA_at"][k] for k in HARVEST},
                        **{f"Lf_{k}": o["Lf_at"][k] for k in HARVEST},
                        **{f"harv3_{k}": o["harvest_mg"][k] for k in HARVEST}}
                       for o in out])
    df.sort_values(["material","photoperiod","rpm","n_shear","shelter","load"]).to_csv(
        os.path.join(HERE, "grid_v3.csv"), index=False)
    print(f"wrote grid_v3.json ({os.path.getsize(os.path.join(HERE,'grid_v3.json'))/1e6:.1f} MB)"
          f" and grid_v3.csv ({len(df)} rows)")


if __name__ == "__main__":
    if sys.argv[1] == "merge":
        merge(); sys.exit(0)
    shard, nsh_ = int(sys.argv[1]), int(sys.argv[2])
    arms = all_arms()
    mine = [(i, a) for i, a in enumerate(arms) if i % nsh_ == shard]
    print(f"shard {shard}: {len(mine)} of {len(arms)} arms", flush=True)
    out, t0 = [], time.time()
    for n, (i, a) in enumerate(mine, 1):
        out.append(_arm(a))
        if n % 25 == 0:
            print(f"shard {shard}: {n}/{len(mine)}  {time.time()-t0:.0f}s", flush=True)
    json.dump(out, open(os.path.join(HERE, f"grid_v3_part{shard}.json"), "w"),
              separators=(",", ":"))
    print(f"shard {shard} DONE {len(out)} arms in {time.time()-t0:.0f}s", flush=True)
