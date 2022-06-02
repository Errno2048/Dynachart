from lib.reader import *
from lib.pic import Board
import json
from xml.etree import ElementTree

if __name__ == '__main__':
    import argparse
    import json
    import os, sys

    parser = argparse.ArgumentParser(add_help=False)

    parser.add_argument('files', metavar='name', nargs='*', type=str)
    #parser.add_argument('--type', '-t', choices=('dynamite', 'dynamix'), type=str, default=None)
    parser.add_argument('--scale', '-s', type=float, default=0.4)
    parser.add_argument('--speed', '-S', type=float, default=0.8)
    parser.add_argument('--page_limit', '-l', type=int, default=16)
    parser.add_argument('--bar_span', '-b', type=int, default=2)
    parser.add_argument('--encoding', '-E', type=str, default='utf8')
    parser.add_argument('--verbose', '-v', action='store_true', default=False)

    args = parser.parse_args()

    for f in args.files:
        if not os.path.isfile(f):
            if args.verbose:
                print(f'File "{f}" is not found.', file=sys.stderr)
            continue
        try:
            if args.verbose:
                print(f'Parsing "{f}".', file=sys.stderr)
            fname = os.path.basename(f)
            if (pt := fname.rfind('.')) != -1:
                ftarget = fname[:pt] + '.png'
            else:
                ftarget = fname + '.png'
            with open(f, 'r', encoding=args.encoding) as F:
                chart = F.read()

            chart = read(chart)

            board = Board(scale=args.scale, time_limit=args.page_limit, speed=args.speed, bar_span=args.bar_span)
            img = board.generate(chart)
            img.save(os.path.join(os.path.dirname(f), ftarget))
            if args.verbose:
                print(f'Saved the overview to "{ftarget}".', file=sys.stderr)
        except Exception:
            if args.verbose:
                print(f'Parsing "{f}" failed.', file=sys.stderr)
            pass
