#!/usr/bin/python

import json
import argparse as ap
import os, sys
from datetime import datetime
from scipy.stats import spearmanr, kurtosis
date_format = "%Y-%m-%d"

parser = ap.ArgumentParser(description = "Computes correlations for a " \
    "JSON file containing time series for a term.")

parser.add_argument( "-i", "--in_file", type=ap.FileType("r"), default=sys.stdin, help = \
        "The JSON file to read time series from. If not specified, standard " \
        "input will be used.")

parser.add_argument("-p", "--pretty", action="store_true", help = "Pretty print the " \
        "output file.")

parser.add_argument("-o", "--out_file", type=ap.FileType("w"), default=sys.stdout, help = \
    "The file to be output. If not specified, the standard output will be used.")


def get_correlation_confidence(series1, series2):

    if len(series1) != len(series2): 
        raise ValueError("Series must have the same length")

    series_length = len(series1)

    correlations = []

    for i in range(series_length):
        s1_temp = series1[0:i] + series1[i+1:]
        s2_temp = series2[0:i] + series2[i+1:]

        correlations.push(spearmanr(s1_temp, s2_temp)[0])


    mean_correlation = sum(correlations)/float(series_length)

    k = kurtosis(correlations)

    return (mean_correlation, k)


args = parser.parse_args()

with args.in_file as json_file:
    with args.out_file as out_file:
        parsed_json = json.loads(json_file.read())

        terms = sorted(parsed_json["series"].keys())
        names = sorted(parsed_json["series"][terms[0]].keys())

        n_terms = len(terms)
        n_names = len(names)

        nodes = [ { \
                  "name": names[i], \
                  "index": i, \
                  "color_value": 0, \
                  "size": 20 } \
                  for i in range(n_names) ]


        links = []

        for term, series in parsed_json["series"].items():
            for i in range(n_names):
                for j in range(i + 1, n_names):
                    correlation_confidence = get_correlation_confidence(\
                            parsed_json["series"][names[i]], \
                            parsed_json["series"][names[j]])

                    links.append( { "source": i, \
                                    "target": j, \
                                    "value" : correlation_confidence })


        if args.pretty:
            out_file.write(json.dumps( { \
                "nodes" : nodes, \
                "links" : links }, \
                indent = 4, separators = (",",":")))
        else:
            out_file.write(json.dumps( { \
                "nodes" : nodes, \
                "links" : links } ))


