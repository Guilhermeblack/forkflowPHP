from scripts.UTMZoneFinder import UTMZoneFinder
from osgeo import ogr 

def get_utm(shape_df, src_crs:str='4326'):
    
    point_sample = shape_df.geometry[0].centroid.coords[0]

    zoneFinder = UTMZoneFinder([point_sample[1], point_sample[0]], src_proj=src_crs)
    utm_epsg = zoneFinder.find_zone()[1]

    return utm_epsg

def get_correct_crs(filepath)->str:
    
    """ Get correct CRS from shapefile 

    Args:
        shape_df (str): shapefile filepath 

    Returns:
        str: CRS of shapefile
    """
    src_file = ogr.Open(filepath)
    crs = src_file.GetLayer().GetSpatialRef().GetAttrValue("AUTHORITY",1)

    return crs
