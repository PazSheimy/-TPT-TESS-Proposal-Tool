from flask import Flask, render_template, request, redirect, url_for
from flask_wtf import FlaskForm
from wtforms import FileField, SubmitField, StringField, IntegerField
from werkzeug.utils import secure_filename
import os
from wtforms.validators import InputRequired, Optional
from astroplan import Observer,FixedTarget
from astropy.coordinates import SkyCoord
from astroquery.mast import Tesscut, Catalogs
from astropy import units as u
from bokeh.plotting import figure
from bokeh.embed import file_html
from bokeh.resources import CDN
from bokeh.resources import Resources
import numpy as np
from bokeh.models import ColumnDataSource

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

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/sectors", methods=["POST"])
# def sectors():
#     search_input = request.form.get("search_input")
#     radius = request.form.get("radius")

#     coord = None
#     ra = None
#     dec = None
#     object_name = None
#     tic_id = None

#     try:
#         coord = SkyCoord(search_input, unit = "deg")
#         ra = coord.ra.degree
#         dec = coord.dec.degree
#     except:
#         if " " in search_input:
#             try:
#                 ra, dec = search_input.split(" ")
#                 coord = SkyCoord(f"{ra} {dec}", unit = "deg")
#             except:
#                 pass
#         if not coord:
#             if search_input.isdigit():
#                 tic_id = search_input
#                 object_name = "TIC " + tic_id
#             else:
#                 object_name = search_input

#     if coord:
#         sectors = Tesscut.get_sectors(coordinates=coord, radius=float(radius)*u.deg)
#     elif object_name:
#         sectors = Tesscut.get_sectors(objectname=object_name, radius=float(radius)*u.deg)
#     elif tic_id:
#         sectors = Tesscut.get_sectors(objectname=tic_id, radius=float(radius)*u.deg)
#     else:
#         return "Error: Please provide either RA and Dec or Object Name or TIC ID."

#     results = []
#     for sector in sectors:
#         sector_number = sector['sector']
#         cycle = (sector_number - 1) // 13 + 1
#         camera = sector['camera']
#         result = [sector_number, cycle, camera]
#         results.append(result)

#      # Get the HR diagram information for the target object
#     if coord:
#         tess_cutout = Tesscut.download_cutouts(coordinates=coord, size=5)
#         metadata = Catalogs.query_region(coord, radius=30 * u.arcmin,catalog="Tic")
#         star_name = f"{ra} {dec}"
#     elif object_name:
#         tess_cutout = Tesscut.download_cutouts(objectname=object_name, size=5)
#         metadata = Catalogs.query_object(object_name, catalog="Tic")
#         star_name = object_name
#     else:
#         return "Error: Please provide either RA and Dec or Object Name or TIC ID."


#     # Extracting the values of the "lum" and "Teff" columns
#     luminosity = metadata['lum'] * u.solLum
#     temperature = metadata['Teff'] * u.K
    
#     # Create the HR diagram plot
#     p = figure(title=f"HR Diagram for {star_name} (Sector {sector_number})")
#     p.circle(temperature, luminosity.to(u.W))
#     p.xaxis.axis_label = "Temperature (K)"
#     p.yaxis.axis_label = "Luminosity (solLum)" 

#     resources = Resources(mode='cdn')
#     html = file_html(p, resources=resources, title=f"HR Diagram for {star_name} (Sector {sector_number})")
#     return render_template("index.html", results=results, star_name=object_name, sector_num=sector_number, diagram=html)


def get_input():
    # get the values of "search_input" and "radius" from the form data
    search_input = request.form.get("search_input")
    radius = request.form.get("radius")

    # call the "sectors" function and store the returned values in variables
    results, ra, dec, object_name, tic_id, coord, sector_number = sectors(search_input, radius)

    luminosity, temperature, star_name, magnitudes, distance = get_metadata(coord, object_name, tic_id)

    # call the "hr_diagram" function and store the returned value in "html"
    html1 = hr_diagram(luminosity, temperature, star_name, sector_number)

    html2 = generate_magnitude_histogram(star_name, magnitudes, sector_number) #generate_magnitude_histogram(star_name, magnitudes, sector_num, distance, mass)
    
    html3 = distance_histogram(star_name, sector_number, distance)

    # Render the HTML in a template and return it
    return render_template("index.html", results=results, star_name=object_name, sector_num=sector_number, diagram1=html1,diagram2=html2, diagram3=html3)

def sectors(search_input, radius):
    # initialize variables with None
    coord = None
    ra = None
    dec = None
    object_name = None
    tic_id = None

    # try to convert the search_input into a SkyCoord object
    try:
        coord = SkyCoord(search_input, unit = "deg")
        ra = coord.ra.degree
        dec = coord.dec.degree
    except:
        # if the conversion fails, check if the search_input contains a space
        if " " in search_input:
            try:
                # if the search_input contains a space, split it into ra and dec
                ra, dec = search_input.split(" ")
                coord = SkyCoord(f"{ra} {dec}", unit = "deg")
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

    # Query the sectors based on the type of the input (coord, object_name, or tic_id)
    if coord:
        sectors = Tesscut.get_sectors(coordinates=coord, radius=float(radius)*u.deg)
    elif object_name:
        sectors = Tesscut.get_sectors(objectname=object_name, radius=float(radius)*u.deg)
    elif tic_id:
        sectors = Tesscut.get_sectors(objectname=tic_id, radius=float(radius)*u.deg)
    else:
        return "Error: Please provide either RA and Dec or Object Name or TIC ID."

    # create a list of results and store sector number, cycle, and camera for each sector
    results = []
    for sector in sectors:
        sector_number = sector['sector'] # Retrieve the sector number
        cycle = (sector_number - 1) // 13 + 1 # Calculate the cycle number
        camera = sector['camera'] # Retrieve the camera information
        result = [sector_number, cycle, camera] # Combine the information into a list
        results.append(result) # Add the list to the results
    
    
    return results, ra, dec, object_name, tic_id, coord, sector_number
    

# def hr_diagram(coord, sector_number, object_name, tic_id, ra, dec):
#     # Check if the input is a coordinate
#     if coord:
#         # Download the TESS cutout using the coordinate
#         tess_cutout = Tesscut.download_cutouts(coordinates=coord, size=5)
#         # Query the metadata of the star using the coordinate
#         metadata = Catalogs.query_region(coord, radius=30 * u.arcmin,catalog="Tic")
#         star_name = f"{coord.ra.degree} {coord.dec.degree}"
#     # Check if the input is an object name
#     elif object_name:
#         # Download the TESS cutout using the object name
#         tess_cutout = Tesscut.download_cutouts(objectname=object_name, size=5)
#         # Query the metadata of the star using the object name
#         metadata = Catalogs.query_object(object_name, catalog="Tic")
#         star_name = object_name
#     # Check if the input is a TIC ID
#     elif tic_id:
#         # Download the TESS cutout using the TIC ID
#         tess_cutout = Tesscut.download_cutouts(objectname=tic_id, size=5)
#         # Query the metadata of the star using the TIC ID
#         metadata = Catalogs.query_object(tic_id, catalog="Tic")
#         star_name = "TIC " + tic_id
#     else:
#         # Return None if no input is provided
#         return None
#     # Retrieve the luminosity and temperature from the metadata
#     luminosity = metadata['lum'] * u.solLum
#     temperature = metadata['Teff'] * u.K

#     # Create a figure with the title HR Diagram for [star_name] (Sector [sector_number])
#     p = figure(title=f"HR Diagram for {star_name} (Sector {sector_number})")
#     # Add a scatter plot of temperature vs. luminosity to the figure
#     p.circle(temperature, luminosity.to(u.W))
#     # Label the x-axis as Temperature (K)
#     p.xaxis.axis_label = "Temperature (K)"
#     # Label the y-axis as Lumin
#     p.yaxis.axis_label = "Luminosity (solLum)"

#     #Set mode of resources to cdn for faster loading
#     resources = Resources(mode='cdn')
#     #Create HTML file from figure with specified title
#     html = file_html(p, resources=resources, title=f"HR Diagram for {star_name} (Sector {sector_number})")

#     return html 

def get_metadata(coord, object_name, tic_id):
    # Check if the input is a coordinate
    if coord:
        # Query the metadata of the star using the coordinate
        metadata = Catalogs.query_region(coord, radius=30 * u.arcmin, catalog="Tic")
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

    #Set mode of resources to cdn for faster loading
    resources = Resources(mode='cdn')
    #Create HTML file from figure with specified title
    html1 = file_html(p, resources=resources, title=f"HR Diagram for {star_name} (Sector {sector_number})")

    return html1
def generate_magnitude_histogram(star_name, magnitudes, sector_number):
    min_value = np.min(magnitudes)
    max_value = np.max(magnitudes)
    hist, edges = np.histogram(magnitudes, bins=200)
    
    #Define the data source for the histogram
    source = ColumnDataSource(data=dict(
        top=hist,
        bottom=np.zeros_like(hist),
        left=edges[:-1],
        right=edges[1:],
    ))


    #Create a Bokeh figure object and add the histogram to it
    p = figure(title=f"{star_name} Magnitude Histogram", x_axis_label='Magnitude', y_axis_label='Frequency')
    p.quad(top='top', bottom='bottom', left='left', right='right', source=source, line_color="#033649")


    p.xaxis.axis_label = "TESS Magnitude"
    p.yaxis.axis_label = "Density"
    
    # how the component should size itself
    p.sizing_mode = "scale_both"

    # Generate the HTML for the magnitude histogram
    resources = Resources(mode='cdn')
    html2 = file_html(p, resources=resources, title=f"Magnitude Histogram for {star_name} (Sector {sector_number})")

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
    p = figure(title="Distance Histogram", x_axis_label='Distance (parsecs)', y_axis_label='Frequency')
    p.quad(top='top', bottom='bottom', left='left', right='right', source=source, line_color="#033649")
    
    # how the component should size itself
    p.sizing_mode = "scale_both"

    #shows the histogram of distances with the x-axis showing the distance in parsecs and 
    #the y-axis showing the frequency of each distance.
    resources = Resources(mode='cdn')
    html3 = file_html(p, resources=resources, title=f"Magnitude Histogram for {star_name} (Sector {sector_num})")
    return html3


if __name__ == "__main__":
    app.run(debug=True)  



