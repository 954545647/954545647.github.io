"""Draw a north-up vector visitor map from a studio map package, preserving its coordinate frame.
Usage: python3 tools/render_scenic_map.py <scenic-or-map-package.json> <output.svg> [source-geography.json]
"""
import html
import json
import math
import random
import sys
from pathlib import Path

src = json.loads(Path(sys.argv[1]).read_text())
pkg = src.get('published') or src.get('draft') or src
pkg = pkg.get('mapPackage', pkg)
g = pkg['geography']
b = g['frame']['bounds']
width = 1300
scale = width / (b['maxX'] - b['minX'])
height = round((b['maxZ'] - b['minZ']) * scale)

def xy(p):
    return ((p[0]-b['minX'])*scale, (p[1]-b['minZ'])*scale)
def points(ps):
    return ' '.join(f'{x:.2f},{y:.2f}' for x,y in map(xy,ps))
def path(ps):
    return 'M'+'L'.join(f'{x:.2f},{y:.2f}' for x,y in map(xy,ps))+'Z'
def inside(p, ring):
    x,y=p; odd=False
    for a,c in zip(ring, ring[1:]+ring[:1]):
        if (a[1]>y)!=(c[1]>y) and x<(c[0]-a[0])*(y-a[1])/(c[1]-a[1])+a[0]: odd=not odd
    return odd

outline=g['scenic']['outline']; waters=g['water']
source_geo=json.loads(Path(sys.argv[3]).read_text()) if len(sys.argv)>3 else None
def source_point(p):
    f=source_geo['frame'];o=f['origin'];unit=f['unitMeters']
    lon=o[0]+p[0]*unit/(111320*math.cos(math.radians(o[1])))
    lat=o[1]-p[1]*unit/110540
    frame=g['frame'];origin=frame['origin'];projection=frame['projection']
    return [(lon-origin[0])*projection['lonUnits'],(origin[1]-lat)*projection['latUnits']]
if source_geo:
    waters=[[source_point(p) for p in ring] for water in source_geo['water'] for ring in [water['outer'],*water['holes']]]
s=[f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<defs><pattern id="paper" width="8" height="8" patternUnits="userSpaceOnUse"><rect width="8" height="8" fill="#f4eddb"/><circle cx="2" cy="3" r=".55" fill="#d4c8ab" opacity=".18"/></pattern>
<linearGradient id="water" x2=".7" y2="1"><stop stop-color="#a8cbd0"/><stop offset="1" stop-color="#78abae"/></linearGradient>
<radialGradient id="hill"><stop stop-color="#6f8d65" stop-opacity=".72"/><stop offset="1" stop-color="#b4c496" stop-opacity="0"/></radialGradient>
<clipPath id="park"><path d="{path(outline)}"/></clipPath>
<pattern id="ripples" width="50" height="28" patternUnits="userSpaceOnUse"><path d="M5 14q10 -3 20 0m5 0h10" fill="none" stroke="#edf3e9" stroke-width="1" opacity=".25"/></pattern>
</defs><rect width="100%" height="100%" fill="url(#paper)"/>
<path d="{path(outline)}" fill="#ccd4ae" stroke="#879a77" stroke-width="2"/>
<g clip-path="url(#park)">''']
hx,hy=xy([-1,0.2]);s.append(f'<ellipse cx="{hx}" cy="{hy}" rx="310" ry="150" fill="url(#hill)"/>')
d=''.join(path(ring) for ring in waters)
s.append(f'<path d="{d}" fill="url(#water)" fill-rule="evenodd" stroke="#5f9294" stroke-width="1.5"/><path d="{d}" fill="url(#ripples)" fill-rule="evenodd"/>')
rng=random.Random(20261023)
for _ in range(2300):
    p=[rng.uniform(b['minX'],b['maxX']),rng.uniform(b['minZ'],b['maxZ'])]
    if not inside(p,outline) or sum(inside(p,w) for w in waters) % 2:continue
    x,y=xy(p);r=rng.uniform(2,6);color=rng.choice(['#709267','#8da272','#9ba979','#5c8263'])
    s.append(f'<ellipse cx="{x+1:.2f}" cy="{y+2:.2f}" rx="{r:.2f}" ry="{r*.65:.2f}" fill="#526b50" opacity=".13"/><circle cx="{x:.2f}" cy="{y:.2f}" r="{r:.2f}" fill="{color}" opacity=".64"/>')
nodes=g['network']['nodes']
roads=[]
if source_geo:
    # Use source geometry rather than AI routing edges, which may be shortcuts.
    roads=[[source_point(p) for p in road['points']] for road in source_geo['paths']]
else:
    roads=[[nodes[e['a']],nodes[e['b']]] for e in g['network']['edges'] if e.get('mode')=='walk']
for color,stroke in [('#a69d81',4),('#f0e5c7',2.3)]:
    for road in roads:
        s.append(f'<polyline points="{points(road)}" fill="none" stroke="{color}" stroke-width="{stroke}" stroke-linecap="round"/>')
causeways=[{'points':[source_point(p) for p in c['points']]} for c in source_geo['causeways']] if source_geo else g.get('causeways',[])
for c in causeways:
    s.append(f'<polyline points="{points(c["points"])}" fill="none" stroke="#d3bf99" stroke-width="6" stroke-linejoin="round"/><polyline points="{points(c["points"])}" fill="none" stroke="#f5e8cc" stroke-width="3"/>')
# Small architectural symbols are illustration, not building footprints.
for sid,spot in g['spots'].items():
    x,y=xy(nodes[spot['node']]);factor=1.5 if sid=='foxiangge' else 1
    if sid in ['west-causeway','seventeen-arch-bridge','jade-belt-bridge']:
        shape='<path d="M-20 3 Q0 -18 20 3L20 8Q0 -9 -20 8Z" fill="#f1e8d4" stroke="#9f9174" stroke-width="1.5"/>'
    elif sid=='marble-boat':
        shape='<path d="M-23 5H23L17 13H-18Z" fill="#e9e4d6" stroke="#928f7d"/><rect x="-15" y="-8" width="30" height="14" fill="#f6f0e0" stroke="#928f7d"/><path d="M-20 -8H20L14 -14H-13Z" fill="#848f81"/>'
    else:
        shape='<rect x="-12" y="-2" width="24" height="15" fill="#a85d48"/><path d="M-21 0L-13 -6L-4 -11H4L13 -6L21 0Z" fill="#b59956" stroke="#837249" stroke-width="1"/><path d="M-10 3V12M0 3V12M10 3V12" stroke="#e5c58c" stroke-width="2"/>'
        if sid=='foxiangge':shape+='<rect x="-8" y="-15" width="16" height="10" fill="#a85d48"/><path d="M-15 -14L-5 -22H5L15 -14Z" fill="#b59956" stroke="#837249"/>'
    s.append(f'<g transform="translate({x:.2f},{y:.2f}) scale({factor})">{shape}</g>')
s.append('</g>')
for name,p,size in [('昆 明 湖',[-.7,6.2],38),('万寿山',[-1,-.7],25),('后 湖',[-2,-1.7],20),('南湖岛',[.4,10.1],22)]:
    x,y=xy(p);s.append(f'<text x="{x}" y="{y}" text-anchor="middle" font-family="Songti SC, serif" font-size="{size}" letter-spacing="4" fill="#38686a" opacity=".84">{html.escape(name)}</text>')
s.append(f'''<g transform="translate(70,{height-260})"><text y="0" font-family="Songti SC, serif" font-size="64" fill="#294f44" letter-spacing="12">颐和园</text><text y="44" font-family="serif" font-size="20" letter-spacing="4" fill="#7a8a72">SUMMER PALACE</text><path d="M0 72H270" stroke="#b2a484"/><text y="111" font-family="Songti SC, serif" font-size="24" fill="#78866a">湖山之间 · 御苑漫游</text></g>
<g transform="translate(80,90)" stroke="#607b67" fill="none"><path d="M0 35V-20M-8 -7L0 -23L8 -7" stroke-width="2"/><text x="0" y="-36" text-anchor="middle" stroke="none" fill="#607b67" font-family="serif" font-size="21">N</text></g>
<text x="70" y="{height-45}" font-family="sans-serif" font-size="16" fill="#7d8b78">© OpenStreetMap contributors · 园林插画示意，建筑符号不代表实测轮廓</text>
</svg>''')
Path(sys.argv[2]).write_text('\n'.join(s),encoding='utf-8')
print(f'{width} x {height}; {len(g["spots"])} points; frame preserved')
