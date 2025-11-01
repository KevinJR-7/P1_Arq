import os
import csv

# === BASE DIRECTORIES ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(BASE_DIR, "results")
STATS_DIR = os.path.join(BASE_DIR, "stats")

# === ENSURE DIRECTORIES EXIST ===
os.makedirs(STATS_DIR, exist_ok=True)

# === CSV OUTPUT FILE ===
csv_file = os.path.join(STATS_DIR, "results_profiling.csv")

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
        print(f"[WARN] Stats file not found: {stats_file}")
        return stats

    with open(stats_file, "r") as f:
        for line in f:
            line = line.strip()
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

# === CREATE RESULTS CSV FILE ===
with open(csv_file, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow([
        "experiment",
        "sim_seconds",
        "ipc",
        "cpi",
        "num_cycles",
        "dcache_misses",
        "dcache_accesses"
    ])

    # === RECURSIVELY SEARCH ALL stats.txt FILES ===
    for root, dirs, files in os.walk(STATS_DIR):
        if "stats.txt" in files:
            stats_path = os.path.join(root, "stats.txt")
            stats = extract_stats(stats_path)

            # experiment name = subfolder name
            experiment_name = os.path.basename(root)

            writer.writerow([
                experiment_name,
                stats["sim_seconds"],
                stats["ipc"],
                stats["cpi"],
                stats["num_cycles"],
                stats["dcache_misses"],
                stats["dcache_accesses"]
            ])

            print(f"[INFO] Added {experiment_name} -> {stats_path}")

print(f"\n Results saved to: {csv_file}")