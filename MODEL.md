# The coupon-scale biofilm model

A description of what the model is and how it works. Terms are defined in
[GLOSSARY.md](GLOSSARY.md); parameter values live in `params_v2.yaml` and rig
dimensions in `rig.yaml`.

---

## 1. What it models

A single carrier coupon hanging in a stirred, illuminated vessel of synthetic
wastewater. Three groups of organisms grow as a film on the coupon surface —
**phototrophs** (algae and cyanobacteria, which need light), **nitrifiers**
(which oxidize ammonia to nitrate and need oxygen), and **heterotrophs** (which
eat dissolved organic matter and also need oxygen) — plus a fourth pool of
cells still floating in the liquid. Cells land on the coupon from the liquid,
grow, die, and slough off; while they do, they draw ammonia, nitrate,
phosphorus and organic matter out of the liquid, which is replaced on a feeding
schedule. The model tracks all of that through time and reports how much
biomass sits on the coupon, how it is divided between the three groups, and how
fast ammonia disappears.

The purpose is to compare **carrier materials and geometries**: which surface
holds the most living, light-reached, oxygen-reached film per unit of reactor
volume and per kilogram of carrier. The same equations run at two scales — one
coupon in a beaker (the bench rig) and a packed carrier in a reactor (the
screening study) — differing only in how much surface there is per unit volume.

---

## 2. State variables

Everything on the carrier is carried as **areal** biomass: grams of dry weight
per square meter of carrier surface. Liquid concentrations are per cubic meter
(numerically the same as mg/L).

| Symbol | Meaning | Units |
|---|---|---|
| `Snh` | ammonia-N in the liquid | g N m⁻³ |
| `Sno` | nitrate-N in the liquid | g N m⁻³ |
| `Sp`  | soluble phosphorus in the liquid | g P m⁻³ |
| `Sb`  | biodegradable organic matter in the liquid | g BOD m⁻³ |
| `Xpl` | suspended cells not yet attached | g DW m⁻² of carrier |
| `Xp`  | phototrophs in the film | g DW m⁻² |
| `Xn`  | nitrifiers in the film | g DW m⁻² |
| `Xh`  | heterotrophs in the film | g DW m⁻² |

The three film groups are each resolved into **irradiance bins** — patches of
the carrier that receive different amounts of light because of self-shading by
the carrier itself. A bin *b* carries an area weight *w_b* (the fraction of
carrier surface in that bin) and a relative irradiance *E_b*. The suspended
pool is held in areal units too, so that every state is the same order of
magnitude and the solver behaves.

---

## 3. The equations

### 3.1 Light reaching the cells

Light is attenuated twice: once by the carrier's own shape, once by the film.

    I_b = I₀ · E_b                                   (carrier self-shading)
    τ   = k_abs · Xp
    Ī_b = I_b · (1 − e^(−τ)) / τ                     (Beer–Lambert through the film)

each patch of carrier starts with a fraction `E_b` of the
incident light because neighboring surfaces shade it; the cells in that patch
then shade each other, so the average cell sees less than the cells at the
surface. The second line is the depth-average of exponential decay.

### 3.2 Phototroph growth

    μ_p = μ_max,p · [Ī/(K_I+Ī)] · [N/(K_N,p+N)] · [Sp/(K_P,p+Sp)] · θ_p^(T−20) · free · α

growth runs at its maximum rate only when light, nitrogen
(ammonia plus nitrate) and phosphorus are all plentiful; each shortage
multiplies the rate down by a saturating (Monod) factor. Temperature scales it
by the usual Arrhenius-style factor. `free` and `α` are defined below.
Phototrophs grow only while the lamps are on, and respire at rate `b_p` only
while they are off.

### 3.3 Carrying capacity — the film cannot grow forever

    free = max(0, 1 − (Xp+Xn+Xh) / X_cap)

as the film thickens, less room is left; when the total areal
biomass reaches `X_cap` all growth and all attachment stop. This is a single
shared ceiling: a surface crowded with heterotrophs leaves no space for
nitrifiers. **Capacity is deliberately the same for every material** — nothing
has been measured that would justify giving the fabric a larger one — which is
why the model predicts no lasting material difference except for graphene.

### 3.4 Nitrification

    r_N = r_N,ref · (Xn/Xn,ref) · [Snh/(K_N,n+Snh)] · θ_n^(T−20) · f_comp · f_wet · [S_O/(K_O,A+S_O)] · free · α
    f_comp = K_comp / (K_comp + Xh)

ammonia removal is proportional to how many nitrifiers are
present, limited by how much ammonia there is and how much oxygen, and
suppressed by heterotrophs — `f_comp` is the competition term: the more
heterotrophs on the surface, the less of it nitrifiers hold. Nitrifier biomass
then grows at yield `Y_n` per gram of nitrogen oxidized.

### 3.5 Heterotrophs are confined to the depth that BOD reaches

    J_S   = Xh · μ_max,h / Y_h · [Sb/(K_S,h+Sb)]      (demand)
    δ_S   = √(2 · D_S,eff · Sb / (J_S / L_f))         (penetration depth)
    cap_h = ρ_dry · min(δ_S, L_f + δ_floor)
    free_h = max(0, 1 − Xh/cap_h)

organic matter diffusing in from the liquid is consumed as it
goes, so it only penetrates a certain depth. Heterotrophs can occupy only that
depth; the rest of the film is left to the others. More BOD in the feed means a
deeper heterotrophic layer and less room for nitrifiers, so the competition
between the two is a consequence of diffusion rather than an imposed rule. The
floor `δ_floor` (50 µm) lets a bare carrier be colonized at all.

### 3.6 Oxygen effectiveness

    J_O2 = 4.57·r_N + (O₂ per BOD)·growth_h/Y_h − Y_O2,p·(photosynthesis − respiration)
    δ    = √(2 · D_O2,eff · S_O / (J_O2 / L_f))
    η    = min(1, δ / L_f)

add up how much oxygen the film demands, subtract what the
phototrophs make, and ask how far oxygen can diffuse in before it is used up.
If that depth is less than the film thickness, only that fraction of the film
is aerobic, and the aerobic rates (nitrification and heterotrophic growth) are
multiplied by η. Bulk dissolved oxygen `S_O` is imposed, not simulated — the
vessel is stirred and open.

### 3.7 Attachment and detachment

    j = k_att · a_mat · [Xpl/(K_pl+Xpl)]
    d(Xp,Xn,Xh)/dt ← + j·fᵢ·free … − k_det·Xᵢ
    dXpl/dt = Σ_b w_b (detached − attached) − b_pl·Xpl

cells land on the coupon at a rate set by how many are in
suspension and how sticky the material is; the material factor `a_mat` is the
**only** place material identity enters (apart from graphene, below). They
leave again at a constant fractional rate. Attached and suspended cells are the
same biomass moving between two places — nothing is created — and the pool runs
down as it is drawn on, which is why a material advantage in attachment fades
once the pool is depleted. Attachment is shut off by the same `free` term as
growth, so it cannot push the film past capacity.

### 3.8 Lag

    α(t) = 1 / (1 + (e^(ν·lag) − 1) · e^(−ν·t)),   ν = μ_max,h

real cells take hours to days to start growing after being
transferred. This is the standard Baranyi–Roberts form: growth ramps from near
zero up to full rate over about `lag_d` days. **The model can express a lag; it
currently does not** — `lag_d = 0`, which makes α ≡ 1 exactly. The term is
there so that the day 3 / 7 / 10 harvests can rule a lag in or out against a
model capable of showing one. It delays growth only, not attachment.

### 3.9 Graphene

    X_cap(t) = X_cap · [1 − (1 − 0.56)·(1 − e^(−(t−14)/10))]   for t > 14 d

A graphene-coated surface is modeled as bare steel with a
capacity that falls as the film matures, reaching 56 % of the normal ceiling,
after Romeu et al. (2022), who report 44 % less biofilm by wet weight at seven
weeks with no effect during early attachment. Until coupon contact angle and
roughness are measured this is the only difference between graphene and steel.

**This is the model's weakest transfer, and it carries the whole graphene
result.** Romeu et al. tested graphene nanoplatelets dispersed in an **epoxy
resin**, against glass and plain epoxy controls, in a **marine** system with
marine cyanobacteria. The arm modeled here is a **coating on stainless steel**,
compared against bare stainless steel, in wastewater. The authors further report
that the dominant measured difference between composite and control was
**roughness, about 1000× higher** — so the 44 % reduction may be a topographic
effect of that composite rather than a property of graphene that a coating would
reproduce. They also report larger reductions on other measures at seven weeks
(54 % thickness, 82 % biovolume, 64 % surface coverage); wet weight is the
smallest of the four and therefore the most conservative choice, but it is a
choice. Because material differences otherwise wash out within about a week —
attachment and detachment only change how fast a carrier reaches the same
capacity-limited plateau — this single borrowed parameter is the only reason
graphene behaves differently from steel at all. It should be replaced by a
measurement on the project's own coupon before any graphene claim is made.

---

## 4. Area per unit volume (`a_v`)

Every rate in §3 is **per square meter of carrier surface**. What the
experiment actually measures is a concentration in the liquid, and `a_v`
(m² m⁻³) — wetted carrier area per unit of liquid volume — is what converts
between the two:

    r_v = a_v · Σ_b w_b · f_col,b · (1 − f_occ,b) · r_a,b

where `w_b` is the area fraction of irradiance bin `b`,
`f_col = 1 − e^(−X/2)` is the colonized fraction of the surface, and `f_occ`
is the share of pores bridged shut by the film. For a flat coupon the sum has
few bins and no occlusion, and it reduces to `a_eff · J_A`, the form used in
the manuscript.

For the bench rig `a_v` is one coupon's wetted area divided by the vessel's
working volume, both from `rig.yaml`: currently 25 cm² in 1.0 L, giving
`a_v = 2.5 m² m⁻³`. **Both numbers are flagged `provenance: placeholder` and
are waiting to be measured.** `a_v` is the single number that sets how fast
bulk concentrations move — the same film empties a small vessel quickly and a
large one slowly — which is why it is the first control in the explorer, and
why the feeding schedule has to be re-derived if the measurement comes back
near 15 (three coupons, both faces) or 30 m² m⁻³. At 30 no manual schedule
keeps up and the rig would need a pump.

`f_occ` is **exploratory**: it is computed and reported, but the headline
ranking is given with and without it, because nothing has been measured
against which to check it.

> **Out of scope for this round.** The same equation extends to a packed
> carrier in a reactor, where `a_v`, the pore-aperture distribution and the
> irradiance bin weights are built by `geometry.py` and `irradiance.py` from a
> voxelized carrier. That pipeline exists and drives the carrier screening
> study, but nothing in the bench experiment tests it, so reactor-scale
> extrapolation is deliberately left for later.

---

## 5. Parameters

Status: **L** from the literature or the plant model · **D** derived or
calibrated from such a value · **U** unmeasured, given a defensible value and
varied in the ensemble. No parameter is yet measured on this system; that is
what the bench experiment is for. Author–year keys resolve in §8.

| Symbol | What it is | Value | Units | Source | Status |
|---|---|---|---|---|---|
| `I0` | Incident irradiance at the vessel | 110 | µmol m⁻² s⁻¹ | assay irradiance of Gross et al. (2016), 110–120; no lamp specification exists for this rig, swept 72–150 | U |
| `k_abs` | Film light-absorption coefficient | 0.21 | m² g⁻¹ DW | Ma et al. (2023), 0.18–0.29 | L |
| `K_I` | Light half-saturation constant | 50 | µmol m⁻² s⁻¹ | typical microalgal value, no source paper; swept 25–100 | U |
| `mu_max_p` | Maximum phototroph growth rate | 4.53 | d⁻¹ | **calibrated** so the model reproduces the Gross et al. (2016) seven-day areal biomass; replaced a PHOBIA placeholder | D |
| `b_p` | Phototroph decay (dark respiration) rate | 0.17 | d⁻¹ | Edmundson & Huesemann (2015), night biomass loss | L |
| `K_N_p` | Phototroph nitrogen half-saturation | 0.017 | g N m⁻³ | Wolf et al. (2007) Table VI, their citation to Eppley et al. (1969) | L |
| `K_P_p` | Phototroph phosphorus half-saturation | 0.02 | g P m⁻³ | typical microalgal value, no source paper; swept 0.005–0.1 | U |
| `fN_p`, `fP_p` | Nitrogen and phosphorus content of phototroph biomass | 0.048, 0.0099 | g g⁻¹ DW | Boelee et al. (2011), nutrient-replete biofilm | L |
| `theta_p`, `theta_h` | Arrhenius coefficients, phototrophs and heterotrophs | 1.07 | – | conventional suspended-growth value (Henze et al. 2000); not measured on a biofilm | U |
| `rN_ref` | Reference areal nitrification rate | 4.2 | g N m⁻² d⁻¹ | Németh et al. (2023), midpoint of 2.96–5.45 — a membrane-aerated reactor, not an RBC | **U** |
| `Xn_ref` | Nitrifier biomass the reference rate is defined at | 0.71 | g DW m⁻² | `Y_n · rN_ref / μ_max,N`, with μ_max,N = 1.0 d⁻¹ from Wolf et al. (2007) Table VI | D |
| `K_N_n` | Ammonia half-saturation, nitrifiers | 1.0 | g N m⁻³ | Wolf et al. (2007) Table VI (the plant model uses 0.7) | L |
| `Y_n` | Nitrifier biomass yield per unit nitrogen | 0.17 | g DW g⁻¹ N | Wolf et al. (2007) Table VI, 0.24 g COD g⁻¹ N ÷ 1.42 | D |
| `theta_n` | Arrhenius temperature coefficient, nitrifiers | 1.025 | – | Németh et al. (2023), 1.024–1.026 | L |
| `mu_max_h` | Maximum heterotroph growth rate | 3.2 | d⁻¹ | Copp (2024) plant model at 20 °C; replaced 5.5 d⁻¹ from Wolf et al. (2007) | L |
| `K_S_h`, `Y_h` | Substrate half-saturation and yield, heterotrophs | 4.0, 0.44 | g m⁻³, g g⁻¹ | Wolf et al. (2007) Table VI; BOD treated as biodegradable COD | L |
| `b_n`, `b_h` | Decay rates, nitrifiers and heterotrophs | 0.15, 0.40 | d⁻¹ | Wolf et al. (2007) Table VI, after Henze et al. (2000) | L |
| `K_comp` | Heterotroph biomass that halves nitrification | 5.0 | g DW m⁻² | no source; the suppression of nitrifiers by heterotrophs has not been measured here | **U** |
| `X_cap` | Carrying capacity — maximum areal biomass | 60 | g DW m⁻² | midpoint of 32–88 implied by plant film thicknesses 0.151–0.412 mm; swept 32–88 | U |
| `k_att` | Areal attachment flux onto bare HDPE | 1.0 | g DW m⁻² d⁻¹ | no source; anchored so HDPE gains in one day the biomass earlier versions imposed as an initial condition | **U** |
| `k_det` | First-order detachment (sloughing) rate | 0.05 | d⁻¹ | no source | U |
| `K_pl`, `b_pl` | Suspended-pool attachment half-saturation and decay rate | 0.5, 0.10 | g m⁻³, d⁻¹ | no source | U |
| `seed_frac` | Share of inoculum already attached at t = 0 | 0.02 | – | no source | U |
| `lag_d` | Baranyi–Roberts lag duration before full growth | 0 | d | form from Baranyi & Roberts (1994); **off**, see §3.8 | U |
| `a_mat` | Material colonization factor on attachment flux | 14.73 / 1.0 / 0.528 | – | Gross et al. (2016) seven-day areal biomass relative to HDPE, for FAB / PE / STL·GRA | L |
| `S_O_bulk` | Dissolved oxygen in the bulk liquid | 8.0 | g O₂ m⁻³ | stirred open vessel; swept 6.5–9.1, upper bound the plant model's saturation at 20 °C | U |
| `D_O2_eff` | Effective oxygen diffusivity inside the film | 1.08×10⁻⁴ | m² d⁻¹ | Copp (2024), water value × 0.5 for biofilm | L |
| `D_S_eff` | Effective substrate diffusivity inside the film | 4.32×10⁻⁵ | m² d⁻¹ | Copp (2024), same construction, readily biodegradable substrate | L |
| `K_O_A`, `K_O_H` | Oxygen half-saturation, nitrifiers and heterotrophs | 0.25, 0.05 | g O₂ m⁻³ | Copp (2024) plant model | L |
| `Y_O2_p` | Oxygen produced per unit phototroph biomass | 1.3 | g O₂ g⁻¹ DW | stoichiometric, biomass CH₁.₈O₀.₅N₀.₂, photosynthetic quotient 1.0 | D |
| `delta_S_floor` | Minimum heterotroph layer thickness | 50 | µm | this study's choice (§3.5) | U |
| `rho_film_wet`, `moisture` | Wet film density and moisture fraction | 1.426, 0.85 | g cm⁻³, – | Copp (2024) Table 1 — an **assumption** in the plant model, not a measurement; replacing it is one purpose of this experiment | L |
| `f_wet` | Submerged (wetted) fraction of carrier area | 1.0 (rig) / 0.76 (screening) | – | rig coupons are fully submerged and `coupon_area` is already wetted area, so no further discount applies; in screening, `a_geo` is total surface and part may sit above the liquor | – |
| `Xp0 : Xn0 : Xh0` | Inoculum guild composition (photo : nitrifier : hetero) | 0.5 : 0.2 : 0.3 | g DW m⁻² | no source; placeholder pending the metagenomic analysis of public datasets | **U** |
| graphene | Graphene maturation: final factor, onset, time constant | 0.56, 14 d, 10 d | – | Romeu et al. (2022); the time constant is a placeholder | L/U |

### Which parameters matter

A Morris screening (8 trajectories × 15 parameters) ranks the elementary
effects on the day-60 volumetric ammonia removal rate `r_v`
(the response `sensitivity.py` actually ranks on; a second ranking on `a_eff`
is computed alongside it):

    K_comp 4373 ≫ rN_ref 1454 > D_O2_eff 802 > f_wet 754 > X_cap 716
    > k_att 683 > S_O_bulk 544 > k_det 362 > b_p 184 > K_I 92 > I0 53

**The two most influential parameters, `K_comp` and `rN_ref`, are both
unmeasured.** This is the model's largest weakness and the main thing the bench
experiment should fix. It also drove a design change: in a closed batch the
feed is exhausted within days and the film becomes ~90 % phototrophs, under
which neither parameter can be constrained at all. The rig is therefore fed —
half the volume replaced twice a day from day 3 — which keeps ammonia from
falling below about 74 % of the nitrifier saturation level and keeps a
nitrifying population to measure.

---

## 6. What the model does not include

- **Denitrification.** Deliberately excluded; the rig is aerobic and nitrate
  accumulates.
- **pH and alkalinity.** Not tracked, so alkalinity limitation of nitrification
  cannot appear.
- **Oxygen as a liquid state.** Bulk DO is imposed; only its gradient *inside*
  the film is resolved.
- **Spatial structure within the film.** Each irradiance bin is a stirred layer
  with analytic penetration depths, not a 1-D multi-species film model.
- **Inter-vessel variation.** Every replicate in an arm is given the same light
  field, so the model cannot reproduce replicate scatter. The rig's lamp
  gradient runs along the replicate axis, not the material axis, and is not yet
  represented.
- **Specular reflection, inter-reflection, wavelength.** The light model is
  diffuse and gray, so its irradiance estimates are a lower bound.
- **Nitrite** as a separate species, and **nitrate inhibition** at high
  concentrations.
- **Temperature dynamics.** Runs are isothermal at 20 °C; θ terms exist but are
  never exercised.
- **Any calibration to a measured growth curve.** Nothing in the model has been
  fitted to data from these coupons.

---

## 7. Running it

```bash
python model/run_demo.py        # one arm, prints a summary and a figure
python model/build_explorer.py  # the parameter grid behind the web explorer
python model/build_page.py      # rebuild index.html from that grid and this file
```

Minimal use from Python:

```python
import yaml, pandas as pd, reactor as R
par  = yaml.safe_load(open("params_v2.yaml"))["parameters"]
bins = pd.read_csv("irradiance_bins.csv").query("material=='FAB' and geometry=='Flat sheet'")
r = R.Reactor(par, bins.area_fraction.values, bins.rel_irradiance.values,
              a_v=2.5, attach=14.73, bulk_mode="batch",
              feed={"Snh": 30, "Sno": 0, "Sp": 5, "Sb": 50})
t, y = r.simulate(days=28, light_h=9.2, T=20.0)
u = r.unpack(y)                          # dict of Snh, Sno, Sp, Sb, Xp, Xn, Xh
```

`Reactor(...)` takes the parameter dict, the bin weights and relative
irradiances, the specific area `a_v`, the material attachment factor, a bulk
mode (`"batch"` for a closed vessel, `"fixed"` to hold the liquid constant) and
the feed composition. `simulate` returns times and the raw state array;
`unpack` turns it into named series and `areal_rate` returns the areal removal
rate.

Requires Python 3.11+, numpy, scipy, pandas, pyyaml and matplotlib; rebuilding the
page additionally needs `markdown`. Run from the repository root. The carrier
geometry and irradiance pipelines referred to in §4 are not part of this release;
their outputs ship as `model/geometry_catalogue.csv` and `model/irradiance_bins.csv`.

---

## 8. References

Every author–year key in §3 and §5 resolves here, with a note on what the model
takes from each source. Several values reach the model second-hand: the entries
drawn from Wolf et al. (2007) Table VI are that paper's own compilation, in
places from Henze et al. (2000) and Eppley et al. (1969). Those compilations are
cited as read, not as if the primary papers had been consulted.

### Peer-reviewed literature

- **Baranyi, József; Roberts, Terry A. (1994).** A dynamic approach to predicting bacterial growth in food. *International Journal of Food Microbiology* **23**(3–4), 277–294. [doi:10.1016/0168-1605(94)90157-0](https://doi.org/10.1016/0168-1605(94)90157-0)  
  *Used for:* the Baranyi–Roberts lag form α(t) in §3.8. The form is implemented; `lag_d = 0`, so no lag is currently asserted.
- **Boelee, N.C.; Temmink, H.; Janssen, M.; Buisman, C.J.N.; Wijffels, R.H. (2011).** Nitrogen and phosphorus removal from municipal wastewater effluent using microalgal biofilms. *Water Research* **45**(18), 5925–5933. [doi:10.1016/j.watres.2011.08.044](https://doi.org/10.1016/j.watres.2011.08.044)  
  *Used for:* phototroph biomass nitrogen and phosphorus content, `fN_p` = 0.048 and `fP_p` = 0.0099 g g⁻¹ DW, measured on a nutrient-replete microalgal biofilm.
- **Edmundson, Scott J.; Huesemann, Michael H. (2015).** The dark side of algae cultivation: Characterizing night biomass loss in three photosynthetic algae, Chlorella sorokiniana, Nannochloropsis salina and Picochlorum sp.. *Algal Research* **12**, 470–476. [doi:10.1016/j.algal.2015.10.012](https://doi.org/10.1016/j.algal.2015.10.012)  
  *Used for:* the phototroph dark-decay rate `b_p` = 0.17 d⁻¹, from measured night biomass loss across three strains.
- **Gross, Martin; Zhao, Xuefei; Mascarenhas, Vernon; Wen, Zhiyou (2016).** Effects of the surface physico-chemical properties and the surface textures on the initial colonization and the attached growth in algal biofilm. *Biotechnology for Biofuels* **9**(1), 38. [doi:10.1186/s13068-016-0451-z](https://doi.org/10.1186/s13068-016-0451-z)  
  *Used for:* the material colonization factors `a_mat` (§3.7), taken as seven-day areal biomass relative to HDPE; the seven-day endpoint that `mu_max_p` is calibrated against; and the assay irradiance that stands in for `I0` until this rig's lamp is characterized.
- **Ma, Shiyan; Huang, Yun; Zhang, Beiyu; Zhu, Xianqing; Xia, Ao; Zhu, Xun; Liao, Qiang (2023).** Comprehensive modeling and predicting light transmission in microalgal biofilm. *Journal of Environmental Management* **326**, 116757. [doi:10.1016/j.jenvman.2022.116757](https://doi.org/10.1016/j.jenvman.2022.116757)  
  *Used for:* the film light-absorption coefficient `k_abs` = 0.21 m² g⁻¹ DW (reported range 0.18–0.29), the Beer–Lambert term in §3.1.
- **Németh, András; Ainsworth, Jude; Ravishankar, Harish; Lens, Piet N. L.; Heffernan, Barry (2023).** Temperature dependence of nitrification in a membrane-aerated biofilm reactor. *Frontiers in Microbiology* **14**, 1114647. [doi:10.3389/fmicb.2023.1114647](https://doi.org/10.3389/fmicb.2023.1114647)  
  *Used for:* the reference areal nitrification rate `rN_ref` = 4.2 g N m⁻² d⁻¹ (midpoint of 2.96–5.45 at 10–20 mg N L⁻¹) and the biofilm Arrhenius coefficient `theta_n` = 1.025. Measured in a membrane-aerated biofilm reactor, not an RBC — the transfer is why `rN_ref` is listed as unmeasured.
- **Romeu, Maria J.; Gomes, Luciana C.; Sousa-Cardoso, Francisca; Morais, João; Vasconcelos, Vítor; Whitehead, Kathryn A.; Pereira, Manuel F. R.; Soares, Olívia S. G. P.; Mergulhão, Filipe J. (2022).** How do Graphene Composite Surfaces Affect the Development and Structure of Marine Cyanobacterial Biofilms?. *Coatings* **12**(11), 1775. [doi:10.3390/coatings12111775](https://doi.org/10.3390/coatings12111775)  
  *Used for:* the graphene maturation factor in §3.9: 44 % less biofilm by wet weight at seven weeks, with no effect during early attachment. §3.9 sets out at length why this transfer is the model's weakest.
- **Wolf, Gundula; Picioreanu, Cristian; van Loosdrecht, Mark C.M. (2007).** Kinetic modeling of phototrophic biofilms: The PHOBIA model. *Biotechnology and Bioengineering* **97**(5), 1064–1079. [doi:10.1002/bit.21306](https://doi.org/10.1002/bit.21306)  
  *Used for:* the PHOBIA parameter set, Table VI: `K_N_p`, `K_N_n`, `K_S_h`, `Y_n`, `Y_h`, `b_n`, `b_h`, and the nitrifier μ_max used to derive `Xn_ref`.

### Books and model standards

- **Antonie, R. L. (2018).** *Fixed Biological Surfaces — Wastewater Treatment:
  The Rotating Biological Contactor.* CRC Press. ISBN 9781351088947.
  *Used for:* the synthetic feed composition in `rig.yaml` — typical RBC
  effluent at BOD₅ 20, TSS 30, NH₃-N 20 mg L⁻¹. Cited second-hand, through the
  experiment setup document; the book itself has not been consulted here.

- **Henze, M., Gujer, W., Mino, T. & van Loosdrecht, M. C. M. (2000).**
  *Activated Sludge Models ASM1, ASM2, ASM2d and ASM3.* IWA Scientific and
  Technical Report No. 9, IWA Publishing, London.
  *Used for:* the conventional suspended-growth Arrhenius coefficient 1.07
  carried by `theta_p` and `theta_h`, and the decay rates that reach the model
  through Wolf et al. (2007).

### Project documents (not peer-reviewed)

- **Copp, J. (2024).** *Modelling the Apple Springs Wastewater Treatment Plant.*
  Technical Memorandum 136-002, Primodal Inc., 11 July 2024.
  *Used for:* the plant-model values the coupon model inherits — `mu_max_h` at
  20 °C, the oxygen half-saturations `K_O_A` and `K_O_H`, the effective
  diffusivities `D_O2_eff` and `D_S_eff`, and the film density and moisture
  `rho_film_wet` = 1.426 g cm⁻³ and `moisture` = 0.85. The last two are
  **assumptions in that model, not measurements** — replacing them with a
  measured value is one of the things this experiment is for.
