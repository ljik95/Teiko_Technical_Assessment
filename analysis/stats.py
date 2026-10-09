"""Part 3: responders vs non-responders among melanoma patients on miraclib (PBMC only)."""

import pandas as pd
from scipy.stats import mannwhitneyu

from .db import DB_PATH, query

# A difference is called significant when its p-value is below this cutoff.
SIGNIFICANCE_LEVEL = 0.05

COHORT_SQL = """
WITH totals AS (
    SELECT sample_id, SUM(count) AS total_count
    FROM cell_counts
    GROUP BY sample_id
)
SELECT
    s.sample_id                         AS sample,
    sub.response,
    c.population,
    100.0 * c.count / t.total_count     AS percentage
FROM cell_counts c
JOIN totals t    ON t.sample_id = c.sample_id
JOIN samples s   ON s.sample_id = c.sample_id
JOIN subjects sub ON sub.subject_id = s.subject_id
WHERE sub.condition = 'melanoma'
  AND sub.treatment = 'miraclib'
  AND s.sample_type = 'PBMC'
  AND sub.response IN ('yes', 'no')
ORDER BY s.sample_id, c.population
"""


def response_cohort(db_path=DB_PATH):
    df = query(COHORT_SQL, db_path=db_path)
    df["group"] = df["response"].map({"yes": "responder", "no": "non-responder"})
    return df


def compare_responders(cohort):
    """Test each population for a difference between responders and non-responders."""
    rows = []
    for population, group in cohort.groupby("population"):
        responders = group.loc[group["response"] == "yes", "percentage"]
        non_responders = group.loc[group["response"] == "no", "percentage"]
        rows.append({
            "population": population,
            "responder_median_pct": responders.median(),
            "non_responder_median_pct": non_responders.median(),
            "p_value": mannwhitneyu(responders, non_responders).pvalue,
        })

    results = pd.DataFrame(rows)
    results["significant"] = results["p_value"] < SIGNIFICANCE_LEVEL
    return results.sort_values("p_value").reset_index(drop=True)


def describe_results(results):
    significant = results[results["significant"]]
    if significant.empty:
        return "No population differs significantly between responders and non-responders."

    lines = []
    for row in significant.itertuples():
        direction = "higher" if row.responder_median_pct > row.non_responder_median_pct else "lower"
        lines.append(
            f"{row.population} is significantly {direction} in responders "
            f"(median {row.responder_median_pct:.2f}% vs {row.non_responder_median_pct:.2f}%, "
            f"p = {row.p_value:.4f})."
        )
    return "\n".join(lines)
