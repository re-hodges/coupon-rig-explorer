"""Coupon area convention for explorer v2 -- the APPROVED decision, encoded.

THE DECISION (user, 4 Nov 2026)
-------------------------------
Every areal quantity in this model is reported per PROJECTED area, and the roughness
ratio r = 1 + Sdr acts ONLY through the attachment term. r is never used as an area
multiplier.

Three reasons, in order of weight:

1. It avoids a double-count the roughness twinlet already identified
   (STEP1_surface_roughness_definitions.md, section 2.6 caveat 4): the same r scales
   wetting through Wenzel (1936), the ensemble already samples wettability for steel
   and fabric, and adding an r-driven AREA term on top would count one physical cause
   twice. Gross et al. (2016) use r as the attachment texture variable -- that is
   where it belongs.
2. At flat-coupon scale the area credit is negligible. Exact arc-length integration
   over a sinusoidal texture gives r = 1.006 at h/lambda = 0.05 and 1.024 at 0.10.
   Reaching the r ~ 1.5 band needs h/lambda ~ 0.52, features as tall as they are
   wide -- that is mesh and texture scale, i.e. the GEOMETRY axis, where a_geo from
   the CAD mesh already captures it. The physics is not dropped, it is assigned to
   the axis that carries it.
3. A_true is not well-posed for the non-woven fabric. A height map cannot represent
   undercuts and fibers always undercut, so ISO 25178 areal parameters are formally
   undefined there (STEP1 caveat 3) -- and the fabric is the material the model
   currently ranks highest. Projected area is defined for all four materials.

COUPON AND MOUNT -- REVISED 4 Nov 2026 (Anthony's rig description)
------------------------------------------------------------------
The coupon is a SQUARE of side 1 9/16 in = 39.6875 mm (stated specification). It is
held in a magnet sandwich -- one round magnet above, one below -- and the lower
magnet clamps the assembly into a divot in the steel band. The stack is therefore

        magnet  |  coupon  |  magnet  |  band floor

which changes the reporting denominator in two ways at once:

  * the LOWER face is no longer a free growth surface: its center is covered by the
    lower magnet and its annulus faces the band floor across the magnet thickness,
    a dark, near-zero-shear crevice;
  * the UPPER face loses the magnet's footprint.

So the lit, sheared, modeled surface is ONE face net of one magnet:

        A_exp = s^2 - pi d^2 / 4 = 15.751 - 2.850 = 12.901 cm^2

This SUPERSEDES the previous "both faces, 28.67 cm^2" denominator, a 2.22x reduction.
A_exp is what J_A is reported per, and what the model's light and shear terms act on.

DELIBERATELY EXCLUDED, and both make the harvest estimate a LOWER BOUND:
  * the underside crevice annulus (another 12.90 cm^2) -- wetted and colonisable but
    unlit and essentially unsheared, i.e. a different environment that this one-
    compartment model does not simulate;
  * the four edges (3.18 cm^2 at a 2 mm placeholder thickness, ~20% of a face) --
    excluded to stay consistent with the projected-area convention above.

MEASUREMENT DISCREPANCY, recorded not resolved
----------------------------------------------
Caine's fabricated coupon measures 36.2 +/- 0.3 x 39.6 +/- 0.1 mm from his scale
photo (Gr67 Scale .jpg) at 26.8 px/mm over ten cut lines. The 39.6 mm axis matches
the 1 9/16 in specification to 0.1 mm; the other axis is ~3.5 mm narrow. The user
ruled on 4 Nov 2026 that the SIMULATOR uses the square specification. Nominal area
is 1.0988x the as-measured area, so a fabricated-coupon result read against the
nominal denominator is biased ~9.9% low.
"""
from __future__ import annotations
import numpy as np

# --------------------------------------------------------------- coupon + mount
COUPON_SIDE_MM = 39.6875          # 1 9/16 in, square -- STATED specification
COUPON_SPEC = "specified square 1 9/16 in (user, 4 Nov 2026); simulator uses nominal"
COUPON_MEASURED_MM = (36.2, 39.6) # as fabricated, from the scale photo
COUPON_THICK_MM = 2.0             # PLACEHOLDER, used only for the excluded edge area

MAGNET_D_MM = 19.05               # 3/4 in -- STATED (read as diameter)
MAGNET_T_MM = 6.35                # PLACEHOLDER (1/4 in); sets the crevice gap
MAGNET_PROVENANCE = "diameter stated by user 4 Nov 2026; thickness is a placeholder"

N_FACES_EXPOSED = 1               # upper face only -- see module docstring

# Roughness ratio r = 1 + Sdr per material. ALL PLACEHOLDERS -- no coupon has been
# profiled. Solid materials sit near 1 because a flat finish adds almost no area;
# the fabric is marked None because r is formally undefined on a re-entrant surface.
R_ROUGHNESS = {
    "PE":  (1.01, "placeholder", "smooth extruded sheet; h/lambda well under 0.1"),
    "STL": (1.02, "placeholder", "rolled finish, anisotropic; Str -> 0"),
    "GRA": (1.02, "placeholder", "inherits the steel substrate texture"),
    "FAB": (None, "undefined",  "re-entrant fibers; ISO 25178 areal parameters undefined"),
}


# --------------------------------------------------------------------- areas
def face_area_m2(side_mm: float = COUPON_SIDE_MM) -> float:
    """Area of one whole coupon face, m2."""
    return (side_mm * 1e-3) ** 2


def magnet_footprint_m2(d_mm: float = MAGNET_D_MM) -> float:
    """Area one round magnet hides, m2."""
    return np.pi * (d_mm * 1e-3) ** 2 / 4.0


def exposed_area_m2(n_coupons: int = 1, side_mm: float = COUPON_SIDE_MM,
                    d_mm: float = MAGNET_D_MM) -> float:
    """A_exp -- THE reporting denominator: upper face net of the magnet footprint."""
    return n_coupons * N_FACES_EXPOSED * (face_area_m2(side_mm) - magnet_footprint_m2(d_mm))


def crevice_area_m2(n_coupons: int = 1, side_mm: float = COUPON_SIDE_MM,
                    d_mm: float = MAGNET_D_MM) -> float:
    """Underside annulus facing the band floor. Colonisable, unlit, unsheared,
    NOT simulated and NOT in the denominator -- reported so the omission is visible."""
    return n_coupons * (face_area_m2(side_mm) - magnet_footprint_m2(d_mm))


def edge_area_m2(n_coupons: int = 1, side_mm: float = COUPON_SIDE_MM,
                 t_mm: float = COUPON_THICK_MM) -> float:
    """Four coupon edges. Excluded by the projected-area convention; reported only."""
    return n_coupons * 4.0 * (side_mm * 1e-3) * (t_mm * 1e-3)


# Back-compatible name. Every caller that wants "the denominator" gets A_exp.
def projected_area_m2(n_coupons: int = 1, **kw) -> float:
    """Alias for `exposed_area_m2`; kept so existing call sites keep working."""
    return exposed_area_m2(n_coupons=n_coupons, **kw)


def true_area_m2(material, **kw):
    """A_exp * r. COMPUTED AND DELIBERATELY UNUSED as a denominator.

    Returns None for the fabric, where r is undefined. Present so the decision is
    auditable: anyone can see what the alternative convention would have given.
    """
    r = R_ROUGHNESS.get(material, (None,))[0]
    if r is None:
        return None
    return exposed_area_m2(**kw) * r


def attachment_roughness_factor(material) -> float:
    """The ONE place r is allowed to act: a multiplier on the attachment rate.

    Returns 1.0 when r is undefined (fabric), so the fabric's advantage continues to
    come from its measured Gross et al. colonization factor and not from an
    ill-posed roughness term.
    """
    r = R_ROUGHNESS.get(material, (None,))[0]
    return 1.0 if r is None else float(r)


# ------------------------------------------------------------ assay sufficiency
# Replaces v1's "drag coupon area up and watch the vessel starve" demo, which has no
# referent once the coupons sit in the plant's own tank: a few hundred cm2 of coupon
# cannot draw down a first-stage RBC. The question that DOES matter now is whether a
# coupon yields enough biomass to assay at the early harvests -- days 5, 7 and 10,
# three coupons each, per Anthony's harvest plan.
ASSAY_MIN_MG = {
    "dry_weight":   1.0,   # analytical balance, 0.1 mg resolution, 10x for 1% precision
    "chlorophyll":  0.5,
    "qPCR_DNA":     0.05,
}
ASSAY_PROVENANCE = "placeholder - typical bench minima, not quoted from a protocol"
HARVEST_DAYS = (5, 7, 10)
COUPONS_PER_HARVEST = 3


def harvestable_mg(X_areal_g_m2, n_coupons: int = 1, **kw) -> float:
    """Dry biomass recoverable from the MODELED surface of n coupons, mg.

    A LOWER BOUND on what a scrape yields: the underside crevice and the edges carry
    film too, and neither is simulated.
    """
    return float(X_areal_g_m2) * exposed_area_m2(n_coupons=n_coupons, **kw) * 1000.0


def assay_sufficiency(X_areal_g_m2, n_coupons: int = COUPONS_PER_HARVEST, **kw) -> dict:
    """Which assays one harvest (default: the 3 coupons pulled together) supports."""
    mg = harvestable_mg(X_areal_g_m2, n_coupons=n_coupons, **kw)
    return {"harvest_mg": mg, "n_coupons": n_coupons,
            **{k: (mg >= v) for k, v in ASSAY_MIN_MG.items()}}
