#!/usr/bin/env python3
import os
import subprocess
import shutil
import concurrent.futures

# === PATHS ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GEM5_DIR = os.path.join(BASE_DIR, "../../gem5")

gem5_bin = os.path.join(GEM5_DIR, "build/ARM/gem5.fast")
config_script = os.path.join(GEM5_DIR, "scripts/CortexA76_scripts_gem5/CortexA76.py")

# === WORKLOADS ===
# Cada workload tiene su propio comando y options exactos
WORKLOADS = {
    "h264_dec": {
        "cmd": "h264_dec",
        "options": "h264dec_testfile.264 h264dec_outfile.yuv"
    },
    "h264_enc": {
        "cmd": "h264_enc",
        "options": "h264enc_configfile.cfg"
    },
    "jpeg2k_dec": {
        "cmd": "jpg2k_dec",
        "options": "-i jpg2kdec_testfile.j2k -o jpg2kdec_outfile.bmp"
    },
    "jpeg2k_enc": {
        "cmd": "jpg2k_enc",
        "options": "-i jpg2kenc_testfile.bmp -o jpg2kenc_outfile.j2k"
    },
    "mp3_dec": {
        "cmd": "mp3_dec",
        "options": "-w mp3dec_outfile.wav mp3dec_testfile.mp3"
    },
    "mp3_enc": {
        "cmd": "mp3_enc",
        "options": "mp3enc_testfile.wav mp3enc_outfile.mp3"
    }
}

# === OUTPUT DIRECTORIES ===
RESULTS_DIR = os.path.join(BASE_DIR, "results")
STATS_DIR = os.path.join(BASE_DIR, "stats")

os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(STATS_DIR, exist_ok=True)

for wl in WORKLOADS.keys():
    os.makedirs(os.path.join(RESULTS_DIR, wl), exist_ok=True)
    os.makedirs(os.path.join(STATS_DIR, wl), exist_ok=True)

# === DEBUG: PRINT PATHS ===
print("\n=== PATHS DE EJECUCIÓN ===")
print(f"BASE_DIR: {BASE_DIR}")
print(f"GEM5_DIR: {GEM5_DIR}")
print(f"gem5_bin: {gem5_bin}")
print(f"config_script: {config_script}")
print(f"RESULTS_DIR: {RESULTS_DIR}")
print(f"STATS_DIR: {STATS_DIR}")
print("============================\n")

# === FUNCTION TO RUN ONE WORKLOAD ===
def run_workload(wl_name, wl_data):
    print(f"Ejecutando {wl_name}...")

    wl_path = os.path.join(GEM5_DIR, "workloads", wl_name)
    out_dir = os.path.join(RESULTS_DIR, wl_name)
    stats_dir = os.path.join(STATS_DIR, wl_name)

    workload_exec = os.path.join(wl_path, wl_data["cmd"])

    # Convertir todos los archivos en options a paths completos
    args = wl_data["options"].split()
    args_full = []
    for a in args:
        # Solo hacemos path absoluto si existe el archivo dentro del workload
        candidate = os.path.join(wl_path, a)
        if os.path.exists(candidate):
            args_full.append(candidate)
        else:
            args_full.append(a)

    # DEBUG: mostrar paths del workload
    print(f"[{wl_name}] Ejecutable: {workload_exec}")
    print(f"[{wl_name}] Options completos: {' '.join(args_full)}\n")

    cmd = [
        gem5_bin,
        f"--outdir={out_dir}",
        config_script,
        "--cmd", workload_exec,
        "--options", ' '.join(args_full)
    ]

    try:
        subprocess.run(cmd, check=True)
        print(f"[OK] {wl_name} completado.")
    except subprocess.CalledProcessError:
        print(f"[ERROR] Falló la simulación de {wl_name}.")
        return

    # Copiar stats.txt
    stats_src = os.path.join(out_dir, "stats.txt")
    stats_dst = os.path.join(stats_dir, "stats.txt")
    if os.path.exists(stats_src):
        shutil.copy(stats_src, stats_dst)
    else:
        print(f"No se encontró stats.txt para {wl_name}")

    # Crear archivo de información
    info_file = os.path.join(stats_dir, "workload_info.txt")
    with open(info_file, "w") as f:
        f.write(f"Este archivo pertenece al workload {wl_name}\n")

# === MAIN ===
if __name__ == "__main__":
    MAX_WORKERS = min(2, os.cpu_count())  # máximo 3 simulaciones paralelas

    with concurrent.futures.ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [
            executor.submit(run_workload, wl_name, wl_data)
            for wl_name, wl_data in WORKLOADS.items()
        ]
        for future in concurrent.futures.as_completed(futures):
            future.result()

    print("\nTodas las simulaciones han terminado.")
    print(f"Resultados completos: {RESULTS_DIR}")
    print(f"Stats organizadas en: {STATS_DIR}")
