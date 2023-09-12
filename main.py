'''
Arcpy library is used for data management, analysis, and manipulation. An ArcGIS Pro lisence is required,
but ideally there is no need to create/load projects to perfrom operations. Everything should be
contained within these modules, and projects used as ways to check work.
'''
import arcpy
import sys
import os
import PIL
import matplotlib
import pandas


def sample():
    aprx = arcpy.mp.ArcGISProject(
        r"C:\Users\j2557wan\OneDrive - University of Waterloo\Documents\ArcGIS\Projects\station data explore\station data explore 2.aprx")
    basinpath = r"C:\Users\j2557wan\OneDrive - University of Waterloo\Documents\MondayFileGallery\static_attributes.csv"
    basinoutpath = aprx.defaultGeodatabase + "\\basin_static_table"
    basintable = arcpy.management.CopyRows(basinpath, basinoutpath)
    basinpoints = arcpy.management.XYTableToPoint(basinoutpath, aprx.defaultGeodatabase + "\\basin_points_w_attr", "lon", "lat")



def load_csv(in_path, out_path, convert=False):
    arcpy.management.CopyRows(in_path, out_path)
    f_names = [f.name for f in arcpy.ListFields(out_path)]
    if convert and "lon" in f_names and "lat" in f_names:
        arcpy.management.XYTableToPoint(out_path, out_path + "_points", "lon", "lat")
    return [out_path, out_path + "_points"]


def load_sqlite(in_path, out_path):
    pass


# This function iterates over every file and folder within the given data path, and
# loads valid data types into the project geodatabase
def load_data(path, out_path):
    dir_list = os.listdir(path)
    data_dict = {}

    for file in dir_list:
        filename, filetype = os.path.splitext(os.path.basename(file))

        full_path = path + "\\" + file
        full_out_path = out_path + "\\" + filename

        print("Loading " + file)

        if filetype == ".csv":
            data_dict[filename] = load_csv(full_path, full_out_path, convert=True)
        elif filetype == ".sqlite3":
            data_dict[filename] = load_sqlite(full_path, full_out_path)

    return data_dict


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


def get_data_by_station():
    path = os.path.join(os.path.dirname(__file__), "PWQMN_cleaned\\Provincial_Water_Quality_Monitoring_Network_PWQMN_cleaned.csv")
    df = pandas.read_csv(path)
    grouped = df.grouby()


def main():
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
'''

def main():



if __name__ == "__main__":
    workspace = sys.argv[0]
    main()