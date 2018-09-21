#!/usr/bin/python

from __future__ import division, print_function, unicode_literals

import os, subprocess, time, difflib

from fontTools.ttLib import TTFont
from fontTools.pens.cocoaPen import CocoaPen
from fontTools.pens.boundsPen import BoundsPen

try:
    import drawBot
except ImportError:
    in_drawbot = False
else:
    in_drawbot = True


# WARNING: It takes around 17 seconds to dump 1000 glyphs.

# TEST MODE?

TEST_MODE = False
TEST_MODE_GLYPHS = 'dvCandrabindu dvKA dvK_S_P_LA'.split() # Specified in development glyph names

# BASIC OPTIONS

# INPUT_PATH can point to either an OTF/TTF file, an OTC/TTC file,
# or a directory containing OTF/TTF/OTC/TTC files.

INPUT_PATH = 'input/KohinoorDevanagari/build20x'
GOADB_PATH = INPUT_PATH + '/GlyphOrderAndAliasDB'

STANDARD_GOADB_PATH = 'input/STANDARD_GOADB_dv'

FONT_SIZE = 100 # px

ZERO_PADDING_WIDTH = 4
APPEND_THE_GLYPH_NAME = True

STROKE_WIDTH = 2 # px
SHOW_BASELINE = True
SHOW_ADVANCE = True

PREFIX = 'dv'

GENERAL_GLYPHS = 'udatta udatta.matrai anudatta danda doubledanda indianrupee zerowidthnonjoiner zerowidthjoiner dottedcircle'.split() # Specified in development glyph names

# CANVAS OPTIONS

ALIGN_TO_PIXELS = True

LINE_HEIGHT_PERCENTAGE = 2.0

MARGIN_HORIZONTAL = 5 # px
VERTICAL_OFFSET_PERCENTAGE = -0.1


def main():

    for font_path in get_font_paths(INPUT_PATH):

        # Initiate the font

        font = TTFont(font_path)

        # Get font information

        info = FontInfo(font)

        # Calculate the scaling factor

        scaling = FONT_SIZE / info.unitsPerEm

        # Calculate some basic drawing parameters

        page_height_raw = FONT_SIZE * LINE_HEIGHT_PERCENTAGE

        lhp = LINE_HEIGHT_PERCENTAGE
        vop = VERTICAL_OFFSET_PERCENTAGE
        asc = info._ascender
        des = abs(info._descender)
        origin_raw = {
            'x': MARGIN_HORIZONTAL,
            'y': FONT_SIZE * ((lhp - 1) / 2 + des / (asc + des) + vop),
        }

        # Prepare the directory

        dump_directory = os.path.join(
            'dump',
            info._familyName_postscript,
            info.styleName,
            info._version,
            '{}'.format(FONT_SIZE),
        )
        mkdir_p(dump_directory)

        # Initiate the glyph set

        font_glyph_set = font.getGlyphSet()

        # Prepare the glyph list

        standard_goadb = parse_goadb(STANDARD_GOADB_PATH)
        standard_goadb_dnames = [d for p, d, u in standard_goadb]
        standard_p2d_map = {p: d for p, d, u in standard_goadb}
        standard_d2p_map = {d: p for p, d, u in standard_goadb}
        standard_d2u_map = {d: u for p, d, u in standard_goadb}

        goadb = parse_goadb(GOADB_PATH)
        goadb_dnames = [d for p, d, u in goadb]
        p2d_map = {p: d for p, d, u in goadb}
        d2p_map = {d: p for p, d, u in goadb}
        d2u_map = {d: u for p, d, u in goadb}

        font_dnames = [p2d_map[pname] for pname in font.getGlyphOrder()]

        kept_standard_goadb_dnames = filter(dname_filter, standard_goadb_dnames)
        kept_font_dnames = filter(dname_filter, font_dnames)

        # Get glyphs of interest

        if TEST_MODE:
            final_dnames = ['  ' + dname for dname in TEST_MODE_GLYPHS]
        else:
            final_dnames = difflib.Differ().compare(kept_standard_goadb_dnames, kept_font_dnames)

        glyphs_of_interest = []
        for line in final_dnames:

            tag = line[:1]
            dname = line[2:]

            pname = d2p_map.get(dname)
            if not pname:
                pname = standard_d2p_map.get(dname)

            character = d2u_map.get(dname)
            if not character:
                character = standard_d2u_map.get(dname)

            if tag == '-':
                glyph = None
                gid = None
            else:
                glyph = font_glyph_set[pname]
                gid = font.getGlyphID(pname)

            glyphs_of_interest.append(
                GlyphInfo(tag, glyph, gid, pname, dname, character, lsb=None, advance=None, rsb=None)
            )

        # Glyph metrics loop

        bounds_top = []
        bounds_bottom = []

        for g in glyphs_of_interest:

            if g.glyph:

                pen_bounds = BoundsPen(font_glyph_set)
                g.glyph.draw(pen_bounds)
                bounds = pen_bounds.bounds

                if bounds is None:
                    bounds = [0, 0, 0, 0]

                g.lsb = bounds[0]
                g.advance = g.glyph.width
                g.rsb = g.glyph.width - bounds[2]

                bounds_top.append(bounds[3])
                bounds_bottom.append(bounds[1])

        # Check if clipping will happen

        stretch_top = max(bounds_top) * scaling
        stretch_bottom = abs(min(bounds_bottom) * scaling)

        canvas_space_top = FONT_SIZE * LINE_HEIGHT_PERCENTAGE - origin_raw['y']
        canvas_space_bottom = origin_raw['y']

        print('{familyName}, {styleName}:'.format(**info.__dict__))

        if any([
            stretch_top > canvas_space_top,
            stretch_bottom > canvas_space_bottom
        ]) :
            print('[WARNING] Some glyphs will be clipped by the canvas.')
            print('  Font size:       ', FONT_SIZE)
            print('  Line height:     ', FONT_SIZE * LINE_HEIGHT_PERCENTAGE)
            print('* Canvas bounds:   ', canvas_space_top, -canvas_space_bottom)
            print('* Outline extremes:', stretch_top, -stretch_bottom)
            print('[BREAK OUT]')
            break

        else:
            print('[Note] The line height {} is large enough.'.format(
                FONT_SIZE * LINE_HEIGHT_PERCENTAGE
            ))

        print('')

        # Glyph drawing loop

        for g in glyphs_of_interest:

            if g.glyph:

                # Genrate the file name

                dump_name = str(g.gid).zfill(ZERO_PADDING_WIDTH)
                if APPEND_THE_GLYPH_NAME:
                    dump_name += '.' + g.dname

                # Calculate drawing parameters

                page_width = g.advance * scaling + MARGIN_HORIZONTAL * 2
                page_height = page_height_raw

                advance_in_px = g.advance * scaling

                origin = origin_raw.copy()

                if g.lsb < 0:
                    page_width += abs(g.lsb) * scaling
                    origin['x'] += abs(g.lsb) * scaling
                if g.rsb < 0:
                    page_width += abs(g.rsb) * scaling

                # Rounding

                if ALIGN_TO_PIXELS:
                    page_width = round(page_width / 2) * 2
                    page_height = round(page_height / 2) * 2
                    origin['x'] = round(origin['x'])
                    origin['y'] = round(origin['y'])
                    advance_in_px = round(advance_in_px)

                # Draw and save

                if in_drawbot:

                    # Initiate the canvas

                    newPage(page_width, page_height)

                    # Draw the background

                    save()
                    fill(1)

                    rect(0, 0, width(), height())

                    restore()

                    # Draw metrics

                    save()
                    translate(origin['x'], origin['y'])
                    fill(None)
                    strokeWidth(STROKE_WIDTH)

                    draw_metrics(g.advance, advance_in_px, origin)

                    restore()

                    # Draw the glyph

                    save()
                    translate(origin['x'], origin['y'])
                    scale(scaling)

                    pen_path = CocoaPen(font_glyph_set)
                    g.glyph.draw(pen_path)
                    drawPath(pen_path.path)

                    restore()

                    # Save the file

                    saveImage(os.path.join(dump_directory, dump_name + '.svg'))

                    # Clear the canvas

                    if not TEST_MODE:
                        newDrawing()

        if info.styleName == 'Regular':

            with open('TEMPLATE.html', 'r') as f:
                template = f.read()

            html_lines = []
            for g in glyphs_of_interest:
                html_lines.extend(generate_tr_lines(info, g))
            html_lines.extend([
                '  </table>',
                '</p>',
                '<p>EOF</p>',
            ])

            html_name = '{}-{}.html'.format(
                info._familyName_postscript,
                info._version.replace('.', '_')
            )
            html_path = os.path.join('dump', info._familyName_postscript, html_name)

            with open(html_path, 'w') as f:
                f.write(template + '\n'.join(html_lines) + '\n')

class FontInfo(object):

    def __init__(self, font):

        self.unitsPerEm   = font['head'].unitsPerEm
        self.fontRevision = font['head'].fontRevision

        self.openTypeHheaAscender  = font['hhea'].ascent
        self.openTypeHheaDescender = font['hhea'].descent

        self.familyName          = get_nameid(font, 16, 1)
        self.styleName           = get_nameid(font, 17, 2)
        self.openTypeNameVersion = get_nameid(font, 5)

        if self.openTypeNameVersion.replace('.', '', 1).isalnum():
            self._version = self.openTypeNameVersion
        else:
            self._version = '{:.3f}'.format(self.fontRevision)

        self._familyName_postscript = self.familyName.replace(' ', '')
        self._ascender  = self.openTypeHheaAscender
        self._descender = self.openTypeHheaDescender

class GlyphInfo(object):
    def __init__(self, tag, glyph, gid, pname, dname, character, lsb=None, advance=None, rsb=None):
        self.tag = tag
        self.glyph = glyph
        self.gid = gid
        self.pname = pname
        self.dname = dname
        self.character = character
        self.lsb = lsb
        self.advance = advance
        self.rsb = rsb

def mkdir_p(directory):
    try:
        os.makedirs(directory)
    except OSError:
        if not os.path.isdir(directory):
            raise

def decompose_otc(otc_path):

    directory_decomposed = otc_path + '.decomposed'
    mkdir_p(directory_decomposed)

    subprocess.call(
        ['otc2otf', os.path.abspath(otc_path)],
        cwd=directory_decomposed,
    )
    otf_paths = [
        os.path.join(directory_decomposed, file_name)
        for file_name in os.listdir(directory_decomposed)
    ]

    return otf_paths

def get_font_paths(input_path):

    font_paths = []

    if os.path.isfile(input_path):
        font_paths.append(input_path)
    elif os.path.isdir(input_path):
        font_paths.extend(
            [os.path.join(input_path, i) for i in os.listdir(input_path)]
        )

    font_paths = [
        decompose_otc(i) if i.endswith(('.otc', '.ttc')) else [i]
        for i in font_paths
    ]
    font_paths = [i for sublist in font_paths for i in sublist]
    font_paths = [i for i in font_paths if i.endswith(('.otf', '.ttf'))]

    return font_paths

def get_nameid(font, nameid, nameid_fallback=None):

    content = ''

    for nameid in nameid, nameid_fallback:
        if nameid:
            record = font['name'].getName(nameid, 3, 1, 0x409)
            if record:
                content = record.string.decode('UTF-16BE').encode('UTF-8')
                break

    return content

def parse_goadb(path):

    with open(path, 'r') as f:
        goadb_content = f.read()

    goadb = []

    for line in goadb_content.splitlines():
        content = line.partition('#')[0]
        if content:
            parts = content.split()
            pname = parts.pop(0)
            dname = parts.pop(0)
            if parts:
                character = parts.pop(0)[3:]
            else:
                character = None
            goadb.append((pname, dname, character))

    return goadb

def draw_metrics(advance, advance_in_px, origin):

    if SHOW_BASELINE:

        save()
        translate(-origin['x'], 0)

        stroke(0.9)

        line((0, 0), (width(), 0))

        restore()

    if SHOW_ADVANCE:

        if advance == 0:

            stroke(1, 0.3, 0.1)

            if not SHOW_BASELINE:
                line((-STROKE_WIDTH*2, 0), (STROKE_WIDTH*2, 0))

            line((0, -STROKE_WIDTH*2), (0, STROKE_WIDTH*2))

        else:

            stroke(0.8)

            if not SHOW_BASELINE:
                line((0, -STROKE_WIDTH/2), (0, STROKE_WIDTH/2))
            else:
                line((0, STROKE_WIDTH/2), (0, -STROKE_WIDTH*2))

            save()
            translate(advance_in_px, 0)

            if not SHOW_BASELINE:
                line((-STROKE_WIDTH/2, 0), (STROKE_WIDTH*2, 0))

            line((0, STROKE_WIDTH/2), (0, -STROKE_WIDTH*2))

            restore()

def dname_filter(dname):
    is_kept = False
    if dname.startswith(PREFIX) or (dname.partition('.')[0] in GENERAL_GLYPHS):
        is_kept = True
    return is_kept

def generate_tr_lines(info, g):

    attributes = ''
    note = ''
    if g.tag == '-':
        attributes = ' class=\'missing\''
        note = 'Missing'
    elif g.tag == '+':
        attributes = ' class=\'addition\''
        note = 'Addition'

    if g.glyph:
        gid = g.gid
        dump_name = str(g.gid).zfill(ZERO_PADDING_WIDTH)
        if APPEND_THE_GLYPH_NAME:
            dump_name += '.' + g.dname
        image_path = os.path.join(
            info.styleName,
            info._version,
            '{}'.format(FONT_SIZE),
            dump_name + '.svg',
        )
        img = '<img src=\'{}\'>'.format(image_path)
    else:
        gid = '-'
        img = '-'
    if g.character:
        character = 'U+' + g.character
    else:
        character = '-'

    lines = []
    lines.append('    <tr{}>'.format(attributes))
    for i in [gid, character, img, g.dname, g.pname, note]:
        lines.append('      <td>{}</td>'.format(i))
    lines.append('    </tr>')

    return lines

if __name__ == '__main__':
    start = time.clock()
    main()
    end = time.clock()
    print(end - start, 's')
