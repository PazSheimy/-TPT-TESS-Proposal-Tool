from flask import Flask, render_template, request, redirect, url_for, Response, make_response, flash
from flask_wtf import FlaskForm
from wtforms import FileField, SubmitField, StringField, IntegerField
from werkzeug.utils import secure_filename
import os
from wtforms.validators import InputRequired, Optional
from astroplan import Observer, FixedTarget
from astropy.coordinates import SkyCoord
from astroquery.mast import Tesscut, Catalogs
from astroquery.exceptions import ResolverError
from astropy import units as u
from bokeh.plotting import figure
from bokeh.embed import file_html
from bokeh.resources import CDN
from bokeh.resources import Resources
import numpy as np
from bokeh.models import ColumnDataSource
import csv
from io import StringIO
import requests.exceptions
from requests.exceptions import ConnectionError
from astropy.coordinates.name_resolve import NameResolveError




app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecretkey'
app.config['UPLOAD_FOLDER'] = 'static/files'

class UploadFileForm(FlaskForm):
    file = FileField("File", validators=[InputRequired()])
    submit = SubmitField("Upload File")

class QueryForm(FlaskForm):
    query = StringField("Query", validators=[InputRequired()])
    sector = IntegerField("Sector", validators=[Optional()])
    submit = SubmitField("Submit Query")

# Route for handling POST requests to upload a CSV file
@app.route('/csv_upload', methods=['POST'])
def csv_upload():

    # Get the value of the radius parameter from the request form
    radius = request.form.get('radius')

    # Get the uploaded CSV file from the request files
    csv_file = request.files.get('csv_file')

    # Check if a radius value was provided
    if not radius:
        # If not, return an error message to the index.html template
        return render_template('index.html', error='Radius value is required')

    # Attempt to convert the radius to a float value
    try:
        radius_float = float(radius)
    except ValueError:
        # If the conversion fails, return an error message to the index.html template
        return render_template('index.html', error='Invalid radius value')

    # Check if a CSV file was provided
    if not csv_file:
        # If not, return an error message to the index.html template
        return render_template('index.html', error='CSV file is required')

    try:
        # Read the contents of the CSV file into a StringIO object and decode it as UTF-8
        csv_contents = StringIO(csv_file.read().decode('utf-8'))

        # Call the process_csv function with the CSV contents and the provided radius
        results = process_csv(csv_contents, radius_float)
    except Exception as e:
        # If there is an error processing the CSV file, return an error message to the index.html template
        return render_template('index.html', error=f'Error processing CSV file: {str(e)}')

    # Generate a URL for the download route and render the index.html template with the results and download URL
    download_url = url_for('download', results=results)
    return render_template('index.html', results=results, download_url=download_url, enumerate=enumerate, csv_file=csv_file)


def process_csv(csv_file, radius):
    # Create an empty list to store the results
    target_results = []
    # Use the built-in csv module to read the csv_file
    reader = csv.reader(csv_file, delimiter=',')
    # Iterate over each row in the csv_file
    for row in reader:
        # Get the right ascension and declination from the row
        ra, dec = row[:2]
        # Use the SkyCoord object from the astropy.coordinates module to create a coordinate object
        coord = SkyCoord(f"{ra} {dec}", unit="deg")
        # Use the TESScut.get_sectors() function to get the TESS sectors that intersect with the given coordinate and radius
        sectors = Tesscut.get_sectors(
            coordinates=coord, radius=float(radius)*u.deg)
        cutouts = Tesscut.get_cutouts(coordinates=coord)

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
    return target_results


@app.route("/")
def index():
    # sets <table> container visibility to 'hidden' upon page load
    table_visibility = 'hidden'

    return render_template("index.html", table_visibility=table_visibility)


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

@app.route("/sectors", methods=["POST"])
def get_input():
    search_input = request.form.get("search_input")
    radius = request.form.get("radius")
    sector_selection = request.form.get("sector")

    is_valid, validation_result = validate_inputs(search_input, radius, sector_selection)

    if not is_valid:
        return render_template("index.html", error=validation_result)
    
    search_input, radius, sector_number = validation_result

    try:
        processed_data = process_data(search_input, radius, sector_number)
        return render_template("index.html", **processed_data)
    except requests.exceptions.ConnectTimeout:
        return render_template("index.html", error="The connection to the MAST API timed out. Please try again later.")

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


def resolve_input(search_input):
     # initialize variables with None
    coord = None
    ra = None
    dec = None
    object_name = None
    tic_id = None
    sector_number = None

    # try to convert the search_input into a SkyCoord object
    try:
        coord = SkyCoord(search_input, unit="deg")
        ra = coord.ra.degree
        dec = coord.dec.degree
    except:
        # if the conversion fails, check if the search_input contains a space
        if " " in search_input:
            try:
                # if the search_input contains a space, split it into ra and dec
                ra, dec = search_input.split(" ")
                coord = SkyCoord(f"{ra} {dec}", unit="deg")
            except:
                # if this conversion also fails, coord will still be None
                pass
        # if coord is still None, check if the search_input is a digit
        if not coord:
            if search_input.isdigit():
                # if the search_input is a digit, store it in tic_id
                tic_id = search_input
                object_name = "TIC " + tic_id
            else:
                # if the search_input is not a digit, store it in object_name
                object_name = search_input
        else:
            # if the input is not ra/dec, object name or tic id, return an error message
            return "Error: Please enter a correct input (RA/Dec, object name, or TIC ID)."

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

        # Get the coordinates of the TIC ID
        catalog_data = Catalogs.query_object(tic_id, catalog="TIC")
        ra = catalog_data[0]['ra']
        dec = catalog_data[0]['dec']
        coord = SkyCoord(ra, dec, unit="deg")

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

def sectors(search_input, radius, sector_number):
    
    coord, ra, dec, object_name, tic_id = resolve_input(search_input)

    if not coord and not object_name and not tic_id:
        return "Error: Please enter a correct input (RA/Dec, object name, or TIC ID)."

    queried_sectors, cutouts = query_sectors(coord, object_name, tic_id, radius)

    results, cycle, obs_date = process_sectors(queried_sectors, cutouts)

    return results, ra, dec, object_name, tic_id, coord, sector_number, cycle, obs_date


def generate_sector_graphs(object_name, results):
    sector_graphs = []
    for result in results:
        sector_graphs.append(sector_graph(object_name, [result], result[1]))
    return sector_graphs


def get_metadata(coord, object_name, tic_id):
    # Check if the input is a coordinate
    if coord:
        # Query the metadata of the star using the coordinate
        metadata = Catalogs.query_region(
            coord, radius=30 * u.arcmin, catalog="Tic")
        star_name = f"{coord.ra.degree} {coord.dec.degree}"
    # Check if the input is an object name
    elif object_name:
        # Query the metadata of the star using the object name
        metadata = Catalogs.query_object(object_name, catalog="Tic")
        star_name = object_name
    # Check if the input is a TIC ID
    elif tic_id:
        # Query the metadata of the star using the TIC ID
        metadata = Catalogs.query_object(tic_id, catalog="Tic")
        star_name = "TIC " + tic_id
    else:
        # Return None if no input is provided
        return None

    # Retrieve the luminosity and temperature from the metadata
    luminosity = metadata['lum'] * u.solLum
    temperature = metadata['Teff'] * u.K
    magnitudes = metadata['Tmag']
    distance = metadata['dstArcSec']

    return luminosity, temperature, star_name, magnitudes, distance


def hr_diagram(luminosity, temperature, star_name, sector_number):
    # Create a figure with the title HR Diagram for [star_name] (Sector [sector_number])
    p = figure(title=f"HR Diagram for {star_name} (Sector {sector_number})")
    # Add a scatter plot of temperature vs. luminosity to the figure
    p.circle(temperature, luminosity.to(u.W))
    # Label the x-axis as Temperature (K)
    p.xaxis.axis_label = "Temperature (K)"
    # Label the y-axis as Lumin
    p.yaxis.axis_label = "Luminosity (solLum)"

    # how the component should size itself
    p.sizing_mode = "scale_both"

    # Set mode of resources to cdn for faster loading
    resources = Resources(mode='cdn')
    # Create HTML file from figure with specified title
    html1 = file_html(p, resources=resources,
                      title=f"HR Diagram for {star_name} (Sector {sector_number})")

    return html1


def generate_magnitude_histogram(star_name, magnitudes, sector_number):
    min_value = np.min(magnitudes)
    max_value = np.max(magnitudes)
    hist, edges = np.histogram(magnitudes, bins=200)

    # Define the data source for the histogram
    source = ColumnDataSource(data=dict(
        top=hist,
        bottom=np.zeros_like(hist),
        left=edges[:-1],
        right=edges[1:],
    ))

    # Create a Bokeh figure object and add the histogram to it
    p = figure(title=f"{star_name} Magnitude Histogram",
               x_axis_label='Magnitude', y_axis_label='Frequency')
    p.quad(top='top', bottom='bottom', left='left',
           right='right', source=source)

    p.xaxis.axis_label = "TESS Magnitude"
    p.yaxis.axis_label = "Density"

    # how the component should size itself
    p.sizing_mode = "scale_both"

    # Generate the HTML for the magnitude histogram
    resources = Resources(mode='cdn')
    html2 = file_html(p, resources=resources,
                      title=f"Magnitude Histogram for {star_name} (Sector {sector_number})")

    return html2


def distance_histogram(star_name, sector_num, distance):
    # Generate some sample data
    distances = distance

    # Create a histogram of the distances
    hist, edges = np.histogram(distances, bins=50)

    # Define the data source for the histogram
    source = ColumnDataSource(data=dict(
        top=hist,
        bottom=np.zeros_like(hist),
        left=edges[:-1],
        right=edges[1:],
    ))

    # Create a Bokeh figure object and add the histogram to it
    p = figure(title="Distance Histogram",
               x_axis_label='Distance (parsecs)', y_axis_label='Frequency')
    p.quad(top='top', bottom='bottom', left='left',
           right='right', source=source, line_color="#033649")

    # how the component should size itself
    p.sizing_mode = "scale_both"

    # shows the histogram of distances with the x-axis showing the distance in parsecs and
    # the y-axis showing the frequency of each distance.
    resources = Resources(mode='cdn')
    html3 = file_html(p, resources=resources,
                      title=f"Magnitude Histogram for {star_name} (Sector {sector_num})")
    return html3


def sector_graph(object_name, results, cycle):
    sectors = []
    cycles = []

    for array in results:
        sector = array[0]
        cycle = array[1]
        sectors.append(sector)
        cycles.append(cycle)

    # Create a ColumnDataSource object with the sector and cycle data
    source = ColumnDataSource(data=dict(sectors=sectors, cycles=cycles))

    # Create a new plot with a title and axis labels
    p = figure(title='Observed Sectors',
               x_axis_label='Sector', y_axis_label='Cycle')

    # Add a scatter plot with the sector and cycle data
    p.vbar(x='sectors', top='cycles', source=source,
           width=0.9, line_color="#033649")

    # Set the chart range for the x-axis and y-axis
    p.x_range.start = 0
    p.y_range.start = 0

    # # how the component should size itself
    p.sizing_mode = "scale_both"

    # shows the histogram of distances with the x-axis showing the distance in parsecs and
    # the y-axis showing the frequency of each distance.
    resources = Resources(mode='cdn')
    html4 = file_html(p, resources=resources,
                      title=f"Sectors Observed for {object_name}")
    return html4


@app.route('/download', methods=['GET', 'POST'])
def download():
    results = request.args.getlist('results')

    # Create a dictionary to store the data
    data = {}
    for result in results:
        try:
            ra, dec, sector_number, cycle, camera, obs_date = map(
                str.strip, result.split(','))
            ra = float(ra.strip('[]'))
            dec = float(dec.strip('[]'))
            if ra not in data:
                data[ra] = {}
            if dec not in data[ra]:
                data[ra][dec] = []
            data[ra][dec].append([sector_number, cycle, camera, obs_date])
        except ValueError:
            pass

    # Generate a CSV file from the data
    csv_data = StringIO()
    writer = csv.writer(csv_data)
    writer.writerow(['RA', 'Dec', 'Sector', 'Camera', 'Cycle', 'Observation Date'])

    for ra, dec_dict in data.items():
        for dec, row_list in dec_dict.items():
            for idx, row in enumerate(row_list):
                writer.writerow([ra if idx == 0 else '', dec if idx ==
                                0 else '', *row[:-1], row[-1].rstrip(']')])

    # Return the CSV data as a response
    response = make_response(csv_data.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=results.csv'
    response.headers['Content-Type'] = 'text/csv'
    return response


if __name__ == "__main__":
    app.run(debug=True)
    