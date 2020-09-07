# -*- coding: utf-8 -*-
#
# Copyright (C) 2010-2016 Thomas Amland
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import re
import xbmc
import requests
from io import BytesIO


def get_subtitles(video_id):
    vtt_sub_url = "https://undertekst.nrk.no/prod/%s/%s/%s/TTV/%s.vtt" % (video_id[0:6], video_id[6:8], video_id, video_id)
    ttml_sub_url = "https://undertekst.nrk.no/prod/%s/%s/%s/TMP/%s.ttml" % (video_id[0:6], video_id[6:8], video_id, video_id)
    print ttml_sub_url
    html = requests.get(ttml_sub_url).text
    if not html:
        return None

    content = _ttml_to_srt(html)
    filename = os.path.join(xbmc.translatePath("special://temp"), 'nor.srt')
    with open(filename, 'w') as f:
        f.write(content)
    return filename


def _ttml_to_srt(ttml):
    lines = re.compile(r'<p begin="(.*?)" dur="(.*?)".*?>(.*?)</p>',
                           re.DOTALL).findall(ttml)

    # drop copyright line
    if len(lines) > 0 and lines[0][2].lower().startswith('copyright'):
        lines.pop(0)

    subtitles = []
    for start, duration, text in lines:
        start = _str_to_time(start)
        duration = _str_to_time(duration)
        end = start + duration
        subtitles.append((start, end, text))

    # fix overlapping
    for i in xrange(0, len(subtitles) - 1):
        start, end, text = subtitles[i]
        start_next, _, _ = subtitles[i + 1]
        subtitles[i] = (start, min(end, start_next - 1), text)

    output = BytesIO()
    for i, (start, end, text) in enumerate(subtitles):
        text = text.replace('<span style="italic">', '<i>') \
            .replace('</span>', '</i>') \
            .replace('&amp;', '&') \
            .split()
        text = ' '.join(text)
        text = re.sub('<br />\s*', '\n', text)
        text = text.encode('utf-8')

        output.write(str(i + 1))
        output.write('\n%s' % _time_to_str(start))
        output.write(' --> %s\n' % _time_to_str(end))
        output.write(text)
        output.write('\n\n')

    return output.getvalue()


def _str_to_time(txt):
    p = txt.split(':')
    try:
        ms = float(p[2])
    except ValueError:
        ms = 0
    return int(p[0]) * 3600 + int(p[1]) * 60 + ms


def _time_to_str(time):
    return '%02d:%02d:%02d,%03d' % (time / 3600, (time % 3600) / 60, time % 60, (time % 1) * 1000)
