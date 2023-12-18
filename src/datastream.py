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


"""

See main() for default behaviour

Run example where asdfja3k3j2o23423j is your datastream API key

>>> python datastream.py -k asdfja3k3j2o23423j

"""


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


DATASTREAM_API_KEY = "REPLACE WITH YOUR OWN API KEY"
api_prefix = "https://api.datastream.org/v1/odata/v4/"

parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description='''key''')
                                     
parser.add_argument('-k', '--key', action='store', default=DATASTREAM_API_KEY, dest='key',
                    help='Datastream API key to use to request data from Datastream')
DATASTREAM_API_KEY = parser.parse_args().key

headers = {'x-api-key': '{0}'.format(DATASTREAM_API_KEY)}



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
        
        ex: variable="Orthophosphate"
            variable=["Orthophosphate", "Nitrate"]
    
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


def api_request(endpoint, variable, select=None, top=10000, **kwargs):
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
    
    # build the initial call string
    api_str = build_api_str(
        endpoint=endpoint, variable=variable, top=top, select=select, **kwargs)
                            
    has_data = True
    print(api_str)
    
    # make API get requests until the desired amount of data has been retrieved
    while has_data:
        # make api request
        response = requests.get(api_str, headers=headers)

        # load data from the api response
        data = json.loads(response.content.decode('utf-8'))
        dump = json.dumps(data)
        
        if not (data.get('value') is None):
            all_results += data.get('value')
        else:
            break
        
        # If there is more data to retreive and the user wants to retreive
        # more than 10000 records, 
        if not (data.get("@odata.nextLink") is None) and top >= 10000 and kwargs.get('count') is None:
                
            print("loaded 10,000 records. Loading more...")
            api_str = data.get("@odata.nextLink")
        else:
            has_data = False
            break
    
    all_results = pd.DataFrame(all_results)
    
    print(all_results)
    # drop records with null result values
    if kwargs.get('count') is None and not all_results.empty:
        all_results.dropna(subset="ResultValue", inplace=True)
    else:
        print(f"Endpoint '{endpoint}' has no records for '{variable}'")
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
    
    if not os.path.isdir(f"../data/datastream/{variable}"):
        os.mkdir(f"../data/datastream/{variable}")
    
    # save the data to appropriately named folder
    all_results.to_csv(f"../data/datastream/{variable}/observations.csv")
    duplicates.to_csv(f"../data/datastream/{variable}/duplicates.csv")
    full_ranges.to_csv(f"../data/datastream/{variable}/full_data_range.csv")


def main():
    """
    Reads record data from the datastream API for each variable in 
    variables N and variables P near the top of the file and saves
    the to "/datastream/variable" in the form of .csv files.
    """
    for var in variables_N:
        generate_data_range(var)
    
    for var in variables_P:
        generate_data_range(var)
    

if __name__ == "__main__":
    main()
    