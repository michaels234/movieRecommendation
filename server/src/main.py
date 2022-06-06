import pandas as pd
import numpy as np
import nltk
import time
from nltk.corpus import stopwords
import string
from nltk.stem.snowball import SnowballStemmer
#from sklearn.pipeline import Pipeline
#from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
#from sklearn.preprocessing import FunctionTransformer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import pickle
import tfidf as tfidf
import json

# the main issues with all this:
# i added the genres as words in the overviews. should i instead actually filter out by genre?
# the nlp needs to be able to understand similar words, like a movie about a mother and her son should be similar to a
# movie about a father and his daughter, or a movie about a thief and a movie about a heist.
# it needs to understand synonyms etc. Also like ate and eat and eaten, its the same but now its considered different.
# right now it gets rid of every capital word, but itd be better if it only got rid of names, because places and names
# of clubs or associations should be kept, and the starts of sentences. And famous names should be kept. A movie about
# Jesus should keep the name jesus in the overview, but a movie about a guy named Danny should remove Danny.

stemmer = SnowballStemmer("english")
start_time = time.time()


def data(saved=[]):
	pd.options.display.max_colwidth = 220
	credits = pd.read_csv("tmdb_5000_credits.csv")
	movies = pd.read_csv("tmdb_5000_movies.csv")
	nltk.download("stopwords")
	credits_column_renamed = credits.rename(index=str, columns={"movie_id": "id"})
	movies_merge = movies.merge(credits_column_renamed, on='id')
	movies_cleaned = movies_merge.drop(columns=['homepage', 'title_x', 'title_y', 'status','production_countries'])
	movies_cleaned.dropna(subset=['overview', 'original_title'], inplace=True)
	movies_cleaned.reset_index(drop=True, inplace=True)
	movies_cleaned.drop_duplicates(subset=['original_title'], inplace=True)
	movies_cleaned.reset_index(drop=True, inplace=True)
	#input()
	if saved is None:
		movies_cleaned['overview'] = movies_cleaned['overview'].apply(process)
		genre_overview_ratio = 0
		# add the genres and the keywords into the overviews
		for movie_title in movies_cleaned['original_title']:
			index = movies_cleaned[movies_cleaned['original_title'] == movie_title].index[0]
			genres = json.loads(movies_cleaned[movies_cleaned['original_title'] == movie_title]['genres'].values[0])
			multiple = round(genre_overview_ratio * len(movies_cleaned.at[index, 'overview'].split()) / len(genres)) if len(genres) != 0 else 1
			multiple = multiple if multiple != 0 else 1
			for genre in genres:
				movies_cleaned.at[index, 'overview'] = movies_cleaned.at[index, 'overview'] + f' {genre["name"].lower()}' * multiple
			#for keyword in json.loads(movies_cleaned[movies_cleaned['original_title'] == movie_title]['keywords'].values[0]):
			#	movies_cleaned.at[index, 'overview'] = movies_cleaned.at[index, 'overview'] + f' {keyword["name"].lower()}'
		print('MACHINE LEARNING')
		# key important details I've found here
		# its best to increase min_df a bit, to make sure very rare words aren't allowed to have too strong of an effect
		# also good to decrease max_df quite a bit, to make sure words that are in X% or more of movies are deemed unimportant
		# and i think binary=True is good, since just because "heist" is used once in a sentence, doesn't make it less important than other words
		tfv = TfidfVectorizer(token_pattern=r'\w{1,}', binary=True, use_idf=False, min_df=1, max_df=.5, ngram_range=(1, 3), max_features=None)
		tfv_matrix = tfv.fit_transform(movies_cleaned['overview'])
		#tfv_matrix = tfidf.fit_transform(movies_cleaned['overview'])  # mine
		similarity_distance = 1 - cosine_similarity(tfv_matrix)
		pickle.dump(similarity_distance, open('saved_model', 'wb'))

		# old version with sigmoid instead of cosine
		#sig = sigmoid_kernel(tfv_matrix, tfv_matrix)
		#indices = pd.Series(range(len(movies_cleaned['original_title'])), index=movies_cleaned['original_title'])
		#idx = indices[title]
		#sig_scores = list(enumerate(sig[idx]))
		#sig_scores = sorted(sig_scores, key=lambda x: x[1], reverse=True)
		#sig_scores = sig_scores[1:11]
		#movie_indices = [i[0] for i in sig_scores]
		#print('TITLE: ' + movies_cleaned["original_title"].iloc[idx] + '.   OVERVIEW: ' + movies_cleaned["overview"].iloc[idx])
		#print('TITLE: ' + movies_cleaned["original_title"].iloc[movie_indices] + '.   OVERVIEW: ' + movies_cleaned["overview"].iloc[movie_indices])
	else:
		similarity_distance = saved
	return similarity_distance, movies_cleaned


def process(text):
	# remove punctuation
	nopunc = [char for char in text if char not in string.punctuation]
	nopunc = ''.join(nopunc)
	# remove stopwords
	nopunc = [word for word in nopunc.split() if word not in stopwords.words('english')]
	final = []
	for word in nopunc:
		# only continue for non numeric non-capitalized words
		if not word[0].isupper() and not word.isnumeric():
			final.append(stemmer.stem(word))
	#if 'Max' in text and 'apocalyptic' in text and 'desert' in text:
	#	print('MAD MAX', ' '.join(final))
	#if 'Danny' in text and 'Ocean' in text:
	#	print('OCEANS', final)
	#if 'An' in text and 'epic' in text and 'love' in text and 'story' in text and 'centered' in text and 'around' in text and 'an' in text and 'older' in text and 'man' in text:
	#	print(' '.join(final))
	return ' '.join(final)


def give_recomendations(title, similarity_distance, movies_cleaned):
	index = movies_cleaned[movies_cleaned['original_title'] == title].index[0]
	output = '\nSOURCE MOVIE:' + '\nTITLE: ' + movies_cleaned["original_title"].iloc[index] + '\nDESCRIPTION: ' + movies_cleaned["overview"].iloc[index]
	#print('\nSOURCE MOVIE:', '\nTITLE: ', movies_cleaned["original_title"].iloc[index], '\nDESCRIPTION: ', movies_cleaned["overview"].iloc[index])
	for i in range(1, 11):
		ind = np.argsort(similarity_distance[index])[i]
		#print('\n', i, '\nTITLE:', movies_cleaned["original_title"].iloc[ind], '\nDESCRIPTION:', movies_cleaned["overview"].iloc[ind])
		output += '\n\n' + str(i) + '\nTITLE:' + movies_cleaned["original_title"].iloc[ind] + '\nDESCRIPTION:' + movies_cleaned["overview"].iloc[ind]
	return output


#if sys.argv[1] == '1':
#	print('FROM FILE')
#	saved = pickle.load(open('saved_model', 'rb'))
#else:
#	print('NEW MODEL')
#	saved = None
#similarity_distance, movies_cleaned = data(saved)
##for i in range(len(movies_cleaned['original_title'])):
##	index = movies_cleaned[movies_cleaned['original_title'] == movies_cleaned['original_title'].iloc[i]].index[0]
##	if i != index:
##		print('NOT EQUAL', i, movies_cleaned['original_title'].iloc[i])
#while 1:
#	inp = input('Input Movie: ')
#	give_recomendations(inp, similarity_distance, movies_cleaned)
