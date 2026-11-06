import unittest, pathlib, json, xml.etree.ElementTree as ET
from generate_v072 import data,picture,audio,ROOT

class EnrichedConversionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        picture();audio()
        cls.p=ET.parse(ROOT/'outputs/avid_picture_enriched_sync.fcpxml').getroot()
        cls.a=ET.parse(ROOT/'outputs/avid_A01_mono_audio_diagnostic.fcpxml').getroot()
    def test_backing_slots(self):
        _,slots=data();self.assertEqual(len(slots),59)
        self.assertEqual(sum(s['media_kind']=='Sound' for s in slots.values()),48)
    def test_picture_timing(self):
        self.assertEqual(len(self.p.findall('.//mc-angle')),9)
        self.assertEqual(len(self.p.findall('.//mc-clip')),11)
        self.assertEqual(len(self.p.findall('.//mc-angle/asset-clip')),12)
        offsets={c.get('name').removesuffix('.mov'):c.get('offset') for c in self.p.findall('.//mc-angle/asset-clip')}
        for name,off in {'B01':'5/1s','C02':'2002/25s','D01':'12/1s','E01':'8/1s','F02':'308/5s','F03':'704/5s','H01':'20/1s'}.items():
            self.assertEqual(offsets[name],off)
        self.assertEqual(self.p.find('.//sequence').get('duration'),'1406/25s')
        self.assertEqual(len(self.p.findall('.//spine/gap')),1)
    def test_audio_mono_source_provenance(self):
        _,slots=data()
        self.assertEqual(slots[2]['segments'][0]['master_mob_slot_id'],2)
        self.assertEqual(len(self.a.findall('.//mc-source')),1)
        self.assertEqual(self.a.find('.//mc-source').get('srcEnable'),'audio')
        self.assertEqual(self.a.find('.//asset').get('audioChannels'),'16')
    def test_no_external_sync_manifest_dependency(self):
        x=json.loads((ROOT/'outputs/embedded_sync_audit.json').read_text())
        self.assertEqual(x['basis'],'embedded CompositionDefinition.backing_placement_model')
        self.assertEqual(len(x['recordings']),14)

if __name__=='__main__':unittest.main()
