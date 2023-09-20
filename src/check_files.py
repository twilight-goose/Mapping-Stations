import os.path


monday_url = "https://github.com/twilight-goose/Mapping-Stations/tree/main/data/MondayFileGallery"
hydat_url = "http://juliane-mai.com/resources/data_nandita/Hydat.sqlite3.zip"
pwqmn_url = "http://juliane-mai.com/resources/data_nandita/Provincial_Water_Quality_Monitoring_Network_PWQMN_cleaned.csv.zip"


def check_path(path: str, name="Unnamed", url="<data source not found>"):
    """
    Checks the

    :param path:
    :param name:
    :param url:

    :raises FileNotFoundError:
    """
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"{name} data not found in expected location. Data available for "
            f"download from {url}; link can also be found in repository "
            f"README. Expected location: {path}")


def check_paths(proj_path: str, data_path: str, hydat_path: str,
                pwqmn_path: str, monday_path: str):
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
                    | PWQMN_cleaned
                        | -- Provincial_Water_Quality_Monitoring_Network_PWQMN_cleaned.csv
                    | MondayFileGallery

        :param proj_path: Path to the project directory
        :param data_path: Path to the data directory within the project
                          directory
        :param hydat_path: Path to hydat data
        :param pwqmn_path: Path to Provincial Water Quality Monitoring Network
                           Data
        :param monday_path: Path to data downloaded from Monday.com

        :raises FileNotFoundError: If any of the 5 passed paths are not found,
                                   raises a FileNotFoundError and provides a
                                   potential solution.
    """

    if os.path.exists(proj_path) and os.path.exists(data_path):
        check_path(hydat_path, 'Hydat', hydat_url)
        check_path(pwqmn_path, 'PWQMN', pwqmn_url)
        check_path(monday_path, 'Monday', monday_url)
    else:
        raise FileNotFoundError(f"{data_path} could not be found. Check "
                                f"project file structure.")
