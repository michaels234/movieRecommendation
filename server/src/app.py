from flask import Flask, request, render_template
import pickle
import os
from main import data, give_recomendations

app = Flask(__name__)

#saved = pickle.load(open('saved_model', 'rb'))
#similarity_distance, movies_cleaned = data(saved)
#while 1:
#	inp = input('Input Movie: ')
#	give_recomendations(inp, similarity_distance, movies_cleaned)


@app.route('/')
def home():
	context = {'prediction_text': 'Not Yet'}
	return render_template('index.html', context=context)


@app.route('/predict', methods=['POST'])
def predict():
	"""Grabs the input values and uses them to make prediction"""
	movie = request.form["movie"]
	saved = pickle.load(open('saved_model', 'rb'))
	similarity_distance, movies_cleaned = data(saved)
	output = give_recomendations(movie, similarity_distance, movies_cleaned)
	context = {'prediction_text': output}
	return render_template('index.html', context=context)


if __name__ == "__main__":
    app.run(debug=True,host='0.0.0.0',port=int(os.environ.get('PORT', 8080)))
