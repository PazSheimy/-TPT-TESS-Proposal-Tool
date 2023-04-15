import csv
from astroquery.mast import Tesscut, Catalogs, Observations
from astropy.coordinates import SkyCoord
from .metadata import get_metadata
from .visualization import generate_magnitude_histogram, generate_sector_graphs, hr_diagram, distance_histogram, sector_graph
from flask import url_for
from astropy.coordinates.name_resolve import NameResolveError
from astropy import units as u
from io import TextIOWrapper

def process_csv(csv_file, radius):
    # Create an empty list to store the results
    target_results = []

    # Use the built-in csv module to read the csv_file
    reader = csv.reader(csv_file, delimiter=',')

    # Iterate over each row in the csv_file
    for row in reader:
        if len(row) == 2:
            # Get the right ascension and declination from the row
            ra, dec = row[:2]
            # Use the SkyCoord object from the astropy.coordinates module to create a coordinate object
            coord = SkyCoord(f"{ra} {dec}", unit="deg")
            # Use the TESScut.get_sectors() function to get the TESS sectors that intersect with the given coordinate and radius
            sectors = Tesscut.get_sectors(
                coordinates=coord, radius=float(radius)*u.deg)
            cutouts = Tesscut.get_cutouts(coordinates=coord)
        elif len(row) == 1:
            id_or_name = row[0]
            # Check if input is a TIC ID
            if id_or_name.isdigit():
                tic_id = int(id_or_name)
                # Query the TIC catalog for the object's coordinates
                tic_object = Catalogs.query_criteria(catalog="TIC", ID=tic_id)
                ra = float(tic_object['ra'][0])
                dec = float(tic_object['dec'][0])
                coord = SkyCoord(f"{ra} {dec}", unit="deg")
                sectors = Tesscut.get_sectors(coordinates=coord, radius=float(radius)*u.deg)
                cutouts = Tesscut.get_cutouts(coordinates=coord)
            else:
                # Input is an object name
                try:
                    coord = SkyCoord.from_name(id_or_name)  # Fetch the coordinates of the object by its name
                    sectors = Tesscut.get_sectors(coordinates=coord, radius=float(radius)*u.deg)
                    cutouts = Tesscut.get_cutouts(coordinates=coord)
                except NameResolveError:
                    raise ValueError("Error: Invalid object name.")
        else:
            raise ValueError("Error: Invalid input format.")

        # Iterate over each sector that intersects with the given coordinate and radius
        for sector, cutout in zip(sectors, cutouts):
            # Get the sector number, cycle number, and camera number for the sector
            sector_number = sector['sector']
            cycle = (sector_number - 1) // 13 + 1
            camera = sector['camera']
            # Retrieve the observation date from the header of the first TPF in the cutout list
            obs_date = cutout[0].header['DATE-OBS']
            # Append the results to the target_results list
            target_results.append(
                [coord.ra.deg, coord.dec.deg, sector_number, camera, cycle,obs_date])
    # Return the target_results list

    print(target_results)
    return target_results

def process_data(search_input, radius, sector_number):
    all_results, ra, dec, object_name, tic_id, coord, sector_number, cycle, obs_date = sectors(
        search_input, radius, sector_number)
    luminosity, temperature, star_name, magnitudes, distance = get_metadata(
        coord, object_name, tic_id)

    # Filter the results based on the entered sector number
    if sector_number is not None:
        filtered_results = [result for result in all_results if result[0] == int(sector_number)]
    else:
        filtered_results = all_results

    sector_graphs = generate_sector_graphs(object_name, all_results)

    # Generate sector graphs for all the results
    sector_graphs = generate_sector_graphs(object_name, all_results)

    html1 = hr_diagram(luminosity, temperature, star_name, sector_number)
    html2 = generate_magnitude_histogram(star_name, magnitudes, sector_number)
    html3 = distance_histogram(star_name, sector_number, distance)
    html4 = sector_graph(object_name, all_results, cycle)
    download_url = url_for('download')

    # sets <table> visibility to 'visible' once query results are received
    table_visibility = 'visible'

    return {
        "results": filtered_results,
        "star_name": object_name,
        "sector_num": sector_number,
        "diagram1": html1,
        "diagram2": html2,
        "diagram3": html3,
        "diagram4": html4,
        "sector_graphs": sector_graphs,
        "download_url": download_url,
        "enumerate": enumerate,
        "table_visibility": table_visibility,
    }


def sectors(search_input, radius, sector_number):
    
    coord, ra, dec, object_name, tic_id = resolve_input(search_input)

    if not coord and not object_name and not tic_id:
        return "Error: Please enter a correct input (RA/Dec, object name, or TIC ID)."

    queried_sectors, cutouts = query_sectors(coord, object_name, tic_id, radius)

    results, cycle, obs_date = process_sectors(queried_sectors, cutouts)

    return results, ra, dec, object_name, tic_id, coord, sector_number, cycle, obs_date


def resolve_input(search_input):
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



def query_sectors(coord, object_name, tic_id, radius):
    # Query the sectors based on the type of the input (coord, object_name, or tic_id)
    if coord:
        sectors = Tesscut.get_sectors(
            coordinates=coord, radius=float(radius)*u.deg)
        cutouts = Tesscut.get_cutouts(coordinates=coord)
    elif object_name:
        try:
            sectors = Tesscut.get_sectors(
                objectname=object_name, radius=float(radius)*u.deg)
            cutouts = Tesscut.get_cutouts(coordinates=object_name)
        except NameResolveError:
            raise ValueError("Error: Invalid object name.")
    elif tic_id:
        # Check and add 'TIC' prefix if needed
        tic_id = str(tic_id).strip()
        if not tic_id.startswith("TIC"):
            tic_id = "TIC " + tic_id

        # Use the coordinates to query sectors and cutouts
        sectors = Tesscut.get_sectors(
            coordinates=tic_id, radius=float(radius)*u.deg)
        cutouts = Tesscut.get_cutouts(coordinates=tic_id)
    else:
        raise ValueError("Error: Please provide either RA and Dec or Object Name or TIC ID.")
    
    return sectors, cutouts

def process_sectors(sectors, cutouts):

    # create a list of results and store sector number, cycle, and camera for each sector
    results = []
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
    coord, _, _, _, _ = resolve_input(str(tic_id))
    if coord is None:
        raise ValueError("Error: Invalid TIC ID.")
    return coord.ra.degree, coord.dec.degree

def process_csv_for_sky_map(csv_file):
    target_data = []

    reader = csv.reader(csv_file, delimiter=',')

    for row in reader:
        if len(row) == 2:
            ra, dec = row[:2]
            target_data.append({'ra': float(ra), 'dec': float(dec), 'target_name': None})
        elif len(row) == 1:
            id_or_name = row[0]
            if id_or_name.isdigit():
                tic_id = int(id_or_name)
                ra, dec = get_ra_dec_from_tic_id(tic_id)
                target_data.append({'ra': ra, 'dec': dec, 'target_name': f"TIC {tic_id}"})
            else:
                try:
                    coord = SkyCoord.from_name(id_or_name)
                    target_data.append({'ra': coord.ra.degree, 'dec': coord.dec.degree, 'target_name': id_or_name})
                except NameResolveError:
                    raise ValueError("Error: Invalid object name.")
        else:
            raise ValueError("Error: Invalid input format.")

    return target_data

def get_targets_from_uploaded_csv(uploaded_csv_file):
    # Wrap the uploaded file in a TextIOWrapper
    uploaded_csv_file = TextIOWrapper(uploaded_csv_file, 'utf-8')
    
    targets = process_csv_for_sky_map(uploaded_csv_file)
    return targets


