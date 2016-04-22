from textblob import TextBlob
import re

def normalize(text):
    tokens = text.split()
    new_string = ""

    for t in tokens:
        if not (t.startswith('#') or t.startswith('@') or t.startswith('&') or t.startswith('http')):
            new_string += t + " "

    return new_string

def get_sentiment(text):
    text = normalize(text.lower())
    s = TextBlob(text).sentiment
    return [s.polarity, s.subjectivity]

# not using this one for now
def is_positive(sentiment):
    polarity = sentiment[0]
    factor = sentiment[1]
    result = 0

    if polarity >= 0.5:
        result = 1
    elif polarity <= -0.5:
        result = -1

    if factor < 0.6:
        return result
    else:
        return 0


