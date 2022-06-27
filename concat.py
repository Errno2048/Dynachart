import os
from pathlib import Path
import re
from PIL import Image

from lib.chart import Chart, Song, AudioFile
from lib.reader import read

_Re_preview = re.compile(r'^_?preview', flags=re.IGNORECASE)
_Re_cover = re.compile(r'^_?o?cover', flags=re.IGNORECASE)
_Re_chart = re.compile(r'([BCNHMGT]?)_?((?:[0-9]+)?)\.(?:json|xml)$', flags=re.IGNORECASE)

_Diff_lut = {
    'b': '1Casual',
    'c': '2Casual',
    'n': '3Normal',
    'h': '4Hard',
    'm': '5Mega',
    'g': '6Giga',
    't': '7Tera',
}

def read_dir(path):
    path = Path(path)
    song = Song()
    song.name = path.name
    charts = []
    for file in os.listdir(path):
        if re.search(_Re_preview, file):
            song.preview = AudioFile.from_file(path / file)
        elif file[-3:] == 'mp3':
            song.song = AudioFile.from_file(path / file)
        elif re.search(_Re_cover, file):
            song.cover = Image.open(path / file)
        elif (m := re.search(_Re_chart, file)):
            diff, lv = m.groups()
            diff = _Diff_lut.get(diff.lower(), _Diff_lut['b'])
            if lv:
                lv = int(lv)
            else:
                lv = 0
            with open(path / file, 'r') as f:
                chart_raw = f.read()
            chart = read(chart_raw)
            charts.append((diff, lv, chart))
    for diff, lv, chart in sorted(charts):
        song.charts.append((chart, diff[1:], lv))
    return song

def write_dir(path, song : Song):
    path = Path(path)
    os.makedirs(path, exist_ok=True)
    song.cover.save(path / f'_cover_{song.name}.png')
    song.preview.to(path / f'_preview_{song.name}.mp3')
    song.song.to(path / f'{song.name}.mp3')
    for chart, diff, lv in song.charts:
        chart_raw = chart.to_xml()
        with open(path / f'{song.name}_{diff[0]}_{lv}.xml', 'w') as f:
            f.write(chart_raw)

def _chart_from_song(song, diff):
    chart, new_diff, new_lv = song.charts[-1]
    if isinstance(diff, str):
        for chart, diff, lv in song.charts:
            if diff.lower().startswith(diff.lower()):
                chart = chart
                new_diff = diff
                new_lv = lv
    elif isinstance(diff, int):
        chart, new_diff, new_lv = song.charts[diff]
    return chart, new_diff, new_lv


def concat(song1 : Song, song2: Song, diff1=None, diff2=None):
    chart1, new_diff, new_lv = _chart_from_song(song1, diff1)
    chart2, *_ = _chart_from_song(song2, diff2)

    audio1 = song1.song
    audio2 = song2.song

    new_chart = Chart.concatenate(chart1, chart2, audio1.duration)
    new_audio = audio1.clone()
    new_audio.concat(audio2)

    new_song = Song()
    new_song.name = song1.name
    new_song.cover = song1.cover
    new_song.preview = song1.preview
    new_song.song = new_audio
    new_song.charts = [(new_chart, new_diff, new_lv)]
    return new_song

def clip(song, diff, start, end, fade=None):
    chart, diff, lv = _chart_from_song(song, diff)
    bps = chart.bar_per_min / 60
    start_sec = start / bps
    end_sec = end / bps

    new_audio : AudioFile = song.song.clone()
    new_chart : Chart = chart.clip(start, end)
    if fade and fade > 0:
        fade_sec = fade / bps
        new_audio.fade_in(start_sec - fade_sec, start_sec)
        new_audio.fade_out(end_sec, end_sec + fade_sec)
        new_audio = new_audio.clip(start_sec - fade_sec, end_sec + fade_sec)
        new_chart.move(fade)

    new_song = Song()
    new_song.name = song.name
    new_song.cover = song.cover
    new_song.preview = song.preview
    new_song.song = new_audio
    new_song.charts = [(new_chart, diff, lv)]
    return new_song

if __name__ == '__main__':
    import argparse, sys

    parser = argparse.ArgumentParser()

    def get_arg(lst, index):
        if index >= len(lst):
            return None
        return lst[index]

    lst_args = sys.argv[1:]

    command = get_arg(lst_args, 0)

    if command == 'concat':
        command_parser = argparse.ArgumentParser()

        parser.add_argument('target', metavar='path', type=str,
                            help='Target directory.')
        parser.add_argument('source', metavar='path', type=str, nargs='+',
                            help='Source directories.')

        args = parser.parse_args(lst_args[1:])

        songs = []
        for path in args.source:
            songs.append(read_dir(path))

        res = songs[0]
        for song in songs[1:]:
            res = concat(res, song)

        write_dir(args.target, res)

    elif command == 'clip':
        command_parser = argparse.ArgumentParser()

        parser.add_argument('target', metavar='path', type=str,
                            help='Target directory.')
        parser.add_argument('source', metavar='path', type=str,
                            help='Source directory.')
        parser.add_argument('start', metavar='bar', type=float,
                            help='Start bar time.')
        parser.add_argument('end', metavar='bar', type=float,
                            help='End bar time.')
        parser.add_argument('--fade', '-f', metavar='bar', type=float, default=1.0,
                            help='To apply fade in and fade out.')

        args = parser.parse_args(lst_args[1:])

        song = read_dir(args.source)
        res = clip(song, None, args.start, args.end, args.fade)
        write_dir(args.target, res)
