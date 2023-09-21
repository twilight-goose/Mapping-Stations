# ============================================================================= ##
# Bounding Box Class ========================================================== ##
# ============================================================================= ##


class BBox:
    """
    Class that represents a longitude/latitude bound

    Mainly here to provide a framework for bounding box objects and
    provide a means of adding additional functionality when desired
    such as in sql_query
    """
    def __init__(self, min_lon=None, max_lon=None, min_lat=None, max_lat=None, *bounds):
        """
        Flexible method for instantiating BoundingBox objects. Sets
        of valid argument sets:
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

        :param cord: {'lon': <float>, 'lat': <float>}
                     Longitude/Latitude coordinate of the point.

        :return: True if cord lies within or on the BBox; False otherwise
        """
        return self is None or \
            self.bounds['min_lat'] <= cord['lat'] <= self.bounds['max_lat'] and \
            self.bounds['min_lon'] <= cord['lon'] <= self.bounds['max_lon']

    def sql_query(self) -> str:
        """
        Translates the bounding box into a SQL query string

        :return: SQL query string starting with "WHERE"
        """
        # For calls from functions where no boundary is declared
        if self is None:
            return ""
        else:
            min_lon, max_lon = self.bounds['min_lon'], self.bounds['max_lon']
            min_lat, max_lat = self.bounds['min_lat'], self.bounds['max_lat']

            return (f"{min_lon} <= 'LONGITUDE' AND {max_lon} >= 'LONGITUDE' AND " +
                    f"{min_lat} <= 'LATITUDE' AND {max_lat} >= 'LATITUDE'")