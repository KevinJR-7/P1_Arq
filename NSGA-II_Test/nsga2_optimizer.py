"""
Optimización multi-objetivo con NSGA-II
"""
import numpy as np
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.core.problem import ElementwiseProblem
from pymoo.optimize import minimize
from pymoo.operators.sampling.rnd import IntegerRandomSampling
from pymoo.operators.crossover.sbx import SBX
from pymoo.operators.mutation.pm import PM
from multiprocessing.pool import Pool
from pymoo.core.problem import StarmapParallelization
from multiprocessing import Manager, Lock

from design_space import DESIGN_SPACE, decode_individual, get_bounds
from simulator import Gem5Simulator


class CacheOptimizationProblem(ElementwiseProblem):
    def __init__(self, workspace_dir, results_log_file, sim_counter, counter_lock, **kwargs):
        self.workspace_dir = workspace_dir
        self.results_log_file = results_log_file
        self.sim_counter = sim_counter  # ← Contador compartido
        self.counter_lock = counter_lock  # ← Lock compartido
        
        n_params = len(DESIGN_SPACE)
        xl, xu = get_bounds()
        
        super().__init__(
            n_var=n_params,
            n_obj=3,  # IPC, Energy, EDP
            n_constr=0,
            xl=xl,
            xu=xu,
            vtype=int,
            **kwargs
        )
    
    def _evaluate(self, x, out, *args, **kwargs):
        """Evalúa un individuo ejecutando gem5+McPAT"""
        # Incrementar contador de forma thread-safe
        with self.counter_lock:
            sim_id = self.sim_counter.value
            self.sim_counter.value += 1
        
        config = decode_individual(x)
        
        sim = Gem5Simulator(self.workspace_dir, self.results_log_file)
        result = sim.run_simulation(config, sim_id=sim_id)
        
        metrics = result['metrics']
        
        # NSGA-II minimiza, así que:
        # - IPC: maximizar → minimizar su negativo
        # - Energy: minimizar
        # - EDP: minimizar
        out["F"] = [
            -metrics['ipc'],   # Minimizar negativo = maximizar IPC
            metrics['energy'],
            metrics['edp']
        ]


def run_optimization(workspace_dir, results_log_file, pop_size=12, n_gen=5, n_cores=6):
    """
    Ejecuta optimización NSGA-II con paralelización
    
    Args:
        workspace_dir: ruta a workspace
        results_log_file: archivo CSV para logs
        pop_size: tamaño de población
        n_gen: número de generaciones
        n_cores: núcleos paralelos a usar
    
    Returns:
        res: resultado de pymoo con frontera Pareto
    """
    print("="*70)
    print("NSGA-II OPTIMIZATION")
    print("="*70)
    print(f"Cores paralelos: {n_cores}")
    print(f"Población: {pop_size}")
    print(f"Generaciones: {n_gen}")
    print(f"Total evaluaciones: {pop_size * (1 + n_gen)}")
    print(f"Design space: {len(DESIGN_SPACE)} parámetros")
    
    # Mostrar solo parámetros variables
    print("\nParámetros variables:")
    for param, values in DESIGN_SPACE.items():
        if len(values) > 1:
            print(f"  {param}: {values}")
    print("="*70)
    
    # ===== CONFIGURAR PARALELIZACIÓN =====
    pool = Pool(n_cores)
    runner = StarmapParallelization(pool.starmap)
    
    # ===== CREAR CONTADOR COMPARTIDO + LOCK =====
    manager = Manager()
    sim_counter = manager.Value('i', 1)  # Contador compartido (empieza en 1)
    counter_lock = manager.Lock()        # Lock para sincronización
    
    # Crear problema con paralelización
    problem = CacheOptimizationProblem(
        workspace_dir=workspace_dir,
        results_log_file=results_log_file,
        sim_counter=sim_counter,
        counter_lock=counter_lock,  # ← Pasar lock
        elementwise_runner=runner
    )
    
    # Configurar algoritmo NSGA-II
    algorithm = NSGA2(
        pop_size=pop_size,
        sampling=IntegerRandomSampling(),
        crossover=SBX(prob=0.9, eta=10),
        mutation=PM(eta=15),
        eliminate_duplicates=True
    )
    
    # Ejecutar optimización
    print("\nIniciando NSGA-II...\n")
    
    res = minimize(
        problem,
        algorithm,
        ('n_gen', n_gen),
        seed=42,
        verbose=True
    )
    
    # Cerrar pool
    pool.close()
    pool.join()
    
    print("\n" + "="*70)
    print("OPTIMIZACIÓN COMPLETADA")
    print("="*70)
    print(f"Tamaño frente Pareto: {len(res.F)}")
    print(f"Resultados en: {results_log_file}")
    print("="*70)
    
    return res