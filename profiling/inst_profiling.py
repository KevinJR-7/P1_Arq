#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import csv

# ------------------ Config de rutas ------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATS_DIR = os.path.join(BASE_DIR, "stats")
OUTPUT_CSV = os.path.join(STATS_DIR, "instruction_fu_profile.csv")

os.makedirs(STATS_DIR, exist_ok=True)

# ------------------ Parser de instrucciones ------------------

def parse_committed_opclasses(stats_file):
    """
    Devuelve:
      - opcounts: diccionario (opclass -> count) de committedInstType_0
      - total_committed: total de instrucciones comprometidas
      - committed_branches: número de branches comprometidas
    """
    opcounts = {}
    total_committed = 0
    committed_branches = 0

    if not os.path.exists(stats_file):
        return opcounts, total_committed, committed_branches

    with open(stats_file, "r", encoding="utf-8", errors="ignore") as f:
        for raw in f:
            line = raw.strip()

            # --- Total de instrucciones class---
            if line.startswith("system.cpu.commit.committedInstType_0::total"):
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        total_committed = int(parts[1])
                    except ValueError:
                        continue
                continue

            # --- Clases de instrucciones ---
            if line.startswith("system.cpu.commit.committedInstType_0::"):
                parts = line.split()
                if len(parts) >= 2:
                    key = parts[0].split("::")[1]
                    try:
                        val = int(parts[1])
                        opcounts[key] = opcounts.get(key, 0) + val
                    except ValueError:
                        continue
                continue

            # --- Branches comprometidas ---
            if line.startswith("system.cpu.branchPred.committed_"):
                parts = line.split()
                if len(parts) >= 2 and parts[0].endswith("::total"):
                    try:
                        committed_branches += int(parts[1])
                    except ValueError:
                        continue
                continue

    # Sumar branches al total de Instrucciones
    total_committed += committed_branches

    return opcounts, total_committed, committed_branches


# ------------------ Parser de FU busy ------------------

FLOAT_SCALAR = {
    "FloatAdd", "FloatCmp", "FloatCvt", "FloatMult", "FloatMultAcc",
    "FloatDiv", "FloatMisc", "FloatSqrt"
}

def parse_fu_busy(stats_file):
    """
    Devuelve un diccionario con el conteo de 'statFuBusy' agrupado por categorías:
    Load, Store, ALUint, ALUfloat, Others
    """
    fu_counts = {}
    total_fu_busy = 0

    if not os.path.exists(stats_file):
        return fu_counts, total_fu_busy

    with open(stats_file, "r", encoding="utf-8", errors="ignore") as f:
        for raw in f:
            line = raw.strip()

            if line.startswith("system.cpu.statFuBusy::"):
                parts = line.split()
                if len(parts) < 2:
                    continue
                key = parts[0].split("::")[1]
                try:
                    val = int(parts[1])
                except ValueError:
                    continue
                fu_counts[key] = fu_counts.get(key, 0) + val
                total_fu_busy += val

    return fu_counts, total_fu_busy


def aggregate_fu_categories(fu_counts, total_fu_busy):
    """
    Agrupa las métricas FU busy en categorías principales.
    """
    def get(op):
        return fu_counts.get(op, 0)

    branch_cnt = 0  # Las FU busy no incluyen branches
    load_cnt = get("MemRead") + get("FloatMemRead")
    store_cnt = get("MemWrite") + get("FloatMemWrite")
    aluint_cnt = get("IntAlu") + get("IntMult") + get("IntDiv")
    alufloat_cnt = sum(get(op) for op in FLOAT_SCALAR)

    known_sum = load_cnt + store_cnt + aluint_cnt + alufloat_cnt
    others_cnt = max(total_fu_busy - known_sum, 0)

    def pct(x):
        return (100.0 * x / total_fu_busy) if total_fu_busy > 0 else 0.0

    return {
        "fu_total": total_fu_busy,
        "fu_load": load_cnt,     "fu_load_pct": pct(load_cnt),
        "fu_store": store_cnt,   "fu_store_pct": pct(store_cnt),
        "fu_aluint": aluint_cnt, "fu_aluint_pct": pct(aluint_cnt),
        "fu_alufloat": alufloat_cnt, "fu_alufloat_pct": pct(alufloat_cnt),
        "fu_others": others_cnt, "fu_others_pct": pct(others_cnt),
    }


# ------------------ Agregación de instrucciones ------------------

def aggregate_categories(opcounts, total_committed, committed_branches):
    """
    Calcula los conteos y porcentajes para:
    Branch, Load, Store, ALUint, ALUfloat, Others.
    (SIMD entra en Others por definición del usuario)
    """
    def get(op):
        return opcounts.get(op, 0)

    branch_cnt = committed_branches
    load_cnt = get("MemRead") + get("FloatMemRead")
    store_cnt = get("MemWrite") + get("FloatMemWrite")
    aluint_cnt = get("IntAlu") + get("IntMult") + get("IntDiv")
    alufloat_cnt = sum(get(op) for op in FLOAT_SCALAR)

    known_sum = branch_cnt + load_cnt + store_cnt + aluint_cnt + alufloat_cnt
    others_cnt = max(total_committed - known_sum, 0)

    def pct(x):
        return (100.0 * x / total_committed) if total_committed > 0 else 0.0

    return {
        "total_committed": total_committed,
        "branch_cnt": branch_cnt,     "branch_pct": pct(branch_cnt),
        "load_cnt": load_cnt,         "load_pct": pct(load_cnt),
        "store_cnt": store_cnt,       "store_pct": pct(store_cnt),
        "aluint_cnt": aluint_cnt,     "aluint_pct": pct(aluint_cnt),
        "alufloat_cnt": alufloat_cnt, "alufloat_pct": pct(alufloat_cnt),
        "others_cnt": others_cnt,     "others_pct": pct(others_cnt),
    }


# ------------------ Main ------------------

def main():
    if not os.path.isdir(STATS_DIR):
        print(f"[ERROR] No existe la carpeta: {STATS_DIR}")
        return

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "experiment",
            # --- Instrucciones ---
            "total_committed",
            "branch_cnt", "branch_pct",
            "load_cnt", "load_pct",
            "store_cnt", "store_pct",
            "aluint_cnt", "aluint_pct",
            "alufloat_cnt", "alufloat_pct",
            "others_cnt", "others_pct",
            # --- FU Busy ---
            "fu_total",
            "fu_load", "fu_load_pct",
            "fu_store", "fu_store_pct",
            "fu_aluint", "fu_aluint_pct",
            "fu_alufloat", "fu_alufloat_pct",
            "fu_others", "fu_others_pct",
        ])

        found = 0
        for root, _, files in os.walk(STATS_DIR):
            if "stats.txt" in files:
                stats_path = os.path.join(root, "stats.txt")
                exp = os.path.basename(root)

                opcounts, total_committed, committed_branches = parse_committed_opclasses(stats_path)
                if total_committed == 0:
                    print(f"[WARN] {exp}: total_committed=0 (¿stats incompleto?)")
                    continue
                instr = aggregate_categories(opcounts, total_committed, committed_branches)

                fu_counts, total_fu_busy = parse_fu_busy(stats_path)
                fu = aggregate_fu_categories(fu_counts, total_fu_busy)

                w.writerow([
                    exp,
                    # --- Instrucciones ---
                    instr["total_committed"],
                    instr["branch_cnt"], f'{instr["branch_pct"]:.2f}',
                    instr["load_cnt"], f'{instr["load_pct"]:.2f}',
                    instr["store_cnt"], f'{instr["store_pct"]:.2f}',
                    instr["aluint_cnt"], f'{instr["aluint_pct"]:.2f}',
                    instr["alufloat_cnt"], f'{instr["alufloat_pct"]:.2f}',
                    instr["others_cnt"], f'{instr["others_pct"]:.2f}',
                    # --- FU Busy ---
                    fu["fu_total"],
                    fu["fu_load"], f'{fu["fu_load_pct"]:.2f}',
                    fu["fu_store"], f'{fu["fu_store_pct"]:.2f}',
                    fu["fu_aluint"], f'{fu["fu_aluint_pct"]:.2f}',
                    fu["fu_alufloat"], f'{fu["fu_alufloat_pct"]:.2f}',
                    fu["fu_others"], f'{fu["fu_others_pct"]:.2f}',
                ])
                found += 1
                print(f"[INFO] Profiled {exp}")

    print(f"\n Perfil combinado (Instrucciones + FU Busy) guardado en: {OUTPUT_CSV}")
    if found == 0:
        print("[WARN] No se encontraron stats.txt en subcarpetas de:", STATS_DIR)


if __name__ == "__main__":
    main()
