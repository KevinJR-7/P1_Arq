"""
Analiza resultados del NSGA-II y encuentra mejores configuraciones
"""
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Cargar resultados
df = pd.read_csv("nsga2_results.csv")
df_valid = df[df['ipc'] > 0].copy()

print("="*70)
print("ANÁLISIS DE RESULTADOS NSGA-II")
print("="*70)
print(f"Total simulaciones: {len(df)}")
print(f"Simulaciones válidas: {len(df_valid)}")
print(f"Simulaciones fallidas: {(df['ipc'] == 0).sum()}")

# Top 3 por métrica
print("\n" + "="*70)
print("🏆 TOP 3 - MAYOR IPC (más rápido)")
print("="*70)
top_ipc = df_valid.nlargest(3, 'ipc')
print(top_ipc[['sim_id', 'L1D_size', 'L2_size', 'load_queue', 'ipc', 'energy', 'edp']])

print("\n" + "="*70)
print("⚡ TOP 3 - MENOR ENERGY (más eficiente)")
print("="*70)
top_energy = df_valid.nsmallest(3, 'energy')
print(top_energy[['sim_id', 'L1D_size', 'L2_size', 'load_queue', 'ipc', 'energy', 'edp']])

print("\n" + "="*70)
print("⚖️  TOP 3 - MENOR EDP (mejor balance)")
print("="*70)
top_edp = df_valid.nsmallest(3, 'edp')
print(top_edp[['sim_id', 'L1D_size', 'L2_size', 'load_queue', 'ipc', 'energy', 'edp']])

# Mejores individuos
best_ipc = df_valid.loc[df_valid['ipc'].idxmax()]
best_energy = df_valid.loc[df_valid['energy'].idxmin()]
best_edp = df_valid.loc[df_valid['edp'].idxmin()]

print("\n" + "="*70)
print("MEJORES CONFIGURACIONES")
print("="*70)
print(f"\n🏆 MEJOR IPC = {best_ipc['ipc']:.4f}")
print(f"   L1D={best_ipc['L1D_size']}, L2={best_ipc['L2_size']}, LQ={best_ipc['load_queue']}")

print(f"\n⚡ MEJOR ENERGY = {best_energy['energy']:.4f}J")
print(f"   L1D={best_energy['L1D_size']}, L2={best_energy['L2_size']}, LQ={best_energy['load_queue']}")

print(f"\n⚖️  MEJOR EDP = {best_edp['edp']:.6f}")
print(f"   L1D={best_edp['L1D_size']}, L2={best_edp['L2_size']}, LQ={best_edp['load_queue']}")

# ===== GRÁFICOS DE DISPERSIÓN =====
print("\n" + "="*70)
print("GENERANDO GRÁFICOS...")
print("="*70)

# Figura 1: IPC vs Energy (Frente Pareto)
fig, axes = plt.subplots(2, 2, figsize=(14, 12))

# 1. IPC vs Energy
ax1 = axes[0, 0]
scatter = ax1.scatter(df_valid['energy'], df_valid['ipc'], 
                     c=df_valid['edp'], cmap='viridis', 
                     alpha=0.6, s=100)
ax1.scatter(best_ipc['energy'], best_ipc['ipc'], 
           color='red', s=300, marker='*', 
           edgecolors='black', linewidths=2, label='Best IPC', zorder=5)
ax1.scatter(best_energy['energy'], best_energy['ipc'], 
           color='green', s=300, marker='*', 
           edgecolors='black', linewidths=2, label='Best Energy', zorder=5)
ax1.scatter(best_edp['energy'], best_edp['ipc'], 
           color='blue', s=300, marker='*', 
           edgecolors='black', linewidths=2, label='Best EDP', zorder=5)
ax1.set_xlabel('Energy (J)', fontsize=12)
ax1.set_ylabel('IPC', fontsize=12)
ax1.set_title('Frente Pareto: IPC vs Energy', fontsize=14, fontweight='bold')
ax1.legend(fontsize=10)
ax1.grid(True, alpha=0.3)
plt.colorbar(scatter, ax=ax1, label='EDP')

# 2. Energy vs EDP
ax2 = axes[0, 1]
ax2.scatter(df_valid['energy'], df_valid['edp'], alpha=0.6, s=100)
ax2.scatter(best_energy['energy'], best_energy['edp'], 
           color='green', s=300, marker='*', 
           edgecolors='black', linewidths=2, label='Best Energy')
ax2.scatter(best_edp['energy'], best_edp['edp'], 
           color='blue', s=300, marker='*', 
           edgecolors='black', linewidths=2, label='Best EDP')
ax2.set_xlabel('Energy (J)', fontsize=12)
ax2.set_ylabel('EDP', fontsize=12)
ax2.set_title('Energy vs EDP', fontsize=14, fontweight='bold')
ax2.legend(fontsize=10)
ax2.grid(True, alpha=0.3)

# 3. Impacto de L2 cache
ax3 = axes[1, 0]
for l2_size in df_valid['L2_size'].unique():
    data = df_valid[df_valid['L2_size'] == l2_size]
    ax3.scatter(data['energy'], data['ipc'], label=f'L2={l2_size}', s=100, alpha=0.7)
ax3.set_xlabel('Energy (J)', fontsize=12)
ax3.set_ylabel('IPC', fontsize=12)
ax3.set_title('Impacto de L2 Cache Size', fontsize=14, fontweight='bold')
ax3.legend(fontsize=10)
ax3.grid(True, alpha=0.3)

# 4. Impacto de L1D cache
ax4 = axes[1, 1]
for l1d_size in df_valid['L1D_size'].unique():
    data = df_valid[df_valid['L1D_size'] == l1d_size]
    ax4.scatter(data['energy'], data['ipc'], label=f'L1D={l1d_size}', s=100, alpha=0.7)
ax4.set_xlabel('Energy (J)', fontsize=12)
ax4.set_ylabel('IPC', fontsize=12)
ax4.set_title('Impacto de L1D Cache Size', fontsize=14, fontweight='bold')
ax4.legend(fontsize=10)
ax4.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('nsga2_analysis.png', dpi=300, bbox_inches='tight')
print("📊 Gráfico guardado: nsga2_analysis.png")

# Figura 2: Evolución de parámetros
fig2, axes2 = plt.subplots(1, 3, figsize=(15, 5))

# Distribución de L1D
ax1 = axes2[0]
l1d_counts = df_valid['L1D_size'].value_counts()
ax1.bar(range(len(l1d_counts)), l1d_counts.values)
ax1.set_xticks(range(len(l1d_counts)))
ax1.set_xticklabels(l1d_counts.index, rotation=45)
ax1.set_xlabel('L1D Size', fontsize=12)
ax1.set_ylabel('Frecuencia', fontsize=12)
ax1.set_title('Distribución de L1D Cache', fontsize=14, fontweight='bold')
ax1.grid(True, alpha=0.3, axis='y')

# Distribución de L2
ax2 = axes2[1]
l2_counts = df_valid['L2_size'].value_counts()
ax2.bar(range(len(l2_counts)), l2_counts.values, color='orange')
ax2.set_xticks(range(len(l2_counts)))
ax2.set_xticklabels(l2_counts.index, rotation=45)
ax2.set_xlabel('L2 Size', fontsize=12)
ax2.set_ylabel('Frecuencia', fontsize=12)
ax2.set_title('Distribución de L2 Cache', fontsize=14, fontweight='bold')
ax2.grid(True, alpha=0.3, axis='y')

# Distribución de Load Queue
ax3 = axes2[2]
lq_counts = df_valid['load_queue'].value_counts()
ax3.bar(range(len(lq_counts)), lq_counts.values, color='green')
ax3.set_xticks(range(len(lq_counts)))
ax3.set_xticklabels(lq_counts.index, rotation=45)
ax3.set_xlabel('Load Queue Entries', fontsize=12)
ax3.set_ylabel('Frecuencia', fontsize=12)
ax3.set_title('Distribución de Load Queue', fontsize=14, fontweight='bold')
ax3.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('nsga2_distributions.png', dpi=300, bbox_inches='tight')
print("Gráfico guardado: nsga2_distributions.png")

# Estadísticas de dispersión
print("\n" + "="*70)
print("ESTADÍSTICAS DE DISPERSIÓN")
print("="*70)
print(f"\nIPC:")
print(f"  Rango: [{df_valid['ipc'].min():.4f}, {df_valid['ipc'].max():.4f}]")
print(f"  Variación: {(df_valid['ipc'].max() - df_valid['ipc'].min()) / df_valid['ipc'].mean() * 100:.2f}%")

print(f"\nEnergy (J):")
print(f"  Rango: [{df_valid['energy'].min():.4f}, {df_valid['energy'].max():.4f}]")
print(f"  Variación: {(df_valid['energy'].max() - df_valid['energy'].min()) / df_valid['energy'].mean() * 100:.2f}%")

print(f"\nEDP:")
print(f"  Rango: [{df_valid['edp'].min():.6f}, {df_valid['edp'].max():.6f}]")
print(f"  Variación: {(df_valid['edp'].max() - df_valid['edp'].min()) / df_valid['edp'].mean() * 100:.2f}%")

print("\n" + "="*70)