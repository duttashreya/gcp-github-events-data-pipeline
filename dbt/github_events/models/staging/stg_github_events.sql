{{ config(materialized='view') }}

with source_data as (

    select
        event_id,
        event_type,
        actor,
        repo,
        payload,
        is_public,
        created_at,
        raw_event,
        ingestion_timestamp,

        row_number() over (
            partition by event_id
            order by ingestion_timestamp desc, created_at desc
        ) as row_num

    from main.raw_github_events

),

staged as (

    select
        event_id,

        event_type,

        json_extract_string(actor, '$.login') as actor_login,

        cast(
            json_extract(actor, '$.id') as bigint
        ) as actor_id,

        json_extract_string(repo, '$.name') as repository_name,

        cast(
            json_extract(repo, '$.id') as bigint
        ) as repository_id,

        json_extract_string(repo, '$.url') as repository_url,

        is_public,

        created_at,

        ingestion_timestamp

    from source_data

    where row_num = 1

)

select *
from staged