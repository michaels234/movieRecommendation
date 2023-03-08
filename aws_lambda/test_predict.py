from predict import lambda_handler


results = lambda_handler({'ind': 1}, {})
print(f"{len(results)=}\n{results=}")