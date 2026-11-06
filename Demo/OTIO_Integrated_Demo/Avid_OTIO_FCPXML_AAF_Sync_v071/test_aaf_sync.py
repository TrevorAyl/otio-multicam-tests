import unittest,json,pathlib
from extract_aaf_picture_sync import derive
P=pathlib.Path(__file__).resolve().parent
class TestBackingSync(unittest.TestCase):
 def test_all_records_grounded(self):
  m,d=derive(json.loads((P/'avid_aaf_structure.json').read_text()),json.loads((P/'avid_multicam_v12_native_roundtrip.otio').read_text()))
  self.assertEqual(len(m['recordings']),12)
  expected={'A01':0,'B01':125,'C01':0,'C02':2002,'D01':300,'E01':200,'F01':0,'F02':1540,'F03':3520,'G01':0,'H01':500,'P01':0}
  self.assertEqual({k:v['sync_start_frame'] for k,v in m['recordings'].items()},expected)
 def test_export_sync_offsets(self):
  import xml.etree.ElementTree as ET
  root=ET.parse(P/'outputs/avid_picture_1406_frames_AAF_SYNC.fcpxml').getroot()
  # source start offsets are in multicam domain; all 12 recordings are represented
  vals={c.attrib['name'].replace('.mov',''):c.attrib['offset'] for c in root.findall('.//mc-angle/asset-clip')}
  self.assertEqual(len(vals),12)
  self.assertEqual(vals['F02'],'308/5s');self.assertEqual(vals['F03'],'704/5s')
if __name__=='__main__':unittest.main()
