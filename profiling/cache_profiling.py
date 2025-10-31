#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import csv

# ------------------ Config de rutas ------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATS_DIR = os.path.join(BASE_DIR, "stats")
OUTPUT_CSV = os.path.join(STATS_DIR, "cache_profile.csv")

os.makedirs(STATS_DIR, exist_ok=True)

# ------------------ Función de parsing ------------------

def parse_cache_stats(stats_file):
    """
    Extrae estadísticas de iCache, dCache, L2 y L3 desde un stats.txt de gem5.
    Retorna un diccionario con accesses, misses, miss% y hit%.
    """
    stats = {
        "icache": {"accesses": 0, "misses": 0},
        "dcache": {"accesses": 0, "misses": 0},
        "l2": {"accesses": 0, "misses": 0},
        "l3": {"accesses": 0, "misses": 0},
    }

    if not os.path.exists(stats_file):
        return stats

    with open(stats_file, "r", encoding="utf-8", errors="ignore") as f:
        for raw in f:
            line = raw.strip()

            # === iCache ===
            if "system.cpu.icache.demandAccesses::total" in line:
                stats["icache"]["accesses"] = int(line.split()[1])
            elif "system.cpu.icache.demandMisses::total" in line:
                stats["icache"]["misses"] = int(line.split()[1])

            # === dCache ===
            elif "system.cpu.dcache.demandAccesses::total" in line:
                stats["dcache"]["accesses"] = int(line.split()[1])
            elif "system.cpu.dcache.demandMisses::total" in line:
                stats["dcache"]["misses"] = int(line.split()[1])

            # === L2 ===
            elif "system.cpu.l2cache.overallAccesses::total" in line:
                stats["l2"]["accesses"] = int(line.split()[1])
            elif "system.cpu.l2cache.overallMisses::total" in line:
                stats["l2"]["misses"] = int(line.split()[1])

            # === L3 ===
            elif "system.l3cache.overallAccesses::total" in line:
                stats["l3"]["accesses"] = int(line.split()[1])
            elif "system.l3cache.overallMisses::total" in line:
                stats["l3"]["misses"] = int(line.split()[1])

    # Calcular porcentajes
    for level in stats:
        acc = stats[level]["accesses"]
        miss = stats[level]["misses"]
        if acc > 0:
            miss_pct = 100.0 * miss / acc
            hit_pct = 100.0 - miss_pct
        else:
            miss_pct = 0.0
            hit_pct = 0.0
        stats[level]["miss_pct"] = miss_pct
        stats[level]["hit_pct"] = hit_pct

    return stats


# ------------------ Main ------------------

def main():
    if not os.path.isdir(STATS_DIR):
        print(f"[ERROR] No existe la carpeta: {STATS_DIR}")
        return

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "experiment",
            # iCache
            "icache_accesses", "icache_misses", "icache_miss_pct", "icache_hit_pct",
            # dCache
            "dcache_accesses", "dcache_misses", "dcache_miss_pct", "dcache_hit_pct",
            # L2
            "l2_accesses", "l2_misses", "l2_miss_pct", "l2_hit_pct",
            # L3
            "l3_accesses", "l3_misses", "l3_miss_pct", "l3_hit_pct"
        ])

        found = 0
        for root, _, files in os.walk(STATS_DIR):
            if "stats.txt" in files:
                stats_path = os.path.join(root, "stats.txt")
                exp = os.path.basename(root)

                cache_data = parse_cache_stats(stats_path)

                writer.writerow([
                    exp,
                    # iCache
                    cache_data["icache"]["accesses"],
                    cache_data["icache"]["misses"],
                    f'{cache_data["icache"]["miss_pct"]:.3f}',
                    f'{cache_data["icache"]["hit_pct"]:.3f}',
                    # dCache
                    cache_data["dcache"]["accesses"],
                    cache_data["dcache"]["misses"],
                    f'{cache_data["dcache"]["miss_pct"]:.3f}',
                    f'{cache_data["dcache"]["hit_pct"]:.3f}',
                    # L2
                    cache_data["l2"]["accesses"],
                    cache_data["l2"]["misses"],
                    f'{cache_data["l2"]["miss_pct"]:.3f}',
                    f'{cache_data["l2"]["hit_pct"]:.3f}',
                    # L3
                    cache_data["l3"]["accesses"],
                    cache_data["l3"]["misses"],
                    f'{cache_data["l3"]["miss_pct"]:.3f}',
                    f'{cache_data["l3"]["hit_pct"]:.3f}'
                ])
                found += 1
                print(f"[INFO] Profiled {exp}")

    print(f"\n Perfil de cachés guardado en: {OUTPUT_CSV}")
    if found == 0:
        print("[WARN] No se encontraron stats.txt en subcarpetas de:", STATS_DIR)


if __name__ == "__main__":
    main()
