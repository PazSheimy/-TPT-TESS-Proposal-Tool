"""This file contains a set of functions to process and analyze data related 
to the TESS mission. The functions handle different input formats,
such as right ascension and declination (RA/Dec), object names, and TIC IDs,
and retrieve relevant information about the TESS sectors 
that intersect with the given coordinates and radius. 
Additionally, the file contains functions for processing and 
visualizing the data obtained from the TESS mission.

Dependencies:
- flask
- astroquery
- csv
- astropy
- concurrent.futures
"""

import csv
from astroquery.mast import Tesscut, Catalogs, Observations
from astropy.coordinates import SkyCoord
from .metadata import get_metadata
from .visualization import generate_magnitude_histogram, hr_diagram, distance_histogram, sector_graph
from flask import url_for
from astropy.coordinates.name_resolve import NameResolveError
from astropy import units as u
from io import TextIOWrapper
from io import StringIO
from concurrent.futures import ThreadPoolExecutor


def read_csv_rows(csv_file):
    """Reads rows from a CSV file and returns a list of rows.

    Args:
        csv_file (file-like object): A file-like object representing the CSV file.

    Returns:
        list: A list of rows from the CSV file.
    """
    reader = csv.reader(csv_file, delimiter=',')
    return [row for row in reader]

def process_row(row):
    """Processes a single row from the CSV file to extract TIC ID, object name, or coordinates.

    Args:
        row (list): A list representing a row in the CSV file.

    Returns:
        tuple: A tuple containing TIC ID (if available), object name (if available), and SkyCoord object.
    """
    # Initialize variables for TIC ID and object name
    tic_id = None
    object_name = None


    # If the row contains two elements (RA and Dec), create a SkyCoord object using these coordinates
    if len(row) == 2:
        ra, dec = row[:2]
        coord = SkyCoord(f"{ra} {dec}", unit="deg")

    # If the row contains only one element, it can be either a TIC ID or an object name
    elif len(row) == 1:
        id_or_name = row[0]

        # If the element is a number, treat it as a TIC ID and get the corresponding RA and Dec
        if id_or_name.isdigit():
            tic_id = int(id_or_name)
            ra, dec = get_ra_dec_from_tic_id(tic_id)
            coord = SkyCoord(f"{ra} {dec}", unit="deg")
        
        # Otherwise, treat it as an object name and get the corresponding coordinates
        else:
            object_name = id_or_name
            coord = SkyCoord.from_name(object_name)

    # If the row has an invalid format, raise an error        
    else:
        raise ValueError("Error: Invalid input format.")
    
    # Return the TIC ID (if available), object name (if available), and the SkyCoord object
    return tic_id, object_name, coord

def process_row_with_results(row, radius):
    """Processes a single row from the CSV file and returns the results for the given radius.

    Args:
        row (list): A list representing a row in the CSV file.
        radius (float): The radius for the query.

    Returns:
        list: A list containing RA, Dec, results, cycle, and obs_date, or None if no results found.
    """
    # This line calls the function process_row(row) to get three values: tic_id, object_name, and coord.
    tic_id, object_name, coord = process_row(row)

    # This line checks if tic_id is not None.
    if tic_id is not None:

        # If tic_id is not None, it calls query_sectors_with_tic_id(tic_id, radius) 
        # to get the sectors and cutouts associated with the given tic_id.
        sectors, cutouts = query_sectors_with_tic_id(tic_id, radius)

    # If tic_id is None, this line checks if object_name is not None.
    elif object_name is not None:

        # If object_name is not None, it calls query_sectors_with_object_name(object_name, radius) 
        # to get the sectors and cutouts associated with the given object_name.
        sectors, cutouts = query_sectors_with_object_name(object_name, radius)

        # If both tic_id and object_name are None, this line assumes that the input coordinate coord is given and calls query_sectors_with_coord(coord, radius) 
        # to get the sectors and cutouts associated with the given coord.
    else:
        sectors, cutouts = query_sectors_with_coord(coord, radius)
    
    # This line calls process_sectors(sectors, cutouts) 
    # to process the sectors and cutouts and obtain the results, cycle, and obs_date.
    results, cycle, obs_date = process_sectors(sectors, cutouts)

    # This line checks if results are obtained.
    if results:
        # If results are obtained, it returns a list containing the RA and Dec coordinates of the input coord, the results, cycle, and obs_date.
        return [coord.ra.deg, coord.dec.deg, results, cycle, obs_date]
    
    # If no results are obtained, it returns None.
    else:
        return None

def process_csv(csv_file, radius, max_workers=4):
    """Processes a CSV file and returns the target results for the given radius.

    Args:
        csv_file (file-like object): A file-like object representing the CSV file.
        radius (float): The radius for the query.
        max_workers (int, optional): The maximum number of worker threads for concurrent processing. Defaults to 4.

    Returns:
        list: A list of target results containing information about the TESS sectors.
    """


    # This function takes a file-like object csv_file and a radius value and returns a list of target results 
    # containing information about the TESS sectors.
    # The function uses ThreadPoolExecutor to concurrently process each row of the CSV file 
    # with the help of the function process_row_with_results(row, radius).

    # csv_file: A file-like object representing the CSV file to be processed.
    # radius: A float representing the radius of the search.
    # max_workers: An optional integer representing the maximum number of worker threads for concurrent
    # processing. Default value is 4.

    print("im in process csv 3")
    target_results = []

    # Read the rows from the CSV file.
    rows = read_csv_rows(csv_file)

    # Process the rows concurrently using ThreadPoolExecutor.
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(lambda row: process_row_with_results(row, radius), rows))

    # Extract the results from the processed rows and add them to the target_results list.
    for result in results:
        if result:
            coord_ra, coord_dec, sectors_info, cycle, obs_date = result
            for sector_info in sectors_info:
                target_results.append([coord_ra, coord_dec] + sector_info)

            
    print(target_results) # this is just to debug take it out when finish

    # Return the target_results
    return target_results

def process_data(search_input, radius, sector_number):
    """
    Process the data based on search_input, radius, and sector_number.

    This function retrieves the TESS sectors and other information for the given search_input (coordinates or object name)
    and radius. If a sector_number is provided, it filters the results based on the given sector_number.

    Args:
        search_input (str): The input string containing either coordinates (RA and Dec) or object name (e.g., a star name).
        radius (float): The radius in degrees to search around the given coordinates or object.
        sector_number (int, optional): The TESS sector number to filter the results. If None, no filtering is applied.

    Returns:
        dict: A dictionary containing the following keys:
            - "results": A list of filtered results based on the given sector_number (if provided).
            - "star_name": The name of the object (if available).
            - "sector_num": The sector number used for filtering (if provided).
            - "enumerate": The enumerate built-in function.
            - "table_visibility": A string ('visible') indicating the visibility of the results table.
    """
    all_results, ra, dec, object_name, tic_id, coord, sector_number, cycle, obs_date = sectors(
        search_input, radius, sector_number)

    # Filter the results based on the entered sector number
    if sector_number is not None:
        filtered_results = [result for result in all_results if result[0] == int(sector_number)]
    else:
        filtered_results = all_results

    # sets <table> visibility to 'visible' once query results are received
    table_visibility = 'visible'

    return {
        "results": filtered_results,
        "star_name": object_name,
        "sector_num": sector_number,
        "enumerate": enumerate,
        "table_visibility": table_visibility,
    }


def sectors(search_input, radius, sector_number=None):

    """
    Get the TESS sectors and other information for the given search_input and radius.

    This function takes the search_input (coordinates, object name, or TIC ID) and radius to get the TESS sectors,
    cutouts, and other information. It first resolves the input to get the coordinates, object name, or TIC ID,
    then queries the sectors and cutouts, and finally processes the sectors to get the results and additional information.

    Args:
        search_input (str): The input string containing either coordinates (RA and Dec), object name, or TIC ID.
        radius (float): The radius in degrees to search around the given coordinates or object.
        sector_number (int, optional): The TESS sector number to filter the results. If None, no filtering is applied.

    Returns:
        tuple: A tuple containing the following values:
            - results (list): A list of processed results for the given search_input and radius.
            - ra (float): The right ascension of the object.
            - dec (float): The declination of the object.
            - object_name (str): The name of the object (if available).
            - tic_id (int): The TIC ID of the object (if available).
            - coord (SkyCoord): The SkyCoord object representing the object's coordinates.
            - sector_number (int): The sector number used for filtering (if provided).
            - cycle (int): The TESS cycle number.
            - obs_date (str): The observation date.
    """
    
    # This function takes an input search string, radius, and an optional sector number,
    # and returns a tuple containing the processed results, coordinates, object name, 
    # TIC ID, and additional information about the TESS sectors.
    # It first resolves the input to obtain the coordinates, object name, or TIC ID, 
    # then queries the sectors and cutouts using the query_sectors function,
    # and finally processes the sectors to get the results and additional information.

    # search_input: A string containing either coordinates (RA and Dec), object name, or TIC ID.
    # radius: A float representing the radius in degrees to search around the given coordinates or object.
    # sector_number: An optional integer representing the TESS sector number to filter the results. If None,
    # no filtering is applied.

    coord, ra, dec, object_name, tic_id = resolve_input(search_input)

    if not coord and not object_name and not tic_id:
        # If the input string is not valid, return an error message.
        return "Error: Please enter a correct input (RA/Dec, object name, or TIC ID)."

    queried_sectors, cutouts = query_sectors(coord, object_name, tic_id, radius)

    # Process the queried sectors to get the results, cycle, and observation date.
    results, cycle, obs_date = process_sectors(queried_sectors, cutouts)
    
    # Return a tuple containing the processed results, coordinates, object name, TIC ID, 
    # and additional information about the TESS sectors.
    return results, ra, dec, object_name, tic_id, coord, sector_number, cycle, obs_date


def resolve_input(search_input):
    """
    Resolve the input string (search_input) to determine if it is a TIC ID, coordinates, or an object name.

    This function takes the search_input (coordinates, object name, or TIC ID) and tries to resolve it to a
    SkyCoord object, object name, or TIC ID, depending on the format of the input. It initializes the variables
    with None and updates them based on the input type.

    Args:
        search_input (str): The input string containing either coordinates (RA and Dec), object name, or TIC ID.

    Returns:
        tuple: A tuple containing the following values:
            - coord (SkyCoord or None): The SkyCoord object representing the object's coordinates, if found.
            - ra (float or None): The right ascension of the object, if found.
            - dec (float or None): The declination of the object, if found.
            - object_name (str or None): The name of the object, if found.
            - tic_id (int or None): The TIC ID of the object, if found.
    """

    # Initialize variables with None
    coord = None
    ra = None
    dec = None
    object_name = None
    tic_id = None

    # Check if the search_input is a digit
    if search_input.isdigit():
        # If the search_input is a digit, store it in tic_id
        tic_id = int(search_input)
        object_name = "TIC " + str(tic_id)
        # Query the TIC catalog for the object's coordinates
        tic_object = Catalogs.query_criteria(catalog="TIC", ID=tic_id)
        if len(tic_object) > 0:
            ra = float(tic_object['ra'][0])
            dec = float(tic_object['dec'][0])
            coord = SkyCoord(f"{ra} {dec}", unit="deg")
        else:
            coord = None
    else:
        # Try to convert the search_input into a SkyCoord object
        try:
            coord = SkyCoord(search_input, unit="deg")
            ra = coord.ra.degree
            dec = coord.dec.degree
        except:
            # If the conversion fails, check if the search_input contains a space
            if " " in search_input:
                try:
                    # If the search_input contains a space, split it into ra and dec
                    ra, dec = search_input.split(" ")
                    coord = SkyCoord(f"{ra} {dec}", unit="deg")
                except:
                    # If this conversion also fails, coord will still be None
                    pass

            # If coord is still None, store the search_input in object_name
            if not coord:
                object_name = search_input

    return coord, ra, dec, object_name, tic_id


def query_sectors_with_coord(coord, radius):
    """
    Query TESS sectors and cutouts using coordinates and a radius.

    Args:
        coord (SkyCoord): A SkyCoord object representing the coordinates (RA, Dec) of the target.
        radius (float): The search radius in degrees.

    Returns:
        tuple: A tuple containing the queried TESS sectors and cutouts.
    """
    
    sectors = Tesscut.get_sectors(coordinates=coord, radius=float(radius) * u.deg)
    cutouts = Tesscut.get_cutouts(coordinates=coord)
    return sectors, cutouts

def query_sectors_with_object_name(object_name, radius):
    """
    Query TESS sectors and cutouts using an object name and a radius.

    Args:
        object_name (str): The name of the celestial object to search.
        radius (float): The search radius in degrees.

    Returns:
        tuple: A tuple containing the queried TESS sectors and cutouts.

    Raises:
        ValueError: If the object name is invalid.
    """
    try:
        sectors = Tesscut.get_sectors(objectname=object_name, radius=float(radius) * u.deg)
        cutouts = Tesscut.get_cutouts(coordinates=object_name)
    except NameResolveError:
        raise ValueError("Error: Invalid object name.")
    return sectors, cutouts

def query_sectors_with_tic_id(tic_id, radius):

    """
    Query TESS sectors and cutouts using a TIC ID and a radius.

    Args:
        tic_id (int): The TESS Input Catalog ID of the target.
        radius (float): The search radius in degrees.

    Returns:
        tuple: A tuple containing the queried TESS sectors and cutouts.
    """

    tic_id = str(tic_id).strip()
    if not tic_id.startswith("TIC"):
        tic_id = "TIC " + tic_id

    sectors = Tesscut.get_sectors(coordinates=tic_id, radius=float(radius) * u.deg)
    cutouts = Tesscut.get_cutouts(coordinates=tic_id)
    return sectors, cutouts

def query_sectors(coord, object_name, tic_id, radius):

    """
    Query TESS sectors and cutouts based on the provided input (coord, object_name, or tic_id).

    Args:
        coord (SkyCoord, optional): A SkyCoord object representing the coordinates (RA, Dec) of the target.
        object_name (str, optional): The name of the celestial object to search.
        tic_id (int, optional): The TESS Input Catalog ID of the target.
        radius (float): The search radius in degrees.

    Returns:
        tuple: A tuple containing the queried TESS sectors and cutouts.

    Raises:
        ValueError: If no valid input (coord, object_name, or tic_id) is provided.
    """

    if coord:
        return query_sectors_with_coord(coord, radius)
    elif object_name:
        return query_sectors_with_object_name(object_name, radius)
    elif tic_id:
        return query_sectors_with_tic_id(tic_id, radius)
    else:
        raise ValueError("Error: Please provide either RA and Dec or Object Name or TIC ID.")


def process_sectors(sectors, cutouts):

    """
    Process the queried TESS sectors and cutouts to extract relevant information.

    Args:
        sectors (list): A list of TESS sectors.
        cutouts (list): A list of TESS cutouts.

    Returns:
        tuple: A tuple containing the processed results, cycle number, and observation date.
    """
    
    # create a list of results and store sector number, cycle, and camera for each sector
    results = []
    cycle = None
    obs_date = None

    for sector, cutout in zip(sectors, cutouts):

        # Retrieve the sector number from the sectors list
        current_sector_number = sector['sector']
        cycle = (current_sector_number - 1) // 13 + 1  # Calculate the cycle number
        
        # Retrieve the camera information from the sectors list
        camera = sector['camera']
        
        # Retrieve the observation date from the header of the first TPF in the cutout list
        obs_date = cutout[0].header['DATE-OBS']
       
        # Combine the information into a list
        result = [current_sector_number, cycle, camera, obs_date]
        results.append(result)  # Add the list to the results
    return results, cycle, obs_date

def get_ra_dec_from_tic_id(tic_id):

    """Retrieves the right ascension (RA) and declination (Dec) for a given TIC ID.

    Args:
        tic_id (int): The TESS Input Catalog (TIC) ID.

    Returns:
        tuple: A tuple containing the right ascension (RA) and declination (Dec) in degrees.

    Raises:
        ValueError: If the TIC ID is invalid.
    """

    coord, _, _, _, _ = resolve_input(str(tic_id))
    if coord is None:
        raise ValueError("Error: Invalid TIC ID.")
    return coord.ra.degree, coord.dec.degree

def process_csv_for_sky_map(csv_file):

    """Processes a CSV file and returns target data for creating a sky map.

    Args:
        csv_file (file-like object): A file-like object representing the CSV file.

    Returns:
        list: A list of dictionaries containing RA, Dec, and target name for each row in the CSV file.

    Raises:
        ValueError: If the input format is invalid or the object name cannot be resolved.
    """

    target_data = []


    # Read rows from the CSV file
    reader = csv.reader(csv_file, delimiter=',')

    for row in reader:
        # If the row contains RA and Dec coordinates, add them to the target_data list
        if len(row) == 2:
            ra, dec = row[:2]
            target_data.append({'ra': float(ra), 'dec': float(dec), 'target_name': None})
        
        # If the row contains a single element, it can be either a TIC ID or an object name    
        elif len(row) == 1:
            id_or_name = row[0]

            # If the element is a number, treat it as a TIC ID and get the corresponding RA and Dec
            if id_or_name.isdigit():
                tic_id = int(id_or_name)
                ra, dec = get_ra_dec_from_tic_id(tic_id)
                target_data.append({'ra': ra, 'dec': dec, 'target_name': f"TIC {tic_id}"})

                # Otherwise, treat it as an object name and get the corresponding coordinates
            else:
                try:
                    coord = SkyCoord.from_name(id_or_name)
                    target_data.append({'ra': coord.ra.degree, 'dec': coord.dec.degree, 'target_name': id_or_name})
                except NameResolveError:
                    raise ValueError("Error: Invalid object name.")
                
        # If the row has an invalid format, raise an error        
        else:
            raise ValueError("Error: Invalid input format.")

    return target_data

def get_targets_from_uploaded_csv(uploaded_csv_file):
    """Processes an uploaded CSV file and returns target data for creating a sky map.

    Args:
        uploaded_csv_file (file-like object): A file-like object representing the uploaded CSV file.

    Returns:
        list: A list of dictionaries containing RA, Dec, and target name for each row in the CSV file.
    """

    # Wrap the uploaded file in a TextIOWrapper to read it as a text file
    uploaded_csv_file = TextIOWrapper(uploaded_csv_file, 'utf-8')
    
    targets = process_csv_for_sky_map(uploaded_csv_file)
    return targets

#handles csv uploads from target_list.html making sure the file is open in text mode
def get_targets_from_uploaded_csv_diagrams(uploaded_csv_file, radius):
    """Processes an uploaded CSV file and returns target results for creating diagrams.

    Args:
        uploaded_csv_file (file-like object): A file-like object representing the uploaded CSV file.
        radius (float): The radius to use for queries in the process_csv function.

    Returns:
        list: A list of target results containing information about the TESS sectors that intersect
              with the given coordinates or TIC IDs and a specified radius.
    """
    print("im in get_targets_from_uploaded_csv_diagrams 2")

    # Wrap the uploaded file in a TextIOWrapper to read it as a text file
    uploaded_csv_file = TextIOWrapper(uploaded_csv_file, 'utf-8')
    
    results = process_csv(uploaded_csv_file, radius)
    print("im back in get_targets_from_uploaded_csv_diagrams 5")
    return results