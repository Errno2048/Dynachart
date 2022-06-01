import re
from lib import pic
from lib.pic import Note
import math


_re_dynamite_info = re.compile(
    r'<m_path>([^<]+)</m_path>\s*'
    r'<m_barPerMin>([^<]+)</m_barPerMin>\s*'
    r'<m_timeOffset>([^<]+)</m_timeOffset>\s*'
    r'<m_leftRegion>([^<]+)</m_leftRegion>\s*'
    r'<m_rightRegion>([^<]+)</m_rightRegion>\s*'
    r'<m_mapID>([^<]+)</m_mapID>\s*'
)

_re_dynamite_note = re.compile(
    r'<CMapNoteAsset>\s*'
    r'<m_id>([^<]+)</m_id>\s*'
    r'<m_type>([^<]+)</m_type>\s*'
    r'<m_time>([^<]+)</m_time>\s*'
    r'<m_position>([^<]+)</m_position>\s*'
    r'<m_width>([^<]+)</m_width>\s*'
    r'<m_subId>([^<]+)</m_subId>\s*'
    r'<status>([^<]+)</status>\s*'
    r'</CMapNoteAsset>'
)

def _read_notes(notes, matched, side):
    holds = {}
    subs = {}
    max_time = 0.0
    for id_, typ, time, pos, width, subid, status in matched:
        id_, subid = int(id_), int(subid)
        time, pos, width = float(time), float(pos), float(width)
        if typ == 'CHAIN':
            typ = Note.NOTE_CHAIN
        elif typ == 'HOLD':
            typ = Note.NOTE_HOLD
        elif typ == 'SUB':
            subs[id_] = time
            continue
        else:
            typ = Note.NOTE_NORMAL
        note = Note(pos, type=typ, width=width, start=time, side=side)
        if typ == Note.NOTE_HOLD:
            holds[id_] = (note, subid)
        notes.append(note)
        max_time = max(max_time, time)
    for note, subid in holds.values():
        sub = subs.get(subid, None)
        if sub is not None:
            note.end = sub
    return max_time

def read_dynamite(s):
    chart = pic.Chart()
    m = re.search(_re_dynamite_info, s)
    if not m:
        return None

    name, barpermin, timeoffset, leftpad, rightpad, mapid = m.groups()
    barpermin, timeoffset = float(barpermin), float(timeoffset)
    chart.bar_per_min = barpermin
    chart.time_offset = timeoffset
    chart.left_slide = leftpad.lower() != 'pad'
    chart.right_slide = rightpad.lower() != 'pad'
    leftpos = s.find('m_notesLeft')

    rightpos = s.find('m_notesRight')
    if leftpos < 0 or rightpos < 0:
        return None

    t1 = _read_notes(chart.notes, re.findall(_re_dynamite_note, s[:leftpos]), Note.SIDE_FRONT)
    t2 = _read_notes(chart.notes, re.findall(_re_dynamite_note, s[leftpos:rightpos]), Note.SIDE_LEFT)
    t3 = _read_notes(chart.notes, re.findall(_re_dynamite_note, s[rightpos:]), Note.SIDE_RIGHT)

    chart.time = math.ceil(max(t1, t2, t3, 1))

    return chart
