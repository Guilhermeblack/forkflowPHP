import fiona 
import geopandas as gpd 
import logging 
from scripts.utils import get_correct_crs


def file_reader(format, filepath, utm_crs:str=""):
    formats_getter = {'.kml':kml_reader,
                      '.geojson':shape_reader,
                      '.shp':shape_reader}
    
    return formats_getter[format](filepath, utm_crs)


def kml_reader(filepath, utm_crs):

    # read kml format and convert to utm_crs, if defined

    fiona.drvsupport.supported_drivers['KML'] = 'rw'
    df = gpd.read_file(filepath, driver='kml')
    if df.crs:
        crs = get_correct_crs(filepath)
        if not crs is None: #if None, crs is in SIRGAS
            logging.debug(f"Setting GeoDataFrame to CRS {crs}")
            df.crs = int(crs)
    else:
        logging.debug(f"GeoDataFrame does not have CRS. Setting to 4326")
        df.crs = 4326

    if utm_crs:
        logging.debug(f"Converting to {utm_crs}")
        df.to_crs(utm_crs, inplace=True)

    return df 

def shape_reader(shape_path, utm_crs):

    # read shapefile and convert to utm_crs, if defined

    df = gpd.read_file(shape_path)
    logging.debug("Getting correct CRS")
    if df.crs:
        crs = get_correct_crs(shape_path)
        if not crs is None: #if None, crs is in SIRGAS
            logging.debug(f"Setting GeoDataFrame to CRS {crs}")
            df.crs = int(crs)
    else:
        logging.debug(f"GeoDataFrame does not have CRS. Setting to 4326")
        df.crs = 4326
    if utm_crs:
        logging.debug(f"Converting to {utm_crs}")
        df.to_crs(utm_crs, inplace=True)
        logging.debug(f"Converted to {utm_crs}")

    return df 