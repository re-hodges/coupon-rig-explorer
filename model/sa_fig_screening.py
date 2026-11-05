"""Re-draws the two SCREENING figures that predate the surrogate's retirement.

Both analyses were always computed on the model itself -- Morris elementary effects on
the ODE, and an exact variance decomposition on the complete 864-arm factorial -- so
only their PRESENTATION was stale. They were still being rendered in the old dark house
style, with the old naming ("competition half-sat" for what every other figure now calls
heterotroph crowding), while the six surrogate-free figures beside them are light.

This script reads the same CSVs the old scripts wrote (sa_morris.csv,
sa_factorial_targets.csv) and redraws them with the shared label vocabulary in
sa_labels.py. It fits nothing and re-runs nothing.
"""
import os, sys
import numpy as np, pandas as pd
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sa_labels as LB

FOCAL, OK, GREY = "#C8102E", "#2B5D7D", "#8A8F98"
RESP = [("X_d60", "total biofilm"), ("Xp_d60", "phototrophs"), ("Xn_d60", "nitrifiers"),
        ("Xh_d60", "heterotrophs"), ("JA_d60", "removal flux")]
# design-factor names: defer to the shared vocabulary, add the two it does not carry
FACT = {"material": "coupon material", "photoperiod": "photoperiod",
        "rpm": LB.short("rpm"), "n_shear": LB.short("n_shear"),
        "shelter": LB.short("shelter"), "load": "feed organic load"}


def fig_morris(out="fig_sa_morris.png", nlab=8):
    mo = pd.read_csv(os.path.join(HERE, "sa_morris.csv")).sort_values("mu_star",
                                                                     ascending=False)
    ev = pd.read_csv(os.path.join(HERE, "sa_evidence.csv"))[["parameter", "evidence_score"]]
    d = mo.merge(ev, on="parameter", how="left")
    top = d.head(nlab)
    rest = d.iloc[nlab:]
    nosrc = int((top.evidence_score == 0).sum())

    fig, ax = plt.subplots(figsize=(7.6, 5.0))
    lim = max(d.mu_star.max(), d.sigma.max()) * 1.12
    ax.plot([0, lim], [0, lim], color=GREY, lw=0.8, ls=(0, (4, 3)), zorder=1)
    ax.scatter(rest.mu_star, rest.sigma, s=26, color=GREY, alpha=0.65,
               edgecolor="none", zorder=3)
    for _, r in top.iterrows():
        c = FOCAL if r.evidence_score == 0 else OK
        ax.scatter(r.mu_star, r.sigma, s=52, color=c, edgecolor="white",
                   linewidth=0.7, zorder=4)
        ax.annotate(f"{LB.short(r.parameter)}\n({LB.sym(r.parameter)})",
                    (r.mu_star, r.sigma), xytext=(7, 6), textcoords="offset points",
                    fontsize=5.8, color=c, zorder=5,
                    fontweight="bold" if r.evidence_score == 0 else "normal")
    ax.set_xlabel("$\\mu^*$   mean |elementary effect| on day-60 areal removal flux "
                  "(g N m$^{-2}$ d$^{-1}$)", fontsize=7)
    ax.set_ylabel("$\\sigma$   spread of elementary effects", fontsize=7)
    ax.set_title(f"Screening on the ODE: {nosrc} of the {nlab} most influential inputs "
                 "have no source", loc="left", fontsize=8.5)
    ax.text(0.98, 0.05, f"{len(rest)} further inputs below "
            f"$\\mu^*$ = {top.mu_star.min():.3f}\\nred = no source for its value\\n"
            "off the diagonal = non-linear or interacting",
            transform=ax.transAxes, fontsize=6, ha="right", va="bottom", color=GREY)
    ax.set_xlim(-0.03 * lim, lim); ax.set_ylim(-0.03 * lim, lim)
    ax.tick_params(labelsize=6)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    p = os.path.join(HERE, out)
    fig.savefig(p, dpi=300)
    return p, top


def fig_factorial(out="fig_sa_factorial_targets.png"):
    f = pd.read_csv(os.path.join(HERE, "sa_factorial_targets.csv")).set_index("factor")
    f = f.loc[[k for k in FACT if k in f.index]]
    y = np.arange(len(f))
    hgt = 0.15
    cmap = plt.get_cmap("viridis")
    fig, ax = plt.subplots(figsize=(7.6, 4.6))
    for i, (col, lab) in enumerate(RESP):
        ax.barh(y + (i - 2) * hgt, f[col].values, height=hgt,
                color=cmap(i / (len(RESP) - 1)), label=lab, alpha=0.92)
    ax.set_yticks(y)
    ax.set_yticklabels([FACT[k] for k in f.index], fontsize=6.6)
    ax.invert_yaxis()
    ax.set_xlabel("total Sobol' index $S_T$ on the 864-arm factorial", fontsize=7)
    ax.set_title("Photoperiod drives phototroph biomass and almost nothing else",
                 loc="left", fontsize=8.5)
    ax.text(0, -0.155, "Exact decomposition \u2014 the grid is a complete orthogonal "
            "design, so these indices need no sampling and no surrogate. Shares are among "
            "the SIX DESIGN FACTORS the team sets,\nnot among all 20 model inputs: "
            "material reads 0.50 here and 0.25 in the Sobol' figure above, which uses the "
            "wider denominator. Both are correct; they answer different questions.",
            transform=ax.transAxes, fontsize=5.8, color=GREY, va="top")
    ax.legend(fontsize=6, frameon=False, ncol=5, loc="lower center",
              bbox_to_anchor=(0.5, -0.30))
    ax.tick_params(labelsize=6)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout(rect=(0, 0.13, 1, 1))
    p = os.path.join(HERE, out)
    fig.savefig(p, dpi=300)
    return p, f


if __name__ == "__main__":
    try:
        apply_figure_style()                       # noqa: F821
    except NameError:
        pass
    p1, top = fig_morris()
    print("MORRIS top inputs:\n", top[["parameter", "mu_star", "sigma",
                                       "evidence_score"]].to_string(index=False))
    print("wrote", p1)
    p2, f = fig_factorial()
    print("\nFACTORIAL:\n", f.round(3).to_string())
    print("wrote", p2)
