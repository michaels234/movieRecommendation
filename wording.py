
import string
import nltk
from nltk.corpus import wordnet
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from nltk.stem import SnowballStemmer
from nltk.stem import LancasterStemmer
nltk.download("stopwords")
nltk.download("wordnet")
stemmer = PorterStemmer()
stemmer2 = SnowballStemmer('english')
stemmer3 = LancasterStemmer()

def process(text):
	# remove punctuation
	nopunc = [char for char in text if char not in string.punctuation]
	nopunc = ''.join(nopunc)
	# remove stopwords
	nopunc = [word for word in nopunc.split() if word not in stopwords.words('english')]
	final = []
	for word in nopunc:
		# only continue for non numeric non-capitalized words
		# otherwise return empty array
		if not word[0].isupper() and not word.isnumeric():
			newword = []
			for syn in wordnet.synsets(word):
				for l in syn.lemmas():
					# avoid duplicates
					if l.name() not in newword:
						newword.append(l.name())
			# if no synonyms, just put the original word in
			if newword == []:
				newword .append(word)
			# sort alphabetically and combine into 1 space-separated string
			newword.sort()
			newword = ' '.join(newword)
			final.append(newword)
	return final


#print(process('steal'))
#thing = stemmer.stem('thief')
#thing = stemmer2.stem(thing)
#thing = stemmer3.stem(thing)
word = 'steal'
newword = []
related_forms = []
for a in wordnet.synsets(word):
	print('a', a.name().split('.')[0])
	c = [b for b in a.lemmas()]
	print('c', c)
	for e in c:
		print('e', e.derivationally_related_forms())
		for f in e.derivationally_related_forms():
			g = f.synset().name().split('.')[0]
			if '_' not in g:
				g = stemmer2.stem(g)
				print('g', g)
				if g not in related_forms:
					related_forms.append(g)
related_forms.sort()
print(related_forms)
#		print('c', c, c.name())
#		for e in [d for d in wordnet.synsets(c.name())]:
#			print('e', e, e.name())
#			for f in e.lemmas():
#				print('f', f)
#				if f.name() not in related_forms:
#					related_forms.append(f.name())
#related_forms.sort()
#print(related_forms)
#b = [n.lemmas for n in (m for m in a)]
#print(b)
#c = [n.derivationally_related_forms() for n in b]
#print(c)