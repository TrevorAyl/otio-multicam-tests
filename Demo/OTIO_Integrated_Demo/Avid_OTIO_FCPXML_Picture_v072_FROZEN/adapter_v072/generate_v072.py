#!/usr/bin/env python3
"""Research adapter: enriched AAF/OTIO placements -> FCPXML 1.14.
All code AI generated, not independently reviewed or validated in Resolve.
"""
import json, pathlib, xml.etree.ElementTree as ET
from fractions import Fraction
from legacy_generate_v07 import export as export_picture_legacy

ROOT=pathlib.Path(__file__).resolve().parent
FPS=25

def seconds(frames):
    f=Fraction(int(frames),FPS)
    return f'{f.numerator}/{f.denominator}s'

def data():
    p=json.loads((ROOT/'avid_multicam_v14_enriched_backing.otio').read_text())
    definitions=[d for d in p['definitions'] if 'backing_placement_model' in d.get('attributes',{})]
    if len(definitions)!=1: raise ValueError('Expected exactly one timed backing composition')
    backing=definitions[0]['attributes']['backing_placement_model']
    slots={int(x['aaf_slot']):x for x in backing['slots']}
    if len(slots)!=59 or backing['duration_frames']!=4500: raise ValueError('Incorrect backing composition')
    return p,slots

def picture():
    p,slots=data()
    placements={}
    for s in slots.values():
        if s['media_kind']!='Picture':continue
        for piece in s['segments']:
            if piece['kind']!='SourceClip':continue
            key=piece['source_name']
            record={'sync_start_frame':piece['timeline_start_frame'],
                    'source_in_frame':piece['source_in_frame'],
                    'duration_frames':piece['duration_frames'],
                    'backing_slot':s['aaf_slot'],
                    'confidence':'embedded_enriched_aaf_backing'}
            if key in placements and placements[key]!=record:raise ValueError('Ambiguous recording '+key)
            placements[key]=record
    if len(placements)!=14: # 12 camera recordings plus GF01/GK01
        raise ValueError(f'Unexpected picture recordings {list(placements)}')
    manifest={'recordings':placements,'basis':'embedded CompositionDefinition.backing_placement_model'}
    path=ROOT/'outputs/embedded_sync_audit.json';path.write_text(json.dumps(manifest,indent=2)+'\n')
    return export_picture_legacy(ROOT/'avid_multicam_v14_enriched_backing.otio',ROOT/'outputs/avid_picture_enriched_sync.fcpxml',ROOT/'outputs/picture_report.json',path)

def audio():
    p,slots=data()
    # AAF's A01 channels are 16 discrete mono slots, indexed by the master/source slot identity.
    a01=slots[2]
    assert a01['media_kind']=='Sound'
    assert len([x for x in a01['segments'] if x['kind']=='SourceClip'])==1
    seg=next(x for x in a01['segments'] if x['kind']=='SourceClip')
    assert seg['timeline_start_frame']==0 and seg['master_mob_slot_id']==2
    matching=[m for m in p['media'] if m['media_id']==seg['media_id']]
    assert len(matching)==1
    media=matching[0]
    identity=media['identity'];url=identity['original_file_locators'][0]
    if url.startswith('file:////'):url='file:///'+url[len('file:////'):]
    tc=int(identity['source_timecodes'][0]['start_frame'])
    root=ET.Element('fcpxml',version='1.14')
    resources=ET.SubElement(root,'resources')
    ET.SubElement(resources,'format',{'id':'r1','name':'FFVideoFormat1080p25','frameDuration':'1/25s','width':'1920','height':'1080'})
    # The source may itself contain 16 mono tracks; FCPXML audioChannels is only a count,
    # not evidence that import will map AAF source channel #2 to an independently routed mono track.
    asset=ET.SubElement(resources,'asset',{'id':'r2','name':media['display_name']+'.mov',
        'start':seconds(tc),'duration':seconds(4500), 'format':'r1',
        'hasVideo':'1','hasAudio':'1','audioSources':'1', 'audioChannels':'16', 'audioRate':'48000'})
    ET.SubElement(asset,'media-rep',{'kind':'original-media','src':url})
    group=ET.SubElement(resources,'media',{'id':'r3','name':'Avid A01 mono-output diagnostic'})
    multicam=ET.SubElement(group,'multicam',{'format':'r1','tcStart':seconds(tc),'tcFormat':'NDF'})
    angle=ET.SubElement(multicam,'mc-angle',{'angleID':'aaf-a01-audio-slot-2','name':'A01 audio output 2 (mono diagnostic)'})
    ET.SubElement(angle,'asset-clip',{'ref':'r2','name':media['display_name']+'.mov',
        'offset':'0/1s','start':seconds(tc+seg['source_in_frame']),
        'duration':seconds(4500),'srcEnable':'audio'})
    library=ET.SubElement(root,'library');event=ET.SubElement(library,'event',{'name':'Avid audio channel diagnostic'})
    project=ET.SubElement(event,'project',{'name':'Avid A01 mono audio test'})
    sequence=ET.SubElement(project,'sequence',{'format':'r1','duration':seconds(100), 'tcStart':'0/1s','tcFormat':'NDF'})
    spine=ET.SubElement(sequence,'spine')
    # A simple 4-sec anchor with selected audio. FCPXML does not describe the AAF channel
    # mapping independently here; the test is solely whether Resolve can make an audio-selection.
    clip=ET.SubElement(spine,'mc-clip',{'ref':'r3','offset':'0/1s','start':seconds(tc), 'duration':seconds(100),'name':'A01 mono diagnostic'})
    ET.SubElement(clip,'mc-source',{'angleID':'aaf-a01-audio-slot-2','srcEnable':'audio'})
    ET.indent(root,space='  ')
    (ROOT/'outputs/avid_A01_mono_audio_diagnostic.fcpxml').write_bytes(
        b'<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE fcpxml>\n'+ET.tostring(root,encoding='utf-8'))
    report={'input_mono_backing_slot':2,'source_media_slot':2,'source_media_channels_declared':16,
      'duration_test_frames':100,'selected_audio_angle':'aaf-a01-audio-slot-2',
      'limitations':['Diagnostic audio only: may import 16 channels, not one mono channel',
       'FCPXML lacks an experimentally validated mapping for selected AAF source channel 2',
       'audioRate 48000 is an unverified test assumption; confirm actual file properties',
       'No independent Avid audio edits, per-track channel assignment or sample-accurate routing tested',
       'Native Resolve import has not been tested']}
    (ROOT/'outputs/audio_report.json').write_text(json.dumps(report,indent=2)+'\n')
    return report

if __name__=='__main__':
    print('Picture:',json.dumps({k:v for k,v in picture().items() if k in ('timeline_frames','picture_selections','picture_gaps','media_assets','provisional_placements')},indent=2))
    print('Audio:',json.dumps(audio(),indent=2))
