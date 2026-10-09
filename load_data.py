"""Create the SQLite database and load cell-count.csv into it.

Usage:
    python load_data.py
"""

import csv
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CSV_PATH = ROOT / "cell-count.csv"
DB_PATH = ROOT / "cell_counts.db"

POPULATIONS = ["b_cell", "cd8_t_cell", "cd4_t_cell", "nk_cell", "monocyte"]

SCHEMA = """
CREATE TABLE projects (
    project_id  TEXT PRIMARY KEY
);

CREATE TABLE subjects (
    subject_id  TEXT PRIMARY KEY,
    project_id  TEXT NOT NULL REFERENCES projects (project_id),
    condition   TEXT NOT NULL,
    age         INTEGER,
    sex         TEXT CHECK (sex IN ('M', 'F')),
    treatment   TEXT NOT NULL,
    response    TEXT CHECK (response IN ('yes', 'no'))  -- NULL when not applicable
);

CREATE TABLE samples (
    sample_id                  TEXT PRIMARY KEY,
    subject_id                 TEXT NOT NULL REFERENCES subjects (subject_id),
    sample_type                TEXT NOT NULL,
    time_from_treatment_start  INTEGER NOT NULL
);

CREATE TABLE populations (
    population  TEXT PRIMARY KEY
);

CREATE TABLE cell_counts (
    sample_id   TEXT NOT NULL REFERENCES samples (sample_id),
    population  TEXT NOT NULL REFERENCES populations (population),
    count       INTEGER NOT NULL CHECK (count >= 0),
    PRIMARY KEY (sample_id, population)
);

CREATE INDEX idx_subjects_filters ON subjects (condition, treatment, response);
CREATE INDEX idx_samples_subject ON samples (subject_id);
CREATE INDEX idx_samples_type_time ON samples (sample_type, time_from_treatment_start);
"""


def read_rows(csv_path):
    with open(csv_path, newline="") as f:
        return list(csv.DictReader(f))


def none_if_blank(value):
    value = value.strip()
    return value or None


def load(rows, conn):
    projects = set()
    subjects = {}
    samples = []
    counts = []

    for row in rows:
        subject_id = row["subject"]
        projects.add(row["project"])

        subject = (
            subject_id,
            row["project"],
            row["condition"],
            int(row["age"]) if row["age"] else None,
            none_if_blank(row["sex"]),
            row["treatment"],
            none_if_blank(row["response"]),
        )
        # Subject-level fields repeat on every sample row, so make sure they agree.
        if subjects.setdefault(subject_id, subject) != subject:
            raise ValueError(f"Inconsistent subject details for {subject_id}")

        samples.append((
            row["sample"],
            subject_id,
            row["sample_type"],
            int(row["time_from_treatment_start"]),
        ))
        for pop in POPULATIONS:
            counts.append((row["sample"], pop, int(row[pop])))

    conn.executemany("INSERT INTO projects VALUES (?)", [(p,) for p in sorted(projects)])
    conn.executemany("INSERT INTO subjects VALUES (?, ?, ?, ?, ?, ?, ?)", subjects.values())
    conn.executemany("INSERT INTO samples VALUES (?, ?, ?, ?)", samples)
    conn.executemany("INSERT INTO populations VALUES (?)", [(p,) for p in POPULATIONS])
    conn.executemany("INSERT INTO cell_counts VALUES (?, ?, ?)", counts)

    return len(subjects), len(samples), len(counts)


def main():
    if not CSV_PATH.exists():
        raise SystemExit(f"Could not find {CSV_PATH}")

    # Build into a temporary file and only move it into place once it's complete,
    # so nothing ever reads a half-built database.
    tmp_path = DB_PATH.with_name(DB_PATH.name + ".tmp")
    tmp_path.unlink(missing_ok=True)

    rows = read_rows(CSV_PATH)
    conn = sqlite3.connect(tmp_path)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        with conn:
            conn.executescript(SCHEMA)
            n_subjects, n_samples, n_counts = load(rows, conn)
    finally:
        conn.close()
    tmp_path.replace(DB_PATH)

    print(f"Created {DB_PATH.name}: {n_subjects} subjects, "
          f"{n_samples} samples, {n_counts} cell count rows")


if __name__ == "__main__":
    main()
