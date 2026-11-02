# Apple Springs coupon-scale biofilm model

A three-guild biofilm model of a single carrier coupon in a stirred, illuminated vessel
of synthetic wastewater, together with an interactive page for exploring what the bench
experiment it was built for could measure.

**[Open the interactive explorer](https://re-hodges.github.io/coupon-rig-explorer/)**

The model tracks phototrophs, nitrifiers and heterotrophs growing as a film on a coupon,
plus a suspended pool of cells that have not yet attached, and follows the ammonia,
nitrate, phosphorus and organic matter they draw out of the liquid. It reports how much
biomass sits on the coupon, how that is divided between the three groups, and how fast
ammonia disappears.

**These are predictions from an uncalibrated model. No coupon has been harvested yet.**

## What is here

| Path | What it is |
|---|---|
| `MODEL.md` | The model: scope, state variables, the nine equations, scaling, parameters, exclusions |
| `GLOSSARY.md` | Definitions of the terms and symbols used in `MODEL.md` |
| `index.html` | The interactive explorer &mdash; one self-contained file, no server or network needed |
| `model/reactor.py` | The model itself |
| `model/params_v2.yaml` | Parameter values, each with its source |
| `model/rig.yaml` | Bench-rig geometry and feeding protocol |
| `model/run_demo.py` | Run one arm and print a summary |
| `model/build_explorer.py` | Precompute the 1,260-run parameter grid |
| `model/build_page.py` | Rebuild `index.html` from that grid, the rig scene and `MODEL.md` |
| `model/build_rig_scene.py` | Build the rig geometry and lamp field for the 3D tab |
| `model/rig_scene.json` | That geometry and light field, already inlined into `index.html` |
| `model/explorer_data.json` | The precomputed grid, already inlined into `index.html` |

The remaining `.csv` files in `model/` are inputs: the carrier geometry catalog, the
irradiance bin weights, the pore-aperture quantiles, the per-vessel lamp field behind the
3D tab, and the recorded output of a Morris sensitivity screen quoted in `MODEL.md` §5.

## Running it

```bash
pip install -r requirements.txt
python model/run_demo.py
```

Everything runs from the repository root. See `MODEL.md` §7 for the Python API.
