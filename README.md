# Serverless PoC
A proof of concept for an event-based pipeline for extracting upload/modification times of files stored in AWS S3. 

The PoC uses the Serverless framework to create an AWS Lambda function that will be triggered on new S3 events (e.g. Object Creation) from an *existing* bucket. The Lambda function will extract the meta data from the event and persist it to a table in Snowflake for auditing purpose. 


## Init Setup
### Credenials
Setup AWS Credentials in `$HOME/aws/credentials` or use the following helper cmd from Serverless:
```
serverless config credentials --provider aws --key <aws_access_key_id> --secret <aws_secret_access_key>
```

All passwords used within the service need to be properly secured. The easiest way, when running on AWS, is to use the AWS SSM Parameter Store (_or AWS Secrets Manager but that is a paid service_). Passwords and other config options can be centrally stored in that service using:
```
# Create non-sensitive config as plain text strings
aws ssm put-parameter --name /serverless/dev/snowsql/acct --value "serverlesspoc" --type String
aws ssm put-parameter --name /serverless/dev/snowsql/db --value "dev" --type String
aws ssm put-parameter --name /serverless/dev/snowsql/schema --value "poc" --type String
aws ssm put-parameter --name /serverless/dev/snowsql/warehouse --value "dev" --type String
aws ssm put-parameter --name /serverless/dev/snowsql/role --value "devuser" --type String

## Create pass as encrypted strings (using the default KMS master key)
aws ssm put-parameter --name /serverless/dev/snowsql/user --value '<USER>' --type SecureString
aws ssm put-parameter --name /serverless/dev/snowsql/pass --value '<PASS>' --type SecureString
```


### Snowflake table
```
CREATE OR REPLACE TABLE S3_SUBS_INGEST_TIMES (
  ID BIGINT AUTOINCREMENT,
	BUCKET STRING,
	OBJ_KEY STRING,
	SIZE BIGINT,
	LMOD_DT TIMESTAMP_TZ(9),
	USER_ID STRING,
  EVENT_NAME STRING
)
COPY GRANTS
COMMENT='S3 ObjectCreated:* notifications for a bucket'
;
```


### Serverless Project
Initialize a new project in the current 
```
serverless create --template aws-python3 --name file-watcher

# Setup a new venv to keep it clean
python3 -m venv venv

# Activate the virtual env
source venv/bin/activate

# Install all required packages in the virtual env
pip install -r requirements.txt 
```

Install extra Serverless plugins:
```
npm install
```

## Deploy to AWS
When you deploy a Service, all of the Functions, Events and Resources in your serverless.yml are translated to an AWS CloudFormation template and deployed as a single CloudFormation stack:
```
serverless deploy -v
```

Bind events to any pre-existing S3 buckets (i.e. not created within the Serverless framework):
```
serverless s3deploy -v
```

## Run a function using dummy data
Use the dummy S3 notification event to test the *deployed* Lambda function:
```
serverless invoke -p s3-file-event.json --function s3FileCreated --log
```

Use the dummy S3 notification event to test the function locally (no deployment):
```
serverless invoke local -p s3-file-event.json --function s3FileCreated --log
```

## Get the logs for deployed functions
* s3FileCreated: `serverless logs -f s3FileCreated --tail`
* s3FileCreatedExistingBucket: `serverless logs -f s3FileCreatedExistingBucket --tail`

## Remove a deployment
If a deployment is no longer needed, running the following will remove all Functions, Events and Resources that were created from the Serverless framework:
```
serverless remove 
```