import json

_Xml_head = """<?xml version="1.0" encoding="UTF-8" ?>
<CMap xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">"""

_Xml_tail = """</CMap>"""

_Xml_notes = """<m_notes>"""
_Xml_notes_tail = """</m_notes>"""

_Xml_notes_bottom = """<m_notes>"""
_Xml_notes_bottom_tail = """</m_notes>"""

_Xml_notes_left = """<m_notesLeft>"""
_Xml_notes_left_tail = """</m_notesLeft>"""

_Xml_notes_right = """<m_notesRight>"""
_Xml_notes_right_tail = """</m_notesRight>"""

_Xml_meta_info = """<m_path>{title}</m_path>
<m_barPerMin>{bpm:.5f}</m_barPerMin>
<m_timeOffset>{offset}</m_timeOffset>
<m_leftRegion>{left_type}</m_leftRegion>
<m_rightRegion>{right_type}</m_rightRegion>
<m_mapID>{map_id}</m_mapID>"""

_Xml_note_info = """<CMapNoteAsset>
<m_id>{id}</m_id>
<m_type>{type}</m_type>
<m_time>{time}</m_time>
<m_position>{position}</m_position>
<m_width>{width}</m_width>
<m_subId>{sub_id}</m_subId>
<status>Perfect</status>
</CMapNoteAsset>
"""

_Dic_region_type = {
    0: 'MULTI',
    1: 'MIXER',
    2: 'PAD',
}

_Dic_note_type = {
    0: 'NORMAL',
    1: 'CHAIN',
    2: 'HOLD',
    3: 'SUB',
}

def _get_meta_info(dic):
    name = dic['m_Name']
    if name[-2:] in ('_B', '_N', '_H', '_M', '_G'):
        name = name[:-2]
    return dict(
        title = name,
        map_id = dic['m_mapID'],
        bpm = dic['m_barPerMin'],
        offset = dic['m_timeOffset'],
        left_type = _Dic_region_type.get(dic['m_leftRegion'], _Dic_region_type[0]),
        right_type = _Dic_region_type.get(dic['m_rightRegion'], _Dic_region_type[0]),
    )

def _get_note_info(dic):
    return dict(
        id = dic['m_id'],
        type = _Dic_note_type.get(dic['m_type'], _Dic_note_type[0]),
        time = dic['m_time'],
        position = dic['m_position'],
        width = dic['m_width'],
        sub_id = dic['m_subId'],
    )

def convert_json(s : dict):
    if not isinstance(s, dict):
        dic = json.loads(s)
    else:
        dic = s
    meta_dict = _get_meta_info(dic)
    bottom_notes = dic['m_notes']['m_notes']
    left_notes = dic['m_notesLeft']['m_notes']
    right_notes = dic['m_notesRight']['m_notes']

    bottom = f"""{_Xml_notes_bottom}
{_Xml_notes}
{''.join((_Xml_note_info.format(**_get_note_info(n)) for n in bottom_notes))}{_Xml_notes_tail}
{_Xml_notes_bottom_tail}"""
    left = f"""{_Xml_notes_left}
{_Xml_notes}
{''.join((_Xml_note_info.format(**_get_note_info(n)) for n in left_notes))}{_Xml_notes_tail}
{_Xml_notes_left_tail}"""
    right = f"""{_Xml_notes_right}
{_Xml_notes}
{''.join((_Xml_note_info.format(**_get_note_info(n)) for n in right_notes))}{_Xml_notes_tail}
{_Xml_notes_right_tail}"""

    return f"""{_Xml_head}
{_Xml_meta_info.format(**meta_dict)}
{bottom}
{left}
{right}
{_Xml_tail}""", meta_dict['map_id']

if __name__ == '__main__':
    import sys, os
    args = sys.argv[1:]
    for file in args:
        if os.path.isfile(file):
            try:
                with open(file, 'r') as f:
                    s = f.read()
                res, map_id = convert_json(s)
                with open(f'{os.path.dirname(os.path.abspath(file))}/{map_id}.xml', 'w') as f:
                    f.write(res)
            except Exception as e:
                print(file, e)
                continue