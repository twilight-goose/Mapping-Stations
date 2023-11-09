import pytest
from gen_util import BBox, Period, ON_bbox


def test_bbox(self):
    bbox1 = BBox(min_x=-80, max_x=-79.5, min_y=45, max_y=45.5)
    bbox2 = BBox(-80, -79.5, 45, 45.5)
    
    assert bbox1.bounds == bbox2.bounds == bbox1.to_tuple() == bbox2.to_tuple()
    
    assert bbox1.contains_point((-79.9, 45.2)) == True
    assert bbox1.contains_point((-89, 45.2)) == False
    assert bbox1.contains_point((-80, 45)) == True
    
    assert bbox1.sql_query('X', 'Y') == "-80 <= X AND -79.5 >= X AND 45 <= Y AND 45.5 >= Y"
    assert bbox2.sql_query('X', 'Y') == "-80 <= X AND -79.5 >= X AND 45 <= Y AND 45.5 >= Y"
    
    
def test_period(self):
    assert Period.check_period(None) is None
    assert Period.check_period(['2020-10-11', None]) is None
    assert Period.check_period([None, '2020-10-11']) is None
    
    # invalide periods
    assert Period.check_period(['2010-10-11', '2009-11-11']) == ValueError
    assert Period.check_period("2022-10-11") == ValueError
    assert Period.check_period(["2022-10-11"]) == ValueError


def test_sql_queries(self):