#!/usr/bin/env python3
"""AI-generated experimental Avid-derived OTIO -> FCPXML 1.14 picture-only adapter.
Not tested for native Resolve import. Exact picture cuts, provisional synchronisation.
"""
import pathlib, json, re, argparse, collections, urllib.parse
import xml.etree.ElementTree as ET
from fractions import Fraction
FPS=25
NS='org.otio_multicam_research.v05'
def sec(fr):
 f=Fraction(int(fr),FPS)
 return f'{f.numerator}/{f.denominator}s'
def slot_of(clip):
 z=clip.get('metadata',{}).get(NS,{})
 i=z.get('selected',{}).get('SourceMobSlotID')
 if i is None:
  q=re.search(r'\bslot\s+(\d+)',clip.get('name',''))
  if q:i=int(q.group(1))
 return int(i) if i is not None else None
def get_media(m):
 i=m.get('identity',{});loc=i.get('original_file_locators') or []
 tc=(i.get('source_timecodes') or [{}])[0]
 if not loc or tc.get('start_frame') is None:raise ValueError(f'Missing media locator or TC for {m.get("display_name")}')
 url=loc[0]
 if url.startswith('file:////'):url='file:///'+url[len('file:////'):]
 return {'name':m['display_name'],'url':url,'tc':int(tc['start_frame'])}
def export(input_path, out_path, report_path, sync_path=None, allow_provisional=False):
 sync=json.loads(pathlib.Path(sync_path).read_text()) if sync_path else {"recordings":{}}
 placements=sync.get("recordings",{})
 missing=[]
 p=json.loads(pathlib.Path(input_path).read_text());assert p['OTIO_SCHEMA']=='MulticamPackage.1'
 tracks=p['timeline']['tracks']['children'];pic=next(x for x in tracks if x['name']=='picture')
 outputs={o['source']['slot_id']:o['source']['media_sources'] for o in p['output_references'] if o['source'].get('kind')=='composition_slot'}
 media={m['media_id']:get_media(m) for m in p['media']}
 used=[];edits=[];pos=0
 for c in pic['children']:
  dur=int(c['source_range']['duration']['value']);assert dur>0
  if c['OTIO_SCHEMA'].startswith('Gap'):
   edits.append({'kind':'gap','pos':pos,'duration':dur})
  else:
   i=slot_of(c)
   if i not in outputs:raise ValueError(f'Unresolved slot {i}')
   if i not in used:used.append(i)
   src=c.get('metadata',{}).get(NS,{}).get('selected',{}).get('StartTime')
   if src is None:raise ValueError(f'Missing selected source time on {c.get("name")}')
   edits.append({'kind':'picture','pos':pos,'duration':dur,'slot':i,'source_start':int(src)})
  pos+=dur
 assert pos==1406, pos
 # Nine unique picture angles by AAF source-slot identity; split recordings kept inside one angle.
 root=ET.Element('fcpxml',version='1.14');res=ET.SubElement(root,'resources')
 ET.SubElement(res,'format',{'id':'r1','name':'FFVideoFormat1080p25','frameDuration':'1/25s','width':'1920','height':'1080'})
 refs={};serial=2;slot_members={}
 for slot in used:
  sources=outputs[slot];slot_members[slot]=[]
  for x in sources:
   mid=x['media_id']
   if mid not in refs:
    v=media[mid];rid=f'r{serial}';serial+=1;refs[mid]=rid
    a=ET.SubElement(res,'asset',{'id':rid,'name':v['name']+'.mov','start':sec(v['tc']),'duration':sec(max(4500,int(x.get('duration_frames') or 0))),'format':'r1','hasVideo':'1'})
    ET.SubElement(a,'media-rep',{'src':v['url'],'kind':'original-media'})
   slot_members[slot].append({'id':mid,'name':media[mid]['name'],'duration':int(x['duration_frames']), 'source_in':int(x.get('source_in_frame') or 0)})
 mid=f'r{serial}';m=ET.SubElement(res,'media',{'id':mid,'name':'Avid MCAM EDIT — picture-only v0.6'})
 base_tc=media[slot_members[used[0]][0]['id']]['tc']
 mc=ET.SubElement(m,'multicam',{'format':'r1','tcStart':sec(base_tc),'tcFormat':'NDF'})
 coverage={}
 for slot in used:
  name='+'.join(x['name'] for x in slot_members[slot]);an=ET.SubElement(mc,'mc-angle',{'angleID':f'aaf-video-slot-{slot}','name':name});cursor=0
  for item in slot_members[slot]:
   mm=media[item['id']]
   rec_name=mm['name']
   placement=placements.get(rec_name,{})
   if placement.get('sync_start_frame') is None:
    missing.append(rec_name)
    if not allow_provisional:
     raise ValueError(f'No confirmed multicam sync_start_frame for {rec_name}. Set it in sync_manifest.json, or use --allow-provisional (not suitable for fidelity claims).')
    place=cursor
   else:
    place=int(placement['sync_start_frame'])
   if place < 0:raise ValueError(f'Negative multicam placement for {rec_name}')
   ET.SubElement(an,'asset-clip',{'ref':refs[item['id']], 'name':mm['name']+'.mov','offset':sec(place), 'start':sec(mm['tc']+int(placement.get('source_in_frame',item['source_in']))),'duration':sec(item['duration']),'srcEnable':'video'})
   cursor=max(cursor,place+item['duration'])
  coverage[slot]=cursor
 l=ET.SubElement(root,'library');e=ET.SubElement(l,'event',{'name':'Avid OTIO picture interchange test'})
 project=ET.SubElement(e,'project',{'name':'Avid MCAM EDIT — picture only v0.6'})
 seq=ET.SubElement(project,'sequence',{'format':'r1','duration':sec(1406),'tcStart':'0/1s','tcFormat':'NDF'})
 spine=ET.SubElement(seq,'spine');issues=[]
 for ed in edits:
  if ed['kind']=='gap':ET.SubElement(spine,'gap',{'offset':sec(ed['pos']),'start':'0/1s','duration':sec(ed['duration']),'name':'AAF picture filler'});continue
  if ed['source_start']+ed['duration']>coverage[ed['slot']]:issues.append({'slot':ed['slot'],'position':ed['pos'],'source':ed['source_start'],'duration':ed['duration'],'angle_duration':coverage[ed['slot']],'note':'Selected source interval exceeds constructed contiguous angle coverage'})
  clip=ET.SubElement(spine,'mc-clip',{'ref':mid,'name':f'AAF video slot {ed["slot"]}','offset':sec(ed['pos']),'start':sec(base_tc+ed['source_start']),'duration':sec(ed['duration'])})
  ET.SubElement(clip,'mc-source',{'angleID':f'aaf-video-slot-{ed["slot"]}','srcEnable':'video'})
 ET.indent(root,space='  ')
 b=b'<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE fcpxml>\n'+ET.tostring(root,encoding='utf-8')
 pathlib.Path(out_path).write_bytes(b)
 report={'status':'EXPERIMENTAL_UNTESTED_IN_RESOLVE','source':'real Avid AAF-derived experimental OTIO','fps':25,'timeline_frames':pos,'timeline_edits':len(edits),'picture_selections':sum(e['kind']=='picture' for e in edits),'picture_gaps':sum(e['kind']=='gap' for e in edits),'picture_angle_slots':used,'media_assets':len(refs),'angle_coverage_frames':coverage,'provisional_placements':sorted(set(missing)),'sync_manifest':str(sync_path) if sync_path else None,'selection_coverage_warnings':issues,'edit_decisions':edits,'limitations':['Audio and composite effects omitted by design','Source offset semantics inferred from AAF Selector StartTime and not independently verified against the Avid source-group timeline','Placements of sources not in sync_manifest are provisional; independent video/audio sync not certified','Media source start and locator require relink validation','No Resolve import has been tested']}
 pathlib.Path(report_path).write_text(json.dumps(report,indent=2)+'\n')
 return report
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('otio');ap.add_argument('--sync',default='sync_manifest.json');ap.add_argument('--allow-provisional',action='store_true');ap.add_argument('--out',default='outputs/avid_picture_1406_frames.fcpxml');ap.add_argument('--report',default='outputs/loss_report.json');a=ap.parse_args()
 r=export(a.otio,a.out,a.report,a.sync,a.allow_provisional);print(json.dumps({k:r[k] for k in ['timeline_frames','picture_selections','picture_gaps','picture_angle_slots','media_assets','selection_coverage_warnings']},indent=2))
