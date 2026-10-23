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
     "颐和园北侧入口，出地铁北宫门站即到，进门后先经苏州街，再上后山。",
     "北宫门正对后山中轴。进门过桥便是苏州街，沿中轴台阶上行可到须弥灵境，再翻过山脊就能俯瞰昆明湖，适合先逛后山、再下到前山湖岸的路线。"),
    ("suzhou-street", "苏州街", "后山后湖", 116.2685788, 40.0006584, "OSM POI",
     "沿后湖两岸展开的仿江南水乡买卖街，小桥、铺面与河道相互穿插。",
     "苏州街原是乾隆年间仿江南水乡修建的宫市，清末被毁，现貌为上世纪八十年代后期复建。店铺沿后湖两岸排开，以小桥相连，站在桥上最能看出水街的纵深。"),
    ("xiequyuan", "谐趣园", "后山东麓", 116.2758315, 39.9991338, "OSM POI",
     "万寿山东麓的园中之园，仿无锡寄畅园布局，池水居中、廊亭环绕。",
     "谐趣园始建于乾隆年间，原名惠山园，以无锡寄畅园为蓝本，嘉庆年间改为今名。小园围绕一池荷水展开，绕池一周能看到亭、榭、桥和曲廊的不同组合。"),
    ("deheyuan", "德和园", "东宫区", 116.2738091, 39.9970297, "OSM POI",
     "园内的大戏楼院落，上下三层的戏台是清宫规模最大的戏台之一。",
     "德和园大戏楼建于光绪年间，供慈禧太后看戏。戏台分上中下三层，可借助天井、地井做出升降布景；对面的颐乐殿是看戏的位置。"),
    ("zhichunting", "知春亭", "东岸", 116.2733692, 39.9954064, "OSM POI",
     "昆明湖东岸的小岛亭，经石桥与岸相连，是眺望万寿山的经典机位。",
     "知春亭建在东岸近处的小岛上，相传春天这一带的冰面最早消融，因而得名。站在亭边向西北望，佛香阁、万寿山与西山远景层层叠在一起。"),
    ("wenchangge", "文昌阁", "东岸", 116.2739486, 39.9952215, "OSM POI",
     "东堤北端的城关式楼阁，下为城台、上为两层楼阁。",
     "文昌阁是颐和园的城关建筑之一，与万寿山西侧的宿云檐一东一西相对，寓意文武。从这里沿东堤南行，可以一路走到铜牛和十七孔桥。"),
    ("long-corridor", "长廊", "前山", 116.270051, 39.997020, "OSM 步道中点",
     "沿昆明湖北岸延伸的彩画长廊，全长七百多米，串起前山各组建筑。",
     "长廊东起邀月门、西至石丈亭，全长约 728 米，梁枋上绘有一万四千余幅彩画，题材多为山水、花鸟与历史故事。雨天或酷暑时边走边抬头看画最舒服。"),
    ("paiyundian", "排云殿", "前山中轴", 116.2680477, 39.9971859, "OSM POI",
     "前山中轴上的主体殿宇，自湖边牌楼起层层抬高，直通佛香阁。",
     "排云殿建筑群是前山中轴的核心，光绪年间重建后用作慈禧太后庆寿的场所。从湖边的云辉玉宇牌楼开始，经排云门、二宫门到排云殿，地势逐级升高，最后接上佛香阁的石台。"),
    ("foxiangge", "佛香阁", "前山中轴", 116.267935, 39.9980571, "OSM POI",
     "建在万寿山前山高台上的八角楼阁，是整座园林的视觉中心。",
     "佛香阁高约 41 米，八面三层四重檐，立在约 20 米高的方形石台上。登上回廊可以俯瞰昆明湖、南湖岛和十七孔桥，是全园视野最开阔的地方。"),
    ("marble-boat", "清晏舫", "前山西端", 116.2636811, 39.9967379, "OSM POI",
     "长廊西端湖边的石舫，船身以巨石砌成，上部为两层船楼。",
     "清晏舫俗称石舫，乾隆年间初建时上部是中式舱楼，英法联军焚园后被毁，光绪年间重建为带西式装饰的两层船楼。从长廊西端看，船身几乎与湖面齐平。"),
    ("west-causeway", "西堤", "湖西", 116.264626, 39.988927, "OSM 步道中点",
     "纵贯昆明湖西部的长堤，仿杭州苏堤修建，沿途有六座桥。",
     "西堤自北向南贯穿昆明湖西侧，格局模仿西湖苏堤，堤上依次分布界湖桥、豳风桥、玉带桥、镜桥、练桥、柳桥六座桥。堤上游人相对少，适合傍晚看西山落日。"),
    ("jade-belt-bridge", "玉带桥", "西堤", 116.261074, 39.992127, "OSM 步道中点",
     "西堤上的高拱石桥，桥拱高耸，桥身洁白如带。",
     "玉带桥是西堤六桥中唯一的高拱桥，桥洞高而尖，便于当年皇家船只从昆明湖驶入玉河。水面平静时，倒影与桥拱合成近乎完整的圆。"),
    ("seventeen-arch-bridge", "十七孔桥", "南湖岛", 116.271467, 39.989490, "OSM 步道中点",
     "连接东堤与南湖岛的长桥，有十七个桥洞，是昆明湖上最大的石桥。",
     "十七孔桥长约 150 米，桥栏望柱上雕有五百多只形态各异的石狮。冬至前后的傍晚，夕阳会照进全部桥洞，被称为「金光穿洞」，届时观众很多。"),
    ("bronze-ox", "铜牛", "东堤", 116.2734175, 39.9894143, "OSM POI",
     "东堤上卧在石座上的铜牛，面朝昆明湖，寓意镇水。",
     "铜牛铸于乾隆二十年（1755 年），牛背上铸有乾隆所作的《金牛铭》，表达镇压水患的愿望。它就在十七孔桥东端附近，可以与桥一起安排。"),
]
NOTICE = "开放时间、预约方式与园中园门票以颐和园官方当日信息为准。"
OFFICIAL = "https://www.summerpalace-china.com/"

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
    ph = photos[sid]
    x, y = norm_xy(lon, lat)
    spots.append({
        "id": sid, "name": name, "description": desc, "guide": guide, "notice": NOTICE,
        "x": x, "y": y, "heading": 0, "scene": zone, "narration": {"text": guide},
        "factSource": OFFICIAL, "coordinateSource": coord_src, "lnglat": [lon, lat],
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
