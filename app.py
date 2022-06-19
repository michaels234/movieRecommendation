from flask import Flask, request, render_template, jsonify
import pickle
import os
from main import get_movies, give_recomendations

app = Flask(__name__)

@app.route('/')
def home():
	context = {'prediction_text': 'Not Yet'}
	return render_template('index.html', context=context)


@app.route('/movies', methods=['GET'])
def movies():
	movies = get_movies()
	data = {'movies': movies['original_title'].to_numpy().tolist()}
	return jsonify(data)


@app.route('/predict', methods=['POST'])
def predict():
	movies = get_movies()
	request_data = request.get_json()
	movie = request_data['movie']
	similarity_distance = pickle.load(open('similarity_distance.pickle', 'rb'))
	output = give_recomendations(movie, similarity_distance, movies)
	data = {'prediction_text': output}
	return jsonify(data)


if __name__ == "__main__":
	app.run(debug=True,host='0.0.0.0',port=int(os.environ.get('PORT', 8080)))
