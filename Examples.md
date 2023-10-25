# Examples

## Part 1: Basic Loading and Plotting

```python
import load_data
import gdf_utils
import plot_utils
from gen_util import BBox

period = ["2002-10-12", "2003-10-12"]
bbox = BBox([-80, 45, -79, 46])

hydat = load_data.get_hydat_station_data(period, bbox)
hydat_gdf = gdf_utils.point_gdf_from_df(hydat)

ax = plot_utils.add_map_to_plot(extent=bbox)
ax.set_title('HYDAT Stations')
plot_utils.add_grid_to_plot(ax=ax)
plot_utils.plot_gdf(hydat_gdf, ax=ax)
plot_utils.add_scalebar(ax=ax)
plot_utils.annotate_stations(hydat_gdf, ax=ax)
plot_utils.show()
```
![Example_1.png](plots%2FExample_1.png)
## Part 2: