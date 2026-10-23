"""Decode the checked OpenFreeMap z14 tiles to WGS84 GeoJSON; requires mapbox-vector-tile."""
from pathlib import Path
import math,json,mapbox_vector_tile
root=Path(__file__).resolve().parent/'raw';layers={}
for p in sorted(root.glob('14-*-*.pbf')):
 z,tx,ty=map(int,p.stem.split('-'))
 def transform(x,y):return ((tx+x/4096)/2**z*360-180,math.degrees(math.atan(math.sinh(math.pi*(1-2*(ty+y/4096)/2**z)))))
 tile=mapbox_vector_tile.decode(p.read_bytes(),default_options={'y_coord_down':True,'transformer':transform})
 for name,layer in tile.items():
  assert layer['extent']==4096
  layers.setdefault(name,[]).extend(layer['features'])
for name,features in layers.items():
 (root/f'osm_{name}.geojson').write_text(json.dumps({'type':'FeatureCollection','features':features},ensure_ascii=False))
print({k:len(v) for k,v in layers.items()})
