#!/usr/bin/env python3
"""Check unchanged frozen v0.7.2 files against their release hashes and XML invariants."""
from pathlib import Path
import hashlib, xml.etree.ElementTree as ET
root=Path(__file__).resolve().parent
for line in (root/'SHA256SUMS.txt').read_text().splitlines():
    sha, rel=line.split('  ', 1)
    f=root/rel
    assert f.is_file() and hashlib.sha256(f.read_bytes()).hexdigest()==sha, rel
x=ET.parse(root/'adapter_v072/outputs/avid_picture_enriched_sync.fcpxml').getroot()
assert len(x.findall('.//mc-angle'))==9
assert len(x.findall('.//mc-angle/asset-clip'))==12
assert len(x.findall('.//mc-clip'))==11
assert len(x.findall('.//spine/gap'))==1
assert x.find('.//sequence').get('duration')=='1406/25s'
print('Frozen release SHA-256 and picture XML checks PASSED')
