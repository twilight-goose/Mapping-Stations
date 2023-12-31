import sys
import os

dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(dir_path + '/../src')

import load_data
import gdf_utils
import plot_utils
from gen_util import BBox
from matplotlib import pyplot as plt


"""
Expected Terminal Output (file paths preceding "Mapping-Stations" will differ):

>>> python ex1.py

>>> Creating a connection to 'D:\Mapping-Stations\examples/..\data\Hydat\Hydat.sqlite3'
>>> Creating a connection to 'D:\Mapping-Stations\examples/..\data\Hydat\Hydat.sqlite3'
>>> BBox provided but no lat/lon fields found. Skipping BBox query.
>>> Attempting conversion with the following CRS parameter: 4326
>>> Dataframe successfully converted to geopandas point geodataframe

Note: A matplotlib window will open. This window has to be closed manually.
See examples/example_output/ex1.png for expected window appearence.
"""


def main(timed=False):
    # initialize period and bbox of interest
    period = ["2002-10-12", "2003-10-12"]
    bbox = BBox([-80, 45, -79, 46])     # min lon, min lat, max lon, max lat

    # load hydat stations within the bbox coordinates that have
    # flow data during the period of interest and convert it to
    # a geodataframe (a spatially referenced dataframe)
    hydat = load_data.get_hydat_stations(period=period, bbox=bbox)
    hydat_gdf = gdf_utils.point_gdf_from_df(hydat)

    # Begin setting up the plot
    
    # add_map_to_plot can either add a map to an axes or create an axes and
    # add a map to it, and then return it
    ax = plot_utils.add_map_to_plot(extent=bbox)    

    # Add other desired elements to the axes
    ax.set_title('HYDAT Stations')
    plot_utils.add_grid_to_plot(ax=ax)

    # Plot the hydat station data and store the output to configure
    # the legend with
    renderer = plot_utils.plot_gdf(hydat_gdf, ax=ax, color='blue')

    # add a scalebar and annotations to the stations
    plot_utils.add_scalebar(ax=ax)
    plot_utils.annotate_stations(hydat_gdf, ax=ax)

    # using the artist object returned from plot_gdf, configure a legend
    # See plot_utils.configure_legend on more information
    legend_elements = [
        {'label': 'HYDAT', 'renderer': renderer}
    ]
    plot_utils.configure_legend(legend_elements, ax=ax)
    
    if timed:
        plot_utils.timed_display()
    else:
        plt.show()


if __name__ == "__main__":
    main()
