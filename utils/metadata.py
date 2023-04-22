"""
This module provides a function to query the TESS Input Catalog (TIC) for metadata associated with 
celestial objects, based on their coordinates, object names, or TIC IDs. It utilizes the astroquery 
library to interact with the TIC catalog.

Dependencies:
    - astropy
    - astroquery
"""
from astropy import units as u
from astroquery.mast import Catalogs


def get_metadata(coords=None, object_names=None, tic_ids=None):
    """Queries the TIC catalog for metadata associated with celestial objects.

    Args:
        coords (list, optional): A list of SkyCoord objects representing the celestial coordinates.
        object_names (list, optional): A list of object names.
        tic_ids (list, optional): A list of TESS Input Catalog (TIC) IDs.

    Returns:
        list: A list of tuples containing metadata for each celestial object: 
              (luminosity, temperature, star_name, magnitudes, distance).
    """
    metadata_list = []

    if coords:
        for coord in coords:
            metadata = Catalogs.query_region(coord, radius=1 * u.arcmin, catalog="Tic")
            star_name = f"{coord.ra.degree} {coord.dec.degree}"
            metadata_list.append((metadata, star_name))
    elif object_names:
        for object_name in object_names:
            metadata = Catalogs.query_object(object_name, catalog="Tic")
            metadata_list.append((metadata, object_name))
    elif tic_ids:
        for tic_id in tic_ids:
            metadata = Catalogs.query_object(tic_id, catalog="Tic")
            star_name = "TIC " + tic_id
            metadata_list.append((metadata, star_name))
    else:
        return None

    results = []

    # For each metadata entry and star name, it calculates the luminosity and temperature,
    # and extracts the magnitudes and distance from the metadata. The extracted values are then appended
    # as a tuple to the results list.
    for metadata, star_name in metadata_list:
        luminosity = metadata['lum'] * u.solLum
        temperature = metadata['Teff'] * u.K
        magnitudes = metadata['Tmag']
        distance = metadata['dstArcSec']

        # Append the extracted values as a tuple to the results list
        results.append((luminosity, temperature, star_name, magnitudes, distance))

    return results

