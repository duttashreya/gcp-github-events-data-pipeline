import duckdb
import pandas as pd
import streamlit as st


DB_PATH = "data/warehouse/github_events.duckdb"


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="GitHub Events Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# DATABASE FUNCTIONS
# =========================================================

@st.cache_data
def load_daily_activity():
    con = duckdb.connect(DB_PATH, read_only=True)

    query = """
        SELECT *
        FROM mart_github_activity_daily
        ORDER BY event_date
    """

    df = con.execute(query).fetchdf()
    con.close()

    return df


@st.cache_data
def load_event_summary(start_date, end_date):
    con = duckdb.connect(DB_PATH, read_only=True)

    query = """
        SELECT
            event_type,
            COUNT(*) AS event_count
        FROM stg_github_events
        WHERE CAST(created_at AS DATE)
              BETWEEN ? AND ?
        GROUP BY event_type
        ORDER BY event_count DESC
    """

    df = con.execute(
        query,
        [start_date, end_date],
    ).fetchdf()

    con.close()

    return df


@st.cache_data
def load_top_repositories(start_date, end_date):
    con = duckdb.connect(DB_PATH, read_only=True)

    query = """
        SELECT
            repository_name,
            COUNT(*) AS event_count
        FROM stg_github_events
        WHERE CAST(created_at AS DATE)
              BETWEEN ? AND ?
        GROUP BY repository_name
        ORDER BY event_count DESC
        LIMIT 10
    """

    df = con.execute(
        query,
        [start_date, end_date],
    ).fetchdf()

    con.close()

    return df


@st.cache_data
def load_period_metrics(start_date, end_date):
    con = duckdb.connect(DB_PATH, read_only=True)

    query = """
        SELECT
            COUNT(*) AS total_events,

            COUNT(DISTINCT actor_login)
                AS unique_actors,

            COUNT(DISTINCT repository_name)
                AS unique_repositories,

            COUNT(
                CASE
                    WHEN event_type = 'PushEvent'
                    THEN 1
                END
            ) AS push_events,

            COUNT(
                CASE
                    WHEN event_type = 'PullRequestEvent'
                    THEN 1
                END
            ) AS pull_request_events,

            COUNT(
                CASE
                    WHEN event_type IN (
                        'IssuesEvent',
                        'IssueCommentEvent'
                    )
                    THEN 1
                END
            ) AS issue_events,

            COUNT(
                CASE
                    WHEN event_type = 'WatchEvent'
                    THEN 1
                END
            ) AS watch_events,

            COUNT(
                CASE
                    WHEN event_type = 'ReleaseEvent'
                    THEN 1
                END
            ) AS release_events,

            COUNT(
                CASE
                    WHEN lower(actor_login) LIKE '%[bot]%'
                    THEN 1
                END
            ) AS bot_events,

            COUNT(
                CASE
                    WHEN lower(actor_login) NOT LIKE '%[bot]%'
                    THEN 1
                END
            ) AS human_events

        FROM stg_github_events

        WHERE CAST(created_at AS DATE)
              BETWEEN ? AND ?
    """

    result = con.execute(
        query,
        [start_date, end_date],
    ).fetchone()

    con.close()

    return result


# =========================================================
# LOAD DAILY DATA
# =========================================================

daily_df = load_daily_activity()


if daily_df.empty:
    st.warning("No GitHub activity data available.")
    st.stop()


daily_df["event_date"] = pd.to_datetime(
    daily_df["event_date"]
)


# =========================================================
# HEADER
# =========================================================

st.title("📊 GitHub Events Analytics Dashboard")

st.caption(
    "End-to-end analytics powered by "
    "GitHub Events API → DuckDB → dbt → Airflow"
)

st.markdown(
    """
    This dashboard provides an overview of public GitHub activity,
    including event trends, event types, repositories, and human
    versus bot activity.
    """
)


# =========================================================
# SIDEBAR FILTERS
# =========================================================

st.sidebar.header("🔎 Filters")

min_date = daily_df["event_date"].min().date()
max_date = daily_df["event_date"].max().date()

selected_dates = st.sidebar.date_input(
    "Select date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)


if (
    isinstance(selected_dates, tuple)
    and len(selected_dates) == 2
):
    start_date, end_date = selected_dates

else:
    start_date = min_date
    end_date = max_date


# =========================================================
# FILTER DAILY MART
# =========================================================

filtered_daily_df = daily_df[
    (daily_df["event_date"].dt.date >= start_date)
    & (daily_df["event_date"].dt.date <= end_date)
].copy()


# =========================================================
# LOAD PERIOD-SPECIFIC DATA
# =========================================================

event_df = load_event_summary(
    start_date,
    end_date,
)

repo_df = load_top_repositories(
    start_date,
    end_date,
)

metrics = load_period_metrics(
    start_date,
    end_date,
)


# =========================================================
# UNPACK METRICS
# =========================================================

(
    total_events,
    unique_actors,
    unique_repositories,
    push_events,
    pull_request_events,
    issue_events,
    watch_events,
    release_events,
    bot_events,
    human_events,
) = metrics


# =========================================================
# OVERVIEW
# =========================================================

st.markdown("### 📈 Overview")

col1, col2, col3, col4 = st.columns(4)


with col1:
    st.metric(
        "Total Events",
        f"{total_events:,}",
    )


with col2:
    st.metric(
        "Unique Actors",
        f"{unique_actors:,}",
    )


with col3:
    st.metric(
        "Unique Repositories",
        f"{unique_repositories:,}",
    )


with col4:
    st.metric(
        "Human / Bot Events",
        f"{human_events:,} / {bot_events:,}",
    )


st.divider()


# =========================================================
# DAILY GITHUB ACTIVITY
# =========================================================

st.markdown("### 📅 Daily GitHub Activity")

import altair as alt

daily_chart = filtered_daily_df[
    [
        "event_date",
        "total_events",
    ]
].copy()

daily_chart["event_date"] = pd.to_datetime(
    daily_chart["event_date"]
)

chart = (
    alt.Chart(daily_chart)
    .mark_line(point=True)
    .encode(
        x=alt.X(
            "event_date:T",
            title="Event Date",
            axis=alt.Axis(format="%Y-%m-%d"),
        ),
        y=alt.Y(
            "total_events:Q",
            title="Total Events",
            scale=alt.Scale(zero=True),
        ),
        tooltip=[
            alt.Tooltip(
                "event_date:T",
                title="Date",
                format="%Y-%m-%d",
            ),
            alt.Tooltip(
                "total_events:Q",
                title="Events",
            ),
        ],
    )
    .properties(height=400)
)

st.altair_chart(
    chart,
    use_container_width=True,
)


# =========================================================
# EVENT TYPES + TOP REPOSITORIES
# =========================================================

col1, col2 = st.columns(2)


# ---------------------------------------------------------
# Event Type Distribution
# ---------------------------------------------------------

with col1:

    st.markdown("### 🔔 Event Type Distribution")

    event_type_data = pd.DataFrame(
        {
            "Event Type": [
                "Push",
                "Pull Request",
                "Issue",
                "Watch",
                "Release",
            ],

            "Events": [
                push_events,
                pull_request_events,
                issue_events,
                watch_events,
                release_events,
            ],
        }
    )


    st.bar_chart(
        event_type_data.set_index(
            "Event Type"
        ),
        height=400,
    )


# ---------------------------------------------------------
# Top Repositories
# ---------------------------------------------------------

with col2:

    st.markdown("### 📦 Top Repositories")

    repo_chart_df = repo_df.copy()

    repo_chart_df["repository_display"] = (
        repo_chart_df["repository_name"]
        .apply(
            lambda x: x if len(x) <= 28 else x[:25] + "..."
        )
    )

    st.bar_chart(
        repo_chart_df.set_index(
            "repository_display"
        )["event_count"],
        height=400,
    )


st.divider()


# =========================================================
# HUMAN VS BOT ACTIVITY
# =========================================================

st.markdown("### 🤖 Human vs Bot Activity")


human_bot_df = pd.DataFrame(
    {
        "Activity Type": [
            "Human",
            "Bot",
        ],

        "Events": [
            human_events,
            bot_events,
        ],
    }
)


st.bar_chart(
    human_bot_df.set_index(
        "Activity Type"
    ),
    height=350,
)


st.divider()


# =========================================================
# DAILY ACTIVITY DATA
# =========================================================

st.markdown("### 📋 Daily Activity Data")


display_df = filtered_daily_df.copy()


display_df["event_date"] = display_df[
    "event_date"
].dt.date


st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True,
)


# =========================================================
# FOOTER
# =========================================================

st.caption(
    f"Showing GitHub activity from "
    f"{start_date} to {end_date}."
)
