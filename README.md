# Teiko Technical Assessment: Loblaw Bio Cell Counts

**Dashboard:** [<DASHBOARD_URL>](https://teikotechnicalassessment-jaythom.streamlit.app/)

## Running it (GitHub Codespaces)

```bash
make setup      # install Python dependencies
make pipeline   # build cell_counts.db and write results to outputs/
make dashboard  # start the dashboard on port 8501
```

When the dashboard starts, Codespaces shows a pop-up for port 8501. Click
**Open in Browser**, or open the **Ports** tab and click the globe icon next to 8501.

`make clean` removes the database and the outputs.

## Project layout

```
load_data.py          Part 1: creates cell_counts.db and loads the CSV
run_analysis.py       Runs Parts 2-4 and saves results to outputs/
analysis/
  db.py               Database connection and query helper
  summary.py          Part 2: relative frequency table
  stats.py            Part 3: responder vs non-responder comparison
  plots.py            Part 3: boxplot
  subsets.py          Part 4: baseline subset queries
dashboard/app.py      Streamlit dashboard (Parts 2-4)
Makefile              setup / pipeline / dashboard targets
```

## Analysis

### Part 2: Data overview

`analysis/summary.py` computes each sample's total count and every population's
share of that total in a single SQL query. The full table (52,500 rows) is saved
to `outputs/frequency_summary.csv`. The dashboard lets you filter it by
population or sample.

### Part 3: Responders vs non-responders

Cohort: melanoma patients treated with miraclib, PBMC samples only (993 responder
and 975 non-responder samples across days 0, 7 and 14).

For each population I compared relative frequencies with a two-sided
**Mann-Whitney U test**. The percentages are bounded and not normally
distributed, so a rank-based test is safer than a t-test. Five populations are
tested at once, so p-values are also **Benjamini-Hochberg adjusted**.

Most subjects contribute three samples, which means the samples are not fully
independent. As a check, the test is repeated after averaging each subject's
samples (`p_value_subject_level`).

| population | responder median % | non-responder median % | p | BH q | subject-level p |
|---|---|---|---|---|---|
| cd4_t_cell | 30.22 | 29.66 | 0.0133 | 0.0667 | 0.0124 |
| b_cell     |  9.43 |  9.79 | 0.0557 | 0.1393 | 0.3458 |
| nk_cell    | 14.51 | 14.80 | 0.1211 | 0.2018 | 0.1267 |
| monocyte   | 19.61 | 19.94 | 0.1632 | 0.2039 | 0.2645 |
| cd8_t_cell | 24.73 | 24.60 | 0.6391 | 0.6391 | 0.6221 |

**Result:** CD4 T cells are the only population that differs significantly
between groups (p = 0.013). They are slightly higher in responders, and the
result holds at the subject level (p = 0.012). The effect is small (about 0.6
percentage points) and falls just short of significance after correcting for five
tests (q = 0.067). So CD4 T cell frequency is a reasonable candidate marker of
response, but it should be confirmed in an independent cohort before relying on it.

The boxplot is saved to `outputs/responder_boxplot.png` and shown interactively in
the dashboard.

### Part 4: Baseline subset

Melanoma PBMC samples at baseline (`time_from_treatment_start = 0`) from
miraclib-treated patients: 656 samples from 656 subjects.

- Samples per project: prj1 = 384, prj3 = 272
- Responders: 331, non-responders: 325
- Males: 344, females: 312

Queries are in `analysis/subsets.py`. Results are saved under `outputs/`.
