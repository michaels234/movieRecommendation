import json
import os
import boto3


def lambda_handler(event, context):
	# return list of title + year for all movies in db
	select_response = list_titles()
	return {
	    "statusCode": 200,
	    "headers": {
	        "Content-Type": "application/json"
	    },
	    "body": json.dumps(select_response)
	}


def list_titles():
	dynamodb = dynamo_connect()
	table = dynamodb.Table('movies')

	items = []
	response = table.scan(
		ProjectionExpression='ind, title, #yr',
		ExpressionAttributeNames={'#yr': 'year'}
	)
	items.extend(response['Items'])
	while True:
		if 'LastEvaluatedKey' not in response:
			break
		response = table.scan(
			ProjectionExpression='ind, title, #yr',
			ExpressionAttributeNames={'#yr': 'year'},
			ExclusiveStartKey=response['LastEvaluatedKey']
		)
		items.extend(response['Items'])

	return [{'ind': item['ind'], 'titleYear': item['title'] + f" ({item['year']})"} for item in items]


def dynamo_connect():
	if 'ENV' not in os.environ or ('ENV' in os.environ and os.environ.get('ENV') == 'DEV'):
		# Local Development Environment
		from dotenv import load_dotenv
		load_dotenv()

		session = boto3.Session(
			region_name='us-east-1',
			aws_access_key_id=os.environ.get('DYNAMODB_ACCESS_KEY'),
			aws_secret_access_key=os.environ.get('DYNAMODB_SECRET_ACCESS_KEY'),
		)
	else:
		# AWS Production Environment
		session = boto3.Session(
			region_name='us-east-1',
		)

	return session.resource('dynamodb')
