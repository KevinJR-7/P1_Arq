"""
Script principal para ejecutar optimización NSGA-II
"""
import os
from nsga2_optimizer import run_optimization

WORKSPACE = os.path.expanduser("~/Arquitectura_Computadores")
RESULTS_LOG = os.path.join(WORKSPACE, "P1_Arq/NSGA-II_Test/nsga2_results.csv")

# Directorio para archivar simulaciones
ARCHIVE_DIR = os.path.join(WORKSPACE, "P1_Arq/NSGA-II_Test/simulations_archive")

# Configuración de optimización
N_CORES = 5        # Número de núcleos para paralelismo
POP_SIZE = 30       # Individuos por generación
N_GEN = 14           # Generaciones




if __name__ == "__main__":
    print(f"Configuración:")
    print(f"  Núcleos: {N_CORES}")
    print(f"  Población: {POP_SIZE}")
    print(f"  Generaciones: {N_GEN}")
    print(f"  Total evaluaciones: {POP_SIZE * (1 + N_GEN)}")
    print(f"  Tiempo estimado: ~{(POP_SIZE * (1 + N_GEN) * 10 / N_CORES / 60):.1f} horas")
    print(f"  Espacio estimado: ~{(POP_SIZE * (1 + N_GEN))} MB")  
    print(f"  Resultados: {RESULTS_LOG}")
    print(f"  Archivo: {ARCHIVE_DIR}\n")  
    
    res = run_optimization(
        workspace_dir=WORKSPACE,
        results_log_file=RESULTS_LOG,
        archive_dir=ARCHIVE_DIR,  
        pop_size=POP_SIZE,
        n_gen=N_GEN,
        n_cores=N_CORES  
    )
    
    print("\nOptimización completada!")
    print(f"Resultados en: {RESULTS_LOG}")
    print(f"Archivos en: {ARCHIVE_DIR}")