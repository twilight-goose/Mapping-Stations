import load_data
import gdf_utils


df = load_data.get_hydat_station_data()
gdf = gdf_utils.point_gdf_from_df(df)
gdf.to_file('hydat.shp')