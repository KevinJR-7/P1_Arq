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

	fig, axes = plt.subplots(ncols=2, figsize=(14, 6), sharey=True)

	if df_miss is not None:
		df_miss.plot(kind="bar", ax=axes[0], width=0.8)
		axes[0].set_title("Cache miss % by level")
		axes[0].set_ylabel("Percent")
		axes[0].legend(title="Level", bbox_to_anchor=(1.05, 1), loc="upper left")
	else:
		axes[0].text(0.5, 0.5, "No miss% columns", ha="center", va="center")
		axes[0].set_axis_off()

	if df_hit is not None:
		df_hit.plot(kind="bar", ax=axes[1], width=0.8)
		axes[1].set_title("Cache hit % by level")
		axes[1].legend(title="Level", bbox_to_anchor=(1.05, 1), loc="upper left")
	else:
		axes[1].text(0.5, 0.5, "No hit% columns", ha="center", va="center")
		axes[1].set_axis_off()

	for ax in axes:
		ax.set_xlabel("")
		ax.set_xticklabels(ax.get_xticklabels(), rotation=30, ha="right")
		ax.set_ylim(0, 100)

	plt.tight_layout()
	out_path.parent.mkdir(parents=True, exist_ok=True)
	fig.savefig(out_path, dpi=200)
	print(f"Saved plot to: {out_path}")
	if show:
		plt.show()

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

		# plot counts: left = misses by level, right = hits by level
		# Do not share y-axis so each subplot can autoscale independently
		fig_counts, axes_counts = plt.subplots(ncols=2, figsize=(14, 6), sharey=False)

		if not df_miss_counts.empty:
			df_miss_counts.plot(kind="bar", ax=axes_counts[0], width=0.8)
			axes_counts[0].set_title("Cache misses (counts) by level")
			axes_counts[0].set_ylabel("Count")
			axes_counts[0].legend(title="Level", bbox_to_anchor=(1.05, 1), loc="upper left")
		else:
			axes_counts[0].text(0.5, 0.5, "No miss count columns", ha="center", va="center")
			axes_counts[0].set_axis_off()

		if df_hit_counts is not None and not df_hit_counts.empty:
			df_hit_counts.plot(kind="bar", ax=axes_counts[1], width=0.8)
			axes_counts[1].set_title("Cache hits (counts) by level")
			axes_counts[1].legend(title="Level", bbox_to_anchor=(1.05, 1), loc="upper left")
		else:
			axes_counts[1].text(0.5, 0.5, "No hit count columns", ha="center", va="center")
			axes_counts[1].set_axis_off()

		for ax in axes_counts:
			ax.set_xlabel("")
			ax.set_xticklabels(ax.get_xticklabels(), rotation=30, ha="right")
			# Ensure y-axis starts at zero so counts are easy to compare visually
			try:
				ax.set_ylim(bottom=0)
			except Exception:
				pass

		plt.tight_layout()
		counts_out = out_path.with_name(out_path.stem + "_counts" + out_path.suffix)
		fig_counts.savefig(counts_out, dpi=200)
		print(f"Saved counts plot to: {counts_out}")
		if show:
			plt.show()


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

