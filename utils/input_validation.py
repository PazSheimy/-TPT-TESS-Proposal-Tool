"""
This module defines the main logic for handling target visualization and target list pages for a web application
using Flask. It processes the user's input from the forms, fetches the necessary data, generates the required
plots, and renders the templates with the corresponding information.

Dependencies:
- flask
- requests
- utils.sector_processing
- utils.metadata
- utils.visualization
- astropy.coordinates

"""

from flask import render_template, request
import requests
from utils.sector_processing import process_data, get_targets_from_uploaded_csv_diagrams # get_targets_from_uploaded_csv, process_csv
from utils.metadata import get_metadata
from utils.visualization import generate_magnitude_histogram,hr_diagram,distance_histogram, sector_graph
from astropy.coordinates import SkyCoord


def target_visualization_page():
    """
    Render the target visualization page based on the user's input.

    This function handles both GET and POST requests to display the target visualization page.
    If a POST request is received, it extracts the target name from the request form and sets
    the table visibility to 'visible'. In case of a GET request, the table visibility is set
    to 'hidden'.

    Returns:
        A rendered HTML template for the target visualization page with the appropriate
        table visibility setting based on the request method.
    """

    table_visibility = 'hidden'

    if request.method == 'POST':
        target = request.form.get('target')
        table_visibility = 'visible'

        # Render the template with the processed data
        return render_template("target_visualization.html", target=target, table_visibility=table_visibility)

    return render_template("target_visualization.html", table_visibility=table_visibility)

def target_list_page():
    """
    Render the target list page and process the user's input.

    This function handles both GET and POST requests to display the target list page.
    If a POST request is received, it processes the uploaded CSV file containing target
    coordinates, calculates the relevant data, and generates various visualizations such
    as sector graph, HR diagram, magnitude histogram, and distance histogram for all targets.
    In case of a GET request, an empty target list page is displayed.

    Returns:
        A rendered HTML template for the target list page with generated visualizations
        based on the user's input in case of a POST request, or an empty target list page
        for a GET request.
    """

    if request.method == 'POST':
        # Define search radius and retrieve uploaded CSV file
        radius = 0.01
        csv_file = request.files.get('csv_file')

        # Process CSV file and retrieve target data
        results = get_targets_from_uploaded_csv_diagrams(csv_file, radius)
        print(results)#take out after just for debuging

        # Aggregate data for all cycles
        all_cycles = [result[4] for result in results]
        
        # Generate the sector graph with all the results
        sector_graph_html = sector_graph("All Targets", results, all_cycles)
        
        # Initialize lists for storing target metadata
        all_luminosities = []
        all_temperatures = []
        all_magnitudes = []
        all_distances = []

        # Retrieve metadata for each target
        coord_list = [SkyCoord(ra=result[0], dec=result[1], unit='deg') for result in results]
        metadata_list = get_metadata(coords=coord_list)

        # Process and aggregate metadata
        for metadata in metadata_list: 
            luminosity, temperature, star_name, magnitudes, distance = metadata
            all_luminosities.extend(luminosity)
            all_temperatures.extend(temperature)
            all_magnitudes.extend(magnitudes)
            all_distances.extend(distance)
        
        # Generate the HR Diagram for all targets
        hr_diagram_html = hr_diagram(all_luminosities, all_temperatures, "All Targets")
        
        # Generate the magnitude histogram for all targets
        magnitude_histogram_html = generate_magnitude_histogram("All Targets", all_magnitudes)
        
        # Handle missing magnitude data
        if magnitude_histogram_html is None:
            magnitude_histogram_html = "No magnitude data available"        

        # Generate the distance histogram for all targets
        distance_histogram_html = distance_histogram("All Targets", all_distances)
        
        # Return the rendered template with generated visualizations
        return render_template('target_list.html', diagram1=sector_graph_html, diagram2=hr_diagram_html, diagram3=magnitude_histogram_html, diagram4=distance_histogram_html)

    return render_template('target_list.html')



#function to validate inputs
def validate_inputs(search_input, radius, sector_selection):
    """
    Validate the user-provided input parameters for search.

    This function checks the validity of the search input, radius, and sector_selection
    provided by the user. If the inputs are valid, the function returns True along with
    a tuple containing the search input, radius, and sector number. If any input is invalid,
    the function returns False along with an appropriate error message.

    Args:
        search_input (str): The search input provided by the user.
        radius (str): The radius value provided by the user, as a string.
        sector_selection (str): The sector selection provided by the user, as a string.

    Returns:
        A tuple with the first element being a boolean indicating whether the inputs are
        valid (True) or not (False), and the second element being either an error message
        (str) if the inputs are invalid, or a tuple containing the search input, radius (float),
        and sector number (int or None) if the inputs are valid.
    """

    if not search_input:
        return False, "Please provide a valid search input."
    
    try:
        radius = float(radius)
    except ValueError:
        return False, "Please provide a valid radius value like 0.5, 1 etc..."
    
    if radius <= 0:
        return False, "Please provide a positive radius value."

    try:
        sector_number = int(sector_selection) if sector_selection else None
    except ValueError:
        return False, "Please provide a valid sector number."
    
    return True, (search_input, radius, sector_number)


def get_input():
    """
    Retrieve and validate input parameters from the form, and render the target visualization page.

    This function retrieves the search_input, radius, and sector_selection values from the form
    submitted by the user, validates them using the validate_inputs function, and processes the
    data if the inputs are valid. If any of the input parameters are not valid, an error message
    is displayed on the target visualization page. If the MAST API connection times out, an
    appropriate error message is also displayed.

    Returns:
        A rendered template of the target visualization page with the processed data or an
        appropriate error message.
    """
    search_input = request.form.get("search_input")
    radius = request.form.get("radius")
    sector_selection = request.form.get("sector")

    is_valid, validation_result = validate_inputs(search_input, radius, sector_selection)

    if not is_valid:
        return render_template("target_visualization.html", error=validation_result)
    
    search_input, radius, sector_number = validation_result

    try:
        processed_data = process_data(search_input, radius, sector_number)
        return render_template("target_visualization.html", **processed_data)
    except requests.exceptions.ConnectTimeout:
        return render_template("target_visualization.html", error="The connection to the MAST API timed out. Please try again later.")
