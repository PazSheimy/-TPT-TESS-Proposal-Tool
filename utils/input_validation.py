from flask import render_template, request
import requests
from utils.sector_processing import process_data, get_targets_from_uploaded_csv, process_csv, get_targets_from_uploaded_csv_diagrams
from utils.metadata import get_metadata
from utils.visualization import generate_magnitude_histogram,hr_diagram,distance_histogram, sector_graph
from astropy.coordinates import SkyCoord

def target_visualization_page():
    table_visibility = 'hidden'

    if request.method == 'POST':
        target = request.form.get('target')
        table_visibility = 'visible'

        # Render the template with the processed data
        return render_template("target_visualization.html", target=target, table_visibility=table_visibility)

    return render_template("target_visualization.html", table_visibility=table_visibility)


def target_list_page():
    if request.method == 'POST':
        radius = 0.01
        csv_file = request.files.get('csv_file')
        results = get_targets_from_uploaded_csv_diagrams(csv_file, radius)

        # Aggregate data for all cycles
        all_cycles = [result[4] for result in results]
        
        # Generate the sector graph with all the results
        sector_graph_html = sector_graph("All Targets", results, all_cycles)

            # Create a SkyCoord object using the right ascension (ra) and declination (dec)
           # coord = SkyCoord(ra=ra, dec=dec, unit='deg')
            # Get the luminosity, temperature, star_name, magnitudes, and distance for the target
            #luminosity, temperature, star_name, magnitudes, distance = get_metadata(
            #    coord, object_name = None, tic_id= None)

            # Generate the sector graphs
             #sector_graphs = generate_sector_graphs(
              #      star_name, results)

            # # Generate the HR Diagram
            # hr_diagram_html = hr_diagram(
            #     luminosity, temperature, star_name, sector_number)

            # # Generate the magnitude histogram
            # magnitude_histogram_html = generate_magnitude_histogram(
            #     star_name, magnitudes, sector_number)

            # # Generate the distance histogram
            # distance_histogram_html = distance_histogram(
            #     star_name, sector_number, distance)

            # diagrams.append((sector_graphs, hr_diagram_html, magnitude_histogram_html, distance_histogram_html))

            

        return render_template('target_list.html', diagram1=sector_graph_html)


    return render_template('target_list.html')


#function to validate inputs
def validate_inputs(search_input, radius, sector_selection):
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
