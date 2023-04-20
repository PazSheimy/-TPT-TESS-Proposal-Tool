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
    #to implement default graph
    # error = None
    # default_luminosities, default_temperatures = default_hr_diagram()
    # hr_diagram_html = hr_diagram(default_luminosities, default_temperatures, "Default Stars")

    if request.method == 'POST':
        radius = 0.01
        csv_file = request.files.get('csv_file')
        print("im in target list function")
        results = get_targets_from_uploaded_csv_diagrams(csv_file, radius)
        print("im back in target_list_page just before entering in the loop 6")
        print(results)

        # Aggregate data for all cycles
        all_cycles = [result[4] for result in results]
        print("i just entered to the loop in  target_list_page 7")
        
        # Generate the sector graph with all the results
        print(" sector graph is going to be call now 8 ")
        sector_graph_html = sector_graph("All Targets", results, all_cycles)
        print(" sector graph was call 9 ")

        all_luminosities = []
        all_temperatures = []
        all_magnitudes = []
        all_distances = []

        # Replace the following lines with the new function
        coord_list = [SkyCoord(ra=result[0], dec=result[1], unit='deg') for result in results]
        metadata_list = get_metadata(coords=coord_list)

        for metadata in metadata_list:
            print(" entering in the loop for the metadata 10")
            luminosity, temperature, star_name, magnitudes, distance = metadata
            all_luminosities.extend(luminosity)
            all_temperatures.extend(temperature)
            all_magnitudes.extend(magnitudes)
            all_distances.extend(distance)
            print(" at the end of the loop 12 ")

        print(" generating graph after getting metadata 13 ")
        
        # Generate the HR Diagram for all targets
        hr_diagram_html = hr_diagram(all_luminosities, all_temperatures, "All Targets")
        print(" generating hr graph 14 ")

        # Generate the magnitude histogram for all targets
        magnitude_histogram_html = generate_magnitude_histogram("All Targets", all_magnitudes)
        print(" generating magnitude graph 15 ")
        
        if magnitude_histogram_html is None:
            magnitude_histogram_html = "No magnitude data available"
            print(" generating magnitude graph 15 ")

        # Generate the distance histogram for all targets
        distance_histogram_html = distance_histogram("All Targets", all_distances)
        print(" generating distance graph 16 ")

        return render_template('target_list.html', diagram1=sector_graph_html, diagram2=hr_diagram_html, diagram3=magnitude_histogram_html, diagram4=distance_histogram_html)

    return render_template('target_list.html')


# def target_list_page():
#     error = None
#     default_luminosities, default_temperatures = default_hr_diagram()
#     hr_diagram_html = hr_diagram(default_luminosities, default_temperatures, "Default Stars")
#     diagram2 = None  # Other diagrams


#     if request.method == 'POST':
#         radius = 0.01
#         csv_file = request.files.get('csv_file')
#         print("im in target list function")
#         results = get_targets_from_uploaded_csv_diagrams(csv_file, radius)
#         print("im back in target_list_page just before entering in the loop 6")
#         print(results)

#         # Aggregate data for all cycles
#         all_cycles = [result[4] for result in results]
#         print("i just entered to the loop in  target_list_page 7")
        
#         # Generate the sector graph with all the results
#         print(" sector graph is going to be call now 8 ")
#         sector_graph_html = sector_graph("All Targets", results, all_cycles)
#         print(" sector graph was call 9 ")

#         all_luminosities = []
#         all_temperatures = []
#         all_magnitudes = []
#         all_distances = []

#         # Replace the following lines with the new function
#         coord_list = [SkyCoord(ra=result[0], dec=result[1], unit='deg') for result in results]
#         metadata_list = get_metadata(coords=coord_list)

#         for metadata in metadata_list:
#             print(" entering in the loop for the metadata 10")
#             luminosity, temperature, star_name, magnitudes, distance = metadata
#             all_luminosities.extend(luminosity)
#             all_temperatures.extend(temperature)
#             all_magnitudes.extend(magnitudes)
#             all_distances.extend(distance)
#             print(" at the end of the loop 12 ")

#         print(" generating graph after getting metadata 13 ")

#         # Update the diagram variables with the new diagrams created based on the CSV file
#         hr_diagram_html += hr_diagram(default_luminosities, default_temperatures, "All Targets", additional_luminosities=all_luminosities, additional_temperatures=all_temperatures)

#         # Generate the HR Diagram for all targets
#         #hr_diagram_html = hr_diagram(all_luminosities, all_temperatures, "All Targets")
#         print(" generating hr graph 14 ")

#         # Generate the magnitude histogram for all targets
#         magnitude_histogram_html = generate_magnitude_histogram("All Targets", all_magnitudes)
#         print(" generating magnitude graph 15 ")
        
#         if magnitude_histogram_html is None:
#             magnitude_histogram_html = "No magnitude data available"
#             print(" generating magnitude graph 15 ")

#         # Generate the distance histogram for all targets
#         distance_histogram_html = distance_histogram("All Targets", all_distances)
#         print(" generating distance graph 16 ")

#         return render_template('target_list.html', diagram1=sector_graph_html, diagram2=hr_diagram_html, diagram3=magnitude_histogram_html, diagram4=distance_histogram_html)

#     return render_template('target_list.html', diagram2=hr_diagram_html)


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
