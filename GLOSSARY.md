# Glossary — coupon explorer

Every symbol the model uses, beside its field-standard equivalent. Where our symbol
departs from the standard the entry says so and gives the reason.

Standards referenced: **IWA ASM** (Activated Sludge Models, Henze et al.) for solutes
and guilds; **Wanner–Gujer** for the film; **ISO 25178** for areal surface texture;
**Wenzel (1936)** for the roughness ratio.


> **Standards caveat.** **No ISO or ASME standard has been obtained in any form** — ISO 25178-2,
> -3, -6 and -600, ISO 21920-2, ISO 16610, ISO 9277 and ASME B46.1 are all paywalled and recorded
> as `NOT OBTAINED` in `standards_needed.csv`. Every ISO number and parameter name below therefore
> comes from reference knowledge or from secondary descriptions in the papers cited, and **must be
> confirmed against the ISO catalog before being cited in a paper.** The parameter definitions
> rest on [Pawlus, Reizer & Wieczorowski (2021)](https://doi.org/10.3390/ma14185326), a peer-reviewed
> review, rather than on the standard text itself.

## Bulk solutes

| ours | standard | standard symbol | units | meaning |
|---|---|---|---|---|
| `Snh` | IWA ASM | `S_NH` | mg N L⁻¹ | ammonia/ammonium nitrogen in the bulk liquid |
| `Sno` | IWA ASM | `S_NO` | mg N L⁻¹ | nitrate + nitrite nitrogen |
| `Sp`  | ASM2 | `S_PO4` | mg P L⁻¹ | orthophosphate |
| `Sb`  | IWA ASM | `S_S` | mg L⁻¹ | biodegradable organic substrate. **Departure:** we carry it as BOD₅ because the plant's records are BOD₅; ASM's `S_S` is a COD fraction. The two are not interchangeable and the conversion is not applied anywhere in this model. |
| — | IWA ASM | `S_O` | mg O₂ L⁻¹ | dissolved oxygen. Ours is `S_O_bulk`, an **imposed boundary condition**, never a state. |

## Guilds and biomass

| ours | standard | standard symbol | units | meaning |
|---|---|---|---|---|
| `X` | — | — | g DW m⁻² | areal dry biomass: what a scraped, dried coupon weighs divided by its projected area |
| `Xn` | IWA ASM | `X_A` | g DW m⁻² | nitrifiers (ASM's autotrophs). The guild the permit depends on. |
| `Xh` | IWA ASM | `X_H` | g DW m⁻² | heterotrophs |
| `Xp` | — | — | g DW m⁻² | phototrophs. **No ASM equivalent** — ASM has no phototrophic guild, which is why this model exists rather than running ASM directly. |
| `Xpl` | — | — | g DW m⁻² of carrier | suspended pool, the inoculum not yet attached. **Departure:** expressed per m² of *carrier*, not per liter, so it stays the same order as the film states; multiply by `a_v` for the concentration a grab sample reads. |
| `X_cap` | — | `X_max` | g DW m⁻² | carrying capacity of the film |

**Areal biomass is tied to whichever area it was divided by.** Here that is always `A_exp`,
the exposed coupon face net of its magnet (see below). A `g DW m⁻²` value is meaningless
without knowing its denominator.

## The film

| ours | standard | standard symbol | units | meaning |
|---|---|---|---|---|
| `Lf` | Wanner–Gujer | `L_F` | m (mm on the page) | biofilm thickness |
| `rho_film_wet` | Wanner–Gujer | `ρ_F` | kg m⁻³ | wet film density, 1.426 g cm⁻³ |
| `JA` | Wanner–Gujer | `j` | g N m⁻² d⁻¹ | **areal removal flux** — the center-panel quantity, and what the coupons genuinely measure |
| `eta_O2` | — | `η` | – | effectiveness factor on aerobic rates from oxygen penetration |
| `delta` | — | `δ` | m | zero-order penetration depth, √(2DS/Rᵥ) |

## Rates and kinetics

| ours | standard | standard symbol | units | meaning |
|---|---|---|---|---|
| `mu_max_p/h` | IWA ASM | `μ_max` | d⁻¹ | maximum specific growth rate |
| `b_p/n/h` | IWA ASM | `b_A`, `b_H` | d⁻¹ | decay/maintenance coefficient |
| `Y_n`, `Y_h` | IWA ASM | `Y_A`, `Y_H` | g DW g⁻¹ | yield |
| `theta_*` | — | `θ` | – | Arrhenius temperature coefficient; nitrification θ ≈ 1.025 |
| `K_*` | IWA ASM | `K_*` | mg L⁻¹ | half-saturation constants |
| `rN_ref` | — | — | g N m⁻² d⁻¹ | reference **areal** nitrification rate. **Departure:** nitrification is carried in an areal form rather than ASM's volumetric Monod form. |
| `k_att` | — | — | g DW m⁻² d⁻¹ | attachment flux coefficient |
| `k_det` | — | — | d⁻¹ | first-order detachment coefficient. In v2 it is shear-modified; see below. |

> **Carried-forward caution on the Gross et al. (2016) material factors.** They measured
> *biomass present after seven days* (fabric 91.2, HDPE 6.2, steel 3.3 g DW m⁻²), which is
> the net outcome of attachment, growth, decay **and** detachment together. Calling it an
> attachment rate is an interpretation the model's own results do not support. It is more
> accurately a **seven-day net retention ratio**.

## RBC mounting and the band rig

| ours | standard | units | meaning |
|---|---|---|---|
| `rpm` | `n` | min⁻¹ | disc rotation rate. 4 rpm as presently run. |
| `omega` | `ω` | rad s⁻¹ | angular velocity, 2πn/60 |
| `r_over_R` | `r/R` | – | mount radius as a fraction of disc radius. **Fixed by hardware at 0.95** — the coupons sit in divots on the steel bands, so this is not a design choice. |
| `shaft_span` | `L` | m | distance between the two end plates, 1.8288 m (6 ft) |
| `f_wet` | – | – | fraction of each **revolution** the coupon is submerged. **Not** the 40 % areal submergence — it is radius-dependent, and at the band it is **0.4469**, so the coupons are emergent 55.3 % of each turn. |
| `tau_free_Pa` | `τ_w` | Pa | free-stream local wall shear, von Kármán laminar rotating-disc form |
| `tau_Pa` | – | Pa | shear the coupon actually feels, `φ_shear · τ_free` |
| `phi_shear` | – | – | **divot shelter factor.** 1.0 is a coupon flush with the band, smaller values a deeper recess. **No source at all** — sampled over 0.3–1.0 rather than fixed. |
| `view_factor` | – | – | fraction of lamp irradiance reaching a recessed coupon, 0.90. Applied to **intensity, never to hours** — applying it to hours would double-count the rotation duty. |
| `Re` | `Re` | – | rotating-disc Reynolds number ωR²/ν; laminar below ≈3 × 10⁵ |
| `n_shear` | `n` | – | exponent in `k_det ∝ τⁿ`. **Sampled across the ensemble, not fixed** — the literature disagrees. |
| `timer_h` | – | h d⁻¹ | lamp timer setting. Photoperiod is set by **axial position**: lamps sit in six cover holes, three at each end. |
| `delivered_h` | – | h d⁻¹ | light the coupon actually receives = `timer_h × (1 − f_wet)`. Submerged means dark. At the band: 8.573 h/d summer, 4.906 h/d winter, against a ceiling of 13.27 h/d. |

**Limitation carried with this block:** optical **cross-contamination between the two ends is
not modeled**. The photoperiod contrast is therefore an upper bound on what the rig delivers.

## Surface area and roughness

| ours | standard | units | meaning |
|---|---|---|---|
| `A_exp` | – | m² | **the sole reporting denominator**: the exposed upper face net of one magnet footprint, 15.751 − 2.850 = **12.901 cm² = 0.001290 m²** |
| `A_crev` | – | m² | underside annulus facing the band floor, 12.901 cm². Wetted and colonizable but unlit and essentially unsheared — **not simulated and not in the denominator**, so every per-coupon figure is a lower bound. |
| `d_mag` | – | mm | magnet diameter, 19.05 mm (3/4 in). Hides 18.1 % of a coupon face. |
| `A_proj` | – | m² | alias for `A_exp`. |
| `r` | Wenzel | – | roughness ratio `1 + Sdr`; the ratio of true to projected area. Acts **only** on attachment, never as an area multiplier. |
| `A_true` | – | m² | `A_exp × r`. Computed and deliberately **unused**; undefined for the fabric. |
| `Sdr` | ISO 25178-2 | % | developed interfacial area ratio — the fractional *increase* in area over the projected area |
| `Sdq` | ISO 25178-2 | – | RMS surface slope. For comparatively smooth surfaces `Sdr ≈ Sdq²/2` |
| `Sa`, `Sq`, `Sz` | ISO 25178-2 | µm | areal height parameters. **These do not determine added area** — height alone says nothing about slope |
| `Sal`, `Str` | ISO 25178-2 | µm, – | autocorrelation length and texture aspect ratio: how wide the features are and whether the texture is directional |
| `a_geo` | – | m² m⁻³ | geometric specific surface area, from the mesh |
| `a_eff` | – | m² m⁻³ | effective specific area, `a_geo · f_col · (1 − f_occ)` |
| `a_v` | – | m² m⁻³ | carrier area per volume of liquid. **Inert here**: with the bulk imposed it multiplies a zero derivative |
| `f_col`, `f_occ` | – | – | colonized and occluded fractions |

**Where these come from.** `r` is [Wenzel's (1936)](https://doi.org/10.1021/ie50320a024) roughness
factor. Read from the paper itself, he defines it as the ratio of actual surface to geometric
surface — the latter being the surface measured in the plane of the interface — and observes that
for any real solid the actual surface exceeds the geometric one. It is the same quantity [Gross, Zhao, Mascarenhas & Wen (2016)](https://doi.org/10.1186/s13068-016-0451-z)
used as their texture variable for algal attachment — which is why it belongs on the attachment term
rather than on area. The `Sdq`/`Sdr` definitions and the `Sdr ≈ Sdq²/2` relation are taken from
[Pawlus, Reizer & Wieczorowski (2021)](https://doi.org/10.3390/ma14185326).

**Four cautions attached to any `r` quoted here:**

1. **`r` is not a single number.** As the sampling interval shrinks, finer features enter the
   integral and `Sdr` rises — without bound on a fractal-like surface. Quantified for `Sdq`/`Sdr`
   specifically by [Pawlus, Reizer & Żelasko (2025)](https://doi.org/10.3390/ma18235394). One
   evaluation scale must be fixed and declared for all four materials or cross-material comparison
   is meaningless. See also [Leach & Haitjema (2010)](https://doi.org/10.1088/0957-0233/21/3/032001)
   on instrument bandwidth and [Todhunter et al. (2017)](https://doi.org/10.1016/j.cirpj.2017.06.001)
   on which parameters are actually used in practice.
2. **Cell-accessible area is not true area.** Features finer than a cell add area no cell can enter;
   attachment depends on feature size *relative to* cell size
   ([Cheng, Feng & Moraru 2019](https://doi.org/10.3389/fmicb.2019.00191)). A roughness threshold
   below which bacterial retention stops changing is the same idea
   ([Bollen, Lambrechts & Quirynen 1997](https://doi.org/10.1016/s0109-5641(97)80038-3)).
3. **Re-entrant features break the formalism.** A height map `z = f(x,y)` has one height per point
   and cannot represent undercuts ([Pagani et al. 2019](https://doi.org/10.1016/j.measurement.2019.04.027)).
   Fibers always undercut, so **ISO 25178 areal parameters are formally undefined on the non-woven
   fabric** — which is why `r` is `None` for that material here.
4. **Double-counting risk.** The same `r` scales wetting through Wenzel, and the ensemble already
   samples wettability. An `r`-driven area term added on top would count one physical cause twice.
   This is the reason for the convention in the model-details tab.

Gas adsorption ([Brunauer, Emmett & Teller 1938](https://doi.org/10.1021/ja01269a023)) returns area
at a molecular probe scale and would overstate cell-accessible area by orders of magnitude; it is
not used.

## Materials

| code | material |
|---|---|
| `PE` | HDPE — conventional RBC media, the baseline |
| `STL` | bare steel |
| `GRA` | graphene-coated steel |
| `FAB` | hydrophilic non-woven fabric |

## Sources, and what was actually read

The roughness and texture entries above draw on the surface-roughness twinlet's reference set
(`surface_roughness_model/references.csv`, 23 records). **Four are held in full text**, filed by DOI under `surface_roughness_model/refs/` in the surface-roughness twinlet, which is not part of this repository:

| source | DOI | full text? |
|---|---|---|
| Gross, Zhao, Mascarenhas & Wen 2016 | [10.1186/s13068-016-0451-z](https://doi.org/10.1186/s13068-016-0451-z) | **yes** — publisher open-access PDF |
| Pawlus, Reizer & Wieczorowski 2021 | [10.3390/ma14185326](https://doi.org/10.3390/ma14185326) | **yes** — PubMed Central |
| Wenzel 1936 | [10.1021/ie50320a024](https://doi.org/10.1021/ie50320a024) | **yes** |
| Brunauer, Emmett & Teller 1938 | [10.1021/ja01269a023](https://doi.org/10.1021/ja01269a023) | no — paywalled, metadata only |
| Bollen, Lambrechts & Quirynen 1997 | [10.1016/s0109-5641(97)80038-3](https://doi.org/10.1016/s0109-5641%2897%2980038-3) | **yes** |
| Pagani et al. 2019 | [10.1016/j.measurement.2019.04.027](https://doi.org/10.1016/j.measurement.2019.04.027) | no — abstract only |
| Cheng, Feng & Moraru 2019 | [10.3389/fmicb.2019.00191](https://doi.org/10.3389/fmicb.2019.00191) | no — abstract only |
| Leach & Haitjema 2010 | [10.1088/0957-0233/21/3/032001](https://doi.org/10.1088/0957-0233/21/3/032001) | no — abstract only |
| Todhunter et al. 2017 | [10.1016/j.cirpj.2017.06.001](https://doi.org/10.1016/j.cirpj.2017.06.001) | no — abstract only |
| Pawlus, Reizer & Żelasko 2025 | [10.3390/ma18235394](https://doi.org/10.3390/ma18235394) | no — abstract only |

The remaining records in that file are abstract-level only. Every one was
verified as a real record — DOI, authors, venue, year — but **a claim resting on a source read only
at abstract level is weaker than one resting on a full text**, and the distinction is kept visible
here rather than buried in a provenance column.

**Full-text status of the detachment sources behind `n_shear`**:

| source | DOI | full text? |
|---|---|---|
| Peyton & Characklis 1993 | [10.1002/bit.260410707](https://doi.org/10.1002/bit.260410707) | **yes** |
| Rittmann 1982 | [10.1002/bit.260240219](https://doi.org/10.1002/bit.260240219) | **yes** |
| Horn, Reiff & Morgenroth 2003 | [10.1002/bit.10503](https://doi.org/10.1002/bit.10503) | **no — still not obtained in any form.** Publisher fetch returned 403; no PMCID. It is the one remaining detachment-form source read only at abstract level. |
| Hassard et al. 2014 | [10.1016/j.psep.2014.07.003](https://doi.org/10.1016/j.psep.2014.07.003) | **yes**; source of the 151 / 412 µm film band behind `X_cap` |

**Not obtained in full text, and therefore weaker ground:** Horn, Reiff & Morgenroth 2003 above;
Brunauer, Emmett & Teller 1938; Waqas et al. 2023 ([10.3390/w15101913](https://doi.org/10.3390/w15101913),
abstract only despite being gold open access); the remaining roughness records listed above; and
**every ISO and ASME standard**, none of which has been obtained in any form.
