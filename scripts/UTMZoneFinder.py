import utm
from pyproj import CRS, transform

class UTMZoneFinder():
    def __init__(self, coordinates:list, src_proj:str='4326'):
        """
        Class to return the correct EPSG UTM zone from a LatLong coordinate, from WGS84 EPSG:4326.
        """
        self.src_proj = int(src_proj)
        self.coordinates = coordinates
        if(src_proj != 4326):
            self.to_4326()

        self.south_zone_letters = ['C', 'D', 'E', 'F', 'G', 'H', 'J', 'K', 'L', 'M']
        self.north_zone_letters = ['N', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X']


    def to_4326(self):
        self.coordinates = transform(int(self.src_proj), 4326, self.coordinates[0], self.coordinates[1])
        self.src_proj = 4326


    def find_zone(self):
        utm_x, utm_y, utm_zone_number, utm_zone_letter = utm.from_latlon(self.coordinates[0], self.coordinates[1])
        dst_proj = CRS.from_dict({"proj":"utm", "zone":str(utm_zone_number), "south":(utm_zone_letter in self.south_zone_letters)}).to_authority()
        dst_proj = f"{dst_proj[0]}:{dst_proj[1]}"
        
        return ([utm_x, utm_y], dst_proj)


if __name__=='__main__':
    zoneFinder = UTMZoneFinder([-15.4, -54.3])
    zone = zoneFinder.find_zone()
    print(zone)