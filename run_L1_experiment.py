#!/usr/bin/env python3
import os
import csv
import subprocess
import shutil

# === PATHS ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GEM5_DIR = os.path.join(BASE_DIR, "../gem5")

gem5_bin = os.path.join(GEM5_DIR, "build/ARM/gem5.fast")
config_script = os.path.join(GEM5_DIR, "scripts/CortexA76_scripts_gem5/CortexA76.py")
workload = os.path.join(GEM5_DIR, "workloads/jpeg2k_dec/jpg2k_dec")
workload_args = f"-i {GEM5_DIR}/workloads/jpeg2k_dec/jpg2kdec_testfile.j2k -o image.pgm"

# === OUTPUT DIRECTORIES ===
RESULTS_DIR = os.path.join(BASE_DIR, "results")
M5OUT_ROOT = os.path.join(RESULTS_DIR, "m5outs")
os.makedirs(M5OUT_ROOT, exist_ok=True)

# === PARAMETERS TO VARY ===
l1_sizes = ["32kB", "64kB", "128kB"]  # Only L1 cache varies
l2_size = "512kB"  # Fixed L2 cache size

# === CSV OUTPUT FILE ===
csv_file = os.path.join(RESULTS_DIR, "results_L1_experiment.csv")

# === FUNCTION TO PARSE STATS.TXT ===
def extract_stats(stats_file):
    stats = {
        "sim_seconds": None,
        "ipc": None,
        "cpi": None,
        "num_cycles": None,
        "dcache_misses": None,
        "dcache_accesses": None
    }
    if not os.path.exists(stats_file):
        print(f"  Stats file not found: {stats_file}")
        return stats

    with open(stats_file) as f:
        for line in f:
            if line.startswith("simSeconds"):
                stats["sim_seconds"] = float(line.split()[1])
            elif line.startswith("system.cpu.ipc"):
                stats["ipc"] = float(line.split()[1])
            elif line.startswith("system.cpu.cpi"):
                stats["cpi"] = float(line.split()[1])
            elif line.startswith("system.cpu.numCycles"):
                stats["num_cycles"] = int(line.split()[1])
            elif "system.cpu.dcache.demandMisses::total" in line:
                stats["dcache_misses"] = int(line.split()[1])
            elif "system.cpu.dcache.demandAccesses::total" in line:
                stats["dcache_accesses"] = int(line.split()[1])
    return stats

# === CREATE RESULTS DIRECTORY AND CSV FILE ===
os.makedirs(RESULTS_DIR, exist_ok=True)
with open(csv_file, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow([
        "L1_size",
        "sim_seconds",
        "ipc",
        "cpi",
        "num_cycles",
        "dcache_misses",
        "dcache_accesses"
    ])

# === RUN SIMULATIONS ===
for size in l1_sizes:
    out_dir = os.path.join(M5OUT_ROOT, f"L1_{size}")
    os.makedirs(out_dir, exist_ok=True)
    print(f"\n=== Running simulation with L1={size} ===")

    cmd = [
        gem5_bin,
        f"--outdir={out_dir}",
        config_script,
        "-c", workload,
        "-o", workload_args,
        f"--l1i_size={size}",
        f"--l1d_size={size}",
        f"--l2_size={l2_size}",
    ]

    subprocess.run(cmd, check=True)

    # Save config.ini for each run
    src_config = os.path.join(out_dir, "config.ini")
    dst_config = os.path.join(RESULTS_DIR, f"config_L1_{size}.ini")
    if os.path.exists(src_config):
        shutil.copy(src_config, dst_config)
        print(f" Saved configuration to {dst_config}")
    else:
        print(f"  config.ini not found in {out_dir}")

    # Save .dot and .pdf if they exist
    for ext in ["dot", "pdf"]:
        src = os.path.join(out_dir, f"config.{ext}")
        dst = os.path.join(RESULTS_DIR, f"config_L1_{size}.{ext}")
        if os.path.exists(src):
            shutil.copy(src, dst)
            print(f" Saved {ext.upper()} to {dst}")

    # Extract stats
    stats_path = os.path.join(out_dir, "stats.txt")
    stats = extract_stats(stats_path)

    # Append results to CSV
    with open(csv_file, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            size,
            stats.get("sim_seconds", ""),
            stats.get("ipc", ""),
            stats.get("cpi", ""),
            stats.get("num_cycles", ""),
            stats.get("dcache_misses", ""),
            stats.get("dcache_accesses", "")
        ])

print("\nSimulations completed.")
print(f"Results saved to: {csv_file}")
print(f"All m5out directories stored in: {M5OUT_ROOT}")
