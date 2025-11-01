#!/usr/bin/env python3
"""Plot cache profile CSV (counts)

Reads `stats/cache_profile.csv` and produces two grouped bar charts side-by-side:
 - left: miss counts for i-cache, d-cache, L2, L3
 - right: hit counts for the same levels (computed as accesses - misses)

Saves output PNG to `profiling/cache_profile.png` by default.
"""

from pathlib import Path
import argparse
import sys

import pandas as pd
import matplotlib.pyplot as plt


DEFAULT_CSV = Path(__file__).resolve().parent / "stats" / "cache_profile.csv"


def load_data(csv_path: Path) -> pd.DataFrame:
	if not csv_path.exists():
		raise FileNotFoundError(f"CSV not found: {csv_path}")
	df = pd.read_csv(csv_path)
	if "experiment" not in df.columns:
		raise ValueError("CSV must contain an 'experiment' column")
	df = df.set_index("experiment")
	return df


def pick_ordered(df: pd.DataFrame, prefix_list):
	# return columns from df that match prefixes in the given order
	cols = []
	for p in prefix_list:
		matches = [c for c in df.columns if c.startswith(p)]
		# if exact match like 'icache_miss_pct' exists prefer it
		if matches:
			# sort to produce a stable order
			matches.sort()
			cols.append(matches[0])
	return cols


def build_plots(df: pd.DataFrame, out_path: Path, show: bool = False):
	miss_prefixes = ["icache_miss_pct", "dcache_miss_pct", "l2_miss_pct", "l3_miss_pct"]
	hit_prefixes = ["icache_hit_pct", "dcache_hit_pct", "l2_hit_pct", "l3_hit_pct"]

	miss_cols = [c for c in miss_prefixes if c in df.columns]
	hit_cols = [c for c in hit_prefixes if c in df.columns]

	if not miss_cols and not hit_cols:
		raise ValueError("No miss% or hit% columns found in CSV")

	# prepare dataframes for plotting; keep experiments on x-axis
	df_miss = df[miss_cols].apply(pd.to_numeric, errors="coerce").fillna(0) if miss_cols else None
	df_hit = df[hit_cols].apply(pd.to_numeric, errors="coerce").fillna(0) if hit_cols else None

	# Create and save percentage plots separately (one PNG per subplot)
	out_path.parent.mkdir(parents=True, exist_ok=True)
	base = out_path.stem
	parent = out_path.parent

	# Miss percentage plot
	if df_miss is not None:
		fig_miss, ax_miss = plt.subplots(figsize=(8, 6))
		df_miss.plot(kind="bar", ax=ax_miss, width=0.8)
		ax_miss.set_title("Cache miss % by level")
		ax_miss.set_ylabel("Percent")
		ax_miss.legend(title="Level", bbox_to_anchor=(1.05, 1), loc="upper left")
		ax_miss.set_xlabel("")
		ax_miss.set_xticklabels(ax_miss.get_xticklabels(), rotation=30, ha="right")
		ax_miss.set_ylim(0, 100)
		miss_pct_out = parent / (base + "_miss_pct" + out_path.suffix)
		fig_miss.tight_layout()
		fig_miss.savefig(miss_pct_out, dpi=200)
		plt.close(fig_miss)
		print(f"Saved plot to: {miss_pct_out}")
		if show:
			plt.show()
	else:
		print("No miss% columns to plot")

	# Hit percentage plot
	if df_hit is not None:
		fig_hit, ax_hit = plt.subplots(figsize=(8, 6))
		df_hit.plot(kind="bar", ax=ax_hit, width=0.8)
		ax_hit.set_title("Cache hit % by level")
		ax_hit.legend(title="Level", bbox_to_anchor=(1.05, 1), loc="upper left")
		ax_hit.set_xlabel("")
		ax_hit.set_xticklabels(ax_hit.get_xticklabels(), rotation=30, ha="right")
		ax_hit.set_ylim(0, 100)
		hit_pct_out = parent / (base + "_hit_pct" + out_path.suffix)
		fig_hit.tight_layout()
		fig_hit.savefig(hit_pct_out, dpi=200)
		plt.close(fig_hit)
		print(f"Saved plot to: {hit_pct_out}")
		if show:
			plt.show()
	else:
		print("No hit% columns to plot")

	# --- Additional output: per-level counts (misses and hits) ---
	# Determine available count columns
	miss_count_cols = [c for c in [
		"icache_misses", "dcache_misses", "l2_misses", "l3_misses"
	] if c in df.columns]
	access_count_cols = [c for c in [
		"icache_accesses", "dcache_accesses", "l2_accesses", "l3_accesses"
	] if c in df.columns]

	# Only create counts plot if we have misses and accesses
	if miss_count_cols and access_count_cols:
		# prepare per-level misses dataframe
		df_miss_counts = df[miss_count_cols].apply(pd.to_numeric, errors="coerce").fillna(0)

		# compute per-level hits where possible (accesses - misses)
		hits_data = {}
		for miss_col in miss_count_cols:
			base_access = miss_col.replace("_misses", "_accesses")
			if base_access in df.columns:
				hits_data[miss_col.replace("_misses", "_hits")] = (
					df[base_access].astype(float).fillna(0) - df[miss_col].astype(float).fillna(0)
				)
		# build hits dataframe if we found any
		df_hit_counts = pd.DataFrame(hits_data, index=df.index) if hits_data else None

		# Plot and save per-level misses and hits as separate PNGs
		# Miss counts
		if not df_miss_counts.empty:
			fig_mc, ax_mc = plt.subplots(figsize=(8, 6))
			df_miss_counts.plot(kind="bar", ax=ax_mc, width=0.8)
			ax_mc.set_title("Cache misses (counts) by level")
			ax_mc.set_ylabel("Count")
			ax_mc.legend(title="Level", bbox_to_anchor=(1.05, 1), loc="upper left")
			ax_mc.set_xlabel("")
			ax_mc.set_xticklabels(ax_mc.get_xticklabels(), rotation=30, ha="right")
			try:
				ax_mc.set_ylim(bottom=0)
			except Exception:
				pass
			miss_counts_out = parent / (base + "_miss_counts" + out_path.suffix)
			fig_mc.tight_layout()
			fig_mc.savefig(miss_counts_out, dpi=200)
			plt.close(fig_mc)
			print(f"Saved counts plot to: {miss_counts_out}")
			if show:
				plt.show()
		else:
			print("No miss count columns to plot")

		# Hit counts
		if df_hit_counts is not None and not df_hit_counts.empty:
			fig_hc, ax_hc = plt.subplots(figsize=(8, 6))
			df_hit_counts.plot(kind="bar", ax=ax_hc, width=0.8)
			ax_hc.set_title("Cache hits (counts) by level")
			ax_hc.legend(title="Level", bbox_to_anchor=(1.05, 1), loc="upper left")
			ax_hc.set_xlabel("")
			ax_hc.set_xticklabels(ax_hc.get_xticklabels(), rotation=30, ha="right")
			try:
				ax_hc.set_ylim(bottom=0)
			except Exception:
				pass
			hit_counts_out = parent / (base + "_hit_counts" + out_path.suffix)
			fig_hc.tight_layout()
			fig_hc.savefig(hit_counts_out, dpi=200)
			plt.close(fig_hc)
			print(f"Saved counts plot to: {hit_counts_out}")
			if show:
				plt.show()
		else:
			print("No hit count columns to plot")


def main(argv=None):
	parser = argparse.ArgumentParser(description="Plot cache profile CSV")
	parser.add_argument("--csv", type=Path, default=DEFAULT_CSV, help="Path to CSV file")
	parser.add_argument("--out", type=Path, default=Path(__file__).resolve().parent / "cache_profile.png", help="Output PNG path")
	parser.add_argument("--show", action="store_true", help="Show plot interactively")
	args = parser.parse_args(argv)

	df = load_data(args.csv)
	build_plots(df, args.out, show=args.show)


if __name__ == "__main__":
	try:
		main()
	except Exception as e:
		print(f"Error: {e}", file=sys.stderr)
		sys.exit(1)

