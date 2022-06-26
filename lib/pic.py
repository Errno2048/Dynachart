from PIL import Image, ImageColor, ImageDraw, ImageFont
from math import ceil
import numpy as np
from .dynamix2dynamite import convert_json

class Note:
    SIDE_LEFT = -1
    SIDE_FRONT = 0
    SIDE_RIGHT = 1

    NOTE_NORMAL = 0
    NOTE_CHAIN = 1
    NOTE_HOLD = 2

    COLOR_NORMAL = (0, 255, 255, 255)
    COLOR_CHAIN = (255, 51, 51, 255)
    COLOR_HOLD_BOARD = (255, 255, 128, 255)
    COLOR_HOLD_FILL = (70, 134, 0, 255)

    WIDTH_NORMAL = 40
    WIDTH_CHAIN = 20
    WIDTH_HOLD = 40
    WIDTH_MIN = 20

    def __lt__(self, other):
        res = self.start - other.start
        if res != 0: return res < 0
        res = self.type - other.type
        if res != 0: return res < 0
        if self.type == self.NOTE_HOLD:
            res = self.end - other.end
            if res != 0: return res < 0
        res = self.pos - other.pos
        if res != 0: return res < 0
        res = self.width - other.width
        if res != 0: return res < 0
        return False

    def __init__(self, pos, width=1.0, side=SIDE_FRONT, type=NOTE_NORMAL, start=0.0, end=None):
        self.type = type
        self.side = side
        self.width = width
        self.pos = pos + width / 2
        self.start = start
        if end is None:
            self.end = start
        else:
            self.end = max(start, end)

    def clone(self):
        note = Note(0, 0, self.side, self.type, self.start, self.end)
        note.pos = self.pos
        note.width = self.width
        return note

    def generate_image(self, width_per_unit, bar_height, scale=1.0):
        fill_color = self.COLOR_NORMAL
        outline_color = None
        width = width_per_unit * self.width
        height = max(1, round(scale * self.WIDTH_NORMAL))
        line_width = 1
        radius = height / 2
        if self.type == self.NOTE_NORMAL:
            pass
        elif self.type == self.NOTE_CHAIN:
            fill_color = self.COLOR_CHAIN
            height = max(1, round(scale * self.WIDTH_CHAIN))
            radius = height / 2
        elif self.type == self.NOTE_HOLD:
            fill_color = self.COLOR_HOLD_FILL
            outline_color = self.COLOR_HOLD_BOARD
            WIDTH_HOLD = max(1, round(scale * self.WIDTH_HOLD))
            line_width = WIDTH_HOLD
            height = bar_height * (self.end - self.start) + WIDTH_HOLD
            radius = max(1, round(scale * self.WIDTH_HOLD / 2))
        width, height, radius = round(width), round(height), round(radius)
        WIDTH_MIN = max(1, round(scale * self.WIDTH_MIN))
        width = max(width, WIDTH_MIN)
        height = max(height, WIDTH_MIN)
        img = Image.new('RGBA', (width, height), color=(0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.rounded_rectangle([(0, 0), (width, height)], radius, fill_color, outline_color, line_width)
        return img

class Chart:
    @classmethod
    def concatenate(cls, former_chart, latter_chart, song_length_sec):
        return former_chart.clone().concat(latter_chart, song_length_sec)

    def __init__(self):
        self.name = None
        self.map_id = None
        self.notes = []
        self.time = 0.0
        self.left_slide = False
        self.right_slide = False
        self.bar_per_min = 0.0
        self.time_offset = 0.0

    def clone(self):
        new_chart = Chart()
        new_chart.name = self.name
        new_chart.map_id = self.map_id
        new_chart.time = self.time
        new_chart.left_slide = self.left_slide
        new_chart.right_slide = self.right_slide
        new_chart.time_offset = self.time_offset
        new_chart.bar_per_min = self.bar_per_min
        for note in self.notes:
            new_chart.notes.append(note.clone())
        return new_chart

    def concat(self, other, song_length_sec):
        other = other.change_bpm(self.bar_per_min)
        time_offset = song_length_sec - self.time_offset + other.time_offset
        bar_offset = self.bar_per_min * time_offset / 60
        note_id = -1
        for note in self.notes:
            note_id = max(note.id, note_id)
        note_id += 1
        for note in other.notes:
            note.start += bar_offset
            note.end += bar_offset
            self.time = max(self.time, note.end)
        self.notes.extend(other.notes)
        return self

    def change_bpm(self, new_bpm):
        new_chart = self.clone()
        new_chart.bar_per_min = new_bpm
        for note in new_chart.notes:
            note.start = new_bpm * note.start / self.bar_per_min
            note.end = new_bpm * note.end / self.bar_per_min
        return new_chart

    def to_dict(self):
        m_notes = []
        m_notesLeft = []
        m_notesRight = []
        data = {
            'm_Name': self.name,
            'm_mapID': self.map_id,
            'm_barPerMin': self.bar_per_min,
            'm_timeOffset': self.time_offset,
            'm_leftRegion': 1 if self.left_slide else 2,
            'm_rightRegion': 1 if self.right_slide else 2,
            'm_notes': {
                'm_notes': m_notes,
            },
            'm_notesLeft': {
                'm_notes': m_notesLeft,
            },
            'm_notesRight': {
                'm_notes': m_notesRight,
            },
        }
        note_id = 0
        for note in self.notes:
            if note.type == Note.NOTE_CHAIN:
                typ = 1
            elif note.type == Note.NOTE_HOLD:
                typ = 2
            elif note.type == Note.NOTE_NORMAL:
                typ = 0
            else:
                typ = 0
            pos = note.pos - note.width / 2
            note_dict = {
                'm_id': note_id,
                'm_type': typ,
                'm_time': note.start,
                'm_position': pos,
                'm_width': note.width,
                'm_subId': note_id + 1 if typ == 2 else -1,
            }
            note_id += 1
            if note.side == Note.SIDE_FRONT:
                m_notes.append(note_dict)
            elif note.side == Note.SIDE_LEFT:
                m_notesLeft.append(note_dict)
            elif note.side == Note.SIDE_RIGHT:
                m_notesRight.append(note_dict)
            else:
                m_notes.append(note_dict)
            if typ == 2:
                note_dict = {
                    'm_id': note_id,
                    'm_type': 3,
                    'm_time': note.end,
                    'm_position': pos,
                    'm_width': note.width,
                    'm_subId': -1,
                }
                note_id += 1
                if note.side == Note.SIDE_FRONT:
                    m_notes.append(note_dict)
                elif note.side == Note.SIDE_LEFT:
                    m_notesLeft.append(note_dict)
                elif note.side == Note.SIDE_RIGHT:
                    m_notesRight.append(note_dict)
                else:
                    m_notes.append(note_dict)
        return data

    def to_xml(self):
        return convert_json(self.to_dict())


class Board:
    SIDE_BORDER = -0.2
    SIDE_CAP = 6.1
    SIDE_LIMIT = -1.1

    SIDE_VISIBLE_LIMIT = -1.3#-1.5
    SIDE_VISIBLE_CAP = 6.5

    FRONT_LEFT_BORDER = -0.3
    FRONT_RIGHT_BORDER = 5.3
    FRONT_LEFT_LIMIT = -0.7
    FRONT_RIGHT_LIMIT = 5.7

    FRONT_VISIBLE_LEFT_LIMIT = -0.7#-1.1
    FRONT_VISIBLE_RIGHT_LIMIT = 5.7#6.1

    FRONT_BOARD_RATE = 2.0
    FRONT_NOTE_RATE = 2.25

    NOTE_SIZE = 100 # size 1 to pixels
    BOARD_SIZE = 150 # size 1 to pixels
    TIME_SIZE = 2880  # bar size

    SIDE_LINE_WIDTH = 10
    BOTTOM_LINE_WIDTH = 15
    BAR_LINE_WIDTH = 5
    SEMI_BAR_LINE_WIDTH = 5
    SPLIT_LINE_WIDTH = 20

    BACKGROUND_COLOR = (0, 0, 0, 255)
    LINE_COLOR = (255, 255, 255, 255)
    BAR_LINE_COLOR = (255, 255, 255, 255)#(127, 127, 127, 255)
    SEMI_BAR_LINE_COLOR = (127, 127, 127, 255)
    SPLIT_LINE_COLOR = (255, 255, 255, 255)

    FONT_SIZE = 96
    FONT_COLOR = (255, 255, 255, 255)

    def __init__(self, scale=0.5, time_limit: int=32, speed = 0.5, bar_span = 2, semi_bar_span = 1 / 16):
        self.scale = scale
        self.notes = []
        self.time_limit = round(time_limit)
        self.speed = speed
        self.bar_span = bar_span
        self.semi_bar_span = semi_bar_span

    def generate(self, chart: Chart):
        board, args = self.draw_board(chart)
        self.draw_notes(board, args, chart)
        return board

    def draw_board(self, chart: Chart):
        pages = ceil(chart.time / self.time_limit)
        page_img, args = self.draw_page()
        pagew, pageh = page_img.size
        img = Image.new('RGBA', (pagew * pages, pageh))
        for i in range(pages):
            img.paste(page_img, (i * pagew, 0))
        draw = ImageDraw.Draw(img)

        font_size = round(self.FONT_SIZE * self.scale)
        font = ImageFont.truetype('Fonts/arial.ttf', size=font_size)

        page_width, page_height, bar_height, bottom_line_y, side_line_leftside_x, side_line_left_x, side_line_right_x, side_line_rightside_x = args
        for i in range(0, pages * self.time_limit + self.bar_span, self.bar_span):
            pg = int(i / self.time_limit)
            x = page_width * pg
            y = bottom_line_y - bar_height * self.scale * (i - pg * self.time_limit)
            if i % self.time_limit != 0:
                draw.line([(x, y), (x + page_width, y)], fill=self.BAR_LINE_COLOR, width=max(1, round(self.scale * self.BAR_LINE_WIDTH)))
            if self.semi_bar_span and self.semi_bar_span > 0:
                for j in np.arange(self.semi_bar_span, self.bar_span, self.semi_bar_span):
                    semi_y = y - bar_height * self.scale * j
                    draw.line([(x, semi_y), (x + page_width, semi_y)], fill=self.SEMI_BAR_LINE_COLOR, width=max(1, round(self.scale * self.SEMI_BAR_LINE_WIDTH)))
            time = round((i / chart.bar_per_min * 60 + chart.time_offset) * 1000)
            h = time // 3600000
            m = (time % 3600000) // 60000
            s = (time % 60000) // 1000
            ms = time % 1000
            if h == 0:
                text = "%02d:%02d:%03d %d" % (m, s, ms, i)
            else:
                text = "%02d:%02d:%02d:%03d %d" % (h, m, s, ms, i)
            draw.text((x + side_line_left_x - font_size / 2, y - font_size), text, fill=self.FONT_COLOR, font=font, anchor='rm')

        for i in range(1, pages):
            draw.line([(i * pagew, 0), (i * pagew, pageh)], fill=self.SPLIT_LINE_COLOR, width=max(1, round(self.scale * self.SPLIT_LINE_WIDTH)))
        return img, args

    def draw_page(self):
        page_width = round((
            2 * (self.SIDE_VISIBLE_CAP - self.SIDE_VISIBLE_LIMIT) +
            self.FRONT_BOARD_RATE * (self.FRONT_VISIBLE_RIGHT_LIMIT - self.FRONT_VISIBLE_LEFT_LIMIT)
        ) * self.BOARD_SIZE * self.scale)
        page_bottom = round(self.BOARD_SIZE * (self.SIDE_BORDER - self.SIDE_LIMIT) * self.scale)
        bar_height = self.speed * self.TIME_SIZE
        page_height = round(2 * page_bottom + (bar_height * self.time_limit) * self.scale)

        bottom_line_y = page_height - page_bottom
        side_line_leftside_x = round((self.SIDE_VISIBLE_CAP - self.SIDE_BORDER) * self.BOARD_SIZE * self.scale)
        side_line_left_x = round((
            (self.SIDE_VISIBLE_CAP - self.SIDE_VISIBLE_LIMIT) +
            self.FRONT_BOARD_RATE * (self.FRONT_LEFT_BORDER - self.FRONT_VISIBLE_LEFT_LIMIT)
        ) * self.BOARD_SIZE * self.scale)
        side_line_right_x = round((
            (self.SIDE_VISIBLE_CAP - self.SIDE_VISIBLE_LIMIT) +
            self.FRONT_BOARD_RATE * (self.FRONT_RIGHT_BORDER - self.FRONT_VISIBLE_LEFT_LIMIT)
        ) * self.BOARD_SIZE * self.scale)
        side_line_rightside_x = round((
            (self.SIDE_VISIBLE_CAP - self.SIDE_VISIBLE_LIMIT) +
            (self.SIDE_BORDER - self.SIDE_VISIBLE_LIMIT) +
            self.FRONT_BOARD_RATE * (self.FRONT_VISIBLE_RIGHT_LIMIT - self.FRONT_VISIBLE_LEFT_LIMIT)
        ) * self.BOARD_SIZE * self.scale)

        img = Image.new('RGBA', (page_width, page_height), self.BACKGROUND_COLOR)
        draw = ImageDraw.Draw(img)

        BOTTOM_LINE_WIDTH = max(1, round(self.scale * self.BOTTOM_LINE_WIDTH))
        SIDE_LINE_WIDTH = max(1, round(self.scale * self.SIDE_LINE_WIDTH))

        draw.line([(0, bottom_line_y), (page_width, bottom_line_y)], fill=self.LINE_COLOR, width=BOTTOM_LINE_WIDTH)
        draw.line([(0, page_bottom), (page_width, page_bottom)], fill=self.LINE_COLOR, width=BOTTOM_LINE_WIDTH)
        draw.line([(side_line_leftside_x, page_bottom), (side_line_leftside_x, bottom_line_y)], fill=self.LINE_COLOR, width=SIDE_LINE_WIDTH)
        draw.line([(side_line_left_x, page_bottom), (side_line_left_x, bottom_line_y)], fill=self.LINE_COLOR, width=SIDE_LINE_WIDTH)
        draw.line([(side_line_right_x, page_bottom), (side_line_right_x, bottom_line_y)], fill=self.LINE_COLOR, width=SIDE_LINE_WIDTH)
        draw.line([(side_line_rightside_x, page_bottom), (side_line_rightside_x, bottom_line_y)], fill=self.LINE_COLOR, width=SIDE_LINE_WIDTH)

        return img, (page_width, page_height, bar_height, bottom_line_y, side_line_leftside_x, side_line_left_x, side_line_right_x, side_line_rightside_x)

    def draw_notes(self, board: Image.Image, args, chart: Chart):
        page_width, page_height, bar_height, bottom_line_y, \
        side_line_leftside_x, side_line_left_x, side_line_right_x, side_line_rightside_x = args

        bar_height = bar_height * self.scale

        board_front = Image.new('RGBA', board.size, (0, 0, 0, 0))

        for note in chart.notes:
            note : Note
            side = note.side
            width_per_unit = self.NOTE_SIZE * self.scale
            if side == Note.SIDE_FRONT:
                width_per_unit *= self.FRONT_NOTE_RATE
            if side == Note.SIDE_LEFT:
                x = (self.SIDE_VISIBLE_CAP - note.pos) * self.BOARD_SIZE * self.scale
            elif side == Note.SIDE_FRONT:
                x = side_line_left_x + (note.pos - self.FRONT_LEFT_BORDER) * self.BOARD_SIZE * self.FRONT_BOARD_RATE * self.scale
            else:
                x = side_line_rightside_x + (note.pos - self.SIDE_BORDER) * self.BOARD_SIZE * self.scale
            page_number = int(note.start / self.time_limit)
            end_page_number = page_number
            if note.type == Note.NOTE_HOLD:
                end_page_number = int(note.end / self.time_limit)
            img = note.generate_image(round(width_per_unit), round(bar_height), scale=self.scale)

            WIDTH_HOLD_2 = max(1, round(self.scale * Note.WIDTH_HOLD / 2))

            if page_number == end_page_number:
                x += page_number * page_width
                y = bottom_line_y - (note.start - page_number * self.time_limit) * bar_height
                realx = round(x - img.width / 2)
                if note.type == Note.NOTE_HOLD:
                    realy = round(y - img.height + WIDTH_HOLD_2)
                else:
                    realy = round(y - img.height / 2)
                if note.type == Note.NOTE_HOLD:
                    board.paste(img, (realx, realy), mask=img)
                else:
                    board_front.paste(img, (realx, realy), mask=img)
            else:
                cap_y = board.height - bottom_line_y
                end_y = round(bottom_line_y - (note.end - end_page_number * self.time_limit) * bar_height - WIDTH_HOLD_2)
                start_clip = round(((page_number + 1) * self.time_limit - note.start) * bar_height + WIDTH_HOLD_2)
                end_clip = round((note.end - end_page_number * self.time_limit) * bar_height + WIDTH_HOLD_2)
                start_crop = img.crop((0, img.height - start_clip, img.width, img.height))
                end_crop = img.crop((0, 0, img.width, end_clip))
                board.paste(start_crop, (round(x + page_number * page_width - img.width / 2), cap_y), mask=start_crop)
                board.paste(end_crop, (round(x + end_page_number * page_width - img.width / 2), end_y), mask=end_crop)

                pagesize = self.time_limit * bar_height
                for pg in range(page_number + 1, end_page_number):
                    cy = img.height - start_clip - (pg - page_number) * pagesize
                    crop = img.crop((0, round(cy), img.width, round(cy + pagesize)))
                    board.paste(crop, (round(x + pg * page_width - img.width / 2), cap_y), mask=crop)
        board.paste(board_front, (0, 0), mask=board_front)