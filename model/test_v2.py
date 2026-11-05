"""Regression + unit tests for coupon explorer v2.

    python test_v2.py

T1  v2 with rotation_enabled=False reproduces v1 EXACTLY (max |diff| must be 0.0).
T2  wet_fraction reproduces the verified duty-cycle table.
T3  delivered light is capped by the emergent fraction.
T4  n_shear = 0 leaves k_det untouched (the Peyton & Characklis end of the range).
T5  the laminar correlation is flagged out-of-range at 4 rpm on the placeholder disc.
T6  roughness r moves attachment but never the reporting denominator.
T7  a 3-coupon harvest clears the assay minima at the earliest harvest, day 5.
T8  divot shelter scales wall shear and is an identity when the coupon is flush.
T9  the divot view factor dims INTENSITY and leaves delivered hours untouched.
"""
from __future__ import annotations
import os, sys
import numpy as np, pandas as pd, yaml

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from reactor import Reactor
from reactor_v2 import RBCReactor
import rbc

XMAX = {"FAB": 91.16, "STL": 3.27, "GRA": 3.27, "PE": 6.19}

def _arm(material="PE", geometry="Flat plate"):
    cat = pd.read_csv(os.path.join(HERE, "geometry_catalogue.csv"))
    ib  = pd.read_csv(os.path.join(HERE, "irradiance_bins.csv"))
    par = yaml.safe_load(open(os.path.join(HERE, "params_v2.yaml")))["parameters"]
    g = cat[(cat.material == material) & (cat.geometry == geometry)].iloc[0]
    b = ib[(ib.material == material) & (ib.geometry == geometry)].sort_values("bin")
    return par, b, g

def t1_regression():
    par, b, g = _arm()
    kw = dict(a_v=g.a_geo_m2_m3, attach=XMAX["PE"]/XMAX["PE"], bulk_mode="fixed", graphene=False)
    r1 = Reactor(dict(par), b.area_fraction.values, b.rel_irradiance.values, **kw)
    r2 = RBCReactor(dict(par), b.area_fraction.values, b.rel_irradiance.values,
                    rotation_enabled=False, **kw)
    t1, y1 = r1.simulate(30.0, light_h=9.683, T=20.0, n_out=120, substep_min=240.0)
    t2, y2, deliv = r2.simulate_rbc(30.0, timer_h=9.683, T=20.0, n_out=120, substep_min=240.0)
    d = float(np.max(np.abs(y1 - y2)))
    assert y1.shape == y2.shape, "shape mismatch"
    assert d == 0.0, f"v2 did not reproduce v1 exactly: max|diff| = {d:.3e}"
    assert deliv == 9.683
    print(f"T1 regression        PASS   max|y_v1 - y_v2| = {d:.1e}  (exact)")

def t2_wet_fraction():
    exp = {1.00:0.450, 0.90:0.444, 0.85:0.441, 0.60:0.415, 0.55:0.407,
           0.50:0.398, 0.35:0.351, 0.30:0.324, 0.25:0.283, 0.20:0.211}
    worst = 0.0
    for rr, want in exp.items():
        got = float(rbc.wet_fraction(rr))
        worst = max(worst, abs(got - want))
    assert worst < 5e-4, f"wet_fraction drifted: max abs error {worst:.2e}"
    assert abs(rbc.waterline_depth(0.40) - 0.1577) < 1e-4
    print(f"T2 wet fraction      PASS   max abs error vs table = {worst:.1e}")

def t3_light_cap():
    fw = float(rbc.wet_fraction(rbc.RIG["band_r_over_R"][0]))
    for timer in (8.87, 15.50, 24.0):
        d = rbc.delivered_light_h(timer, fw)
        assert d <= 24.0 * (1 - fw) + 1e-12
        assert abs(d - timer * (1 - fw)) < 1e-12
    cap = 24.0 * (1 - fw)
    assert rbc.delivered_light_h(24.0, fw) < 24.0
    print(f"T3 light cap         PASS   ceiling {cap:.2f} h/d at the band (r/R=0.95); "
          f"15.50 h timer -> {rbc.delivered_light_h(15.50, fw):.2f} h delivered")

def t4_shear_identity():
    par, b, g = _arm()
    kw = dict(a_v=g.a_geo_m2_m3, bulk_mode="fixed")
    base = RBCReactor(dict(par), b.area_fraction.values, b.rel_irradiance.values,
                      rpm=4.0, n_shear=0.0, **kw)
    assert base.p["k_det"] == base.k_det_base, "n_shear=0 must leave k_det untouched"
    # radius is now fixed by the band, so the shear ordering is tested across rpm
    at = lambda rpm: RBCReactor(dict(par), b.area_fraction.values, b.rel_irradiance.values,
                                rpm=rpm, n_shear=1.0, **kw).p["k_det"]
    hi, lo = at(4.0), at(0.5)
    assert abs(hi - base.k_det_base) < 1e-12, "4 rpm flush must be the anchor"
    assert lo < hi, "shear ordering wrong"
    print(f"T4 shear modifier    PASS   n=0 identity held; across rpm at n=1, k_det "
          f"{lo:.4f} (0.5 rpm) < {hi:.4f} (4 rpm, = base {base.k_det_base:.4f}) /d")

def t5_regime_flag():
    R = 1.0
    assert rbc.shear_regime_ok(1.0, R) is True or rbc.shear_regime_ok(1.0, R)
    assert not rbc.shear_regime_ok(4.0, R), "4 rpm on D=2.0 m should be flagged"
    par, b, g = _arm()
    r = RBCReactor(dict(par), b.area_fraction.values, b.rel_irradiance.values,
                   a_v=g.a_geo_m2_m3, bulk_mode="fixed", rpm=4.0)
    assert r.duty()["laminar_ok"] is False
    print(f"T5 regime flag       PASS   Re={r.Re:.3e} at 4 rpm -> laminar_ok=False")



# ---------------------------------------------------------------- area tests
def t6_area_convention():
    import area
    A = area.exposed_area_m2()
    want = (0.0396875 ** 2) - np.pi * (0.01905 ** 2) / 4.0
    assert abs(A - want) < 1e-12, "A_exp must be one face net of one magnet"
    assert area.projected_area_m2() == A, "the alias must track A_exp"
    # the guard against the double-count: changing r must NOT move the denominator
    saved = dict(area.R_ROUGHNESS)
    try:
        area.R_ROUGHNESS["PE"] = (1.50, "test", "deliberately large")
        A_after = area.projected_area_m2()
        assert A_after == A, "roughness leaked into the reporting denominator"
        assert abs(area.attachment_roughness_factor("PE") - 1.50) < 1e-12, \
            "r must still act on attachment"
        assert abs(area.true_area_m2("PE") - A * 1.50) < 1e-12
    finally:
        area.R_ROUGHNESS.clear(); area.R_ROUGHNESS.update(saved)
    assert area.true_area_m2("FAB") is None, "A_true must be undefined for the fabric"
    assert area.attachment_roughness_factor("FAB") == 1.0
    print(f"T6 area convention   PASS   A_exp = {A*1e4:.2f} cm2 (one face less magnet); "
          f"r moves attachment, never the denominator")

def t7_assay():
    """Harvest is 3 coupons per material per day, at days 5, 7 and 10."""
    import area
    out = {f"day {d}": area.assay_sufficiency(x) for d, x in
           [(5, 12.5), (7, 13.7), (10, 15.1)]}      # areal biomass from a v3 grid arm
    for d, o in out.items():
        flags = "  ".join(f"{k}={'y' if v else 'n'}" for k, v in o.items()
                          if k not in ("harvest_mg", "n_coupons"))
        print(f"      {d:7s} {o['harvest_mg']:7.2f} mg from {o['n_coupons']} coupons  {flags}")
    assert out["day 10"]["harvest_mg"] > out["day 5"]["harvest_mg"]
    assert all(out["day 5"][k] for k in area.ASSAY_MIN_MG), \
        "the earliest harvest must clear every assay minimum"
    print("T7 assay sufficiency PASS   day 5 clears all three minima (thresholds placeholder)")


def t8_shelter():
    par, b, g = _arm()
    kw = dict(a_v=g.a_geo_m2_m3, bulk_mode="fixed", rpm=4.0, n_shear=1.0)
    flush = RBCReactor(dict(par), b.area_fraction.values, b.rel_irradiance.values,
                       phi_shear=1.0, **kw)
    deep = RBCReactor(dict(par), b.area_fraction.values, b.rel_irradiance.values,
                      phi_shear=0.3, **kw)
    assert abs(flush.p["k_det"] - flush.k_det_base) < 1e-12, \
        "flush at the reference rpm must be the identity"
    assert abs(flush.tau_Pa - flush.tau_free_Pa) < 1e-15
    assert abs(deep.tau_Pa - 0.3 * deep.tau_free_Pa) < 1e-15, "shelter must scale tau"
    assert abs(deep.p["k_det"] - 0.3 * flush.p["k_det"]) < 1e-12, \
        "at n_shear=1, k_det must follow the shelter linearly"
    print(f"T8 divot shelter     PASS   tau {deep.tau_free_Pa:.5f} -> {deep.tau_Pa:.5f} Pa at "
          f"phi=0.3; k_det {flush.p['k_det']:.4f} -> {deep.p['k_det']:.4f} /d")


def t9_view_factor():
    par, b, g = _arm()
    kw = dict(a_v=g.a_geo_m2_m3, bulk_mode="fixed", rpm=4.0)
    full = RBCReactor(dict(par), b.area_fraction.values, b.rel_irradiance.values,
                      view_factor=1.0, **kw)
    dim = RBCReactor(dict(par), b.area_fraction.values, b.rel_irradiance.values,
                     view_factor=0.90, **kw)
    assert abs(dim.p["I0"] - 0.90 * full.p["I0"]) < 1e-12, "view factor must scale I0"
    t_f, y_f, dh_full = full.simulate_rbc(1.0, timer_h=15.50, T=15.0, n_out=2, substep_min=240.0)
    t_d, y_d, dh_dim = dim.simulate_rbc(1.0, timer_h=15.50, T=15.0, n_out=2, substep_min=240.0)
    assert dh_full == dh_dim, "the view factor must NOT change delivered hours"
    assert abs(dh_full - 15.50 * (1 - full.f_wet)) < 1e-12
    print(f"T9 view factor       PASS   I0 {full.p['I0']:.1f} -> {dim.p['I0']:.1f} "
          f"umol m-2 s-1; delivered hours unchanged at {dh_full:.3f} h/d")

if __name__ == "__main__":
    t1_regression(); t2_wet_fraction(); t3_light_cap(); t4_shear_identity(); t5_regime_flag()
    t6_area_convention(); t7_assay(); t8_shelter(); t9_view_factor()
    print("\nall tests passed")
