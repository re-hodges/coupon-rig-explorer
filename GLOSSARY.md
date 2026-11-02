# Glossary — coupon-scale biofilm model

Every term the model and the figures use, in plain language, with units and why it
matters. Written for someone who has not worked on this model. Where a term is used
loosely elsewhere in the literature, the entry says so.

---

## The four things that change how much biofilm is on a coupon

A biofilm's mass is set by four processes. Mixing them up is the single easiest
mistake to make when reading results from this model, so they are listed first.

| process | what it is | symbol | units |
|---|---|---|---|
| **attachment** | cells already in the liquid land on the surface and stick | `k_att` | g DW m⁻² d⁻¹ |
| **growth** | cells already attached divide, using nutrients and light | `mu_max_*` | d⁻¹ |
| **decay** | attached cells die or burn biomass on maintenance | `b_*` | d⁻¹ |
| **detachment** | film sloughs or erodes back off into the liquid | `k_det` | d⁻¹ |

**Attachment rate (`k_att`) is biofilm attachment in the ordinary sense** — arrival
and sticking, not growth. It is an areal flux: grams of dry biomass arriving per
square meter of carrier per day. In this model attachment draws from a finite
suspended pool, so it *moves* cells onto the surface rather than creating them.

**A caution about the Gross et al. (2016) material factors.** That study measured the
*biomass present on a coupon after seven days* (fabric 91.2, HDPE 6.2, steel 3.3
g DW m⁻²). That number is the net outcome of all four processes above — it is **not**
a measurement of attachment alone. Earlier versions of this model called the ratio an
"attachment rate"; that was an interpretation, and this model's own results do not
support it (see `COUPON_MODEL_SPEC.md`). It is more accurately a **seven-day net
retention ratio**, and which of the four processes produces it is still open.

---

## Biomass and the film

| term | symbol | units | meaning |
|---|---|---|---|
| **Areal biomass** | `X` | g DW m⁻² | dry weight of biofilm per square meter of carrier. What a scraped-and-dried coupon weighs. |
| **Dry weight (DW)** | — | g | biomass after drying off the water. A wet film is roughly 90 % water, so wet and dry weights differ by about tenfold. |
| **Guild** | — | — | a functional group of organisms, grouped by what they do rather than what they are. This model has three. |
| **Phototrophs** | `Xp` | g DW m⁻² | algae and cyanobacteria. Use light, release oxygen. |
| **Nitrifiers** | `Xn` | g DW m⁻² | bacteria that oxidize ammonia to nitrate. Slow-growing, oxygen-hungry — these are the ones the permit depends on. |
| **Heterotrophs** | `Xh` | g DW m⁻² | bacteria that eat organic carbon (BOD). Fast-growing; they crowd nitrifiers out of the outer film. |
| **Suspended pool** | `Xpl` | g DW m⁻² of carrier | cells in the liquid, not yet attached. The inoculum starts here. Multiply by `a_v` to get the concentration a liquid sample would show. |
| **Carrying capacity** | `X_cap` | g DW m⁻² | the most biofilm a square meter of carrier will hold before it stops accumulating. A ceiling, not a rate. Currently the same for every material. |
| **Film thickness** | `L_f` | mm | how deep the film is. Converted from areal biomass using the film's wet density and moisture. Measured coupons sat at 0.151–0.412 mm. |

---

## Rates — what the carrier actually does

| term | symbol | units | meaning |
|---|---|---|---|
| **Areal rate** | `r_a` | g N m⁻² d⁻¹ | ammonia removed per square meter of **colonized, non-occluded** carrier per day. The "colonized, non-occluded" part matters: bare and blocked surface is already excluded, so multiplying by the colonized fraction again would double-count the same loss. |
| **Volumetric rate** | `r_v` | g N m⁻³ d⁻¹ | the same removal per cubic meter of installed media. **This is the number that decides a retrofit**, because a tank has a fixed volume. |

---

## Area — the heart of the geometry argument

A carrier's catalog area and its useful area are not the same number, and the gap
between them is what the geometry axis is about.

| term | symbol | units | meaning |
|---|---|---|---|
| **Geometric specific area** | `a_geo` | m² m⁻³ | total carrier surface per cubic meter of media, straight off the geometry. The brochure number. |
| **Effective specific area** | `a_eff` | m² m⁻³ | the share of that which is actually colonized **and** still reachable. |
| **Illuminated specific area** | `a_ill` | m² m⁻³ | the share that is colonized, reachable **and** receiving light. The quantity Hypothesis 1 is framed on. |
| **Colonized fraction** | `f_col` | — (0–1) | share of surface carrying enough biomass to count as colonized. |
| **Occluded fraction** | `f_occ` | — (0–1) | share of pores bridged shut by the growing film, cutting off the surface behind them. Exploratory and simulation-only by ruling — it sits outside the headline ranking. |
| **Aperture** | — | mm | the width of the gap between neighboring carrier surfaces. A film roughly half an aperture wide will bridge it. |
| **Wetted vs one-sided area** | — | m² m⁻³ | a sheet has two faces. The project's tabulated gyroid areas are the **one-sided** minimal surface; wetted area (both faces) is about double. Mixing the two is a factor-of-two error. |

---

## Transport and limitation

| term | symbol | units | meaning |
|---|---|---|---|
| **Penetration depth** | `δ` | mm | how far a dissolved substance gets into the film before it is used up. Biomass deeper than this is not working. |
| **Oxygen effectiveness factor** | `η_O₂` | — (0–1) | the share of the film that oxygen actually reaches. 1.0 means fully oxic; a thick film is mostly anoxic. |
| **Effective diffusivity** | `D_*_eff` | m² d⁻¹ | how fast a substance moves *through biofilm*, which is slower than through water. |
| **Half-saturation constant** | `K_*` | mg L⁻¹ | the concentration at which a process runs at half its maximum speed. Low value = the organism copes with scarcity. |
| **Monod kinetics** | — | — | the standard rate law: rate rises with concentration, then flattens. `S/(K+S)`. |
| **Arrhenius / theta (θ)** | `theta_*` | — | the factor a rate changes by per °C. θ = 1.025 means +2.5 % per degree. |
| **Wetted fraction** | `f_wet` | — (0–1) | share of time or area in contact with liquid. |
| **Yield** | `Y_*` | g g⁻¹ | biomass made per unit of substrate consumed. |

---

## Experiment and operation

| term | meaning |
|---|---|
| **Coupon** | a small test piece of carrier material, harvested and weighed at intervals. |
| **Arm** | one combination of material × geometry × photoperiod — a single experimental condition. |
| **RBC** | rotating biological contactor. Discs on a shaft, half-submerged, turning slowly so the film is alternately in water and in air. |
| **Photoperiod** | hours of light per day. The experiment uses Fairbanks (5.0 h), Sturgis (9.2 h), Key West (10.8 h) and a Part 1 fixed value (9.7 h). |
| **As-built protocol** | the rig as currently configured: a closed vessel, filled once, nothing replenished. |
| **Fed protocol** | the proposed alternative: the liquid is replaced daily, which also washes out suspended cells. |
| **Ensemble** | the model run many times with different draws of the uncertain parameters, so a result can be quoted with a range rather than a single number. |
| **Morris screening** | a method that ranks which parameters matter most. `μ*` is the average size of a parameter's effect; `σ` shows whether that effect depends on the other parameters. It ranks; it does not apportion variance. |

---

## Materials

| code | material |
|---|---|
| `FAB` | non-woven fabric (AlgaFilm) |
| `STL` | bare steel |
| `GRA` | graphene-coated steel |
| `PE` | HDPE |
