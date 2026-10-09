"""Streamlit dashboard for the Loblaw Bio cell count analysis.

Run with `make dashboard` (or `streamlit run dashboard/app.py`) after `make pipeline`.
"""

import sys
from pathlib import Path

import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from analysis import stats, subsets, summary  # noqa: E402
from analysis.db import DB_PATH  # noqa: E402
import load_data  # noqa: E402

st.set_page_config(page_title="Loblaw Bio - Cell Counts", layout="wide")


@st.cache_resource(show_spinner="Building the database from cell-count.csv...")
def ensure_database():
    # `make pipeline` normally creates the database. Building it here as well lets the
    # app run on its own (e.g. on Streamlit Community Cloud). cache_resource runs this
    # once per server, and other sessions wait for it to finish.
    if not DB_PATH.exists():
        load_data.main()


@st.cache_data
def load_frequencies():
    return summary.frequency_table()


@st.cache_data
def load_cohort():
    cohort = stats.response_cohort()
    return cohort, stats.compare_responders(cohort)


@st.cache_data
def load_baseline():
    return (
        subsets.baseline_samples(),
        subsets.samples_per_project(),
        subsets.subjects_by_response(),
        subsets.subjects_by_sex(),
    )


def overview_tab():
    st.subheader("Relative frequency of each population per sample")
    freq = load_frequencies()

    col1, col2 = st.columns([1, 3])
    with col1:
        populations = sorted(freq["population"].unique())
        selected = st.multiselect("Populations", populations, default=populations)
        sample_filter = st.text_input("Sample ID contains", "")

    view = freq[freq["population"].isin(selected)]
    if sample_filter:
        view = view[view["sample"].str.contains(sample_filter.strip(), case=False)]

    with col2:
        st.caption(f"{len(view):,} of {len(freq):,} rows")
        st.dataframe(
            view,
            hide_index=True,
            width="stretch",
            column_config={"percentage": st.column_config.NumberColumn(format="%.2f")},
        )

    st.download_button(
        "Download full table (CSV)",
        freq.to_csv(index=False),
        file_name="frequency_summary.csv",
        mime="text/csv",
    )


def statistics_tab():
    st.subheader("Responders vs non-responders: melanoma, miraclib, PBMC")
    cohort, results = load_cohort()

    n_resp = cohort.loc[cohort["response"] == "yes", "sample"].nunique()
    n_non = cohort.loc[cohort["response"] == "no", "sample"].nunique()
    st.caption(f"{n_resp} responder samples, {n_non} non-responder samples "
               "(all time points)")

    fig = px.box(
        cohort,
        x="population",
        y="percentage",
        color="group",
        category_orders={"group": ["responder", "non-responder"]},
        color_discrete_map={"responder": "#4C72B0", "non-responder": "#DD8452"},
        labels={"percentage": "Relative frequency (%)", "population": "", "group": ""},
    )
    fig.update_layout(height=500, legend=dict(orientation="h", y=1.08))
    st.plotly_chart(fig, width="stretch")

    st.markdown(f"**Significance test per population** (p < {stats.SIGNIFICANCE_LEVEL} "
                "is significant)")
    st.dataframe(
        results,
        hide_index=True,
        width="stretch",
        column_config={
            col: st.column_config.NumberColumn(format="%.4f")
            for col in results.select_dtypes("float").columns
        },
    )
    st.info(stats.describe_results(results))


def subset_tab():
    st.subheader("Baseline melanoma PBMC samples from miraclib-treated patients")
    baseline, by_project, by_response, by_sex = load_baseline()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Samples", len(baseline))
    c2.metric("Subjects", baseline["subject"].nunique())
    responders = by_response.set_index("response")["n_subjects"]
    c3.metric("Responders / non-responders",
              f"{responders.get('responder', 0)} / {responders.get('non-responder', 0)}")
    sexes = by_sex.set_index("sex")["n_subjects"]
    c4.metric("Males / females", f"{sexes.get('male', 0)} / {sexes.get('female', 0)}")

    col1, col2, col3 = st.columns(3)
    for col, df, label in [
        (col1, by_project, "Samples per project"),
        (col2, by_response, "Subjects by response"),
        (col3, by_sex, "Subjects by sex"),
    ]:
        with col:
            st.markdown(f"**{label}**")
            st.dataframe(df, hide_index=True, width="stretch")
            x, y = df.columns
            st.plotly_chart(px.bar(df, x=x, y=y, text=y).update_layout(height=300),
                            width="stretch")

    with st.expander("Show all baseline samples"):
        st.dataframe(baseline, hide_index=True, width="stretch")


def main():
    st.title("Loblaw Bio: immune cell populations")

    ensure_database()

    tab1, tab2, tab3 = st.tabs(
        ["Part 2: Data overview", "Part 3: Statistical analysis", "Part 4: Subset analysis"]
    )
    with tab1:
        overview_tab()
    with tab2:
        statistics_tab()
    with tab3:
        subset_tab()


main()
