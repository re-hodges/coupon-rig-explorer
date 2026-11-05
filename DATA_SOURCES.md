# Data sources

Everything the model consumes, grouped by **what kind of evidence it is**. The categories run
from strongest to weakest, and the last two are the ones that limit what the model can claim.

> **Read this first.** `K_comp` is the **most influential parameter in the model by every
> independent analysis** on the Sensitivity tab, all of them now computed on the differential
> equations themselves — Morris elementary effects (μ* = 0.934, rank 1 of 19), **exact Shapley
> values by complete coalition enumeration** (mean |φ| = 0.119 g N m⁻² d⁻¹, rank 1 of 8), and
> **Sobol' indices on the ODE** (S_T = 0.476 ± 0.123, rank 1 of 20) — and **it has no source at
> all**. It is also the only input whose S_T interval separates from the next input's at 95 %.
> The next most influential sourced parameter, `rN_ref`, comes from a membrane-aerated reactor
> rather than an RBC. Influence and evidence are close to inversely ordered here, and that is
> the main limitation on the model's quantitative claims.

## 1. Field records — Apple Springs plant

The operating envelope. These are records of the real plant, not literature.

| What | Used for | Note |
|---|---|---|
| Discharge permit SD0028620 | effluent limits, monitoring frequency | the 1.6 mg N/L ammonia limit the study is judged against |
| Laboratory results 2023–2026 | influent and effluent characterization | ~190 effluent samples; only two influent samples |
| One-minute flow logger, Oct 2025 – Aug 2026 | hydraulic loading | 294 complete days; median 3,660 gal/d, max day 17,040 gal |
| Technical memorandum (Primodal) | film wet density 1.426 g/cm³; BOD onto the RBCs ≈100 mg/L | |
| Operator report | rotation rate 4 rpm; media is plastic | verbal, 4 Nov 2026 |
| **RBC 1 rig description (Anthony)** | the whole mounting geometry: two rotating steel end plates **6 ft apart**; two steel **bands** at 0° and 180° running plate to plate; **divots** in the bands holding **9 coupons each**, one material per divot; **3 coupons harvested on each of days 5, 7, 10**; two divots per material, one per photoperiod; lamps in **six round holes in the cover, three at each end**; coupon **1 9/16 in square**; magnets **3/4 in**; pilot runs **indoors under the cover**, so there is no ambient daylight | relayed 4 Nov 2026. This replaced the earlier design in which boards were magnet-mounted on each **face** of the wheel. |

## 2. Measured by the team

| What | Value | Note |
|---|---|---|
| Coupon dimensions, as fabricated | 36.2 ± 0.3 × 39.6 ± 0.1 mm | photogrammetry from the scale photograph at 26.8 px/mm over ten cut lines, ±1 mm systematic. The 39.6 mm axis **matches the 1 9/16 in specification to 0.1 mm**; the other is ~3.5 mm narrow. The simulator uses the square specification, so a result read against it is biased ~9.9 % low. |
| Graphene coating, Raman | I(D)/I(G) = 0.55, I(2D)/I(G) = 1.33 | few-layer graphene with substantial defect density |
| Graphene coating coverage | dark phase ≈45% of a 100× field | optical contrast, phase not confirmed by Raman mapping |

**Not yet measured:** every RBC site dimension, coupon roughness, coupon contact angle, bulk
dissolved oxygen, and the fabric's true fiber area.

## 3. Plant-level reference model

Values inherited from the plant-scale model rather than measured. Legitimate as defaults;
each is an assumption in that model too.

| Parameter | Source | Note |
|---|---|---|
| `mu_max_h` 3.2 d⁻¹ | Copp (2024) plant model at 20 °C | replaced 5.5 d⁻¹ from Wolf et al. (2007) |
| `D_O2_eff`, `D_S_eff` | Copp (2024), water value × 0.5 biofilm reduction | |
| `K_O_A`, `K_O_H` | Copp (2024) plant model | |
| `rho_film_wet`, `moisture` | Copp (2024) Table 1 | **an assumption in the plant model, not a measurement** — replacing it is one purpose of this study |
| `S_O_bulk` upper bound | plant model saturation at 20 °C, 9.09 mg/L | |

## 4. Peer-reviewed literature

| Source | Supplies | Full text? |
|---|---|---|
| Gross, Zhao, Mascarenhas & Wen 2016, [doi:10.1186/s13068-016-0451-z](https://doi.org/10.1186/s13068-016-0451-z) | material colonization factors (FAB 14.73, PE 1.0, STL/GRA 0.53); `I0`; roughness ratio r as the attachment texture variable | **yes** |
| Hassard et al. 2014, [doi:10.1016/j.psep.2014.07.003](https://doi.org/10.1016/j.psep.2014.07.003) | the 151–412 µm RBC film band, and through it `X_cap` | **yes** |
| Rittmann 1982, [doi:10.1002/bit.260240219](https://doi.org/10.1002/bit.260240219) | shear-dependent detachment, exponent 0.58 | **yes** |
| Peyton & Characklis 1993, [doi:10.1002/bit.260410707](https://doi.org/10.1002/bit.260410707) | the counter-position that shear has no significant effect | **yes** |
| Wenzel 1936, [doi:10.1021/ie50320a024](https://doi.org/10.1021/ie50320a024) | the roughness factor r = actual / geometric surface | **yes** |
| Pawlus, Reizer & Wieczorowski 2021, [doi:10.3390/ma14185326](https://doi.org/10.3390/ma14185326) | Sdq / Sdr definitions and Sdr ≈ Sdq²/2 | **yes** |
| Wolf et al. 2007 | `K_N_p`, `K_N_n`, `Y_n`, `K_S_h`, `Y_h`, `b_n`, `b_h`, `Xn_ref` | — |
| Németh et al. 2023 | `rN_ref` 4.2 g N m⁻² d⁻¹, `theta_n` 1.025 | **membrane-aerated reactor, not an RBC** |
| Henze et al. 2000 (IWA ASM) | decay forms, `theta` convention | suspended growth, not measured on a biofilm |
| Romeu et al. 2022 (Coatings 12:1775) | graphene maturation, 44% wet-weight reduction at 7 weeks | |
| Sousa-Cardoso et al. 2023 (Nanomaterials 13:381) | graphene early-effect time points | |
| Boelee et al. 2011 | `fN_p`, `fP_p`, nutrient-replete biofilm | |
| Edmundson & Huesemann 2015 | `b_p`, night biomass loss | |
| Ma et al. 2023 | `k_abs` 0.18–0.29 m² g⁻¹ DW | |
| Baranyi & Roberts 1994 | lag form (switched **off** by default) | |
| Horn, Reiff & Morgenroth 2003, [doi:10.1002/bit.10503](https://doi.org/10.1002/bit.10503) | thickness- and growth-rate-based detachment forms | **no — abstract only** |

Roughness and texture entries draw on a 23-record reference set; **four are held in full text**,
the rest at abstract level. **No ISO or ASME standard has been obtained in any form**, so every
areal-parameter name rests on a secondary review.

## 5. Calibrated against data

Not independent inputs — fitted so the model reproduces a measurement.

| Parameter | Fitted to |
|---|---|
| `mu_max_p` 4.53 d⁻¹ | the Gross et al. (2016) seven-day areal biomass |
| `gra_onset_d` 5.9 d, `gra_tau_d` 12.8 d | 7 published time points from Romeu 2022 and Sousa-Cardoso 2023; RMSE 9.5 → 5.2 percentage points |

## 6. Computed, not sourced

Derived by arithmetic from geometry or astronomy. No measurement uncertainty beyond their inputs.

| Quantity | How |
|---|---|
| Waterline depth 0.1577 R | solving the circular-segment area for 40% submergence |
| `f_wet` per mount radius | ½ + arcsin(−uR/r)/π |
| Photoperiods 15.50 / 8.87 h | sunrise-to-sunset at Rapid City, 44.0805 °N, solstices, standard refraction |
| Delivered light | timer hours × (1 − `f_wet`) |
| Wall shear `τ_w` | von Kármán laminar rotating-disc result |
| O₂ penetration per pass | √(2 D t) over the emergent dwell |
| `a_geo`, porosity, apertures | marching cubes and a distance transform on a voxel representative volume |
| Coupon `A_exp` 12.901 cm² | one 39.6875 mm face (15.751 cm²) less one 19.05 mm magnet footprint (2.850 cm²) |
| Band `f_wet` 0.4469 | the `f_wet` formula at the band radius r/R = 0.95 |

## 7. This study's choices

Declared decisions, defensible but not derived from a source.

`delta_S_floor` 50 µm · occlusion begins at half the local aperture · sheet stacking gap 11 mm ·
corrugation and pleat depth 4 mm · printed wall 1.0 mm · bed depth 60 mm for the irradiance
comparison · `capacity_headroom` 1.25 · six irradiance bins · `n_shear` sampled over {0, 0.5, 1} ·
`phi_shear` sampled over {0.3, 0.5, 1.0} · the underside crevice and the coupon edges excluded
from the denominator · **no optical cross-contamination between the two ends** (directed 4 Nov
2026; carried as a limitation, and it makes the photoperiod contrast an upper bound)

## 8. No source

The honest category. Each is a number the model needs and nobody has measured.

Ranks are against day-60 areal removal flux `J_A`, from the Sensitivity tab. **Every column is
computed on the differential equations.** Morris μ* uses 19 continuous inputs (material fixed at
HDPE); Sobol' S_T uses all 20; exact Shapley covers the 8 highest-μ* inputs by complete 2⁸
coalition enumeration, so inputs outside that set show "—" rather than a small number.

| Parameter | Value | Morris μ* (rank) | exact Shapley mean &#124;φ&#124; (rank) | Sobol' S_T (rank) | Status |
|---|---|---|---|---|---|
| `K_comp` | 5.0 g DW m⁻² | **0.934 — rank 1 of 19** | **0.119 — rank 1 of 8** | **0.476 ± 0.123 — rank 1 of 20** | **no source at all**; heterotroph suppression of nitrifiers has not been measured here. The only input whose S_T interval separates from the next at 95 %. |
| `k_det` | 0.05 d⁻¹ | 0.304 — rank 6 | 0.103 — rank 2 of 8 | 0.150 ± 0.068 — rank 5 | no source |
| **`phi_shear`** | **0.3 / 0.5 / 1.0 sampled** | **0.290 — rank 7** | 0.023 — rank 8 of 8 | 0.009 ± 0.004 — rank 10 | **no source at all.** New with the band-mounted rig: nothing measures how much a recessed coupon is sheltered. Morris rates it far higher than Sobol' does, which means its influence is local rather than variance-dominant. |
| `k_att` | 1.0 g DW m⁻² d⁻¹ | 0.275 — rank 8 | 0.067 — rank 6 of 8 | 0.083 ± 0.040 — rank 7 | no source; anchored to reproduce earlier behavior |
| `K_I` | 50 µmol m⁻² s⁻¹ | 0.021 — rank 14 | — | 0.0002 — rank 15 | typical microalgal value, no source paper; swept 25–100 |
| `K_P_p` | 0.02 g P m⁻³ | 0.0003 — rank 19 | — | 0.0000 — rank 20 | typical microalgal value, no source paper |
| `K_pl`, `b_pl` | 0.5, 0.1 | not sampled | — | not sampled | no source |
| `seed_frac` | 0.02 | not sampled | — | not sampled | no source |
| `Xp0 : Xn0 : Xh0` | 0.5 : 0.2 : 0.3 | not sampled | — | not sampled | placeholder pending metagenomic analysis of public datasets |


**Two unsourced parameters now sit in the top seven by Morris μ*** — `K_comp` at rank 1 and the
new `phi_shear` at rank 7. `X_cap`, which ranks 2nd, **is** sourced (Hassard et al. 2014), as is
`rN_ref` at rank 3, with the reactor-type caveat above.

### Rig geometry placeholders

Best estimates so the model can run, flagged as placeholders wherever they appear:

| Quantity | Placeholder |
|---|---|
| media disc / end-plate diameter | 2.00 m |
| band radius | r/R = 0.95 |
| divots per band | 4, two near each end |
| divot cavity | 140 × 140 mm, 10 mm deep |
| coupon recess below the band face | 3 mm |
| divot light view factor | 0.90 |
| magnet thickness | 6.35 mm (diameter 19.05 mm **is** reported) |
| lamp height above the waterline | 0.50 m |
| cover hole diameter | 150 mm |
| bulk dissolved oxygen | from `params_v2.yaml`, assumed |
| per-material roughness ratios | 1.01 / 1.02 / 1.02 / undefined |
| assay mass thresholds | 1.0 / 0.5 / 0.05 mg |

## What would most improve the evidence base

1. **Measure or bound `K_comp`.** It dominates the sensitivity and has no source; no other single
   change improves the model as much.
2. **An RBC-derived areal nitrification rate** to replace `rN_ref`, which currently comes from a
   different reactor type.
3. **Divot depth and the shelter factor it implies.** `phi_shear` enters the model with no source
   and the grid shows it worth a factor of 2.2–2.6 on day-60 flux once shear acts at all. A tape
   measure in the divot would retire the largest new unknown this rig introduced.
4. **The remaining site measurements** in `FIELD_MEASUREMENTS_RBC1.md` — end-plate diameter and
   the band radius first, since together they set the duty cycle and the shear.
5. **ISO 25178-2**, so the areal parameters rest on the standard rather than a review.
