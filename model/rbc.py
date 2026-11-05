"""RBC mounting geometry, duty cycle and shear for coupon explorer v2.

Every function here is a pure function of the site geometry. Nothing is fitted.
All site constants are PLACEHOLDERS pending the field measurements listed in
coupon_model/FIELD_MEASUREMENTS_RBC1.md -- see PLACEHOLDERS below.

Symbols follow the project glossary; where a field-standard symbol exists it is
given in the docstring.
"""
from __future__ import annotations
import numpy as np
from scipy.optimize import brentq

# ----------------------------------------------------------------- RIG GEOMETRY
# Revised 4 Nov 2026 from Anthony's description of RBC 1, relayed by the user.
# Values marked "placeholder" are best estimates committed at the user's direction so
# the model can run; they are listed for replacement in FIELD_MEASUREMENTS_RBC1.md.
#
# THE RIG. Two rotating round steel END PLATES 6 ft apart on a common shaft, with the
# wafer (media disc) pack between them. Two steel BANDS run axially from plate to
# plate at 0 and 180 degrees. Each band carries DIVOTS -- sheltered recesses -- and
# each divot holds 9 coupons of one material, each in a magnet sandwich clamped to the
# divot floor. Three coupons are harvested at each of days 5, 7 and 10. Two divots per
# material, one per photoperiod, so 8 divots and 72 coupons in total. Lamps sit in six
# existing round holes in the RBC cover, three at each end, which makes photoperiod a
# function of AXIAL position rather than of which face a board is on.
RIG = {
    "D_disc_m":      (2.0,     "placeholder", "media disc / end-plate outside diameter"),
    "shaft_span_m":  (1.8288,  "reported",    "6 ft between end plates (Anthony)"),
    "band_r_over_R": (0.95,    "placeholder", "band radius as a fraction of disc radius"),
    "n_bands":       (2,       "reported",    "steel bands at 0 and 180 deg (Anthony)"),
    "divots_per_band": (4,     "placeholder", "8 divots over 2 bands, two near each end"),
    "coupons_per_divot": (9,   "reported",    "3 harvested on each of days 5, 7, 10"),
    "divot_w_mm":    (45.0,    "placeholder", "cavity width, clears the coupon stack"),
    "divot_d_mm":    (10.0,    "placeholder", "cavity depth"),
    "recess_mm":     (3.0,     "placeholder", "coupon face below the band surface"),
    "submergence":   (0.40,    "standard",    "fraction of disc AREA submerged (RBC convention)"),
    "rpm_now":       (4.0,     "reported",    "Anthony, 4 Nov 2026 - as currently run"),
    "n_lamps":       (6,       "reported",    "three per end, in existing cover holes"),
    "lamp_height_m": (0.5,     "placeholder", "fixture height above the waterline"),
    "hole_d_mm":     (150.0,   "placeholder", "cover hole diameter"),
    "ambient_light": (0.0,     "reported",    "indoor, under the cover: lamps are the only source"),
    "nu_water":      (1.14e-6, "literature",  "kinematic viscosity, water at 15 C (m2/s)"),
    "rho_water":     (999.0,   "literature",  "density, water at 15 C (kg/m3)"),
    "Re_crit":       (3.0e5,   "literature",  "rotating-disc laminar-turbulent transition"),
    "coupon_mm":     (39.6875, "reported",    "square, 1 9/16 in (user, 4 Nov 2026)"),
    "magnet_d_mm":   (19.05,   "reported",    "3/4 in, read as diameter"),
}
PLACEHOLDERS = RIG            # back-compatible name

# Divot shelter. A coupon recessed below the band surface sees less than the free-stream
# wall shear and less than the full lamp irradiance. BOTH factors are NEW and UNSOURCED
# -- there is no measurement and no literature value behind either; they are this study's
# declared estimates, and phi_shear is carried as a sampled axis rather than fixed.
PHI_SHEAR_DEFAULT  = 0.5      # sampled 0.3 - 1.0 across the grid; 1.0 = no shelter
VIEW_FACTOR_DEFAULT = 0.90    # fraction of lamp irradiance reaching a recessed coupon

# LIMITATION, stated at the user's direction (4 Nov 2026): the model assumes NO optical
# cross-contamination between the two ends. With lamps 6 ft apart in a shared cover and
# bands that may run outside the wafer pack, some light from one end's fixtures will
# reach the other end's coupons. That crosstalk is not modeled, so the contrast between
# the two photoperiods is an UPPER BOUND on what the rig will actually deliver.
CROSSTALK_MODELED = False

# ------------------------------------------------------------- submergence
def waterline_depth(submergence: float = 0.40) -> float:
    """u = |h|/R, the waterline depth below the shaft centerline, in units of R,
    that puts `submergence` of the DISC AREA under water.

    Solves  [arccos(u) - u*sqrt(1-u^2)] / pi = submergence.
    At the RBC-standard 40% this returns 0.1577.
    """
    f = lambda u: (np.arccos(u) - u * np.sqrt(1.0 - u * u)) / np.pi - submergence
    return brentq(f, 1e-9, 1.0 - 1e-9)


def wet_fraction(r_over_R, submergence: float = 0.40):
    """f_wet: fraction of each REVOLUTION a point at radius r spends submerged.

    This is NOT the areal submergence. A point at radius r is under water for the
    share of its circular path that lies below the waterline:

        f_wet(r) = 1/2 + arcsin(-u R / r) / pi,      u = waterline_depth()

    so f_wet -> 0.450 at the rim and falls toward 0 near the hub. The nominal 40%
    is recovered only near r/R = 0.5. Boards at different radii therefore run
    different duty cycles -- the reason mount radius must be matched or treated
    as a factor.
    """
    r_over_R = np.asarray(r_over_R, float)
    u = waterline_depth(submergence)
    k = np.clip(-u / np.maximum(r_over_R, 1e-9), -1.0, 1.0)
    return np.where(r_over_R <= u, 0.0, 0.5 + np.arcsin(k) / np.pi)


# ------------------------------------------------------------- rotation
def cycle_period_s(rpm: float) -> float:
    """Seconds per revolution."""
    return 60.0 / float(rpm)


def dwell_s(rpm: float, r_over_R: float, submergence: float = 0.40):
    """(submerged, emergent) dwell in seconds per revolution at this radius."""
    T = cycle_period_s(rpm)
    fw = float(wet_fraction(r_over_R, submergence))
    return T * fw, T * (1.0 - fw)


SECONDS_PER_DAY = 86400.0

def o2_penetration_um(rpm: float, r_over_R: float, D_O2_eff_m2_per_day: float = 1.296e-4,
                      submergence: float = 0.40) -> float:
    """sqrt(2 D t_emergent) in micrometres -- how deep oxygen reaches per emergent pass.

    A scaling estimate, not a solution: it is the diffusion length over the emergent
    dwell, and the physical reason rotation rate matters for nitrification.

    UNITS: the reactor params carry D_O2_eff in m2/DAY (the model's time unit) while
    the dwell is in SECONDS; the conversion is done here. Passing an SI diffusivity
    (~1.5e-9 m2/s) unconverted understates the depth ~294x, and passing the m2/d value
    unconverted overstates it by the same factor. Default 1.296e-4 m2/d = 1.5e-9 m2/s.
    """
    _, te = dwell_s(rpm, r_over_R, submergence)
    D_si = float(D_O2_eff_m2_per_day) / SECONDS_PER_DAY
    return 1e6 * np.sqrt(2.0 * D_si * te)


# ------------------------------------------------------------- hydrodynamics
def omega(rpm: float) -> float:
    """Angular velocity, rad/s."""
    return 2.0 * np.pi * float(rpm) / 60.0


def Re_disc(rpm: float, R_m: float, nu: float = 1.14e-6) -> float:
    """Rotating-disc Reynolds number omega R^2 / nu."""
    return omega(rpm) * R_m * R_m / nu


def tau_wall_Pa(rpm: float, r_m: float, rho: float = 999.0, nu: float = 1.14e-6) -> float:
    """Local wall shear stress (Pa), von Karman LAMINAR rotating-disc result:

        tau_w = 0.512 rho sqrt(nu) omega^{3/2} r

    Valid only while Re_disc < Re_crit. `shear_regime_ok` flags when it is not.
    No turbulent correlation is provided: see SHEAR_BASIS.md, the geometry does
    not yet justify selecting one.
    """
    return 0.512 * rho * np.sqrt(nu) * omega(rpm) ** 1.5 * r_m


def shear_regime_ok(rpm: float, R_m: float, nu: float = 1.14e-6,
                    Re_crit: float = 3.0e5) -> bool:
    """False when the laminar correlation is being used outside its range."""
    return Re_disc(rpm, R_m, nu) < Re_crit


# ------------------------------------------------------------- light
def delivered_light_h(timer_h: float, f_wet: float) -> float:
    """Hours per day the coupon is ACTUALLY lit.

    Submerged means dark -- mixed liquor is opaque -- so light lands only during the
    emergent share of each revolution. Rotation (tens of seconds) and the lamp timer
    (hours) are independent and separated by ~3 orders of magnitude in timescale, so
    the joint duty is the product:

        delivered = timer_h * (1 - f_wet)

    Consequence: delivered light is capped at (1 - f_wet) x 24 h regardless of the
    timer, and a 24 h photoperiod is physically unreachable on a rotating disc.
    """
    return float(timer_h) * (1.0 - float(f_wet))


# ------------------------------------------------------------- detachment
def k_det_shear(k_det_base: float, tau_Pa: float, tau_ref_Pa: float,
                n_shear: float) -> float:
    """Shear-modified first-order detachment coefficient.

        k_det = k_det_base * (tau / tau_ref)^n_shear

    n_shear is SAMPLED ACROSS THE ENSEMBLE, not fixed:
      n_shear = 0   -> no shear dependence (Peyton & Characklis 1993, who found
                       no significant shear effect on detachment rate)
      n_shear > 0   -> a positive shear dependence in the spirit of Rittmann (1982)

    The literature does not support a single exponent and the two most-cited
    primary sources disagree, so the ensemble carries the disagreement rather than
    resolving it by fiat. tau_ref anchors the baseline at the plant's present
    operating point so that varying n_shear does not shift the reference case.
    See SHEAR_BASIS.md -- note that NONE of those sources was obtained in full text.
    """
    if tau_ref_Pa <= 0:
        return float(k_det_base)
    return float(k_det_base) * (float(tau_Pa) / float(tau_ref_Pa)) ** float(n_shear)


# ------------------------------------------------------------- divot shelter
def tau_local_Pa(tau_free_Pa: float, phi_shear: float = PHI_SHEAR_DEFAULT) -> float:
    """Wall shear actually felt inside the divot.

        tau_local = phi_shear * tau_free

    phi_shear = 1 is a coupon flush with the band surface; smaller values are deeper
    recesses. UNSOURCED -- see PHI_SHEAR_DEFAULT. Sampled across the grid so the
    ranking can be checked against the whole plausible range instead of one guess.
    """
    return float(tau_free_Pa) * float(phi_shear)


def divot_irradiance(I0: float, view_factor: float = VIEW_FACTOR_DEFAULT) -> float:
    """Irradiance at a recessed coupon face.

    The shelter is applied to INTENSITY, not to hours: a recess dims the coupon, it
    does not change when the lamp timer fires or when the coupon surfaces. Applying it
    to hours would double-count against `delivered_light_h`, which already carries the
    rotation duty cycle.
    """
    return float(I0) * float(view_factor)
