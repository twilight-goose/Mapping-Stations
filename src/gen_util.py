import cartopy.crs as ccrs
import geopandas as gpd
from datetime import datetime
from shapely import Polygon, Point


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


def check_geom(data, type_str):
    """
    Checks if all geometry in data is of type type_str.

    :param data: GeoDataFrame or GeoSeries
        The dataset to check.

    :param type_str: string
        The type of geometry to check for.

    :return: bool
        True if all geometry in data is of type type_str
    """
    if type(data) is gpd.GeoDataFrame:
        data = data.geometry
    return list(data.geom_type.values).count(type_str) == data.size


# ========================================================================= ##
# Classes ================================================================= ##
# ========================================================================= ##


class BBox:
    """
    Class that represents a longitude/latitude bounding box.
    Functionally a container for a Shapely.Polygon object that
    that defines the geometry of the bounding box. Adds additional
    functionality specific to this project, such as generating sql
    queries with BBox.sql_query() and support for None value BBoxes.

    Static methods can be called through (1) BBox objects or (2) by
    referencing the class with BBox.<function name> and passing the
    bounding box as a parameter.

    For spatial data purposes, the CRS of BBox objects is assumed to
    be Geodetic (lat/lon) to simplify instantiation and avoid dealing
    with CRS format compatibility within this class declaration. To
    change the CRS, refer to set_ccrs().

    examples:
        1: BBox.<function name>(bbox)
        2: <BBox obj>.<function name>()
    """
    def __init__(self, min_x=None, max_x=None, min_y=None, max_y=None, crs=ccrs.Geodetic()):
        """
        Flexible method for instantiating BoundingBox objects.
        Valid argument sets:

        1. None; Creates an empty BBox Object
        2. 4 keyword arguments in any order;
        3. 4 positional arguments in the following order:  min_x, max_x, min_y, max_y
        """
        if hasattr(min_x, '__iter__'):
            assert len(min_x) != 2,\
                "Iterable with len 2 is not a valid input. Valid inputs are: \n" \
                "- None \n- 4 numeric keyword arguments \n" \
                "- 4 numeric positional arguments in the order: min_x, max_x, min_y, max_y"
            min_x, min_y, max_x, max_y = min_x

        self.shape = Polygon([(min_x, min_y), (max_x, min_y), (max_x, max_y), (min_x, max_y)])
        self.crs = crs

    def contains_point(self, point) -> bool:
        """
        Determines if the bounding box of self contains cord

        :param self: BBox object or None

        :param point: list-like or shapely Point
            Coordinates of the Point or a point geometry.

        :return: bool
            True if cord lies within or on the BBox or BBox is None;
            False otherwise
        """
        return self is None or self.shape.contains(Point(point))

    def set_ccrs(self, crs):
        """
        Set the CRS. Does not change the coordinates.

        :param crs: Cartopy CRS object
            The CRS to set the BBox to. Must be a Cartopy.crs.CRS
            object. Refer to the Cartopy documentation for more
            information.
        """
        self.crs = crs

    def to_ccrs(self, crs):
        """
        Generates a tuple of the BBox's bounds in the given CRS. Does
        not change the coordinates of the original BBox.

        Using the provided Cartopy CRS object, transforms bounds to the
        coordinate system defined by the CRS object. Before using this
        function, ensure that self.crs is set to the coordinate system
        of your bounds with set_ccrs().

        :param crs: Cartopy CRS object
            The CRS to transform the BBox to. Must be a Cartopy.crs.CRS
            object.

        :return: tuple
            Transformed min_x, min_y, max_x, max_y coordinates of the
            BBox.
        """
        bounds = self.bounds
        minx, miny, maxx, maxy = crs.transform_point(*bounds[:2], self.crs) + \
                                 crs.transform_point(*bounds[2:], self.crs)
        return BBox([minx, miny, maxx, maxy])

    @property
    def bounds(self):
        return self.shape.bounds

    @staticmethod
    def sql_query(bbox, x_field, y_field) -> str:
        """
        Translates the bounding box into a SQL query string.

        :param bbox: BBox object or None
            The bounding box to generate an SQL query from.

        :param x_field: string
            The name of the field holding coordinate X data.

        :param y_field: string
            The name of the field holding coordinate Y data.

        :return: <str>
            SQL query string or a blank string.
        """
        query = ""
        # For calls from functions where no boundary is declared
        if bbox is not None:
            min_x, min_y, max_x, max_y = bbox.bounds

            query = (f"({min_x} <= {x_field} AND {max_x} >= {x_field} AND " +
                     f"{min_y} <= {y_field} AND {max_y} >= {y_field})")

        return query

    @staticmethod
    def filter_df(series, bbox, x_field: str, y_field: str):
        """
        A wrapper function for passing BBox.contains_point to
        <pandas DataFrame>.apply() for the purpose of filtering a
        DataFrame.

        Scans a row

        :param series: Pandas Series
            The series/row to be scanned

        :param bbox: BBox or None (default)
            BBox object defining area of interest. If None, doesn't
            filter by a bounding box.

        :param x_field: string
            The name of the x_field of the series

        :param y_field: string
            The name of the y_field of the series

        :return: bool

        :raises ValueError:
        """
        if type(bbox) is BBox or bbox is None:
            return BBox.contains_point(bbox, [series[x_field],
                                              series[y_field]])

        raise ValueError("None or BBox object expected but", type(bbox), "found")

    def to_tuple(self):
        """
        Returns min_x, min_y, max_x, max_y of the bounding box.

        :return:
        """
        if self is None:
            return None
        return self.bounds


class Period:
    """
    Class representing a date range.

    start and end should be either strings in "YYYY-MM-DD" format or
    None. If start or end is a 'None' value, that means there is no
    upper/lower bound on the date. If both are 'None', then there are
    no bounds on the date.

    Static methods can be called through (1) Period objects or (2) by
    referencing the class with Period.<function name> and passing the
    period as a parameter.

    examples:
        1: Period.<function name>(period)
        2: <Period obj>.<function name>()
    """
    def __init__(self, start=None, end=None):
        self.start = start
        self.end = end

    def is_empty(self):
        return self.start is None and self.end is None

    @staticmethod
    def check_period(period):
        """
        Checks that period is in a valid period format. Raises an error
        if it's in an invalid format, with a message describing the issue.

        :param period: the period to be checked

        :raises ValueError:

                if period is not valid. period is valid if it is either:

                    Tuple/list of (<start date>, <end date>); dates can be
                    either <str> in format "YYYY-MM-DD" or None

                    or

                    None
        """
        if period is not None:
            if hasattr(period, '__iter__') and len(period) != 2:
                raise ValueError(f"Period expected 2 values, found {len(period)}.")
            elif type(period) is not list and type(period) is not tuple and \
                type(period) != Period:
                raise ValueError(f"Period of wrong type, {type(period)} found.")
            elif period[0] >= period[1]:
                raise ValueError("Period start date must be the same as or after the end date.")

    @staticmethod
    def sql_query(period, fields) -> str:
        """
        Given a list of fields, generates an SQL query based on period
        and identified date fields. Searches for "DATE", "YEAR_FROM",
        and "YEAR_TO".

        :param period: The period to be checked

            Tuple/list of (<start date>, <end date>); dates can be either
            <str> in format "YYYY-MM-DD" or None; If None, all dates
            after(before) the start(end) date are retrieved.

                or

            None; No date query. Does not filter data by date.

        :param fields: list of <field name str> to build the query with

        :return: <str>

            If period (from outer scope) does not have any date bounds
            returns "" (a blank string) to indicate a date query is not
            necessary.

            If period (from outer scope) has date bounds, returns a SQL
            query string.
        """
        def formatter(f_name):
            query = []
            if period.start:
                query.append(f"{f_name} >= {period_start_str}")
            if period.end:
                query.append(f"{f_name} <= {period_end_str}")
            return " OR ".join(query)

        # if a list or tuple of <str> is passed as the period,
        # convert it to a period object
        if type(period) == list or type(period) == tuple:
            Period.check_period(period)
            period = Period(start=period[0], end=period[1])

        # if no date range is declared, return an empty string
        if period is None or period.is_empty():
            return ""

        period_start_str = f"strftime('%Y-%m-%d', '{period.start}')"
        period_end_str = f"strftime('%Y-%m-%d', '{period.end}')"

        # if the period has at least one valid bound, begin
        # building the query
        start_f, end_f = "", ""

        for field in fields:
            if field.upper() == 'YEAR_FROM' or field.upper() == 'DATE':
                start_f = field
            elif field.upper() == 'YEAR_TO':
                end_f = field
            elif field.upper() == 'YEAR' and 'MONTH' in fields:
                start_f = f"strftime('%Y-%m', YEAR || '-' || SUBSTR('00' || MONTH, -2, 2) || '-01')"
                period_start_str = f"strftime('%Y-%m', '{period.start}')"
                period_end_str = f"strftime('%Y-%m', '{period.end}')"

        # Construct the SQL query, based on the period bounds and
        # identified date fields
        query = []
        if start_f:
            query.append(formatter(start_f))
        if end_f:
            query.append(formatter(end_f))
        query = " OR ".join(query)

        return query


class Timer:
    """
    Just for timing operations to compare temporal efficiency
    """
    def __init__(self):
        self.s_time = datetime.now()

    def start(self):
        self.s_time = datetime.now()

    def stop(self):
        d = datetime.now() - self.s_time
        print("That took {0} seconds and {1} microseconds\n".format(d.seconds, d.microseconds))



ON_bbox = BBox(min_x=-95.154826, max_x=-74.343496, min_y=41.681435, max_y=56.859036)
