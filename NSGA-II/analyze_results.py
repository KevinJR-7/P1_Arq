"""
Análisis simplificado de resultados NSGA-II
Genera solo las gráficas esenciales para el informe
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import os

# Configuración
plt.rcParams['font.size'] = 11
plt.rcParams['figure.dpi'] = 300
sns.set_style("whitegrid")

# Crear carpeta Img si no existe
os.makedirs('Img', exist_ok=True)

print("="*70)
print("ANÁLISIS DE RESULTADOS NSGA-II")
print("="*70)

# ===== CARGAR DATOS =====
df = pd.read_csv("nsga2_results.csv")
df_valid = df[df['ipc'] > 0].copy()

print(f"\nSimulaciones totales: {len(df)}")
print(f"Simulaciones válidas: {len(df_valid)}")

# ===== IDENTIFICAR FRONTERA DE PARETO =====
print("\n" + "="*70)
print("IDENTIFICANDO FRONTERA DE PARETO")
print("="*70)

def find_pareto_front(df):
    """
    Encuentra frontera de Pareto:
    - Maximizar IPC
    - Minimizar Energy
    - Minimizar EDP
    """
    is_pareto = np.ones(len(df), dtype=bool)
    
    for i in range(len(df)):
        if is_pareto[i]:
            for j in range(len(df)):
                if i != j and is_pareto[j]:
                    # j domina a i si es mejor o igual en todo y estrictamente mejor en algo
                    ipc_better = df.iloc[j]['ipc'] >= df.iloc[i]['ipc']
                    energy_better = df.iloc[j]['energy'] <= df.iloc[i]['energy']
                    edp_better = df.iloc[j]['edp'] <= df.iloc[i]['edp']
                    
                    strictly_better = (
                        df.iloc[j]['ipc'] > df.iloc[i]['ipc'] or
                        df.iloc[j]['energy'] < df.iloc[i]['energy'] or
                        df.iloc[j]['edp'] < df.iloc[i]['edp']
                    )
                    
                    if ipc_better and energy_better and edp_better and strictly_better:
                        is_pareto[i] = False
                        break
    
    return is_pareto

pareto_mask = find_pareto_front(df_valid)
pareto = df_valid[pareto_mask].copy()
dominated = df_valid[~pareto_mask].copy()

print(f"Configuraciones en frontera de Pareto: {len(pareto)}")
print(f"Configuraciones dominadas: {len(dominated)}")

# Guardar configuraciones Pareto
pareto.to_csv('pareto_configurations.csv', index=False)
print("✅ Guardadas configuraciones Pareto en pareto_configurations.csv")

# ===== ESTADÍSTICAS =====
print("\n" + "="*70)
print("ESTADÍSTICAS DE LA FRONTERA DE PARETO")
print("="*70)

print(f"\nRangos:")
print(f"  IPC:    [{pareto['ipc'].min():.4f}, {pareto['ipc'].max():.4f}]")
print(f"  Energy: [{pareto['energy'].min():.4f}, {pareto['energy'].max():.4f}] J")
print(f"  EDP:    [{pareto['edp'].min():.4f}, {pareto['edp'].max():.4f}]")

# Encontrar mejores individuales
best_ipc_idx = pareto['ipc'].idxmax()
best_energy_idx = pareto['energy'].idxmin()
best_edp_idx = pareto['edp'].idxmin()

print(f"\nMejor IPC:")
print(f"   Simulación: {best_ipc_idx}")
print(f"   IPC:    {pareto.loc[best_ipc_idx, 'ipc']:.4f}")
print(f"   Energy: {pareto.loc[best_ipc_idx, 'energy']:.4f} J")
print(f"   EDP:    {pareto.loc[best_ipc_idx, 'edp']:.4f}")

print(f"\nMejor Energy:")
print(f"   Simulación: {best_energy_idx}")
print(f"   IPC:    {pareto.loc[best_energy_idx, 'ipc']:.4f}")
print(f"   Energy: {pareto.loc[best_energy_idx, 'energy']:.4f} J")
print(f"   EDP:    {pareto.loc[best_energy_idx, 'edp']:.4f}")

print(f"\nMejor EDP (RECOMENDADO - Mejor trade-off):")
print(f"   Simulación: {best_edp_idx}")
print(f"   IPC:    {pareto.loc[best_edp_idx, 'ipc']:.4f}")
print(f"   Energy: {pareto.loc[best_edp_idx, 'energy']:.4f} J")
print(f"   EDP:    {pareto.loc[best_edp_idx, 'edp']:.4f}")

# Mostrar configuración del mejor EDP
print(f"\n📋 Configuración del mejor trade-off (EDP):")
best_config = pareto.loc[best_edp_idx]
params = ['L1I_size', 'L1D_size', 'L2_size', 'L1I_assoc', 'L1D_assoc', 
          'L2_assoc', 'load_queue', 'store_queue', 'num_fu_read', 'num_fu_write']
for param in params:
    if param in best_config:
        print(f"   {param:15s}: {best_config[param]}")

# ===== GRÁFICAS =====
print("\n" + "="*70)
print("GENERANDO GRÁFICAS")
print("="*70)

# ===== 1. IPC vs ENERGY =====
plt.figure(figsize=(10, 7))
plt.scatter(dominated['ipc'], dominated['energy'], 
           alpha=0.4, s=50, c='lightgray', edgecolors='gray', 
           linewidth=0.5, label='Dominadas')
plt.scatter(pareto['ipc'], pareto['energy'], 
           s=150, c='red', edgecolors='black', linewidth=2, 
           label='Frontera de Pareto', zorder=10)

# Marcar mejor trade-off (EDP)
plt.scatter(best_config['ipc'], best_config['energy'],
           s=400, c='gold', marker='*', edgecolors='black', 
           linewidth=2.5, label=f'Mejor EDP (sim #{best_edp_idx})', zorder=15)

plt.xlabel('IPC', fontsize=14, fontweight='bold')
plt.ylabel('Energy (J)', fontsize=14, fontweight='bold')
plt.title('Trade-off: IPC vs Energy', fontsize=16, fontweight='bold')
plt.legend(fontsize=11, loc='best')
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig('Img/ipc_vs_energy.png', bbox_inches='tight')
print("Img/ipc_vs_energy.png")
plt.close()

# ===== 2. IPC vs EDP =====
plt.figure(figsize=(10, 7))
plt.scatter(dominated['ipc'], dominated['edp'], 
           alpha=0.4, s=50, c='lightgray', edgecolors='gray', 
           linewidth=0.5, label='Dominadas')
plt.scatter(pareto['ipc'], pareto['edp'], 
           s=150, c='red', edgecolors='black', linewidth=2, 
           label='Frontera de Pareto', zorder=10)
plt.scatter(best_config['ipc'], best_config['edp'],
           s=400, c='gold', marker='*', edgecolors='black', 
           linewidth=2.5, label=f'Mejor EDP (sim #{best_edp_idx})', zorder=15)

plt.xlabel('IPC', fontsize=14, fontweight='bold')
plt.ylabel('EDP', fontsize=14, fontweight='bold')
plt.title('Trade-off: IPC vs EDP', fontsize=16, fontweight='bold')
plt.legend(fontsize=11, loc='best')
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig('Img/ipc_vs_edp.png', bbox_inches='tight')
print("Img/ipc_vs_edp.png")
plt.close()

# ===== 3. ENERGY vs EDP =====
plt.figure(figsize=(10, 7))
plt.scatter(dominated['energy'], dominated['edp'], 
           alpha=0.4, s=50, c='lightgray', edgecolors='gray', 
           linewidth=0.5, label='Dominadas')
plt.scatter(pareto['energy'], pareto['edp'], 
           s=150, c='red', edgecolors='black', linewidth=2, 
           label='Frontera de Pareto', zorder=10)
plt.scatter(best_config['energy'], best_config['edp'],
           s=400, c='gold', marker='*', edgecolors='black', 
           linewidth=2.5, label=f'Mejor EDP (sim #{best_edp_idx})', zorder=15)

plt.xlabel('Energy (J)', fontsize=14, fontweight='bold')
plt.ylabel('EDP', fontsize=14, fontweight='bold')
plt.title('Trade-off: Energy vs EDP', fontsize=16, fontweight='bold')
plt.legend(fontsize=11, loc='best')
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig('Img/energy_vs_edp.png', bbox_inches='tight')
print("Img/energy_vs_edp.png")
plt.close()

# ===== 4. EVOLUCIÓN DE IPC (SOLO PUNTOS) =====
plt.figure(figsize=(12, 6))
plt.scatter(df_valid.index, df_valid['ipc'], 
           alpha=0.5, s=40, c='steelblue', edgecolors='darkblue', linewidth=0.5)
plt.axhline(y=pareto['ipc'].max(), color='green', linestyle='--', 
           linewidth=2, label=f'Mejor IPC: {pareto["ipc"].max():.4f} (sim #{best_ipc_idx})')
plt.axhline(y=df_valid['ipc'].mean(), color='orange', linestyle='--', 
           linewidth=2, label=f'Media: {df_valid["ipc"].mean():.4f}')
plt.xlabel('Número de simulación', fontsize=14, fontweight='bold')
plt.ylabel('IPC', fontsize=14, fontweight='bold')
plt.title('Evolución del IPC a través de las simulaciones', 
         fontsize=16, fontweight='bold')
plt.legend(fontsize=11)
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig('Img/evolution_ipc.png', bbox_inches='tight')
print("Img/evolution_ipc.png")
plt.close()

# ===== 5. EVOLUCIÓN DE ENERGY (SOLO PUNTOS) =====
plt.figure(figsize=(12, 6))
plt.scatter(df_valid.index, df_valid['energy'], 
           alpha=0.5, s=40, c='coral', edgecolors='darkred', linewidth=0.5)
plt.axhline(y=pareto['energy'].min(), color='green', linestyle='--', 
           linewidth=2, label=f'Mejor Energy: {pareto["energy"].min():.4f} J (sim #{best_energy_idx})')
plt.axhline(y=df_valid['energy'].mean(), color='orange', linestyle='--', 
           linewidth=2, label=f'Media: {df_valid["energy"].mean():.4f} J')
plt.xlabel('Número de simulación', fontsize=14, fontweight='bold')
plt.ylabel('Energy (J)', fontsize=14, fontweight='bold')
plt.title('Evolución de Energy a través de las simulaciones', 
         fontsize=16, fontweight='bold')
plt.legend(fontsize=11)
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig('Img/evolution_energy.png', bbox_inches='tight')
print("Img/evolution_energy.png")
plt.close()

# ===== 6. EVOLUCIÓN DE EDP (SOLO PUNTOS) =====
plt.figure(figsize=(12, 6))
plt.scatter(df_valid.index, df_valid['edp'], 
           alpha=0.5, s=40, c='purple', edgecolors='darkviolet', linewidth=0.5)
plt.axhline(y=pareto['edp'].min(), color='green', linestyle='--', 
           linewidth=2, label=f'Mejor EDP: {pareto["edp"].min():.4f} (sim #{best_edp_idx})')
plt.axhline(y=df_valid['edp'].mean(), color='orange', linestyle='--', 
           linewidth=2, label=f'Media: {df_valid["edp"].mean():.4f}')
plt.xlabel('Número de simulación', fontsize=14, fontweight='bold')
plt.ylabel('EDP', fontsize=14, fontweight='bold')
plt.title('Evolución del EDP a través de las simulaciones', 
         fontsize=16, fontweight='bold')
plt.legend(fontsize=11)
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig('Img/evolution_edp.png', bbox_inches='tight')
print("Img/evolution_edp.png")
plt.close()

# ===== 7. HISTOGRAMA IPC =====
plt.figure(figsize=(10, 6))
plt.hist(df_valid['ipc'], bins=30, alpha=0.7, color='steelblue', 
         edgecolor='black', linewidth=1.2)
plt.axvline(x=pareto['ipc'].mean(), color='red', linestyle='--', 
           linewidth=2.5, label=f'Media Pareto: {pareto["ipc"].mean():.4f}')
plt.axvline(x=df_valid['ipc'].mean(), color='orange', linestyle='--', 
           linewidth=2.5, label=f'Media total: {df_valid["ipc"].mean():.4f}')
plt.xlabel('IPC', fontsize=14, fontweight='bold')
plt.ylabel('Frecuencia', fontsize=14, fontweight='bold')
plt.title('Distribución de IPC', fontsize=16, fontweight='bold')
plt.legend(fontsize=11)
plt.grid(alpha=0.3, axis='y')
plt.tight_layout()
plt.savefig('Img/histogram_ipc.png', bbox_inches='tight')
print("Img/histogram_ipc.png")
plt.close()

# ===== 8. HISTOGRAMA ENERGY =====
plt.figure(figsize=(10, 6))
plt.hist(df_valid['energy'], bins=30, alpha=0.7, color='coral', 
         edgecolor='black', linewidth=1.2)
plt.axvline(x=pareto['energy'].mean(), color='red', linestyle='--', 
           linewidth=2.5, label=f'Media Pareto: {pareto["energy"].mean():.4f} J')
plt.axvline(x=df_valid['energy'].mean(), color='orange', linestyle='--', 
           linewidth=2.5, label=f'Media total: {df_valid["energy"].mean():.4f} J')
plt.xlabel('Energy (J)', fontsize=14, fontweight='bold')
plt.ylabel('Frecuencia', fontsize=14, fontweight='bold')
plt.title('Distribución de Energy', fontsize=16, fontweight='bold')
plt.legend(fontsize=11)
plt.grid(alpha=0.3, axis='y')
plt.tight_layout()
plt.savefig('Img/histogram_energy.png', bbox_inches='tight')
print("Img/histogram_energy.png")
plt.close()

# ===== 9. HISTOGRAMA EDP =====
plt.figure(figsize=(10, 6))
plt.hist(df_valid['edp'], bins=30, alpha=0.7, color='purple', 
         edgecolor='black', linewidth=1.2)
plt.axvline(x=pareto['edp'].mean(), color='red', linestyle='--', 
           linewidth=2.5, label=f'Media Pareto: {pareto["edp"].mean():.4f}')
plt.axvline(x=df_valid['edp'].mean(), color='orange', linestyle='--', 
           linewidth=2.5, label=f'Media total: {df_valid["edp"].mean():.4f}')
plt.xlabel('EDP', fontsize=14, fontweight='bold')
plt.ylabel('Frecuencia', fontsize=14, fontweight='bold')
plt.title('Distribución de EDP', fontsize=16, fontweight='bold')
plt.legend(fontsize=11)
plt.grid(alpha=0.3, axis='y')
plt.tight_layout()
plt.savefig('Img/histogram_edp.png', bbox_inches='tight')
print(" Img/histogram_edp.png")
plt.close()

# ===== RESUMEN FINAL =====
print("\n" + "="*70)
print("ARCHIVOS GENERADOS")
print("="*70)
print("\nTrade-offs (scatter plots):")
print("   - Img/ipc_vs_energy.png")
print("   - Img/ipc_vs_edp.png")
print("   - Img/energy_vs_edp.png")

print("\nEvoluciones (scatter plots):")
print("   - Img/evolution_ipc.png")
print("   - Img/evolution_energy.png")
print("   - Img/evolution_edp.png")

print("\nDistribuciones (histogramas):")
print("   - Img/histogram_ipc.png")
print("   - Img/histogram_energy.png")
print("   - Img/histogram_edp.png")

print("\nDatos:")
print("   - pareto_configurations.csv")

print("\n" + "="*70)
print("ANÁLISIS COMPLETADO")
print("="*70)

print(f"\nCONFIGURACIÓN RECOMENDADA (Mejor trade-off EDP):")
print(f"   Simulación: #{best_edp_idx}")
print(f"   IPC:    {best_config['ipc']:.4f}")
print(f"   Energy: {best_config['energy']:.4f} J")
print(f"   EDP:    {best_config['edp']:.4f}")