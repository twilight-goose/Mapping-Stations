'''
Arcpy library is used for data management, analysis, and manipulation. An ArcGIS Pro lisence is required,
but ideally there is no need to create/load projects to perfrom operations. Everything should be
contained within these modules, and projects used as ways to check work.
'''
import sys
import os
import pandas as pd
import geopandas as gpd
import arcpy
import sqlite3
from datetime import datetime


PWQMN_PATH = os.path.join(os.path.dirname(__file__), "PWQMN_cleaned\\Provincial_Water_Quality_Monitoring_Network_PWQMN_cleaned.csv")


def load_csv(in_path, out_path, convert=False):
    arcpy.management.CopyRows(in_path, out_path)
    f_names = [f.name for f in arcpy.ListFields(out_path)]
    if convert and "lon" in f_names and "lat" in f_names:
        arcpy.management.XYTableToPoint(out_path, out_path + "_points", "lon", "lat")
    return [out_path, out_path + "_points"]


def get_sqlite_table_list(connection):
    pass

def load_sqlite():

    hydat_path = os.path.join(os.path.dirname(__file__), "Hydat.sqlite3\\Hydat.sqlite3")
    conn = sqlite3.connect(hydat_path)
    cursor = conn.cursor()

    table_list = pd.read_sql_query("SELECT * FROM sqlite_master where type= 'table'", conn)
    station_data = pd.read_sql_query("SELECT * FROM 'STATIONS' WHERE PROV_TERR_STATE_LOC == 'ON'", conn)

    station_data['STATION_NUMBER'] = station_data['STATION_NUMBER'].astype('|S')
    print(station_data.dtypes)

    for tbl_name in table_list['tbl_name'][1:]:
        table_data = pd.read_sql_query("SELECT * FROM %s" % tbl_name, conn)
        if 'STATION_NUMBER' in table_data.columns.values:
            table_data['STATION_NUMBER'] = table_data['STATION_NUMBER'].astype('|S')
            print("Table:" + tbl_name)
            print(table_data.dtypes)

            station_data = station_data.join(table_data, on=['STATION_NUMBER'], lsuffix="_L")

    conn.close()
    print(station_data)
    return station_data


def aprx_map(aprx, data):
    n = len(aprx.listMaps())
    # create a new map, named based on the existing number of maps
    newMap = aprx.createMap("Map " + str(n + 1))

    # iterate over each piece of data loaded into the geodatabase
    for key in data.keys():
        try:
            newMap.addDataFromPath(data[key][1])
        except RuntimeError:
            pass
        # save after sucessfully adding each layer to the new map
        aprx.save()

    print("Output mapped to Map " + str(n + 1) + "in the project at " + aprx.filePath)


def load_monday_files():
    print("Loading Monday File Gallery to Memory...")
    mondayPath = os.path.join(os.path.dirname(__file__), "MondayFileGallery")
    data_dict = {}

    for file in filter(lambda x: x.endswith(".csv"), os.listdir(mondayPath)):
        print("> loading '{0}'".format(file))
        data_dict[file] = pd.read_csv(os.path.join(mondayPath, file))

    return data_dict


def point_from_df(df, x_field='lat', y_field='lon'):
    # probably want to add field searching and auto matching functionality
    print(df.columns.values)
    try:
        print("X/Y fields found. Loading....")
        pointArray = gpd.points_from_xy(df[x_field], df[y_field])
        print("Dataframe converted to geopandas point array")
        return pointArray
    except KeyError:
        print("X/Y field not found")


def get_station_data(station_info_df, query):
    """
    This function performs a query on station info list, and retrieves dated water information of stations passing the
    criteria
    :return:
    """
    tstart = datetime.now()

    df = pd.read_csv(PWQMN_PATH,
                         usecols=['MonitoringLocationName', 'ActivityStartDate', 'SampleCollectionEquipmentName',
                                  'CharacteristicName', 'ResultSampleFraction', 'ResultValue', 'ResultUnit',
                                  'ResultValueType', 'ResultDetectionCondition',
                                  'ResultDetectionQuantitationLimitMeasure',
                                  'ResultDetectionQuantitationLimitUnit'],
                         dtype={'ResultSampleFraction' : str,
                                'ResultValue' : float,
                                'ResultUnit' : str,
                                'ResultDetectionCondition' : str,
                                'ResultDetectionQuantitationLimitMeasure' : str,
                                'ResultDetectionQuantitationLimitUnit' : str},
                         )
    delta = datetime.now() - tstart
    print("It took {0} seconds and {1} microseconds to query and retrieve water data".format(delta.seconds, delta.microseconds))
    df.query(query, inplace=True)
    print(df)
    return df


def get_station_info():
    """
    This function reads from the cleaned PWQMN data into RAM using pd, and returns the following information about
    each station: Name, ID, Longitude, Latitude, and Start Date
    :return:
    """
    tstart = datetime.now()

    df = pd.read_csv(PWQMN_PATH, usecols=['MonitoringLocationName', 'MonitoringLocationID',
                                              'MonitoringLocationLatitude', 'MonitoringLocationLongitude',
                                              'ActivityStartDate'])
    grouped = df.groupby(by=['MonitoringLocationName', 'MonitoringLocationID', 'MonitoringLocationLatitude',
                             'MonitoringLocationLongitude'],)

    station_data = []

    for name, subset_df in grouped:    # iterate through sequences of (group name, subsetted object (df)]
        time_range = pd.to_datetime(subset_df['ActivityStartDate'])
        station_data.append(name + (time_range.min(), time_range.size, subset_df.index))

    station_data = pd.DataFrame(station_data, columns=['Name', 'ID', 'Longitude', 'Latitude', 'Start Date',
                                                           'NumRecords', 'Indices'])
    station_data.set_index('Name')
    station_data.style.hide(['Indices'], axis=1)
    delta = datetime.now() - tstart
    print("It took {0} seconds and {1} microseconds to retrieve station data".format(delta.seconds, delta.microseconds))

    print(station_data)
    return station_data


def main():
    tstart = datetime.now()

    # station_info = get_station_info()
    # station_data = get_station_data(station_info, 'MonitoringLocationName=="ABERFOYLE CREEK STATION"')

    # hydrat_df = load_sqlite()

    # hydat_stations = get_hydat_stations()

    mondayFiles = load_monday_files()
    for key in mondayFiles.keys():
        pointArray = point_from_df(mondayFiles[key])
    return

    delta = datetime.now() - tstart
    print("It took {0} seconds and {1} microseconds total".format(delta.seconds, delta.microseconds))
    return

    data_path = input("Data Folder Path:\n")
    aprx_path = input("ArcGIS Project Path:\n")

    if data_path == "":
        data_path = os.path.join(os.path.dirname(__file__), "MondayFileGallery")
    if aprx_path == "":
        aprx_path = os.path.join(os.path.dirname(__file__), "MyProject\\MyProject.aprx")

    aprx = arcpy.mp.ArcGISProject(aprx_path)

    # Check if "newGDB.gdb" already exists within the ArcGIS Pro project
    # If yes, delete it
    newGDB_path = aprx.homeFolder + "\\newGDB.gdb"
    if os.path.exists(newGDB_path):
        arcpy.management.Delete(newGDB_path)
    # Create a new geodatabase to house the loaded data
    newGDB = arcpy.management.CreateFileGDB(aprx.homeFolder, "newGDB.gdb")

    # load the data at data_path into the new geodatabase
    data = load_data(data_path, newGDB_path)

    # map the data that was just loaded
    aprx_map(aprx, data)

    # save the aprx file
    aprx.save()


if __name__ == "__main__":
    workspace = sys.argv[0]
    main()