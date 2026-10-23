"""Build a traced, attributed 2D scenic package. Requires Pillow and Shapely.
OSM geometry is WGS84; the display rectangle is an editorial crop, not a legal boundary.
"""
import json,math,html
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from shapely.geometry import shape,box,Point
ROOT=Path(__file__).resolve().parent; SITE=ROOT.parents[1]; RAW=ROOT/'raw'; SID='sun-yat-sen'
E=json.loads((ROOT/'editorial.json').read_text()); PH=json.loads((RAW/'photos_final.json').read_text())
B=(113.52065,22.44405,113.52465,22.44705); LON0=(B[0]+B[2])/2;LAT0=(B[1]+B[3])/2
METERS_LON=111320*math.cos(math.radians(LAT0));METERS_LAT=110540;UNIT=10
W=1600;H=1320;crop=box(*B)
def loc(lon,lat):return [round((lon-LON0)*METERS_LON/UNIT,3),round((LAT0-lat)*METERS_LAT/UNIT,3)]
def norm(lon,lat):return [(lon-B[0])/(B[2]-B[0]),(B[3]-lat)/(B[3]-B[1])]
def pixel(lon,lat):
 x,y=norm(lon,lat);return (round(x*W),round(y*H))
def features(layer):
 p=RAW/f'osm_{layer}.geojson';return json.loads(p.read_text())['features'] if p.exists() else []
poi=features('poi');spots=[]
for item in E['spots']:
 matches=[f for f in poi if (f['properties'].get('name:zh') or f['properties'].get('name'))==item['osmName']]
 if len(matches)>1:matches.sort(key=lambda f:-f['geometry']['coordinates'][1])
 f=matches[0];lon,lat=f['geometry']['coordinates'];xy=norm(lon,lat);assert 0<xy[0]<1 and 0<xy[1]<1
 credit=dict(PH[item['id']]);credit['changes']='Wikimedia 提供的 1280px 宽缩略图；页面按容器显示或裁切。'
 spots.append(dict(id=item['id'],name=item['name'],description=item['description'],guide=item['guide'],notice=E['notice'],x=round(xy[0],5),y=round(xy[1],5),heading=0,scene=item['zone'],narration={'text':item['guide']},factSource=item['factSource'],coordinateSource='OpenStreetMap via OpenFreeMap 20261018, z14; tile feature '+str(f['id']),lnglat=[lon,lat],photos={'front':{'url':f'/assets/scenics/{SID}/spots/{item["id"]}/photos/photo-01.jpg','name':item['name']+' · 实拍','kind':'real','accepted':True,'credit':credit}}))
img=Image.new('RGB',(W,H),'#f1eee2');draw=ImageDraw.Draw(img)
clipped={}
for layer in ['landcover','landuse','park','water','transportation','building']:
 out=[]
 for f in features(layer):
  g=shape(f['geometry'])
  if not g.is_valid:g=g.buffer(0)
  if not g.intersects(crop):continue
  g=g.intersection(crop);out.append(dict(type='Feature',geometry=g.__geo_interface__,properties=f['properties'],id=f.get('id')))
  props=f['properties'];typ=props.get('class');gs=list(g.geoms) if hasattr(g,'geoms') else [g]
  for part in gs:
   if part.geom_type=='Polygon':
    fill={'landcover':'#dce4d0','park':'#d8e3ce','water':'#b9d5cf','building':'#d4cbb8'}.get(layer,'#ece8db')
    if layer=='landcover' and typ not in ['wood','grass','farmland']:fill='#e8e5d8'
    pts=[pixel(*p) for p in part.exterior.coords]
    draw.polygon(pts,fill=fill)
    if layer=='building':draw.line(pts,fill='#b1a58c',width=2)
    for ring in part.interiors:draw.polygon([pixel(*p) for p in ring.coords],fill='#f1eee2')
   elif part.geom_type=='LineString' and layer=='transportation':
    pts=[pixel(*p) for p in part.coords];width=14 if typ in ['primary','secondary','tertiary'] else 7 if typ in ['minor','service'] else 4
    draw.line(pts,fill='#c8bfa7',width=width+3,joint='curve');draw.line(pts,fill='#faf7ed',width=width,joint='curve')
 clipped[layer]={'type':'FeatureCollection','features':out}
 (RAW/f'clipped_{layer}.geojson').write_text(json.dumps(clipped[layer],ensure_ascii=False))
# Highlight each corresponding building footprint; no fabricated footprints or routing lines.
for s in spots:
 p=Point(s['lnglat'])
 for f in clipped['building']['features']:
  g=shape(f['geometry'])
  parts=list(g.geoms) if hasattr(g,'geoms') else [g]
  for part in parts:
   if part.geom_type=='Polygon' and part.buffer(.000015).contains(p):
    pts=[pixel(*q) for q in part.exterior.coords];draw.polygon(pts,fill='#c77d65' if s['id']=='sun-residence' else '#9cae95');draw.line(pts,fill='#766750',width=3)
fontpath='/System/Library/Fonts/STHeiti Medium.ttc'
F=lambda n:ImageFont.truetype(fontpath,n)
draw.rounded_rectangle((40,38,670,190),radius=16,fill='#fffdf5',outline='#d6ccb5',width=2)
draw.text((66,56),'翠亨寻迹',font=F(48),fill='#254b43');draw.text((68,122),'孙中山故居纪念馆 · 核心区导览',font=F(26),fill='#61736a')
# Labels match interactive markers and leave separation between adjacent points.
offsets={'sun-residence':(24,18),'memorial-museum':(-300,-40),'folk-houses':(20,-50),'yang-yin':(-180,18),'lu-haodong':(20,-55),'feng-ancestral-hall':(18,-45),'zhenyi-hall':(20,20),'warning-bell':(-140,-65),'conference-hall':(20,25)}
for i,s in enumerate(spots):
 x,y=pixel(*s['lnglat']);dx,dy=offsets[s['id']];label=f'{i+1:02d}  {s["name"]}';bounds=draw.textbbox((0,0),label,font=F(23));tw=bounds[2];th=32
 lx=max(15,min(W-tw-30,x+dx));ly=max(205,min(H-120,y+dy))
 draw.line([(x,y),(lx+10,ly+17)],fill='#8e8067',width=2)
 draw.rounded_rectangle((lx,ly,lx+tw+20,ly+42),radius=8,fill='#fffdf5',outline='#c8bfa7',width=1);draw.text((lx+10,ly+5),label,font=F(23),fill='#294b42')
 draw.ellipse((x-6,y-6,x+6,y+6),fill='#9e5844')
# Orientation and attribution remain readable in the downloadable map.
draw.polygon([(W-80,55),(W-95,100),(W-80,91),(W-65,100)],fill='#36574d');draw.text((W-91,106),'北',font=F(22),fill='#36574d')
scale=50/METERS_LON/(B[2]-B[0])*W;draw.line([(55,H-100),(55+scale,H-100)],fill='#36574d',width=5);draw.text((55,H-88),'50 m',font=F(20),fill='#36574d')
draw.rectangle((0,H-48,W,H),fill='#fffdf5');draw.text((30,H-39),'© OpenStreetMap contributors · ODbL 1.0｜点位与道路为导览示意，通行以现场为准',font=F(19),fill='#60695e')
img.save(ROOT/'map.png',optimize=True)
published={'title':E['title'],'intro':E['intro'],'map':{'url':f'/assets/scenics/{SID}/map-preview.png','name':'翠亨寻迹 · 核心区导览图','legend':'© OpenStreetMap contributors · ODbL 1.0；导览示意，通行以现场为准','custom':False},'spots':spots}
package_path=ROOT/'map-package.json'
if package_path.exists(): published['mapPackage']=json.loads(package_path.read_text())
(ROOT/'scenic.json').write_text(json.dumps({'schema':7,'id':SID,'draft':published,'published':published,'publishNumber':1,'publishedAt':None},ensure_ascii=False,indent=2))
bounds=dict(zip(['minX','minZ','maxX','maxZ'],[*loc(B[0],B[3]),*loc(B[2],B[1])]))
(ROOT/'geography.json').write_text(json.dumps({'schemaVersion':2,'id':SID,'name':E['title'],'frame':{'origin':[LON0,LAT0],'unitMeters':UNIT,'bounds':bounds,'axes':{'x':'east','z':'south'}},'boundsWgs84':B,'places':{s['id']:loc(*s['lnglat']) for s in spots},'provenance':{'attribution':'© OpenStreetMap contributors','license':'ODbL-1.0','source':'https://tiles.openfreemap.org/planet/20261018_080001_pt/14/13358/7143.pbf','retrieved':'2026-10-23','notes':['图幅为编辑选定的核心区，不表示景区法定边界。','未纳入影视城复制景点、农场、远处墓群与学校。','z14 矢量瓦片坐标存在数米量化误差。']}},ensure_ascii=False,indent=2))
(ROOT/'sources.json').write_text(json.dumps({'checkedAt':E['checkedAt'],'facts':{s['id']:s['factSource'] for s in spots},'photos':PH,'map':{'source':'OpenStreetMap via OpenFreeMap','license':'ODbL-1.0','url':'https://www.openstreetmap.org/copyright'},'service':E['serviceSource'],'review':['逐张查看照片内容，剔除分类内的植物、错配祖屋照片。','2D 坐标用 WGS84；高德 GCJ-02 只用于生成端搜索和范围选择。','杨殷故居存在两个相邻 OSM POI，取北侧建筑点并合并为一处。']},ensure_ascii=False,indent=2))
print('Built',len(spots),'spots',W,H)
