"""Retrieve Commons category membership and per-file licenses; no full-text photo search."""
import json,html,re,urllib.request,urllib.parse,concurrent.futures
from pathlib import Path
ROOT=Path(__file__).resolve().parent; RAW=ROOT/'raw'
def get(params):
 u='https://commons.wikimedia.org/w/api.php?'+urllib.parse.urlencode(dict(params,format='json'))
 return json.load(urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'JingjianScenicResearch/1.0'}),timeout=30))
cats=['Former Residence of Lu Haodong','Former Residence of Yang Yin','Zhenyi Hall']
for cat in cats:
 d=get({'action':'query','list':'categorymembers','cmtitle':'Category:'+cat,'cmlimit':500})
 (RAW/('commons-'+cat+'.json')).write_text(json.dumps(d,ensure_ascii=False,indent=2))
 print(cat,[x['title'] for x in d['query']['categorymembers']],flush=True)
alltitles=[]
for p in RAW.glob('commons*.json'):
 alltitles.extend(x['title'] for x in json.loads(p.read_text())['query']['categorymembers'] if x['ns']==6)
alltitles=sorted(set(alltitles))
# Metadata only; later human visual review chooses actual assets.
def info(batch):
 d=get({'action':'query','titles':'|'.join(batch),'prop':'imageinfo','iiprop':'url|size|extmetadata','iiurlwidth':1280})
 result=[]
 for p in d['query']['pages'].values():
  if not p.get('imageinfo'):continue
  ii=p['imageinfo'][0];m=ii.get('extmetadata',{})
  val=lambda k:re.sub('<[^>]*>','',html.unescape(m.get(k,{}).get('value',''))).strip()
  result.append({'title':p['title'],'url':ii.get('thumburl') or ii['url'],'original':ii['url'],'source':ii['descriptionurl'],'width':ii['width'],'height':ii['height'],'artist':val('Artist'),'license':val('LicenseShortName'),'licenseUrl':val('LicenseUrl'),'date':val('DateTimeOriginal'),'description':val('ImageDescription'),'retrieved':'2026-10-23'})
 return result
result=[]
for batch in concurrent.futures.ThreadPoolExecutor(3).map(info,[alltitles[i:i+40] for i in range(0,len(alltitles),40)]):result.extend(batch)
(RAW/'photo_candidates.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
print('Total metadata',len(result),flush=True)
