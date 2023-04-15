from io import StringIO
import csv
from flask import request, render_template, url_for, make_response, jsonify
from .sector_processing import process_csv, get_targets_from_uploaded_csv


def csv_upload():
    # Check if the request is for the sky map
    if 'csv_file' in request.files and 'radius' not in request.form:
        uploaded_csv_file = request.files['csv_file']
        targets = get_targets_from_uploaded_csv(uploaded_csv_file)
        return jsonify(targets)

    # Check if the request is for the query table
    elif 'csv_file' in request.files and 'radius' in request.form:
        # Get the value of the radius parameter from the request form
        radius = request.form.get('radius')

        # Get the uploaded CSV file from the request files
        csv_file = request.files.get('csv_file')
        
        # Check if a radius value was provided
        if not radius:
            # If not, return an error message to the index.html template
            return render_template('target_visualization.html', error='Radius value is required')

        # Attempt to convert the radius to a float value
        try:
            radius_float = float(radius)
            
        except ValueError:
            
            # If the conversion fails, return an error message to the index.html template
            return render_template('target_visualization.html', error='Invalid radius value')

        # Check if a CSV file was provided
        if not csv_file:
            # If not, return an error message to the index.html template
            return render_template('target_visualization.html', error='CSV file is required')

        try:
            # Read the contents of the CSV file into a StringIO object and decode it as UTF-8
            csv_contents = StringIO(csv_file.read().decode('utf-8'))

            # Call the process_csv function with the CSV contents and the provided radius
            results = process_csv(csv_contents, radius_float)

        except Exception as e:
            # If there is an error processing the CSV file, return an error message to the index.html template
            return render_template('target_visualization.html', error=f'Error processing CSV file: {str(e)}')

        download_url = url_for('download', results=results)
        return render_template('target_visualization.html', results=results, download_url=download_url, enumerate=enumerate, csv_file=csv_file)

    # Return an error if no file was provided
    else:
        return jsonify({"error": "No file provided"}), 400


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
