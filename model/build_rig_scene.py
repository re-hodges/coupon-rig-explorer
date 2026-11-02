"""Build the interactive rig scene for the explorer's "Rig in 3D" tab.

Emits rig_scene.json: axis-aligned primitives (boxes and cylinders) in Blender world
coordinates, Z up, generated from the SAME constants as Blender_site_model/scene_source/
as_rig.py and from coupon_model/rig.yaml, so the browser view and the rendered scene can
not disagree about vessel or coupon geometry.

Also emits the per-vessel light field: relative irradiance on each coupon face under the
modelled LED panel, by numerical quadrature over the panel (Lambertian, uniform radiance),
normalised to a horizontal surface at coupon mid-height under the chamber centre.
"""
import json, math, os, sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))

def rig_yaml(path):
    vals, in_geom = {}, False
    for raw in open(path, encoding="utf-8"):
        line = raw.split("#")[0].rstrip()
        if not line.strip():
            continue
        if not line.startswith((" ", "\t")):
            in_geom = line.strip().rstrip(":") == "geometry"
            continue
        if in_geom and ":" in line:
            k, v = line.split(":", 1)
            try:
                vals[k.strip()] = float(v.strip())
            except ValueError:
                pass
    return vals

RY = rig_yaml(os.path.join(HERE, "rig.yaml"))
COUPON_AREA = RY["coupon_area_m2"]          # m2 wetted per vessel (f_wet = 1 at the rig)
VOLUME      = RY["working_volume_l"] / 1000.0
VES_R  = 0.050
R_LIQ  = VES_R - 0.004
WATER  = VOLUME / (math.pi * R_LIQ ** 2)
VES_H  = max(0.150, WATER + 0.060)
COUPON_W, COUPON_T = 0.030, 0.002
COUPON_H = COUPON_AREA / (2.0 * COUPON_W)
BENCH_Z = 0.90
CH_W, CH_D = 0.88, 0.52
PW, PD = CH_W - 0.07, CH_D - 0.07            # LED panel
PZ = BENCH_Z + 0.437

MATERIALS = [("FAB", "Non-woven fabric"), ("STL", "Bare steel"),
             ("GRA", "Graphene-coated"), ("PE", "HDPE")]
PHOTO = [("FBK", "Fairbanks AK", "5 h 00"), ("STG", "Sturgis SD", "9 h 12"),
         ("KEY", "Key West FL", "10 h 46")]

# ---------------------------------------------------------------- light field
# Radiosity over the chamber interior, not direct light alone. RULING 2 Nov 2026: the
# chambers are lined WHITE and the field is treated as uniform across the coupons; the
# calculation below is what justifies that. Direct light from the panel alone leaves the
# four substrate columns 1.33x apart, because a vertical coupon near the panel's edge sees
# less of it. With white walls the bounced field dominates on vertical surfaces and the
# column difference falls to about 1.04x.
#
# Surfaces: bench floor, back wall, two side walls, ceiling (the LED is the emitting part
# of it). FRONT_OPEN keeps the open front of the as-built chamber, where escaping light
# leaves a front-to-back gradient; closing it with a white panel removes that and equalises
# the two coupon faces.
WALL_RHO   = 0.85        # white-lined interior
FRONT_OPEN = True        # as built: the chamber has no front panel
PATCH      = 0.04        # m, radiosity patch size
CH_H       = 0.44

def _grid(p0, e1, e2, n1, n2, normal):
    p0 = np.asarray(p0, float); e1 = np.asarray(e1, float); e2 = np.asarray(e2, float)
    area = (np.linalg.norm(e1) / n1) * (np.linalg.norm(e2) / n2)
    pts = [p0 + e1 * ((i + 0.5) / n1) + e2 * ((j + 0.5) / n2)
           for i in range(n1) for j in range(n2)]
    return (np.array(pts), np.tile(np.asarray(normal, float), (n1 * n2, 1)),
            np.full(n1 * n2, area))

def _enclosure():
    nx, ny, nz = int(CH_W / PATCH), int(CH_D / PATCH), int(CH_H / PATCH)
    C, N, A, E = [], [], [], []
    def add(c, n, a, em):
        C.append(c); N.append(n); A.append(a); E.append(em)
    c, n, a = _grid([-CH_W/2, -CH_D/2, BENCH_Z], [CH_W,0,0], [0,CH_D,0], nx, ny, [0,0,1])
    add(c, n, a, np.zeros(len(a)))                                    # bench floor
    c, n, a = _grid([-CH_W/2, CH_D/2, BENCH_Z], [CH_W,0,0], [0,0,CH_H], nx, nz, [0,-1,0])
    add(c, n, a, np.zeros(len(a)))                                    # back wall
    if not FRONT_OPEN:
        c, n, a = _grid([-CH_W/2, -CH_D/2, BENCH_Z], [CH_W,0,0], [0,0,CH_H], nx, nz, [0,1,0])
        add(c, n, a, np.zeros(len(a)))                                # optional front panel
    for sx, nrm in ((-CH_W/2, [1,0,0]), (CH_W/2, [-1,0,0])):
        c, n, a = _grid([sx, -CH_D/2, BENCH_Z], [0,CH_D,0], [0,0,CH_H], ny, nz, nrm)
        add(c, n, a, np.zeros(len(a)))                                # side walls
    c, n, a = _grid([-CH_W/2, -CH_D/2, BENCH_Z+CH_H], [CH_W,0,0], [0,CH_D,0], nx, ny, [0,0,-1])
    em = ((np.abs(c[:,0]) <= PW/2) & (np.abs(c[:,1]) <= PD/2)).astype(float)
    add(c, n, a, em)                                                  # ceiling + LED
    return np.vstack(C), np.vstack(N), np.concatenate(A), np.concatenate(E)

def _radiosity(rho):
    C, N, A, E = _enclosure()
    d = C[None,:,:] - C[:,None,:]
    r2 = (d*d).sum(-1); np.fill_diagonal(r2, 1e9); r = np.sqrt(r2)
    ci = (N[:,None,:]*d).sum(-1)/r
    cj = -(N[None,:,:]*d).sum(-1)/r
    F = np.clip(ci,0,None)*np.clip(cj,0,None)*A[None,:]/(math.pi*r2)
    np.fill_diagonal(F, 0.0)
    B = E.copy()
    for _ in range(90):
        B = E + rho * (F @ B)
    return C, N, A, B

def face_irradiance(C, N, A, B, px, py, pz, nrm):
    d = C - np.array([px, py, pz]); r2 = (d*d).sum(1); r = np.sqrt(r2)
    cj = -(N*d).sum(1)/r
    cp = ((-d) @ np.asarray(nrm, float))/r
    return float((B*np.clip(cj,0,None)*np.clip(cp,0,None)*A/(math.pi*r2)).sum())

def build():
    zc = BENCH_Z + 0.012 + COUPON_H / 2.0                     # coupon mid-height
    C, N, A, Bq = _radiosity(WALL_RHO)
    ref = face_irradiance(C, N, A, Bq, 0.0, 0.0, zc, (0, 0, 1))   # horizontal, centre

    parts, vessels, labels = [], [], []
    def box(role, cx, cy, cz, sx, sy, sz, vid=-1):
        parts.append({"t": "b", "role": role, "v": vid,
                      "c": [round(cx, 5), round(cy, 5), round(cz, 5)],
                      "s": [round(sx, 5), round(sy, 5), round(sz, 5)]})
    def cyl(role, cx, cy, cz, r, h, vid=-1):
        parts.append({"t": "c", "role": role, "v": vid,
                      "c": [round(cx, 5), round(cy, 5), round(cz, 5)],
                      "r": round(r, 5), "h": round(h, 5)})

    box("bench", 0, 0, BENCH_Z - 0.0225, 3.10, 1.15, 0.045)
    for sx in (-1.45, 1.45):
        for sy in (-0.50, 0.50):
            box("leg", sx, sy, (BENCH_Z - 0.045) / 2, 0.05, 0.05, BENCH_Z - 0.045)

    n = 0
    for ci, (pcode, city, hrs) in enumerate(PHOTO):
        x0 = (ci - 1) * 1.00
        box("panel", x0, CH_D / 2, BENCH_Z + 0.22, CH_W, 0.012, 0.44)
        for s in (-1, 1):
            box("panel", x0 + s * CH_W / 2, 0, BENCH_Z + 0.22, 0.012, CH_D, 0.44)
        box("hood", x0, 0, BENCH_Z + 0.45, CH_W, CH_D, 0.018)
        box("led", x0, 0, BENCH_Z + 0.437, PW, PD, 0.006)
        labels.append({"k": "chamber", "t": hrs + " light  \u00b7  " + city,
                       "p": [x0, -CH_D / 2, BENCH_Z + 0.50]})
        for si, (mcode, mname) in enumerate(MATERIALS):
            vx = x0 - CH_W / 2 + 0.115 + si * 0.215
            box("card", vx, -CH_D / 2 - 0.045, BENCH_Z + 0.008, 0.17, 0.004, 0.016,
                vid=-(si + 2))                                 # colour-keyed to material
            for rep in range(3):
                vy = -CH_D / 2 + 0.115 + rep * 0.145
                cyl("glass",  vx, vy, BENCH_Z + VES_H / 2, VES_R, VES_H, n)
                cyl("liquor", vx, vy, BENCH_Z + WATER / 2, R_LIQ, WATER, n)
                box("holder", vx, vy, BENCH_Z + 0.010, COUPON_W + 0.010, 0.012, 0.012, n)
                box("coupon", vx, vy, BENCH_Z + 0.012 + COUPON_H / 2,
                    COUPON_W, COUPON_T, COUPON_H, n)
                box("film",   vx, vy, BENCH_Z + 0.012 + COUPON_H / 2,
                    COUPON_W * 1.02, COUPON_T * 2.6, COUPON_H * 0.98, n)
                # light field on the two faces: +y looks at the back of the chamber
                lx = vx - x0                               # chamber-local x
                e_back  = face_irradiance(C, N, A, Bq, lx, vy, zc, (0, 1, 0)) / ref
                e_front = face_irradiance(C, N, A, Bq, lx, vy, zc, (0, -1, 0)) / ref
                e_horiz = face_irradiance(C, N, A, Bq, lx, vy, zc, (0, 0, 1)) / ref
                vessels.append({"i": n, "m": mcode, "p": pcode, "rep": rep + 1,
                                "x": round(vx, 4), "y": round(vy, 4),
                                "eb": round(e_back, 4), "ef": round(e_front, 4),
                                "em": round((e_back + e_front) / 2, 4),
                                "eh": round(e_horiz, 4)})
                n += 1
    scene = {
        "meta": {
            "bench_z": BENCH_Z, "ves_r": VES_R, "ves_h": round(VES_H, 5),
            "water": round(WATER, 5), "r_liq": round(R_LIQ, 5),
            "coupon_w": COUPON_W, "coupon_t": COUPON_T, "coupon_h": round(COUPON_H, 5),
            "coupon_area_m2": COUPON_AREA, "volume_l": VOLUME * 1000.0,
            "ch_w": CH_W, "ch_d": CH_D, "panel": [PW, PD, round(PZ, 4)],
            "film_rho_g_per_l": 211.0,
            "materials": MATERIALS, "photoperiods": PHOTO,
            "light_note": ("relative irradiance on the coupon faces, radiosity over a white-lined "
                           "chamber (rho %.2f, front %s); 1.0 = a horizontal surface at coupon "
                           "mid-height under the chamber centre; the lamp is a reconstruction"
                           % (WALL_RHO, "open" if FRONT_OPEN else "closed")),
            "source": "build_rig_scene.py from rig.yaml + as_rig.py constants",
            "wall_rho": WALL_RHO, "front_open": FRONT_OPEN,
        },
        "parts": parts, "vessels": vessels, "labels": labels,
    }
    return scene

if __name__ == "__main__":
    sc = build()
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "rig_scene.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(sc, f, separators=(",", ":"))
    print("parts", len(sc["parts"]), "vessels", len(sc["vessels"]),
          "bytes", os.path.getsize(out))
    csv = os.path.join(os.path.dirname(out), "rig_lamp_uniformity_v4.csv")
    with open(csv, "w", encoding="utf-8", newline="") as f:
        f.write("substrate,photoperiod,replicate,x_m,y_m,horiz_rel,face_back_rel,"
                "face_front_rel,two_face_mean_rel,bright_dim_ratio\n")
        names = dict(MATERIALS)
        for v in sc["vessels"]:
            hi, lo = max(v["eb"], v["ef"]), min(v["eb"], v["ef"])
            f.write("%s,%s,%d,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f,%.1f\n" %
                    (names[v["m"]], v["p"], v["rep"], v["x"], v["y"], v["eh"],
                     v["eb"], v["ef"], v["em"], hi / lo if lo > 0 else float("inf")))
    print("wrote", csv)
