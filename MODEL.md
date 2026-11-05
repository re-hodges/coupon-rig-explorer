# Coupon explorer — model details

Apple Springs carrier screening. Coupons magnet-mounted in divots on the first-stage RBC's
steel bands. Rig geometry follows the operator's description of RBC 1.

## 1. The system being modeled

Each RBC has two rotating round steel **end plates 6 ft (1.829 m) apart** on a common shaft,
with the wafer pack turning between them. Two steel **bands** run axially from plate to plate
at **0° and 180°**. Each band carries **divots** — sheltered recesses — and each divot holds
**nine coupons of one material**, every coupon held in a magnet sandwich clamped to the divot
floor. Three coupons are harvested on each of days **5, 7 and 10**.

Two divots per material, one per photoperiod, gives **8 divots and 72 coupons**. Lamps sit in
six existing round holes in the RBC cover, **three at each end**, so photoperiod is a function
of **axial position along the shaft** — one end on the summer timer, the other on the winter
timer.

The coupons ride the rotation. Each revolution carries them through the liquor and back out
again, so substrate uptake happens submerged and oxygen uptake happens emergent — which is the
RBC mechanism itself rather than an approximation to it.

**The system is open.** The coupons sit in the plant's own first-stage tank, so bulk ammonia,
nitrate, phosphate, BOD₅ and dissolved oxygen are **imposed boundary conditions** set by the
plant. A few hundred cm² of coupon cannot move them. Consequently the carrier-area-to-liquid-
volume ratio `a_v` multiplies a zero derivative and is inert; it is carried in the state only so
the suspended pool stays dimensionally consistent.

The model therefore predicts what the coupons genuinely measure — areal biomass by guild, film
thickness, and areal removal flux — and does not predict bulk chemistry, because the coupons do
not control it.

**Mount radius is fixed by the hardware.** The bands hold every coupon at **r/R = 0.95**, the
most-submerged, least-lit and highest-shear station on the wheel, so radius is not a design
choice and `f_wet` is a constant 0.4469. The design axis in its place is **divot shelter**,
which the band mounting introduces and which nothing measures.

## 2. Governing equations

Areal biomass per guild `i ∈ {p, n, h}`, on each irradiance bin:

    dX_i/dt = growth_i + attachment_i − decay_i − detachment_i

**Phototrophs** grow only while lit, Monod in light, nitrogen and phosphorus:

    μ_p = μ_max,p · I̅/(K_I + I̅) · N/(K_N,p + N) · S_P/(K_P,p + S_P) · θ_p^(T−20) · free · α(t)

`I̅` is the Beer–Lambert average of the bin irradiance through the film, so a thickening film
self-shades.

**Nitrifiers** use a measured areal form:

    r_N = rN_ref · (X_n/Xn_ref) · S_NH/(K_N,n + S_NH) · θ_n^(T−20) · f_comp · f_wet · η_O2 · free

**Heterotrophs** are Monod on BOD and confined to the depth BOD actually reaches. That
stratification is what produces guild coexistence: a single shared capacity pool gives a
knife-edge instead.

**Oxygen is a state inside the film**, with bulk `S_O` imposed at the outer boundary.
Phototrophs are a source, nitrifiers and heterotrophs sinks. It is solved by an analytic
zero-order penetration depth rather than a PDE:

    δ = √(2 D S / R_v),    η_O2 = min(1, δ/L_f)

**Attachment is a rate, not an initial condition**, and it is mass-conserving: cells move from a
finite suspended pool onto the carrier and detachment returns them. Every arm is seeded
identically; what differs between materials is how readily cells stick and stay.

**Primary response:**

    J_V = a_eff · J_A,     a_eff = a_geo · f_col · (1 − f_occ)

`J_A` is the areal removal flux reported per the exposed coupon area defined in §5.

## 3. The rotation duty cycle

**Wet fraction depends on mount radius.** For a given fraction of the disc *area* submerged, the
waterline sits `u·R` below the shaft centerline, where

    [arccos(u) − u√(1−u²)] / π = submergence        →  u = 0.1577 at 40 %

and a point at radius `r` spends this share of each revolution under water:

    f_wet(r) = ½ + arcsin(−uR/r)/π

| r/R | 1.00 | **0.95** | 0.85 | 0.55 | 0.50 | 0.35 | 0.25 |
|---|---|---|---|---|---|---|---|
| `f_wet` | 0.450 | **0.4469** | 0.441 | 0.407 | 0.398 | 0.351 | 0.283 |

The band sits at r/R = 0.95, so **`f_wet` = 0.4469** — the coupons are submerged 44.7 % and
emergent 55.3 % of every revolution. The nominal 40 % areal submergence is recovered only near
r/R = 0.5 and does not describe the band.

**Light has a hard ceiling.** Submerged means dark — mixed liquor is opaque — so

    delivered_h = timer_h × (1 − f_wet)

At the band the ceiling is **13.27 h/d**. The two timer settings deliver:

| photoperiod | timer | delivered at the band |
|---|---|---|
| summer solstice | 15.50 h | **8.573 h/d** |
| winter solstice | 8.87 h | **4.906 h/d** |

A 24 h photoperiod is physically unreachable on a rotating disc. Timer hours and delivered hours
are reported separately throughout and are never conflated.

**Oxygen per emergent pass**, as √(2 D t) at `D_O2_eff` = 1.08 × 10⁻⁴ m² d⁻¹:

| rpm | 0.5 | 1.0 | 1.5 | 2.0 | 2.5 | 4.0 |
|---|---|---|---|---|---|---|
| penetration (µm) | 407 | 288 | 235 | 204 | 182 | 144 |

Slowing the wheel roughly doubles how deep oxygen reaches per pass while simultaneously cutting
shear. Those are opposing effects with an optimum between them, which is why rotation rate is a
variable here rather than a fixed condition — and §10.4 shows the optimum is real.

## 4. Shear, shelter and detachment

Detachment is first-order in areal biomass. Because areal biomass and film thickness are
proportional, that makes the detachment *flux* proportional to thickness.

Shear enters as a modifier whose exponent is **sampled across the ensemble, not fixed**:

    k_det = k_det,base · (τ_local / τ_ref)^n_shear ,    n_shear ∈ {0, 0.5, 1}

`τ_ref` anchors the baseline at the plant's present operating point — **4 rpm, at the band,
unsheltered** — so changing `n_shear` does not shift the reference case. `n_shear = 0` means no
shear dependence at all.

**Divot shelter.** A coupon recessed below the band surface feels less than the free-stream
wall shear:

    τ_local = φ_shear · τ_free ,    φ_shear ∈ {0.3, 0.5, 1.0}

`φ_shear = 1` is a coupon flush with the band. **This factor has no source** — no measurement
and no literature value — so it is sampled rather than fixed, and it appears in the Data sources
tab under "no source" beside `K_comp`. The divot also **dims** the coupon by a view factor of
0.90, applied to irradiance and never to hours, which would double-count the rotation duty.

The exponent is sampled because the literature does not support a single value, and the
disagreement is between the most-cited sources on the question:

- **Peyton & Characklis 1993** (doi:10.1002/bit.260410707) crossed three shear levels with three
  substrate loadings and report **no significant influence of shear** on detachment rate,
  proposing an expression in substrate utilization, yield and film thickness instead.
- **Horn, Reiff & Morgenroth 2003** (doi:10.1002/bit.10503) used growth-rate- and thickness-based
  forms across all three experimental phases, including a deliberate shear step-up.
- **Rittmann 1982** (doi:10.1002/bit.260240219) is the classic shear-dependent source and the
  most cited on the question.

**Rittmann's expression.** The shear loss is a first-order term *added* to the decay
coefficient, with **exponent 0.58** on shear stress and a thickness amplification above a 30 µm
film:

    b' = b + 8.42e-2 · σ^0.58                                for L_f < 0.003 cm
    b' = b + 8.42e-2 · σ^0.58 · (1 + 433.2 (L_f − 0.003))     for L_f > 0.003 cm

Our sampled levels {0, 0.5, 1} bracket 0.58, so the ensemble is not mis-specified and can now be
narrowed. Note that Rittmann's form is **also thickness-dependent**, so the three sources
disagree about whether an explicit shear term is needed *on top of* thickness, not about whether
thickness matters. Modeled films of 59–124 µm sit on the amplified branch.

Local wall shear uses the von Kármán **laminar** rotating-disc result:

    τ_w = 0.512 · ρ · √ν · ω^{3/2} · r

At the band this gives **0.0019–0.141 Pa** across speeds and shelter levels — the bottom of the
range over which biofilm shear effects are reported.

**Regime warning.** The disc Reynolds number `ωR²/ν` crosses the ≈3 × 10⁵ transition between
2.5 rpm (2.30 × 10⁵) and 4 rpm (3.67 × 10⁵), so the laminar correlation is out of range at the
plant's present speed. The model raises `laminar_ok = False` rather than reporting silently; 144
of the 864 arms carry that flag.

## 5. The coupon area convention

**All areal quantities are reported per the exposed coupon area `A_exp`. The roughness ratio
`r = 1 + Sdr` acts only through attachment, never as an area multiplier.**

1. **It avoids a double-count.** The same `r` scales wetting through Wenzel, and the ensemble
   already samples wettability for steel and fabric. An `r`-driven area term on top would count
   one physical cause twice. Gross et al. use `r` as the attachment texture variable — that is
   where it belongs.
2. **The credit is negligible at this scale.** Exact arc-length integration gives `r` = 1.006 at
   h/λ = 0.05 and 1.024 at 0.10. Reaching `r ≈ 1.5` needs h/λ ≈ 0.52, features as tall as they
   are wide — mesh and texture scale, i.e. the geometry axis, where `a_geo` already captures it.
3. **`A_true` is ill-posed for the fabric.** Height maps cannot represent undercuts and fibers
   always undercut, so ISO 25178 areal parameters are formally undefined there.
4. **It keeps the plant join dimensionally honest.** `a_eff` is built from `a_geo`, a geometric
   area; a `J_A` per true area would put a stray factor `r` into `J_V = a_eff · J_A`.

`A_true` is computed and deliberately carried unused, so the choice is auditable. A unit test
inflates `r` to 1.50 and asserts the denominator does not move.

**The counter-argument, and why it was declined:** a rough surface does present more colonizable
area. But cell-accessible area is not true area — features finer than a cell add area no cell can
enter — and at flat-coupon scale the dispute is worth 1–2 %, inside measurement error.

## 6. Coupon geometry and the magnet mounting

The coupon is a **square of side 1 9/16 in = 39.6875 mm**, per the specification.

It is held in a magnet sandwich — one round magnet above, one below — and the lower magnet
clamps the assembly into the divot:

    magnet  |  coupon  |  magnet  |  band floor

**The mounting constrains the reporting denominator in two ways at once.** The lower face is
not a free growth surface: its center is covered by the lower magnet and its annulus faces the band
floor across the magnet thickness, a dark, near-zero-shear crevice. The upper face loses the
magnet's footprint. So the lit, sheared, modeled surface is one face net of one magnet:

| quantity | value |
|---|---|
| one whole face | 15.751 cm² |
| magnet footprint, 19.05 mm dia | 2.850 cm² (18.1 % of a face) |
| **`A_exp` = one face − one magnet** | **12.901 cm² = 0.001290 m²** ← the denominator |

This supersedes the previous "both faces, 28.670 cm²" denominator, a **2.22× reduction**. To be
precise about what it does and does not change: `J_A` is *per* unit area and is unaffected;
everything *per coupon* — harvestable biomass, assay sufficiency — falls by 2.22×.

**Deliberately excluded, and both make the harvest estimate a lower bound:**

- the underside crevice annulus, another 12.90 cm² — wetted and colonizable but unlit and
  essentially unsheared, a different environment this one-compartment model does not simulate;
- the four edges, 3.18 cm² at a 2 mm placeholder thickness — excluded to stay consistent with
  the projected-area convention in §5.

**A measurement discrepancy, recorded rather than resolved.** Caine's fabricated coupon measures
36.2 ± 0.3 × 39.6 ± 0.1 mm from his scale photo at 26.8 px/mm over ten cut lines. The 39.6 mm
axis matches the 1 9/16 in specification to 0.1 mm; the other axis is about 3.5 mm narrow. The
simulator uses the square specification, so nominal area is **1.0988×** the as-fabricated area —
a result read against the nominal denominator is biased about 9.9 % low.

## 7. Placeholders

Values marked **placeholder** are best estimates committed so the model can run. They are not
measurements and no conclusion should rest on them; they are listed for replacement in
`FIELD_MEASUREMENTS_RBC1.md`.

| quantity | value | provenance | confidence |
|---|---|---|---|
| media disc / end-plate diameter | 2.0 m | **placeholder** | **low** — measure first |
| shaft span between plates | 1.8288 m | **reported** (6 ft, Anthony) | high |
| band radius | r/R = 0.95 | **placeholder** | medium |
| bands | 2, at 0° and 180° | **reported** | high |
| divots per band | 4, two near each end | **placeholder** | medium |
| coupons per divot | 9 | **reported** | high |
| divot cavity | 140 × 140 mm, 10 mm deep | **placeholder** | **low** |
| coupon recess below band face | 3 mm | **placeholder** | **low** |
| **shelter factor φ_shear** | **0.3 / 0.5 / 1.0 sampled** | **no source at all** | **lowest** |
| divot view factor | 0.90 | **placeholder** | **low** |
| submergence | 40 % areal | RBC standard | medium |
| waterline depth | 0.1577 R | derived from submergence | derived |
| rotation now | 4.0 rpm | **reported** (plant) | high |
| band tip speed @ 4 rpm | 0.398 m s⁻¹ | derived (guideline ≈0.30) | derived |
| coupon | 39.6875 mm square | **reported** (specification) | high |
| magnet | 19.05 mm dia × 6.35 mm thick | dia **reported**, thickness **placeholder** | medium |
| lamp fixtures | 6, three per end, in cover holes | **reported** | high |
| lamp height above waterline | 0.5 m | **placeholder** | low |
| cover hole diameter | 150 mm | **placeholder** | low |
| ambient daylight | none — indoor, under cover | **reported** | high |
| photoperiod | 15.50 / 8.87 h timer | **computed** — Rapid City 44.0805 °N solstices | high |
| bulk NH₄-N | 30 mg L⁻¹ | plant records / technical memorandum | medium |
| bulk BOD₅ | 72 / 120 mg L⁻¹ | plant lab records range | medium |
| temperature | 15 °C | plant band 12.2–18.3 °C | high |
| bulk DO | from `params_v2.yaml` | **assumed** | **low** — ask if logged |
| roughness `r` | 1.01 / 1.02 / 1.02 / undefined | **placeholder** — no coupon profiled | **low** |
| assay minima | 1.0 / 0.5 / 0.05 mg | **placeholder** — not from a protocol | low |

## 8. Assumptions

1. **No optical cross-contamination between the two ends.** Asserted by the project team and
   carried as a **limitation**, not a result. With lamps 6 ft apart in a shared cover and bands
   that may run outside the wafer pack, some light from one end's fixtures will reach the other
   end's coupons. That crosstalk is not modeled, so the contrast between the two photoperiods
   is an **upper bound** on what the rig will deliver. Baffling or shrouding the fixtures is
   cheap before fabrication and impossible after.
2. **Timescale separation.** Rotation (15–120 s) and the lamp timer (hours) are treated as
   independent, so the joint light duty is their product. Justified by roughly three orders of
   magnitude of separation, but it is an assumption.
3. **Pulsed light integrates.** Light arriving in short pulses is treated as a time average for
   photosynthesis. Flashing-light enhancement occurs at far higher frequencies; not tested here.
4. **The divot shelter is a single scalar.** One factor dims the lamp and another scales the
   shear; in reality both depend on recess depth, divot wall angle and the coupon's angular
   phase relative to the fixture. Not represented.
5. **Coupons do not perturb the bulk.** Safe at plant scale; it is what makes `a_v` inert.
6. **The two bands are replicates, not treatments.** Angular position on a turning wheel is a
   phase, not a location, so bands at 0° and 180° sample the same duty cycle. This holds only if
   their divots are at matched axial positions and matched depths. Note that with 8 divots over
   2 bands, each material × photoperiod appears on exactly **one** band, so band is confounded
   with material and the three coupons per harvest are within-divot replicates.
7. **No drying when emergent.** Reasonable in a humid indoor building at 12–18 °C; **fails if the
   wheel stops**, which is why stoppages must be logged.
8. **Isothermal.** Every arm runs at a fixed temperature; the plant's seasonal swing is explored
   by changing that temperature, not by driving a time series.

## 9. Known discrepancies, recorded rather than tuned away

1. At low feed BOD the areal nitrification rate reaches values above the literature band. The
   areal form is linear in nitrifier biomass and the model runs far from its calibration point.
2. No inert or EPS fraction, so film thickness sits at **59–124 µm**, below the 151–412 µm
   reported on RBC media by Hassard et al. (2014). Because the film stays thin, oxygen never
   limits, so phototrophic oxygen production buys the nitrifiers nothing while the phototrophs
   still occupy film capacity. The modeled light effect on nitrification is therefore one-sided
   by construction — which is why §10.3 shows photoperiod moving biomass but not flux.
3. **Graphene-coated steel is distinguished from bare steel only by a maturation factor** with a
   fitted onset at 5.9 d. The consequence for the experiment is in §10.5 and it is severe.
4. `f_occ` is exploratory and simulation-only; on flat coupons it is ≈0 and carries no weight.
5. The laminar shear correlation is out of range at 4 rpm (§4).
6. Raman work on the graphene coupon suggests the coating covers **under half** the surface at
   micron scale, so that arm should be read as an area-weighted mixture. **Not represented.**
7. **The fabric's fiber-scale area is not in the model.** A fabric sheet is treated as a solid
   slab, so its `a_geo` (171.7 m²/m³ flat) sits only 13 % above HDPE's (151.9), and that 13 %
   comes from sheet thickness, not fibers. A real nonwoven carries of order 7–16 m² of fiber per
   m² of footprint. The fabric's entire advantage therefore sits in its attachment factor, which
   means **unmeasured area is currently being read as a material effect**. The arithmetic is
   self-consistent because the denominator is projected area throughout, but the attribution is
   not established. If a supplier figure for true fiber area is adopted, the attachment factor
   must be re-derived against it rather than kept alongside it.
8. **The underside crevice is not simulated** (§6), so every per-coupon biomass figure is a
   lower bound.

## 10. Results from the 864-arm band-mounted grid

4 materials × 2 photoperiods × 6 rotation rates × 3 shear exponents × 3 shelter levels × 2 feed
loads = **864 arms**, 60 days, 15 °C. All converged; none non-finite.

**1. The material ranking is invariant from day 7 onward.** `fabric > HDPE > bare steel >
graphene-coated steel` holds in **all 216** conditions at days 7, 10 and 60, with no inversion.
Mean flux relative to HDPE: fabric **1.37×**, bare steel **0.76×**, graphene **0.57×** at day 60.
Subject to the fabric-area caveat in §9.7.

**2. Detachment is helping, and sheltering the coupons hurts.** With the shear exponent at 1,
raising the shelter factor from 0.3 to 1.0 — i.e. moving the coupon flush with the band —
**raises** day-60 flux by 2.2–2.6× (fabric 0.149 → 0.381, HDPE 0.135 → 0.291 g N m⁻² d⁻¹). More
shear strips film, the thinner film oxygenates and lights better, and flux rises. A deep divot
is a comfortable place for a coupon and a poor place for nitrification.

**3. Photoperiod moves biomass but barely moves flux.** Summer yields more total biomass in
every arm, but day-60 flux differs by under 1 % for HDPE and bare steel, and is very slightly
**higher in winter** for graphene. The mechanism is the one identified earlier: phototrophs
crowd nitrifiers out of the shared capacity term, and because the film is too thin for oxygen
ever to limit (§9.2), the phototrophs' oxygen production returns nothing.

**4. Rotation rate has a genuine optimum for the steels.** At `n_shear` = 1 and no shelter,
day-60 flux for bare steel peaks at **2.5 rpm** (0.312) and falls at 4 rpm (0.301); graphene
peaks at 2.5 rpm (0.234) and falls to 0.229. Fabric and HDPE keep rising to 4 rpm. This is the
oxygen-penetration-versus-shear trade-off of §3 appearing as a turning point.

**5. The proposed harvest schedule cannot test the graphene hypothesis.** Graphene and bare
steel differ in this model only through a maturation factor with onset 5.9 d, so:

| harvest | GRA vs STL, areal biomass | GRA vs STL, flux |
|---|---|---|
| day 5 | **0.000 %** — identical to machine precision in all 216 arms | 0.000 % |
| day 7 | 0.010 % | 0.104 % |
| day 10 | 0.257 % | 1.09 % |
| day 60 | 7.75 % | 24.3 % |

Through day 10 the gap stays under 0.3 % of biomass, far inside coupon-to-coupon scatter at
n = 3. Usable separation arrives past roughly day 21. This is a statement about the model's
structure as much as about the coating: the model contains **no early-time mechanism** —
wettability, coverage fraction — that could produce an early difference, and the real coupons
might. Reported as a design finding, not a prediction of null result.

**6. Every harvest clears every assay minimum.** The worst arm yields **45.0 mg** from the three
day-5 coupons against a 1.0 mg dry-weight threshold — and that is the lower bound of §6, which
excludes the crevice and the edges.

**7. 144 of 864 arms (all 4 rpm) are outside the laminar correlation's range** and are flagged
rather than reported silently.

**8. The three guilds do not share a driver**, which is why they are reported separately rather
than summed. Total Sobol indices on the same factorial, by response:

| design factor | total biofilm | phototrophs | nitrifiers | heterotrophs | removal flux |
|---|---|---|---|---|---|
| material | 0.466 | **0.627** | **0.601** | 0.082 | **0.502** |
| photoperiod | 0.076 | **0.228** | 0.003 | 0.007 | 0.001 |
| wheel speed | 0.076 | 0.077 | 0.161 | 0.014 | 0.180 |
| shear exponent | 0.250 | 0.280 | **0.509** | 0.040 | 0.488 |
| divot shelter | 0.027 | 0.029 | 0.055 | 0.005 | 0.056 |
| feed load | 0.313 | 0.008 | 0.005 | **0.891** | 0.063 |

Heterotrophs are set by substrate supply and almost nothing else. Phototrophs are the only
response photoperiod moves. Nitrifiers are set by material and by how hard the film is stripped.
Material leads for every response except heterotrophs, so the screening question the study was
built to answer is well posed for the guilds the permit depends on. Details, including the per-guild
attribution, are in the Sensitivity tab.
