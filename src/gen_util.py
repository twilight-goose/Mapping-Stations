import os.path
import cartopy.crs as ccrs


central_lon = -85
central_lat = 40
stand_parallel_1 = 50
stand_parallel_2 = 70

# WKT string for Canadian lambert conformal conic projection
# refer to the source for projected and WGS84 bounds
# As of 2023-10-02:
#   Center coordinates: 261638.61 2500407.04
#   Projected bounds: -3827665.83  -207619.51
#                      4510310.33  5481591.53
#   WGS84 bounds: -141.01  38.21
#                  -40.73  86.46
# source: https://epsg.io/102002
Can_LCC_wkt = ('PROJCS["Canada_Lambert_Conformal_Conic",'
                    'GEOGCS["NAD83",'
                        'DATUM["North_American_Datum_1983",'
                            'SPHEROID["GRS 1980",6378137,298.257222101,'
                                'AUTHORITY["EPSG","7019"]],'
                            'AUTHORITY["EPSG","6269"]],'
                        'PRIMEM["Greenwich",0,'
                            'AUTHORITY["EPSG","8901"]],'
                        'UNIT["degree",0.0174532925199433,'
                            'AUTHORITY["EPSG","9122"]],'
                        'AUTHORITY["EPSG","4269"]],'
                    'PROJECTION["Lambert_Conformal_Conic_2SP"],'
                    f'PARAMETER["latitude_of_origin",{central_lat}],'
                    f'PARAMETER["central_meridian",{central_lon}]'
                    f'PARAMETER["standard_parallel_1",{stand_parallel_1}],'
                    f'PARAMETER["standard_parallel_2",{stand_parallel_2}],'
                    'PARAMETER["false_easting",0],'
                    'PARAMETER["false_northing",0],'
                    'UNIT["metre",1,'
                        'AUTHORITY["EPSG","9001"]],'
                    'AXIS["Easting",EAST],'
                    'AXIS["Northing",NORTH],'
                    'AUTHORITY["ESRI","102002"]]')

# Coordinate Reference System Constants
geodetic = ccrs.Geodetic()
lambert = ccrs.LambertConformal(central_longitude=central_lon,
                                central_latitude=central_lat,
                                standard_parallels=(stand_parallel_1,
                                                    stand_parallel_2))



def find_xy_fields(df) -> [str, str]:
    """
    Searches a pandas DataFrame for specific field names to use as
    longitudinal and latitudinal values.

    If more than 1 match is found for X or Y, "Failed" will be
    returned. If no match is found for X or Y, an empty string
    will be returned. Not case-sensitive.

    :param df: Pandas DataFrame
        The DataFrame to search

    :return: list-like of strings of length 2
        The result of the search for x and y fields, where each item
        in the list is either the field name or "Failed"
        i.e:
            [<X field name> or "Failed", <Y field name> or "Failed"]
    """

    # simple helper function
    def _(i, field_name) -> str:
        return field_name if i == "" else "Failed"

    # initiate x and y
    x, y = "", ""

    # Iterate through dataframe field names
    for field in df.columns.values:
        # Check if the field matches one of the X or Y field names
        if field.upper() in ["LON", "LONG", "LONGITUDE", "X"]:
            x = _(x, field)
        elif field.upper() in ["LAT", "LATITUDE", "Y"]:
            y = _(y, field)

    return x, y

