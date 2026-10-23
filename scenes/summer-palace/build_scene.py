"""Build a draft 景见-style scene package for the Summer Palace from raw OSM/Wikidata/Commons data.

Inputs (raw/): boundary.geojson (Wikimedia geoshape of Q4132), osm_*.geojson (OpenFreeMap tiles,
decoded), photos_final.json (Commons metadata). Outputs: geography.json, scenic.json, sources.json,
preview-map.png. Coordinates follow the site's convention: x = east, z = south, 1 unit = UNIT_M metres.
"""
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from shapely.geometry import Point, shape
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parent
if (ROOT / "studio-map-package.json").exists():
    raise SystemExit("此景区已同步生成端三维地图。请使用 tools/sync_studio_scene.py，避免初始 OSM 草稿覆盖已发布数据。")
RAW = ROOT / "raw"
SCENE_ID = "summer-palace"
UNIT_M = 50
RETRIEVED = "2026-10-23"
OSM_ATTRIBUTION = "© OpenStreetMap contributors, ODbL 1.0"

park = shape(json.load(open(RAW / "boundary.geojson"))["features"][0]["geometry"])
minlon, minlat, maxlon, maxlat = park.bounds
LON0, LAT0 = round((minlon + maxlon) / 2, 5), round((minlat + maxlat) / 2, 5)
M_PER_LON = 111320 * math.cos(math.radians(LAT0))
M_PER_LAT = 110540


def local(lon, lat):
    return [round((lon - LON0) * M_PER_LON / UNIT_M, 2), round(-(lat - LAT0) * M_PER_LAT / UNIT_M, 2)]


# (id, name, zone, lon, lat, coordinate source, description, guide)
SPOTS = [
    ("beigongmen", "北宫门", "后山后湖", 116.2713683, 40.0011926, "OSM 北宫门站（近似，取地铁站点位）",
     "颐和园北侧入口，可从地铁北宫门站步行前往，入园后可先游后湖与苏州街。",
     "北宫门是颐和园北侧的入园入口，可由地铁4号线北宫门站前往。从这一侧入园，可以先游览后湖与苏州街，再按体力选择登山或沿湖路线。"),
    ("suzhou-street", "苏州街", "后山后湖", 116.2685788, 40.0006584, "OSM POI",
     "沿后湖两岸展开的仿江南水乡买卖街，小桥、铺面与河道相互穿插。",
     "苏州街在乾隆年间模仿江南水乡建造，原来供帝后体验逛市。1860年遭焚毁，现有水街于1990年在遗址上复建。沿后湖两岸的铺面和小桥，可以感受江南街市的空间布局。"),
    ("xiequyuan", "谐趣园", "后山东麓", 116.2758315, 39.9991338, "OSM POI",
     "万寿山东麓的园中之园，仿无锡寄畅园布局，池水居中、廊亭环绕。",
     "谐趣园最初名为惠山园，1751年参照无锡寄畅园营建，1811年重修时改为今名。池塘周围的亭、榭、楼与游廊，组成一座可以慢慢欣赏的园中园。"),
    ("deheyuan", "德和园", "东宫区", 116.2738091, 39.9970297, "OSM POI",
     "园内的大戏楼院落，上下三层的戏台是清宫规模最大的戏台之一。",
     "德和园从1891年开始兴建，是慈禧太后在园内看戏的地方。园中以三层大戏楼最为醒目，还有颐乐殿和庆善堂，可以结合院落布局了解清宫观戏的场景。"),
    ("zhichunting", "知春亭", "东岸", 116.2733692, 39.9954064, "OSM POI",
     "昆明湖东岸的小岛亭，经石桥与岸相连，是眺望万寿山的经典机位。",
     "知春亭在昆明湖东岸、玉澜堂前的小岛上。这里背山朝阳，春意来得较早，亭名由此而来。从亭边眺望，可以把万寿山、昆明湖与远处西山的借景联系起来欣赏。"),
    ("wenchangge", "文昌阁", "东岸", 116.2739486, 39.9952215, "OSM POI",
     "东堤北端的城关式楼阁，下为城台、上为两层楼阁。",
     "文昌阁与园西的宿云檐遥相呼应，一东一西寄寓文治与武功。游览时可以留意城关式建筑的轮廓，再沿东堤欣赏湖景。"),
    ("long-corridor", "长廊", "前山", 116.270051, 39.997020, "OSM 步道中点",
     "沿昆明湖北岸延伸的彩画长廊，全长七百多米，串起前山各组建筑。",
     "长廊连接邀月门与石丈亭，全长728米，分为273间。梁枋上的彩画超过一万四千幅，能看到人物故事、山水和花鸟。沿廊慢行，可以同时欣赏彩画与昆明湖景色。"),
    ("paiyundian", "排云殿", "前山中轴", 116.2680477, 39.9971859, "OSM POI",
     "前山中轴上的主体殿宇，自湖边牌楼起层层抬高，直通佛香阁。",
     "排云殿在1886年建于原大报恩延寿寺大雄宝殿的遗址上，是为慈禧太后祝寿的场所。它位于万寿山前山中轴，是理解佛香阁与湖岸建筑关系的重要一站。"),
    ("foxiangge", "佛香阁", "前山中轴", 116.267935, 39.9980571, "OSM POI",
     "建在万寿山前山高台上的八角楼阁，是整座园林的视觉中心。",
     "佛香阁立在20米高的石台上，阁身通高36.44米，采用八面、三层、四重檐的结构。它是颐和园的视觉中心，从湖岸远望，最容易看出楼阁与万寿山的层次。"),
    ("marble-boat", "清晏舫", "前山西端", 116.2636811, 39.9967379, "OSM POI",
     "长廊西端湖边的石舫，船身以巨石砌成，上部为两层船楼。",
     "清晏舫原称石舫，1755年建成，石质船身长36米。原来的中式舱楼毁于1860年，1893年重建时改用西式装饰，并以河清海晏之意命名。可以留意船身与上层建筑的材质差别。"),
    ("west-causeway", "西堤", "湖西", 116.264626, 39.988927, "OSM 步道中点",
     "纵贯昆明湖西部的长堤，仿杭州苏堤修建，沿途有六座桥。",
     "西堤的布局借鉴杭州西湖苏堤，从北到南有界湖桥、豳风桥、玉带桥、镜桥、练桥和柳桥。一路行走，可以比较六桥的不同造型，欣赏桃柳与湖水相映的景色。"),
    ("jade-belt-bridge", "玉带桥", "西堤", 116.261074, 39.992127, "OSM 步道中点",
     "西堤上的高拱石桥，桥拱高耸，桥身洁白如带。",
     "玉带桥是昆明湖西堤六桥之一，位于豳风桥与镜桥之间。游览时可以从桥侧观察高高拱起的桥身，再从岸边欣赏它与湖水、堤柳的组合。"),
    ("seventeen-arch-bridge", "十七孔桥", "南湖岛", 116.271467, 39.989490, "OSM 步道中点",
     "连接东堤与南湖岛的长桥，有十七个桥洞，是昆明湖上最大的石桥。",
     "十七孔桥建于1750年，连接东堤与南湖岛，全长150多米。桥名来自十七个桥洞，桥头和望柱上还有五百多只石狮。过桥时可以留意不同石狮的姿态。"),
    ("bronze-ox", "铜牛", "东堤", 116.2734175, 39.9894143, "OSM POI",
     "东堤上卧在石座上的铜牛，面朝昆明湖，寓意镇水。",
     "这尊铜牛铸于1755年，也称金牛，卧在雕花石座上。牛背的《金牛铭》由乾隆撰写，与传统的镇水寓意相联系。它与附近的十七孔桥可以一起游览。"),
]
NOTICE = "开放时间、预约方式与园中园门票以颐和园官方当日信息为准。"
OFFICIAL = "https://summerpalace.net.cn/home.html"
EDITORIAL = json.loads((ROOT / "editorial.json").read_text(encoding="utf-8"))

# --- geography -------------------------------------------------------------------------------
corners = [local(minlon, maxlat), local(maxlon, minlat)]
pad = 1.5
bounds = {"minX": math.floor(corners[0][0] - pad), "maxX": math.ceil(corners[1][0] + pad),
          "minZ": math.floor(corners[0][1] - pad), "maxZ": math.ceil(corners[1][1] + pad)}


def ring_local(coords):
    return [local(lon, lat) for lon, lat in coords]


water = []
water_fc = json.load(open(RAW / "osm_water.geojson"))
lakes = unary_union([shape(f["geometry"]).buffer(0) for f in water_fc["features"]])
lakes = lakes.intersection(park.buffer(0.0005))
for poly in getattr(lakes, "geoms", [lakes]):
    if poly.geom_type != "Polygon" or poly.area * M_PER_LON * M_PER_LAT < 2000:
        continue
    simple = poly.simplify(0.00004, preserve_topology=True)
    water.append({"outer": ring_local(simple.exterior.coords),
                  "holes": [ring_local(h.coords) for h in simple.interiors],
                  "areaM2": round(poly.area * M_PER_LON * M_PER_LAT)})
water.sort(key=lambda w: -w["areaM2"])

paths, causeways = [], []
for f in json.load(open(RAW / "osm_transportation.geojson"))["features"]:
    p = f["properties"]
    if p.get("class") not in ("path", "track", "service", "minor"):
        continue
    g = shape(f["geometry"]).intersection(park.buffer(0.0002))
    for line in getattr(g, "geoms", [g]):
        if line.geom_type != "LineString" or line.length * M_PER_LON < 15:
            continue
        pts = ring_local(line.simplify(0.00003).coords)
        paths.append({"class": p.get("subclass") or p.get("class"), "points": pts})
for f in json.load(open(RAW / "osm_transportation_name.geojson"))["features"]:
    name = f["properties"].get("name:zh") or f["properties"].get("name")
    if name in ("西堤", "东堤"):
        for line in getattr(shape(f["geometry"]), "geoms", [shape(f["geometry"])]):
            causeways.append({"id": "west" if name == "西堤" else "east", "name": name, "width": 0.3,
                              "points": ring_local(line.simplify(0.00003).coords)})

geography = {
    "schemaVersion": 2,
    "id": SCENE_ID,
    "name": "颐和园",
    "draft": True,
    "frame": {"origin": [LON0, LAT0], "unitMeters": UNIT_M, "bounds": bounds,
              "source": OSM_ATTRIBUTION, "axes": {"x": "east", "z": "south"}},
    "provenance": {
        "attribution": f"{OSM_ATTRIBUTION}；园区边界来自 Wikimedia Maps geoshape (Wikidata Q4132)",
        "url": "https://www.openstreetmap.org/",
        "fetched": RETRIEVED,
        "notes": ["矢量数据取自 OpenFreeMap 2026-10-18 OSM 瓦片（z14），已简化到约 3–5 米精度。",
                  "万寿山地形为艺术化估计，不是测绘高程。"],
    },
    "places": {sid: local(lon, lat) for sid, _, _, lon, lat, *_ in SPOTS},
    "water": water,
    "causeways": causeways,
    "paths": paths,
    "terrain": {"cell": 0.1, "hills": [
        {"at": local(116.2650, 39.9988), "radius": 4.0, "height": 2.6, "name": "万寿山西段"},
        {"at": local(116.2692, 39.9985), "radius": 4.5, "height": 3.2, "name": "万寿山主峰"},
        {"at": local(116.2735, 39.9987), "radius": 4.0, "height": 2.4, "name": "万寿山东段"},
    ]},
}


# --- scenic (spots, photos) --------------------------------------------------------------------
photos = json.load(open(RAW / "photos_final.json"))


def norm_xy(lon, lat):
    x, z = local(lon, lat)
    return (round((x - bounds["minX"]) / (bounds["maxX"] - bounds["minX"]), 4),
            round((z - bounds["minZ"]) / (bounds["maxZ"] - bounds["minZ"]), 4))


spots = []
for sid, name, zone, lon, lat, coord_src, desc, guide in SPOTS:
    reviewed = EDITORIAL["spots"][sid]
    guide = reviewed["guide"]
    ph = photos[sid]
    x, y = norm_xy(lon, lat)
    spots.append({
        "id": sid, "name": name, "description": desc, "guide": guide, "notice": NOTICE,
        "x": x, "y": y, "heading": 0, "scene": zone, "narration": {"text": guide},
        "factSource": reviewed["factSource"], "coordinateSource": coord_src, "lnglat": [lon, lat],
        "photos": {"front": {
            "url": f"/assets/scenics/{SCENE_ID}/spots/{sid}/photos/photo-01.jpg",
            "name": f"{name} · 实拍", "kind": "real", "accepted": False,
            "credit": {"title": ph["title"], "source": ph["page"], "url": ph["thumb"],
                       "license": ph["license"], "licenseUrl": ph["licenseUrl"], "artist": ph["artist"],
                       "date": ph["date"], "retrieved": RETRIEVED, "localFile": ph["file"]},
        }},
    })

scenic = {
    "schema": 7, "id": SCENE_ID, "publishNumber": 0, "publishedAt": None, "draft": True,
    "published": {
        "title": "颐和园 · 湖山之间",
        "intro": "万寿山与昆明湖相映，从长廊、佛香阁到十七孔桥，在皇家园林里慢慢走一圈。",
        "map": {"url": f"/assets/scenics/{SCENE_ID}/map-preview.png", "name": "颐和园 · OSM 数据预览底图",
                "legend": "依据 OpenStreetMap 数据生成，仅供打点校对，正式版需替换为艺术绘卷",
                "custom": False},
        "spots": spots,
    },
}

sources = {
    "scene": SCENE_ID, "retrieved": RETRIEVED,
    "editorial": EDITORIAL,
    "datasets": [
        {"what": "园区边界", "source": "Wikimedia Maps geoshape, Wikidata Q4132",
         "url": "https://maps.wikimedia.org/geoshape?getgeojson=1&ids=Q4132", "license": "ODbL 1.0 (OSM)"},
        {"what": "水面、步道、东西堤、景点 POI", "source": "OpenFreeMap OSM 矢量瓦片 20261018, z14",
         "url": "https://tiles.openfreemap.org/planet", "license": "ODbL 1.0 (OSM)，需署名 © OpenStreetMap contributors"},
        {"what": "景点清单与交叉校验坐标", "source": "Wikidata SPARQL（P361 部分 / 1.8km 范围）",
         "url": "https://query.wikidata.org/", "license": "CC0"},
        {"what": "实拍照片", "source": "Wikimedia Commons（逐张许可见 scenic.json credit）",
         "url": "https://commons.wikimedia.org/", "license": "CC0 / CC BY / CC BY-SA / 公有领域"},
        {"what": "开放与票务信息", "source": "颐和园官网", "url": OFFICIAL, "license": "仅作事实来源链接，不搬运文字"},
    ],
    "coordinateIssues": [
        "Wikidata 中 德和园(Q35136521)、东宫门(Q10870031)、玉澜堂(Q15911169) 的坐标落在园区边界外约 580 米，已改用 OSM。",
        "东宫门、仁寿殿、玉澜堂、乐寿堂在 OSM 瓦片里没有可用点位，未纳入本草稿。",
    ],
}

for name, obj in (("geography.json", geography), ("scenic.json", scenic), ("sources.json", sources)):
    (ROOT / name).write_text(json.dumps(obj, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

# --- preview map ---------------------------------------------------------------------------------
W = 1600
H = round(W * (bounds["maxZ"] - bounds["minZ"]) / (bounds["maxX"] - bounds["minX"]))


def px(pt):
    return ((pt[0] - bounds["minX"]) / (bounds["maxX"] - bounds["minX"]) * W,
            (pt[1] - bounds["minZ"]) / (bounds["maxZ"] - bounds["minZ"]) * H)


FONT = "/System/Library/Fonts/Hiragino Sans GB.ttc"


def render_map(labels):
    """labels=True draws spot dots and names for proofreading; the site gets the clean version
    because the app draws its own numbered pins on top of the map image."""
    img = Image.new("RGB", (W, H), (245, 241, 230))
    d = ImageDraw.Draw(img)
    for poly in getattr(park, "geoms", [park]):
        d.polygon([px(local(*c)) for c in poly.exterior.coords], fill=(226, 234, 214), outline=(150, 160, 130))
    for hill in geography["terrain"]["hills"]:
        cx, cy = px(hill["at"])
        r = hill["radius"] / (bounds["maxX"] - bounds["minX"]) * W
        d.ellipse([cx - r, cy - r * 0.55, cx + r, cy + r * 0.55], fill=(205, 214, 186))
    for w in water:
        d.polygon([px(p) for p in w["outer"]], fill=(170, 205, 222))
        for h in w["holes"]:
            d.polygon([px(p) for p in h], fill=(226, 234, 214))
    for p in paths:
        d.line([px(q) for q in p["points"]], fill=(190, 180, 160), width=2)
    for c in causeways:
        d.line([px(q) for q in c["points"]], fill=(160, 140, 110), width=5)
    if labels:
        font = ImageFont.truetype(FONT, 26)
        for s in spots:
            cx, cy = s["x"] * W, s["y"] * H
            d.ellipse([cx - 9, cy - 9, cx + 9, cy + 9], fill=(196, 52, 46), outline="white", width=3)
            d.text((cx + 13, cy - 16), s["name"], fill=(40, 40, 40), font=font, stroke_width=3, stroke_fill="white")
    d.text((16, H - 40), OSM_ATTRIBUTION, fill=(90, 90, 90), font=ImageFont.truetype(FONT, 20))
    return img


render_map(labels=True).save(ROOT / "preview-map.png")
render_map(labels=False).save(ROOT / "map.png")

print(f"origin={LON0},{LAT0} bounds={bounds} spots={len(spots)} water={len(water)} "
      f"paths={len(paths)} causeways={len(causeways)} map={W}x{H}")
