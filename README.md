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
datasets. Specifically, Hydat dataset tables are expected to have a field exactly named "STATION_NUMBER".
The HYDAT dataset is also expected to contain the following table names:

- STATIONS

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
The pre-processed data may be obtainable from the following links:

Hydat Data: http://juliane-mai.com/resources/data_nandita/Hydat.sqlite3.zip \
PWQMN Data: http://juliane-mai.com/resources/data_nandita/Provincial_Water_Quality_Monitoring_Network_PWQMN_cleaned.csv.zip \
Monday Files: https://github.com/twilight-goose/Mapping-Stations/tree/main/data/MondayFileGallery \

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


## Testing Code
```commandline

```
## Output Accuracy Table
### Zone 1: Southern/Central Ontario
@submission 49303b0
   hydat_id    pwqmz`n_id  alg dist (m)   pos   manual
0   02EA001  3009800302   3247.810984    On  ~3670 m
1   02EA001  3009800402   3838.929621    On  ~4590 m
14  02EB005  3008501601   7682.088931    Up  ~8630 m
13  02EB005  3009200202   3343.306653    On  ~3300 m
12  02EB005  3008500102   8299.933080    On ~11200 m
17  02EB006  3008501601   7966.240139    Up       NA
16  02EB006  3009200202   3676.271811    On  ~3675 m
15  02EB006  3008500102   7937.783292    On  ~9580 m
19  02EB010  3009200202   4568.338660    On  ~5315 m
18  02EB010  3008500102   7129.984936    On  ~8800 m
20  02EB010  3008501601   9527.944128    Up       NA
8   02EB011  3009200102    336.848454    On  331.3 m
21  02EB012  3008500102     64.850527    On`` 63.5 m`
9   02EB015  3008501802   4561.711575    On  ~6700 m
11  02EB015  3009200202   1926.939631  Down  ~1780 m
10  02EB015  3008501601   2279.480735    On  ~3780 m
7   02EB020  3008502301   4348.473836    Up  ~4500 m
6   02EB020  3008501102   1021.073825    On  ~1650 m
5   02EB020  3008501002     17.148932    On   16.9 m
4   02EB020  3008500202     62.877379    On   62.0 m
2   02EB103  3008502802     18.925278    On   18.6 m
3   02EB105  3008502502     31.614124    On   31.1 m

Matches with NA instead of a manual distance indicate they are far enough that
they would not reasonably be matched with said station for any reason, and/or
there are significantly closer water quality stations that would be matched to
it. (i.e. 02EB103 & 3008501002)