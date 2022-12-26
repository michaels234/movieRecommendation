import pandas as pd
import numpy as np
import nltk
import time
from nltk.corpus import stopwords
import string
from nltk.stem.snowball import SnowballStemmer
from nltk.stem.porter import PorterStemmer
from nltk.stem import LancasterStemmer
#from sklearn.pipeline import Pipeline
#from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
#from sklearn.preprocessing import FunctionTransformer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
#import tfidf as tfidf
import json
import pickle

# the main issues with all this:
# i added the genres as words in the overviews. should i instead actually filter out by genre?
# the nlp needs to be able to understand similar words, like a movie about a mother and her son should be similar to a
# movie about a father and his daughter, or a movie about a thief and a movie about a heist.
# it needs to understand synonyms etc. Also like ate and eat and eaten, its the same but now its considered different.
# right now it gets rid of every capital word, but itd be better if it only got rid of names, because places and names
# of clubs or associations should be kept, and the starts of sentences. And famous names should be kept. A movie about
# Jesus should keep the name jesus in the overview, but a movie about a guy named Danny should remove Danny.

start_time = time.time()
print('START')
stemmer = SnowballStemmer("english")
stemmer2 = PorterStemmer()
stemmer3 = LancasterStemmer()


def get_movies():
	print('GET MOVIES')
	pd.options.display.max_colwidth = 220
	credits = pd.read_csv("tmdb_5000_credits.csv")
	movies = pd.read_csv("tmdb_5000_movies.csv")
	nltk.download("stopwords")
	credits_column_renamed = credits.rename(index=str, columns={"movie_id": "id"})
	movies = movies.merge(credits_column_renamed, on='id')
	movies = movies.drop(columns=['homepage', 'title_x', 'title_y', 'status','production_countries'])
	movies.dropna(subset=['overview', 'original_title'], inplace=True)
	movies.reset_index(drop=True, inplace=True)
	movies.drop_duplicates(subset=['original_title'], inplace=True)
	movies.reset_index(drop=True, inplace=True)
	return movies


def clean_movie_data(movies, genr_atio=.3, key_ratio=.3):
	global stemmer, stemmer2, stemmer3
	print('CLEAN MOVIE DATA')
	movies_cleaned = movies.copy(deep=True)
	movies_cleaned['overview'] = movies['overview'].apply(process)
	for movie_title in movies_cleaned['original_title']:
		index = movies_cleaned[movies_cleaned['original_title'] == movie_title].index[0]
		genres = json.loads(movies_cleaned[movies_cleaned['original_title'] == movie_title]['genres'].values[0])
		keywords = json.loads(movies_cleaned[movies_cleaned['original_title'] == movie_title]['keywords'].values[0])
		#print('keywords', keywords)
		# genr_atio = multiple1 * len(genres) / len(movies_cleaned.at[index, 'overview'].split()
		multiple1 = round(genr_atio * len(movies_cleaned.at[index, 'overview'].split()) / len(genres)) if len(genres) != 0 else 1
		multiple1 = multiple1 if multiple1 != 0 else 1
		multiple2 = round(key_ratio * len(movies_cleaned.at[index, 'overview'].split()) / len(keywords)) if len(keywords) != 0 else 1
		multiple2 = multiple2 if multiple2 != 0 else 1
		for genre in genres:
			word = stemmer.stem(stemmer2.stem(stemmer3.stem(genre["name"].lower())))
			movies_cleaned.at[index, 'overview'] = movies_cleaned.at[index, 'overview'] + f' {word}' * multiple1
		for keyword in keywords:
			for keyw in keyword["name"].split():
				word = stemmer.stem(stemmer2.stem(stemmer3.stem(keyw.lower())))
				movies_cleaned.at[index, 'overview'] = movies_cleaned.at[index, 'overview'] + f' {word}' * multiple2
		#print(movies_cleaned.at[index, 'overview'])
	return movies_cleaned


def fit_model(movies_cleaned, binary=True, use_idf=True, min_df=2, max_df=.9, save=False):
	tfv = TfidfVectorizer(token_pattern=r'\w{1,}', binary=binary, use_idf=use_idf, min_df=min_df, max_df=max_df, ngram_range=(1, 3), max_features=None)
	tfv_matrix = tfv.fit_transform(movies_cleaned['overview'])
	similarity_distance = 1 - cosine_similarity(tfv_matrix)
	if save:
		pickle.dump(similarity_distance, open('similarity_distance.pickle', 'wb'))
		print('SAVED')
	return similarity_distance


def process(text):
	global stemmer, stemmer2, stemmer3
	# remove punctuation
	text = text.replace('-', ' ')
	text = [char for char in text if char not in string.punctuation+"'"+"–"]
	text = ''.join(text)
	# remove stopwords
	text = [word for word in text.split() if word not in stopwords.words('english')]
	final = []
	for word in text:
		# only continue for non numeric non-capitalized words
		if not word[0].isupper() and not word.isnumeric() and word not in string.punctuation+"'"+"–":
			final.append(stemmer.stem(stemmer2.stem(stemmer3.stem(word))))
	return ' '.join(final)


def give_recomendations(movie, similarity_distance, movies):
	index = movies[movies['original_title'] == movie].index[0]
	output = 'SOURCE MOVIE:' + '\nTITLE: ' + movies["original_title"].iloc[index] + '\nDESCRIPTION: ' + movies["overview"].iloc[index] + '\n\nRECOMMENDATIONS:'
	for i in range(1, 11):
		ind = np.argsort(similarity_distance[index])[i]
		output += '\n\n#' + str(i) + '\nTITLE: ' + movies["original_title"].iloc[ind] + '\nDESCRIPTION: ' + movies["overview"].iloc[ind]
	return output


if __name__ == "__main__":
	movies = get_movies()
	
	# uncomment below to fit a particular hyperparameter setting
	binary, use_idf, min_df, max_df, genr_atio, key_ratio = False, False, 7, 0.7, 0.2, 0.1
	movies_cleaned = clean_movie_data(movies, genr_atio=genr_atio, key_ratio=key_ratio)
	print('FIT MODEL')
	similarity_distance = fit_model(movies_cleaned, binary=binary, use_idf=use_idf, min_df=min_df, max_df=max_df, save=True)
	devil_wears_prada_recs = give_recomendations('The Devil Wears Prada', similarity_distance, movies)
	mad_max_recs = give_recomendations('Mad Max: Fury Road', similarity_distance, movies)
	godfather_recs = give_recomendations('The Godfather', similarity_distance, movies)
	oceans_eleven_recs = give_recomendations("Ocean's Eleven", similarity_distance, movies)
	devil_wears_prada_goals = ['TITLE: Clueless\n', 'TITLE: The Women\n', 'TITLE: Morning Glory\n', 'TITLE: Legally Blonde', 'TITLE: Sex and the City', 'TITLE: The Proposal\n', 'Bridget Jones', 'TITLE: The Intern\n']
	mad_max_goals = ['TITLE: Mad Max Beyond Thunderdome\n', 'TITLE: Dredd\n', 'TITLE: The Book of Eli\n', 'TITLE: Mad Max 2', 'TITLE: Doomsday\n', 'TITLE: Waterworld\n', 'TITLE: Death Race\n', 'Riddick', 'TITLE: Mortal Engines\n']
	godfather_goals = ['TITLE: The Godfather: Part', 'TITLE: Goodfellas\n', 'TITLE: Casino\n', 'TITLE: Donnie Brasco\n', 'TITLE: Once Upon a Time in America\n', 'TITLE: Scarface\n', 'TITLE: The Departed\n', 'TITLE: Black Mass\n', 'TITLE: American Gangster\n']
	oceans_eleven_goals = ['TITLE: The Italian Job\n', 'TITLE: Snatch\n', "TITLE: Ocean's Twelve\n", "TITLE: Ocean's Thirteen\n", 'TITLE: Now You See Me\n', 'TITLE: Focus\n', 'TITLE: 21\n', 'TITLE: Leverage\n', 'TITLE: The Sting\n', 'TITLE: Catch Me If You Can\n']
	all_goals = oceans_eleven_goals + devil_wears_prada_goals + godfather_goals + mad_max_goals
	num_goals = len(all_goals)
	devil_wears_prada_TF = [el in devil_wears_prada_recs for el in devil_wears_prada_goals]
	mad_max_TF = [el in mad_max_recs for el in mad_max_goals]
	godfather_TF = [el in godfather_recs for el in godfather_goals]
	oceans_eleven_TF = [el in oceans_eleven_recs for el in oceans_eleven_goals]
	all_TF = oceans_eleven_TF + devil_wears_prada_TF + godfather_TF + mad_max_TF
	maxim = sum(all_TF)
	best = [binary, use_idf, min_df, max_df, genr_atio, key_ratio]
	print(f'Maximum: {maxim} {maxim/num_goals*100}%, Params: {best}, sum TF: [{sum(devil_wears_prada_TF)}, {sum(mad_max_TF)}, {sum(godfather_TF)}, {sum(oceans_eleven_TF)}]')

	## uncomment below to do hyperparameter tuning
	#f = open("written.txt", "w", encoding="utf-8")
	#maxim = 8
	#best = []
	#for genr_atio in [.15, .175, .2, .225, .25, .275, .3]:
	##for genr_atio in [.1, .2, .3, .4, .5, .6, .7, .8, .9, 1, 2]:
	#	for key_ratio in [.05, .075, .1, .125, .15, .175, .2]:
	#	#for key_ratio in [.1, .2, .3, .4, .5, .6, .7, .8, .9, 1, 2]:
	#		print(genr_atio, key_ratio)
	#		movies_cleaned = clean_movie_data(movies, genr_atio=genr_atio, key_ratio=key_ratio)
	#		print('FIT MODELS')
	#		#for binary in [True, False]:
	#		for binary in [False]:
	#			#for use_idf in [True, False]:
	#			for use_idf in [False]:
	#				#for min_df in [2, 5, 10, 20, 50, 100, .1, .2, .3]:
	#				for min_df in [5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]:
	#					#for max_df in [.99, .9, .8, .7, .6, .5, .4, .3, .2, .1, 100]:
	#					for max_df in [.99, .9, .8, .7, .6, .5, .4, .3, .2, .1]:
	#						try:
	#							min_check = min_df if min_df > 1 else min_df * len(movies)
	#							max_check = max_df if max_df > 1 else max_df * len(movies)
	#							if max_check < min_check:
	#								continue
	#							similarity_distance = fit_model(movies_cleaned, binary=binary, use_idf=use_idf, min_df=min_df, max_df=max_df, save=False)
	#							devil_wears_prada_recs = give_recomendations('The Devil Wears Prada', similarity_distance, movies)
	#							fight_club_recs = give_recomendations('Fight Club', similarity_distance, movies)
	#							mad_max_recs = give_recomendations('Mad Max: Fury Road', similarity_distance, movies)
	#							godfather_recs = give_recomendations('The Godfather', similarity_distance, movies)
	#							oceans_eleven_recs = give_recomendations("Ocean's Eleven", similarity_distance, movies)
	#							devil_wears_prada_goals = ['TITLE: Clueless\n', 'TITLE: The Women\n', 'TITLE: Morning Glory\n', 'TITLE: Legally Blonde', 'TITLE: Sex and the City', 'TITLE: The Proposal\n', 'Bridget Jones', 'TITLE: The Intern\n']
	#							mad_max_goals = ['TITLE: Mad Max Beyond Thunderdome\n', 'TITLE: Dredd\n', 'TITLE: The Book of Eli\n', 'TITLE: Mad Max 2', 'TITLE: Doomsday\n', 'TITLE: Waterworld\n', 'TITLE: Death Race\n', 'Riddick', 'TITLE: Mortal Engines\n']
	#							godfather_goals = ['TITLE: The Godfather: Part', 'TITLE: Goodfellas\n', 'TITLE: Casino\n', 'TITLE: Donnie Brasco\n', 'TITLE: Once Upon a Time in America\n', 'TITLE: Scarface\n', 'TITLE: The Departed\n', 'TITLE: Black Mass\n', 'TITLE: American Gangster\n']
	#							oceans_eleven_goals = ['TITLE: The Italian Job\n', 'TITLE: Snatch\n', "TITLE: Ocean's Twelve\n", "TITLE: Ocean's Thirteen\n", 'TITLE: Now You See Me\n', 'TITLE: Focus\n', 'TITLE: 21\n', 'TITLE: Leverage\n', 'TITLE: The Sting\n', 'TITLE: Catch Me If You Can\n']
	#							all_goals = oceans_eleven_goals + devil_wears_prada_goals + godfather_goals + mad_max_goals
	#							num_goals = len(all_goals)
	#							devil_wears_prada_TF = [el in devil_wears_prada_recs for el in devil_wears_prada_goals]
	#							mad_max_TF = [el in mad_max_recs for el in mad_max_goals]
	#							godfather_TF = [el in godfather_recs for el in godfather_goals]
	#							oceans_eleven_TF = [el in oceans_eleven_recs for el in oceans_eleven_goals]
	#							all_TF = oceans_eleven_TF + devil_wears_prada_TF + godfather_TF + mad_max_TF
	#							#if 'The Omen' not in devil_wears_prada_rec and 'Go for It!' not in fight_club_rec and 'Copying Beethoven' not in fight_club_rec and 'High School Musical' not in fight_club_rec and 'Legally Blonde' not in fight_club_rec and 'Creed' in fight_club_rec and 'Agent Cody Banks' not in fight_club_rec:
	#							if (sum(devil_wears_prada_TF)>=2 and sum(mad_max_TF)>=2 and sum(godfather_TF)>=2 and sum(oceans_eleven_TF)>=2):
	#								if sum(all_TF) >= maxim:
	#									maxim = sum(all_TF)
	#									best = [binary, use_idf, min_df, max_df, genr_atio, key_ratio]
	#									print(f'NEW BEST! Maximum: {maxim} {maxim/num_goals*100}%, Params: {best}, sum TF: [{sum(devil_wears_prada_TF)}, {sum(mad_max_TF)}, {sum(godfather_TF)}, {sum(oceans_eleven_TF)}]')
	#									f.write(f'\n\nNEW BEST! Maximum: {maxim} {maxim/num_goals*100}%, Params: [{best}], sum TF: [{sum(devil_wears_prada_TF)}, {sum(mad_max_TF)}, {sum(godfather_TF)}, {sum(oceans_eleven_TF)}]')
	#									f.write(devil_wears_prada_recs)
	#									f.write(f'\n\nNEW BEST! Maximum: {maxim} {maxim/num_goals*100}%, Params: [{best}], sum TF: [{sum(devil_wears_prada_TF)}, {sum(mad_max_TF)}, {sum(godfather_TF)}, {sum(oceans_eleven_TF)}]')
	#									f.write(fight_club_recs)
	#									f.write(f'\n\nNEW BEST! Maximum: {maxim} {maxim/num_goals*100}%, Params: [{best}], sum TF: [{sum(devil_wears_prada_TF)}, {sum(mad_max_TF)}, {sum(godfather_TF)}, {sum(oceans_eleven_TF)}]')
	#									f.write(mad_max_recs)
	#									f.write(f'\n\nNEW BEST! Maximum: {maxim} {maxim/num_goals*100}%, Params: [{best}], sum TF: [{sum(devil_wears_prada_TF)}, {sum(mad_max_TF)}, {sum(godfather_TF)}, {sum(oceans_eleven_TF)}]')
	#									f.write(godfather_recs)
	#									f.write(f'\n\nNEW BEST! Maximum: {maxim} {maxim/num_goals*100}%, Params: [{best}], sum TF: [{sum(devil_wears_prada_TF)}, {sum(mad_max_TF)}, {sum(godfather_TF)}, {sum(oceans_eleven_TF)}]')
	#									f.write(oceans_eleven_recs)
	#						except ValueError:
	#							continue
	#f.close()
