from flask import Flask, render_template, request, redirect, url_for
from flask_wtf import FlaskForm
from wtforms import FileField, SubmitField, StringField, IntegerField
from werkzeug.utils import secure_filename
import os
from wtforms.validators import InputRequired, Optional
from astroplan import Observer,FixedTarget
from astropy.coordinates import SkyCoord
from astroquery.mast import Tesscut
from astropy import units as u


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
def sectors():
    search_input = request.form.get("search_input")
    radius = request.form.get("radius")

    coord = None
    ra = None
    dec = None
    object_name = None
    tic_id = None

    try:
        coord = SkyCoord(search_input, unit = "deg")
        ra = coord.ra.degree
        dec = coord.dec.degree
    except:
        if " " in search_input:
            try:
                ra, dec = search_input.split(" ")
                coord = SkyCoord(f"{ra} {dec}", unit = "deg")
            except:
                pass
        if not coord:
            if search_input.isdigit():
                tic_id = search_input
                object_name = "TIC " + tic_id
            else:
                object_name = search_input

    if coord:
        sectors = Tesscut.get_sectors(coordinates=coord, radius=float(radius)*u.deg)
    elif object_name:
        sectors = Tesscut.get_sectors(objectname=object_name, radius=float(radius)*u.deg)
    elif tic_id:
        sectors = Tesscut.get_sectors(objectname=tic_id, radius=float(radius)*u.deg)
    else:
        return "Error: Please provide either RA and Dec or Object Name or TIC ID."

    results = []
    for sector in sectors:
        sector_number = sector['sector']
        cycle = (sector_number - 1) // 13 + 1
        camera = sector['camera']
        result = [sector_number, cycle, camera]
        results.append(result)

    return render_template("index.html", results=results)




if __name__ == "__main__":
    app.run(debug=True)  


