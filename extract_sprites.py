from extract import extract_sprites
from lib.fileutils import force_mkdir
import UnityPy as unity
import os
from pathlib import Path
from PIL.Image import Image
from tqdm import tqdm

def extract_game_sprites(src, dst, match_list, format='png', verbose=False):
    src = Path(src)
    dst = Path(dst)
    force_mkdir(dst)
    files = []
    for file in os.listdir(src):
        for s in match_list:
            if file.startswith(s):
                files.append((file, file[len(s):]))
    gen = files
    if verbose:
        gen = tqdm(files, total=len(files))
    for file, name in gen:
        if verbose:
            gen.set_postfix({
                'name': name,
            })
        force_mkdir(dst / name)
        sprites = extract_sprites(src / file, fix_horizontal=True)
        for s_name, sprite in sprites:
            sprite.save(dst / name / f'{s_name}.{format}', format=format)

def extract_characters(src, dst, format='png', verbose=False):
    return extract_game_sprites(src, Path(dst) / 'characters', match_list=('_avator_', '_char_'), format=format, verbose=verbose)

def extract_backgrounds(src, dst, format='png', verbose=False):
    return extract_game_sprites(src, Path(dst) / 'backgrounds', match_list=('_background_', '_bg_'), format=format, verbose=verbose)

def extract_fronts(src, dst, format='png', verbose=False):
    return extract_game_sprites(src, Path(dst) / 'fronts', match_list=('_front_',), format=format, verbose=verbose)

def extract_titles(src, dst, format='png', verbose=False):
    return extract_game_sprites(src, Path(dst) / 'titles', match_list=('_title_',), format=format, verbose=verbose)

def extract_avatorlist(src, dst, format='png', verbose=False):
    src = Path(src) / '_avatorlist'
    dst = Path(dst) / 'avatorlist'
    force_mkdir(dst)
    if not os.path.exists(src):
        return
    sprites = extract_sprites(src)
    if verbose:
        sprites = tqdm(sprites, total=len(sprites))
    for s_name, sprite in sprites:
        if verbose:
            sprites.set_postfix({
                'name': s_name,
            })
        sprite.save(dst / f'{s_name}.{format}', format=format)

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument('source', metavar='name', type=str, help='Android/data/com.c4cat.dynamix/files/UnityCache/Shared')
    parser.add_argument('target', metavar='dir', nargs='?', default=None, type=str, help='The target directory.')

    parser.add_argument('--verbose', '-v', action='store_true', help='')

    args = parser.parse_args()

    src = args.source
    dst = args.target
    verbose = args.verbose
    if dst is None:
        dst = os.path.abspath(os.curdir)

    extract_characters(src, dst, verbose=verbose)
    extract_backgrounds(src, dst, verbose=verbose)
    extract_fronts(src, dst, verbose=verbose)
    extract_titles(src, dst, verbose=verbose)
    extract_avatorlist(src, dst, verbose=verbose)
