"""The impact-versus-evidence diagram.

Impact says how far the day-60 flux moves when an input is varied over its range.
Evidence says how much the input's value is worth believing. Plotting one against the
other turns the limitation already written into DATA_SOURCES.md -- that influence and
evidence are close to inversely ordered here -- into a figure, and converts it into a
ranked list of what to measure first.

Impact axis: Morris mu*, computed on the differential equations themselves (sa_morris.csv),
so this figure owes nothing to any surrogate. Material carries no mu* because the Morris
trajectories hold material fixed at HDPE; it is reported separately from the exact
factorial and from the ODE Sobol' run.

Quadrants split at the median mu* and between evidence scores 1 and 2.
"""
import os, sys
import numpy as np, pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sa_labels as LB

HERE = os.path.dirname(os.path.abspath(__file__))

FOCAL = "#C8102E"      # the measure-first quadrant
OK = "#2B5D7D"
GREY = "#8A8F98"


def draw(out="fig_sa_evidence_impact.png"):
    d = pd.read_csv(os.path.join(HERE, "sa_evidence.csv"))
    d = d[d.mu_star.notna()].copy()
    xsplit = float(d.mu_star.median())
    ysplit = 1.5
    d["weak"] = d.evidence_score < ysplit
    d["big"] = d.mu_star >= xsplit
    d["priority"] = d.weak & d.big

    fig, ax = plt.subplots(figsize=(9.4, 5.0))
    xlo, xhi = d.mu_star.min() * 0.30, d.mu_star.max() * 5.0
    ax.set_xscale("log")
    ax.set_xlim(xlo, xhi)
    ax.set_ylim(-0.95, 4.4)

    # quadrant washes
    ax.axhspan(-0.95, ysplit, xmin=0, xmax=1, color=FOCAL, alpha=0.045, zorder=0)
    ax.axvline(xsplit, color=GREY, lw=0.8, ls=(0, (4, 3)), zorder=1)
    ax.axhline(ysplit, color=GREY, lw=0.8, ls=(0, (4, 3)), zorder=1)

    # vertical jitter so points sharing an evidence score are readable
    # Points sharing an evidence score sit on one horizontal band, so spread them
    # vertically within the band AND alternate which side the label goes on --
    # adjacent members of a band can be close in mu*, and a single label side collides.
    d = d.sort_values("mu_star")
    yj, side = [], {}
    for s, grp in d.groupby("evidence_score"):
        g = grp.sort_values("mu_star")
        n = len(g)
        off = np.linspace(-0.36, 0.36, n) if n > 1 else np.array([0.0])
        yj.append(pd.Series(s + off, index=g.index))
        for i, idx in enumerate(g.index):
            side[idx] = 1 if i % 2 == 0 else -1
    d["y"] = pd.concat(yj).reindex(d.index)
    d["side"] = pd.Series(side).reindex(d.index)

    for i, r in d.iterrows():
        c = FOCAL if r.priority else (OK if not r.weak else GREY)
        ax.scatter(r.mu_star, r.y, s=58 if r.priority else 38, color=c,
                   zorder=4, edgecolor="white", linewidth=0.7)
        right = r.side > 0
        ax.annotate(LB.short(r.parameter), (r.mu_star, r.y),
                    xytext=(7 if right else -7, 0),
                    textcoords="offset points", fontsize=5.8,
                    ha="left" if right else "right", va="center",
                    color=c if r.priority else "#2A2E35",
                    fontweight="bold" if r.priority else "normal", zorder=5)

    ax.set_yticks([0, 1, 2, 3, 4])
    ax.set_yticklabels(["no source", "plant model\nor study choice",
                        "literature\n(analogue)", "field record or\nsame system type",
                        "measured here"], fontsize=6)
    ax.set_xlabel("Morris $\\mu^*$ on day-60 areal removal flux "
                  "(computed on the differential equations)", fontsize=7)
    ax.set_ylabel("strength of evidence for the input's value", fontsize=7)
    ax.set_title("The input that moves the flux most is the one with no source behind it",
                 loc="left", fontsize=8.5)

    ax.text(xhi / 1.08, -0.88, "MEASURE FIRST", fontsize=7, color=FOCAL,
            ha="right", va="bottom", fontweight="bold")
    ax.text(xlo * 1.08, -0.88, "safe to leave unmeasured", fontsize=6.5,
            color=GREY, ha="left", va="bottom")
    ax.text(xhi / 1.08, 4.25, "high impact, sound footing", fontsize=6.5,
            color=OK, ha="right", va="top")
    ax.text(xlo * 1.08, 4.25, "over-invested", fontsize=6.5,
            color=GREY, ha="left", va="top")
    ax.text(0.5, -0.185, "higher = moves the flux more  \u2192", transform=ax.transAxes,
            fontsize=6, color=GREY, ha="center")

    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.tick_params(labelsize=6)
    fig.tight_layout()
    p = os.path.join(HERE, out)
    fig.savefig(p, dpi=300)
    return fig, ax, d, p


if __name__ == "__main__":
    try:
        apply_figure_style()                      # noqa: F821  (figure-style kernel helper)
    except NameError:
        pass
    fig, ax, d, p = draw()
    pr = d[d.priority].sort_values("mu_star", ascending=False)
    print("MEASURE-FIRST quadrant (high impact, weak evidence):")
    print(pr[["parameter", "mu_star", "evidence_tier"]].to_string(index=False))
    print("\nsafe-to-leave corner (low impact, weak evidence):")
    lo = d[(~d.big) & d.weak].sort_values("mu_star")
    print(lo[["parameter", "mu_star", "evidence_tier"]].to_string(index=False))
    print(f"\nwrote {p}")
