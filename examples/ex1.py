import sys
import os

dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(dir_path + '/../src')

import load_data
import gdf_utils
import plot_utils
from gen_util import BBox
from matplotlib import pyplot as plt


def main():
    # initialize period and bbox of interest
    period = ["2002-10-12", "2003-10-12"]
    bbox = BBox([-80, 45, -79, 46])

    # load hydat stations within the bbox coordinates that have
    # flow data during the period of interest and convert it to
    # a geodataframe (a spatially referenced dataframe)
    hydat = load_data.get_hydat_stations(period=period, bbox=bbox)
    hydat_gdf = gdf_utils.point_gdf_from_df(hydat)

    # Begin setting up the plot
    # Add a background map, and get the matplotlib axes object that
    # the map was drawn onto
    ax = plot_utils.add_map_to_plot(extent=bbox)

    # Add the other desired elements to the axes
    ax.set_title('HYDAT Stations')
    plot_utils.add_grid_to_plot(ax=ax)

    # Plot the hydat station data and store the output to configure
    # the legend with
    renderer = plot_utils.plot_gdf(hydat_gdf, ax=ax, color='blue')

    # add a scalebar and annotations to the stations
    plot_utils.add_scalebar(ax=ax)
    plot_utils.annotate_stations(hydat_gdf, ax=ax)

    # using the artist object returned from plot_gdf, configure a legend
    legend_elements = [
        {'label': 'HYDAT', 'renderer': renderer}
    ]
    plot_utils.configure_legend(legend_elements, ax=ax)

    plt.show()


if __name__ == "__main__":
    main()
