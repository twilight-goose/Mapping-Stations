#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
#
# Copyright 2016-2023 Juliane Mai - juliane.mai(at)uwaterloo.ca
#
# License
# This file is part of Juliane Mai's personal code library.
#
# Juliane Mai's personal code library is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Juliane Mai's personal code library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.

# You should have received a copy of the GNU Lesser General Public License
# along with Juliane Mai's personal code library.  If not, see <http://www.gnu.org/licenses/>.
#
# pyenv activate env-385-new
# python 6_find_streamflow_gauge.py -i "Total_Phosphorus_mixed_forms_obs.json" -o "test" -s 10 -e 15


import os
import sys

# -----------------------
# add subolder scripts/lib to search path
# -----------------------
dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(dir_path+'/lib')

import argparse
import json

import gdf_utils
import load_data

import geopandas as gpd
import pandas as pd
import browser
from gen_util import Can_LCC_wkt

input_file    = os.path.join("..", "data", "datastream", "Total_Phosphorus_mixed_forms_obs.json")
output_folder = os.path.join("..", "data", "datastream")
start         = 1
end           = 10

parser  = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                  description='''Find close streamflow gauging station for list of water quality gauges.''')
parser.add_argument('-i', '--input_file', action='store', default=input_file, dest='input_file',
                    help="Input JSON file. Default: None.")
parser.add_argument('-o', '--output_folder', action='store', default=output_folder, dest='output_folder',
                    help="Name of folder to dump shapefiles into. Folder will be created if it doesnt exist. Default: None.")
parser.add_argument('-s', '--start', action='store', default=start, dest='start',
                    help="Station number to start with. This is an index. If start=1, first station will be delineated. If start=10, 10th station will be delineated first and first 9 will be skipped. If None, start=1. Default: None.")
parser.add_argument('-e', '--end', action='store', default=end, dest='end',
                    help="Station number to end with. This is an index. If end=2, second station is last station to delineate. If end=5, 5th station is the last one that will be delineated. If None, end=len(stations). Default: None.")

args          = parser.parse_args()
input_file    = args.input_file
output_folder = args.output_folder
start         = int(args.start)
end           = int(args.end)

if (input_file is None):
    raise ValueError("Input file needs to be specified.")

if (output_folder is None):
    raise ValueError("Output folder needs to be specified.")

if not os.path.exists(input_file):
    raise ValueError("Input file {} does not exist.".format(input_file))

if not os.path.exists(output_folder):
    os.makedirs(output_folder)


del parser, args


print("")
print("----------------------------------------------")
print("Working on stations in file: {}".format(input_file))
print("----------------------------------------------")

# -------------------------------
# load data
# -------------------------------
if os.path.exists(input_file):
    print("Read data from: {}".format(input_file))
    with open(input_file, 'r', encoding='utf-8') as ff:
        data = json.load(ff)
else:
    raise ValueError("File {} not found".format(input_file))

# -------------------------------
# properly set start and end index
# -------------------------------
if start is None:
    start = 0
else:
    start -= 1  # indexes start with 0 in Python

if end is None:
    end = len(data['value'])


# -------------------------------
# filter only data needed for delineation
# -------------------------------

stations = []
for dd in data['value'][start:end]:

    tmp = { 'id': dd['Id'],
            'lat': dd['LatitudeNormalized'],
            'lon': dd['LongitudeNormalized'],
          }
    stations.append(tmp)

# -------------------------------
# perform delineation
# -------------------------------

lines = load_data.load_rivers()

hydat = load_data.get_hydat_stations()
hydat = gdf_utils.point_gdf_from_df(hydat)

origin = pd.DataFrame(stations)
origin = origin.assign(Station_ID=origin['id'])
origin = gdf_utils.point_gdf_from_df(origin)

hydat.to_file(os.path.join(load_data.shp_save_path, 'hydat.shp'))
origin.to_file(os.path.join(load_data.shp_save_path, 'origin.shp'))

lines = gdf_utils.assign_stations(lines, hydat, prefix="hydat_", max_distance=10000)
lines = gdf_utils.assign_stations(lines, origin, prefix="origin_", max_distance=10000)

network = gdf_utils.hyriv_gdf_to_network(lines)

match_df = gdf_utils.dfs_search(    network,
                                    max_distance=1000000,   # in [m]
                                    prefix1="origin_",    # list of stations to find a match for
                                    prefix2="hydat_",     # all stations to find a match from
                            )
match_df.drop(columns=['path', 'seg_apart'], inplace=True)
print(match_df.to_string())
match_df.to_csv(os.path.join(output_folder,"table.csv"))
