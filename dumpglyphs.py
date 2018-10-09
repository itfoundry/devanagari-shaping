#!/usr/bin/env python

from __future__ import division, print_function, unicode_literals

# BASIC OPTIONS

# INPUT_PATH can point to either an OTF/TTF file, an OTC/TTC file,
# or a directory containing OTF/TTF/OTC/TTC files.

INPUT_PATH = 'input/'

ZERO_PADDING_WIDTH = 4
APPEND_THE_GLYPH_NAME = True

STROKE_WIDTH = 10 # px
SHOW_BASELINE = True
SHOW_ADVANCE = True

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

def main():

    for font_path in get_font_paths(INPUT_PATH):

        # Initiate the font

        font = TTFont(font_path)

        # Get font information

        info = FontInfo(font)

        # Prepare the directory

        dump_directory = os.path.join(
            'dump',
            info._familyName_postscript,
            info.styleName,
            info._version,
        )
        mkdir_p(dump_directory)

        # Prepare the glyph list

        glyphs_in_font = font.getGlyphSet()
        glyph_names = font.getGlyphOrder()
        reversed_cmap = font["cmap"].buildReversed()

        glyphs = []
        for name in glyph_names:
            gid = font.getGlyphID(name)
            codepoints = reversed_cmap.get(name)
            glyph = glyphs_in_font[name]
            glyphs.append(
                GlyphInfo(glyph, gid, name, codepoints, lsb=None, advance=None, rsb=None)
            )

        # Glyph metrics loop

        bounds_left = []
        bounds_bottom = []
        bounds_right = []
        bounds_top = []

        for g in glyphs:

            pen_bounds = BoundsPen(glyphs_in_font)
            g.glyph.draw(pen_bounds)
            bounds = pen_bounds.bounds

            if bounds is None:
                bounds = [0, 0, 0, 0]

            g.lsb = bounds[0]
            g.advance = g.glyph.width
            g.rsb = g.glyph.width - bounds[2]

            bounds_left.append(bounds[0])
            bounds_bottom.append(bounds[1])
            bounds_right.append(bounds[2])
            bounds_top.append(bounds[3])

        canvas_bounds = [
            min(bounds_left), min(bounds_bottom),
            max(bounds_right), max(bounds_top),
        ]

        print('{familyName}, {styleName}...'.format(**info.__dict__))

        # Glyph drawing loop

        for g in glyphs:

            # Genrate the file name

            dump_name = str(g.gid).zfill(ZERO_PADDING_WIDTH)
            if APPEND_THE_GLYPH_NAME:
                dump_name += '.' + g.name

            # Calculate drawing parameters

            page_width = abs(canvas_bounds[0]) + canvas_bounds[2]
            page_height = abs(canvas_bounds[1]) + canvas_bounds[3]

            origin = {"x": abs(canvas_bounds[0]), "y": abs(canvas_bounds[1])}

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

                draw_metrics(g.advance, origin)

                restore()

                # Draw the glyph

                save()
                translate(origin['x'], origin['y'])

                pen_path = CocoaPen(glyphs_in_font)
                g.glyph.draw(pen_path)
                drawPath(pen_path.path)

                restore()

                # Save the file

                saveImage(os.path.join(dump_directory, dump_name + '.svg'))

                # Clear the canvas

                newDrawing()

        # Generate the HTML chart

        with open('TEMPLATE.html', 'r') as f:
            template = f.read()

        html_lines = []
        for g in glyphs:
            html_lines.extend(generate_tr_lines(info, g))
        html_lines.extend([
            '  </table>',
            '</p>',
            '<p>EOF</p>',
        ])

        html_name = '{}-{}-{}.html'.format(
            info._familyName_postscript,
            info.styleName,
            info._version.replace('.', '_')
        )
        html_path = os.path.join('dump', info._familyName_postscript, html_name)

        with open(html_path, 'w') as f:
            f.write(template + '\n'.join(html_lines) + '\n')

class FontInfo(object):

    def __init__(self, font):

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
    def __init__(self, glyph, gid, name, codepoints, lsb=None, advance=None, rsb=None):
        self.glyph = glyph
        self.gid = gid
        self.name = name
        self.codepoints = codepoints
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

def draw_metrics(advance, origin):

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
            translate(advance, 0)

            if not SHOW_BASELINE:
                line((-STROKE_WIDTH/2, 0), (STROKE_WIDTH*2, 0))

            line((0, STROKE_WIDTH/2), (0, -STROKE_WIDTH*2))

            restore()

def generate_tr_lines(info, g):

    attributes = ''
    note = ''

    if g.glyph:
        gid = g.gid
        dump_name = str(g.gid).zfill(ZERO_PADDING_WIDTH)
        if APPEND_THE_GLYPH_NAME:
            dump_name += '.' + g.name
        image_path = os.path.join(
            info.styleName,
            info._version,
            dump_name + '.svg',
        )
        img = '<img src=\'{}\'>'.format(image_path)
    else:
        gid = '-'
        img = '-'
    if g.codepoints:
        unicode_mapping = ", ".join('U+' + hex(i)[2:].zfill(4).upper() for i in sorted(g.codepoints))
    else:
        unicode_mapping = '-'

    lines = []
    lines.append('    <tr{}>'.format(attributes))
    for i in [gid, img, unicode_mapping, g.name, note]:
        lines.append('      <td>{}</td>'.format(i))
    lines.append('    </tr>')

    return lines

if __name__ == '__main__':
    start = time.clock()
    main()
    end = time.clock()
    print(end - start, 's')
