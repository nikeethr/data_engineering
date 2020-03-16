import os
import geopandas as gpd

_dir = os.path.dirname(os.path.realpath(__file__))
shp_path = os.path.join(_dir, 'ovens/VIC_SWIFT_Subarea_ovens.shp')
shp = gpd.read_file(shp_path)
import pdb; pdb.set_trace()

