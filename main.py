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
#import csv_handle



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
    return render_template('index.html', results=results, download_url=download_url, enumerate=enumerate)


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
    return render_template("index.html")




@app.route("/sectors", methods=["POST"])
def get_input():
    # get the values of "search_input" and "radius" from the form data
    search_input = request.form.get("search_input")
    radius = request.form.get("radius")

    # Validate input for search_input and radius
    if not search_input:
        return render_template("index.html", error="Please provide a valid search input.")
    try:
        radius = float(radius)
    except ValueError:
        return render_template("index.html", error="Please provide a valid radius value like 0.5, 1 etc...")

    if radius <= 0:
        return render_template("index.html", error="Please provide a positive radius value.")

    csv_file = request.files.get("csv_file")
    if csv_file:
        # If a CSV file was uploaded, process it
        csv_contents = StringIO(csv_file.read().decode('utf-8'))
        csv_results = process_csv(csv_contents, radius)
    else:
        # Otherwise, process the search input normally
        csv_results = sectors(search_input, radius)

    # call the "sectors" function and store the returned values in variables
    try:
        results, ra, dec, object_name, tic_id, coord, sector_number, cycle, obs_date = sectors(
            search_input, radius)
        # call the "get_metadata" function and store the returned values in variables
        luminosity, temperature, star_name, magnitudes, distance = get_metadata(
            coord, object_name, tic_id)

        # call the "hr_diagram" function and store the returned value in "html1"
        html1 = hr_diagram(luminosity, temperature, star_name, sector_number)

        # call the "generate_magnitude_histogram" function and store the returned value in "html2"
        html2 = generate_magnitude_histogram(star_name, magnitudes, sector_number)

        # call the "distance_histogram" function and store the returned value in "html3"
        html3 = distance_histogram(star_name, sector_number, distance)

        # call the "sector_graph" function and store the returned value in "html4"
        html4 = sector_graph(object_name, results, cycle)

        # To download the csv result file
        download_url = url_for('download')

        # Render the HTML in a template and return it
        return render_template("index.html", results=results, star_name=object_name, sector_num=sector_number, diagram1=html1, diagram2=html2, diagram3=html3, diagram4=html4, csv_results=csv_results, download_url=download_url, enumerate=enumerate)

    except requests.exceptions.ConnectTimeout:
        return render_template("index.html", error="The connection to the MAST API timed out. Please try again later.")


def sectors(search_input, radius):
    try:
        sectors = Tesscut.get_sectors(coordinates=search_input, radius=radius)
    except ResolverError:
        # Display an error message to the user and prompt them to try again
        return "Could not resolve input to a sky position. Please try again with a different input."


    # initialize variables with None
    coord = None
    ra = None
    dec = None
    object_name = None
    tic_id = None

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

    # Query the sectors based on the type of the input (coord, object_name, or tic_id)
    if coord:
        sectors = Tesscut.get_sectors(
            coordinates=coord, radius=float(radius)*u.deg)
        cutouts = Tesscut.get_cutouts(coordinates=coord)
    elif object_name:
        sectors = Tesscut.get_sectors(
            objectname=object_name, radius=float(radius)*u.deg)
        cutouts = Tesscut.get_cutouts(coordinates=object_name)
    elif tic_id:
        sectors = Tesscut.get_sectors(
            objectname=tic_id, radius=float(radius)*u.deg)
        cutouts = Tesscut.get_cutouts(coordinates=tic_id)

    else:
        return "Error: Please provide either RA and Dec or Object Name or TIC ID."

    # create a list of results and store sector number, cycle, and camera for each sector
    results = []
    for sector, cutout in zip(sectors, cutouts):
        # Retrieve the sector number from the sectors list
        sector_number = sector['sector']
        cycle = (sector_number - 1) // 13 + 1  # Calculate the cycle number
        # Retrieve the camera information from the sectors list
        camera = sector['camera']
        # Retrieve the observation date from the header of the first TPF in the cutout list
        obs_date = cutout[0].header['DATE-OBS']
        # Combine the information into a list
        result = [sector_number, cycle, camera, obs_date]
        results.append(result)  # Add the list to the results

    return results, ra, dec, object_name, tic_id, coord, sector_number, cycle, obs_date


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
    writer.writerow(['RA', 'Dec', 'Sector', 'Cycle', 'Camera', 'Observation Date'])

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
