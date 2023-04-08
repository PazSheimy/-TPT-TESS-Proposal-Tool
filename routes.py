from utils.csv_processing import csv_upload, download
from utils.input_validation import get_input
from utils.visualization import index

def register_routes(app):
    app.route("/")(index)
    app.route('/csv_upload', methods=['POST'])(csv_upload)
    app.route('/sectors', methods=['POST'])(get_input)
    app.route('/download', methods=['GET', 'POST'])(download)
