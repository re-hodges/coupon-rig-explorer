# Sensitivity analysis

**Every index reported here is computed on the differential equations themselves.** Nothing
is fitted to approximate the model, and no machine learning is involved anywhere — in the
model or in its analysis.

## What is computed

| Analysis | Runs on | Cost | What it answers |
|---|---|---|---|
| Exact factorial | the 864-arm grid | already run | exact variance shares for the **design factors** the team sets |
| Morris elementary effects | the ODE | 400 runs | screening: which inputs move the output at all; `sigma` flags non-linearity |
| SRC / SRRC + R² | the ODE, 4,096 runs | free | signed linear and monotone ranking, **with the R² that says whether a regression ranking is usable at all** |
| PRCC | the ODE, 4,096 runs | free | signed monotone association with every other input partialled out |
| Borgonovo delta | the ODE, 4,096 runs | free | moment-independent: how far the whole output **distribution** shifts |
| PAWN | the ODE, 4,096 runs | free | CDF-based importance, robust to the skew in `J_A` |
| RBD-FAST | the ODE, 4,096 runs | free | first-order indices without a Saltelli design |
| Sobol' S1 / S_T | the ODE | 5,632 runs | variance decomposition **including interactions**, with bootstrap CIs |
| Exact Shapley | the ODE | 3,072 runs | per-arm signed attribution in g N m⁻² d⁻¹ |
| Grouped Shapley | the ODE | 96 runs | the same, aggregated to surface / environmental / biological |
| Multiplicative decomposition | the ODE | 1 run per arm | exact term-by-term account of a single prediction |

"Free" means the method consumes an input/output sample that already exists, so it costs no
new integrations.

## Exact Shapley

For a chosen set of *k* inputs, **every one of the 2^k coalitions is evaluated on the ODE**.
A member of a coalition takes the arm's value, a non-member takes the baseline value. The
Shapley value is then the exact weighted average of marginal contributions over all orderings
— no sampling, so no sampling error, and the efficiency property holds to machine precision
rather than being asserted by a test. It is checked anyway (`sa_ode_analyze.py` aborts if
`sum(phi)` misses `v(full) - v(empty)`); the residual is 3.3e-16.

The price is that *k* must stay small, and the remaining inputs are held at baseline, so the
decomposition explains the gap between the arm and the baseline **through those k inputs**.

- **k = 8**, the highest-`mu_star` inputs: `K_comp`, `X_cap`, `rN_ref`, `rpm`, `n_shear`,
  `k_det`, `shelter`, `k_att`. 256 coalitions per arm.
- **12 arms**, three per material, drawn at evenly spaced quantiles of day-60 flux.
- **Grouped** over surface / environmental / biological, where material toggles with the
  surface group. 8 coalitions per arm.

**The baseline.** `params_v2.yaml` nominals for the 14 physical parameters, the wheel at its
as-found 4 rpm, the shear exponent and divot shelter at the midpoints of their disputed
ranges, the lamp timer at the midpoint of the two solstice photoperiods, and feed BOD at
~100 g m⁻³. A Shapley value is always relative to a baseline: quoted attributions mean
"relative to the nominal arm". That nominal arm has `J_A` = 0.456 g N m⁻² d⁻¹, which is the
**83rd percentile** of the sampled flux range, so most explained arms fall below it and their
signed attributions are negative.

## The multiplicative decomposition

`J_A` is a product of terms. In logarithms a product is a sum, and a sum decomposes exactly
with no residual and no attribution scheme required. This yields a per-arm waterfall that is
a *complete* account of one prediction, attributing to the physics terms rather than to the
parameters behind them. Maximum relative residual over the 12 arms: 3.5e-16.

Five factors carry no bin index (`rN_ref`, the ammonia Monod term, the Arrhenius factor,
`f_wet`, the oxygen Monod term) and factor straight out. The four bin-dependent factors
(nitrifier biomass ratio, heterotroph crowding, remaining film space, oxygen effectiveness)
are decomposed by a chain of partial sums, which telescopes exactly but is order-dependent:
each is credited with its effect *given* the ones before it.

## Evidence scoring

`sa_evidence.csv` grades every input on the strength of the evidence behind its value, using
the categories in `DATA_SOURCES.md`, which run strongest to weakest. The ordinal score exists
so the grading can be plotted against influence; it is a rendering of the tier, not an
independent judgement.

| score | tier |
|---|---|
| 4 | measured here — instrumented measurement on this system |
| 3 | field record, literature on the same system type, or computed exactly |
| 2 | literature on an analogue system, calibrated, or a stoichiometric estimate |
| 1 | inherited from the plant reference model, or a declared choice of this study |
| 0 | no source — nobody has measured it |

The grading sits in one column precisely so a reviewer who disagrees can re-score it and
redraw `fig_sa_evidence_impact.png` without touching anything else.

## Results

**`K_comp` rules the flux and has no source.** Rank 1 by every measure: Morris `mu_star` =
0.934, exact Shapley mean |phi| = 0.119 g N m⁻² d⁻¹, Sobol' S_T = 0.476 ± 0.123. Then
material 0.250, `rN_ref` 0.195, `X_cap` 0.172, `k_det` 0.150.

**Rank separability.** At N = 256 only **4 of 19 adjacent pairs** separate at 95 %. `K_comp`
clears the next input ([0.353, 0.598] against material's [0.161, 0.340]) and is the one rank
this design licenses. Below it, `material`, `rN_ref`, `X_cap` and `k_det` are a band, not an
order.

**The model is monotone but not linear.** For the flux a linear description captures
R² = 0.630 of its own variance, a monotone one 0.826. Rank-based rankings are therefore
usable and raw linear coefficients are not. Per response, R²(SRRC): heterotrophs 0.860,
flux 0.826, phototrophs 0.794, total biofilm 0.762, nitrifiers 0.729. **These describe how
linear the model's own response is. They say nothing about agreement with measurement.**

**Crowding is the throttle; oxygen is not.** Heterotroph crowding removes **61–86 %** of the
flux across arms, while the oxygen effectiveness factor is **exactly 1.00 in every arm** —
the film never gets thick enough for oxygen to limit. That is the mechanism behind
photoperiod moving biomass but not flux.

**Material leads every response except two.** It takes the largest share of total biofilm,
phototrophs and nitrifiers; heterotrophs are ruled by feed substrate and the flux by
`K_comp`.

## Reading these numbers

1. **Ranking and ignorance are entangled.** An input's influence is measured over the range
   it was swept, and the widest ranges belong to the inputs nobody has measured. Read the
   ranking as *"what would be most worth measuring"* — not as *"which physical process
   matters most"*.
2. **Two denominators for material.** The factorial gives material S_T = 0.502 as a share
   among the **six design factors**; the Sobol' run gives 0.250 as a share among **all 20
   inputs**. Both are correct and they answer different questions. Do not quote one against
   the other.
3. **Runs are at 15 °C**, so the Arrhenius coefficients are live inputs here.
4. **Morris holds material fixed at HDPE**, so material carries no `mu_star`; its influence
   comes from the factorial and from the Sobol' run.
5. **Delta and PAWN carry a positive noise floor** at this sample size. Their lower half is
   not rankable. Where they disagree with the variance-based and monotone measures, the
   Sobol' run on the ODE is the arbiter.
6. **Identifiability was not assessed.** Whether `K_comp` can be estimated from the planned
   day 5/7/10 harvests, or whether it trades off against `k_att` and `X_cap`, is a separate
   analysis and has not been run.
