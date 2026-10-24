# otio-multicam-tests
Synthetic multicam interchange test projects for Avid, Premiere Pro, DaVinci Resolve and OpenTimelineIO

## Purpose:

Attempt to provide Multicam sequences from 3 major NLEs to help develop interchange via OTIO further to https://github.com/AcademySoftwareFoundation/OpenTimelineIO/issues/427

## NLE versions:

Avid Media Composer 2025.12.1
Adobe Premiere 27.1.0 BETA (Build 24)
DaVinci Resolve 21.1.1 Build 10

Media generated to simulate different camera angles, source timecodes, audio configurations, groups and nested graphics that might be found in a Multicam edit.

Download the media from https://github.com/TrevorAyl/otio-multicam-tests/releases/tag/1.0, unzip, open the native projects, relink to this media folder and export.


## Current results:

AVID:
AAF - imports correctly, with Multicam groups preserved, linked to media 
OTIO - imports flattened, not linked to media

PP:
AAF - imports as flattened but some file audio channel configurations have been changed and cannot relink. 
OTIO - multicam groups are now nested sequences - incorrect audio tracks and cannot successfully be reconstructed. 

Resolve:
AAF - imports but doesn’t seem to retain file names, paths etc. 
OTIO - pretty much the same as AAF - has more information in the name


## Known differences:

The projects are as close as practical, but not necessarily frame-identical.

In Premiere and Resolve the graphics fill and key clips are nested as one angle - in Avid they are 2 angles that are composited and then nested. 

There are export folders within each NLE with an H265 and an OTIO, EDL, AAF etc. 



