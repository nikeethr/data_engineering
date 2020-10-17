import os
from osgeo import ogr

DIR = os.path.dirname(os.path.abspath(__file__))
SHP_PATH = os.path.join(DIR,
    'sample_data/ovens_example/VIC_SWIFT_Subarea_ovens.shp')

def print_srid():
    driver = ogr.GetDriverByName('ESRI Shapefile')
    shape = driver.Open(SHP_PATH)
    layer= shape.GetLayer()
    # the crs
    crs = layer.GetSpatialRef()
    print(crs)
    print(crs.GetAuthorityCode("GEOGCS"))

if __name__ == '__main__':
    print_srid()
