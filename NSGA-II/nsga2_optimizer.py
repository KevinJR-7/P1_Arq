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
    def __init__(self, workspace_dir, results_log_file, archive_dir, sim_counter, counter_lock, **kwargs):  
        self.workspace_dir = workspace_dir
        self.results_log_file = results_log_file
        self.archive_dir = archive_dir  
        self.sim_counter = sim_counter
        self.counter_lock = counter_lock
        
        n_params = len(DESIGN_SPACE)
        xl, xu = get_bounds()
        
        super().__init__(
            n_var=n_params,
            n_obj=3,
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
        
        # ← pasar archive_dir al simulador
        sim = Gem5Simulator(self.workspace_dir, self.results_log_file, self.archive_dir)
        result = sim.run_simulation(config, sim_id=sim_id)
        
        metrics = result['metrics']
        
        out["F"] = [
            -metrics['ipc'],
            metrics['energy'],
            metrics['edp']
        ]


class ArchitectureOptimization(ElementwiseProblem):
    def __init__(self, workspace_dir, results_log_file, archive_dir=None, n_cores=1):
        self.workspace_dir = workspace_dir
        self.results_log_file = results_log_file
        self.archive_dir = archive_dir  
        self.n_cores = n_cores
        
        n_params = len(DESIGN_SPACE)
        xl, xu = get_bounds()
        
        super().__init__(
            n_var=n_params,
            n_obj=3,  # IPC, Energy, EDP
            n_constr=0,
            xl=xl,
            xu=xu,
            vtype=int
        )
    
    def _evaluate(self, x, out, *args, **kwargs):
        """Evalúa un individuo"""
        with self.counter_lock:
            sim_id = self.sim_counter.value
            self.sim_counter.value += 1
        
        config = decode_individual(x)
        
        
        sim = Gem5Simulator(self.workspace_dir, self.results_log_file, self.archive_dir)
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


def run_optimization(workspace_dir, results_log_file, archive_dir=None, pop_size=30, n_gen=20, n_cores=6):
    """
    Ejecuta optimización NSGA-II
    
    Args:
        workspace_dir: ruta a ~/Arquitectura_Computadores
        results_log_file: archivo CSV para resultados
        archive_dir: directorio para archivar simulaciones (opcional)
        pop_size: tamaño población
        n_gen: número generaciones
        n_cores: núcleos paralelos
    """
    # ===== CONFIGURAR PARALELIZACIÓN =====
    pool = Pool(n_cores)
    runner = StarmapParallelization(pool.starmap)
    
    # ===== CREAR CONTADOR COMPARTIDO + LOCK =====
    manager = Manager()
    sim_counter = manager.Value('i', 1)
    counter_lock = manager.Lock()
    
    # Crear problema con paralelización Y archive_dir
    problem = CacheOptimizationProblem(
        workspace_dir=workspace_dir,
        results_log_file=results_log_file,
        archive_dir=archive_dir,  
        sim_counter=sim_counter,
        counter_lock=counter_lock,
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
    if archive_dir:  # ← AÑADIR
        print(f"Archivos en: {archive_dir}")  # ← AÑADIR
    print("="*70)
    
    return res