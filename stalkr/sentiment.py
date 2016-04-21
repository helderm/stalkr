from textblob import TextBlob

def get_sentiment(text):
    s = TextBlob(text).sentiment
    print s
    return is_positive([s.polarity, s.subjectivity])


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
