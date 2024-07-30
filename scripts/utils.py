from scripts.UTMZoneFinder import UTMZoneFinder
from osgeo import ogr 
import shapely

def get_utm(shape_df, src_crs:str='4326'):
    
    point_sample = shape_df.geometry[0].centroid.coords[0]

    zoneFinder = UTMZoneFinder([point_sample[1], point_sample[0]], src_proj=src_crs)
    utm_epsg = zoneFinder.find_zone()[1]
    utm_epsg = int(utm_epsg.split(':')[-1])

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

def convert_3D_2D(geometry:shapely.geometry)->list:
    """

    Takes a 3D Multi/Polygons geometry (has_z) and returns a list of 2D Multi/Polygons

    Args:
        geometry (Union[Polygon, MultiPolygon]): shapely geometry to be converted to 2D

    Returns:
        list: list with converted 2D geometries
    """
    geometries_2d = []
    printed = False 
    for p in geometry:
        if p. has_z:
            if not printed: print("Polygon has z-component. Converting to planar....")
            printed = True
            geometries_2d.append(shapely.ops.transform(lambda x, y, z=None: (x, y), p))
        else:
            geometries_2d.append(p)
    return geometries_2d