import word2vec
import topics

#Functionality using word2vec and nltk to use a previously trained model
#and from an input word find synonyms and return them in a list.
#The words are cleaned according to the method get_topics in topics.py.
#Have not tested code on unix, vectors.bin can be found at google drive together with the shared report.

def get_synonyms(word):
    #Clean input word (lowercase, stemming, ect)
    # res = topics.get_topics(word)
    cleanedWord = word
    
    #Load trained model, !-CHANGE PATH TO PATH OF MODEL-!
    model = word2vec.load("/Users/thiagolobo/Desktop/irproject/repo_new/stalkr/stalkr/vectors.bin")

    try:
        #get similar words from model
        indexes, metrics = model.cosine(cleanedWord)
        synonyms = model.vocab[indexes]

        #Clean data
        string = ""
        for elem in synonyms:
            string = string + " " + elem
        cleanedSynonyms = topics.get_topics(string)

        #remove duplicate of search word
        wordList = list(cleanedSynonyms)
        while cleanedWord in wordList: wordList.remove(cleanedWord)
        
    except KeyError as e:
        #return empty list if word was not present in model
        wordList = []
        
    return wordList
