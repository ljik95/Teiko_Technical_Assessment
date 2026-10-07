"""Part 4: baseline melanoma PBMC samples from miraclib-treated patients."""

from .db import DB_PATH, query

BASELINE_FILTER = """
    sub.condition = 'melanoma'
    AND sub.treatment = 'miraclib'
    AND s.sample_type = 'PBMC'
    AND s.time_from_treatment_start = 0
"""


def baseline_samples(db_path=DB_PATH):
    sql = f"""
        SELECT s.sample_id AS sample, sub.subject_id AS subject, sub.project_id AS project,
               sub.condition, sub.age, sub.sex, sub.treatment, sub.response,
               s.sample_type, s.time_from_treatment_start
        FROM samples s
        JOIN subjects sub ON sub.subject_id = s.subject_id
        WHERE {BASELINE_FILTER}
        ORDER BY s.sample_id
    """
    return query(sql, db_path=db_path)


def samples_per_project(db_path=DB_PATH):
    sql = f"""
        SELECT sub.project_id AS project, COUNT(*) AS n_samples
        FROM samples s
        JOIN subjects sub ON sub.subject_id = s.subject_id
        WHERE {BASELINE_FILTER}
        GROUP BY sub.project_id
        ORDER BY sub.project_id
    """
    return query(sql, db_path=db_path)


def _subjects_by(column, db_path):
    # Count distinct subjects, since a subject could in principle have several baseline samples.
    sql = f"""
        SELECT sub.{column} AS {column}, COUNT(DISTINCT sub.subject_id) AS n_subjects
        FROM samples s
        JOIN subjects sub ON sub.subject_id = s.subject_id
        WHERE {BASELINE_FILTER}
        GROUP BY sub.{column}
        ORDER BY sub.{column}
    """
    return query(sql, db_path=db_path)


def subjects_by_response(db_path=DB_PATH):
    df = _subjects_by("response", db_path)
    df["response"] = df["response"].map({"yes": "responder", "no": "non-responder"})
    return df


def subjects_by_sex(db_path=DB_PATH):
    df = _subjects_by("sex", db_path)
    df["sex"] = df["sex"].map({"M": "male", "F": "female"})
    return df
