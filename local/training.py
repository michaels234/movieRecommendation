import time
import nltk
from nltk.corpus import stopwords
import string
from nltk.stem.snowball import SnowballStemmer
from nltk.stem.porter import PorterStemmer
from nltk.stem import LancasterStemmer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from local_db import DataBase
from aws_lambda.predict import list_to_output
import sys
import numpy as np
import re
import json

# things that would improve the model:
# i added the genres as words in the overviews. should i instead actually filter out by genre?
# the nlp needs to be able to understand similar words, like a movie about a mother and her son should be similar to a
# movie about a father and his daughter, or a movie about a thief and a movie about a heist.
# it needs to understand synonyms etc. Also congugations etc. like ate and eat and eaten, its the same but now its considered different.
# right now it gets rid of every capital word, but itd be better if it only got rid of characters' names, because places and names
# of clubs or associations should be kept, and the starts of sentences. And famous names should be kept. A movie about
# Jesus should keep the name Jesus in the overview, but a movie about a guy named Danny should remove Danny.


class Hyperparameters():
	def __init__(self):
		self.genre_ratio = 0.2
		self.key_ratio = 0.1
		self.binary = False
		self.use_idf = False
		self.min_df = 7
		self.max_df = 0.7
		self.token_length = 2
	
	def setter(self, params):
		if 'genre_ratio' in params: self.genre_ratio = params['genre_ratio']
		if 'key_ratio' in params: self.key_ratio = params['key_ratio']
		if 'binary' in params: self.binary = params['binary']
		if 'use_idf' in params: self.use_idf = params['use_idf']
		if 'min_df' in params: self.min_df = params['min_df']
		if 'max_df' in params: self.max_df = params['max_df']
		if 'token_length' in params: self.token_length = params['token_length']
	
	def lister(self):
		return self.genre_ratio, self.key_ratio, self.binary, self.use_idf, self.min_df, self.max_df, self.token_length


class MachineLearning():

	def get_fittable_words(self):
		# get fittable words using particular hyperparameter settings
		if self.tuning:
			all_movie_data = self.db.list_all_movie_data()
			all_fittable_words = []
		else:
			print('GETTING FITTABLE WORDS')
		for ind in range(self.movie_count):  # for every movie
			# get movie from ind
			if self.tuning:
				movie_data = all_movie_data[ind]
			else:
				movie_data = self.db.get_movie(ind)
			# change movie data from tuple to dict with column names
			columns = ['ind', 'title', 'clean_title', 'year', 'overview', 'genres', 'keywords', 'fittable_words', 'similarity_indicies']
			movie = {column: movie_data[i] for i, column in enumerate(columns)}

			# get fittable words
			def clean_characters(text):
				# remove punctuation
				text = text.replace('-', ' ').replace("'", '')
				text = [char for char in text if char not in string.punctuation]
				text = ''.join(text)
				# remove stopwords
				text = [word for word in text.split() if word not in stopwords.words('english')]
				final = []
				for word in text:
					# only continue for non numeric non-capitalized words
					if not word[0].isupper() and not word.isnumeric() and word not in string.punctuation:
						final.append(self.stemmer.stem(self.stemmer2.stem(self.stemmer3.stem(word))))
				return ' '.join(final)

			fittable_words = clean_characters(movie['overview'])
			genres = movie['genres'].split(',')
			keywords = movie['keywords'].split(',')
			multiple1 = round(self.hp.genre_ratio * len(fittable_words.split()) / len(genres)) if len(genres) != 0 else 1
			multiple1 = multiple1 if multiple1 != 0 else 1
			multiple2 = round(self.hp.key_ratio * len(fittable_words.split()) / len(keywords)) if len(keywords) != 0 else 1
			multiple2 = multiple2 if multiple2 != 0 else 1
			for genre in genres:
				word = self.stemmer.stem(self.stemmer2.stem(self.stemmer3.stem(genre.lower().replace('-',' ').strip())))
				if word:
					fittable_words += f' {word}' * multiple1
			for keyword in keywords:
				for keyw in keyword.split():
					word = self.stemmer.stem(self.stemmer2.stem(self.stemmer3.stem(keyw.lower().replace('-',' ').strip())))
					if word:
						fittable_words += f' {word}' * multiple2
			if self.tuning:
				all_fittable_words += [fittable_words]
			else:
				# update fittable words in database
				self.db.update_movie_fittable_words(ind, fittable_words)
		if self.tuning:
			self.all_fittable_words = all_fittable_words

	def fit_model(self):
		if self.tuning:
			all_fittable_words = self.all_fittable_words
		else:
			print('FITTING MODEL')
			# get list fittable words for all movies
			all_fittable_words = self.db.list_all_fittable_words()
		# fit using particular hyperparameter settings
		tfv = TfidfVectorizer(
			token_pattern=re.compile(f'\\b\\w{{{self.hp.token_length},}}\\b'),
			binary=self.hp.binary,
			use_idf=self.hp.use_idf,
			min_df=self.hp.min_df,
			max_df=self.hp.max_df,
			ngram_range=(1, 3),
			max_features=None
		)
		tfv_matrix = tfv.fit_transform(all_fittable_words)
		similarity_distance = 1 - cosine_similarity(tfv_matrix)
		if self.tuning:
			similarity_indices = []
		else:
			print('SAVING SIMILARITY INDICIES')
			# save whole similarity distance matrix for later, just in case (tho I don't use it anywhere)
			np.save('similarity_distance.npy', similarity_distance)
		for ind in range(self.movie_count):  # for every movie
			if self.tuning:
				similarity_indices += [tuple(np.argsort(similarity_distance[ind])[:11])]
			else:
				# save 11 (10 + itself) similar movies' indicies
				sorted = ', '.join(map(str, np.argsort(similarity_distance[ind])[:11]))
				# update similarity indices for this movie in the database
				self.db.update_movie_similarity_indices(ind, sorted)
		if self.tuning:
			self.similarity_indices = similarity_indices

	def results(self):

		def get_output(ind):
			if self.tuning:
				movie_list = self.db.get_title_overview_from_ind_list(self.similarity_indices[ind])
				return list_to_output(movie_list)['prediction_text']
			else:
				with app.test_request_context('/predict', method='GET', query_string=f'ind={ind}'):
					return json.loads(predict().data)['prediction_text']

		# see results for confirmation
		devil_wears_prada_recs = get_output(1366)  # The Devil Wears Prada
		mad_max_recs = get_output(127)  # Mad Max: Fury Road
		godfather_recs = get_output(3336)  # The Godfather
		oceans_eleven_recs = get_output(388)  # Ocean's Eleven
		devil_wears_prada_goals = ['TITLE: Clueless\n', 'TITLE: The Women\n', 'TITLE: Morning Glory\n', 'TITLE: Legally Blonde', 'TITLE: Sex and the City', 'TITLE: The Proposal\n', 'Bridget Jones', 'TITLE: The Intern\n']
		mad_max_goals = ['TITLE: Mad Max Beyond Thunderdome\n', 'TITLE: Dredd\n', 'TITLE: The Book of Eli\n', 'TITLE: Mad Max 2', 'TITLE: Doomsday\n', 'TITLE: Waterworld\n', 'TITLE: Death Race\n', 'Riddick', 'TITLE: Mortal Engines\n']
		godfather_goals = ['TITLE: The Godfather: Part', 'TITLE: Goodfellas\n', 'TITLE: Casino\n', 'TITLE: Donnie Brasco\n', 'TITLE: Once Upon a Time in America\n', 'TITLE: Scarface\n', 'TITLE: The Departed\n', 'TITLE: Black Mass\n', 'TITLE: American Gangster\n']
		oceans_eleven_goals = ['TITLE: The Italian Job\n', 'TITLE: Snatch\n', "TITLE: Ocean's Twelve\n", "TITLE: Ocean's Thirteen\n", 'TITLE: Now You See Me\n', 'TITLE: Focus\n', 'TITLE: 21\n', 'TITLE: Leverage\n', 'TITLE: The Sting\n', 'TITLE: Catch Me If You Can\n']
		num_goals = (len(devil_wears_prada_goals)+1) * (len(mad_max_goals)+1) * (len(godfather_goals)+1) * (len(oceans_eleven_goals)+1)
		devil_wears_prada_TF = [el in devil_wears_prada_recs for el in devil_wears_prada_goals]
		mad_max_TF = [el in mad_max_recs for el in mad_max_goals]
		godfather_TF = [el in godfather_recs for el in godfather_goals]
		oceans_eleven_TF = [el in oceans_eleven_recs for el in oceans_eleven_goals]
		all_TF = (sum(oceans_eleven_TF)+1) * (sum(devil_wears_prada_TF)+1) * (sum(godfather_TF)+1) * (sum(mad_max_TF)+1)
		maxim = all_TF
		best = self.hp.lister()
		if not self.tuning:
			print(f'Maximum: {maxim} {maxim/num_goals*100}%, Params: {best}, sum TF: [{sum(devil_wears_prada_TF)}, {sum(mad_max_TF)}, {sum(godfather_TF)}, {sum(oceans_eleven_TF)}]')
		return devil_wears_prada_TF, mad_max_TF, godfather_TF, oceans_eleven_TF, all_TF, num_goals, devil_wears_prada_recs, mad_max_recs, godfather_recs, oceans_eleven_recs

	def __init__(self, tuning):
		self.start_time = time.time()
		print('START')
		self.stemmer = SnowballStemmer("english")
		self.stemmer2 = PorterStemmer()
		self.stemmer3 = LancasterStemmer()
		nltk.download("stopwords")
		self.tuning = tuning

		self.db = DataBase()
		self.movie_count = self.db.get_movie_count()
		self.hp = Hyperparameters()

		if not self.tuning:
			self.get_fittable_words()
			self.fit_model()
			self.results()
		else:
			# hyperparameter tuning (*warning* very long calculation)
			print('HYPERPARAMETER TUNING')
			with open("written.txt", "w", encoding="utf-8") as f:
				maxim = 8
				best = []
				#for genre_ratio in [.1, .2, .3, .4, .5, .6, .7, .8, .9, 1, 2]:
				#for genre_ratio in [.15, .175, .2, .225, .25, .275, .3]:
				for genre_ratio in [.2, .25]:
					#for key_ratio in [.1, .2, .3, .4, .5, .6, .7, .8, .9, 1, 2]:
					#for key_ratio in [.05, .075, .1, .125, .15, .175, .2]:
					for key_ratio in [.05, .1, .15]:
						self.hp.setter({'genre_ratio': genre_ratio, 'key_ratio': key_ratio})
						self.get_fittable_words()
						#for min_df in [2, 5, 10, 20, 50, 100, .1, .2, .3]:
						#for min_df in [5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]:
						for min_df in [5, 6, 7, 8, 9]:
							#for max_df in [.99, .9, .8, .7, .6, .5, .4, .3, .2, .1, 100]:
							#for max_df in [.99, .9, .8, .7, .6, .5, .4, .3, .2, .1]:
							for max_df in [.8, .7, .6]:
								for token_length in [1, 2, 3, 4]:
									#for binary in [True, False]:
									binary = False
									#for use_idf in [True, False]:
									use_idf = False
									try:
										min_check = min_df if min_df > 1 else min_df * self.movie_count
										max_check = max_df if max_df > 1 else max_df * self.movie_count
										if max_check < min_check:
											continue
										
										self.hp.setter({'binary': binary, 'use_idf': use_idf, 'min_df': min_df, 'max_df': max_df, 'token_length': token_length})
										self.fit_model()
										devil_wears_prada_TF, mad_max_TF, godfather_TF, oceans_eleven_TF, all_TF, num_goals, devil_wears_prada_recs, mad_max_recs, godfather_recs, oceans_eleven_recs = self.results()
										#if 'The Omen' not in devil_wears_prada_rec and 'Go for It!' not in fight_club_rec and 'Copying Beethoven' not in fight_club_rec and 'High School Musical' not in fight_club_rec and 'Legally Blonde' not in fight_club_rec and 'Creed' in fight_club_rec and 'Agent Cody Banks' not in fight_club_rec:
										#if (sum(devil_wears_prada_TF)>=2 and sum(mad_max_TF)>=2 and sum(godfather_TF)>=2 and sum(oceans_eleven_TF)>=2):
										if all_TF >= maxim:
											maxim = all_TF
											best = self.hp.lister()
											print(f'NEW BEST! Maximum: {maxim} {maxim/num_goals*100}%, Params: {best}, sum TF: [{sum(devil_wears_prada_TF)}, {sum(mad_max_TF)}, {sum(godfather_TF)}, {sum(oceans_eleven_TF)}]')
											f.write(f'\n\nNEW BEST! Maximum: {maxim} {maxim/num_goals*100}%, Params: [{best}], sum TF: [{sum(devil_wears_prada_TF)}, {sum(mad_max_TF)}, {sum(godfather_TF)}, {sum(oceans_eleven_TF)}]')
											f.write(devil_wears_prada_recs)
											f.write(f'\n\nNEW BEST! Maximum: {maxim} {maxim/num_goals*100}%, Params: [{best}], sum TF: [{sum(devil_wears_prada_TF)}, {sum(mad_max_TF)}, {sum(godfather_TF)}, {sum(oceans_eleven_TF)}]')
											f.write(mad_max_recs)
											f.write(f'\n\nNEW BEST! Maximum: {maxim} {maxim/num_goals*100}%, Params: [{best}], sum TF: [{sum(devil_wears_prada_TF)}, {sum(mad_max_TF)}, {sum(godfather_TF)}, {sum(oceans_eleven_TF)}]')
											f.write(godfather_recs)
											f.write(f'\n\nNEW BEST! Maximum: {maxim} {maxim/num_goals*100}%, Params: [{best}], sum TF: [{sum(devil_wears_prada_TF)}, {sum(mad_max_TF)}, {sum(godfather_TF)}, {sum(oceans_eleven_TF)}]')
											f.write(oceans_eleven_recs)
									except ValueError:
										continue


if __name__ == "__main__":  # to tune, just include any argument when running
	tuning = len(sys.argv) > 1
	machine_learning = MachineLearning(tuning)
