"""Variable key + evidence scoring for every input in the sensitivity analyses.

Writes sa_evidence.csv, which does two jobs:

  1. It is the KEY printed at the bottom of the Sensitivity tab: what each symbol means,
     its units, its nominal value, the range it was swept over, and where the number
     came from.
  2. It is the CONFIDENCE axis of the impact-versus-evidence diagram. Impact says how
     far the output moves; this says how much the input is worth believing.

Nominal values are read from params_v2.yaml and sweep ranges from sa_design.py, so the
key cannot drift from what was actually run. Only the prose and the evidence grading
are curated here.

EVIDENCE TIERS are taken verbatim from the categories in DATA_SOURCES.md, which already
orders its sections strongest to weakest. The ordinal score exists so the table can be
plotted; it is a rendering of the tier, not an independent judgement:

    4  measured here            instrumented measurement on this system
    3  field record             reported for this plant/rig, or peer-reviewed
                                literature on the SAME system type (an RBC biofilm)
    3  computed (exact)         derived by arithmetic from geometry or astronomy
    2  literature (analogue)    peer-reviewed, but a different system type
    2  calibrated               fitted so the model reproduces a published measurement
    2  computed (stoichiometric) estimated from an assumed biomass formula
    1  plant reference model    inherited from the plant-scale model; an assumption there too
    1  study choice             a declared decision of this study, defensible but underived
    0  no source                nobody has measured it

A reviewer who disagrees with a grade can re-score one column and redraw the figure.
"""
import os, sys
import numpy as np, pandas as pd, yaml

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sa_design as SD
import sa_labels as LB

PAR = yaml.safe_load(open(os.path.join(HERE, "params_v2.yaml"), encoding="utf-8"))["parameters"]

TIER_SCORE = {
    "measured here": 4, "field record": 3, "computed (exact)": 3,
    "literature (analogue)": 2, "calibrated": 2, "computed (stoichiometric)": 2,
    "plant reference model": 1, "study choice": 1, "no source": 0,
}

# symbol, label, units, domain, tier, source, definition
KEY = [
 ("K_comp", "K_comp", "g DW m-2", "biological", "no source",
  "None. Heterotroph suppression of nitrifiers has not been measured on this system.",
  "Half-saturation of heterotroph crowding on nitrification. Nitrification is multiplied "
  "by K_comp/(K_comp+Xh), so when heterotroph areal biomass reaches K_comp the modelled "
  "nitrification rate is halved."),
 ("X_cap", "X_cap", "g DW m-2", "surface", "field record",
  "Hassard et al. 2014 (doi:10.1016/j.psep.2014.07.003), the 151-412 um film band "
  "measured on RBC media; full text held.",
  "Carrying capacity of the film: the total areal biomass at which the shared capacity "
  "term closes and no guild can grow further. ASM/Wanner-Gujer call this X_max."),
 ("rN_ref", "r_N,ref", "g N m-2 d-1", "biological", "literature (analogue)",
  "Nemeth et al. 2023 -- a MEMBRANE-AERATED reactor, not an RBC. Reactor type differs "
  "from ours; full-text status not asserted in DATA_SOURCES.md.",
  "Reference areal nitrification rate at 20 C and reference nitrifier biomass. The "
  "multiplicative anchor of the whole flux chain: every other term scales it."),
 ("rpm", "n", "min-1", "environmental", "field record",
  "Operator report, 4 rpm as presently run (verbal, 4 Nov 2026). Not instrumented.",
  "Wheel rotation rate. Sets the submerged/emergent duty cycle and, through the "
  "rotating-disc correlation, the wall shear the coupon feels."),
 ("n_shear", "n_shear", "-", "environmental", "literature (analogue)",
  "Contested: Rittmann 1982 (doi:10.1002/bit.260240219) gives exponent 0.58; Peyton & "
  "Characklis 1993 (doi:10.1002/bit.260410707) find no significant shear effect. Both "
  "held in full text. Swept 0-1 rather than fixed because the literature disagrees.",
  "Exponent in k_det proportional to tau^n_shear. Zero means detachment ignores shear; "
  "one means it scales linearly with it."),
 ("k_det", "k_det", "d-1", "biological", "no source",
  "None.",
  "First-order detachment coefficient: the fraction of film lost per day before the "
  "shear modifier is applied."),
 ("shelter", "phi_shear", "-", "environmental", "no source",
  "None at all. New with the band-mounted rig -- nothing measures how much a recessed "
  "coupon is sheltered from the free-stream.",
  "Divot shelter factor on wall shear. 1.0 is a coupon flush with the band; smaller "
  "values a deeper recess feeling less shear."),
 ("k_att", "k_att", "g DW m-2 d-1", "surface", "no source",
  "None; anchored so that HDPE gains in one day the areal biomass v2 previously imposed "
  "as its initial condition.",
  "Areal attachment flux onto bare HDPE. The material factor multiplies it."),
 ("Sb", "S_b", "g m-3", "environmental", "field record",
  "Two influent samples only (BOD5 72-120 mg/L) plus the Primodal technical memorandum's "
  "~100 mg/L onto the RBCs. The weakest field input -- n = 2.",
  "Biodegradable organic substrate reaching the first stage, carried as BOD5. Feeds the "
  "heterotrophs, which then crowd the nitrifiers."),
 ("theta_h", "theta_h", "-", "biological", "literature (analogue)",
  "Henze et al. 2000 (IWA ASM) convention -- suspended growth, not measured on a biofilm.",
  "Arrhenius temperature coefficient for heterotrophs. Inert in every result reported "
  "here: all runs are isothermal at 15 C."),
 ("b_p", "b_p", "d-1", "biological", "literature (analogue)",
  "Edmundson & Huesemann 2015, night biomass loss in microalgae.",
  "Phototroph decay/maintenance coefficient, including dark respiration losses."),
 ("D_O2_eff", "D_O2,eff", "m2 d-1", "environmental", "plant reference model",
  "Copp (2024) plant model: the water value halved for the biofilm. An assumption in "
  "that model too.",
  "Effective oxygen diffusivity inside the film. Sets the penetration depth delta = "
  "sqrt(2 D S / R_v) and so the oxygen effectiveness factor eta_O2."),
 ("I0", "I_0", "umol m-2 s-1", "environmental", "literature (analogue)",
  "Gross, Zhao, Mascarenhas & Wen 2016 (doi:10.1186/s13068-016-0451-z); full text held.",
  "Incident photon flux density at the coupon surface before the divot view factor."),
 ("S_O_bulk", "S_O", "g O2 m-3", "environmental", "plant reference model",
  "Copp (2024) plant model saturation at 20 C (9.09 mg/L) as the upper bound. Bulk "
  "dissolved oxygen on this rig is listed as NOT YET MEASURED.",
  "Imposed bulk dissolved oxygen. A boundary condition, never a state variable."),
 ("theta_p", "theta_p", "-", "biological", "literature (analogue)",
  "Henze et al. 2000 (IWA ASM) convention -- suspended growth, not measured on a biofilm.",
  "Arrhenius temperature coefficient for phototrophs. Inert in every result reported "
  "here: all runs are isothermal at 15 C."),
 ("Y_O2_p", "Y_O2,p", "g O2 g-1 DW", "biological", "computed (stoichiometric)",
  "Stoichiometric estimate from an assumed biomass formula CH1.8O0.5N0.2 (24.63 g/C-mol), "
  "not a measurement.",
  "Oxygen produced per unit phototroph biomass grown. The route by which light could in "
  "principle help nitrification -- and does not, because the film never runs out of oxygen."),
 ("timer_h", "timer_h", "h d-1", "environmental", "computed (exact)",
  "Sunrise-to-sunset at Rapid City (44.0805 N) at the solstices, standard refraction: "
  "15.50 h summer, 8.87 h winter.",
  "Lamp timer setting. Light actually delivered is timer_h x (1 - f_wet), because a "
  "submerged coupon is a dark coupon."),
 ("K_I", "K_I", "umol m-2 s-1", "biological", "no source",
  "None. A typical microalgal value with no source paper behind it.",
  "Half-saturation of the phototroph light response."),
 ("K_P_p", "K_P,p", "g P m-3", "biological", "no source",
  "None. A typical microalgal value with no source paper behind it.",
  "Half-saturation of phototroph phosphorus uptake."),
 ("material", "material", "-", "surface", "literature (analogue)",
  "Gross et al. 2016 seven-day areal biomass (fabric 91.2, HDPE 6.2, steel 3.3 g DW m-2), "
  "used as colonization factors. CAVEAT: this is a net seven-day retention ratio, not an "
  "attachment rate, and the fabric's fibre-scale area is absent from the model, so unmeasured "
  "area is currently being read as a material effect.",
  "Coupon material: HDPE (PE), bare steel (STL), graphene-coated steel (GRA) or fabric "
  "(FAB). Enters only through the attachment factor and, for GRA, a maturation factor."),
]


def build():
    rows = []
    for sym, label, units, domain, tier, source, defn in KEY:
        if sym == "material":
            nominal, lo, hi, samp = "PE (baseline)", np.nan, np.nan, "4 levels: PE/STL/GRA/FAB"
        elif sym in SD.LOGU:
            lo, hi = SD.LOGU[sym]
            nominal, samp = PAR[sym], "log-uniform"
        else:
            lo, hi = SD.UNIF[sym]
            nominal, samp = "", "uniform"
        rows.append(dict(
            parameter=sym, symbol=label, units=units, domain=domain,
            display_name=LB.long(sym), short_label=LB.short(sym),
            role_in_model=LB.role(sym),
            nominal=nominal, range_lo=lo, range_hi=hi, sampling=samp,
            evidence_tier=tier, evidence_score=TIER_SCORE[tier],
            source=source, definition=defn))
    d = pd.DataFrame(rows)
    # attach the model-truth impact measure already computed on the ODE
    mo = pd.read_csv(os.path.join(HERE, "sa_morris.csv"))
    d = d.merge(mo[["parameter", "mu_star", "sigma"]], on="parameter", how="left")
    d["mu_star_rank"] = d.mu_star.rank(ascending=False, method="min")
    return d.sort_values("mu_star", ascending=False, na_position="last")


if __name__ == "__main__":
    d = build()
    assert d.evidence_score.notna().all()
    d.to_csv(os.path.join(HERE, "sa_evidence.csv"), index=False)
    print(d[["parameter", "units", "evidence_tier", "evidence_score",
             "mu_star", "mu_star_rank"]].to_string(index=False))
    print(f"\n{len(d)} inputs; no-source inputs: "
          f"{list(d[d.evidence_score == 0].parameter)}")
