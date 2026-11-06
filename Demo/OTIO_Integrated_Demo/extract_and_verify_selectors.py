#!/usr/bin/env python3
"""Read original AAF selectors; verify and refresh reference v1.4 selector fields.
Strictly dataset-specific, not general AAF -> OTIO interchange. Frozen source unchanged.
"""
import copy,hashlib,json,pathlib,re,shutil,subprocess,sys,tempfile
ROOT=pathlib.Path(__file__).resolve().parent
FROZEN=ROOT/'Avid_OTIO_FCPXML_Picture_v072_FROZEN'
ADAPTER=FROZEN/'adapter_v072'
AAF=ROOT/'Avid MCAM EDIT.aaf'
OUTPUT=ROOT/'selector_validation_output'

def prop(obj,key):
    try:return obj[key].value
    except Exception:
        try:return obj.get(key).value
        except Exception as e:raise RuntimeError(f'{type(obj).__name__}.{key}: {e}')

def typename(obj):return type(obj).__name__
def length(obj):return int(prop(obj,'Length'))

def source(clip):
    if typename(clip)!='SourceClip':raise TypeError(f'Expected SourceClip, got {typename(clip)}')
    return {'source_id':str(prop(clip,'SourceID')),
        'source_slot':int(prop(clip,'SourceMobSlotID')),
        'start_frame':int(prop(clip,'StartTime')),
        'duration_frames':length(clip)}

def select_info(obj):
    if typename(obj)!='Selector':raise TypeError(f'Expected Selector, got {typename(obj)}')
    selected=source(prop(obj,'Selected'))
    try:alts=[source(x) for x in prop(obj,'Alternates')]
    except Exception as e:
        # Only absent Alternates is acceptable; don't conceal genuine parse problems.
        if 'Alternates' not in str(e):raise
        alts=[]
    return {'selected':selected,'alternatives':alts,'duration_frames':length(obj)}

def walk(obj,parts):
    if not parts:return obj
    label,idx=parts[0],int(parts[1]);rest=parts[2:]
    if label=='components':
        if typename(obj)!='Sequence':raise TypeError(f'components on {typename(obj)}')
        return walk(list(prop(obj,'Components'))[idx],rest)
    if label=='layers':
        if typename(obj)!='NestedScope':raise TypeError(f'layers on {typename(obj)}')
        return walk(list(prop(obj,'Slots'))[idx],rest)
    if label=='inputs':
        if typename(obj)!='OperationGroup':raise TypeError(f'inputs on {typename(obj)}')
        return walk(list(prop(obj,'InputSegments'))[idx],rest)
    raise ValueError('Unknown path label '+label)

def main():
    import aaf2
    OUTPUT.mkdir(exist_ok=True)
    fixture=json.loads((ADAPTER/'avid_multicam_v14_enriched_backing.otio').read_text())
    selectors=fixture['selectors']
    diagnostics=[];errors=[];checked=0
    with aaf2.open(str(AAF),'r') as f:
        mobs={str(m.mob_id):m for m in f.content.mobs}
        for s in selectors:
            loc=s['provenance']['aaf_path']
            m=re.fullmatch(r'definitions/(.+?)/slots/(\d+)(?:/(.*))?',loc)
            if not m:raise ValueError('Invalid selector path '+loc)
            mobid,slotid,tail=m.group(1),int(m.group(2)),m.group(3)
            record={'path':loc,'stream':s['stream'],'selector_id':s['selector_id']}
            try:
                mob=mobs[mobid]
                slots=[x for x in mob.slots if int(x.slot_id)==slotid]
                if len(slots)!=1:raise ValueError('Expected unique slot')
                obj=slots[0].segment
                if tail:obj=walk(obj,tail.split('/'))
                actual=select_info(obj)
                ref_sel=s['selected'];ref_alt=s['alternatives']
                # In the OTIO v1.4 fixture, alternatives lists ALL choices, selected first.
                # AAF Selector.Alternates omits Selector.Selected, so restore it explicitly.
                aaf_choices=[actual['selected'], *actual['alternatives']]
                field_keys=('source_id','source_slot','start_frame','duration_frames')
                problems=[]
                for key in field_keys:
                    if actual['selected'][key]!=ref_sel[key]:problems.append(f'selected.{key}: AAF={actual["selected"][key]!r} fixture={ref_sel[key]!r}')
                if actual['duration_frames']!=s['timing']['duration_frames']:
                    problems.append('selector duration differs')
                if len(aaf_choices)!=len(ref_alt):
                    problems.append(f'complete choices count: AAF={len(aaf_choices)} fixture={len(ref_alt)}')
                for i,(a,r) in enumerate(zip(aaf_choices,ref_alt)):
                    for key in field_keys:
                        if a[key]!=r[key]:problems.append(f'alternative[{i}].{key}: AAF={a[key]!r} fixture={r[key]!r}')
                if actual['selected']['start_frame']!=s['timing']['source_in_frame']:
                    problems.append('timing.source_in_frame differs')
                record.update(AAF=actual,reference= {'selected':ref_sel,'alternatives':ref_alt},match=not problems,errors=problems)
                checked+=1
                for problem in problems:errors.append(f'{loc}: {problem}')
            except Exception as exc:
                record.update(match=False,errors=[str(exc)])
                errors.append(f'{loc}: {exc}')
            diagnostics.append(record)
    report={'fresh_aaf':AAF.name,'fixture_selector_count':len(selectors),'selector_occurrences_checked':checked,
        'selector_matches':sum(x['match'] for x in diagnostics),'all_match':not errors,'errors':errors,
        'selectors':diagnostics,'scope':'AAF selector field verification versus existing v1.4 fixture; not independent regeneration of all OTIO semantics'}
    (OUTPUT/'selector_aaf_audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f'Fresh AAF selectors: {checked}/{len(selectors)} readable, {report["selector_matches"]} exact matches')
    if errors:
        print('FAIL — first differences:')
        for e in errors[:15]:print(' -',e)
        print('Full audit:',OUTPUT/'selector_aaf_audit.json')
        return 1
    # Refresh strictly the AAF-derived selected/alternatives/timing fields in copy; all portable
    # identifiers, media metadata and timeline structure still come from reference v1.4 fixture.
    refreshed=copy.deepcopy(fixture)
    for s,diagnostic in zip(refreshed['selectors'],diagnostics):
        actual=diagnostic['AAF']
        for key in ('source_id','source_slot','start_frame','duration_frames'):s['selected'][key]=actual['selected'][key]
        for dest,alt in zip(s['alternatives'],[actual['selected'], *actual['alternatives']]):
            for key in ('source_id','source_slot','start_frame','duration_frames'):dest[key]=alt[key]
        s['timing']['duration_frames']=actual['duration_frames']
        s['timing']['source_in_frame']=actual['selected']['start_frame']
    generated=OUTPUT/'selector_refreshed_from_raw_aaf.otio'
    generated.write_text(json.dumps(refreshed,indent=2)+'\n')
    with tempfile.TemporaryDirectory(prefix='otio_sel_') as temp:
        work=pathlib.Path(temp)/'adapter'
        shutil.copytree(ADAPTER,work)
        (work/'avid_multicam_v14_enriched_backing.otio').write_text(json.dumps(refreshed,indent=2)+'\n')
        p=subprocess.run([sys.executable,'generate_v072.py'],cwd=work,text=True,capture_output=True)
        (OUTPUT/'generator.log').write_text(p.stdout+'\n'+p.stderr)
        if p.returncode:
            print('FCPXML generator failed; see generator.log');return p.returncode
        new=(work/'outputs/avid_picture_enriched_sync.fcpxml').read_bytes()
        baseline=(ADAPTER/'outputs/avid_picture_enriched_sync.fcpxml').read_bytes()
        same=new==baseline
        (OUTPUT/'selector_refreshed_picture.fcpxml').write_bytes(new)
        report['fcpxml_byte_identical']=same
        report['fcpxml_sha256']=hashlib.sha256(new).hexdigest()
        report['baseline_sha256']=hashlib.sha256(baseline).hexdigest()
        (OUTPUT/'selector_aaf_audit.json').write_text(json.dumps(report,indent=2)+'\n')
        print('Frozen v0.7.2 FCPXML byte-identical:', 'PASS' if same else 'FAIL')
        print('Audit:',OUTPUT/'selector_aaf_audit.json')
        return 0 if same else 1
if __name__=='__main__':sys.exit(main())
