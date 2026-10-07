"""Part 3: responders vs non-responders among melanoma patients on miraclib (PBMC only).

Each population is compared with a two-sided Mann-Whitney U test on the per-sample
relative frequencies. The percentages aren't normally distributed and the groups are
independent, so a rank-based test is a reasonable default. Because five populations
are tested at once, p-values are also adjusted with Benjamini-Hochberg.

Most subjects contribute three samples (day 0, 7 and 14), so samples aren't fully
independent. As a sanity check the same test is repeated after averaging each
subject's samples, which gives one value per subject.
"""

import pandas as pd
from scipy.stats import false_discovery_control, mannwhitneyu

from .db import DB_PATH, query

ALPHA = 0.05

COHORT_SQL = """
WITH totals AS (
    SELECT sample_id, SUM(count) AS total_count
    FROM cell_counts
    GROUP BY sample_id
)
SELECT
    s.sample_id                         AS sample,
    sub.subject_id                      AS subject,
    sub.response,
    s.time_from_treatment_start,
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


def _mwu_pvalue(df):
    responders = df.loc[df["response"] == "yes", "percentage"]
    non_responders = df.loc[df["response"] == "no", "percentage"]
    return mannwhitneyu(responders, non_responders, alternative="two-sided").pvalue


def compare_responders(cohort):
    """Return one row of test results per population."""
    per_subject = (
        cohort.groupby(["subject", "response", "population"], as_index=False)["percentage"]
        .mean()
    )

    rows = []
    for population, group in cohort.groupby("population"):
        resp = group.loc[group["response"] == "yes", "percentage"]
        non_resp = group.loc[group["response"] == "no", "percentage"]
        subj = per_subject[per_subject["population"] == population]
        rows.append({
            "population": population,
            "n_responder_samples": len(resp),
            "n_non_responder_samples": len(non_resp),
            "responder_median_pct": resp.median(),
            "non_responder_median_pct": non_resp.median(),
            "median_difference": resp.median() - non_resp.median(),
            "p_value": _mwu_pvalue(group),
            "p_value_subject_level": _mwu_pvalue(subj),
        })

    results = pd.DataFrame(rows)
    results["q_value_bh"] = false_discovery_control(results["p_value"], method="bh")
    results["significant_raw"] = results["p_value"] < ALPHA
    results["significant_bh"] = results["q_value_bh"] < ALPHA
    return results.sort_values("p_value").reset_index(drop=True)


def describe_results(results):
    """Plain-language summary of the test results."""
    nominal = results[results["significant_raw"]]
    adjusted = results[results["significant_bh"]]

    if nominal.empty:
        return (f"No population differs significantly between responders and "
                f"non-responders (all p >= {ALPHA}).")

    lines = []
    for row in nominal.itertuples():
        direction = "higher" if row.median_difference > 0 else "lower"
        lines.append(
            f"{row.population}: {direction} in responders "
            f"(median {row.responder_median_pct:.2f}% vs {row.non_responder_median_pct:.2f}%), "
            f"p = {row.p_value:.4f}, BH q = {row.q_value_bh:.4f}, "
            f"subject-level p = {row.p_value_subject_level:.4f}"
        )

    if adjusted.empty:
        lines.append(
            f"Note: none of these remain below {ALPHA} after Benjamini-Hochberg "
            "correction for the five populations tested, so treat them as candidates "
            "that need confirmation rather than firm findings."
        )
    return "\n".join(lines)
