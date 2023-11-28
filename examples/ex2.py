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

    # load the data
    hydroRIVERS = load_data.load_rivers(bbox=bbox)
    hydat = load_data.get_hydat_stations(period=period, bbox=bbox)
    hydat_gdf = gdf_utils.point_gdf_from_df(hydat)

    hydroRIVERS = gdf_utils.assign_stations(hydroRIVERS, hydat_gdf)

    # Get the new points and lines connecting the original to new points
    new_points, connectors = gdf_utils.connect_points_to_feature(hydat_gdf, hydroRIVERS)

    # plot setup
    ax = plot_utils.add_map_to_plot(extent=bbox)
    ax.set_title('Projected Location of HYDAT Stations on HydroRIVERS Segments')
    plot_utils.add_grid_to_plot(ax=ax)
    rivers = plot_utils.plot_gdf(hydroRIVERS, color="grey")

    # plot the data
    og = plot_utils.plot_gdf(hydat_gdf, ax=ax, color='blue')
    new = plot_utils.plot_g_series(new_points, ax=ax, color='red')
    connect = plot_utils.plot_g_series(connectors, ax=ax, color='grey', linestyle='--')

    # add some more plot elements
    plot_utils.add_scalebar(ax=ax)
    plot_utils.annotate_stations(hydat_gdf, ax=ax)

    # Configure custom legend
    legend_elements = [
        {'label': 'HYDAT', 'renderer': og},
        {'label': 'NEW', 'renderer': new},
        {'label': 'Connectors', 'renderer': connect},
        {'label': 'HydroRIVERS', 'renderer': rivers}
    ]
    plot_utils.configure_legend(legend_elements, ax=ax)
    
    plt.show()


if __name__ == "__main__":
    main()
    