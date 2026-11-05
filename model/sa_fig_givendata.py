"""Figure: do the model-truth rankings agree? (fig_sa_givendata.png)

Six measures, all computed on the differential equations from runs already on disk.
Each column is normalised to its own maximum so the methods can be compared as
rankings rather than as numbers on incompatible scales.

Material is NOT a row here: it is categorical, handled by stratification for the
distribution-based methods, and its influence is reported by the exact factorial and
by the Sobol' run on the ODE.
"""
import os
import numpy as np, pandas as pd
import matplotlib.pyplot as plt
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sa_labels as LB

HERE = os.path.dirname(os.path.abspath(__file__))
METHODS = ["SRC", "SRRC", "PRCC", "delta", "pawn", "rbd_S1"]
NICE = {"SRC": "SRC", "SRRC": "SRRC", "PRCC": "PRCC", "delta": "Borgonovo\n$\\delta$",
        "pawn": "PAWN", "rbd_S1": "RBD-FAST\n$S_1$"}


def draw(target="JA_d60", out="fig_sa_givendata.png"):
    G = pd.read_csv(os.path.join(HERE, "sa_givendata.csv"))
    M = pd.read_csv(os.path.join(HERE, "sa_givendata_meta.csv")).set_index("target")
    W = (G[G.target == target]
         .pivot_table(index="parameter", columns="method", values="value")
         .reindex(columns=METHODS))
    W = W[~W.index.str.startswith("material[")]
    A = W.abs()
    N = A / A.max()                       # normalise each method to its own maximum
    N = N.loc[N.mean(axis=1).sort_values(ascending=False).index]

    fig, ax = plt.subplots(figsize=(9.2, 7.4))
    im = ax.imshow(N.values, aspect="auto", cmap="magma_r", vmin=0, vmax=1)
    ax.set_xticks(range(len(METHODS)))
    ax.set_xticklabels([NICE[m] for m in METHODS], fontsize=7.4)
    ax.set_yticks(range(len(N)))
    ax.set_yticklabels([LB.two_line(p) for p in N.index], fontsize=6.8)
    for i in range(N.shape[0]):
        for j in range(N.shape[1]):
            v = N.values[i, j]
            ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=6.6,
                    color="white" if v > 0.55 else "#2A2E35")
    sgn = W["PRCC"].reindex(N.index)
    for i, s in enumerate(sgn):
        if abs(s) > 0.15:
            ax.text(len(METHODS) - 0.35, i, "+" if s > 0 else "\u2212",
                    fontsize=8, ha="left", va="center",
                    color="#2B5D7D" if s > 0 else "#C8102E")
    ax.text(len(METHODS) - 0.35, len(N) - 0.3, "sign\n(PRCC)", fontsize=5.6, ha="left",
            va="top", color="#6B7280")

    r2 = M.loc[target]
    ax.set_title("Six independent measures on the equations agree: "
                 "$K_{comp}$ dominates the flux", loc="left", fontsize=8.5, pad=10)
    ax.text(0, -0.055,
            f"day-60 areal removal flux \u00b7 n = {int(r2.n)} runs of the ODE \u00b7 no surrogate "
            f"\u00b7 linear fit R\u00b2 = {r2.R2_SRC:.2f} \u00b7 monotone fit R\u00b2 = {r2.R2_SRRC:.2f}",
            transform=ax.transAxes, fontsize=6.2, color="#6B7280", va="top")
    cb = fig.colorbar(im, ax=ax, fraction=0.035, pad=0.11)
    cb.set_label("importance, each method scaled to its own maximum", fontsize=6)
    cb.ax.tick_params(labelsize=5.5)
    ax.tick_params(length=0)
    fig.tight_layout()
    p = os.path.join(HERE, out)
    fig.savefig(p, dpi=300, bbox_inches="tight")
    return fig, N, p


if __name__ == "__main__":
    try:
        apply_figure_style()                       # noqa: F821
    except NameError:
        pass
    fig, N, p = draw()
    print(N.round(3).to_string())
    print("\nwrote", p)
