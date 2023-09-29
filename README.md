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
Original Hydat Data: http://collaboration.cmc.ec.gc.ca/cmc/hydrometrics/www/ \
PWQMN Data: http://juliane-mai.com/resources/data_nandita/Provincial_Water_Quality_Monitoring_Network_PWQMN_cleaned.csv.zip \
Monday Files: https://github.com/twilight-goose/Mapping-Stations/tree/main/data/MondayFileGallery \
HydroRIVERS: https://www.hydrosheds.org/products/hydrorivers

### Provincial (Stream) Water Quality Monitoring Network (PWQMN) data
Here are Juliane's steps for pre-processing the PWQMN data (2023-09-10).

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
