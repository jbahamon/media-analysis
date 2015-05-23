#!/usr/bin/python
import sys
import numpy as np
import nltk, string
from sklearn.feature_extraction.text import TfidfVectorizer

number_of_sources = int(sys.argv[3])

def tokenize(text):
    return nltk.tokenize.word_tokenize(text)

vectorizer = TfidfVectorizer(tokenizer=tokenize,
        stop_words=nltk.corpus.stopwords.words('spanish'))

def cosine_sim(text1, text2):
    tfidf = vectorizer.fit_transform([text1, text2])
    return ((tfidf * tfidf.T).A)[0,1]

with open(sys.argv[1], "r") as source_file:
    with open(sys.argv[2], "w") as destination_file:
        news_data = source_file.readlines()
        tfidfs = vectorizer.fit_transform(news_data)

        sims = ((tfidfs * tfidfs.T).A)

        for i in xrange(number_of_sources):
            for j in xrange(i + 1, number_of_sources):
                destination_file.write(str(i) + " " + str(j) + " " + \
                    str(sims[i,j]) + "\n")
