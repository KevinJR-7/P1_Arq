"""
Definición del espacio de diseño y funciones de encoding/decoding
"""

# Espacio de diseño COMPLETO (8 parámetros variables)
DESIGN_SPACE = {
    # L1 Instruction Cache
    "L1I_size": ["64kB", "128kB"],                # VARIABLE (2)
    "L1I_assoc": [4],                       # VARIABLE (3)
    
    # L1 Data Cache
    "L1D_size": ["64kB", "128kB", "512kB", "1MB"],# VARIABLE (4)
    "L1D_assoc": [2, 4, 8],                       # VARIABLE (3)

    # L2 Unified Cache
    "L2_size": ["128kB", "256kB", "512kB", "1MB"],# VARIABLE (4)
    "L2_assoc": [8, 16],                       # VARIABLE (3)
    
    # L3 Unified Cache (FIJO)
    "L3_size": ["2MB"],                           # FIJO (1)
    "L3_assoc": [16],                             # FIJO (1)
    
    # Load/Store Queues
    "load_queue": [48, 64, 72],                   # VARIABLE (3)
    "store_queue": [64, 72, 80],                  # VARIABLE (3)
    
    # Functional Units (puertos de cache)
    "num_fu_read": [2, 3, 4],                     # VARIABLE (3) 
    "num_fu_write": [1, 2],                       # VARIABLE (2) 
}

# Espacio total = 2 × 3 × 4 × 3 × 4 × 3 × 1 × 1 × 3 × 3 × 3 × 2 = 31,104 configuraciones únicas
# Con 1,040 simulaciones: 3.34% de cobertura, <1% duplicados

def decode_individual(x):
    """Convierte [0,1,2,...] a {"L1D_size": "64kB", ...}"""
    config = {}
    param_names = list(DESIGN_SPACE.keys())
    
    for i, param in enumerate(param_names):
        idx = int(x[i])
        idx = max(0, min(idx, len(DESIGN_SPACE[param]) - 1))
        config[param] = DESIGN_SPACE[param][idx]
    
    return config

def get_bounds():
    """Retorna límites (0, n_opciones-1) para cada parámetro"""
    import numpy as np
    n_params = len(DESIGN_SPACE)
    xl = np.zeros(n_params)
    xu = np.array([len(values) - 1 for values in DESIGN_SPACE.values()])
    return xl, xu