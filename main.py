from routes import register_routes
from flask import Flask,  jsonify, request
import requests
from utils.sector_processing import get_ra_dec_from_tic_id


app = Flask(__name__)
register_routes(app)

@app.route('/tic/<int:tic_id>')
def get_tic_data(tic_id):
    url = f'https://exo.mast.stsci.edu/api/v0.1/exoplanets/tic/{tic_id}/properties/'
    response = requests.get(url)
    return jsonify(response.json())

@app.route('/lookup_tic', methods=['POST'])
def lookup_tic():
    try:
        tic_id = request.form['tic_id']
        print(f"Received TIC ID: {tic_id}")
        
        # Remove the 'TIC' prefix and any whitespace
        tic_id = tic_id.replace('TIC', '').replace('tic', '').strip()
        print(f"Processed TIC ID: {tic_id}")
        
        ra, dec = get_ra_dec_from_tic_id(tic_id)
        
        print(f"RA: {ra}, DEC: {dec}")
        
        return jsonify({'ra': ra, 'dec': dec})
    except Exception as e:
        print(f"Error in lookup_tic: {e}")
        return jsonify({'error': str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)

#token
# TPTwebapp | April 10, 2023 13:42:53
#  2279672527c4473796a55d03a466c6bb