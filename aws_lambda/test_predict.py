import json
from predict import lambda_handler


results = lambda_handler({'ind': 1}, {})
output = json.loads(results['body'])['prediction_text'].split('\n\n')
length = len(output)
print(f"{length=}\n{output=}")
