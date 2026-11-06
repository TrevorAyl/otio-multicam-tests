#!/usr/bin/env python3
"""Fresh AAF structural read and checked picture export, without modifying frozen v0.7.2.
Uses archived enriched v1.4 template for EDITORIAL selectors/media mapping. NOT a full independent AAF -> OTIO adapter.
"""
import argparse,copy,hashlib,json,pathlib,shutil,subprocess,sys,tempfile,xml.etree.ElementTree as ET
ROOT=pathlib.Path(__file__).resolve().parent
V71=ROOT/'Avid_OTIO_FCPXML_AAF_Sync_v071'
FROZEN=ROOT/'Avid_OTIO_FCPXML_Picture_v072_FROZEN'
ADAPTER=FROZEN/'adapter_v072'

def val(obj,name):
    try:return obj[name].value
    except Exception:
        try:return obj.get(name).value
        except Exception as e:raise ValueError(f'Cannot read {name} on {type(obj).__name__}: {e}')

def raw_slots(path):
    import aaf2
    candidates=[]
    with aaf2.open(str(path),'r') as f:
        for mob in f.content.mobs:
            if type(mob).__name__!='CompositionMob':continue
            slots=list(mob.slots)
            if len(slots)!=59:continue
            candidates.append((str(mob.mob_id),slots))
        if len(candidates)!=1:raise ValueError(f'Expected one 59-slot CompositionMob, found {len(candidates)}')
        mobid,slots=candidates[0];results=[]
        for slot in slots:
            sid=int(slot.slot_id); seg=slot.segment
            if type(seg).__name__!='Sequence':raise ValueError(f'Backing slot {sid}: expected Sequence, got {type(seg).__name__}')
            cursor=0;parts=[]
            for item in list(seg.components):
                kind=type(item).__name__
                duration=int(val(item,'Length'))
                if kind=='SourceClip':
                    parts.append({'kind':kind,'timeline_start_frame':cursor,'duration_frames':duration,
                       'source_in_frame':int(val(item,'StartTime')),
                       'source_mob_id':str(val(item,'SourceID')),
                       'source_mob_slot_id':int(val(item,'SourceMobSlotID'))})
                elif kind=='Filler':parts.append({'kind':kind,'timeline_start_frame':cursor,'duration_frames':duration})
                else:raise ValueError(f'Slot {sid}: unexpected {kind}')
                cursor+=duration
            results.append({'aaf_slot':sid,'total_frames':cursor,'segments':parts})
    return mobid,results

def expected_slots(dump):
    mobs=[m for m in dump['mobs'] if m['type']=='CompositionMob' and len(m.get('slots',[]))==59]
    if len(mobs)!=1:raise ValueError('Archived dump lacks a unique 59-slot CompositionMob')
    mob=mobs[0];res=[]
    for slot in mob['slots']:
        cursor=0;parts=[]
        for item in slot['segment']['children']:
            kind=item['type'];p=item['properties'];length=int(p['Length'])
            s={'kind':kind,'timeline_start_frame':cursor,'duration_frames':length}
            if kind=='SourceClip':s.update(source_in_frame=int(p['StartTime']),source_mob_id=str(p['SourceID']),source_mob_slot_id=int(p['SourceMobSlotID']))
            elif kind!='Filler':raise ValueError('Unexpected archived segment '+kind)
            parts.append(s);cursor+=length
        res.append({'aaf_slot':int(slot['slot_id']),'total_frames':cursor,'segments':parts})
    return mob['mob_id'],res

def core(x):return {int(s['aaf_slot']):{'total_frames':s['total_frames'],'segments':s['segments']} for s in x}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--aaf',type=pathlib.Path,default=ROOT/'Avid MCAM EDIT.aaf')
    parser.add_argument('--out',type=pathlib.Path,default=ROOT/'demo_output_fresh_aaf')
    parser.add_argument('--archived-only',action='store_true',help='Test checker and exporter using stored AAF JSON; no raw AAF parsing')
    args=parser.parse_args();out=args.out.resolve();out.mkdir(parents=True,exist_ok=True)
    archived=json.loads((V71/'avid_aaf_structure.json').read_text())
    old_mob,old_slots=expected_slots(archived)
    if args.archived_only:mob,slots=old_mob,old_slots;mode='ARCHIVED JSON SELF-TEST (NOT FRESH AAF)'
    else:mob,slots=raw_slots(args.aaf.resolve());mode='FRESH RAW AAF'
    errors=[]
    if mob!=old_mob:errors.append('Backing CompositionMob ID differs')
    actual,expected=core(slots),core(old_slots)
    for sid in sorted(set(actual)|set(expected)):
        if actual.get(sid)!=expected.get(sid):errors.append(f'AAF backing slot {sid} differs from archived dump')
    print(f'{mode}: {len(actual)} slots, {sum(len(s["segments"]) for s in slots)} segments')
    print('Archived structural comparison:', 'MATCH' if not errors else 'FAIL')
    for e in errors[:30]:print('  ',e)
    report={'mode':mode,'fresh_aaf':not args.archived_only,'source':str(args.aaf),'backing_mob_id':mob,
      'slots':len(actual),'segments':sum(len(s['segments']) for s in slots),'structural_match':not errors,'errors':errors}
    (out/'fresh_aaf_validation.json').write_text(json.dumps(report,indent=2)+'\n')
    if errors:return 1
    fixture=json.loads((ADAPTER/'avid_multicam_v14_enriched_backing.otio').read_text())
    definitions=[d for d in fixture['definitions'] if 'backing_placement_model' in d.get('attributes',{})]
    if len(definitions)!=1:raise ValueError('Enriched fixture lacks unique backing model')
    model=definitions[0]['attributes']['backing_placement_model']
    template={int(s['aaf_slot']):s for s in model['slots']}
    replacements=[]
    for s in slots:
        slot=copy.deepcopy(template[s['aaf_slot']]);source=iter(s['segments'])
        if len(slot['segments'])!=len(s['segments']):raise ValueError(f'Slot {s["aaf_slot"]}: segment-count mismatch')
        for dest,src in zip(slot['segments'],s['segments']):
            for field in ('kind','timeline_start_frame','duration_frames','source_in_frame','source_mob_id','source_mob_slot_id'):
                if field in src:dest[field]=src[field]
        slot['total_frames']=s['total_frames'];replacements.append(slot)
    model['slots']=replacements
    # Core semantics and ancillary metadata remain sourced from the KNOWN-GOOD enriched fixture.
    # Exact-match guard ensures that this refresh is not silently used for new AAFs.
    with tempfile.TemporaryDirectory(prefix='otio_fresh_aaf_') as td:
        t=pathlib.Path(td)/'adapter';shutil.copytree(ADAPTER,t)
        (t/'avid_multicam_v14_enriched_backing.otio').write_text(json.dumps(fixture,indent=2)+'\n')
        p=subprocess.run([sys.executable,str(t/'generate_v072.py')],cwd=t,capture_output=True,text=True)
        (out/'generator_stdout.txt').write_text(p.stdout+'\n'+p.stderr)
        if p.returncode:print('Generator failed:',p.stderr);return p.returncode
        a=t/'outputs/avid_picture_enriched_sync.fcpxml'
        b=ADAPTER/'outputs/avid_picture_enriched_sync.fcpxml'
        if not b.exists():raise ValueError('Missing known-good FCPXML baseline')
        same=a.read_bytes()==b.read_bytes()
        shutil.copy2(a,out/'avid_picture_enriched_sync.fcpxml')
        shutil.copy2(t/'outputs/picture_report.json',out/'picture_report.json')
        (out/'fresh_enriched_from_verified_template.otio').write_text(json.dumps(fixture,indent=2)+'\n')
        report['fcpxml_byte_identical']=same
        report['fcpxml_sha256']=hashlib.sha256(a.read_bytes()).hexdigest()
        report['baseline_fcpxml_sha256']=hashlib.sha256(b.read_bytes()).hexdigest()
        (out/'fresh_aaf_validation.json').write_text(json.dumps(report,indent=2)+'\n')
        print('FCPXML byte-identical to frozen v0.7.2:', 'PASS' if same else 'FAIL')
        print('Output:',out)
        return 0 if same else 1

if __name__=='__main__':sys.exit(main())
