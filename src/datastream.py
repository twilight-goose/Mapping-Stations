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


DATASTREAM_API_KEY = "qoaJ6s42ryD2wGezfzkDhx9qSek1YGal"
api_prefix = "https://api.datastream.org/v1/odata/v4/"
headers = {'x-api-key': '{0}'.format(DATASTREAM_API_KEY)}


def build_api_str(endpoint, variable, select=None, skip=None, top=10000):
    query = [f"$filter=CharacteristicName%20eq%20%27{variable}%27",
             f"$top={top}"]
             
    if not select is None:
        query.append(f"$select=" + "%2C".join(select))
    
    if not skip is None:
        query.append(f"skiptoken=Id%3A{skip}")
    
    query = "&".join(query)
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


def generate_data_range(variable):
    def add_to_output(st_id, start, end):
        out_data['Station_ID'].append(st_id)
        out_data['P_Start'].append(start)
        out_data['P_End'].append(end)
        delta = date.fromisoformat(end) - date.fromisoformat(start)
        out_data['Num_Days'].append(delta.days + 1)
    
    def add_to_duplicates(st_id, sub_df, i):
        duplicates['Ind'].append(sub_df['Id'].iloc[i])
        duplicates['Station_ID'].append(st_id)
        duplicates['ActivityStartDate'].append(sub_df['Date'].iloc[i])
        duplicates['ActivityEndDate'].append(sub_df['ActivityEndDate'].iloc[i])
    
    def add_to_data_range(st_id, start, end, num):
        full_ranges['Station_ID'].append(st_id)
        full_ranges['Start'].append(start)
        full_ranges['End'].append(end)
        full_ranges['Num_Days'].append(num)
    
    all_results = []

    api_str = build_api_str(endpoint="Observations",
                            variable=variable,
                            select=["Id", "LocationId", "ActivityStartDate", "ActivityEndDate",
                                    "ResultValue"])
                            
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
            
        if not data.get("@odata.nextLink") is None:
            print("loaded 10,000 records. Loading more...")
            api_str = data.get("@odata.nextLink")
        else:
            has_data = False
            break
    
    all_results = pd.DataFrame(all_results)
    all_results = all_results.dropna(subset="ResultValue")
    all_results.rename(columns={"LocationId": "Station_ID", "ActivityStartDate": "Date"},
                       inplace=True)
    
    ### same as pwqmn_create_data_range() core code
    grouped = all_results.groupby(by=["Station_ID"])
    
    duplicates = {"Ind": [], "Station_ID": [], "ActivityStartDate": [], "ActivityEndDate": []}
    out_data = {'Station_ID': [], 'P_Start': [], 'P_End': [], 'Num_Days': []}
    full_ranges = {'Station_ID': [], 'Start': [], 'End': [], 'Num_Days': []}
    
    for key, sub_df in grouped:
        sub_df = sub_df.sort_values(by="Date")
        dates = sub_df['Date'].to_list()
        
        add_to_data_range(key[0], dates[0], dates[-1], len(set(dates)))
        
        start = None
        last = None
        
        i = 0
        for idate in dates:
            if start is None:
                start = idate
            else:
                str_date = datetime.strptime(idate, "%Y-%m-%d")
                str_last = datetime.strptime(last, "%Y-%m-%d")
                
                if str_date == str_last:
                    add_to_duplicates(key[0], sub_df, i)
                    add_to_duplicates(key[0], sub_df, i - 1))
                
                if  str_date != str_last + timedelta(days=1) and str_date != str_last:
                    add_to_output(key[0], start, last)
                    start = idate
                    
            last = idate
            i += 1
        add_to_output(key[0], start, last)
      
    out_data = pd.DataFrame(out_data)
    duplicates = pd.DataFrame(duplicates)
    full_ranges = pd.DataFrame(full_ranges)
    ###
    
    out_data.to_csv(f"datastream/{variable}.csv")
    duplicates.to_csv(f"datastream/{variable}_duplicates.csv")
    full_ranges.to_csv(f"datastream/{variable}_full_data_range.csv")
    

def main():
    #for var in variables_N:
    #    generate_data_range(var)
    
    for var in variables_P:
        generate_data_range(var)
    

if __name__ == "__main__":
    main()
    