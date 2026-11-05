"""One shard of the surrogate-free sweep (sa_ode2_design.csv).

    python sa_ode_worker.py <shard> <n_shards>

Reads sa_ode2_design.csv, runs every row whose run_id is congruent to <shard> mod
<n_shards>, appends to sa_ode2_results_<shard>.csv after every row so a killed worker
loses one run rather than the shard, and SKIPS run_ids already present on restart.

Separate processes, not threads: the reactor RHS is pure Python so LSODA holds the GIL
(sa_worker.py measured 3.93 s/run on 8 threads against 4.43 s/run on one). Four workers
rather than five -- each holds roughly 400 MB and the box reported ~3 GiB free.
"""
import os, sys, time, glob
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sa_worker as W

OUTCOLS = ["JA_d60", "JA_d10", "JA_d5", "X_d60", "X_d10", "X_d5",
           "Xp_d60", "Xn_d60", "Xh_d60", "Lf_d60",
           "f_wet", "delivered_h", "tau_Pa", "k_det_eff", "finite"]


def main():
    """sa_ode_worker.py <shard> <n_shards> [<sub> <n_sub>]

    The optional sub-split exists because a worker dies silently under memory pressure
    now and then -- it happened to shard 3 of this sweep, which stopped writing after
    1,385 of its 2,200 rows while the other three ran on. Re-running a lost shard
    serially costs the better part of an hour; splitting its remainder four ways costs a
    quarter of that. Resume scans EVERY result file, not just this worker's own, so a
    re-split never repeats a run another process already finished.
    """
    shard, nsh = int(sys.argv[1]), int(sys.argv[2])
    sub, nsub = (int(sys.argv[3]), int(sys.argv[4])) if len(sys.argv) > 4 else (0, 1)
    tag = f"{shard}" if nsub == 1 else f"{shard}s{sub}"
    d = pd.read_csv(os.path.join(HERE, "sa_ode2_design.csv"))
    mine = d[d.run_id % nsh == shard]
    if nsub > 1:
        mine = mine.iloc[sub::nsub]
    out = os.path.join(HERE, f"sa_ode2_results_{tag}.csv")
    done = set()
    for f in glob.glob(os.path.join(HERE, "sa_ode2_results_*.csv")):
        try:
            done |= set(pd.read_csv(f).run_id.tolist())
        except Exception:
            pass
    todo = mine[~mine.run_id.isin(done)]
    log = open(os.path.join(HERE, f"sa_ode2_log_{tag}.txt"), "a", buffering=1)
    log.write(f"shard {shard}/{nsh} sub {sub}/{nsub}: {len(mine)} rows, "
              f"{len(done)} already done globally, {len(todo)} to run\n")
    t0 = time.time()
    first = not os.path.exists(out) or os.path.getsize(out) == 0
    f = open(out, "a", newline="", buffering=1)
    if first:
        f.write("run_id," + ",".join(OUTCOLS) + "\n")
    for i, (_, row) in enumerate(todo.iterrows()):
        try:
            r = W.run_point(row)
            f.write(str(int(row.run_id)) + "," +
                    ",".join(repr(r[c]) for c in OUTCOLS) + "\n")
        except Exception as e:                      # one bad point must not kill a shard
            log.write(f"FAIL run_id={int(row.run_id)}: {type(e).__name__}: {e}\n")
        if i % 50 == 0:
            el = time.time() - t0
            rate = (i + 1) / max(el, 1e-9)
            log.write(f"{i+1}/{len(todo)}  {el/60:.1f} min  {rate:.2f} run/s  "
                      f"eta {(len(todo)-i-1)/max(rate,1e-9)/60:.1f} min\n")
    f.close()
    log.write(f"DONE shard {tag} in {(time.time()-t0)/60:.1f} min\n")
    log.close()


if __name__ == "__main__":
    main()
