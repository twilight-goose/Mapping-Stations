#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
#
# Copyright 2016-2022 Juliane Mai - juliane.mai(at)uwaterloo.ca
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

# Modfied by James Wang

# ========================================================================= ##
# License ================================================================= ##
# ========================================================================= ##

# Copyright (c) 2023 James Wang - jcw4698(at)gmail.com
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


import os
import sys

# -----------------------
# add subolder scripts/lib to search path
# -----------------------
dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(dir_path+'/lib')

import argparse
import subprocess

import requests
import json

import pandas as pd
from datetime import datetime
from datetime import timedelta
from datetime import date
from load_data import datastream_path


DATASTREAM_API_KEY = "qoaJ6s42ryD2wGezfzkDhx9qSek1YGal"
api_prefix = "https://api.datastream.org/v1/odata/v4/"
headers = {'x-api-key': '{0}'.format(DATASTREAM_API_KEY)}


def build_api_str(endpoint, variable, top=10000, **kwargs):
    """
    Constructs a Datastream api request string from provided
    parameters.
    
    :param endpoint: str
        API endpoint to request data from.
        
    :param variable: str or list-like of str
        CharacteristicName(s) to filter the data request by.
        Requesting more than 1 variable while also filtering by
        extent may lead to unintended behaviour.
    
    :param top: int (default=10000)
        Number of rows to retrieve from Datastream.
    
    :param kwargs: keyword arguments
        Additional arguments to add to the api request.
        Keywords with special behaviour:
            
            extent: list-like of float of length 4
                Latitude/Longitude bounding box to add
                to api request (minx, miny, maxx, maxy).
                
                ex: extent=(-80, 42, -77, 45)
                
            select: str of list-like of str
                Names of data to request from datastream.
                See file head for valid selct by values.
                
                ex: select="MonitoringLocationID"
                    select=["MonitoringLocationID", "MonitoringLocationType"]
            
            skip: int
                Index of the row to start from.
                
                ex: skip=10
        
        For keywords without special behaviour, they will be
        formatted as follows:
            
            $<key>=<value>
    
    :return: str
        The API request string.
        
    examples:
        api_str = build_api_str(
            "Records", "Orthophosphate", top=10,
            extent=(-80, 40, -77, 42),
            select=["Id", "MonitoringLocationID", "MonitoringLocationName",
                    "ActivityStartDate", "ActivityStartTime", "ActivityEndDate",
                    "ResultSampleFraction", "ResultValue", "ResultUnit"]
        )
    """
    if type(variable) is str:
        variable = [variable]
        
    variable = [f"CharacteristicName eq '{v}'" for v in variable]
    query = [f"$top={top}", f"$filter=" + " or ".join(variable)]
    
    for key in kwargs:
        value = kwargs.get(key)
        
        if key == "extent":
            q_parts = [f"'{value[0]}' lte MonitoringLocationLongitude",
                       f"'{value[1]}' lte MonitoringLocationLatitude",
                       f"'{value[2]}' gte MonitoringLocationLongitude",
                       f"'{value[3]}' gte MonitoringLocationLatitude"]
            query[1] += " and " + " and ".join(q_parts)
        elif key == "select":
            query.append(f"$select=" + ",".join(value))
        elif key == "skip":
            query.append(f"skiptoken=Id:{value}")
        else:
            query.append(f"${key}={value}")
        
    query = "&".join(query)
    query = query.replace(" ", "%20")
    query = query.replace(",", "%2C")
    query = query.replace("'", "%27")
    query = query.replace(":", "%3A")
    
    return api_prefix + endpoint + "?" + query
    

variables_P = [    "Orthophosphate",
                   "Phosphorus, hydrolyzable",
                   "Soluble Reactive Phosphorus (SRP)",
                   "Total Phosphorus, mixed forms",
                   "Organic phosphorus"]
                   
variables_N = [    "Inorganic nitrogen (ammonia, nitrate and nitrite)",
                   "Inorganic nitrogen (nitrate and nitrite)",
                   "Nitrate",
                   "Organic Nitrogen",
                   "Total Nitrogen, mixed forms"]


def api_request(endpoint, variable, select=None, top=None, **kwargs):
    """
    Requests data from the Datastream api.
    
    :param endpoint: str
        API endpoint to request data from.
        
    :param variable: str or list-like of str
        CharacteristicName(s) to filter the data request by.
        Requesting more than 1 variable while also filtering by
        extent may lead to unintended behaviour.
    
    :param select: str or list-like of str or None (default)
        Names of data to request from datastream. If nothing is
        provided, requests specific sets of data based on the
        chosen endpoint.
        
    :param top: int or None (default)
        Number of rows to retrieve from Datastream. If None,
        retrieves all data.
    
    :param kwargs: keyword arguments
        Additional arguments to add to the api request.
        Keywords with special behaviour:
            
            extent: list-like of float of length 4
                Latitude/Longitude bounding box to add
                to api request (minx, miny, maxx, maxy).
                
                ex: extent=(-80, 42, -77, 45)
            
            skip: int
                Index of the row to start from.
                
                ex: skip=10
                
            count: {'true'}
                Whether or not to get the count of records,
                instead of the data itself.
        
        For keywords without special behaviour, they will be
        formatted as follows:
            
            $<key>=<value>
    
    :return: DataFrame
        The data retreived from the request.
        
    examples:
        data = api_request(
            "Records", "Orthophosphate",
            extent=(-80, 40, -77, 42),
            select=["Id", "MonitoringLocationID", "MonitoringLocationName",
                    "ActivityStartDate", "ActivityStartTime", "ActivityEndDate",
                    "ResultSampleFraction", "ResultValue", "ResultUnit"])
        
        data = api_request(
            "Records", ["Orthophosphate", "Nitrate"],
            top=500,
            select=["Id", "MonitoringLocationID", "MonitoringLocationName",
                    "ActivityStartDate", "ActivityStartTime", "ActivityEndDate",
                    "ResultSampleFraction", "ResultValue", "ResultUnit"])
    """
    o_select = ["Id", "LocationId", "ActivityStartDate",
                "ActivityStartTime", "ActivityEndDate", "CharacteristicName",
                "ResultSampleFraction", "ResultValue", "ResultUnit"]
                                    
    r_select = ["Id", "MonitoringLocationID", "MonitoringLocationName",
                "ActivityStartDate", "ActivityStartTime", "ActivityEndDate",
                "ResultSampleFraction", "ResultValue", "ResultUnit"]
    
    all_results = []
    
    if select is None:
        if endpoint == "Observations":
            select = o_select
        elif endpoint == "Records":
            select = r_select
    
    api_str = build_api_str(
        endpoint=endpoint, variable=variable, top=top, select=select,
        **kwargs)
                            
    has_data = True
    print(api_str)

    while has_data:
        response = requests.get(api_str, headers=headers)

        # load data
        data = json.loads(response.content.decode('utf-8'))
        dump = json.dumps(data)
        
        if not data.get('value') is None:
            all_results += data.get('value')
        else:
            break
            
        if not data.get("@odata.nextLink") is None and \
                (not top is None and len(all_results) < top) and \
                kwargs.get('count') is None:
                
            print("loaded 10,000 records. Loading more...")
            api_str = data.get("@odata.nextLink")
        else:
            has_data = False
            break
    
    all_results = pd.DataFrame(all_results)
    if kwargs.get('count') is None:
        all_results.dropna(subset="ResultValue", inplace=True)
    return all_results


def generate_data_range(variable):
    """
    Creates and saves .json and .csv files containing
    the date ranges and number of days where variable
    data is available.
    
    Outputs to "/datastream" and "/datastream_jsons"
    
    variable_observations.ext:
        All observations retrieved from the datastream.
        
    variable_duplicates.ext:
        All instances of multiple observations being recorded
        for the same date.
    
    variable_full_data_range.ext:
        The first date and last date that observations were recorded
        for each station, and the total number of records made within
        that time period.
        
        Station_ID: StationID
        Start: Date of first record
        End: Date of last record
        Num_Days: Number of unique dates that records are available for
    
    :param variable: str
        The CharacteristicName to request data for and
        build date ranges for.
    """
    def add_to_data_range(st_id, start, end, num):
        full_ranges['Station_ID'].append(st_id)
        full_ranges['Start'].append(start)
        full_ranges['End'].append(end)
        full_ranges['Num_Days'].append(num)
    
    all_results = api_request("Records", variable)
    
    ### same as pwqmn_create_data_range() core code
    grouped = all_results.groupby(by=["MonitoringLocationID"])
    
    duplicates = []
    full_ranges = {'Station_ID': [], 'Start': [], 'End': [], 'Num_Days': []}
    
    for key, sub_df in grouped:
        sub_df = sub_df.sort_values(by="ActivityStartDate")
        dates = sub_df['ActivityStartDate'].to_list()
        
        add_to_data_range(key[0], dates[0], dates[-1], len(set(dates)))
        
        for i in range(1, len(dates)):
            if dates[i] == dates[i - 1]:
                duplicates.append(sub_df.iloc[i - 1])
                duplicates.append(sub_df.iloc[i])
        
    duplicates = pd.DataFrame(duplicates)
    full_ranges = pd.DataFrame(full_ranges)
    ###

    all_results.to_csv(f"datastream/{variable}_observations.csv")
    duplicates.to_csv(f"datastream/{variable}_duplicates.csv")
    full_ranges.to_csv(f"datastream/{variable}_full_data_range.csv")
    
    all_results.to_json(f"datastream_jsons/{variable}_observations.json")
    duplicates.to_json(f"datastream_jsons/{variable}_duplicates.json")
    full_ranges.to_json(f"datastream_jsons/{variable}_full_data_range.json")
 

def drange_from_json(path):
    def sort_by_date(obs_dict):
        return obs_dict["ActivityStartDate"]
    
    with open(path, 'r', encoding='utf-8') as ff:

        data = json.load(ff)['value']
        drange = []
        
        for st_dict in data:
            out_dict = st_dict.copy()
            del out_dict['observations']

            obs_dates = pd.DataFrame(st_dict['observations'])
            obs_dates = obs_dates['ActivityStartDate'].to_list()
            
            out_dict['First Date'] = obs_dates[0]
            out_dict["Last Date"] = obs_dates[-1]
            out_dict["Total Observations"] = len(obs_dates)
            out_dict["Unique Days"] = len(set(obs_dates))
            
            drange.append(out_dict)

    return drange
    

def get_dranges(dirpath):
    all_data = {}

    for file in filter(lambda x:x.endswith(".json"), os.listdir(dirpath)):
        
        drange = drange_from_json(os.path.join(datastream_path, file))
        all_data[file[:-5]] = drange
    
    return all_data

def main():
    data = get_dranges(datastream_path)

    for i in data:
        print(i)
    return
    
    for var in variables_N:
        generate_data_range(var)
    
    for var in variables_P:
        generate_data_range(var)
    

if __name__ == "__main__":
    main()
    