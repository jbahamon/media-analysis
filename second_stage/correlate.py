#!/usr/bin/python
import json
import argparse as ap
import os, sys
from datetime import datetime

import numpy as np
from scipy import stats
from scipy.stats import spearmanr, kurtosis
from math import sqrt, log

import warnings
warnings.filterwarnings('error')
date_format = "%Y-%m-%d"

def positive_float(x):
    x = float(x)
    if x <= 0:
        raise argparse.ArgumentTypeError("Must be a positive float.")
    return x

def normalize_series(time_series, args):
         
    try:
        prev_value = float(time_series[0]) 
        # This deletes it from time_series.
        time_series = time_series[1:]
    except KeyError:
        return None
  
    for k, current_value in enumerate(time_series):

        if args.ext:
            if current_value != last_value:
                time_series[k] = current_value - last_value
                last_value = current_value
            else:
                time_series[k] = 0
        else:
            time_series[k] = log(current_value + args.log) -\
                log(prev_value + args.log)
            prev_value = current_value

    return time_series 

def get_correlation_confidence(series1, series2, args):

    if len(series1) != len(series2): 
        raise ValueError("Series must have the same length")

    series_length = len(series1)

    correlations = []
    n = 0
    for i in range(series_length):

        if series1[i] != 0 or series2[i] != 0:
            n += 1

        s1_temp = series1[0:i] + series1[i+1:]
        s2_temp = series2[0:i] + series2[i+1:]
        
        s1_norm = normalize_series(s1_temp, args)
        s2_norm = normalize_series(s2_temp, args)
        
        if sum(s1_temp) > 0 and sum(s2_temp) > 0:
            correlations.append(spearmanr(s1_norm, s2_norm)[0])

    if len(correlations) == 0:
        return (0, 1, 0)
    
    mean, sigma = np.mean(correlations), np.std(correlations)

    if sigma > 0: 

        CI = stats.norm.interval(0.95, loc=mean,
                scale=sigma/sqrt(len(correlations)))
        CI_size = CI[1] - CI[0]
        k = kurtosis(correlations)
    else:
        CI_size = 0
        k = 0
    
    full_correlation = spearmanr(normalize_series(series1, args),\
            normalize_series(series2, args))[0]
    return (full_correlation, CI_size, n)


parser = ap.ArgumentParser(description = "Computes correlations for a " \
    "JSON file containing time series for a term.")

parser.add_argument( "-i", "--in_file", type=ap.FileType("r"), default=sys.stdin, help = \
        "The JSON file to read time series from. If not specified, standard " \
        "input will be used.")

parser.add_argument("-p", "--pretty", action="store_true", help = "Pretty print the " \
        "output file.")

parser.add_argument("-o", "--out_file", type=ap.FileType("w"), default=sys.stdout, help = \
    "The file to be output. If not specified, the standard output will be used.")

normalizer = parser.add_mutually_exclusive_group(required=True)
normalizer.add_argument("-l", "--log", nargs="?", const=1, type=positive_float,\
        help = "Use this value as a additive "\
        "base to normalize using difference of logarithms.")

normalizer.add_argument("-e", "--ext", action="store_true", help = "Extend "\
                        "nonzero values and normalize using linear differences.")

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


        links = { term: [] for term in parsed_json["series"].keys() }

        for term, series in parsed_json["series"].items():
            for i in [ i for i in range(n_names) if names[i] in series ]:
                for j in [ j for j in range(i + 1, n_names) if names[j] in series ]:

                    correlation_confidence = get_correlation_confidence(\
                            series[names[i]][0], \
                            series[names[j]][0],
                            args)

                    links[term].append( { "source": i, \
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


