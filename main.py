'''
Arcpy library is used for data management, analysis, and manipulation. An ArcGIS Pro lisence is required,
but ideally there is no need to create/load projects to perfrom operations. Everything should be
contained within these modules, and projects used as ways to check work.
'''
import arcpy
import sys
import os


def sample():
    aprx = arcpy.mp.ArcGISProject(
        r"C:\Users\j2557wan\OneDrive - University of Waterloo\Documents\ArcGIS\Projects\station data explore\station data explore 2.aprx")
    basinpath = r"C:\Users\j2557wan\OneDrive - University of Waterloo\Documents\MondayFileGallery\static_attributes.csv"
    basinoutpath = aprx.defaultGeodatabase + "\\basin_static_table"
    basintable = arcpy.management.CopyRows(basinpath, basinoutpath)
    basinpoints = arcpy.management.XYTableToPoint(basinoutpath, aprx.defaultGeodatabase + "\\basin_points_w_attr", "lon", "lat")


def load_csv(in_path, out_path):
    arcpy.management.CopyRows(in_path, out_path)
    f_names = [f.name for f in arcpy.ListFields(out_path)]
    if "lon" in f_names and "lat" in f_names:
        arcpy.management.XYTableToPoint(out_path, out_path + "_points", "lon", "lat")
    return [out_path, out_path + "_points"]


def load_sqlite(in_path, out_path):
    pass


def load_data(path, out_path):
    dir_list = os.listdir(path)
    data_dict = {}

    for file in dir_list:
        filename, filetype = os.path.splitext(os.path.basename(file))

        full_path = path + "\\" + file
        full_out_path = out_path + "\\" + filename

        print("Loading " + file)

        if filetype == ".csv":
            data_dict[filename] = load_csv(full_path, full_out_path)
        elif filetype == ".sqlite3":
            data_dict[filename] = load_sqlite(full_path, full_out_path)

    return data_dict


def aprx_map(aprx, data):
    n = len(aprx.listMaps())
    newMap = aprx.createMap("Map " + str(n + 1))
    for key in data.keys():
        try:
            newMap.addDataFromPath(data[key][1])
        except RuntimeError:
            pass
        aprx.save()


def main():
    data_path = input("Data Folder Path:\n")
    aprx_path = input("ArcGIS Project Path:\n")

    if data_path == "":
        data_path = r"C:\Users\j2557wan\OneDrive - University of Waterloo\Documents\MondayFileGallery"
    if aprx_path == "":
        aprx_path = r"C:\Users\j2557wan\OneDrive - University of Waterloo\Documents\ArcGIS\Projects\station data explore\station data explore 2.aprx"

    aprx = arcpy.mp.ArcGISProject(aprx_path)
    if os.path.exists(aprx.homeFolder + "\\newGDB.gdb"):
        arcpy.management.Delete(aprx.homeFolder + "\\newGDB.gdb")
    arcpy.management.CreateFileGDB(aprx.homeFolder, "newGDB.gdb")

    data = load_data(data_path, aprx.homeFolder + "\\newGDB.gdb")

    aprx_map(aprx, data)
    aprx.save()


if __name__ == "__main__":
    main()