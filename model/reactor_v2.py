"""RBCReactor -- coupon explorer v2.

A thin subclass of the v1 `Reactor`. The RBC mounting changes three things, and all
three are CONSTANTS for a given arm (radius and rpm do not change during a run), so
nothing in `rhs` needs overriding:

  1. f_wet is derived from mount radius and submergence instead of being a fixed
     rig number. It is radius-dependent -- see rbc.wet_fraction. On the band-mounted
     rig the radius is FIXED by hardware at r/R = 0.95, so f_wet = 0.4469 and the
     coupons are emergent 55.3% of each revolution.
  2. k_det is multiplied by a sampled shear factor (tau_local/tau_ref)^n_shear, where
     tau_local = phi_shear * tau_free is the shear inside the divot.
  3. The light the coupon receives is the timer hours times the emergent fraction,
     because submerged means dark. Handled by `delivered_light_h` and applied in
     `simulate_rbc`. The divot additionally DIMS the coupon by `view_factor`, applied
     to I0 -- to intensity, never to hours, which would double-count the duty cycle.

Bulk mode defaults to 'fixed'. On the wheel the coupons sit in the plant's own
first-stage tank, so the bulk is an imposed boundary condition set by the plant and
a few hundred cm2 of coupon cannot draw it down. The v1 'batch' mode described a
closed 1 L vessel and has no referent here.

Set rotation_enabled=False to recover v1 behavior EXACTLY (used by the regression
test): f_wet and k_det are then left at their params values and light is the raw
timer value.
"""
from __future__ import annotations
import numpy as np
from reactor import Reactor
import rbc as _rbc


class RBCReactor(Reactor):
    def __init__(self, p, bins_w, bins_E, a_v, attach=1.0, bulk_mode="fixed", feed=None,
                 graphene=False, *, rotation_enabled=True, rpm=4.0, r_over_R=0.95,
                 D_disc_m=2.0, submergence=0.40, n_shear=0.0,
                 phi_shear=1.0, view_factor=1.0,
                 rpm_ref=4.0, r_over_R_ref=0.95, phi_shear_ref=1.0,
                 rho=999.0, nu=1.14e-6, Re_crit=3.0e5):
        super().__init__(p, bins_w, bins_E, a_v, attach=attach, bulk_mode=bulk_mode,
                         feed=feed, graphene=graphene)
        self.rotation_enabled = bool(rotation_enabled)
        self.rpm = float(rpm)
        self.r_over_R = float(r_over_R)
        self.D_disc_m = float(D_disc_m)
        self.submergence = float(submergence)
        self.n_shear = float(n_shear)
        self.phi_shear = float(phi_shear)
        self.view_factor = float(view_factor)
        self.R_m = self.D_disc_m / 2.0

        if not self.rotation_enabled:
            self.f_wet = self.p["f_wet"]
            self.tau_Pa = float("nan")
            self.laminar_ok = True
            self.k_det_base = self.p["k_det"]
            self.tau_free_Pa = float("nan")
            self.I0_free = self.p["I0"]
            return

        # 1. duty cycle from geometry
        self.f_wet = float(_rbc.wet_fraction(self.r_over_R, self.submergence))
        self.p["f_wet"] = self.f_wet

        # 2. shear -> detachment. tau_free is the free-stream wall shear at the band;
        # tau_Pa is what the coupon feels after the divot shelter. The reference is the
        # present operating point, UNSHELTERED, so phi_shear=1 at rpm_ref is the anchor
        # and changing n_shear never moves the baseline case.
        self.tau_free_Pa = _rbc.tau_wall_Pa(self.rpm, self.r_over_R * self.R_m, rho, nu)
        self.tau_Pa = _rbc.tau_local_Pa(self.tau_free_Pa, self.phi_shear)
        tau_ref = _rbc.tau_local_Pa(
            _rbc.tau_wall_Pa(rpm_ref, r_over_R_ref * self.R_m, rho, nu), phi_shear_ref)
        self.k_det_base = self.p["k_det"]
        self.p["k_det"] = _rbc.k_det_shear(self.k_det_base, self.tau_Pa, tau_ref, self.n_shear)

        # 3. divot shelter dims the lamp. Applied to intensity only.
        self.I0_free = self.p["I0"]
        self.p["I0"] = _rbc.divot_irradiance(self.I0_free, self.view_factor)

        # 3. regime flag -- never let a 4 rpm run be reported as if laminar held
        self.laminar_ok = _rbc.shear_regime_ok(self.rpm, self.R_m, nu, Re_crit)
        self.Re = _rbc.Re_disc(self.rpm, self.R_m, nu)

    # ------------------------------------------------------------------ info
    def duty(self):
        """Everything the explorer's summary cards need about the cycle."""
        T = _rbc.cycle_period_s(self.rpm)
        sub, em = _rbc.dwell_s(self.rpm, self.r_over_R, self.submergence)
        return dict(f_wet=self.f_wet, period_s=T, submerged_s=sub, emergent_s=em,
                    tau_Pa=self.tau_Pa, tau_free_Pa=self.tau_free_Pa,
                    phi_shear=self.phi_shear, view_factor=self.view_factor,
                    I0=self.p["I0"], I0_free=self.I0_free,
                    k_det=self.p["k_det"], k_det_base=self.k_det_base,
                    laminar_ok=self.laminar_ok,
                    Re=getattr(self, "Re", float("nan")),
                    o2_penetration_um=_rbc.o2_penetration_um(
                        self.rpm, self.r_over_R, self.p["D_O2_eff"], self.submergence))

    # -------------------------------------------------------------- integrate
    def simulate_rbc(self, days, timer_h, **kw):
        """Integrate with the light duty corrected for submergence.

        `timer_h` is the LAMP TIMER setting (e.g. Rapid City solstices 15.50 / 8.87 h).
        What the coupon receives is timer_h * (1 - f_wet); returns that alongside the
        trajectory so the page can show both and never conflate them.
        """
        if self.rotation_enabled:
            delivered = _rbc.delivered_light_h(timer_h, self.f_wet)
        else:
            delivered = float(timer_h)
        ts, ys = self.simulate(days, delivered, **kw)
        return ts, ys, delivered
