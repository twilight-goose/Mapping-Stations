ex1.py: FAST :: basic plotting
ex2.py: FAST :: displays how stations are 'snapped' to river networks (you will need to zoom in to see the conencting lines)
ex3.py: DONT RUN :: Loading stations from shapefiles (don't run, points1.shp and points2.shp don't exist.)
ex4.py: FAST :: match browser. Load all stations within a specificed lat/lon bounding box and create an nteractive plot allowing the user to click on stations and see a list of matches.
ex5.py: FAST :: same as ex4, except uses the OHN dataset for rivers.
ex6.py: FAST :: match array
ex7.py: FAST :: save to shapefile (no output)
ex8.py: REALLY SLOW :: compare station matching between OHN and hydrorivers datasets, calculate the error between the two, and save it to "table.csv"
ex9.py: FAST :: loading lists of stations from .csv files and saving the station data to .csv files
ex10.py: REALLY SLOW :: example of loading large lists of stations from .csv files and matching them.

	        Some things to potentially change in main.py of PySheds
			(in Kasope's GitHub)

            line 40: FLDIR = os.path.join(os.path.dirname(__file__), "data", "Rasters", "hyd_na_dir_15s.tif")
            line 41: FLACC = os.path.join(os.path.dirname(__file__), "data", "Rasters", "hyd_na_acc_15s.tif")

	        line 144: lons = basins['lon'].tolist()

ex11.py: FAST :: Load and match hydat stations in "MondayFileGallery/Q_C_pairs.csv", then compare the matches made.
ex12.py: Load and match pwqmn stations in "MondayFileGallery/Q_C_pairs.csv", then compare the matches made.
