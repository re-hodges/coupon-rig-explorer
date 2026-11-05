"""Figure: what throttles the flux, term by term (fig_sa_waterfall.png).

One row per material, each the median-flux arm of that material. The running value
starts at the reference areal rate and is multiplied by each term of the rate expression
in turn, ending exactly at the model's own day-60 J_A. Because the chain is
multiplicative the account is complete: no residual, no approximation.
"""
import os
import numpy as np, pandas as pd
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
import sa_decompose as DC

MATS = ["PE", "STL", "GRA", "FAB"]
MATLAB = {"PE": "HDPE", "STL": "bare steel", "GRA": "graphene-coated steel",
          "FAB": "fabric"}
DOWN, UP, FINAL = "#C8102E", "#2B5D7D", "#1F2937"


def draw(out="fig_sa_waterfall.png"):
    d = pd.read_csv(os.path.join(HERE, "sa_decomposition.csv"))
    keys = [k for k, _ in DC.LABELS]
    labs = [l for _, l in DC.LABELS]

    fig, axes = plt.subplots(len(MATS), 1, figsize=(7.4, 7.0), sharex=True)
    for ax, mat in zip(axes, MATS):
        sub = d[d.material == mat].sort_values("_JA_model")
        row = sub.iloc[len(sub) // 2]                     # median-flux arm
        vals = [row[k] for k in keys]
        run = [row["_S0"]]
        for v in vals:
            run.append(run[-1] * v)
        xs = np.arange(len(keys) + 1)

        for i, v in enumerate(vals):
            lo, hi = sorted((run[i], run[i + 1]))
            c = UP if v > 1.0 else DOWN
            ax.vlines(xs[i + 1] - 0.5, run[i], run[i], color="none")
            ax.bar(xs[i + 1] - 1 + 0.5, hi - lo, bottom=lo, width=0.62,
                   color=c, alpha=0.85, zorder=3)
            ax.plot([xs[i + 1] - 1 + 0.81, xs[i + 1] + 0.19],
                    [run[i + 1], run[i + 1]], color="#9CA3AF", lw=0.6,
                    zorder=2)
            if abs(np.log10(v)) > 0.05:
                ax.text(xs[i + 1] - 0.5, hi * 1.08, f"×{v:.2f}", fontsize=5.6,
                        ha="center", va="bottom", color=c, zorder=5)
            elif abs(v - 1.0) < 1e-12:
                # an exactly inert term draws no bar; mark it so the reader sees it
                # was evaluated. eta_O2 = 1.00 everywhere is a finding, not an omission.
                ax.scatter([xs[i + 1] - 0.5], [run[i + 1]], s=16, facecolor="white",
                           edgecolor="#6B7280", linewidth=0.8, zorder=5)
                ax.text(xs[i + 1] - 0.5, run[i + 1] * 1.22, "×1.00", fontsize=5.6,
                        ha="center", va="bottom", color="#6B7280", zorder=5)
        ax.scatter([xs[-1] + 0.3], [run[-1]], s=26, color=FINAL, zorder=5)
        ax.text(xs[-1] + 0.45, run[-1], f"  $J_A$ = {run[-1]:.3f}", fontsize=6.5,
                va="center", ha="left", color=FINAL, fontweight="bold")
        ax.set_yscale("log")
        ax.set_ylim(min(run) * 0.35, max(run) * 3.2)
        ax.set_xlim(-0.8, len(keys) + 1.9)
        ax.set_ylabel(MATLAB[mat], fontsize=7)
        ax.tick_params(labelsize=5.8)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)

    axes[-1].set_xticks(np.arange(len(keys)) + 0.5)
    axes[-1].set_xticklabels(labs, fontsize=5.8, rotation=28, ha="right")
    axes[0].set_title("Heterotroph crowding removes 61\u201386 % of the flux; oxygen removes none",
                      loc="left", fontsize=8.5, pad=8)
    fig.text(0.012, 0.012,
             "Median-flux arm of each material, day 60, 15 °C. The running value starts at "
             "the reference areal rate and is multiplied by each term in turn, ending exactly "
             "at the model's own $J_A$\n(max relative residual 3.5e-16 over 12 arms). Blue "
             "raises the flux, red lowers it. Bin-dependent terms are credited in the order "
             "shown; the scalar terms are order-free.",
             fontsize=5.8, color="#6B7280", va="bottom")
    fig.tight_layout(rect=(0, 0.075, 1, 1))
    p = os.path.join(HERE, out)
    fig.savefig(p, dpi=300)
    return fig, d, p


if __name__ == "__main__":
    try:
        apply_figure_style()                       # noqa: F821
    except NameError:
        pass
    fig, d, p = draw()
    keys = [k for k, _ in DC.LABELS]
    print(d.groupby("material")[keys].median().round(4).to_string())
    print("\nwrote", p)
