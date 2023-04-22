"""
This module defines the routes for the application.

It imports utility functions from various modules for CSV processing, input validation, and visualization.
It then registers the routes with the appropriate functions using the Flask app object.

Dependencies:
- utils.csv_processing: This module provides the csv_upload and download functions.
- utils.input_validation: This module provides the get_input, target_visualization_page, and target_list_page 
  functions and likely depends on Flask and other modules for handling HTTP requests.
- utils.visualization: This module provides the index function and likely depends on other modules for generating visualization output.
"""
# Import utility functions from different modules
from utils.csv_processing import csv_upload, download
from utils.input_validation import get_input, target_visualization_page, target_list_page
from utils.visualization import index

def register_routes(app):
    """
    Register routes for the application using the provided Flask app object.

    Args:
        app: A Flask app object.
    """
    # Register the index route
    app.route("/")(index)

    # Register the CSV upload route, accepts POST requests
    app.route('/csv_upload', methods=['POST'])(csv_upload)

    # Register the sectors route, accepts POST requests
    app.route('/sectors', methods=['POST'])(get_input)

    # Register the download route, accepts GET and POST requests
    app.route('/download', methods=['GET', 'POST'])(download)

    # Register the target visualization route, accepts GET and POST requests
    app.route("/target_visualization", methods=['GET', 'POST'])(target_visualization_page)

    # Register the target list route, accepts GET and POST requests
    app.route("/target_list", methods=['GET', 'POST'])(target_list_page)