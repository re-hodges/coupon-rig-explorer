# Apple Springs coupon-scale biofilm model

A three-guild biofilm model of a single carrier coupon in a stirred, illuminated vessel
of synthetic wastewater, together with an interactive page for exploring what the bench
experiment it was built for could measure.

**[Open the interactive explorer](https://USERNAME.github.io/REPOSITORY/)** &mdash; replace
`USERNAME` and `REPOSITORY` once GitHub Pages is switched on.

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
| `model/build_page.py` | Rebuild `index.html` from that grid and `MODEL.md` |
| `model/explorer_data.json` | The precomputed grid, already inlined into `index.html` |

The remaining `.csv` files in `model/` are inputs: the carrier geometry catalog, the
irradiance bin weights, the pore-aperture quantiles, and the recorded output of a Morris
sensitivity screen quoted in `MODEL.md` §5.

## Running it

```bash
pip install -r requirements.txt
python model/run_demo.py
```

Everything runs from the repository root. See `MODEL.md` §7 for the Python API.

## Rebuilding the page

`index.html` has the parameter grid and the rendered `MODEL.md` baked into it, so it
needs no server at runtime. Both are generated &mdash; do not edit them by hand:

```bash
python model/build_explorer.py   # only if parameters or the grid definition changed
python model/build_page.py       # always, after changing MODEL.md or the grid
```

`build_explorer.py` runs 1,260 simulations and takes well over an hour on one core.
`build_page.py` takes a second.

## Publishing the page

The explorer is a single static file, so GitHub Pages serves it with no build step:

1. Push this repository to GitHub, with `index.html` at the root.
2. Go to **Settings &rarr; Pages**.
3. Under **Build and deployment**, set **Source** to *Deploy from a branch*.
4. Choose branch `main` and folder `/ (root)`, then **Save**.
5. Wait a minute or two. The page appears at `https://USERNAME.github.io/REPOSITORY/`.

The repository must be public for Pages on a free account; Pages from a private
repository needs GitHub Pro. The empty `.nojekyll` file at the root tells GitHub to serve
the files as they are rather than running them through Jekyll.

`index.html` is about 2.3 MB because the parameter grid and the rig images are embedded
in it. That is well inside Pages' limits, but the whole file downloads before anything
appears. If that becomes annoying, split `explorer_data.json` and the images back out as
separate assets and fetch them &mdash; the single-file design exists only so the page can
be opened straight from disk.

## Status

`MODEL.md` §5 marks every parameter as measured, taken from literature, or unmeasured,
and §6 lists what the model does not include. The two parameters it is most sensitive to,
`K_comp` and `rN_ref`, are both unmeasured.
