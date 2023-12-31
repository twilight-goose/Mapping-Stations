import cartopy.crs as ccrs
import geopandas as gpd
import pandas as pd
from datetime import datetime
from datetime import timedelta
from datetime import date
from shapely import Polygon, Point


# ========================================================================= ##
# License ================================================================= ##
# ========================================================================= ##

# Copyright (c) 2023 James Wang - jcw4698(at)gmail.com
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# ========================================================================= ##
# ========================================================================= ##
# ========================================================================= ##

# Lambert conformal conic paramaters
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


# ========================================================================= ##
# Functions =============================================================== ##
# ========================================================================= ##


def find_xy_fields(fields) -> [str, str]:
    """
    Searches a list, tuple, or pandas DataFrame for specific field
    names to use as longitudinal and latitudinal values.

    If more than 1 match is found for X or Y, "Failed" will be
    returned. If no match is found for X or Y, an empty string
    will be returned. Not case-sensitive.

    :param fields: Pandas DataFrame or list-like of str
        The object to search. If a Pandas DataFrame is passed,
        column values will be used. 

    :return: list-like of str of length 2
        The result of the search for x and y fields, where each item
        in the list is either the field name or "Failed".
        i.e:
            [<X field name> or "Failed", <Y field name> or "Failed"]
            
    tests:
    >>> import pandas as pd
    >>> data = {"X": [1], "Y", [2]}
    >>> df = pd.DataFrame(data)
    >>> assert find_xy_fields(df) == ("X", "Y")
    >>> assert find_xy_fields(["X", "Y"]) == ("X", "Y")
    >>> assert find_xy_fields(["lat", "lon"]) == ("lon", "lat")
    >>> assert find_xy_fields(["x", "y", "lon"]) == ("Failed", "y
    >>> assert find_xy_fields(["day", "y"]) == ("", "y")
    """
    # simple helper function
    def _(i, field_name) -> str:
        return field_name if i == "" else "Failed"

    # initiate x and y
    x, y = "", ""
    
    if type(fields) is pd.DataFrame:
        fields = fields.columns.values
    # Iterate through dataframe field names
    for field in fields:
        # Check if the field matches one of the X or Y field names
        if field.upper() in ["LON", "LONG", "LONGITUDE", "X"]:
            x = _(x, field)
        elif field.upper() in ["LAT", "LATITUDE", "Y"]:
            y = _(y, field)

    return x, y


def check_geom(data, type_str):
    """
    Checks if all geometry in data is of type type_str using
    GeoSeries.geom_type.

    :param data: GeoDataFrame or GeoSeries
        The dataset to check.

    :param type_str: string
        The type of geometry to check for.

    :return: bool
        True if all geometry in data is of type type_str.
    """
    if type(data) is gpd.GeoDataFrame:
        data = data.geometry
        
    return list(data.geom_type.values).count(type_str) == data.size


def days_overlapped(start1, end1, start2, end2):
    """
    Calculates the number of days of overlap between periods
    defined by start and end dates.
    
    :param start1: str
        The start date of period 1.
        
    :param end1: str
        The end date of period 1.
    
    :param start2: str
        The start date of period 2.
    
    :param end2: str
        The end date of period 2.
        
    :return: int
        The number of days of overlap between the 2 periods.
        
    test:
    >>> dates1 = ["2002-02-12", "2005-10-12", "2006-04-12", "2008-10-12"]
    >>> dates2 = ["2002-02-12", "2002-04-17", "2002-04-15", "2002-10-21"]
    >>> assert days_overlapped(*dates1) == 0
    >>> assert days_overlapped(*dates2) == 3
    """
    start = date.fromisoformat(max(start1, start2))
    end = date.fromisoformat(min(end1, end2))
    delta = end - start
    days = delta.days
    
    if days >= 0:
        return days + 1
    else:
        return 0


def period_overlap(ps1, ps2):
    """
    Caculates the number of days that overlap between two sets of
    periods. Period sets may be either list-like or DataFrame but
    must both be of the same type.
    
    If list-like, a set of periods must be of the shape (N, 2) where
    N is the number of periods within the set, and the first element
    (index 0) is the start date and the second element (index 1) is
    the end date. If a period set has overlapping dates,
    ie (["2020-10-12", "2020-10-17"], ["2020-10-17", "2020-10-25"])
    unexpected behaviour may occur.
    
    If DataFrame, the set of periods must contain a 'P_Start' and
    a 'P_End' column.
    
    :param ps1: list-like or DataFrame
        The first set of periods.
    
    :param ps2: like-like or DataFrame
        The other set of periods.
    
    :return: int
        The total number of days of overlap between ps1 and ps2.
        
    tests:
    >>> periods1 = [["2002-02-12", "2005-10-12"], ["2006-04-12", "2008-10-12"]]
    
    >>> periods2 = [["2002-02-12", "2002-02-12"], ["2004-02-12", "2004-02-12"],
                    ["2005-10-12", "2005-10-13"], ["2006-04-11", "2006-04-12"],
                    ["2006-06-12", "2007-06-12"], ["2008-10-12", "2008-10-13"]]
                
    >>> periods3 = [["2005-10-10", "2006-04-20"]]
                
    >>> expected = 1 + 1 + 1 + 1 + 366 + 1
    
    >>> assert days_overlapped(*periods1[0], *periods2[0]) == 1
    >>> assert days_overlapped(*periods1[0], *periods2[2]) == 1
    >>> assert days_overlapped(*periods1[0], *periods2[3]) == 0
    >>> assert days_overlapped(*periods1[1], *periods2[0]) == 0
    >>> assert days_overlapped(*periods1[1], *periods2[3]) == 1
    >>> assert days_overlapped(*periods1[0], "2005-10-10", "2005-10-13") == 3
    >>> assert days_overlapped(*periods1[0], "2005-10-01", "2005-10-10") == 10
    
    >>> assert period_overlap(periods1, periods2) == expected
    >>> assert period_overlap(periods1, periods3) == 12
    """
    if type(ps1) is type(ps2):
        p_ind = 0
        h_ind = 0
        total_overlap = 0
        
        if type(ps1) is pd.DataFrame:
            ps1 = ps1.sort_values(by="P_Start")
            ps2 = ps2.sort_values(by="P_Start")
            
            h_len = ps1.shape[0]
            p_len = ps2.shape[0]
            
        elif type(ps1) is list:
            ps1 = ps1.sort()
            ps2 = ps2.sort()
        
            h_len = len(ps1)
            p_len = len(ps2)
        
        while h_ind < h_len and p_ind < p_len:
            
            if type(ps1) is pd.DataFrame:
                h_start, h_end = ps1.iloc[h_ind]['P_Start'], ps1.iloc[h_ind]['P_End']
                p_start, p_end = ps2.iloc[p_ind]['P_Start'], ps2.iloc[p_ind]['P_End']
                
            elif type(ps1) is list:
                h_start, h_end = ps1[h_ind]
                p_start, p_end = ps2[p_ind]
            
            # check if the current periods overlap
            if h_end < p_start:
                h_ind += 1
            elif p_end < h_start:
                p_ind += 1
            else:
                # if the current periods overlap, calculate the overlap
                # and add it to the total_days of overlap
                overlap = days_overlapped(h_start, h_end, p_start, p_end)
                if overlap >= 1:
                    total_overlap += overlap
                
                # overlap between these two periods has been calculated,
                # so move to the next two periods
                if h_end > p_end:
                    # if h_end > p_end, the next p period could overlap with
                    # the current h period, so increment only p
                    p_ind += 1
                elif h_end < p_end:
                # if h_end < p_end, the next h period could overlap with
                    # the current h period, so increment only h
                    h_ind += 1
                else:
                    # if h_end == p_end the periods ended on the same day
                    # and neither of them can overlap with the next periods
                    p_ind += 1
                    h_ind += 1
                    
        return total_overlap
    else:
        print("periods not in same format. No calculation performed.")

# ========================================================================= ##
# Classes ================================================================= ##
# ========================================================================= ##


class BBox:
    """
    Class that represents a longitude/latitude bounding box.
    Functionally a container for a Shapely.Polygon object that
    that defines the geometry of the bounding box. Adds additional
    functionality specific to this project, such as generating sql
    queries with BBox.sql_query().

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
        
    tests:
    
    >>> bbox1 = BBox(min_x=-80, max_x=-79.5, min_y=45, max_y=45.5)
    >>> bbox2 = BBox(-80, -79.5, 45, 45.5)
    
    >>> assert bbox1.bounds == bbox2.bounds == bbox1.to_tuple() == bbox2.to_tuple()
    
    >>> assert bbox1.contains_point((-79.9, 45.2)) == True
    >>> assert bbox1.contains_point((-89, 45.2)) == False
    >>> assert bbox1.contains_point((-80, 45)) == False
    
    >>> assert bbox1.sql_query('X', 'Y') == "(-80.0 <= X AND -79.5 >= X AND 45.0 <= Y AND 45.5 >= Y)"
    >>> assert bbox2.sql_query('X', 'Y') == "(-80.0 <= X AND -79.5 >= X AND 45.0 <= Y AND 45.5 >= Y)"
    
    >>> assert BBox.sql_query(bbox1, 'X', 'Y') == "(-80.0 <= X AND -79.5 >= X AND 45.0 <= Y AND 45.5 >= Y)"
    >>> assert BBox.sql_query(bbox2, 'X', 'Y') == "(-80.0 <= X AND -79.5 >= X AND 45.0 <= Y AND 45.5 >= Y)"
    """
    def __init__(self, min_x=None, max_x=None, min_y=None, max_y=None, crs=ccrs.Geodetic()):
        """
        Flexible method for instantiating BoundingBox objects.
        Valid argument sets:

        1. 4 keyword arguments in any order;
        3. 4 positional arguments in the following order:  min_x, max_x, min_y, max_y
        """
        if type(min_x) is list or type(min_x) is tuple:
            min_x, min_y, max_x, max_y = min_x

        self.shape = Polygon([(min_x, min_y), (max_x, min_y), (max_x, max_y), (min_x, max_y)])
        self.crs = crs

    def contains_point(self, point) -> bool:
        """
        Determines if the bounding box of self contains cord.

        :param self: BBox object or None

        :param point: list-like or shapely Point
            Coordinates of the Point or a point geometry.

        :return: bool
            True if cord lies within the BBox; False otherwise.
        """
        return self.shape.contains(Point(point))

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
        """
        The bounding coordinates of the BBox. In the order
        minx, miny, maxx, maxy.
        
        :return: tuple of int   
            The bounding coorindates of the BBox.
        """
        return self.shape.bounds
    
    def sql_query(self, x_field, y_field) -> str:
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
        if self is not None:
            min_x, min_y, max_x, max_y = self.bounds

            query = (f"({min_x} <= {x_field} AND {max_x} >= {x_field} AND " +
                     f"{min_y} <= {y_field} AND {max_y} >= {y_field})")

        return query

    def to_tuple(self):
        """
        Returns min_x, min_y, max_x, max_y of the bounding box.
        Wrapper for the bounds property.

        :return: tuple of int of length 4
            The bounding coorindates of the BBox.
        """
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
        """
        :return: bool
            True if the period has no start and no end date.
        """
        return self.start is None and self.end is None
        
    @staticmethod
    def from_list(period):
        """
        Generates a period object from a list of 2 dates.
        
        :param period: list-like of str of length 2
            List-like of (<start date>, <end date>).
        
        :return: Period object
            A Period object representing the date range.
        """
        return Period(start=period[0], end=period[1])

    @staticmethod
    def check_period(period):
        """
        Checks that period is in a valid period format. Raises an error
        if it's in an invalid format, with a message describing the issue.

        :param period: list or tuple or None
            The period to be checked

        :return: True
            If the period is valid, returns True. Otherwise, raises a ValueError.

        :raises ValueError:

                Ff period is not valid. period is valid if it is either:

                    Tuple/list of (<start date>, <end date>); dates can be
                    either <str> in format "YYYY-MM-DD" or None

                    or

                    None
        
        tests:
            period1 = ['2020-10-11', None]
            period2 = [None, '2020-10-11']
            period3 = ['2020-09-11', '2020-10-11']
            
            assert Period.check_period(period1) is None
            assert Period.check_period(period2) is None
            assert Period.check_period(period3) is None
            
            # invalid periods
            pytest.raises(ValueError, Period.check_period, ['2010-10-11', '2009-11-11'])
            pytest.raises(ValueError, Period.check_period, "2022-10-11")
            pytest.raises(ValueError, Period.check_period, ["2022-10-11"])
            pytest.raises(ValueError, Period.check_period, ["", "", ""])
        """
        if period is not None:
            if type(period) in (list, tuple) and len(period) != 2:
                raise ValueError(f"Period expected 2 values, found {len(period)}.")
            elif type(period) is not list and type(period) is not tuple and \
                 type(period) != Period:
                raise ValueError(f"Period of wrong type, {type(period)} found.")
            elif not (period[0] is None) and not (period[1] is None) and period[0] >= period[1]:
                raise ValueError("Period start date must be the same as or after the end date.")
                
        return True

    def sql_query(period, fields) -> str:
        """
        Given a list of fields, generates an SQL query based on period
        and identified date fields. Searches for "DATE", "YEAR_FROM",
        "YEAR_TO", "YEAR", and "MONTH".

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
        
        tests:
            period1 = ['2020-10-11', None]
            period2 = [None, '2020-10-11']
            period3 = ['2020-09-11', '2020-10-11']
            
            assert Period.sql_query(period1, ['DATE']) == \
                "(strftime('%Y-%m-%d', '2020-10-11') <= DATE AND DATE <= strftime('%Y-%m-%d', '9999-12-31'))"
            assert Period.sql_query(period1, ['YEAR_FROM', 'YEAR_TO']) == \
                "(strftime('%Y', '2020-10-11') <= YEAR_FROM AND YEAR_FROM <= strftime('%Y', '9999-12-31')) OR " + \
                "(strftime('%Y', '2020-10-11') <= YEAR_TO AND YEAR_TO <= strftime('%Y', '9999-12-31')) OR " + \
                "(YEAR_FROM <= strftime('%Y', '2020-10-11') AND strftime('%Y', '2020-10-11') <= YEAR_TO) OR " + \
                "(YEAR_FROM <= strftime('%Y', '9999-12-31') AND strftime('%Y', '9999-12-31') <= YEAR_TO)"
            assert Period.sql_query(period1, ['YEAR', 'MONTH']) == \
                "(strftime('%Y-%m', '2020-10-11') <= " + \
                "strftime('%Y-%m', YEAR || '-' || SUBSTR('00' || MONTH, -2, 2) || '-01') AND " + \
                "strftime('%Y-%m', YEAR || '-' || SUBSTR('00' || MONTH, -2, 2) || '-01') <= " + \
                "strftime('%Y-%m', '9999-12-31'))"
                
            assert Period.sql_query(period2, ['DATE']) == \
                "(strftime('%Y-%m-%d', '0000-01-01') <= DATE AND DATE <= strftime('%Y-%m-%d', '2020-10-11'))"
            assert Period.sql_query(period2, ['YEAR_FROM', 'YEAR_TO']) == \
                "(strftime('%Y', '0000-01-01') <= YEAR_FROM AND YEAR_FROM <= strftime('%Y', '2020-10-11')) OR " + \
                "(strftime('%Y', '0000-01-01') <= YEAR_TO AND YEAR_TO <= strftime('%Y', '2020-10-11')) OR " + \
                "(YEAR_FROM <= strftime('%Y', '0000-01-01') AND strftime('%Y', '0000-01-01') <= YEAR_TO) OR " + \
                "(YEAR_FROM <= strftime('%Y', '2020-10-11') AND strftime('%Y', '2020-10-11') <= YEAR_TO)"
            assert Period.sql_query(period2, ['YEAR', 'MONTH']) == \
                "(strftime('%Y-%m', '0000-01-01') <= " + \
                "strftime('%Y-%m', YEAR || '-' || SUBSTR('00' || MONTH, -2, 2) || '-01') AND " + \
                "strftime('%Y-%m', YEAR || '-' || SUBSTR('00' || MONTH, -2, 2) || '-01') <= " + \
                "strftime('%Y-%m', '2020-10-11'))"
                
            assert Period.sql_query(period3, ['DATE']) == \
                "(strftime('%Y-%m-%d', '2020-09-11') <= DATE AND DATE <= strftime('%Y-%m-%d', '2020-10-11'))"
            assert Period.sql_query(period3, ['YEAR_FROM', 'YEAR_TO']) == \
                "(strftime('%Y', '2020-09-11') <= YEAR_FROM AND YEAR_FROM <= strftime('%Y', '2020-10-11')) OR " + \
                "(strftime('%Y', '2020-09-11') <= YEAR_TO AND YEAR_TO <= strftime('%Y', '2020-10-11')) OR " + \
                "(YEAR_FROM <= strftime('%Y', '2020-09-11') AND strftime('%Y', '2020-09-11') <= YEAR_TO) OR " + \
                "(YEAR_FROM <= strftime('%Y', '2020-10-11') AND strftime('%Y', '2020-10-11') <= YEAR_TO)"
            assert Period.sql_query(period3, ['YEAR', 'MONTH']) == \
                "(strftime('%Y-%m', '2020-09-11') <= " + \
                "strftime('%Y-%m', YEAR || '-' || SUBSTR('00' || MONTH, -2, 2) || '-01') AND " + \
                "strftime('%Y-%m', YEAR || '-' || SUBSTR('00' || MONTH, -2, 2) || '-01') <= " + \
                "strftime('%Y-%m', '2020-10-11'))"
        """
        def formatter(f_name):
            return f"({p_start_str} <= {f_name} AND {f_name} <= {p_end_str})"
        
        def formatter_2():
            return f"({start_f} <= {p_start_str} AND {p_start_str} <= {end_f}) OR " + \
                   f"({start_f} <= {p_end_str} AND {p_end_str} <= {end_f})"
                   
        # if a list or tuple of <str> is passed as the period,
        # convert it to a period object
        if type(period) == list or type(period) == tuple:
            Period.check_period(period)
            period = Period(start=period[0], end=period[1])
        
        p_start = period.start if not (period.start is None) else "0000-01-01"
        p_end = period.end if not (period.end is None) else "9999-12-31"
       
        # if the period has at least one valid bound, begin
        # building the query
        start_f, end_f = "", ""
        time_fmt_str = '%Y-%m-%d'
        
        for field in fields:
            if field.upper() in ['DATE', 'P_START']:
                start_f = field
            if field.upper() in ['YEAR_TO', 'P_END']:
                end_f = field
            elif field.upper() == 'YEAR' and 'MONTH' in fields:
                time_fmt_str = '%Y-%m'
                start_f = f"strftime('%Y-%m', YEAR || '-' || SUBSTR('00' || MONTH, -2, 2) || '-01')"
            elif field.upper() == 'YEAR_FROM':
                start_f = field
                time_fmt_str = '%Y'
            
        p_start_str = f"strftime('{time_fmt_str}', '{p_start}')"
        p_end_str = f"strftime('{time_fmt_str}', '{p_end}')"

        # Construct the SQL query, based on the period bounds and
        # identified date fields
        query = []
        if start_f:
            query.append(formatter(start_f))
        if end_f:
            query.append(formatter(end_f))
        if start_f and end_f:
            query.append(formatter_2())
    
        query = " OR ".join(query)
        return query
    
    @staticmethod
    def get_periods(dates=None,silent=True):
        """
            Returns the periods of consecutive dates from a provided list of dates.


            Definition
            ----------
            def get_periods(dates,silent=True):


            Input           Format          Description
            -----           -----           -----------
            dates           list            List of dates in format YYYY-MM-DD.
                                            Default: None

            silent          Boolean         If set to True, nothing will be printed to terminal.
                                            Default: True


            Output          Format          Description
            -----           -----           -----------
            periods         list(lists)     List of lists containing start and end date of each period of consecutive dates. For example,
                                            [ [2000-01-01,2000-12-31], [2001-02-01, 2001,12,31] ]
                                            if dates for January 2001 are missing.


            Description
            -----------
            Reads data of a station (or list of stations) for one specific variable from a STREAMFLOW dataset.


            Restrictions
            ------------
            Expected to be dates in format YYYY-MM-DD. Sub-daily dates are not considered.


            Examples
            --------

            Find periods

            >>> dates = ['1991-02-01', '1991-02-02', '1991-02-03', '1991-02-04', '1991-02-05', '1991-02-06', '1991-02-07']
            >>> periods = get_periods(dates=dates,silent=True)
            >>> print("periods = {}".format(periods))
            periods = [['1991-02-01', '1991-02-07']]

            >>> dates = ['1991-02-01', '1991-02-02', '1991-02-03', '1991-02-05', '1991-02-06', '1991-02-07']
            >>> periods = get_periods(dates=dates,silent=True)
            >>> print("periods = {}".format(periods))
            periods = [['1991-02-01', '1991-02-03'], ['1991-02-05', '1991-02-07']]
            
            tests:
                dates = ['1991-02-01', '1991-02-02', '1991-02-03', '1991-02-04', '1991-02-05', '1991-02-06', '1991-02-07']
                periods = Period.get_periods(dates=dates,silent=True)
                assert periods == [['1991-02-01', '1991-02-07']]

                dates = ['1991-02-01', '1991-02-02', '1991-02-03', '1991-02-05', '1991-02-06', '1991-02-07']
                periods = Period.get_periods(dates=dates,silent=True)
                assert periods == [['1991-02-01', '1991-02-03'], ['1991-02-05', '1991-02-07']]

            License
            -------
            This file is part of the PWQMN toolbox library which contains scripts to
            retrieve raw PWQMN data, preprocessing them, run models using these data,
            or analysing the data in any other shape or form..

            The PWQMN code library is free software: you can redistribute it and/or modify
            it under the terms of the GNU Lesser General Public License as published by
            the Free Software Foundation, either version 2.1 of the License, or
            (at your option) any later version.

            The PWQMN code library is distributed in the hope that it will be useful,
            but WITHOUT ANY WARRANTY; without even the implied warranty of
            MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
            GNU Lesser General Public License for more details.

            You should have received a copy of the GNU Lesser General Public License
            along with The PWQMN code library.
            If not, see <https://github.com/julemai/PWQMN/blob/main/LICENSE>.

            Copyright 2022-2023 Juliane Mai - juliane.mai@uwaterloo.ca


            History
            -------
            Written,  Juliane Mai, January 2023
            Modified, James Wang, November 2023
        """
        # initialize return
        periods = []

        # check inputs
        if dates is None:
            raise ValueError("get_periods: list of dates in format YYYY-MM-DD needs to be provided.")

        start = None
        last = None
        
        for idates in dates:
        
            if start is None:
                start = idates
            else:
                if datetime.strptime(idates, "%Y-%m-%d") != \
                        datetime.strptime(last, "%Y-%m-%d") + timedelta(days=1):
                    periods.append([start, last])
                    start = idates
            last = idates
        periods.append([start, last])

        return periods
    
    def generate_data_range(obs):
        """
        Produces data ranges from a DataFrame of dates and station ids.
        Each row of the output DataFrame holds a start and end date for
        when data is availabe for that given station. Station IDs are
        not unique, in the situation where stations have records 
        available at 2 different periods of time.
        
        i.e. (11/11/2001 - 12/09/2002), (11/17/2005 - 12/09/2007) will
            be stored in 2 different rows.
        
        :param obs: DataFrame
            DataFrame containing observation data. Must contain
            "Date" and "Station_ID" fields. Neither need to be unique.
        
        :return: DataFrame
            The date ranges. Has the following structure:
            
            Station_ID | P_Start | P_End |
        """
        def add_to_output(st_id, start, end):
            out_data['Station_ID'].append(st_id)
            out_data['P_Start'].append(start)
            out_data['P_End'].append(end)
            delta = date.fromisoformat(end) - date.fromisoformat(start)
            out_data['Num_Days'].append(delta.days + 1)
        
        obs['Date'] = pd.to_datetime(obs['Date'])
        obs['Date'] = obs['Date'].dt.strftime("%Y-%m-%d")
        
        grouped = obs.groupby(by="Station_ID")
        
        out_data = {'Station_ID': [], 'P_Start': [], 'P_End': [], 'Num_Days': []}
        
        for key, sub_df in grouped:
            dates = sub_df['Date'].sort_values().to_list()
            start = None
            last = None
            
            for idate in dates:
                if start is None:
                    start = idate
                else:
                    str_date = datetime.strptime(idate, "%Y-%m-%d")
                    str_last = datetime.strptime(last, "%Y-%m-%d")
                    
                    if  str_date != str_last + timedelta(days=1) and str_date != str_last:
                        add_to_output(key, start, last)
                        start = idate
                        
                last = idate
            add_to_output(key, start, last)
      
        return pd.DataFrame(out_data)
        
    @staticmethod
    def check_data_range(period, dates):
        """
        Checks that all date ranges in dates overlaps with period
        (inclusive).
        
        :param period: list-like of string of length 2
            The period to check dates against.
        
        :param dates: DataFrame
            Periods to check; must contain "P_Start" and
            "P_End" columns.
            
        :return: bool
            Returns True if all date ranges in dates overlap with 
            period, False otherwise (inclusive).
            
        tests:
        >>> period = ["2002-10-14", "2003-05-01"]
        >>> dates1 = {"P_Start": ["2002-10-14", "2003-01-14", "2003-05-01"],
                      "P_End": ["2002-10-14", "2003-01-14", "2003-05-01"]}
        >>> dates2 = {"P_Start": ["2002-10-14", "2003-01-14", "2003-05-02"],
                      "P_End": ["2002-10-14", "2003-01-14", "2003-05-02"]}
        >>> dates1 = pd.DataFrame(dates1)
        >>> dates2 = pd.DataFrame(dates2)
        >>> assert Period.check_data_range(period, dates1) == True
        >>> assert Period.check_data_range(period, dates2) == False
        """
        n = 0
        for ind, row in dates.iterrows():
            start = row['P_Start']
            end = row['P_End']
            
            if not (period[0] is None) and not (period [1] is None):
                if not ((start <= period[0] <= end) or \
                        (start <= period[1] <= end) or \
                        (period[0] <= start <= period[1]) or \
                        (period[0] <= end <= period[1])):
                    print("date range out of period:", start, end)
                    n+=1
            elif period[0] is None:
                if not (start <= period[1]):
                    print("date range out of period:", start, end)
                    n+=1
            elif period[1] is None:
                if not (period[0] <= end):
                    # If functions correctly, nothing is outputted
                    print("date range out of period:", start, end)
                    n+=1
                    
        print(f"{n} date ranges were incorrect")
        return n == 0


class Timer:
    """
    Just for timing operations to compare temporal efficiency.
    """
    def __init__(self):
        self.s_time = datetime.now()

    def start(self):
        self.s_time = datetime.now()

    def stop(self):
        d = datetime.now() - self.s_time
        print("That took {0} seconds and {1} microseconds\n".format(d.seconds, d.microseconds))


ON_bbox = BBox(min_x=-95.154826, max_x=-74.343496, min_y=41.681435, max_y=56.859036)
