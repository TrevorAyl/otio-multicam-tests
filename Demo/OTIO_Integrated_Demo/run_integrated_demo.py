#!/usr/bin/env python3
"""Dataset-specific AAF-backed OTIO refresh and frozen FCPXML comparison.
Not a general-purpose AAF->OTIO converter. Original source files remain untouched.
"""
import copy, hashlib, importlib.util, json, pathlib, shutil, subprocess, sys, tempfile, traceback
from collections import Counter

ROOT=pathlib.Path(__file__).resolve().parent
FROZEN=ROOT/'Avid_OTIO_FCPXML_Picture_v072_FROZEN'
ADAPTER=FROZEN/'adapter_v072'
AAF=ROOT/'Avid MCAM EDIT.aaf'
V71=ROOT/'Avid_OTIO_FCPXML_AAF_Sync_v071'
OUT=ROOT/'demo_output'

def load(name,file):
    spec=importlib.util.spec_from_file_location(name,file)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    return mod

def sha(file):return hashlib.sha256(pathlib.Path(file).read_bytes()).hexdigest()

def run():
    import aaf2
    fresh=load('fresh_aaf',ROOT/'run_fresh_aaf_demo.py')
    sel=load('selector_extract',ROOT/'extract_and_verify_selectors.py')
    OUT.mkdir(exist_ok=True)
    report={'scope':'Known Avid AAF; reference v1.4 fixture identity/track/media model retained',
            'source_aaf':AAF.name,'checks':{},'limitations':[
            'Not a general-purpose AAF-to-OTIO converter',
            'Original fixture still provides portable IDs, timeline topology, angle definitions and media metadata',
            'Audio reconstruction and Resolve-native import are not validated by this command']}
    def check(name,condition,detail=None):
        report['checks'][name]={'pass':bool(condition),'detail':detail}
        print(('PASS' if condition else 'FAIL'),name, (f'— {detail}' if detail else ''))
        if not condition:raise ValueError(name + (': '+str(detail) if detail else ''))
    try:
        # Assert frozen files are unaltered, including all listed checksums.
        sums=(FROZEN/'SHA256SUMS.txt').read_text().splitlines()
        for line in sums:
            if not line.strip():continue
            expected,rel=line.split(maxsplit=1)
            f=FROZEN/rel.strip().lstrip('*')
            check('frozen hash '+rel, f.exists() and sha(f)==expected) if not (f.exists() and sha(f)==expected) else None
        check('frozen release checksums',all(sha(FROZEN/line.split(maxsplit=1)[1].strip().lstrip('*'))==line.split(maxsplit=1)[0] for line in sums if line.strip()))
        old_dump=json.loads((V71/'avid_aaf_structure.json').read_text())
        old_mob,old_slots=fresh.expected_slots(old_dump)
        mob,slots=fresh.raw_slots(AAF)
        check('backing CompositionMob',mob==old_mob,mob)
        check('59 backing slots',len(slots)==59,len(slots))
        check('107 backing segments',sum(len(x['segments']) for x in slots)==107)
        check('fresh AAF backing equals archived',fresh.core(slots)==fresh.core(old_slots))
        # Load known-good v1.4 and refresh ONLY fields grounded in the AAF.
        fixture=json.loads((ADAPTER/'avid_multicam_v14_enriched_backing.otio').read_text())
        defs=[d for d in fixture['definitions'] if 'backing_placement_model' in d.get('attributes',{})]
        check('one enriched backing model',len(defs)==1)
        model=defs[0]['attributes']['backing_placement_model']
        backing={int(s['aaf_slot']):s for s in model['slots']}
        check('same AAF backing slots in fixture',set(backing)=={int(s['aaf_slot']) for s in slots})
        newslots=[]
        for srcslot in slots:
            dst=copy.deepcopy(backing[srcslot['aaf_slot']])
            check('slot segment count '+str(srcslot['aaf_slot']),len(dst['segments'])==len(srcslot['segments'])) if len(dst['segments'])!=len(srcslot['segments']) else None
            for old,new in zip(dst['segments'],srcslot['segments']):
                for field in ('kind','timeline_start_frame','duration_frames','source_in_frame','source_mob_id','source_mob_slot_id'):
                    if field in new:old[field]=new[field]
            dst['total_frames']=srcslot['total_frames'];newslots.append(dst)
        model['slots']=newslots
        # Traverse all AAF Selector objects using their fixture provenance paths.
        import re
        entries=[];errors=[]
        with aaf2.open(str(AAF),'r') as f:
            mobs={str(m.mob_id):m for m in f.content.mobs}
            for s in fixture['selectors']:
                loc=s['provenance']['aaf_path']
                m=re.fullmatch(r'definitions/(.+?)/slots/(\d+)(?:/(.*))?',loc)
                if not m:raise ValueError('invalid provenance path '+loc)
                mobid,slotid,tail=m.group(1),int(m.group(2)),m.group(3)
                candidates=[x for x in mobs[mobid].slots if int(x.slot_id)==slotid]
                if len(candidates)!=1:raise ValueError('nonunique AAF mob slot at '+loc)
                obj=candidates[0].segment
                if tail:obj=sel.walk(obj,tail.split('/'))
                a=sel.select_info(obj)
                choices=[a['selected'],*a['alternatives']]
                keys=('source_id','source_slot','start_frame','duration_frames')
                problems=[]
                for key in keys:
                    if a['selected'][key]!=s['selected'][key]:problems.append('selected.'+key)
                if len(choices)!=len(s['alternatives']):problems.append('choice-count')
                for i,(source,reference) in enumerate(zip(choices,s['alternatives'])):
                    for key in keys:
                        if source[key]!=reference[key]:problems.append(f'choice {i}.{key}')
                if a['duration_frames']!=s['timing']['duration_frames']:problems.append('selector duration')
                if a['selected']['start_frame']!=s['timing']['source_in_frame']:problems.append('timing inpoint')
                if problems:errors.append({'path':loc,'differences':problems})
                entries.append({'path':loc,'AAF':a,'match':not problems})
        check('79 AAF selector occurrences',len(entries)==79,len(entries))
        (OUT/'selector_evidence.json').write_text(json.dumps({'selectors':entries,'errors':errors},indent=2)+'\n')
        check('all selector choices and timing match',not errors,errors[:5] if errors else '79/79')
        for dest,entry in zip(fixture['selectors'],entries):
            a=entry['AAF']
            for key in keys:dest['selected'][key]=a['selected'][key]
            for dst,src in zip(dest['alternatives'],[a['selected'],*a['alternatives']]):
                for key in keys:dst[key]=src[key]
            dest['timing']['duration_frames']=a['duration_frames']
            dest['timing']['source_in_frame']=a['selected']['start_frame']
        (OUT/'refreshed_from_AAF_verified_template.otio').write_text(json.dumps(fixture,indent=2)+'\n')
        with tempfile.TemporaryDirectory(prefix='otio_integrated_') as tmp:
            work=pathlib.Path(tmp)/'adapter';shutil.copytree(ADAPTER,work)
            (work/'avid_multicam_v14_enriched_backing.otio').write_text(json.dumps(fixture,indent=2)+'\n')
            p=subprocess.run([sys.executable,'generate_v072.py'],cwd=work,text=True,capture_output=True)
            (OUT/'generator.log').write_text(p.stdout+'\n'+p.stderr)
            check('frozen generator execution',p.returncode==0,p.stderr[-500:] if p.returncode else 'exit 0')
            produced=work/'outputs/avid_picture_enriched_sync.fcpxml'
            expected=ADAPTER/'outputs/avid_picture_enriched_sync.fcpxml'
            check('FCPXML byte identity',produced.read_bytes()==expected.read_bytes(),sha(produced))
            shutil.copy2(produced,OUT/'avid_picture_enriched_sync.fcpxml')
            shutil.copy2(work/'outputs/picture_report.json',OUT/'picture_report.json')
        check('original frozen hashes unchanged',all(sha(FROZEN/line.split(maxsplit=1)[1].strip().lstrip('*'))==line.split(maxsplit=1)[0] for line in sums if line.strip()))
        report['success']=True
    except Exception as exc:
        report['success']=False;report['error']=str(exc)
        (OUT/'failure_traceback.txt').write_text(traceback.format_exc())
        print('STOPPED:',exc)
    finally:
        (OUT/'structural_report.json').write_text(json.dumps(report,indent=2)+'\n')
        lines=['# Integrated AAF → verified enriched OTIO → FCPXML','',f'Overall: **{"PASS" if report.get("success") else "FAIL"}**','',
               '| Check | Result |','|---|---|']
        for name,result in report['checks'].items():lines.append(f'| {name} | {"PASS" if result["pass"] else "FAIL"} |')
        lines+=['','## Scope','This refresh uses independently parsed backing placements and selected/alternative AAF choices, but retains portable OTIO structure, identifiers and media metadata from a validated reference fixture. This is not a general AAF converter. Audio interchange is not demonstrated. Resolve import/editability remains a separate operator verification.','',
                'The experimental v1.4 schema and frozen v0.7.2 exporter remain unchanged. Code and materials were created with AI assistance; original NLE source and application validation were supplied by the project owner.']
        (OUT/'VALIDATION_REPORT.md').write_text('\n'.join(lines)+'\n')
    return 0 if report.get('success') else 1

if __name__=='__main__':sys.exit(run())
