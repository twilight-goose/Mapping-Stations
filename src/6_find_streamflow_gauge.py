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


"""
Expected ouput for (file path preceing Mapping-Stations will differ):
>>> python 6_find_streamflow_gauge.py -i "../data/DataStream/Total_Phosphorus_mixed_forms_obs.json" -o test  -s 10 -e 15

>>> ----------------------------------------------
>>> Working on stations in file: ../data/DataStream/Total_Phosphorus_mixed_forms_obs.json
>>> ----------------------------------------------
>>> Read data from: ../data/DataStream/Total_Phosphorus_mixed_forms_obs.json
>>> Loading rivers from 'C:\Users\jcw46\Documents\GitHub\Mapping-Stations\data\Hydro_RIVERS_v10\HydroRIVERS_v10_na.shp'
>>> Creating a connection to 'C:\Users\jcw46\Documents\GitHub\Mapping-Stations\data\Hydat\Hydat.sqlite3'
>>> Creating a connection to 'C:\Users\jcw46\Documents\GitHub\Mapping-Stations\data\Hydat\Hydat.sqlite3'
>>> Attempting conversion with the following CRS parameter: 4326
>>> Dataframe successfully converted to geopandas point geodataframe
>>> Attempting conversion with the following CRS parameter: 4326
>>> Dataframe successfully converted to geopandas point geodataframe
>>> Creating a connection to 'C:\Users\jcw46\Documents\GitHub\Mapping-Stations\data\Hydat\Hydat.sqlite3'
>>>    origin_id hydat_id  origin_dist_from_net  hydat_dist_from_net        dist      pos  data_overlap  total_hydat_records  total_origin_records
>>> 0       4829  01AR005            135.347169             55.03769  496.183479  On-Down             0                17166                     2
>>> (1, 9)
>>> Output saved to: test\Total_Phosphorus_mixed_forms_obs_10_15.csv


Output table field description:

origin_id
    - The ID of the station that was matched
    - field name will differ based on assign_stations() parameters

hydat_id
    - The ID of the station that the origin station was matched to
    - field name will differ based on assign_stations() parameters

origin_dist_from_net
    - The distance in metres between the origin station and the river network
    - field name will differ based on assign_stations() parameters

hydat_dist_from_net
    - The distance in metres between the matched station and the river network
    - field name will differ based on assign_stations() parameters

dist
    - The distance (in metres) between the origin and candidate station

pos
    - The position of the candidate station relative to the origin station
        - starts with "On": same river segment
        - contains "Down": downstream
        - contains "Up": upstream
        
total_origin_records
    - The number of days where observation data is available for the origin station
    
total_hydat_records
    - The number of days where observation data is available for the hydat station
    
data_overlap
    - The number of days where observation ata is available for both the origin and hydat station
    
"""

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
from gen_util import Can_LCC_wkt, Period

input_file    = os.path.join("..", "data", "datastream", "Inorganic_nitrogen_(nitrate_and_nitrite)_obs.json")
output_folder = os.path.join("..", "data", "datastream")
start         = 701
end           = 800
dataset       = None

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
parser.add_argument('-d', '--dataset', action='store', default=dataset, dest='dataset',
                    help="River network dataset to perform the matching with.")

args          = parser.parse_args()
input_file    = args.input_file
output_folder = args.output_folder
start         = int(args.start)
end           = int(args.end)
dataset       = args.dataset


if (input_file is None):
    raise ValueError("Input file needs to be specified.")

if (output_folder is None):
    raise ValueError("Output folder needs to be specified.")

if not os.path.exists(input_file):
    raise ValueError("Input file {} does not exist.".format(input_file))


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
observations = []

for dd in data['value'][start:end]:

    tmp = { 'id': dd['Id'],
            'lat': dd['LatitudeNormalized'],
            'lon': dd['LongitudeNormalized']
          }
    observations += dd['observations']
    stations.append(tmp)

# -------------------------------
# perform matching
# -------------------------------
if dataset is None:
    lines = load_data.load_rivers()
else:
    lines = load_data.load_rivers(path=dataset)
    

hydat = load_data.get_hydat_stations()
hydat = gdf_utils.point_gdf_from_df(hydat)

origin = pd.DataFrame(stations)
origin = origin.assign(Station_ID=origin['id'])
origin = gdf_utils.point_gdf_from_df(origin)

observations = pd.DataFrame(observations)
observations.rename(columns={'LocationId': 'Station_ID', 'ActivityStartDate': 'Date'}, inplace=True)
observations.drop(columns=['ResultSampleFraction', 'ResultValue', 'ResultUnit',
                            'ResultStatusID', 'ResultDetectionCondition', 'ResultValueType',
                            'ResultAnalyticalMethodContext', 'MethodSpeciation', 'ActivityEndDate'],
                    inplace=True)

# If you wish to snap stations to rivers that are farther than
# 750 m away, add "max_distance=X" where X is the desired maximum distance
# to snap stations to rivers.
lines = gdf_utils.assign_stations(lines, hydat, prefix="hydat", max_distance=1500)
lines = gdf_utils.assign_stations(lines, origin, prefix="origin", max_distance=1500)

network = gdf_utils.hyriv_gdf_to_network(lines)

# prefix1 and prefix2 must be featured/used when assigning stations
match_df = gdf_utils.dfs_search(    network,
                                    max_distance=12000, # in [m]
                                    prefix1="origin",   # list of stations to find a match for
                                    prefix2="hydat",    # all stations to find a match from
                                    max_depth=1200      # I recommend a max_depth around 1/10th of the max_distance
                            )
# In this iteration of the project, data overlap must be calculated
# as a separate operation

# ============
# Calculate the periods and period overlaps
# ============

# Period.generate_data_range requires observations be a DataFrame
# containng a 'Station_ID' field as well as a 'Date' field

hydat_dr = load_data.get_hydat_data_range(subset=match_df['hydat_id'].to_list())
origin_dr = Period.generate_data_range(observations)

## data range consists of {"Station_ID", "P_Start", "P_End"} fields
## where "Station_ID" contains every station id from observations
## adds 3 fields to the output table (see gdf_utils.assign_period_overlap())

match_df = gdf_utils.assign_period_overlap( match_df,
                                            'hydat',
                                            hydat_dr,
                                            'origin',
                                            origin_dr
                                            )

# ============
# ============

# the path column contains line geometry of the network edges
# between the origin and candidate node used for plotting
# seg_apart is an arbitrary measure of distance from the origin
# node, and the actual length of river separating the two is more
# important
match_df.drop(columns=['path', 'seg_apart'], inplace=True)

# display the dataframe
print(match_df.to_string())
print(match_df.shape)

# -------------------------------
# perform delineation
# -------------------------------

## delineate_matches requires the prefixes as well as the station data to function
## adds 3 fields to the ouput table (see gdf_utils.delineate_matches())
# delineated = gdf_utils.delineate_matches(match_df, "origin", origin, "hydat", hydat)

# -------------------------------
# output
# -------------------------------

if not os.path.isdir(output_folder):
    print("creating output folder")
    os.mkdir(output_folder)

# remove the extension and the folders from the file path to extract only the filename
filename = os.path.splitext(os.path.basename(input_file))[0]
output_file_path = os.path.join(output_folder, f"{filename}_{start+1}_{end}.csv")
match_df.to_csv(output_file_path)

print(f"Output saved to: {output_file_path}")
