from PIL import Image
import UnityPy as unity
import pydub
import librosa
import soundfile
import numpy as np
import os
import json

from lib.dynamix2dynamite import convert_json

def wav_file_clip(path, start, end, fadein=None, fadeout=None, sr=None):
    audio, sample_rate = librosa.load(path, sr=sr)
    audio : np.ndarray = audio.copy()
    length = audio.shape[0]
    start = int(max(start, 0) * sample_rate)
    end = min(int(end * sample_rate), length)

    clip_start = start
    if fadein is not None:
        fadein = int(fadein * sample_rate)
        fadein = min(fadein, start)
        clip_start = start - fadein
        fadein_curve = np.linspace(0.0, 1.0, fadein)
        audio[clip_start : start] = audio[clip_start : start] * fadein_curve

    clip_end = end
    if fadeout is not None:
        fadeout = int(fadeout * sample_rate)
        fadeout = min(fadeout, length - end)
        clip_end = end + fadeout
        fadeout_curve = np.linspace(1.0, 0.0, fadeout)
        audio[end : clip_end] = audio[end : clip_end] * fadeout_curve

    clip = audio[clip_start : clip_end]
    return clip, sample_rate

def get_source_file(folder):
    dirs = os.listdir(folder)
    assert len(dirs) == 1
    file = f'{folder}/{dirs[0]}/__data'
    return file

def get_songlist(folder):
    songlist_folder = f'{folder}/_songlist'
    songlist_file = get_source_file(songlist_folder)
    src = unity.load(songlist_file)
    dic_m_list = None
    for obj in src.objects:
        if obj.type.name == 'MonoBehaviour' and obj.serialized_type.nodes:
            dic = obj.read_typetree()
            if dic['m_Name'] == 'SongList':
                dic_m_list = dic['m_list']
                break
    assert dic_m_list is not None, 'Corrupted song list file'
    songlist = dic_m_list['Songs']
    return songlist

def extract_song(path):
    file = get_source_file(path)
    src = unity.load(file)
    for obj in src.objects:
        if obj.type.name == 'AudioClip':
            obj = obj.read()
            samples = obj.samples
            assert len(samples) == 1, f'Invalid AudioClip samples with size {len(samples)}'
            return (obj.name, *list(samples.items())[0])
    assert False, f'Cannot find AudioClip in {path}'

def extract_cover(path):
    file = get_source_file(path)
    src = unity.load(file)
    for obj in src.objects:
        if obj.type.name == 'Sprite':
            obj = obj.read()
            return obj.name, obj.image
    assert False, f'Cannot find Sprite in {path}'

def extract_map(path):
    file = get_source_file(path)
    src = unity.load(file)
    for obj in src.objects:
        if obj.type.name == 'MonoBehaviour' and obj.serialized_type.nodes:
            obj = obj.read_typetree()
            if 'm_notes' in obj:
                return obj
    assert False, f'Cannot find MonoBehaviour with m_notes in {path}'

def extract(song_dict, src, dst):
    if not os.path.isdir(dst):
        if os.path.isfile(dst):
            os.remove(dst)
        os.makedirs(dst)

    path_song = song_dict['id']
    path_preview = song_dict['PreviewAudio']['id']
    path_cover = song_dict['Cover']['id']

    name_song, _file_song, data_song = extract_song(f'{src}/{path_song}')
    name_preview, _file_preview, data_preview = extract_song(f'{src}/{path_preview}')
    file_cover, image_cover = extract_cover(f'{src}/{path_cover}')

    image_cover : Image.Image
    image_cover.save(f'{dst}/{file_cover}.png')
    file_song = f'{dst}/{_file_song}'
    with open(file_song, 'wb') as f:
        f.write(data_song)
    file_preview = f'{dst}/{_file_preview}'
    with open(file_preview, 'wb') as f:
        f.write(data_preview)

    wav_song = pydub.AudioSegment.from_wav(file_song)
    wav_song.export(f'{dst}/{name_song}.mp3', format='mp3')
    wav_preview = pydub.AudioSegment.from_wav(file_preview)
    wav_preview.export(f'{dst}/{name_preview}.mp3', format='mp3')

    maps = song_dict['Maps']
    res_maps = []
    for _map in maps:
        map_id = _map['id']
        map_level = _map['level']
        map_level_name = _map['LevelName']
        map_dict = extract_map(f'{src}/{map_id}')
        with open(f'{dst}/{map_id}.json', 'w') as f:
            json.dump(map_dict, f)
        map_xml, _ = convert_json(map_dict)
        with open(f'{dst}/{map_id}_{map_level}.xml', 'w') as f:
            f.write(map_xml)
        res_maps.append({
            'id': map_id,
            'level': map_level,
            'level_name': map_level_name,
            'map': map_dict,
        })

    return {
        'song': {
            'name': name_song,
            'file': _file_song,
            'data': data_song,
        },
        'preview': {
            'name': name_preview,
            'file': _file_preview,
            'data': data_preview,
        },
        'cover': {
            'name': file_cover,
            'data': image_cover,
        },
        'maps': res_maps,
    }

def extract_clip(song_dict, src, dst, start_time, end_time, fade=4, level=None, align=64, use_bar=True):
    if not os.path.isdir(dst):
        if os.path.isfile(dst):
            os.remove(dst)
        os.makedirs(dst)

    data = extract(song_dict, src, f'{dst}_origin')
    name_song, _file_song, data_song = data['song']['name'], data['song']['file'], data['song']['data']
    name_preview, _file_preview, data_preview = data['preview']['name'], data['preview']['file'], data['preview']['data']
    file_cover, image_cover = data['cover']['name'], data['cover']['data']

    image_cover : Image.Image
    image_cover.save(f'{dst}/{file_cover}.png')

    file_song_origin = f'{dst}/{_file_song}_origin.wav'
    with open(file_song_origin, 'wb') as f:
        f.write(data_song)
    file_preview = f'{dst}/{_file_preview}'
    with open(file_preview, 'wb') as f:
        f.write(data_preview)

    maps = data['maps']
    assert maps, 'Empty maps'
    target_map = maps[-1]
    if level is not None:
        for _map in maps:
            if _map['level_name'] == level:
                target_map = _map
    map_id, map_level, map_dict = target_map['id'], target_map['level'], target_map['map']
    bar_per_sec = map_dict['m_barPerMin'] / 60
    if use_bar:
        bar_start_time = start_time
        bar_end_time = end_time
        start_time = bar_start_time / bar_per_sec
        end_time = bar_end_time / bar_per_sec
    else:
        bar_start_time = bar_per_sec * start_time
        bar_end_time = bar_per_sec * end_time
    if align:
        bar_start_time = round(bar_start_time * align) / align
        bar_end_time = round(bar_end_time * align) / align
        start_time = bar_start_time / bar_per_sec
        end_time = bar_end_time / bar_per_sec

    fade_time = fade / bar_per_sec

    clip_song, sr = wav_file_clip(file_song_origin, start_time, end_time, fade_time, fade_time)
    file_song = f'{dst}/{_file_song}'
    soundfile.write(file_song, clip_song, sr)
    wav_song = pydub.AudioSegment.from_wav(file_song)
    wav_song.export(f'{dst}/{name_song}.mp3', format='mp3')
    wav_preview = pydub.AudioSegment.from_wav(file_preview)
    wav_preview.export(f'{dst}/{name_preview}.mp3', format='mp3')

    map_dict = map_dict.copy()
    for note_name in ('m_notes', 'm_notesLeft', 'm_notesRight'):
        notes = map_dict[note_name]['m_notes']
        new_notes = []
        hold_subs = {}
        for note in notes:
            note : dict
            m_time = note['m_time']
            if bar_start_time <= m_time and m_time <= bar_end_time:
                note['m_time'] = round((m_time - max(0, bar_start_time - fade)) * 100000) / 100000
                note['m_position'] = round(note['m_position'] * 100000) / 100000
                note['m_width'] = round(note['m_width'] * 100000) / 100000
                new_notes.append(note)
                if note['m_type'] == 2:
                    # hold
                    hold_sub = hold_subs.setdefault(note['m_subId'], [None, None])
                    hold_sub[0] = note
                elif note['m_type'] == 3:
                    # sub
                    hold_sub = hold_subs.setdefault(note['m_id'], [None, None])
                    hold_sub[1] = note
        for k, v in hold_subs.items():
            hold, sub = v
            if hold is None:
                # change to chain
                sub['m_type'] = 1
            elif sub is None:
                # change to normal
                hold['m_type'] = 0
                hold['m_subId'] = -1
        map_dict[note_name]['m_notes'] = new_notes

    with open(f'{dst}/{map_id}.json', 'w') as f:
        json.dump(map_dict, f)
    map_xml, _ = convert_json(map_dict)
    with open(f'{dst}/{map_id}_{map_level}.xml', 'w') as f:
        f.write(map_xml)

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(add_help=False)

    parser.add_argument('source', metavar='name', nargs=1, type=str, help='Android/data/com.c4cat.dynamix/files/UnityCache/Shared')
    parser.add_argument('song', metavar='name', nargs='?', default=None, type=str, help='The song to be extracted. Show song list when not passed.')
    parser.add_argument('target', metavar='dir', nargs='?', default=None, type=str, help='The target directory.')
    parser.add_argument('--clip', '-c', metavar=('start', 'end'), type=float, nargs=2, default=None, help='To clip the chart and the song.')
    parser.add_argument('--fade', '-f', metavar='bar', type=float, default=1.0, help='To apply fade in and fade out.')
    parser.add_argument('--align', '-a', metavar='a', type=float, default=4.0, help='To align with 1/a bar size.')
    parser.add_argument('--level', '-l', metavar='lv', type=int, default=None, help='The chart level to be clipped. Casual is 0 and Giga is 4. The highest level will be automatically chosen if not provided.')

    args = parser.parse_args()

    src = args.source[0]
    songlist = get_songlist(src)

    song = args.song

    if song is None:
        for index, song_info in enumerate(songlist):
            id_name = song_info['id'][6:]
            name = song_info['Name']
            print(f'{index}:{id_name}:"{name}"')
    else:
        target = args.target
        if target is None:
            target = f'{os.path.abspath(os.path.curdir)}/{song}'
        song_index = None
        for index, song_info in enumerate(songlist):
            id_name = song_info['id'][6:]
            name = song_info['Name']
            if id_name == song or name == song:
                song_index = index
                break
        if song_index is None:
            print(f'Cannot find {song}.')
        else:
            s = songlist[song_index]
            if args.clip is None:
                extract(s, src, target)
            else:
                clip_start, clip_end = args.clip
                extract_clip(s, src, target, clip_start, clip_end, fade=args.fade, align=args.align, level=args.level)