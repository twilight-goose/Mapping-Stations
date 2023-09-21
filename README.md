# Mapping-Stations

This repository exists

## Environment Creation & Setup
The setup steps listed below present one way to set up the environment that will enable you to run this code.
The goal of these steps is to set up a conda channel that has python and geopandas installed, which is needed
to run the scripts.

## Steps
1. Install conda
2. Create a new conda environment
3. Install other dependencies
5. Change the file paths in "/src/load_data.py" to match the location of your data if necessary

### 1. Install Conda
From [the anaconda website](https://www.anaconda.com/) download the Anaconda installer compatible with your system.
This comes with Anaconda Prompt, which is where you will access conda. If you have worked with conda before,
and already have access to conda through another platform (such as miniconda), these setup steps may work there
as well, but full functionality is not guaranteed.

### 2. Create a new conda environment
Conda provides environment creation functionality built in. Open Anaconda Prompt and create a new environment using conda.
"fall2023" can be replaced with any name of your choosing consisting of ONLY LETTERS, NUMBERS, AND UNDERSCORES.

```bash
conda create -n fall2023 python=3.9.18
```

### 3. Install Dependencies
The 2 dependences that need to be installed manually are geopandas (0.14.0) and contextily (1.3.0)

```bash
conda install -n fall2023 geopandas=0.14.0
conda install -n fall2023 contextily
```

A number of other dependencies will come with geopandas. You can check the version of each of these dependencies
by activating your environment and opening a python terminal.
```bash
conda activate fall2023
python
```
This will start python, and you should see the following:
```bash
Python 3.9.18 | packaged by conda-forge | (main, Aug 30 2023, 03:40:31) [MSC v.1929 64 bit (AMD64)] on win32
Type "help", "copyright", "credits" or "license" for more information.
>>>
```
Once here, use
```bash
import geopandas
geopandas.show_versions()
```
If geopandas and python have been correctly installed, you will see something akin to:

```commandline
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
PROJ       : 9.2.0
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
Geopandas version 0.14.0 should install up-to-date releases of PROG and PYPROJ, but if you have a PROJ version less than 9.2.0 and/or a pyproj version less than 3.5.0, they need to be updated

### 3b: Updating proj and pyproj
To update proj and pyproj, run the following commands in Anaconda Prompt. Pyproj version 3.5.0 works with
a release of PROJ that implemented a crucial bugfix (reported [here](https://github.com/geopandas/geopandas/issues/2874)).

```commandline
conda uninstall -n fall2023 pyproj
conda install -n fall2023 pyproj=3.5.0
```

Once you have pyproj version 3.5.0 installed, you should have all required dependencies.
Next, you need to configure project structure and data paths.

### 4. Configuring Project Structure and Data Paths
```commandline
<project_folder>
    | data
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

## Testing Code


##
