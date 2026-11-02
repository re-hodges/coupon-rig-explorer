"""Run the coupon-scale model for one arm and show it working.

    python run_demo.py                          # HDPE flat plate, screening conditions
    python run_demo.py --material FAB --geometry "Pleated 5 mm"
    python run_demo.py --material GRA --geometry "Flat plate" --days 60
    python run_demo.py --rig                    # the bench rig as configured (batch)

Needs numpy, scipy, pandas, pyyaml, matplotlib:
    python -m pip install numpy scipy pandas pyyaml matplotlib
Reads the geometry and irradiance tables that are already in this folder, so
scikit-image is NOT needed unless you regenerate them with geometry.py.
"""
from __future__ import annotations
import argparse, os, sys
import numpy as np, pandas as pd, yaml
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from reactor import Reactor
import occlusion as OC

XMAX = {"FAB": 91.16, "STL": 3.27, "GRA": 3.27, "PE": 6.19}      # Gross 2016, 7-day areal biomass
NAME = {"FAB": "non-woven fabric", "STL": "bare steel",
        "GRA": "graphene-coated steel", "PE": "HDPE"}


def build(material, geometry, rig=False):
    cat = pd.read_csv(os.path.join(HERE, "geometry_catalogue.csv"))
    ib = pd.read_csv(os.path.join(HERE, "irradiance_bins.csv"))
    par = yaml.safe_load(open(os.path.join(HERE, "params_v2.yaml")))["parameters"]
    g = cat[(cat.material == material) & (cat.geometry == geometry)]
    if g.empty:
        raise SystemExit(f"no such arm. geometries for {material}: "
                         + ", ".join(cat[cat.material == material].geometry))
    g = g.iloc[0]
    b = ib[(ib.material == material) & (ib.geometry == geometry)].sort_values("bin")
    r = Reactor(par, b.area_fraction.values, b.rel_irradiance.values,
                a_v=7.5 if rig else g.a_geo_m2_m3,
                attach=XMAX[material] / XMAX["PE"],
                bulk_mode="batch" if rig else "fixed",
                graphene=(material == "GRA"))
    return r, g, par


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--material", default="PE", choices=list(XMAX))
    ap.add_argument("--geometry", default="Flat plate")
    ap.add_argument("--days", type=float, default=60.0)
    ap.add_argument("--light", type=float, default=9.683, help="photoperiod, h/d")
    ap.add_argument("--temp", type=float, default=20.0)
    ap.add_argument("--rig", action="store_true",
                    help="bench rig as configured: closed batch at A/V = 7.5 m2/m3")
    ap.add_argument("--out", default="demo_run.png")
    a = ap.parse_args()

    r, g, par = build(a.material, a.geometry, a.rig)
    t, y = r.simulate(a.days, light_h=a.light, T=a.temp, n_out=300, substep_min=120.0)
    d = r.unpack(y)
    w = r.w
    Xp, Xn, Xh = (np.einsum("tb,b->t", d[k], w) for k in ("Xp", "Xn", "Xh"))
    Xt = Xp + Xn + Xh
    Lf = 1e3 * r.film_thickness(Xt)
    ra = np.array([r.areal_rate(row) for row in y])
    q = pd.read_csv(os.path.join(HERE, "aperture_quantiles.csv"))
    key = (q.geometry_kind == g.geometry_kind) & (q.wall_mm == g.wall_mm) & \
          (q.feature_mm.fillna(-1) == (g.feature_mm if g.feature_mm == g.feature_mm else -1))
    ap_q = q[key].sort_values("quantile")
    f_occ = OC.f_occluded(Lf, ap_q.aperture_mm.values, ap_q["quantile"].values)
    f_col = OC.f_colonised(Xt)
    rv = g.a_geo_m2_m3 * f_col * (1 - f_occ) * ra

    mode = "bench rig, closed batch" if a.rig else "screening, bulk held at feed"
    print(f"\n{NAME[a.material]} / {a.geometry}   ({mode})")
    print(f"  wetted area {g.a_geo_m2_m3:7.1f} m2/m3   carrier mass {g.carrier_mass_kg_m3:6.1f} kg/m3"
          f"   photoperiod {a.light:.2f} h/d   {a.temp:.0f} C")
    print(f"\n{'day':>5} {'Xp':>7} {'Xn':>7} {'Xh':>7} {'L_f mm':>8} {'r_a':>7} {'r_v':>9} "
          f"{'NH3-N':>7} {'BOD5':>6} {'f_occ':>6}")
    for day in [0, 3, 7, 10, 28, 60]:
        if day > a.days:
            break
        i = int(np.argmin(abs(t - day)))
        print(f"{day:5d} {Xp[i]:7.2f} {Xn[i]:7.2f} {Xh[i]:7.2f} {Lf[i]:8.3f} {ra[i]:7.3f} "
              f"{rv[i]:9.1f} {d['Snh'][i]:7.2f} {d['Sb'][i]:6.2f} {f_occ[i]:6.3f}")
    print("\n  r_a  g N m-2 d-1 (per colonised, non-occluded area);  r_v  g N m-3 d-1")

    fig, axs = plt.subplots(1, 3, figsize=(11, 3.2))
    for v, c, lab in ((Xh, "#D55E00", "heterotrophs"), (Xn, "#0072B2", "nitrifiers"),
                      (Xp, "#009E73", "phototrophs")):
        axs[0].plot(t, v, color=c, lw=1.6, label=lab)
    axs[0].set_xlabel("day"); axs[0].set_ylabel("areal biomass (g DW m$^{-2}$)")
    axs[0].legend(frameon=False, fontsize=8)
    axs[1].plot(t, d["Snh"], color="#0072B2", label="NH$_3$-N")
    axs[1].plot(t, d["Sno"], color="#56B4E9", ls="--", label="NO$_3$-N")
    axs[1].plot(t, d["Sb"], color="#D55E00", label="BOD$_5$")
    axs[1].set_xlabel("day"); axs[1].set_ylabel("bulk (mg L$^{-1}$)")
    axs[1].legend(frameon=False, fontsize=8)
    axs[2].plot(t, Lf, color="#08519C")
    axs[2].axhspan(0.151, 0.412, color="#08519C", alpha=0.10, lw=0)
    axs[2].set_xlabel("day"); axs[2].set_ylabel("film thickness (mm)")
    axs[2].set_title("shaded: measured RBC film", fontsize=8, loc="left")
    fig.suptitle(f"{NAME[a.material]} / {a.geometry} - {mode}", fontsize=10)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, a.out), dpi=150)
    print(f"  figure -> {os.path.join(HERE, a.out)}\n")


if __name__ == "__main__":
    main()
