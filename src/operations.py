import geopandas as gpd
import pandas as pd


def find_three_closest(gdf_1:gpd.GeoDataFrame, gdf_2: gpd.GeoDataFrame):
    sindex_1 = gdf_1.