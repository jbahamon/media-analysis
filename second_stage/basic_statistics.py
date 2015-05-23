#!/usr/bin/python

import json
import argparse as ap
import os, fnmatch
from collections import defaultdict

class readable_dir(ap.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        prospective_dir = values
        if not os.path.isdir(prospective_dir):
            raise ap.ArgumentTypeError(("readable_dir:{0} is not a valid" + \
                    "path").format(prospective_dir)) 

        if os.access(prospective_dir, os.R_OK):
            setattr(namespace, self.dest, prospective_dir)
        else:
            raise ap.ArgumentTypeError(("readable_dir:{0} is not a" + \
            "readable dir".format(prospective_dir)))

parser = ap.ArgumentParser(description = "Computes basic statistics for a" + \
    "folder of JSON files containing tweets.")

parser.add_argument("folder", action=readable_dir, help = \
        "The folder to read JSON files from.")

args = parser.parse_args()

folder = args.folder

media_histogram = defaultdict(int)

for path in [ os.path.join(folder, filename) for filename in os.listdir(folder) \
        if os.path.isfile(os.path.join(folder, filename)) and \
        os.access(os.path.join(folder, filename), os.R_OK) and filename.endswith(".json") ]:

    with open(path, "r") as f:
        parsed_json = json.loads(f.read())

        for tweet in parsed_json:
            media_histogram[tweet["user"]["screen_name"]] += 1


for k, v in media_histogram.items():
    print str(v)
