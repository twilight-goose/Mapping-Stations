'''
Arcpy library is used for data management, analysis, and manipulation. An ArcGIS Pro lisence is required,
but ideally there is no need to create/load projects to perfrom operations. Everything should be
contained within these modules, and projects used as ways to check work.
'''
import arcpy


class DataManager():
    data_tables = {}

    def __init__(self, *data_path):
        self.load_all(data_path)

    def load_all(self, path_list):
        for path in path_list:
            name = path[path.rindex("\\") + 1:]
            self.data_tables[name] = arcpy.management.CopyRows(path)


def main():
    aprx = arcpy.mp.ArcGISProject(
        r"C:\Users\j2557wan\OneDrive - University of Waterloo\Documents\ArcGIS\Projects\station data explore\station data explore 2.aprx")
    basinpath = r"C:\Users\j2557wan\OneDrive - University of Waterloo\Documents\MondayFileGallery\static_attributes.csv"
    basinoutpath = aprx.defaultGeodatabase + "\\basin_static_table"
    basintable = arcpy.management.CopyRows(basinpath, basinoutpath)
    basinpoints = arcpy.management.XYTableToPoint(basinoutpath, aprx.defaultGeodatabase + "\\basin_points_w_attr", "lon", "lat")


if __name__ == "__main__":
    main()