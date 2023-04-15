from utils.csv_processing import csv_upload, download
from utils.input_validation import get_input, target_visualization_page, target_list_page
from utils.visualization import index

def register_routes(app):
    app.route("/")(index)
    app.route('/csv_upload', methods=['POST'])(csv_upload)
    app.route('/sectors', methods=['POST'])(get_input)
    app.route('/download', methods=['GET', 'POST'])(download)
    app.route("/target_visualization", methods=['GET', 'POST'])(target_visualization_page)
    app.route("/target_list", methods=['GET', 'POST'])(target_list_page)