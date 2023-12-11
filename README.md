# Mapping-Stations

This repository exists

# Instllation: Windows

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

conda install -n env-conda-3.9.18 -c conda-forge pandas=2.1.1
conda install -n env-conda-3.9.18 -c conda-forge geopandas=0.14.0
conda install -n env-conda-3.9.18 -c conda-forge matplotlib=3.8.0
conda install -n env-conda-3.9.18 -c conda-forge cartopy=0.22.0
conda install -n env-conda-3.9.18 -c conda-forge momepy=0.6.0
conda install -n env-conda-3.9.18 -c conda-forge networkx=3.1
conda install -n env-conda-3.9.18 -c conda-forge matplotlib-scalebar=0.8.1
conda install -n env-conda-3.9.18 -c conda-forge adjusttext=0.7.3.1
conda install -n env-conda-3.9.18 -c conda-forge pytest
conda install -n env-conda-3.9.18 -c conda-forge pysheds=0.3.5
conda install -n env-conda-3.9.18 -c conda-forge area
```

# Installation: GRAHAM

```
git clone https://github.com/twilight-goose/Mapping-Stations.git
cd Mapping-Stations/
​
module purge
module load StdEnv/2020 netcdf/4.7.4 gcc/9.3.0 gdal/3.5.1
module load mpi4py/3.1.3 proj/9.0.1
module load geos/3.10.2
module load nco/5.0.6
module load python/3.10.2
​
mkdir env-3.10
virtualenv --no-download env-3.10
source env-3.10/bin/activate
​
pip install --no-index --upgrade pip
​
pip install netCDF4 --no-index # no need, it is for raven-hydro
pip install GDAL --no-index
pip install numpy --no-index
pip install argparse --no-index
pip install geopandas --no-index
​
pip install pandas --no-index
pip install matplotlib --no-index
pip install cartopy --no-index
pip install momepy --no-index
pip install networkx --no-index
pip install matplotlib-scalebar --no-index
pip install adjusttext --no-index
pip install pytest --no-index
pip install pysheds --no-index
pip install area
​
​
scp -r Hydat/Hydat.sqlite3 julemai@gra-platform.computecanada.ca:/home/julemai/projects/rpp-julemai/julemai/Mapping-Stations/data/Hydat/.
scp -r datastream/Total_Phosphorus_mixed_forms_obs.json julemai@gra-platform.computecanada.ca:/home/julemai/projects/rpp-julemai/julemai/Mapping-Stations/data/datastream/.
scp -r Hydro_RIVERS_v10 julemai@gra-platform.computecanada.ca:/home/julemai/projects/rpp-julemai/julemai/Mapping-Stations/data/.
scp -r OHN julemai@gra-platform.computecanada.ca:/home/julemai/projects/rpp-julemai/julemai/Mapping-Stations/data/.
scp -r PWQMN_cleaned julemai@gra-platform.computecanada.ca:/home/julemai/projects/rpp-julemai/julemai/Mapping-Stations/data/.
​
mkdir data/shapefiles
```
The best way to check that everything is installed correctly is by running the examples in "Mapping-Stations/examples" (excluding 3 and 8)
Next, you need to configure project structure and data paths.

### 4. Configuring Project Structure and Data Paths
In addition to Mapping-Stations, you will need [Watershed Delineation](https://github.com/kokubadejo/Watershed_Delineation)
created by [Kasope Okubadejo](https://github.com/kokubadejo). Follow the data installation instructions found in
the README.md file and ignore the environment setup instructions as everything needed for both projects can be found above.
Omitting many of the files included in the repositories, the downloaded data and watershed
delineation repository should be structured and named as follows if you do not intend to change
file paths within scripts.
```
| Mapping-Stations
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
			| --Q_C_pairs.csv (for ex11 and ex12)
		| OHN (needed to run ex5 & ex8)
			| --Ontario_Hydro_Network_(OHN)_-_Watercourse.dbf
			| --Ontario_Hydro_Network_(OHN)_-_Watercourse.prj
			| --Ontario_Hydro_Network_(OHN)_-_Watercourse.sbn
			| --Ontario_Hydro_Network_(OHN)_-_Watercourse.sbx
			| --Ontario_Hydro_Network_(OHN)_-_Watercourse.shp
			| --Ontario_Hydro_Network_(OHN)_-_Watercourse.shx
		| PWQMN_cleaned
			|--Provincial_Water_Quality_Monitoring_Network_PWQMN_cleaned.csv
		| datastream
		| shapefiles
	| errors
	| examples
		| ex1.py - ex12.py
		| --example_index.md	[contains information about the examples]
	| plots
	| src
		| --gen_util.py
		| --gdf_utils.py
		| --plot_utils.py
		| --load_data.py
		| --browser.py
		| --check_files.py

| Watershed_Delineation (https://github.com/twilight-goose/Watershed_Delineation/tree/patch-1)
	| src
		| PySheds
			| --main.py
			| data
				| Rasters
					| --hyd_na_dir_15s.tif
					| --hyd_na_acc_15s.tif
		| RabPro
```

The HYDAT and PWQMN data used in this project were pre-processed by [Juliane Mai](https://github.com/julemai).
The pre-processed data may be obtainable from the following links (you will need to have pop-ups either enabled or set to ask).

Hydat Data: http://juliane-mai.com/resources/data_nandita/Hydat.sqlite3.zip \
PWQMN Data: http://juliane-mai.com/resources/data_nandita/Provincial_Water_Quality_Monitoring_Network_PWQMN_cleaned.csv.zip \
Monday Files: https://github.com/twilight-goose/Mapping-Stations/tree/main/data/MondayFileGallery

Raw data is available from these links:

Hydat Data: http://collaboration.cmc.ec.gc.ca/cmc/hydrometrics/www/ \
HydroRIVERS: https://www.hydrosheds.org/products/hydrorivers \
- download the North and Central America shapefile
PWQMN Data: https://greatlakesdatastream.ca/explore/#/dataset/f3877597-9114-4ace-ad6f-e8a68435c0ba/
OHN Data: https://geohub.lio.gov.on.ca/datasets/a222f2996e7c454f9e8d028aa05995d3/explore
- Go to the shapefile
- click download options
- download previously generated version (unless you have a lot of time)

### Provincial (Stream) Water Quality Monitoring Network (PWQMN) data
The following are Juliane's steps for pre-processing the PWQMN data (2023-09-10).

The data need to be manually downloaded through:
https://greatlakesdatastream.ca/explore/#/dataset/f3877597-9114-4ace-ad6f-e8a68435c0ba/ \
Then click the download button appearing on that website.

Name: `Provincial_Water_Quality_Monitoring_Network_PWQMN.csv` (data) \
Name: `Provincial_Water_Quality_Monitoring_Network_PWQMN_metadata.csv` (metadata)

The datafile is a comma-separated file but several entries contain
commas themselves. The entry is then in double-quotes, e.g.,
123,"ABC, DEV 23",345,534.202,"abd,dged,sdg",2,4
The handling of this in the code takes ages. Hence, we clean the data
from those double-quotes and commas and replace them by semi-colons,
e.g.,
123,ABC;DEV;23,345,534.202,abd;dged;sdg,2,4
using:
awk -F'"' -v OFS='' '{ for (i=2; i<=NF; i+=2) gsub(",", ";", $i) } 1' Provincial_Water_Quality_Monitoring_Network_PWQMN.csv > Provincial_Water_Quality_Monitoring_Network_PWQMN_cleaned.csv


Data loading functions within these python files assumes the above project structure. To load
data/files from directories or files with different names, data file paths can be modified near the
top of "/src/load_data.py". Anything beyond changing file and folder names is **not recommended**.

Functions in "src/load_data.py" were designed to accommodate specific versions of the Hydat and PWQMN
datasets. Specifically, HYDAT dataset tables are expected to have a field exactly named "STATION_NUMBER".
The HYDAT sqlite3 dataset is also expected to contain the following tables:

- STATIONS
- DLY_FLOWS
    
STATIONS must contain the following fields:

- STATION_NUMBER
- STATION_NAME
- LONGITUDE
- LATITUDE
    
DLY_FLOWS must contain **STATION_NUMBER** and one of the following sets of fields (or
another field name compatible with Period.sql_query()):

- YEAR and MONTH
- YEAR_FROM and YEAR_TO
- DATE

The PWQMN dataset is expected to contain the following fields, and a missing one will result in KeyErrors.
If certain fields are not present, they can be removed from the dictionaries in load_data.generate_pwqmn_sql()
to bypass the KeyErrors.
```
'MonitoringLocationName',
'MonitoringLocationID',
'MonitoringLocationLongitude',
'MonitoringLocationLatitude',
'MethodSpeciation',
'ActivityStartDate',
'CharacteristicName',
'SampleCollectionEquipmentName',
'ResultSampleFraction',
'ResultValue',
'ResultUnit',
'ResultValueType',
'ResultDetectionCondition',
'ResultDetectionQuantitationLimitType',
'ResultDetectionQuantitationLimitMeasure',
'ResultDetectionQuantitationLimitUnit'
'ResultComment',
'ResultAnalyticalMethodID',
'ResultAnalyticalMethodContext',
'LaboratorySampleID'
```

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


## Use Cases and Usage Examples
Refer to `../examples/` for exampls; Explanations below. See files for expected terminal output/messages.

* note: The first time running any process will likely take an extended period as the program builds/generates tables 
```
ex1.py: FAST :: basic plotting

ex2.py: FAST :: displays how stations are 'snapped' to river networks (you will need to zoom
				in to see the conencting lines).
				
ex3.py: DONT RUN :: Loading stations from shapefiles (don't run, points1.shp and points2.shp don't exist.)

ex4.py: FAST :: match browser. Load all stations within a specificed lat/lon bounding box,
				load and assign data range overlaps, and create an interactive plot allowing
				the user to click on stations and see a list of matches.
				
ex5.py: FAST :: same as ex4, except uses the OHN dataset for rivers.

ex6.py: FAST :: match array

ex7.py: FAST :: save to shapefile
				- creates "data/shapefiles/hydat.shp" and "data/shapefiles/pwqmn.shp"
				
ex8.py: REALLY SLOW :: compare station matching between OHN and hydrorivers datasets, calculate the
						error between the two, and save it to "table.csv"
				- creates "examples/table.csv"
				
				GRAHAM: requireds too much memeory for login node
						
ex9.py: FAST :: loading lists of stations from .csv files and saving the station data to .csv files
				- loads from "examples\ex9_hydat_subset.csv"
				- loads from "examples\ex9_pwqmn_subset.csv"
				- creates "examples\p_subset_station_data.csv"
				- creates "data\Hydat\h_subset_station_data.csv"

ex10.py: SLOW :: example of loading large lists of stations from .csv files and matching them, then delineating the watersheds of a sample of matches and comparing them.
				- requires the "Watershed_Delineation" repository
				
ex11.py: FAST :: Load and match hydat stations in "MondayFileGallery/Q_C_pairs.csv", then compare the matches made.
				- loads from "data\MondayFileGallery\Q_C_pairs.csv"
				- creates "examples\q_c_pair_comparison.csv"
				
ex12.py: FAST :: Load and match pwqmn stations in "MondayFileGallery/Q_C_pairs.csv", then compare the matches made.
				- loads from "data\MondayFileGallery\Q_C_pairs.csv"
				- creates "examples\q_c_pair_comparison2.csv"
```

## Matching and Distance Criteria
Steps for matching stations:
1. Load both origin and candidate stations
2. Load the river dataset
3. Assign stations to the river dataset
- Each station within a certain distance of a river segment will be 'assigned' to
the closest river segment
- Stations assigned to a river segment have their attributes stored in containers,
which are written to attributes of the river segment and are carried over when the
dataset is converted to a networkX directed graph.
4. Convert the river dataset to a network graph. This enables the search algorithm
to be run and builds directionality.
5. Run the matching algorithm (dfs_search)

For a more detailed breakdown of matching and distance, see mapping-stations.pptx

Note: The first time loading PWMQN data (and any instance after deleting the database)
will take longer than usual, as it is generating the pwqmn sqlite3 database.

## Output Accuracy Table
### Zone 1: Southern/Central Ontario
All distances are in meters. The algorithm is also designed
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
```
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
```

On-Up = On the same river segment, upstream
On-Down = On the same river segment, downstream
Up = Upstream
Down = Downstream
% Error is % error in hydroRIVERS, calculated as (hydroRIVERS - OHN_dist) / OHN_dist * 100

Table produced using test_cases.network_compare()

### Compared to Manual Matching
As of submission @8c9d254, the algorithm is able to match all stations manually matched in q_c_pairs.csv.
See ex11.py and ex12.py to run the code necessary for the comparison.
