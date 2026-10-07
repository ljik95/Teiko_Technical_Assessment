"""Part 2: relative frequency of each cell population per sample."""

from .db import DB_PATH, query

FREQUENCY_SQL = """
WITH totals AS (
    SELECT sample_id, SUM(count) AS total_count
    FROM cell_counts
    GROUP BY sample_id
)
SELECT
    c.sample_id                            AS sample,
    t.total_count,
    c.population,
    c.count,
    100.0 * c.count / t.total_count        AS percentage
FROM cell_counts c
JOIN totals t ON t.sample_id = c.sample_id
ORDER BY c.sample_id, c.population
"""


def frequency_table(db_path=DB_PATH):
    """One row per (sample, population) with count and percentage of the sample total."""
    return query(FREQUENCY_SQL, db_path=db_path)
