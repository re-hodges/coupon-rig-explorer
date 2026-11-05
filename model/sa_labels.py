"""Single source of truth for how every sensitivity input is NAMED on a figure.

Three strings per input, used for different amounts of space:

  LONG   a plain-language name a reader understands without the glossary
  SHORT  the same idea compressed, for axis ticks and heatmap rows
  SYM    the model's own symbol, kept visible so the figure still ties back to
         MODEL.md, GLOSSARY.md and the code

The symbol is never DROPPED, only demoted to a second line. This project's standing
rule is that reported quantities use terminology already current in the field rather
than newly coined names, so these strings describe the existing symbol in words — they
are not a competing notation, and nothing here should be cited as a symbol.

Every figure script imports from here. If a name changes it changes everywhere,
including the variable key at the foot of the Sensitivity tab.
"""

# parameter -> (LONG, SHORT, SYM)
LABELS = {
    "K_comp":   ("heterotroph crowding on nitrifiers", "heterotroph crowding", "K_comp"),
    "X_cap":    ("film carrying capacity",             "film capacity",        "X_cap"),
    "rN_ref":   ("reference nitrification rate",       "nitrification rate",   "r_N,ref"),
    "rpm":      ("wheel rotation speed",               "wheel speed",          "n"),
    "n_shear":  ("shear sensitivity of detachment",    "shear sensitivity",    "n_shear"),
    "k_det":    ("detachment rate",                    "detachment",           "k_det"),
    "shelter":  ("divot shelter from shear",           "divot shelter",        "phi_shear"),
    "k_att":    ("attachment flux",                    "attachment",           "k_att"),
    "Sb":       ("feed organic load",                  "feed BOD",             "S_b"),
    "theta_h":  ("heterotroph temperature coefficient", "heterotroph theta",   "theta_h"),
    "b_p":      ("phototroph decay rate",              "phototroph decay",     "b_p"),
    "D_O2_eff": ("oxygen diffusivity in the film",     "O2 diffusivity",       "D_O2,eff"),
    "timer_h":  ("lamp hours per day",                 "lamp hours",           "timer_h"),
    "K_I":      ("light half-saturation",              "light half-sat.",      "K_I"),
    "S_O_bulk": ("bulk dissolved oxygen",              "bulk oxygen",          "S_O"),
    "I0":       ("incident light intensity",           "incident light",       "I_0"),
    "theta_p":  ("phototroph temperature coefficient", "phototroph theta",     "theta_p"),
    "Y_O2_p":   ("oxygen yield from phototrophs",      "O2 yield",             "Y_O2,p"),
    "K_P_p":    ("phosphorus half-saturation",         "P half-sat.",          "K_P,p"),
    "material": ("coupon material",                    "material",             "material"),
}

# how the input ACTS in the model: the one clause that makes the name make sense
ROLE = {
    "K_comp":   "multiplies nitrification by K_comp/(K_comp+Xh), so nitrification halves "
                "once heterotroph biomass reaches this value",
    "X_cap":    "the total areal biomass at which the shared capacity term closes and no "
                "guild can grow further",
    "rN_ref":   "the areal nitrification rate at reference conditions; every other term in "
                "the flux chain scales it",
    "rpm":      "sets the submerged/emergent duty cycle and, through the rotating-disc "
                "correlation, the wall shear",
    "n_shear":  "the exponent in k_det proportional to tau^n; zero means detachment ignores "
                "shear entirely",
    "k_det":    "the fraction of film lost per day before the shear modifier is applied",
    "shelter":  "scales the wall shear a recessed coupon feels; 1.0 is flush with the band",
    "k_att":    "the areal attachment flux onto bare HDPE, multiplied by the material factor",
    "Sb":       "the substrate reaching the first stage; feeds heterotrophs, which then "
                "crowd the nitrifiers",
    "theta_h":  "Arrhenius coefficient on heterotroph growth; live here because these runs "
                "are at 15 C, not 20 C",
    "b_p":      "phototroph decay and maintenance, including dark respiration",
    "D_O2_eff": "sets the oxygen penetration depth and so the effectiveness factor eta_O2",
    "timer_h":  "the lamp timer; light delivered is timer_h x (1 - f_wet), because a "
                "submerged coupon is a dark coupon",
    "K_I":      "half-saturation of the phototroph light response",
    "S_O_bulk": "imposed bulk dissolved oxygen; a boundary condition, never a state",
    "I0":       "incident photon flux at the coupon before the divot view factor",
    "theta_p":  "Arrhenius coefficient on phototroph growth",
    "Y_O2_p":   "oxygen produced per unit phototroph biomass grown",
    "K_P_p":    "half-saturation of phototroph phosphorus uptake",
    "material": "enters through the attachment factor and, for graphene, a maturation factor",
}

GROUP_LABELS = {
    "surface":       "surface properties",
    "environmental": "environmental &\nphysiological",
    "biological":    "biological",
}


def long(p):
    return LABELS.get(p, (p, p, p))[0]


def short(p):
    return LABELS.get(p, (p, p, p))[1]


def sym(p):
    return LABELS.get(p, (p, p, p))[2]


def two_line(p, width=None):
    """Descriptive name over the model's own symbol, for axis ticks."""
    return f"{short(p)}\n({sym(p)})"


def role(p):
    return ROLE.get(p, "")
