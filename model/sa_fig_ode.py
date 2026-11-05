"""Figures for the surrogate-free analyses: Sobol' on the ODE, exact Shapley on the ODE.

  fig_sa_sobol_ode.png     S1 and S_T with bootstrap CIs, computed on the differential
                           equations rather than on a fitted approximation of them.
  fig_sa_shapley_exact.png (a) mean |phi| per input, (b) per-arm signed attribution
                           coloured by the input's own value -- the exact counterpart of
                           a SHAP beeswarm -- and (c) the same aggregated to the three
                           domain groups.
"""
import os, sys
import numpy as np, pandas as pd
import matplotlib.pyplot as plt
from matplotlib import cm, colors

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sa_design as SD
import sa_ode_design as OD
import sa_labels as LB

FOCAL, OK, GREY = "#C8102E", "#2B5D7D", "#8A8F98"


def _swarm(x, half=0.17, step=0.05):
    """Beeswarm offsets: vertical position encodes LOCAL DENSITY, which is what gives a
    real SHAP beeswarm its silhouette. Uniform jitter does not do this -- it produces a
    strip plot that happens to be the same height. Points are placed in x order into the
    nearest free slot that does not collide with an already-placed neighbour."""
    x = np.asarray(x, float)
    spread = float(np.ptp(x))
    xtol = (spread / 45.0) if spread > 0 else 1.0
    y = np.zeros(len(x))
    placed = []
    cands = [0.0]
    k = 1
    while k * step <= half:
        cands += [k * step, -k * step]
        k += 1
    for idx in np.argsort(x):
        chosen = None
        for c in cands:
            if all(not (abs(x[idx] - px) < xtol and abs(c - py) < step * 0.9)
                   for px, py in placed):
                chosen = c
                break
        if chosen is None:
            chosen = float(np.clip(
                np.random.default_rng(int(idx)).normal(0, half / 3), -half, half))
        y[idx] = chosen
        placed.append((x[idx], chosen))
    return y


def fig_sobol(out="fig_sa_sobol_ode.png", top=14):
    S = pd.read_csv(os.path.join(HERE, "sa_sobol_ode.csv")).head(top).iloc[::-1]
    y = np.arange(len(S))
    fig, ax = plt.subplots(figsize=(7.4, 5.0))
    ax.barh(y + 0.19, S.ST, height=0.36, color=FOCAL, alpha=0.9, label="total $S_T$",
            xerr=S.ST_conf, error_kw=dict(ecolor="#4B5563", lw=0.7, capsize=1.6))
    ax.barh(y - 0.19, S.S1, height=0.36, color=OK, alpha=0.9, label="first-order $S_1$",
            xerr=S.S1_conf, error_kw=dict(ecolor="#4B5563", lw=0.7, capsize=1.6))
    ax.set_yticks(y); ax.set_yticklabels([LB.two_line(p) for p in S.parameter], fontsize=5.6)
    ax.set_xlabel("Sobol' index on day-60 areal removal flux", fontsize=7)
    ax.set_title("Sobol' indices computed on the differential equations, not a surrogate",
                 loc="left", fontsize=8.5)
    ax.legend(fontsize=6, frameon=False, loc="lower right")
    ax.tick_params(labelsize=6)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    gap = (S.ST - S.S1)
    ax.text(0.98, 0.46, "$S_T - S_1$ is the part of an input's\ninfluence that acts "
            "through interactions", transform=ax.transAxes, fontsize=6,
            ha="right", va="top", color=GREY)
    # Honest statement of what the CIs do and do not license at N=256.
    ax.text(0.98, 0.30, "Only $K_{comp}$ separates from the next input at 95 %:\n"
            "its $S_T$ interval [0.35, 0.60] clears material's [0.16, 0.34].\n"
            "Adjacent ranks BELOW it overlap and are not ordered by this run.",
            transform=ax.transAxes, fontsize=6, ha="right", va="top", color="#C8102E")
    fig.tight_layout()
    p = os.path.join(HERE, out)
    fig.savefig(p, dpi=300)
    return p, S, gap


def fig_shapley(out="fig_sa_shapley_exact.png"):
    SH = pd.read_csv(os.path.join(HERE, "sa_shapley_exact.csv"))
    SG = pd.read_csv(os.path.join(HERE, "sa_shapley_grouped.csv"))
    arms = pd.read_csv(os.path.join(HERE, "sa_ode2_arms.csv"))

    agg = (SH.groupby("parameter").phi.apply(lambda s: s.abs().mean())
             .sort_values(ascending=True))
    order = list(agg.index)

    fig = plt.figure(figsize=(8.8, 6.6))
    gs = fig.add_gridspec(2, 2, width_ratios=[1.0, 1.35], height_ratios=[1.0, 0.42],
                          hspace=1.05, wspace=0.32)
    ax0 = fig.add_subplot(gs[:, 0])
    ax1 = fig.add_subplot(gs[0, 1])
    ax2 = fig.add_subplot(gs[1, 1])

    # (a) mean |phi|
    ax0.barh(np.arange(len(order)), agg.values, color=FOCAL, alpha=0.88, height=0.62)
    ax0.set_yticks(np.arange(len(order)))
    ax0.set_yticklabels([LB.two_line(p) for p in order], fontsize=5.6)
    ax0.set_xlabel("mean |$\\phi$|   (g N m$^{-2}$ d$^{-1}$)", fontsize=6.5)
    ax0.set_title("a  Exact Shapley, mean |$\\phi$| over arms (sign discarded)",
                  loc="left", fontsize=7.5)

    # (b) per-arm signed attribution, coloured by the input's own value
    rng = {}
    for f in order:
        if f in SD.LOGU:
            lo, hi = np.log(SD.LOGU[f]); rng[f] = (lo, hi, True)
        else:
            lo, hi = SD.UNIF[f]; rng[f] = (lo, hi, False)
    cmap = plt.get_cmap("viridis")
    for i, f in enumerate(order):
        sub = SH[SH.parameter == f].merge(arms[["arm", f]], on="arm")
        lo, hi, islog = rng[f]
        v = np.log(sub[f].values) if islog else sub[f].values
        t = np.clip((v - lo) / (hi - lo), 0, 1)
        off = _swarm(sub.phi.values)
        ax1.scatter(sub.phi, i + off, c=t, cmap=cmap, s=16, vmin=0, vmax=1,
                    edgecolor="none", alpha=0.95)
    ax1.axvline(0, color=GREY, lw=0.7)
    ax1.set_yticks(np.arange(len(order)))
    ax1.set_yticklabels([LB.short(p) for p in order], fontsize=5.6)
    ax1.set_xlabel("$\\phi$ for one arm   (g N m$^{-2}$ d$^{-1}$)", fontsize=6.5)
    nar = SH.arm.nunique()
    ax1.set_title("b  Position = Shapley value;  colour = the input's setting",
                  loc="left", fontsize=7.5)
    ax1.text(0.0, -0.26, f"n = {nar} arms \u2014 each dot is one ARM, not one simulation. "
             "Exact Shapley costs 2\u2078 model runs per arm, so this is a dot plot "
             "rather than\nthe dense swarm a surrogate-based SHAP report shows: a "
             "surrogate can be sampled thousands of times for free, the ODE cannot.\n"
             "Colour encodes the input's SETTING, not its Shapley value \u2014 the Shapley "
             "value is the horizontal axis. Log scale where the sampling was log-uniform.",
             transform=ax1.transAxes, fontsize=5.4, ha="left", va="top",
             color="#6B7280")
    sm = cm.ScalarMappable(cmap=cmap, norm=colors.Normalize(0, 1))
    cb = fig.colorbar(sm, ax=ax1, fraction=0.03, pad=0.02)
    cb.set_ticks([0, 1]); cb.set_ticklabels(["bottom\nof range", "top\nof range"])
    cb.set_label("the input's setting in that arm,\npositioned within its swept range",
                 fontsize=5.2)
    cb.ax.tick_params(labelsize=5.5)

    # (c) grouped
    gnames = list(OD.GROUPS)
    base = float(SG.v_empty.iloc[0])
    nbelow = int((SG.drop_duplicates("arm").v_full < base).sum())
    ntot = SG.arm.nunique()
    for i, gname in enumerate(gnames):
        v = SG[SG.parameter == gname].phi.values
        ax2.scatter(v, i + _swarm(v, half=0.15, step=0.045), s=13, color=OK,
                    alpha=0.85, edgecolor="none", zorder=3)
        ax2.scatter([v.mean()], [i], s=42, marker="|", color=FOCAL, zorder=4,
                    linewidth=1.6)
    ax2.axvline(0, color=GREY, lw=0.7)
    g = SG.groupby("parameter").phi.agg(["mean", "std"]).reindex(gnames)
    ax2.set_yticks(np.arange(len(g)))
    ax2.set_yticklabels([LB.GROUP_LABELS[g] for g in OD.GROUPS], fontsize=5.8)
    ax2.set_xlabel("grouped $\\phi$   (g N m$^{-2}$ d$^{-1}$)", fontsize=6.5)
    ax2.set_title("c  By domain (exact, 2\u00b3 coalitions) \u2014 one dot per arm, "
                  "red tick = mean", loc="left", fontsize=7.5)
    ax2.text(0.0, -0.46,
             f"Zero here means 'the same flux as the nominal arm', not 'no effect'. "
             f"The nominal arm sits at $J_A$ = {base:.3f} g N m$^{{-2}}$ d$^{{-1}}$, the 83rd "
             f"percentile of the sampled\nrange, so {nbelow} of {ntot} explained arms fall "
             "below it and all three domain means come out negative. That is a property of "
             "the BASELINE, not of the domains.\nPanel a cannot show it because |$\\phi$| "
             "discards sign; the signed totals of a and c agree (\u22120.105 and \u22120.112).",
             transform=ax2.transAxes, fontsize=5.4, ha="left", va="top", color="#6B7280")

    for ax in (ax0, ax1, ax2):
        ax.tick_params(labelsize=6)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
    fig.suptitle("Shapley values computed by complete enumeration on the ODE "
                 "\u2014 no surrogate, additivity exact by construction",
                 x=0.012, ha="left", fontsize=8.5, y=0.985)
    fig.tight_layout(rect=(0, 0.07, 1, 0.945))
    p = os.path.join(HERE, out)
    fig.savefig(p, dpi=300)
    return p, agg, g


if __name__ == "__main__":
    try:
        apply_figure_style()                       # noqa: F821
    except NameError:
        pass
    p1, S, gap = fig_sobol()
    print("SOBOL' on the ODE\n", S.round(4).to_string(index=False))
    print("\nwrote", p1)
    p2, agg, g = fig_shapley()
    print("\nmean |phi| (exact Shapley):\n", agg.sort_values(ascending=False).round(5).to_string())
    print("\ngrouped:\n", g.round(5).to_string())
    print("\nwrote", p2)
