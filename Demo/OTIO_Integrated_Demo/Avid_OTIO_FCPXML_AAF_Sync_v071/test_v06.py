import unittest,tempfile,pathlib,xml.etree.ElementTree as ET
from generate_v06 import export
ROOT=pathlib.Path(__file__).parent
class BridgeTests(unittest.TestCase):
 def test_picture_edit(self):
  with tempfile.TemporaryDirectory() as t:
   report=export(ROOT/'avid_multicam_v12_native_roundtrip.otio',pathlib.Path(t)/'a.fcpxml',pathlib.Path(t)/'report.json')
   xml=ET.parse(pathlib.Path(t)/'a.fcpxml').getroot()
   self.assertEqual(report['timeline_frames'],1406)
   self.assertEqual(report['picture_selections'],11)
   self.assertEqual(report['picture_gaps'],1)
   self.assertEqual(len(report['picture_angle_slots']),9)
   self.assertEqual(len(xml.findall('.//mc-clip')),11)
   self.assertEqual(len(xml.findall('.//mc-angle')),9)
   self.assertEqual(len(xml.findall('.//spine/gap')),1)
   self.assertEqual(len(xml.findall('.//mc-source')),11)
   self.assertEqual(len(report['selection_coverage_warnings']),0)
if __name__=='__main__':unittest.main()
