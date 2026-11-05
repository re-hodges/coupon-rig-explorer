"""Figure: which inputs drive which response (fig_sa_targets_givendata.png).

Surrogate-free replacement for the old SHAP-share heatmap.

The share measure is the SQUARED standardised rank regression coefficient, normalised so
each column sums to 1. Squared standardised coefficients are a principled variance
partition when the inputs are sampled independently, which they are here, and they sum to
the rank regression's R2. That R2 is printed under each column so a reader can see how
much of the response the partition actually covers.

The three material dummy columns are summed back into a single material row. Summing
squares is exact for a one-hot encoding of one categorical input.
"""
import os
import numpy as np, pandas as pd
import matplotlib.pyplot as plt
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sa_labels as LB

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = {"X_d60": "total\nbiofilm", "Xp_d60": "photo-\ntrophs", "Xn_d60": "nitri-\nfiers",
       "Xh_d60": "hetero-\ntrophs", "JA_d60": "removal\nflux"}
ORDER = ["X_d60", "Xp_d60", "Xn_d60", "Xh_d60", "JA_d60"]


def draw(out="fig_sa_targets_givendata.png"):
    G = pd.read_csv(os.path.join(HERE, "sa_givendata.csv"))
    M = pd.read_csv(os.path.join(HERE, "sa_givendata_meta.csv")).set_index("target")
    W = (G[G.method == "SRRC"]
         .pivot_table(index="parameter", columns="target", values="value")
         .reindex(columns=ORDER))
    sq = W ** 2
    mat = sq[sq.index.str.startswith("material[")].sum()
    sq = sq[~sq.index.str.startswith("material[")]
    sq.loc["material"] = mat
    share = sq / sq.sum()
    share = share.loc[share.mean(axis=1).sort_values(ascending=False).index]

    fig, ax = plt.subplots(figsize=(5.6, 5.6))
    im = ax.imshow(share.values, aspect="auto", cmap="magma_r", vmin=0,
                   vmax=float(share.values.max()))
    ax.set_xticks(range(len(ORDER)))
    ax.set_xticklabels([f"{LAB[t]}\nR\u00b2={M.loc[t,'R2_SRRC']:.2f}" for t in ORDER],
                       fontsize=6.2)
    ax.set_yticks(range(len(share)))
    ax.set_yticklabels([LB.two_line(p) for p in share.index], fontsize=5.4)
    hi = float(share.values.max())
    for i in range(share.shape[0]):
        for j in range(share.shape[1]):
            v = share.values[i, j]
            txt = "·" if v < 0.005 else f"{v:.2f}"
            ax.text(j, i, txt, ha="center", va="center", fontsize=5.6,
                    color="white" if v > 0.55 * hi else "#2A2E35")
    ax.set_title("Material leads every response except heterotrophs (feed BOD) and flux (crowding)",
                 loc="left", fontsize=7.8, pad=8)
    ax.text(0, -0.105, "share of each column's explained variance (squared SRRC, "
            "normalised) · 4,096 ODE runs · no surrogate\n"
            "R² under each column is the rank regression's own fit: the fraction of that "
            "response the partition covers.",
            transform=ax.transAxes, fontsize=5.8, color="#6B7280", va="top")
    ax.tick_params(length=0)
    cb = fig.colorbar(im, ax=ax, fraction=0.035, pad=0.04)
    cb.ax.tick_params(labelsize=5.5)
    fig.tight_layout()
    p = os.path.join(HERE, out)
    fig.savefig(p, dpi=300, bbox_inches="tight")
    return fig, share, p


if __name__ == "__main__":
    try:
        apply_figure_style()                       # noqa: F821
    except NameError:
        pass
    fig, share, p = draw()
    print(share.round(3).to_string())
    print("\nwrote", p)
