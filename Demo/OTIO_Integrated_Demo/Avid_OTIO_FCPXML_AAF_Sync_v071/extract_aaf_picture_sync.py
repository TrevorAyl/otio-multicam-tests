#!/usr/bin/env python3
"""Extract exact 25-fps picture sync offsets from Avid AAF structural dump.
No source-timecode estimation; strictly map same slot and SourceClip order.
"""
import json,sys,pathlib
SLOTS=(1,18,21,23,26,28,31,44,57)
def derive(aaf,otio):
 mobs=[m for m in aaf['mobs'] if m['type']=='CompositionMob' and len(m.get('slots',[]))==59]
 if len(mobs)!=1:raise ValueError(f'Expected exactly one 59-slot backing composition, got {len(mobs)}')
 slots={s['slot_id']:s for s in mobs[0]['slots']}
 outs={o['source']['slot_id']:o['source']['media_sources'] for o in otio['output_references'] if o['source'].get('kind')=='composition_slot'}
 identities={m['media_id']:m['display_name'] for m in otio['media']}
 result={};details={}
 for slot in SLOTS:
  comps=slots[slot]['segment']['children'];cursor=0;seen=[]
  for part in comps:
   prop=part['properties']; length=prop['Length'];kind=part['type']
   if kind=='SourceClip':seen.append({'offset':cursor,'duration':length,'source_in':prop['StartTime']})
   elif kind!='Filler':raise ValueError(f'Unexpected segment {kind} in slot {slot}')
   cursor+=length
  members=outs[slot]
  if cursor!=4500:raise ValueError(f'Slot {slot}: backing length {cursor}, not 4500')
  if len(members)!=len(seen):raise ValueError(f'Slot {slot}: {len(seen)} SourceClips != {len(members)} OTIO media records')
  details[str(slot)]=[]
  for member,seg in zip(members,seen):
   name=identities[member['media_id']]
   if int(member['duration_frames'])!=seg['duration']:raise ValueError(f'{name}: length mismatch')
   if name in result:raise ValueError('Duplicate recording '+name)
   result[name]={'sync_start_frame':seg['offset'],'confidence':'aaf_backing_composition_segment','backing_slot':slot,'source_in_frame':seg['source_in'],'duration_frames':seg['duration']}
   details[str(slot)].append({'recording':name,**seg})
 return {'fps':25,'origin':'Avid 59-slot CompositionMob backing timeline origin','basis':'Exact SourceClip start from preceding Filler/SourceClip lengths in original AAF structure; no source-TC inference','recordings':result},details
if __name__=='__main__':
 here=pathlib.Path(__file__).resolve().parent
 aaf=json.loads((here/'avid_aaf_structure.json').read_text());otio=json.loads((here/'avid_multicam_v12_native_roundtrip.otio').read_text())
 m,d=derive(aaf,otio)
 (here/'sync_manifest.json').write_text(json.dumps(m,indent=2)+'\n')
 (here/'backing_slot_placements.json').write_text(json.dumps(d,indent=2)+'\n')
 for k,v in m['recordings'].items():print(f'{k:4} slot={v["backing_slot"]:2} sync={v["sync_start_frame"]:4} len={v["duration_frames"]:4}')
