{{ config(materialized='table') }}

with events as (

    select *
    from {{ ref('int_github_events_enriched') }}

),

daily_activity as (

    select
        event_date,

        count(*) as total_events,

        count(distinct actor_login) as unique_actors,

        count(distinct repository_name) as unique_repositories,

        count(
            case
                when event_type = 'PushEvent'
                then 1
            end
        ) as push_events,

        count(
            case
                when event_type = 'PullRequestEvent'
                then 1
            end
        ) as pull_request_events,

        count(
            case
                when event_type in (
                    'IssuesEvent',
                    'IssueCommentEvent'
                )
                then 1
            end
        ) as issue_events,

        count(
            case
                when event_type = 'WatchEvent'
                then 1
            end
        ) as watch_events,

        count(
            case
                when event_type = 'ReleaseEvent'
                then 1
            end
        ) as release_events,

        count(
            case
                when is_bot = true
                then 1
            end
        ) as bot_events,

        count(
            case
                when is_bot = false
                then 1
            end
        ) as human_events

    from events

    group by event_date

)

select *
from daily_activity
order by event_date