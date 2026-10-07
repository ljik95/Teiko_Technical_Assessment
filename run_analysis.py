"""Run Parts 2-4 against the database and write the results to outputs/.

Usage:
    python run_analysis.py
"""

from pathlib import Path

from analysis import stats, subsets, summary
from analysis.plots import response_boxplot

OUTPUT_DIR = Path(__file__).resolve().parent / "outputs"


def section(title):
    print(f"\n=== {title} ===")


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)

    section("Part 2: relative frequencies")
    freq = summary.frequency_table()
    freq.to_csv(OUTPUT_DIR / "frequency_summary.csv", index=False)
    print(freq.head(10).to_string(index=False))
    print(f"... {len(freq)} rows written to outputs/frequency_summary.csv")

    section("Part 3: responders vs non-responders (melanoma, miraclib, PBMC)")
    cohort = stats.response_cohort()
    results = stats.compare_responders(cohort)
    results.to_csv(OUTPUT_DIR / "responder_stats.csv", index=False)
    response_boxplot(cohort, results, OUTPUT_DIR / "responder_boxplot.png")
    print(results.round(4).to_string(index=False))
    print()
    print(stats.describe_results(results))

    section("Part 4: baseline melanoma PBMC samples on miraclib")
    baseline = subsets.baseline_samples()
    baseline.to_csv(OUTPUT_DIR / "baseline_samples.csv", index=False)
    print(f"{len(baseline)} samples\n")

    by_project = subsets.samples_per_project()
    by_response = subsets.subjects_by_response()
    by_sex = subsets.subjects_by_sex()
    for name, df in [("samples_per_project", by_project),
                     ("subjects_by_response", by_response),
                     ("subjects_by_sex", by_sex)]:
        df.to_csv(OUTPUT_DIR / f"{name}.csv", index=False)
        print(df.to_string(index=False), end="\n\n")

    print(f"All outputs saved in {OUTPUT_DIR.name}/")


if __name__ == "__main__":
    main()
