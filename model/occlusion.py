"""Occlusion and the areal-to-volumetric aggregation rule.

f_occ is the share of colonised surface lost when the film bridges a pore. It is
EXPLORATORY and SIMULATION-ONLY (ruling of 31 October 2026): computed and
reported, with no measured counterpart claimed and no weight in the headline
ranking, which is reported with and without it.

The aggregation rule is the binned weighted sum

    r_v = a_geo * sum_b w_b * f_col_b * (1 - f_occ_b) * r_a_b

with w_b the area fraction of irradiance bin b. With a single bin this reduces
exactly to the manuscript's a_eff * J_A, so the binned form generalises the
published equation rather than replacing it (see `single_bin_equivalence`).

CAUTION, enforced by assertion in `volumetric_rate`: r_a must be defined per
unit of COLONISED, NON-OCCLUDED area. If it already carries those losses, the
f_col and (1 - f_occ) factors discount them a second time.
"""
from __future__ import annotations
import numpy as np

OCCLUSION_RATIO = 0.5   # film bridges when it reaches half the local aperture (this study's choice)


def f_occluded(L_f_mm, aperture_quantiles_mm, quantiles=None, ratio=OCCLUSION_RATIO):
    """Share of pores bridged: the aperture CDF evaluated at L_f / ratio.

    The CDF is INTERPOLATED, not counted. Counting a finite quantile sample makes
    f_occ a step function of film thickness, and because the apertures come from a
    voxel distance transform those steps sit at voxel-distance shells -- which would
    read as physical events in a time series when they are purely numerical.
    """
    ap = np.sort(np.asarray(aperture_quantiles_mm, float))
    q = np.linspace(0.0, 1.0, len(ap)) if quantiles is None else np.asarray(quantiles, float)
    thresh = np.atleast_1d(np.asarray(L_f_mm, float)) / ratio
    return np.clip(np.interp(thresh, ap, q, left=0.0, right=1.0), 0.0, 1.0)


def f_colonised(X_total, coverage_scale=2.0):
    """Colonised fraction from areal biomass, the project's existing coverage form."""
    return 1.0 - np.exp(-np.asarray(X_total, float) / coverage_scale)


def volumetric_rate(a_geo, w, f_col, f_occ, r_a, apply_occlusion=True):
    """Binned weighted sum. r_a MUST be per unit colonised, non-occluded area."""
    w = np.asarray(w, float)
    occ = (1.0 - np.asarray(f_occ, float)) if apply_occlusion else 1.0
    return float(a_geo * np.sum(w * np.asarray(f_col, float) * occ * np.asarray(r_a, float)))


def single_bin_equivalence(a_geo, f_col, f_occ, J_A):
    """The manuscript's a_eff * J_A, for the one-bin check."""
    a_eff = a_geo * f_col * (1.0 - f_occ)
    return a_eff * J_A, a_eff
