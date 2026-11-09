{{ config(materialized='view') }}

with source_data as (

    select *
    from {{ ref('stg_github_events') }}

),

enriched as (

    select
        event_id,
        event_type,
        actor_login,
        actor_id,
        repository_name,
        repository_id,
        repository_url,
        is_public,
        created_at,
        ingestion_timestamp,

        cast(created_at as date) as event_date,

        extract(hour from created_at) as event_hour,

        split_part(repository_name, '/', 1) as repository_owner,

        split_part(repository_name, '/', 2) as repository_name_only,

        case
            when lower(actor_login) like '%[bot]%'
                then true
            else false
        end as is_bot,

        case
            when event_type in (
                'PushEvent',
                'CreateEvent',
                'DeleteEvent'
            )
                then 'code_activity'

            when event_type in (
                'PullRequestEvent',
                'PullRequestReviewEvent',
                'PullRequestReviewCommentEvent'
            )
                then 'pull_request_activity'

            when event_type in (
                'IssuesEvent',
                'IssueCommentEvent'
            )
                then 'issue_activity'

            when event_type = 'WatchEvent'
                then 'repository_engagement'

            when event_type = 'ReleaseEvent'
                then 'release_activity'

            else 'other'
        end as event_category

    from source_data

)

select *
from enriched