import os.path


# Data source URLs
monday_url = "https://github.com/twilight-goose/Mapping-Stations/tree/main/data/MondayFileGallery"
hydat_url = "http://juliane-mai.com/resources/data_nandita/Hydat.sqlite3.zip"
pwqmn_url = ("http://juliane-mai.com/resources/data_nandita/"
             "Provincial_Water_Quality_Monitoring_Network_PWQMN_cleaned.csv.zip")
hydroRIVERS_url = "https://data.hydrosheds.org/file/HydroRIVERS/HydroRIVERS_v10_na_shp.zip"



def check_path(path: str, name="Unnamed", url="<data source not found>", ):
    """
    Checks if the data path exists. If it doesn't exist and a url is
    passed, will suggest where to download/obtain the data

    :param path: The file path to check
    :param name: The name of the dataset that was checked
    :param url: URL to obtain the data from

    :raises FileNotFoundError:
    """
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"{name} data not found in expected location. Data available for "
            f"download from {url}; link can also be found in repository "
            f"README. Expected location: {path}")


def check_paths(proj_path: str, data_path: str, hydat_path: str,
                pwqmn_path: str, monday_path: str, hydroRIVERS_path: str):
    """
        Checks if the passed paths exist, and provides data download
        links for missing data. Assumes that 5 paths are passed in a
        specific order and the project has a specific file structure.

        Path order: proj_path, data_path, hydat_path, pwqmn_path, monday_path

        File Structure (file and folder names are examples and the defaults):
            proj_path
                | data_path
                    | Hydate
                        | --Hydate.sqlite3
                    |Hydro_RIVERS_v10
                        | --HydroRIVERS_v10.na.shp
                        | + (5 shapefile dependency files)
                    | PWQMN_cleaned
                        | --Provincial_Water_Quality_Monitoring_Network_PWQMN_cleaned.csv
                    | MondayFileGallery
                        | --q_c_pairs.csv

        :param proj_path: string
            Full project directory path.

        :param data_path: string
            Full path of project data directory.

        :param hydat_path: string
            Full path to HYDAT data.

        :param pwqmn_path: string
            Full path to Provincial Water Quality Monitoring Network data.

        :param monday_path: string
            Full path to data downloaded from Monday.com

        :param hydroRIVERS_path: string
            Full path to the HydroRIVERS data.

        :raises FileNotFoundError:
            If any of the 5 passed paths are not found, raises a
            FileNotFoundError and suggests a potential solution.
    """

    if os.path.exists(proj_path) and os.path.exists(data_path):
        check_path(hydat_path, 'Hydat', hydat_url)
        check_path(pwqmn_path, 'PWQMN', pwqmn_url)
        check_path(monday_path, 'Monday', monday_url)
        check_path(hydroRIVERS_path, 'HydroRivers', hydroRIVERS_path)
    else:
        raise FileNotFoundError(f"{data_path} could not be found. Check "
                                f"project file structure.")
