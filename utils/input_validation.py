from flask import render_template, request
import requests
from utils.sector_processing import process_data


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
        ra = request.form.get('target-list')
        dec = request.form.get('target-list-dec')
        radius = request.form.get('target-list-radius')
        
        # Process the data and generate graphs
        diagram1, diagram2, diagram3, diagram4 = process_data(ra, dec, radius)

        return render_template('target_list.html', diagram1=diagram1, diagram2=diagram2, diagram3=diagram3, diagram4=diagram4)
    
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
