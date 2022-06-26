from lib import pic
from lib.pic import Note
import math
from xml.etree import ElementTree
import json

def _read_notes(notes, matched, side):
    holds = {}
    subs = {}
    max_time = 0.0
    for xml_node in matched:
        id_ = xml_node.find('m_id').text
        typ = xml_node.find('m_type').text
        time = xml_node.find('m_time').text
        pos = xml_node.find('m_position').text
        width = xml_node.find('m_width').text
        subid = xml_node.find('m_subId').text

        id_, subid = int(id_), int(subid)
        time, pos, width = float(time), float(pos), float(width)
        typ = typ.upper()
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
    xml = ElementTree.fromstring(s)

    name = xml.find('m_path').text
    barpermin = float(xml.find('m_barPerMin').text)
    timeoffset = float(xml.find('m_timeOffset').text)
    leftpad = xml.find('m_leftRegion').text
    rightpad = xml.find('m_rightRegion').text
    mapid = xml.find('m_mapID').text

    chart.name = name
    chart.bar_per_min = barpermin
    chart.time_offset = timeoffset
    chart.left_slide = leftpad.lower() != 'pad'
    chart.right_slide = rightpad.lower() != 'pad'
    chart.map_id = mapid

    bottom_notes = xml.find('m_notes').find('m_notes').findall('CMapNoteAsset')
    left_notes = xml.find('m_notesLeft').find('m_notes').findall('CMapNoteAsset')
    right_notes = xml.find('m_notesRight').find('m_notes').findall('CMapNoteAsset')

    t1 = _read_notes(chart.notes, bottom_notes, Note.SIDE_FRONT)
    t2 = _read_notes(chart.notes, left_notes, Note.SIDE_LEFT)
    t3 = _read_notes(chart.notes, right_notes, Note.SIDE_RIGHT)

    chart.time = math.ceil(max(t1, t2, t3, 1))

    return chart

def _dynamix_read_notes(notes, matched, side):
    holds = {}
    subs = {}
    max_time = 0.0
    for dic in matched:
        id_ = dic['m_id']
        typ = dic['m_type']
        time = dic['m_time']
        pos = dic['m_position']
        width = dic['m_width']
        subid = dic['m_subId']

        if typ == 1:
            typ = Note.NOTE_CHAIN
        elif typ == 2:
            typ = Note.NOTE_HOLD
        elif typ == 3:
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

def read_dynamix(s : dict):
    if not isinstance(s, dict):
        s = json.loads(str(s))

    chart = pic.Chart()
    name = s['m_Name']
    barpermin = s['m_barPerMin']
    timeoffset = s['m_timeOffset']
    leftpad = s['m_leftRegion']
    rightpad = s['m_rightRegion']
    mapid = s['m_mapID']

    chart.name = name
    chart.bar_per_min = barpermin
    chart.time_offset = timeoffset
    chart.left_slide = leftpad == 1
    chart.right_slide = rightpad == 1
    chart.map_id = mapid

    bottom_notes = s['m_notes']['m_notes']
    left_notes = s['m_notesLeft']['m_notes']
    right_notes = s['m_notesRight']['m_notes']

    t1 = _dynamix_read_notes(chart.notes, bottom_notes, Note.SIDE_FRONT)
    t2 = _dynamix_read_notes(chart.notes, left_notes, Note.SIDE_LEFT)
    t3 = _dynamix_read_notes(chart.notes, right_notes, Note.SIDE_RIGHT)

    chart.time = math.ceil(max(t1, t2, t3, 1))

    return chart

def read(chart):
    try:
        _ = ElementTree.fromstring(chart)
        reader = read_dynamite
    except:
        try:
            _ = json.loads(chart)
            reader = read_dynamix
        except:
            raise ValueError(f'Chart is neither XML format nor JSON format.')
    return reader(chart)
