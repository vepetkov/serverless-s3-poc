from __future__ import print_function

import os

import snowflake.connector


def s3_file_created(event, context):
    """Extract metadata from object modification events for a bucket and store them in an audit table in Snowflake."""
    values = []
    for record in event['Records']:
        event_name = record['eventName'].replace('ObjectCreated:', '')
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']
        size = record['s3']['object']['size']
        time = record['eventTime']
        user_id = record['userIdentity']['principalId']

        # Skip all temporary files from the Hadoop distcp cmd
        if ".distcp.tmp.attempt" in key: 
            continue

        val = f"('{bucket}', '{key}', '{size}', '{time}', '{user_id}', '{event_name}')"
        values.append(val)

    if len(values) > 0:
        # Dump all metadata to Snowflake
        print(values)
        conn = snowflake.connector.connect(
            account=os.environ['SNOWSQL_ACCOUNT'],
            user=os.environ['SNOWSQL_USER'],
            password=os.environ['SNOWSQL_PWD'],
            authenticator='snowflake',
            warehouse=os.environ['SNOWSQL_WAREHOUSE'],
            role=os.environ['SNOWSQL_ROLE'],
            database=os.environ['SNOWSQL_DATABASE'],
            schema=os.environ['SNOWSQL_SCHEMA']
        )
        try:
            values_str = ','.join(values)
            insert_query = f"INSERT INTO S3_SUBS_INGEST_TIMES(BUCKET, OBJ_KEY, SIZE, LMOD_DT, USER_ID, EVENT_NAME) VALUES{values_str};"
            print(f"Running query: {insert_query}")

            conn.cursor().execute(insert_query)
        finally:
            conn.close()

    return {
        'status': f"Processed {len(values)} record(s)!"
    }
