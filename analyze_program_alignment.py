"""Program-level split and competency alignment analysis.

This script generates two summary tables for the report:
    BSW vs MSW t-test
    competency alignment table

Run from the project root after the pipeline:
    python analyze_program_alignment.py

Outputs:
    outputs/tables/program_split_stats.csv
    outputs/tables/competency_alignment_summary.csv
"""

from __future__ import annotations

import pandas as pd
from scipy import stats

from config import (
    competency_file,
    input_file,
    profiles_dir,
    tables_dir,
)
from constants import (
    likert_cols,
    likert_display,
    likert_map,
    placement_metric_labels,
    placement_quality_cols,
    program_level_map,
)


def ttest_summary(
    group_a: pd.Series, group_b: pd.Series, label: str
) -> dict[str, object]:
    """Run one welch t-test and return the summary"""
    a = group_a.dropna()
    b = group_b.dropna()
    t_stat, p_value = stats.ttest_ind(a, b, equal_var=False)
    return {
        "metric": label,
        "bsw_mean": round(a.mean(), 3),
        "bsw_n": len(a),
        "msw_mean": round(b.mean(), 3),
        "msw_n": len(b),
        "difference": round(b.mean() - a.mean(), 3),
        "t_statistic": round(t_stat, 3),
        "p_value": round(p_value, 4),
        "significant": "yes" if p_value < 0.05 else "no",
    }


def run_program_split_analysis(evaluations_df: pd.DataFrame) -> pd.DataFrame:
    """Compare BSW and MSW responses across the key structured measures."""
    print("\nbsw vs msw program split")

    evaluations_df = evaluations_df.copy()
    evaluations_df["placement_quality_score"] = evaluations_df[
        list(placement_quality_cols)
    ].mean(axis=1)

    bsw = evaluations_df[evaluations_df["program_level"] == "BSW"]
    msw = evaluations_df[evaluations_df["program_level"] == "MSW"]

    total = len(evaluations_df)
    print(f"  bsw: {len(bsw)} ({round(100 * len(bsw) / total, 1)}%)")
    print(f"  msw: {len(msw)} ({round(100 * len(msw) / total, 1)}%)")

    metric_map = {
        "Placement Quality Score": "placement_quality_score",
        "Recommendation rate": "recommend_num",
        **{label: col for col, label in placement_metric_labels.items()},
    }
    for col in likert_cols:
        if col not in placement_metric_labels:
            metric_map[likert_display.get(col, col)] = col

    rows = []
    for label, col in metric_map.items():
        rows.append(ttest_summary(bsw[col], msw[col], label))

    results_df = pd.DataFrame(rows)

    key_metric_names = [
        "Placement Quality Score",
        "Recommendation rate",
        *placement_metric_labels.values(),
    ]
    key_rows = results_df[results_df["metric"].isin(key_metric_names)]

    print("\n  key differences:")
    for _, row in key_rows.iterrows():
        marker = " *" if row["significant"] == "yes" else ""
        if row["difference"] > 0:
            direction = "MSW higher"
        elif row["difference"] < 0:
            direction = "BSW higher"
        else:
            direction = "no difference"

        print(
            f"    {row['metric']}: BSW {row['bsw_mean']:.3f} | "
            f"MSW {row['msw_mean']:.3f} | diff {row['difference']:+.3f} "
            f"({direction}){marker}"
        )
    print("  * p < 0.05")

    return results_df


def run_competency_alignment_analysis(
    profiles_df: pd.DataFrame,
    comp_df: pd.DataFrame,
) -> pd.DataFrame:
    """Summarize how program-level competency scores align with agency fit."""
    analysis_df = profiles_df[
        profiles_df["data_quality"] == "sufficient"
    ].copy()
    analysis_df = analysis_df.dropna(
        subset=["mean_competency_score", "placement_quality_score"]
    )

    print(
        f"\ncompetency alignment ({len(analysis_df)} agencies with both scores)"
    )

    corr_fit, p_fit = stats.pearsonr(
        analysis_df["mean_competency_score"],
        analysis_df["placement_quality_score"],
    )
    print(
        f"  competency vs placement quality: "
        f"r = {corr_fit:.3f}, p = {p_fit:.4f}"
    )

    misaligned = analysis_df[
        analysis_df["misalignment_flag"]
        .str.lower()
        .eq("score-narrative mismatch")
    ]
    print(f"  score-narrative mismatch: {len(misaligned)} agencies")
    for _, row in misaligned.iterrows():
        print(
            f"    {row['agency_name_display']}: "
            f"comp {row['mean_competency_score']:.1f}, "
            f"pqs {row['placement_quality_score']:.2f}, "
            f"sent {row['overall_sentiment_score']:.3f}"
        )

    print("\n  program-level competency context:")
    for level in ["bsw", "msw"]:
        level_df = comp_df[comp_df["program_level"] == level]
        comp_cols = [
            col for col in level_df.columns if col.startswith("competency_")
        ]
        level_means = level_df[comp_cols].mean()
        print(
            f"    {level.upper()}: mean {level_means.mean():.2f}, "
            f"range {level_means.min():.2f} to {level_means.max():.2f}"
        )

    output_df = analysis_df[
        [
            "agency_name",
            "agency_name_display",
            "response_count",
            "mean_competency_score",
            "placement_quality_score",
            "overall_sentiment_score",
            "recommendation_rate",
            "concern_flag",
            "misalignment_flag",
            "fit_trend",
        ]
    ].copy()

    # Convert Placement Quality Score from a 1-5 scale to a 0-100 scale
    # before comparing it to the competency score.
    output_df["competency_quality_gap"] = (
        output_df["mean_competency_score"]
        - output_df["placement_quality_score"] * 20
    ).round(2)

    return output_df.sort_values("competency_quality_gap", ascending=False)


def run_analysis() -> None:
    """Run the split and alignment analysis and save two summary tables."""
    print("running program split and competency alignment")

    evaluations_df = pd.read_csv(input_file)
    evaluations_df["program_level"] = (
        evaluations_df["program_year"]
        .astype("string")
        .str.strip()
        .str.lower()
        .map(program_level_map)
        .replace({"bsw": "BSW", "msw": "MSW"})
    )

    for col in likert_cols:
        evaluations_df[col] = (
            evaluations_df[col]
            .astype("string")
            .str.strip()
            .str.lower()
            .map(likert_map)
        )

    evaluations_df["recommend_num"] = (
        evaluations_df["recommend"]
        .astype("string")
        .str.strip()
        .str.lower()
        .map({"yes": 1, "no": 0})
    )

    profiles_df = pd.read_csv(profiles_dir / "agency_profiles.csv")

    comp_df = pd.read_csv(competency_file)
    comp_df["program_level"] = (
        comp_df["program_level"].astype("string").str.strip().str.lower()
    )

    split_results = run_program_split_analysis(evaluations_df)
    alignment_results = run_competency_alignment_analysis(profiles_df, comp_df)

    tables_dir.mkdir(parents=True, exist_ok=True)
    split_results.to_csv(tables_dir / "program_split_stats.csv", index=False)
    alignment_results.to_csv(
        tables_dir / "competency_alignment_summary.csv",
        index=False,
    )



if __name__ == "__main__":
    run_analysis()
