"""Coupon-scale reactor model v2: three guilds, per-irradiance-bin films,
in-film oxygen.

Changes from sim/templates/phototrophic_biofilm_batch (v1):
  * one film per irradiance bin, area-weighted (binned-resolution ruling)
  * oxygen is a STATE INSIDE THE FILM; bulk S_O stays an imposed boundary
    condition. Phototrophs are a source, nitrifiers and heterotrophs sinks.
    Solved by an analytic penetration depth, not a PDE (the MATLAB twinlet's
    approach), so no extra solver machinery is needed.
  * f_wet re-derived from rig geometry (0.76), not inherited from the plant's
    40% disc submergence.
  * heterotroph mu_max from the plant-level model (3.2 /d); nitrifier kinetics
    stay in the measured AREAL form, as the manuscript states.
  * bulk_mode: 'batch' reproduces the coupon rig; 'fixed' holds the bulk at the
    stated feed, which is the correct setting for screening carriers at equal
    loading (a closed vessel would simply let a dense carrier starve itself).

  * ATTACHMENT is a rate, not an initial condition, and it is mass-conserving.
    Cells move from a finite suspended pool Xpl onto the carrier; detachment
    returns them. The vessel is seeded once, so the pool is what the inoculum
    put there plus whatever has sloughed off since. Without the pool, a material
    with a high attachment factor accumulates biofilm out of nothing -- in the
    closed rig that produced 173% of the nitrogen actually supplied.

State, per arm: [Snh, Sno, Sp, Sb, Xpl] + [Xp, Xn, Xh] x n_bins
                (four bulk solutes in mg/L; Xpl and every film state in g DW per m2
                of carrier). Xpl is the SUSPENDED pool expressed per unit carrier
                area -- multiply by a_v for the concentration a liquid sample shows.
"""
from __future__ import annotations
import numpy as np

# --------------------------------------------------------------- stoichiometry
F_O2_N = 4.57      # g O2 per g NH4-N nitrified (ASM)
G_COD_DW = 1.42    # g COD per g DW

def o2_per_bod(Y_h):
    """g O2 consumed per g BOD removed, after the biomass share."""
    return max(0.0, 1.0 - G_COD_DW * Y_h)


class Reactor:
    def __init__(self, p, bins_w, bins_E, a_v, attach=1.0, bulk_mode="fixed", feed=None,
                 graphene=False):
        self.p = dict(p)
        self.w = np.asarray(bins_w, float)
        self.E = np.asarray(bins_E, float)
        self.nb = len(self.w)
        self.a_v = float(a_v)                 # m2 of carrier surface per m3 of liquid
        self.attach = float(attach)           # material colonisation factor (HDPE = 1),
                                              # applied to the attachment RATE k_att
        s = p["Xp0"] + p["Xn0"] + p["Xh0"]    # attaching cells carry the inoculum composition
        self.f_att = np.array([p["Xp0"], p["Xn0"], p["Xh0"]]) / max(s, 1e-12)
        self.bulk_mode = bulk_mode
        self.feed = dict(feed or dict(Snh=20.0, Sno=0.0, Sp=4.0, Sb=20.0))
        # Total film capacity is set by the MEASURED RBC film thickness band, not by the
        # Gross et al. 2016 seven-day algal biomass -- that experiment measured early
        # colonisation on smooth coupons, which is an attachment RATE, not an equilibrium
        # carrying capacity. Material therefore enters through `attach`, which scales the
        # attachment flux; capacity itself is material-independent.
        self.cap = self.p["X_cap"] * self.p["capacity_headroom"]
        self.graphene = bool(graphene)

    # ------------------------------------------------------------- oxygen
    def film_thickness(self, X):
        """Wet film thickness (m) from areal dry biomass (g DW m-2)."""
        rho_dry = self.p["rho_film_wet"] * 1e6 * (1.0 - self.p["moisture"])   # g dry m-3
        return X / np.maximum(rho_dry, 1e-9)

    def capacity(self, day):
        """Film capacity, reduced on a graphene coating as the film matures.

        Romeu et al. (2022) report 44% lower biofilm wet weight on a graphene
        nanoplatelet composite at 7 weeks, with no effect during early attachment.
        Modelled as an exponential approach to `final_factor` beginning at `onset_d`.
        This is the ONLY thing that distinguishes graphene from bare steel until the
        coupon contact angle and roughness are measured.
        """
        if not self.graphene:
            return self.cap
        g = self.p
        if day <= g["gra_onset_d"]:
            return self.cap
        ramp = 1.0 - np.exp(-(day - g["gra_onset_d"]) / g["gra_tau_d"])
        return self.cap * (1.0 - (1.0 - g["gra_final_factor"]) * ramp)

    def lag_factor(self, t):
        """Baranyi-Roberts adjustment function alpha(t), the standard lag form.

        Real biofilms take hours to days to get going -- conditioning film, reversible
        then irreversible attachment, physiological acclimation -- and none of that was
        represented. alpha ramps growth from near zero to full over `lag_d` days:

            alpha(t) = 1 / (1 + (exp(nu*lag) - 1) * exp(-nu*t))

        so alpha(0) = exp(-nu*lag) and alpha -> 1. The adaptation rate nu is taken as the
        fastest guild's mu_max, the usual choice when nu is not measured separately.

        lag_d = 0 disables it exactly (alpha == 1), which is the default: there is no
        measurement of a lag on these coupons, so switching it on asserts something the
        data cannot yet support. It exists so the day 3/7/10 harvests can rule a lag IN
        or OUT rather than being compared against a model incapable of showing one.

        NOT represented: a lag on ATTACHMENT itself (conditioning-film formation). This
        delays growth only, so a material whose biomass arrives rather than grows -- the
        fabric, at 14.7x -- is less affected than one that must grow its own film.
        """
        lag = self.p.get("lag_d", 0.0)
        if lag <= 0.0:
            return 1.0
        nu = self.p["mu_max_h"]
        return 1.0 / (1.0 + np.expm1(nu * lag) * np.exp(-nu * max(t, 0.0)))

    def penetration(self, D_eff, S_bulk, J_demand, L_f):
        """Analytic zero-order penetration depth (m) of a solute into the film."""
        Rv = np.where(L_f > 1e-9, J_demand / np.maximum(L_f, 1e-9), 0.0)
        return np.where(Rv > 0, np.sqrt(np.maximum(2.0 * D_eff * S_bulk / np.maximum(Rv, 1e-9), 0.0)),
                        np.inf)

    def oxygen_factor(self, L_f, J_demand):
        """Effectiveness factor for the aerobic rates from an analytic
        zero-order penetration depth delta = sqrt(2 D S / R_v)."""
        p = self.p
        Rv = np.where(L_f > 1e-9, J_demand / np.maximum(L_f, 1e-9), 0.0)      # g O2 m-3 d-1
        delta = np.where(Rv > 0, np.sqrt(np.maximum(2.0 * p["D_O2_eff"] * p["S_O_bulk"]
                                                    / np.maximum(Rv, 1e-9), 0.0)), np.inf)
        return np.clip(np.where(L_f > 1e-9, delta / np.maximum(L_f, 1e-9), 1.0), 0.0, 1.0)

    # ---------------------------------------------------------------- rhs
    def rhs(self, t, y, lit, T):
        p, nb = self.p, self.nb
        Snh, Sno, Sp, Sb, Xpl = np.maximum(y[:5], 0.0)
        X = np.maximum(y[5:], 0.0).reshape(3, nb)
        Xp, Xn, Xh = X
        Xtot = Xp + Xn + Xh

        # light: bin irradiance, then Beer-Lambert through the film
        I_b = p["I0"] * self.E
        tau = p["k_abs"] * np.maximum(Xp, 1e-9)
        I_bar = np.where(tau < 1e-6, I_b, I_b * (1.0 - np.exp(-tau)) / np.maximum(tau, 1e-12))
        lim_light = I_bar / (p["K_I"] + I_bar)

        N = Snh + Sno
        lim_N = N / (p["K_N_p"] + N)
        lim_P = Sp / (p["K_P_p"] + Sp)
        cap_t = self.capacity(t)                           # graphene: capacity falls as the film matures
        free = np.maximum(0.0, 1.0 - Xtot / cap_t)         # phototrophs and nitrifiers share the film
        alpha = self.lag_factor(t)                 # 1.0 unless lag_d > 0
        mu_p = (p["mu_max_p"] * lim_light * lim_N * lim_P * p["theta_p"] ** (T - 20.0)
                * free * alpha)
        growth_p = lit * mu_p * Xp

        # oxygen: surface Monod on the imposed bulk, then in-film penetration
        SO = p["S_O_bulk"]
        oxy_A = SO / (p["K_O_A"] + SO)
        oxy_H = SO / (p["K_O_H"] + SO)
        f_comp = p["K_comp"] / (p["K_comp"] + Xh) if p["comp_on"] >= 0.5 else 1.0
        rN0 = (p["rN_ref"] * (Xn / p["Xn_ref"]) * (Snh / (p["K_N_n"] + Snh))
               * p["theta_n"] ** (T - 20.0) * f_comp * p["f_wet"] * oxy_A * free * alpha)
        # STRATIFICATION: heterotrophs can hold only the depth that BOD reaches.
        # delta_S is the substrate penetration depth; the areal biomass that fits inside it
        # is the heterotroph capacity. More BOD -> deeper layer -> less room for nitrifiers,
        # which makes the memorandum's limiting mechanism physical rather than an empirical
        # competition term. Nitrifiers and phototrophs share the remaining film.
        rho_dry = p["rho_film_wet"] * 1e6 * (1.0 - p["moisture"])
        L_f0 = self.film_thickness(Xtot)
        J_S = np.maximum(Xh, 1e-9) * p["mu_max_h"] / max(p["Y_h"], 1e-9) * (Sb / (p["K_S_h"] + Sb))
        delta_S = self.penetration(p["D_S_eff"], Sb, J_S, L_f0)
        cap_h = np.minimum(cap_t, rho_dry * np.minimum(delta_S, L_f0 + p["delta_S_floor"]))
        free_h = np.maximum(0.0, 1.0 - Xh / np.maximum(cap_h, 1e-9))
        mu_h0 = (p["mu_max_h"] * (Sb / (p["K_S_h"] + Sb)) * p["theta_h"] ** (T - 20.0)
                 * oxy_H * free_h * alpha)
        growth_h0 = mu_h0 * Xh

        L_f = self.film_thickness(Xtot)
        J_O2 = (F_O2_N * rN0 + o2_per_bod(p["Y_h"]) * growth_h0 / max(p["Y_h"], 1e-9)
                - p["Y_O2_p"] * (growth_p - (1.0 - lit) * p["b_p"] * Xp))
        eta_O2 = self.oxygen_factor(L_f, J_O2)
        rN, growth_h = rN0 * eta_O2, growth_h0 * eta_O2

        # ATTACHMENT. Material enters here, as a rate, not as an initial condition.
        # Every vessel is seeded from the same inoculum culture, so y0 is identical across
        # arms; what differs is how readily cells stick and keep sticking. `attach` is the
        # Gross et al. (2016) material factor (HDPE = 1) applied to the areal attachment
        # flux k_att. Attachment stops as the film fills, through the same free-surface
        # terms that limit growth, so it cannot push biomass past capacity.
        # Attachment is limited by how many cells are actually in suspension, so it
        # transfers biomass rather than creating it. Monod in Xpl, shut off by the same
        # free-surface terms that limit growth.
        j = p["k_att"] * self.attach * (Xpl / (p["K_pl"] + Xpl))
        att_p, att_n, att_h = (j * self.f_att[0] * free, j * self.f_att[1] * free,
                               j * self.f_att[2] * free_h)
        det_p, det_n, det_h = p["k_det"] * Xp, p["k_det"] * Xn, p["k_det"] * Xh

        dXp = growth_p + att_p - (1.0 - lit) * p["b_p"] * Xp - det_p
        dXn = p["Y_n"] * rN + att_n - p["b_n"] * Xn - det_n
        dXh = growth_h + att_h - p["b_h"] * Xh - det_h
        # Suspended pool: fed by detachment, drained by attachment, decays slowly.
        # Held in AREAL units (g DW per m2 of carrier) so it stays the same order of
        # magnitude as the film states. Stored as a concentration it would be a_v times
        # larger -- up to 1e4 -- and the solver tolerances, which are set for states of
        # order 1, would chase it and the integration would not finish.
        dXpl = (float(np.dot(self.w, (det_p + det_n + det_h) - (att_p + att_n + att_h)))
                - p["b_pl"] * Xpl)

        if self.bulk_mode == "fixed":
            dB = np.zeros(4)
        else:
            AV = self.a_v
            uN = (growth_p * p["fN_p"] * p["f_wet"] * self.w).sum()
            uP = (growth_p * p["fP_p"] * p["f_wet"] * self.w).sum()
            uS = (growth_h / max(p["Y_h"], 1e-9) * p["f_wet"] * self.w).sum()
            rN_a = (rN * self.w).sum()
            f_nh4 = Snh / (N + 1e-9)
            dB = np.array([-(uN * f_nh4 + rN_a) * AV,
                           (rN_a - uN * (1.0 - f_nh4)) * AV,
                           -uP * AV, -uS * AV])
        return np.concatenate([dB, [dXpl], dXp, dXn, dXh])

    # ----------------------------------------------------------- integrate
    def simulate(self, days, light_h, T=20.0, n_out=200, substep_min=15.0, y0=None, t0=0.0):
        """Integrate. Pass `y0` (and `t0`) to continue an existing run, which is what a
        semi-continuous feed needs: run a day, reset the bulk, carry the biofilm forward."""
        from scipy.integrate import solve_ivp
        p = self.p
        # The inoculum arrives SUSPENDED and identical in every arm. A small seed is put
        # on the carrier so the growth terms are not identically zero at t = 0; the rest
        # is in the pool, where the material factor decides how fast it lands.
        seed = p["seed_frac"]
        X0 = p["Xp0"] + p["Xn0"] + p["Xh0"]
        y = np.concatenate([[self.feed["Snh"], self.feed["Sno"], self.feed["Sp"], self.feed["Sb"],
                             (1.0 - seed) * X0],
                            np.full(self.nb, seed * p["Xp0"]),
                            np.full(self.nb, seed * p["Xn0"]),
                            np.full(self.nb, seed * p["Xh0"])])
        if y0 is not None:
            y = np.asarray(y0, float).copy()
        frac = np.clip(light_h / 24.0, 0.0, 1.0)
        h = substep_min / (60.0 * 24.0)
        ts, ys = [t0], [y.copy()]
        t = t0

        def lit_fraction(d0, d1):
            """Share of [d0, d1] that is lit; lamps switch on at the start of each day."""
            if d1 <= d0:
                return float((d0 % 1.0) < frac)
            lit_until = lambda d: np.floor(d) * frac + min(d - np.floor(d), frac)
            return (lit_until(d1) - lit_until(d0)) / (d1 - d0)

        while t < t0 + days - 1e-12:
            step = min(h, t0 + days - t)
            lit = lit_fraction(t, t + step)
            sol = solve_ivp(self.rhs, [t, t + step], y, args=(lit, T),
                            method="LSODA", rtol=1e-7, atol=1e-10)
            y = np.maximum(sol.y[:, -1], 0.0)
            t += step
            ts.append(t); ys.append(y.copy())
        ts = np.array(ts); ys = np.array(ys)
        keep = np.unique(np.linspace(0, len(ts) - 1, min(n_out, len(ts))).astype(int))
        return ts[keep], ys[keep]

    # ------------------------------------------------------------ outputs
    def unpack(self, y):
        X = y[..., 5:].reshape(*y.shape[:-1], 3, self.nb)
        return dict(Snh=y[..., 0], Sno=y[..., 1], Sp=y[..., 2], Sb=y[..., 3],
                    Xpl=y[..., 4],
                    Xp=X[..., 0, :], Xn=X[..., 1, :], Xh=X[..., 2, :])

    def areal_rate(self, y, T=20.0):
        """Area-weighted areal nitrification rate, g N m-2 d-1, per unit COLONISED
        non-occluded area (the definition the aggregation rule assumes)."""
        p = self.p
        d = self.unpack(y)
        Snh = d["Snh"]; Xn = d["Xn"]; Xh = d["Xh"]
        SO = p["S_O_bulk"]
        f_comp = p["K_comp"] / (p["K_comp"] + Xh) if p["comp_on"] >= 0.5 else 1.0
        Xtot = d["Xp"] + d["Xn"] + d["Xh"]
        free = np.maximum(0.0, 1.0 - Xtot / self.cap)      # steady-state form; see capacity()
        rN = (p["rN_ref"] * (Xn / p["Xn_ref"]) * (Snh[..., None] / (p["K_N_n"] + Snh[..., None]))
              * p["theta_n"] ** (T - 20.0) * f_comp * p["f_wet"] * SO / (p["K_O_A"] + SO) * free)
        L_f = self.film_thickness(Xtot)
        J = F_O2_N * rN
        return (rN * self.oxygen_factor(L_f, J) * self.w).sum(axis=-1)
