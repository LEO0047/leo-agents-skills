#!/usr/bin/env python3
"""Build an FCPXML 1.10 timeline (Final Cut Pro 10.6+ / DaVinci Resolve 18+) from the cut list in harness/director.js.

Every shot becomes its own clip on the timeline (all pointing into the no-music master),
with the music as a connected audio clip, so the edit can be re-timed or re-ordered in an NLE.

  python3 make_fcpxml.py --director harness/director.js --frames 1443 \
      "/Users/me/Downloads/Reel/noMusic.mp4" "/Users/me/Downloads/track.mp3" out.fcpxml

Media paths must be the absolute paths on the machine that will open the timeline.
"""
import argparse, re, urllib.parse, os
from xml.sax.saxutils import quoteattr

FPS, NF = 60, 1443


def shots(director):
    src = open(director, encoding='utf-8').read()
    out = []
    for m in re.finditer(r"\{ id: '([^']+)'(?:, name: '([^']+)')?, f0: (\d+)", src):
        out.append([m.group(1), m.group(2) or '', int(m.group(3))])
    out.sort(key=lambda s: s[2])
    for i, s in enumerate(out):
        s.append(out[i + 1][2] if i + 1 < len(out) else NF)
    return out


def t(fr):
    return '0s' if fr == 0 else f'{fr}/{FPS}s'


def url(p):
    return 'file://' + urllib.parse.quote(p)


def main(director, video, music, dst):
    cl = []
    for i, (sid, name, f0, f1) in enumerate(shots(director)):
        label = f'{sid} {name}'.strip()
        inner = ''
        if i == 0:
            inner = f'\n              <asset-clip ref="r3" lane="-1" offset="0s" start="0s" duration="{t(NF)}" name="MUSIC" audioRole="music"/>\n            '
        cl.append(f'            <asset-clip ref="r2" offset="{t(f0)}" name={quoteattr(label)} start="{t(f0)}" duration="{t(f1 - f0)}" format="r1" tcFormat="NDF">'
                  f'{inner}<marker start="{t(f0)}" duration="1/60s" value={quoteattr(label)}/></asset-clip>')
    xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE fcpxml>
<fcpxml version="1.10">
  <resources>
    <format id="r1" name="FFVideoFormat1080x1920p60" frameDuration="1/60s" width="1080" height="1920" colorSpace="1-1-1 (Rec. 709)"/>
    <asset id="r2" name="ThermalReel_noMusic" start="0s" duration="{t(NF)}" hasVideo="1" format="r1" videoSources="1">
      <media-rep kind="original-media" src="{url(video)}"/>
    </asset>
    <asset id="r3" name="music" start="0s" duration="{t(NF)}" hasAudio="1" audioSources="1" audioChannels="2" audioRate="48000">
      <media-rep kind="original-media" src="{url(music)}"/>
    </asset>
  </resources>
  <library>
    <event name="Web Tool Reel">
      <project name="REEL">
        <sequence format="r1" duration="{t(NF)}" tcStart="0s" tcFormat="NDF" audioLayout="stereo" audioRate="48k">
          <spine>
{chr(10).join(cl)}
          </spine>
        </sequence>
      </project>
    </event>
  </library>
</fcpxml>
'''
    open(dst, 'w', encoding='utf-8').write(xml)
    print('wrote', dst, len(cl), 'clips')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--director', required=True)
    ap.add_argument('--frames', type=int, default=1443)
    ap.add_argument('--fps', type=int, default=60)
    ap.add_argument('video'); ap.add_argument('music'); ap.add_argument('out')
    a = ap.parse_args()
    FPS, NF = a.fps, a.frames
    main(a.director, a.video, a.music, a.out)
