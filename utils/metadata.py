from astropy import units as u
from astroquery.mast import Catalogs


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
