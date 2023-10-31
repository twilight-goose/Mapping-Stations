# Mapping-Stations

This repository exists

## Python Environment
It is recommended to conda to set up a Python environment, but any method of creating a python 3.9.18 environment
should function as normal. Python 3.9.18 is recommended, as the code was written and tested in 3.9.18. Later
versions with adequate compatibility with project packages may work, but use them at your own risk.

### Conda setup and installation
From [the anaconda website](https://www.anaconda.com/) download the Anaconda installer compatible with your system.
This comes with Anaconda Prompt, which is where you will access conda. If you have worked with conda before,
and already have access to conda through another platform (such as miniconda), these setup steps may work there
as well, but full functionality is not guaranteed.

```bash
conda create -n env-conda-3.9.18 python=3.9.18
conda activate env-conda-3.9.18

conda install -n env-conda-3.9.18 -c conda-forge pandas
conda install -n env-conda-3.9.18 -c conda-forge geopandas
conda install -n env-conda-3.9.18 -c conda-forge matplotlib
conda install -n env-conda-3.9.18 -c conda-forge cartopy
conda install -n env-conda-3.9.18 -c conda-forge momepy
conda install -n env-conda-3.9.18 -c conda-forge networkx
conda install -n env-conda-3.9.18 -c conda-forge matplotlib-scalebar
```

A number of other dependencies will come with geopandas. You can check the version of each of these dependencies
by opening a python terminal, importing geopandas, and calling geopandas.show_versions()
```bash
python

import geopandas
geopandas.show_versions()
```
Once here, do
```bash
import geopandas
geopandas.show_versions()
```
If geopandas and python have been correctly installed, you will see something akin to:

```
SYSTEM INFO
-----------
python     : 3.9.18 | packaged by conda-forge | (main, Aug 30 2023, 03:40:31) [MSC v.1929 64 bit (AMD64)]
executable : <location of python executable>
machine    : <Machine>

GEOS, GDAL, PROJ INFO
---------------------
GEOS       : 3.11.2
GEOS lib   : None
GDAL       : 3.7.0
GDAL data dir: None
PROJ       : 9.2.0i
PROJ data dir: <proj data directory>

PYTHON DEPENDENCIES
-------------------
geopandas  : 0.14.0
numpy      : 1.26.0
pandas     : 2.1.0
pyproj     : 3.5.0
shapely    : 2.0.1
fiona      : 1.9.4
geoalchemy2: None
geopy      : 2.4.0
matplotlib : 3.8.0
mapclassify: 2.5.0
pygeos     : None
pyogrio    : None
psycopg2   : None
pyarrow    : None
rtree      : 1.0.1
```
Versions of geopandas after 0.14.0 should install up-to-date releases of PROG and PYPROJ, but if you have a PROJ version less than 9.2.0 and/or a pyproj version less than 3.5.0, they need to be updated.

### 3b: Updating proj and pyproj
To update proj and pyproj, run the following commands in Anaconda Prompt. Pyproj version 3.5.0 works with
releases of PROJ that implemented a crucial bugfix (reported [here](https://github.com/geopandas/geopandas/issues/2874)).

```
conda update -n env-conda-3.9.18 -c conda-forge pyproj
```

Once you have pyproj version 3.5.0 installed, you should have all required dependencies.
Next, you need to configure project structure and data paths.

### 4. Configuring Project Structure and Data Paths
```
<project_folder>
    | data
        | Hydro_RIVERS_v10
            |--HydroRIVERS_v10_na.dbf
            |--HydroRIVERS_v10_na.prj
            |--HydroRIVERS_v10_na.sbn
            |--HydroRIVERS_v10_na.sbx
            |--HydroRIVERS_v10_na.shp
            |--HydroRIVERS_v10_na.shx
        | Hydat
            |--hydat.sqlite3
        | MondayFileGallery
            |--<file 1>.csv
            ...
            |--<file n>.csv
        | PWQMN_cleaned
            |--Provincial_Water_Quality_Monitoring_Network_PWQMN_cleaned.csv
    | src
    | plots
    | maps
```
Data loading functions within these python files assumes the above project structure. To load
data/files from directories or files with different names, data file paths can be modified near the
top of "/src/load_data.py". Anything beyond changing file and folder names is **not recommended**.

Functions in "src/load_data.py" were designed to accommodate specific versions of the Hydat and PWQMN
datasets. Specifically, HYDAT dataset tables are expected to have a field exactly named "STATION_NUMBER".
The HYDAT dataset is also expected to contain the following table names:

- STATIONS
- DLY_FLOWS
    
STATIONS must contain the following fields:

- STATION_NUMBER
- STATION_NAME
- LONGITUDE
- LATITUDE
- DRAINAGE_AREA_GROSS
- DRAINAGE_AREA_EFFECT
    
DLY_FLOWS must contain **STATION_NUMBER** and one of the following sets of fields (or
another field name compatible with Period.sql_query()):

- YEAR and MONTH
- YEAR_FROM and YEAR_TO
- DATE

The PWQMN dataset is expected to contain the following fields, and a missing one will result in ValueErrors.
```
'MonitoringLocationName',
'MonitoringLocationID',
'MonitoringLocationLongitude',
'MonitoringLocationLatitude',
'ActivityStartDate',
'CharacteristicName',
'SampleCollectionEquipmentName',
'ResultSampleFraction',
'ResultValue',
'ResultUnit',
'ResultValueType',
'ResultDetectionCondition',
'ResultDetectionQuantitationLimitMeasure',
'ResultDetectionQuantitationLimitUnit'
```

The HYDAT and PWQMN data used in this project were pre-processed by [Juliane Mai](https://github.com/julemai).
The pre-processed data may be obtainable from the following links (you will need to have pop-ups either enabled or set to ask)

Hydat Data: http://juliane-mai.com/resources/data_nandita/Hydat.sqlite3.zip \
PWQMN Data: http://juliane-mai.com/resources/data_nandita/Provincial_Water_Quality_Monitoring_Network_PWQMN_cleaned.csv.zip \
Monday Files: https://github.com/twilight-goose/Mapping-Stations/tree/main/data/MondayFileGallery

Raw data is available from these links:

Hydat Data: http://collaboration.cmc.ec.gc.ca/cmc/hydrometrics/www/
HydroRIVERS: https://www.hydrosheds.org/products/hydrorivers
PWQMN Data: https://greatlakesdatastream.ca/explore/#/dataset/f3877597-9114-4ace-ad6f-e8a68435c0ba/

### Provincial (Stream) Water Quality Monitoring Network (PWQMN) data
The following are Juliane's steps for pre-processing the PWQMN data (2023-09-10).

The data need to be manually downloaded through:
https://greatlakesdatastream.ca/explore/#/dataset/f3877597-9114-4ace-ad6f-e8a68435c0ba/
Then click the download button appearing on that website.

Name: `Provincial_Water_Quality_Monitoring_Network_PWQMN.csv` (data)
Name: `Provincial_Water_Quality_Monitoring_Network_PWQMN_metadata.csv`

(metadata)
The datafile is a comma-separated file but several entries contain
commas themselves. The entry is then in double-quotes, e.g.,
123,"ABC, DEV 23",345,534.202,"abd,dged,sdg",2,4
The handling of this in the code takes ages. Hence, we clean the data
from those double-quotes and commas and replace them by semi-colons,
e.g.,
123,ABC;DEV;23,345,534.202,abd;dged;sdg,2,4
using:
awk -F'"' -v OFS='' '{ for (i=2; i<=NF; i+=2) gsub(",", ";", $i) } 1' Provincial_Water_Quality_Monitoring_Network_PWQMN.csv > Provincial_Water_Quality_Monitoring_Network_PWQMN_cleaned.csv

## Module Overview
The load_data.py module, as its name implies, is used for the loading of data. This is where
file path constants can be found and modified.

The gen_utils.py module contains code and constants used throughout the other modules, such
as 'geodetic', 'lambert', and 'Can_LCC_wkt' which define coordinate systems, so they may
be consistent between scripts. It also contains classes that define and provide structure
to certain concepts used throught the project.

The gdf_utils.py module contains code used to manipulate data. Functions do not change
the original passed data, and instead returns copies with the manipulations performed.

The plot_utils.py module contains code used to add elements to matplotlib plots, such
as maps, grids, data, and custom legends, and do not change data passed to it in any
way. Outputs from this functions within this script generally only hold relevance for plotting.

The browser.py module contains complex code that creates interactive matplotlib windows.
Code within browser.py is not useful for performing any operations outside of the script,
and it's relevance is limited to its exact use case - creating and opening data browsers.

## Output Accuracy Table
### Zone 1: Southern/Central Ontario
All distances are in meters. For stations on the same segment within 350m, regardless
of the dataset that the network was built with, distance is calculated from origin
to candidate station point instead of along the network. The algorithm is also designed
to report ALL candidate stations within a maximum distance that lie on the same river
segment as the origin station. This means that where the greater resolution of the OHN
dataset breaks stretches of river that are recorded as single edges in HydroRIVERS into
multiple segments some stations will no longer lie on the same segment.

It is noted that the network built from the OHN watercourses dataset follows real-world
rivers most accurately, containing lines placed near or at the weighted center of rivers
at a very high resolution. More information and download can be found [here](https://geohub.lio.gov.on.ca/datasets/a222f2996e7c454f9e8d028aa05995d3_26/about). The 
shapefile used for the comparison was created on May 2, 2022.

Matches with NA instead of a distance indicate 1 of the following:
- they are far enough that they would not reasonably be matched with said station for any reason
- there are other significantly close water quality stations that would be matched to it
- the complexity/sinuosity of the river segment(s) is too great for manual measuring to have any accuracy benefit over the OHN dist
- In HydroRIVERS dist, stations with an NA value did not have a river segment close enough to snap to
- In % Error, algorithm calculated direct distance between stations for both networks (see above)

@submission 0895cd7 {Extent (lat/lon): min_x=-80, max_x=-79, min_y=45, max_y=46}
   hydat_id    pwqmn_id  dist_hyRivers pos_hyRivers     dist_OHN  pos_OHN     error  manual
0   02DD009  3013302302      43.451882      On-Down    43.451882  On-Down  0.000000    43.1
1   02EA005  3012400102    6232.601156         Down  7894.037701     Down  0.210467      NA
2   02EA006  3012400202    1073.440993      On-Down  1700.666633     Down  0.368812   ~1656
3   02EA006  3012400102    2792.096362         Down          NaN      NaN       NaN      NA
4   02EA001  3009800302    3785.120896      On-Down  3910.138179     Down  0.031973   ~3670
5   02EA001  3009800402    4467.751704      On-Down          NaN      NaN       NaN   ~4590
6   02EB013  3008503202    5124.624633         Down          NaN      NaN       NaN      NA
7   02EB103  3008502802      18.925278        On-Up    18.925278  On-Down  0.000000    18.6
8   02EB004  3008500602      30.923688        On-Up    30.923688    On-Up  0.000000    30.5
9   02EB007  3008500602    3372.482868           Up  3776.371041       Up  0.106951      NA
10  02EB008  3008500902     296.543161        On-Up   310.248873    On-Up  0.044177     302
11  02EB105  3008502502      31.614124      On-Down    31.614124    On-Up  0.000000    31.1
12  02EB011  3009200102     336.848454        On-Up   333.795511       Up  0.009146   331.3 
13  02EB005  3009200202    3223.123205        On-Up  3600.401277       Up  0.104788   ~3300
14  02EB005  3008501601    7682.088931           Up          NaN      NaN       NaN   ~8630
15  02EB006  3009200202    3507.274414        On-Up  4286.953203       Up  0.181872   ~3675
16  02EB006  3008501601    7966.240139           Up          NaN      NaN       NaN      NA
17  02EB010  3008500102    8982.163362      On-Down  9848.652301     Down  0.087980   ~8800
18  02EB010  3009200202    5068.978402        On-Up          NaN      NaN       NaN   ~5315
19  02EB010  3008501601    9527.944128           Up          NaN      NaN       NaN      NA
20  02EB012  3008500102      64.850527      On-Down    64.850527  On-Down  0.000000    63.5
21  02EB009  3009200102            NaN          NaN  8863.486486     Down       NaN      NA
22  02EB009  3009200202            NaN          NaN  6024.150516       Up       NaN      NA

On-Up = On the same river segment, upstream
On-Down = On the same river segment, downstream
Up = Upstream
Down = Downstream
% Error is % error in hydroRIVERS, calculated as (hydroRIVERS - OHN_dist) / OHN_dist * 100

Table produced using test_cases.network_compare()
