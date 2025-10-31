#!/usr/bin/env python3
"""Simple plotting utility for instruction vs FU percentage profiles.

Reads `stats/instruction_fu_profile.csv` (by default) and creates two
stacked bar charts side-by-side:
 - left: instruction-type percentages (branch, load, store, ALU int, ALU float, others)
 - right: functional-unit percentages (fu_load, fu_store, fu_aluint, fu_alufloat, fu_others)

The script saves a PNG next to this file (`instruction_fu_profile.png`) by default.

Usage:
  python plot.py [--csv PATH] [--out PATH] [--show]

Requires: pandas, matplotlib
"""

from pathlib import Path
import argparse
import sys

import pandas as pd
import matplotlib.pyplot as plt


DEFAULT_CSV = Path(__file__).resolve().parent / "stats" / "instruction_fu_profile.csv"


def load_data(csv_path: Path) -> pd.DataFrame:
	if not csv_path.exists():
		raise FileNotFoundError(f"CSV not found: {csv_path}")
	df = pd.read_csv(csv_path)
	if "experiment" not in df.columns:
		raise ValueError("CSV must contain an 'experiment' column")
	df = df.set_index("experiment")
	return df


def pick_columns(df: pd.DataFrame, candidates):
	# return the sublist of candidates that exist in df.columns
	return [c for c in candidates if c in df.columns]


def build_plots(df: pd.DataFrame, out_path: Path, show: bool = False):
	instr_candidates = [
		"branch_pct",
		"load_pct",
		"store_pct",
		"aluint_pct",
		"alufloat_pct",
		"others_pct",
	]

	fu_candidates = [
		"fu_load_pct",
		"fu_store_pct",
		"fu_aluint_pct",
		"fu_alufloat_pct",
		"fu_others_pct",
	]

	instr_cols = pick_columns(df, instr_candidates)
	fu_cols = pick_columns(df, fu_candidates)

	if not instr_cols:
		raise ValueError("No instruction percentage columns found in CSV")
	if not fu_cols:
		raise ValueError("No FU percentage columns found in CSV")

	# Select only the needed columns and ensure numeric
	df_instr = df[instr_cols].apply(pd.to_numeric, errors="coerce").fillna(0)
	df_fu = df[fu_cols].apply(pd.to_numeric, errors="coerce").fillna(0)

	# Create figure with two subplots
	fig, axes = plt.subplots(ncols=2, figsize=(14, 6), sharey=True)

	df_instr.plot(
		kind="bar",
		stacked=True,
		ax=axes[0],
		colormap="tab20",
		width=0.8,
	)
	axes[0].set_title("Instruction mix (%)")
	axes[0].set_ylabel("Percent")
	axes[0].legend(title="Instr", bbox_to_anchor=(1.05, 1), loc="upper left")

	df_fu.plot(
		kind="bar",
		stacked=True,
		ax=axes[1],
		colormap="tab20",
		width=0.8,
	)
	axes[1].set_title("Functional unit busy (%)")
	axes[1].legend(title="FU", bbox_to_anchor=(1.05, 1), loc="upper left")

	# Tidy x-axis labels
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


def main(argv=None):
	parser = argparse.ArgumentParser(description="Plot instruction and FU percentage profiles")
	parser.add_argument("--csv", type=Path, default=DEFAULT_CSV, help="Path to CSV file")
	parser.add_argument("--out", type=Path, default=Path(__file__).resolve().parent / "instruction_fu_profile.png", help="Output PNG path")
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

