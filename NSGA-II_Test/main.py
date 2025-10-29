"""
Script principal para ejecutar optimización NSGA-II
"""
import os
from nsga2_optimizer import run_optimization

WORKSPACE = os.path.expanduser("~/Arquitectura_Computadores")
RESULTS_LOG = os.path.join(WORKSPACE, "P1_Arq/NSGA-II_Test/nsga2_results.csv")

# Configuración de optimización
N_CORES = 2         # ← AQUÍ defines cuántos núcleos usar
POP_SIZE = 3       # 40 individuos por generación
N_GEN = 1           # 25 generaciones


if __name__ == "__main__":
    print(f"Configuración:")
    print(f"  Núcleos: {N_CORES}")
    print(f"  Población: {POP_SIZE}")
    print(f"  Generaciones: {N_GEN}")
    print(f"  Total evaluaciones: {POP_SIZE * (1 + N_GEN)}")
    print(f"  Resultados: {RESULTS_LOG}\n")
    
    res = run_optimization(
        workspace_dir=WORKSPACE,
        results_log_file=RESULTS_LOG,
        pop_size=POP_SIZE,
        n_gen=N_GEN,
        n_cores=N_CORES  # ← Pasar núcleos al optimizador
    )
    
    print("\n✅ Optimización completada!")
    print(f"Ejecuta: python3 analyze_results.py")