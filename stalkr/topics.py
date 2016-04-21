from sets import Set
import re

import nltk
from nltk.tokenize import WhitespaceTokenizer

# nltk.download('punkt')
# nltk.download('maxent_ne_chunker')
# nltk.download('words')
# nltk.download('averaged_perceptron_tagger')

# List of words to ignore, all in lowercase.
ignore = Set([
    "don't",
    "i'll",
    "retweet",
    "rt",
])

stemmer = nltk.stem.porter.PorterStemmer()
tokenizer = WhitespaceTokenizer()

def skip(token):
    return token.startswith('#') \
        or token.startswith('@') \
        or token.startswith('&') \
        or token.startswith('http') \
        or token in ignore

def normalize(token):
    return re.sub("[^A-za-z0-9#@'&]", "", token)

def get_topics(text):
    tokens = tokenizer.tokenize(text.lower())
    tokens = filter(lambda t: not len(t) < 3, tokens)
    tokens = map(lambda t: normalize(t), tokens)
    tokens = filter(lambda t: not skip(t), tokens)
    tagged = nltk.pos_tag(tokens)
    nouns = filter(lambda t: t[1].startswith('NN'), tagged)
    norm = map(lambda t: stemmer.stem(t[0]), nouns)
    return norm
