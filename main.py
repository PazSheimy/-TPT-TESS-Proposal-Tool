"""
This module sets up and runs the Flask application.

It imports the register_routes function, initializes a Flask app object, and registers the routes.
The module also includes additional routes for TIC data lookup and TIC ID processing.

Dependencies:
- flask
- routes
- requests
- jsonify
- utils.sector_processingA custom module containing functions to process data related to celestial targets, 
such as converting TIC IDs to RA and DEC coordinates, and processing CSV files containing target information.
"""
from routes import register_routes
from flask import Flask, jsonify, request
import requests
from utils.sector_processing import get_ra_dec_from_tic_id, get_targets_from_uploaded_csv
from flask import send_from_directory

# Create a Flask app instance and register routes
app = Flask(__name__)
register_routes(app)

@app.route('/tic/<int:tic_id>')
def get_tic_data(tic_id):

    """
    Retrieve TIC data from the MAST API for the given TIC ID.

    Args:
        tic_id (int): TIC ID for which to fetch data.

    Returns:
        A JSON object with the TIC data.
    """

    url = f'https://exo.mast.stsci.edu/api/v0.1/exoplanets/tic/{tic_id}/properties/'
    response = requests.get(url)
    return jsonify(response.json())

@app.route('/lookup_tic', methods=['POST'])
def lookup_tic():
    """
    Process a TIC ID received from a form and return the corresponding RA and DEC coordinates.

    The TIC ID is expected to be provided as a form field with the name 'tic_id'.

    Returns:
        A JSON object with the RA and DEC coordinates, or an error message and status code 500 if an exception occurs.
    """
    try:
        # Get the TIC ID from the form data
        tic_id = request.form['tic_id']
        print(f"Received TIC ID: {tic_id}")
        
        # Remove the 'TIC' prefix and any whitespace from the TIC ID
        tic_id = tic_id.replace('TIC', '').replace('tic', '').strip()
        print(f"Processed TIC ID: {tic_id}")
        
        # Get the RA and DEC coordinates for the given TIC ID
        ra, dec = get_ra_dec_from_tic_id(tic_id)

        # Print the RA and DEC coordinates
        print(f"RA: {ra}, DEC: {dec}")
        
        # Return the RA and DEC coordinates as a JSON response
        return jsonify({'ra': ra, 'dec': dec})
    
    # If any exception occurs during the process, handle it and return an error message
    except Exception as e:
        print(f"Error in lookup_tic: {e}")
        # Return the error message as a JSON response with a 500 status code
        return jsonify({'error': str(e)}), 500




@app.route('/files_csv/<path:filename>')
def serve_csv(filename):
    return send_from_directory('files_csv', filename)
    


if __name__ == "__main__":

    # Run the Flask app in debug mode
    app.run(debug=True)

