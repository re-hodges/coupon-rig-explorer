"""EXACT multiplicative decomposition of the day-60 areal removal flux.

J_A is a product of terms, so in logarithms it is a SUM of terms, and a sum decomposes
with no residual and no attribution scheme required. This gives a per-arm waterfall that
is a complete account of one prediction -- what a SHAP waterfall approximates, computed
exactly -- and it attributes to the PHYSICS TERMS rather than to the parameters behind
them.

Structure of the rate (reactor.areal_rate):

    J_A = SUM_b  w_b * rN_b * eta_b

    rN_b = rN_ref * (Xn_b/Xn_ref) * [Snh/(K_N_n+Snh)] * theta_n^(T-20)
                  * f_comp_b * f_wet * [S_O/(K_O_A+S_O)] * free_b

Five of those factors carry NO bin index -- rN_ref, the ammonia Monod term, the Arrhenius
factor, f_wet and the oxygen Monod term are scalars. They factor straight out of the sum
and contribute exactly.

The four bin-dependent factors (nitrifier biomass ratio, heterotroph crowding, remaining
film space, oxygen effectiveness) cannot be factored out of a sum of products, so they
are decomposed by a CHAIN of partial sums:

    S0 = SUM_b w_b
    S1 = SUM_b w_b (Xn_b/Xn_ref)
    S2 = SUM_b w_b (Xn_b/Xn_ref) f_comp_b
    S3 = SUM_b w_b (Xn_b/Xn_ref) f_comp_b free_b
    S4 = SUM_b w_b (Xn_b/Xn_ref) f_comp_b free_b eta_b

and each factor's contribution is the ratio S_k/S_(k-1). The product telescopes exactly,
so the decomposition is exact to machine precision. It is ORDER-DEPENDENT: each
bin-dependent factor is credited with its effect GIVEN the ones before it in the chain.
The order used is the physical reading order of the rate expression, and it is stated on
the figure. (This is the same order-dependence a Shapley value exists to remove, which is
why both decompositions are reported: Shapley over parameters, chain over mechanisms.)
"""
import os, sys
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sa_worker as W
from reactor import F_O2_N
from reactor_v2 import RBCReactor
import area as AR

DAYS, TEMP, NOUT, SUBSTEP = 60.0, 15.0, 241, 240.0
BAND_R_OVER_R, D_DISC_M, VIEW_FACTOR = 0.95, 2.0, 0.90

LABELS = [
    ("rN_ref",      "reference areal rate $r_{N,ref}$"),
    ("ammonia",     "ammonia Monod"),
    ("arrhenius",   "temperature $\\theta_n^{(T-20)}$"),
    ("f_wet",       "wetted fraction $f_{wet}$"),
    ("oxy_monod",   "bulk oxygen Monod"),
    ("Xn_ratio",    "nitrifier biomass ratio"),
    ("crowding",    "heterotroph crowding $f_{comp}$"),
    ("free_space",  "remaining film space"),
    ("eta_O2",      "oxygen effectiveness $\\eta_{O_2}$"),
]


def build(row):
    """Reactor for one design row, mirroring sa_worker.run_point exactly."""
    mat = row["material"]
    geo = W.FLAT.get(mat, "Flat plate")
    g = W.CAT[(W.CAT.material == mat) & (W.CAT.geometry == geo)].iloc[0]
    b = W.IB[(W.IB.material == mat) & (W.IB.geometry == geo)].sort_values("bin")
    pp = dict(W.PAR)
    for c in W.PARAM_COLS:
        pp[c] = float(row[c])
    r = RBCReactor(pp, b.area_fraction.values, b.rel_irradiance.values,
                   a_v=g.a_geo_m2_m3,
                   attach=(W.XMAX[mat] / W.XMAX["PE"]) * AR.attachment_roughness_factor(mat),
                   bulk_mode="fixed",
                   feed=dict(Snh=30.0, Sno=0.0, Sp=4.0, Sb=float(row["Sb"])),
                   graphene=(mat == "GRA"),
                   rpm=float(row["rpm"]), r_over_R=BAND_R_OVER_R, D_disc_m=D_DISC_M,
                   n_shear=float(row["n_shear"]), phi_shear=float(row["shelter"]),
                   view_factor=VIEW_FACTOR)
    return r


def decompose(row):
    r = build(row)
    t, y, _ = r.simulate_rbc(DAYS, timer_h=float(row["timer_h"]), T=TEMP,
                             n_out=NOUT, substep_min=SUBSTEP)
    i60 = int(np.argmin(abs(t - 60.0)))
    yv = y[i60]
    p, w = r.p, r.w
    d = r.unpack(yv)
    Snh, Xn, Xh = d["Snh"], d["Xn"], d["Xh"]
    SO = p["S_O_bulk"]

    # --- the five scalar factors
    f = {}
    f["rN_ref"] = p["rN_ref"]
    f["ammonia"] = Snh / (p["K_N_n"] + Snh)
    f["arrhenius"] = p["theta_n"] ** (TEMP - 20.0)
    f["f_wet"] = p["f_wet"]
    f["oxy_monod"] = SO / (p["K_O_A"] + SO)

    # --- the four bin-dependent factors, by chained partial sums
    f_comp = p["K_comp"] / (p["K_comp"] + Xh) if p["comp_on"] >= 0.5 else np.ones_like(Xh)
    Xtot = d["Xp"] + d["Xn"] + d["Xh"]
    free = np.maximum(0.0, 1.0 - Xtot / r.cap)
    rN = (f["rN_ref"] * (Xn / p["Xn_ref"]) * f["ammonia"] * f["arrhenius"]
          * f_comp * f["f_wet"] * f["oxy_monod"] * free)
    eta = r.oxygen_factor(r.film_thickness(Xtot), F_O2_N * rN)

    S = [float((w).sum())]
    S.append(float((w * (Xn / p["Xn_ref"])).sum()))
    S.append(float((w * (Xn / p["Xn_ref"]) * f_comp).sum()))
    S.append(float((w * (Xn / p["Xn_ref"]) * f_comp * free).sum()))
    S.append(float((w * (Xn / p["Xn_ref"]) * f_comp * free * eta).sum()))
    for k, nm in enumerate(["Xn_ratio", "crowding", "free_space", "eta_O2"]):
        f[nm] = S[k + 1] / S[k] if S[k] > 0 else 0.0

    JA_decomp = S[0] * np.prod([f[k] for k, _ in LABELS])
    JA_model = float(r.areal_rate(yv, T=TEMP))
    f["_S0"] = S[0]
    f["_JA_decomp"] = JA_decomp
    f["_JA_model"] = JA_model
    f["_rel_residual"] = abs(JA_decomp - JA_model) / max(JA_model, 1e-300)
    return f


def run():
    arms = pd.read_csv(os.path.join(HERE, "sa_ode2_arms.csv"))
    rows = []
    for _, a in arms.iterrows():
        f = decompose(a)
        f["arm"] = int(a["arm"]); f["material"] = a["material"]
        f["JA_d60_qmc"] = float(a["JA_d60"])
        rows.append(f)
        print(f"arm {int(a['arm']):2d} {a['material']}  J_A={f['_JA_model']:.5f}  "
              f"residual={f['_rel_residual']:.2e}")
    d = pd.DataFrame(rows)
    worst = d["_rel_residual"].max()
    assert worst < 1e-10, f"decomposition is not exact: max relative residual {worst:.3e}"
    d.to_csv(os.path.join(HERE, "sa_decomposition.csv"), index=False)
    print(f"\nEXACT: max relative residual over {len(d)} arms = {worst:.2e}")
    return d


if __name__ == "__main__":
    run()
