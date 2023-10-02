from datetime import datetime
"""

Overview:

"""


# ========================================================================= ##
# License ================================================================= ##
# ========================================================================= ##


# ========================================================================= ##
# Classes ================================================================= ##
# ========================================================================= ##


class BBox:
    """
    Class that represents a longitude/latitude bounding box.
    Technically, can be used to represent any bounding rectangle
    with a min x, max x, min y, and max y.

    Provides a framework for bounding box objects and a means of
    adding additional functionality when desired, such as generating
    sql queries with BBox.sql_query().

    Static methods can be called through (1) BBox objects or (2) by
    referencing the class with BBox.<function name> and passing the
    bounding box as a parameter.

    examples:
        1: BBox.<function name>(bbox)
        2: <BBox obj>.<function name>()
    """
    def __init__(self, min_lon=None, max_lon=None, min_lat=None, max_lat=None, *bounds):
        """
        Flexible method for instantiating BoundingBox objects.
        Valid argument sets:

        1. None; Creates an empty BBox Object
        2. 4 keyword arguments in any order;
        3. 4 positional arguments in the following order:
            min_lon, max_lon, min_lat, max_lat
        """
        if len(bounds) == 4:
            min_lon, max_lon, min_lat, max_lat = bounds
        self.bounds = {'min_lon': min_lon, 'max_lon': max_lon,
                       'min_lat': min_lat, 'max_lat': max_lat}

    def contains_point(self, cord: dict) -> bool:
        """
        Determines if the bounding box of self contains cord

        :param self: BBox object or None
        :param cord: {'lon': <float>, 'lat': <float>}
                     Longitude/Latitude coordinate of the point.

        :return: True if cord lies within or on the BBox or BBox is
                 None; False otherwise
        """
        return self is None or \
            (self.bounds['min_lat'] <= cord['lat'] <= self.bounds['max_lat'] and
                self.bounds['min_lon'] <= cord['lon'] <= self.bounds['max_lon'])

    @staticmethod
    def sql_query(bbox, lon_field, lat_field) -> str:
        """
        Translates the bounding box into a SQL query string.

        :param bbox:

        :return: <str>
            SQL query string or a blank string
        """
        query = ""
        # For calls from functions where no boundary is declared
        if bbox is not None:
            min_lon, max_lon = bbox.bounds['min_lon'], bbox.bounds['max_lon']
            min_lat, max_lat = bbox.bounds['min_lat'], bbox.bounds['max_lat']

            query = (f"({min_lon} <= {lon_field} AND {max_lon} >= {lon_field} AND " +
                     f"{min_lat} <= {lat_field} AND {max_lat} >= {lat_field})")

        return query

    @staticmethod
    def filter_df(series, bbox, x_field: str, y_field: str):
        """
        A wrapper function for passing BBox.contains_point to
        <pandas DataFrame>.apply() for the purpose of filtering a
        DataFrame. Not to be used outside the .apply() function

        Works with both pandas DataFrames and Series, without needing
        to import the pandas library.

        :param series: The pandas DataFrame to be scanned
        :param bbox: The bounding box object (or None)
        :param x_field: The name of the x_field of the series
        :param y_field: The name of the y_field of the series

        :return bool:

        :raises ValueError:
        """
        if type(bbox) is BBox or bbox is None:
            return BBox.contains_point(bbox, {'lon': series[x_field], 'lat': series[y_field]})

        raise ValueError("None or BBox object expected but", type(bbox), "found")

    @staticmethod
    def to_tuple(bbox):
        if bbox is None:
            return None
        return (bbox.bounds['min_lon'], bbox.bounds['min_lat'],
                bbox.bounds['max_lon'], bbox.bounds['max_lat'])


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

        :raises TypeError:

                if period is not valid. period is valid if it is either:

                    Tuple/list of (<start date>, <end date>); dates can be
                    either <str> in format "YYYY-MM-DD" or None

                    or

                    None
        """
        if period is not None:
            if len(period) != 2:
                raise TypeError("Period expected 2 values, found", len(period))
            elif type(period) is not list and type(period) is not tuple:
                raise TypeError("Period of wrong type,", type(period), "found")

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
        # if a list or tuple of <str> is passed as the period,
        # convert it to a period object
        if type(period) == list or type(period) == tuple:
            Period.check_period(period)
            period = Period(start=period[0], end=period[1])

        # if no date range is declared, return an empty string
        if period is None or period.is_empty():
            return ""

        # if the period has at least one valid bound, begin
        # building the query
        query, start_f, end_f = "", "", ""

        for field in fields:
            if field.upper() == "DATE":
                start_f = field
            elif field.upper() == "YEAR":
                start_f = field
            elif field.upper() == 'YEAR_FROM':
                start_f = field
            elif field.upper() == 'YEAR_TO':
                end_f = field

        # Construct the SQL query, based on the period bounds and
        # identified date fields

        # period has start_date and end_date
        if period.start and period.end:
            query += f"({start_f} BETWEEN '{period.start}' AND '{period.end}')"
            if end_f:
                query += f" OR ({end_f} BETWEEN '{period.start}' AND '{period.end}')"

        # period has an end_date but no start_date
        elif not period.start and period.end:
            query += f"({start_f} <= '{period.end}')"
            if end_f:
                query += f" OR ({end_f} <= '{period.end}')"

        # period has start_date but no end_date
        else:
            query += f"({start_f} >= '{period.start}')"
            if end_f:
                query += f" OR ({end_f} >= '{period.start}')"

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
