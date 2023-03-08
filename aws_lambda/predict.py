import json
import os
import boto3


#@app.route('/predict', methods=['GET'])
def lambda_handler(event, context):
	ind = event['ind']
	movie_list = list_similar_movies_from_ind(ind)
	return {
	    "statusCode": 200,
	    "headers": {
	        "Content-Type": "application/json"
	    },
	    "body": json.dumps(list_to_output(movie_list))
	}


def list_to_output(movie_list):
	output = 'SOURCE MOVIE:' + '\nTITLE: ' + movie_list[0]['title'] + '\nDESCRIPTION: ' + movie_list[0]['overview'] + '\n\nRECOMMENDATIONS:'
	for i in range(1, 11):
		output += '\n\n#' + str(i) + '\nTITLE: ' + movie_list[i]['title'] + '\nDESCRIPTION: ' + movie_list[i]['overview']
	return {'prediction_text': output}


	
def list_similar_movies_from_ind(ind):
	dynamodb = dynamo_connect()
	table = dynamodb.Table('movies')

	response = table.get_item(
		Key={'ind': str(ind)},
		ProjectionExpression='similarity_indices'
	)
	similarity_indices = tuple(response['Item']['similarity_indices'].split(', '))

	items = []
	for ind in similarity_indices:
		items.append(table.get_item(
			Key={'ind': ind},
			ProjectionExpression='ind, title, overview',
		)['Item'])

	unordered = {str(item['ind']): {'title': item['title'], 'overview': item['overview']} for item in items}
	return [unordered[str(ind)] for ind in similarity_indices]


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
