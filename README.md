# Apple Springs coupon-scale biofilm model

A three-guild biofilm model of carrier coupons riding the first-stage RBC at the Apple
Springs plant, together with an interactive page for exploring what the coupon campaign it
was built for could measure.

**[Open the interactive explorer](https://re-hodges.github.io/coupon-rig-explorer/)**

The model tracks phototrophs, nitrifiers and heterotrophs growing as a film on a coupon
held in a divot on one of the wheel's two steel bands, and follows the ammonia the film
removes from the liquid. Because the coupons sit in the plant's own tank, the bulk is
imposed rather than solved: the model reports how much biomass sits on a coupon, how that
divides between the three guilds, how thick the film becomes, and the **areal removal
flux** — ammonia-nitrogen removed per square metre of exposed coupon per day.

**These are predictions from an uncalibrated model. No coupon has been harvested yet, and
nothing here has been fitted to a measured flux.**

## What is here

| Path | What it is |
|---|---|
| `MODEL.md` | The model: the system, the equations, the duty cycle, shear, the area convention, placeholders, assumptions, known discrepancies, results |
| `GLOSSARY.md` | Every symbol beside its field-standard equivalent (IWA ASM, Wanner–Gujer, ISO 25178, Wenzel) |
| `DATA_SOURCES.md` | Where every number comes from, graded strongest to weakest, including what has no source at all |
| `SENSITIVITY.md` | What the sensitivity analyses compute, how, and what they found |
| `index.html` | The interactive explorer &mdash; one self-contained file, no server or network needed |
| `model/reactor.py` | The three-guild reactor: growth, decay, attachment, detachment, oxygen penetration |
| `model/reactor_v2.py` | The RBC subclass: rotation duty cycle, shear-modified detachment, delivered light |
| `model/rbc.py` | Wheel geometry — wet fraction, wall shear, the laminar regime check |
| `model/area.py` | The reporting denominator: one coupon face net of its magnet |
| `model/params_v2.yaml` | Parameter values, each with its source |
| `model/rig.yaml` | Rig geometry and the coupon layout |
| `model/test_v2.py` | Nine regression and unit tests |
| `model/build_grid_v3.py` | Precompute the 864-arm parameter grid |
| `model/build_page_v3.py` | Rebuild `index.html` from that grid, the figures and the four docs |
| `model/grid_v3.json` | The precomputed grid, already inlined into `index.html` |
| `model/_scene_js_v3.txt` | The canvas renderer behind the 3D tab |
| `model/sa_*.py` | The sensitivity analyses — design, execution, analysis and figures |
| `model/fig_sa_*.png` | The eight sensitivity figures, already inlined into `index.html` |

The remaining `.csv` files in `model/` are the data behind the numbers. The carrier geometry
catalog and the irradiance bin weights are read at run time; the pore-aperture quantiles and
the shear reference set record where two parameter values came from and are cited in
`DATA_SOURCES.md`; the `sa_*.csv` files are the recorded sensitivity results that the figures
and `SENSITIVITY.md` quote.

## Running it

```bash
pip install -r requirements.txt
python model/test_v2.py
```

Everything runs from the repository root.

To rebuild the page after changing the model, the docs or a figure:

```bash
python model/build_grid_v3.py     # 864 arms, a few hours
python model/build_page_v3.py     # rewrites index.html, seconds
```

The sensitivity sweeps are not shipped as raw run data because they are large and
regenerable. `model/sa_design.py` and `model/sa_ode_design.py` write the designs,
`model/sa_worker.py` and `model/sa_ode_worker.py` execute them in shards, and
`model/sa_ode_analyze.py`, `model/sa_givendata.py` and the `sa_fig_*.py` scripts turn them
into the tables and figures that are shipped. One model run takes about two seconds.

## What this model does not do

It does not predict the plant. The bulk is an imposed boundary condition, no coupon flux has
been measured, and the single most influential parameter in the model — the half-saturation
of heterotroph crowding on nitrifiers — has no source at all. `DATA_SOURCES.md` grades every
input on that basis and `SENSITIVITY.md` ranks them by influence; read the two together.
