"""Precompute the coupon-model grid behind the interactive explorer.

Writes explorer_data.json: one entry per (a_v, feeds/day, replace fraction, material,
photoperiod), each carrying the 28-day trajectory on a half-day grid plus the summary
numbers the explorer reports. The grid is deliberately small enough to embed in a single
self-contained HTML page that needs no server.

    python build_explorer.py            # ~35 min
"""
from __future__ import annotations
import itertools, json, os, sys, time
import numpy as np, pandas as pd, yaml

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from reactor import Reactor

PAR = yaml.safe_load(open(os.path.join(HERE, "params_v2.yaml")))["parameters"]
CAT = pd.read_csv(os.path.join(HERE, "geometry_catalogue.csv"))
IB = pd.read_csv(os.path.join(HERE, "irradiance_bins.csv"))
RIG = yaml.safe_load(open(os.path.join(HERE, "rig.yaml")))
F_WET = RIG["geometry"]["f_wet"]
FEED = {"Snh": RIG["protocol"]["feed"]["nh3n_mg_l"], "Sno": RIG["protocol"]["feed"]["no3n_mg_l"],
        "Sp": RIG["protocol"]["feed"]["tp_mg_l"], "Sb": RIG["protocol"]["feed"]["bod5_mg_l"]}

XMAX = {"FAB": 91.16, "STL": 3.27, "GRA": 3.27, "PE": 6.19}
GEOM = {"FAB": "Flat sheet", "STL": "Flat plate", "GRA": "Flat plate", "PE": "Flat plate"}
MATERIALS = [("FAB", "Non-woven fabric"), ("STL", "Bare steel"),
             ("GRA", "Graphene-coated"), ("PE", "HDPE")]
PHOTO = [("FBK", "Fairbanks AK", 5.0), ("STG", "Sturgis SD", 9.2), ("KEY", "Key West FL", 10.767)]

AV = [2.5, 5.0, 7.5, 15.0, 30.3]          # m2 coupon per m3 liquid
FEEDS = [0, 1, 2, 4]                       # 0 = closed batch, nothing replenished
FRACS = [0.5, 1.0]                         # share of the volume exchanged each time
# Irradiance AT THE VESSEL. The project documents specify photoperiod in hours but contain
# no lamp, PAR, irradiance, lux or umol figure anywhere -- so this is unmeasured, and it
# stands in for both lamp output and where a vessel sits under the panel. 110 is the
# params_v2.yaml placeholder (Gross et al. 2016); 72 is what a vessel at the dim edge of
# the modelled LED panel would receive (0.66 x), 150 the top of the sampled range.
I0S = [72.0, 110.0, 150.0]
FIRST_FEED_DAY = RIG["protocol"]["first_feed_day"]
DAYS, OUT_DT, SUBSTEP = 28.0, 0.5, 120.0


def run(code, av, per_day, frac, light_h, i0):
    g = CAT[(CAT.material == code) & (CAT.geometry == GEOM[code])].iloc[0]
    b = IB[(IB.material == code) & (IB.geometry == GEOM[code])].sort_values("bin")
    pp = dict(PAR); pp["I0"] = i0
    pp["f_wet"] = F_WET
    r = Reactor(pp, b.area_fraction.values, b.rel_irradiance.values, a_v=av,
                attach=XMAX[code] / XMAX["PE"], bulk_mode="batch", feed=FEED,
                graphene=(code == "GRA"))
    if per_day == 0:
        t, y = r.simulate(DAYS, light_h=light_h, T=20.0, n_out=10_000, substep_min=SUBSTEP)
    else:
        feed = np.array([FEED["Snh"], FEED["Sno"], FEED["Sp"], FEED["Sb"]])
        step = 1.0 / per_day
        ts, ys, y_, t0 = [], [], None, 0.0
        for _ in range(int(round(DAYS * per_day))):
            tt, yy = r.simulate(step, light_h=light_h, T=20.0, n_out=10_000,
                                substep_min=SUBSTEP, y0=y_, t0=t0)
            ts.append(tt); ys.append(yy)
            y_ = yy[-1].copy(); t0 = tt[-1]
            if t0 >= FIRST_FEED_DAY - 1e-9:
                y_[:4] = (1.0 - frac) * y_[:4] + frac * feed
                y_[4] *= (1.0 - frac)
        t = np.concatenate(ts); y = np.concatenate(ys)

    d = r.unpack(y); w = r.w
    Xp, Xn, Xh = (np.einsum("tb,b->t", d[k], w) for k in ("Xp", "Xn", "Xh"))
    tot = Xp + Xn + Xh
    grid = np.arange(0.0, DAYS + 1e-9, OUT_DT)
    at = lambda v, dd: float(np.interp(dd, t, v))
    sel = (t >= 3) & (t <= 10)                    # the harvest window
    rnd = lambda a, n=3: [round(float(v), n) for v in a]
    return dict(
        X=rnd(np.interp(grid, t, tot), 2),
        nh3=rnd(np.interp(grid, t, d["Snh"]), 2),
        no3=rnd(np.interp(grid, t, d["Sno"]), 2),
        X3=round(at(tot, 3), 2), X7=round(at(tot, 7), 2),
        X10=round(at(tot, 10), 2), X28=round(at(tot, 28), 2),
        Xp10=round(at(Xp, 10), 2), Xn10=round(at(Xn, 10), 2), Xh10=round(at(Xh, 10), 2),
        nh3_min=round(float(d["Snh"][sel].min()), 2),
        nh3_mean=round(float(d["Snh"][sel].mean()), 2),
        pct_above2=round(100.0 * float((d["Snh"][sel] > 2.0).mean()), 1),
        Lf28=round(1e3 * float(r.film_thickness(at(tot, 28))), 3),
    )


def main():
    combos = []
    for av, per, frac in itertools.product(AV, FEEDS, FRACS):
        if per == 0 and frac != FRACS[0]:
            continue                      # fraction is meaningless with no feeding
        combos.append((av, per, frac))
    total = len(combos) * len(MATERIALS) * len(PHOTO) * len(I0S)
    print(f"{len(combos)} protocols x {len(MATERIALS)} materials x {len(PHOTO)} photoperiods "
          f"x {len(I0S)} irradiances = {total} runs", flush=True)
    data, t0, n = {}, time.time(), 0
    for av, per, frac in combos:
        for code, _ in MATERIALS:
            for pc, _, light in PHOTO:
                for i0 in I0S:
                    key = f"{av:.1f}|{per}|{frac:.2f}|{code}|{pc}|{i0:.0f}"
                    data[key] = run(code, av, per, frac, light, i0)
                    n += 1
        print(f"  av={av:<5} feeds={per} frac={frac}  {n}/{total}  {time.time()-t0:5.0f}s",
              flush=True)
    meta = dict(days=[round(x, 1) for x in np.arange(0.0, DAYS + 1e-9, OUT_DT)],
                av=AV, feeds=FEEDS, fracs=FRACS, i0s=I0S,
                first_feed_day=FIRST_FEED_DAY,
                materials=[list(m) for m in MATERIALS],
                photoperiods=[[c, n_, h] for c, n_, h in PHOTO],
                feed=FEED, x_cap=PAR["X_cap"],
                film_band_mm=[0.151, 0.412],
                source="coupon_model v2 (reactor.py), 28-day batch at 20 C")
    out = os.path.join(HERE, "explorer_data.json")
    json.dump(dict(meta=meta, runs=data), open(out, "w"), separators=(",", ":"))
    print(f"wrote explorer_data.json: {len(data)} runs, "
          f"{os.path.getsize(out)/1e6:.2f} MB, {(time.time()-t0)/60:.0f} min")


if __name__ == "__main__":
    main()
