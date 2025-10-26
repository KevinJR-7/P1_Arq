BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATS_DIR = os.path.join(BASE_DIR, "results")

# === CSV OUTPUT FILE ===
csv_file = os.path.join(STATS_DIR, "results_L1_experiment.csv")

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