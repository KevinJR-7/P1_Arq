"""
Módulo para ejecutar simulaciones gem5 + McPAT y parsear métricas
Calcula: IPC, Energy, EDP (Energy-Delay Product)
"""
import subprocess
import tempfile
import os
import re
import json
from pathlib import Path
from multiprocessing import Pool
import time


class Gem5Simulator:
    def __init__(self, workspace_dir, results_log_file=None):
        """
        Args:
            workspace_dir: ruta a ~/Arquitectura_Computadores
            results_log_file: archivo CSV para guardar resultados (opcional)
        """
        self.workspace_dir = Path(workspace_dir)
        self.results_log_file = results_log_file
        
        self.gem5_binary = self.workspace_dir / "gem5/build/ARM/gem5.fast"
        self.config_script = self.workspace_dir / "gem5/scripts/CortexA76_scripts_gem5/CortexA76.py"
        self.workload_binary = self.workspace_dir / "gem5/workloads/mp3_enc/mp3_enc"
        self.workload_input = self.workspace_dir / "gem5/workloads/mp3_enc/mp3enc_testfile.wav"
        
        # McPAT paths
        self.mcpat_script = self.workspace_dir / "gem5/scripts/McPAT/gem5toMcPAT_cortexA76.py"
        self.mcpat_template = self.workspace_dir / "gem5/scripts/McPAT/ARM_A76_2.1GHz.xml"
        self.mcpat_bin = self.workspace_dir / "gem5/mcpat/mcpat"
        
        # Verificar que existen
        assert self.gem5_binary.exists(), f"gem5 no encontrado en {self.gem5_binary}"
        assert self.config_script.exists(), f"Script no encontrado en {self.config_script}"
        assert self.workload_binary.exists(), f"Workload no encontrado en {self.workload_binary}"
        assert self.workload_input.exists(), f"Input no encontrado en {self.workload_input}"
        assert self.mcpat_script.exists(), f"McPAT script no encontrado en {self.mcpat_script}"
        assert self.mcpat_template.exists(), f"McPAT template no encontrado en {self.mcpat_template}"
        assert self.mcpat_bin.exists(), f"McPAT binary no encontrado en {self.mcpat_bin}"
        
        # Crear header del CSV si el archivo no existe
        if self.results_log_file and not Path(self.results_log_file).exists():
            self._create_csv_header()
    
    def _create_csv_header(self):
        """Crea el header del CSV con todos los parámetros y métricas"""
        header = [
            "sim_id",
            "timestamp",
            # Parámetros de diseño (12 columnas) ← AÑADIDOS num_fu_read y num_fu_write
            "L1I_size", "L1I_assoc",
            "L1D_size", "L1D_assoc",
            "L2_size", "L2_assoc",
            "L3_size", "L3_assoc",
            "load_queue", "store_queue",
            "num_fu_read", "num_fu_write",  # ← AÑADIDO
            # Métricas (9 columnas)
            "ipc", "cpi", "energy", "edp",
            "runtime_power", "leakage_power", "total_power",
            "sim_seconds", "sim_ticks"
        ]
        
        with open(self.results_log_file, 'w') as f:
            f.write(",".join(header) + "\n")
    
    def run_simulation(self, config, sim_id):
        """
        Ejecuta una simulación gem5 + McPAT
        
        Args:
            config: dict con parámetros de diseño
                   {"L1I_size": "64kB", "L1I_assoc": 4, ...}
            sim_id: identificador único de la simulación
        
        Returns:
            dict: {
                "config": config original,
                "metrics": {
                    "ipc": float,
                    "cpi": float,
                    "energy": float,
                    "edp": float,
                    ...
                }
            }
        """
        # Crear directorio temporal en /dev/shm (RAM disk, ultra rápido)
        tmpdir = f"/dev/shm/sim_{sim_id:04d}"
        os.makedirs(tmpdir, exist_ok=True)
        
        try:
            # ===== PASO 1: Ejecutar gem5 =====
            cmd = self._build_gem5_command(config, tmpdir)
            
            print(f"[Sim {sim_id}] Running... ", end="", flush=True)
            result = subprocess.run(
                cmd,
                cwd=str(self.workspace_dir / "gem5"),
                capture_output=True,
                text=True,
                timeout=1800  # 30 minutos máximo
            )
            
            if result.returncode != 0:
                print(f"FAILED")
                metrics = self._get_invalid_metrics()
                self._log_result(sim_id, config, metrics)
                return {"config": config, "metrics": metrics}
            
            # Verificar archivos generados
            stats_file = Path(tmpdir) / "stats.txt"
            config_json = Path(tmpdir) / "config.json"
            
            if not stats_file.exists():
                print(f"FAILED (no stats)")
                metrics = self._get_invalid_metrics()
                self._log_result(sim_id, config, metrics)
                return {"config": config, "metrics": metrics}
            
            # Parsear stats.txt (CPI, sim_seconds, etc.)
            gem5_metrics = self._parse_gem5_stats(stats_file)
            
            # ===== PASO 2: Ejecutar McPAT =====
            mcpat_metrics = self._run_mcpat(tmpdir, stats_file, config_json)
            
            # ===== PASO 3: Calcular métricas finales =====
            metrics = self._calculate_final_metrics(gem5_metrics, mcpat_metrics)
            
            # ===== PASO 4: Guardar resultado en CSV =====
            self._log_result(sim_id, config, metrics)
            
            print(f"OK - IPC={metrics['ipc']:.4f} Energy={metrics['energy']:.4f}J EDP={metrics['edp']:.6f}")
            
            return {"config": config, "metrics": metrics}
        
        except subprocess.TimeoutExpired:
            print(f"TIMEOUT")
            metrics = self._get_invalid_metrics()
            self._log_result(sim_id, config, metrics)
            return {"config": config, "metrics": metrics}
        
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
            metrics = self._get_invalid_metrics()
            self._log_result(sim_id, config, metrics)
            return {"config": config, "metrics": metrics}
        
        finally:
            # Limpiar directorio temporal
            if os.path.exists(tmpdir):
                import shutil
                shutil.rmtree(tmpdir)
    
    def _log_result(self, sim_id, config, metrics):
        """
        Guarda resultado en CSV
        
        Formato: sim_id, timestamp, config_params..., metrics...
        """
        if not self.results_log_file:
            return
        
        import datetime
        
        row = [
            str(sim_id),
            datetime.datetime.now().isoformat(),
            # Parámetros de diseño (12 valores) ← AÑADIDOS num_fu_read y num_fu_write
            config["L1I_size"], str(config["L1I_assoc"]),
            config["L1D_size"], str(config["L1D_assoc"]),
            config["L2_size"], str(config["L2_assoc"]),
            config["L3_size"], str(config["L3_assoc"]),
            str(config["load_queue"]), str(config["store_queue"]),
            str(config["num_fu_read"]), str(config["num_fu_write"]),  # ← AÑADIDO
            # Métricas
            f"{metrics['ipc']:.6f}", f"{metrics['cpi']:.6f}",
            f"{metrics['energy']:.6f}", f"{metrics['edp']:.10f}",
            f"{metrics['runtime_power']:.6f}", f"{metrics['leakage_power']:.6f}",
            f"{metrics['total_power']:.6f}",
            f"{metrics['sim_seconds']:.6f}", str(metrics['sim_ticks'])
        ]
        
        # Escribir en CSV (thread-safe para multiprocessing)
        with open(self.results_log_file, 'a') as f:
            f.write(",".join(row) + "\n")
    
    def _build_gem5_command(self, config, outdir):
        """Construye el comando gem5 con los parámetros"""
        output_mp3 = f"/tmp/out_{os.getpid()}_{config['L1D_size']}_{config['L2_size']}.mp3"
        
        cmd = [
            str(self.gem5_binary),
            f"--outdir={outdir}",
            str(self.config_script),
            "--cmd", str(self.workload_binary),
            "--options", f"{self.workload_input} {output_mp3}",
            
            # Parámetros de caché
            "--l1i_size", config["L1I_size"],
            "--l1i_assoc", str(config["L1I_assoc"]),
            "--l1d_size", config["L1D_size"],
            "--l1d_assoc", str(config["L1D_assoc"]),
            "--l2_size", config["L2_size"],
            "--l2_assoc", str(config["L2_assoc"]),
            "--l3_size", config["L3_size"],
            "--l3_assoc", str(config["L3_assoc"]),
            
            # Parámetros de queues
            "--lq_entries", str(config["load_queue"]),
            "--sq_entries", str(config["store_queue"]),
            
            # Functional Units (puertos de cache) ← AÑADIDO
            "--num_fu_read", str(config["num_fu_read"]),
            "--num_fu_write", str(config["num_fu_write"]),
        ]
        
        return cmd
    
    def _parse_gem5_stats(self, stats_file):
        """
        Parsea stats.txt de gem5
        
        Returns:
            dict: {"cpi": float, "ipc": float, "sim_seconds": float, "sim_ticks": int}
        """
        metrics = {
            "cpi": None,
            "ipc": None,
            "sim_seconds": None,
            "sim_ticks": None,
        }
        
        with open(stats_file, 'r') as f:
            content = f.read()
        
        # Buscar CPI (system.cpu.cpi)
        match = re.search(r'system\.cpu\.cpi\s+(\d+\.\d+)', content)
        if match:
            metrics["cpi"] = float(match.group(1))
            metrics["ipc"] = 1.0 / metrics["cpi"] if metrics["cpi"] > 0 else 0.0
        
        # Buscar sim_seconds
        match = re.search(r'simSeconds\s+(\d+\.\d+)', content)
        if match:
            metrics["sim_seconds"] = float(match.group(1))
        
        # Buscar sim_ticks
        match = re.search(r'simTicks\s+(\d+)', content)
        if match:
            metrics["sim_ticks"] = int(match.group(1))
        
        # Verificar que se encontró CPI
        if metrics["cpi"] is None:
            metrics["cpi"] = float('inf')
            metrics["ipc"] = 0.0
        
        return metrics
    
    def _run_mcpat(self, tmpdir, stats_file, config_json):
        """
        Ejecuta McPAT y parsea salida
        
        Returns:
            dict: {"runtime_dynamic": float, "total_leakage": float} en Watts
        """
        mcpat_config_xml = Path(tmpdir) / "config.xml"
        mcpat_output = Path(tmpdir) / "salida_mcpat.txt"
        
        try:
            # Generar config.xml para McPAT
            subprocess.run([
                "python3", str(self.mcpat_script),
                str(stats_file),
                str(config_json),
                str(self.mcpat_template)
            ], cwd=tmpdir, check=True, capture_output=True, timeout=60)
            
            # Ejecutar McPAT
            with open(mcpat_output, "w") as mf:
                subprocess.run([
                    str(self.mcpat_bin),
                    "-infile", str(mcpat_config_xml),
                    "-print_level", "1"
                ], cwd=tmpdir, stdout=mf, check=True, timeout=60)
            
            # Parsear salida de McPAT
            return self._parse_mcpat_output(mcpat_output)
        
        except subprocess.TimeoutExpired:
            return {"runtime_dynamic": 0.0, "total_leakage": 0.0}
        except Exception as e:
            return {"runtime_dynamic": 0.0, "total_leakage": 0.0}
    
    def _parse_mcpat_output(self, mcpat_output):
        """
        Parsea salida_mcpat.txt
        
        Busca:
          Runtime Dynamic = X W
          Total Leakage = Y W
        
        Returns:
            dict: {"runtime_dynamic": float, "total_leakage": float}
        """
        metrics = {
            "runtime_dynamic": 0.0,
            "total_leakage": 0.0
        }
        
        with open(mcpat_output, 'r') as f:
            content = f.read()
        
        # Buscar "Runtime Dynamic = X W"
        match = re.search(r'Runtime Dynamic\s*=\s*(\d+\.?\d*)\s*W', content)
        if match:
            metrics["runtime_dynamic"] = float(match.group(1))
        
        # Buscar "Total Leakage = Y W"
        match = re.search(r'Total Leakage\s*=\s*(\d+\.?\d*)\s*W', content)
        if match:
            metrics["total_leakage"] = float(match.group(1))
        
        return metrics
    
    def _calculate_final_metrics(self, gem5_metrics, mcpat_metrics):
        """
        Calcula métricas finales combinando gem5 y McPAT
        
        Fórmulas (CORRECCIÓN según especificación):
          Energy (J) = (Runtime Dynamic + Total Leakage) × CPI
          EDP = Energy × CPI
        
        Returns:
            dict con todas las métricas
        """
        cpi = gem5_metrics["cpi"]
        ipc = gem5_metrics["ipc"]
        sim_seconds = gem5_metrics["sim_seconds"] or 0.0
        
        runtime_power = mcpat_metrics["runtime_dynamic"]  # Watts
        leakage_power = mcpat_metrics["total_leakage"]    # Watts
        
        # Total power
        total_power = runtime_power + leakage_power  # W
        
        # Energy = Power × CPI (según tu especificación)
        energy = total_power * cpi  # J
        
        # EDP = Energy × CPI
        edp = energy * cpi  # J·cycles
        
        return {
            "ipc": ipc,
            "cpi": cpi,
            "energy": energy,
            "edp": edp,
            "runtime_power": runtime_power,
            "leakage_power": leakage_power,
            "total_power": total_power,
            "sim_seconds": sim_seconds,
            "sim_ticks": gem5_metrics["sim_ticks"]
        }
    
    def _get_invalid_metrics(self):
        """Retorna métricas inválidas para configuraciones que fallan"""
        return {
            "ipc": 0.0,
            "cpi": float('inf'),
            "energy": float('inf'),
            "edp": float('inf'),
            "runtime_power": 0.0,
            "leakage_power": 0.0,
            "total_power": 0.0,
            "sim_seconds": 0.0,
            "sim_ticks": 0
        }


# ===== FUNCIÓN WRAPPER PARA PARALELIZACIÓN =====
def run_single_simulation(args):
    """
    Wrapper para ejecutar una simulación (necesario para multiprocessing.Pool)
    
    Args:
        args: tupla (workspace_dir, config, sim_id, name, results_log_file)
    
    Returns:
        tupla (name, result, elapsed_time)
    """
    workspace_dir, config, sim_id, name, results_log_file = args
    
    # Crear simulador (cada proceso necesita su propia instancia)
    sim = Gem5Simulator(workspace_dir, results_log_file)
    
    # Ejecutar simulación con timer
    start = time.time()
    result = sim.run_simulation(config, sim_id)
    elapsed = time.time() - start
    
    return (name, result, elapsed)