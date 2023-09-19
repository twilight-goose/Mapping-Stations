# Mapping-Stations

This repository exists

## Environment Creation & Setup
The setup steps listed below present one way to set up the environment that will enable you to run this code.
The goal of these steps is to set up a conda channel that has python and geopandas installed, which is needed
to run the scripts.

## Steps
1. Create a new conda environment
2. Using conda, install geopandas (a compatible version of pandas will install with geopandas)
3. Check your pyproj version, and update it to pyproj 3.5.0 if necessary
4. Change the file paths in "Loader.py" to match the location of your data