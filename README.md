# Teiko Technical Assessment: Loblaw Bio Cell Counts

A SQLite database built from `cell-count.csv`, an analysis pipeline, and a Streamlit
dashboard showing the results.

**Dashboard:** https://teikotechnicalassessment-jaythom.streamlit.app/

## Running it (GitHub Codespaces)

```bash
make setup      # install dependencies
make pipeline   # build cell_counts.db and write results to outputs/
make dashboard  # start the dashboard on port 8501
```

When the dashboard starts, Codespaces shows a pop-up for port 8501. Click
**Open in Browser** (or use the **Ports** tab).

## Project layout

```
load_data.py          Part 1: creates cell_counts.db and loads the CSV
run_analysis.py       Runs Parts 2-4 and saves results to outputs/
analysis/
  db.py               Database connection helper
  summary.py          Part 2: relative frequency table
  stats.py            Part 3: responder vs non-responder comparison
  plots.py            Part 3: boxplot
  subsets.py          Part 4: baseline subset queries
dashboard/app.py      Streamlit dashboard
Makefile              setup / pipeline / dashboard targets
```

## Database schema

```
projects    (project_id PK)
subjects    (subject_id PK, project_id FK, condition, age, sex, treatment, response)
samples     (sample_id PK, subject_id FK, sample_type, time_from_treatment_start)
populations (population PK)
cell_counts (sample_id FK, population FK, count)   PK (sample_id, population)
```

Subject details (condition, sex, treatment, response) are stored once per subject
instead of being repeated on every sample. Cell counts are stored one row per sample
and population, so adding a new population only means adding rows, not changing
the schema.

## Results

### Part 2: Data overview

Relative frequency of each population in each sample, saved to
`outputs/frequency_summary.csv` (52,500 rows).

### Part 3: Responders vs non-responders

Melanoma patients on miraclib, PBMC samples only. Each population's relative
frequency is compared between responders and non-responders, and a difference is
significant when p < 0.05.

| population | responder median % | non-responder median % | p-value |
|---|---|---|---|
| cd4_t_cell | 30.22 | 29.66 | 0.0133 |
| b_cell     |  9.43 |  9.79 | 0.0557 |
| nk_cell    | 14.51 | 14.80 | 0.1211 |
| monocyte   | 19.61 | 19.94 | 0.1632 |
| cd8_t_cell | 24.73 | 24.60 | 0.6391 |

**cd4_t_cell is the only population with a significant difference**: it is higher
in responders. The boxplot is saved to `outputs/responder_boxplot.png`.

### Part 4: Baseline subset

Melanoma PBMC samples at baseline (`time_from_treatment_start = 0`) from
miraclib-treated patients: 656 samples.

- Samples per project: prj1 = 384, prj3 = 272
- Subjects: 331 responders, 325 non-responders
- Subjects: 344 males, 312 females
