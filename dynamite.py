import os, shutil
import re
import json

import uuid

def random_uuid():
    return str(uuid.uuid4()).replace('-', '')[:24].lower()

def path_escape(s):
    return re.sub(r'\t\\/:\*\?"<>\|', '', s)

_Re_list = re.compile(
    r'B\.(?P<id>.*)[\r\n]+'
    r'(?P<hidden>Y\?1[\r\n]+|)'
    r'(?P<ranked>R\?1[\r\n]+|)'
    r'N\?(?P<name>.*)[\r\n]+'
    r'S\?(?P<song>.*)[\r\n]+'
    r'C\?(?P<cover>.*)[\r\n]+'
    r'P\?(?P<preview>.*)[\r\n]+'
    r'U\?(?P<charter>.*)[\r\n]+'
    r'W\?(?P<artist>.*)[\r\n]+'
    r'I\?(?P<desc>.*)[\r\n]+'
    r'H\?(?P<difficulties>.*)[\r\n]+'
    r'M\?(?P<charts>.*)[\r\n]+'
    r'E\.'
)

_Re_difficulties = re.compile(r'(?P<name>[A-Za-z0-9]*),(?P<level>[\-A-Za-z0-9]*);')
_Re_charts = re.compile(r'(?P<file>[^;]*);')

_Re_read_chart_dir_chart = re.compile(r'_(?P<diff>[BCNHMGTbcnhmgt])(?P<lv>_[0-9]+|)\.[Xx][Mm][Ll]$')
_Re_read_chart_dir_cover = re.compile(r'^(?:_o?)?cover')
_Re_read_chart_dir_preview = re.compile(r'^_?preview')

def _diff2lvname(s):
    s = s.upper()
    if s == 'B' or s == 'C' or s == '1':
        return '1CASUAL'
    if s == 'N' or s == '2':
        return '2NORMAL'
    if s == 'H' or s == '3':
        return '3HARD'
    if s == 'M' or s == '4':
        return '4MEGA'
    if s == 'G' or s == '5':
        return '5GIGA'
    if s == 'T' or s == '6':
        return '6TERA'
    return '0TUTORIAL'

def read_chart_dir(src, name, *, artist=None, charter=None, desc=None, id=None, ranked=False, with_dir=True):
    files = os.listdir(src)
    dir_name = os.path.basename(src)
    charts = []
    song = None
    preview = None
    cover = None
    song_name = name
    for name in files:
        _ext = name[-4:]
        if _ext == '.xml':
            m = re.search(_Re_read_chart_dir_chart, name)
            if m:
                diff, lv = m.groups()
                if lv:
                    lv = int(lv[1:])
                else:
                    lv = 0
                charts.append({
                    'difficulty': _diff2lvname(diff),
                    'level': lv,
                    'file': f'{dir_name}/{name}' if with_dir else name,
                })
        elif _ext == '.mp3':
            if re.search(_Re_read_chart_dir_preview, name):
                preview = name
            else:
                song = name
        elif _ext == '.rnx':
            subext = name[-9:-4]
            if subext[0] == 'a':
                song = name
            elif subext[0] == 'b':
                preview = name
            elif subext[0] == 'c':
                cover = name
            elif subext[1:] == '.xml':
                lv = 0
                diff = subext[0]
                charts.append({
                    'difficulty': _diff2lvname(diff),
                    'level': lv,
                    'file': f'{dir_name}/{name}' if with_dir else name,
                })
        else:
            if re.search(_Re_read_chart_dir_cover, name):
                cover = name
    charts.sort(key=lambda x: x['difficulty'])
    for chart in charts:
        chart['difficulty'] = chart['difficulty'][1:]
    if not song or not preview or not cover or not charts:
        return None
    return {
        'id': random_uuid() if id is None else id,
        'ranked': ranked,
        'name': song_name,
        'song': f'{dir_name}/{song}' if with_dir else song,
        'cover': f'{dir_name}/{cover}' if with_dir else cover,
        'preview': f'{dir_name}/{preview}' if with_dir else preview,
        'charter': charter if charter else '-',
        'artist': artist if artist else '-',
        'desc': desc if desc else '',
        'charts': charts,
    }

def read_list(s):
    lst = []
    for id_, ranked, name, song, cover, preview, charter, artist, desc, difficulties, charts in re.findall(_Re_list, s):
        diffs = re.findall(_Re_difficulties, difficulties)
        charts = re.findall(_Re_charts, charts)
        if len(diffs) != len(charts):
            print(f'Corrupted item: {id_}:{name}')
            continue
        _charts = []
        for (k, level), file in zip(diffs, charts):
            _charts.append({
                'difficulty': k,
                'level': level,
                'file': file,
            })
        json_dic = {
            'id': id_,
            'ranked': bool(ranked),
            'name': name,
            'song': song,
            'cover': cover,
            'preview': preview,
            'charter': charter,
            'artist': artist,
            'desc': desc,
            'charts': _charts
        }
        lst.append(json_dic)
    return lst

def force_mkdir(path):
    if os.path.exists(path):
        if os.path.isfile(path):
            os.remove(path)
        else:
            return
    os.makedirs(path)

def force_remove(path):
    if os.path.isfile(path):
        os.remove(path)
    elif os.path.isdir(path):
        shutil.rmtree(path)

def force_copy(src, dst):
    if not os.path.exists(src):
        return
    parent_dir = os.path.dirname(os.path.abspath(dst))
    force_mkdir(parent_dir)
    force_remove(dst)
    if os.path.isfile(src):
        shutil.copyfile(src, dst)
    else:
        shutil.copytree(src, dst)

def json_dict_to_list_file(lst):
    res = []
    for dic in lst:
        data = [f'B.{dic["id"]}']
        if dic['ranked']:
            data.append('R?1')
        data.append(f'N?{dic["name"]}')
        data.append(f'S?{dic["song"]}')
        data.append(f'C?{dic["cover"]}')
        data.append(f'P?{dic["preview"]}')
        data.append(f'U?{dic["charter"]}')
        data.append(f'W?{dic["artist"]}')
        data.append(f'I?{dic["desc"]}')
        charts = dic['charts']
        diffs = []
        _charts = []
        for chart in charts:
            diffs.append(f'{chart["difficulty"]},{chart["level"]};')
            _charts.append(f'{chart["file"]};')
        data.append(f'H?{"".join(diffs)}')
        data.append(f'M?{"".join(_charts)}')
        data.append('E.\n')
        res.append('\n'.join(data))
    res.append('')
    return '\n'.join(res)

def _id_rename(dic):
    return path_escape(f'{dic["name"]}_{dic["charter"]}')

def sort_out(lst, src, dst, rename=False):
    abs_src = os.path.abspath(src)
    abs_dst = os.path.abspath(dst)
    new_lst = []
    for dic in lst:
        new_dic = dic.copy()
        id_ = _id_rename(dic) if rename else dic['id']
        new_dic['id'] = id_
        name = dic['name']
        dst_folder = id_
        song, cover, preview = dic['song'], dic['cover'], dic['preview']
        charts = dic['charts']
        chart_files = []
        new_charts = []
        for chart in charts:
            f = chart['file']
            chart_files.append(f)
            new_chart = chart.copy()
            new_chart['file'] = f'{dst_folder}/{f}'
            new_charts.append(new_chart)
        path_dst = os.path.join(abs_dst, dst_folder)
        force_mkdir(path_dst)
        for f in (song, cover, preview, *chart_files):
            shutil.copyfile(os.path.join(abs_src, f), os.path.join(path_dst, f))
        new_dic['song'] = f'{dst_folder}/{song}'
        new_dic['cover'] = f'{dst_folder}/{song}'
        new_dic['preview'] = f'{dst_folder}/{preview}'
        new_dic['charts'] = new_charts
        new_lst.append(new_dic)
    new_list_file = json_dict_to_list_file(new_lst)
    with open(os.path.join(abs_dst, '__rena_index_2'), 'w', encoding='utf8') as f:
        f.write(new_list_file)
    with open(os.path.join(abs_dst, '__rena_index_2.json'), 'w', encoding='utf8') as f:
        json.dump(new_lst, f, indent=2)
    return new_lst

def get_list(src):
    abs_src = os.path.abspath(src)
    with open(os.path.join(abs_src, '__rena_index_2'), 'r', encoding='utf8') as f:
        s_list = f.read()
    lst = read_list(s_list)
    return lst

def sort_dir(src, dst, rename=False):
    lst = get_list(src)
    return sort_out(lst, src, dst, rename=rename)

def merge_list(src1, src2):
    lst1 = get_list(src1)
    lst2 = get_list(src2)

    ids = set()
    for dic in lst1:
        ids.add(dic['id'])

    for dic in lst2:
        if dic['id'] in ids:
            continue
        charts = dic['charts']
        chart_files = map(lambda x: x['file'], charts)
        for f in (dic['song'], dic['cover'], dic['preview'], *chart_files):
            force_copy(os.path.join(src2, f), os.path.join(src1, f))
        lst1.append(dic)
    with open(os.path.join(src1, '__rena_index_2'), 'w', encoding='utf8') as f:
        f.write(json_dict_to_list_file(lst1))
    return lst1

if __name__ == '__main__':
    import argparse
    import sys
    def get_arg(lst, index):
        if index >= len(lst):
            return None
        return lst[index]

    lst_args = sys.argv[1:]

    sort_parser = argparse.ArgumentParser(add_help=False)
    sort_parser.add_argument('target', type=str)
    sort_parser.add_argument('--rename', '-r', action='store_true')

    import_parser = argparse.ArgumentParser(add_help=False)
    import_parser.add_argument('source', type=str)
    import_parser.add_argument('name', type=str)
    import_parser.add_argument('--id', '-i', type=str, default=None)
    import_parser.add_argument('--artist', '-a', type=str, default=None)
    import_parser.add_argument('--charter', '-c', type=str, default=None)
    import_parser.add_argument('--desc', '-d', type=str, default=None)
    import_parser.add_argument('--ranked', '-r', action='store_true')

    remove_parser = argparse.ArgumentParser(add_help=False)
    remove_parser.add_argument('id', nargs='+', type=str)

    merge_parser = argparse.ArgumentParser(add_help=False)
    merge_parser.add_argument('source', nargs='+', type=str)

    command = get_arg(lst_args, 0)
    source = get_arg(lst_args, 1)

    if source is None:
        exit(0)

    rest_args = lst_args[2:]

    if command == 'sort':
        sort_args = sort_parser.parse_args(rest_args)
        target = sort_args.target
        force_remove(target)
        sort_dir(source, target, rename=sort_args.rename)
    elif command == 'list':
        lst = get_list(source)
        target_file = os.path.join(source, '__rena_index_2.json')
        with open(target_file, 'w', encoding='utf8') as f:
            json.dump(lst, f, indent=2)
        print(f'JSON output to {target_file}')
    elif command == 'relist':
        dirs = os.listdir(source)
        lst = []
        for _dir in dirs:
            path_dir = os.path.join(source, _dir)
            if os.path.isdir(path_dir):
                item = read_chart_dir(path_dir, _dir)
                if item:
                    lst.append(item)
                else:
                    print(f'Skipped {_dir}')
        with open(os.path.join(source, '__rena_index_2'), 'w', encoding='utf8') as f:
            f.write(json_dict_to_list_file(lst))
    elif command == 'import':
        import_args = import_parser.parse_args(rest_args)

        lst = get_list(source)
        ids = set()
        for dic in lst:
            ids.add(dic['id'])
        if import_args.id:
            ruuid = import_args.id
            if ruuid in ids:
                print('ID already exists.')
                exit(0)
        else:
            ruuid = random_uuid()
            while ruuid in ids:
                ruuid = random_uuid()
        new_item = read_chart_dir(import_args.source, import_args.name, artist=import_args.artist,
                                  charter=import_args.charter, desc=import_args.desc, ranked=import_args.ranked,
                                  id=ruuid)
        if new_item:
            basename = os.path.basename(import_args.source)
            target = os.path.join(source, basename)
            force_remove(target)
            shutil.copytree(import_args.source, target)
            lst.append(new_item)
            with open(os.path.join(source, '__rena_index_2'), 'w', encoding='utf8') as f:
                f.write(json_dict_to_list_file(lst))

    elif command == 'remove':
        remove_args = remove_parser.parse_args(rest_args)

        lst = get_list(source)
        new_lst = []
        remove_ids = set(remove_args.id)
        for dic in lst:
            if dic['id'] not in remove_ids:
                new_lst.append(dic)

        with open(os.path.join(source, '__rena_index_2'), 'w', encoding='utf8') as f:
            f.write(json_dict_to_list_file(new_lst))
    elif command == 'merge':
        merge_args = merge_parser.parse_args(rest_args)

        merges = merge_args.source
        for src in merges:
            merge_list(source, src)

