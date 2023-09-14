'''
Arcpy library is used for data management, analysis, and manipulation. An ArcGIS Pro lisence is required,
but ideally there is no need to create/load projects to perfrom operations. Everything should be
contained within these modules, and projects used as ways to check work.
'''
import sys
import Loader
from datetime import datetime


def get_sqlite_table_list(connection):
    pass


def main():
    data = Loader.load_default()


if __name__ == "__main__":
    workspace = sys.argv[0]
    main()