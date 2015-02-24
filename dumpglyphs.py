import os, subprocess, time

from fontTools.ttLib import TTFont
from fontTools.pens.cocoaPen import CocoaPen
from fontTools.pens.boundsPen import BoundsPen

# WARNING: IT TAKES AROUND 17 SECONDS TO DUMP 1000 GLYPHS

# Basic options

TEST_MODE = True

# INPUT_PATH can point to either an OTF/TTF file, an OTC/TTC file,
# or a directory containing OTF/TTF/OTC/TTC files.

INPUT_PATH = 'input/ITFDevanagari/latest/ITFDevanagari-Medium.otf'

GOADB_PATH = 'input/ITFDevanagari/latest/GlyphOrderAndAliasDB'

FONT_SIZE = 100 # px

APPEND_THE_GLYPH_NAME = True

STROKE_WIDTH = 2 # px
SHOW_BASELINE = True
SHOW_ADVANCE = True

# Canvas options

ALIGN_TO_PIXELS = True

MARGIN_HORIZONTAL = 5 # px
LINE_HEIGHT_PERCENTAGE = 1.7
VERTICAL_OFFSET_PERCENTAGE = -0.1

# Temp

width_of_the_biggest_gid = 4
extension = [
    'danda',
    'doubledanda',
    'zerowidthnonjoiner',
    'zerowidthjoiner',
    'dottedcircle',
]


def main():

    start = time.clock()

    for font_path in get_font_paths(INPUT_PATH):

        # Initiate the font

        tt = TTFont(font_path)

        # Get font information

        info = {}

        info['unitsPerEm']   = tt['head'].unitsPerEm
        info['fontRevision'] = tt['head'].fontRevision

        info['openTypeHheaAscender']  = tt['hhea'].ascent
        info['openTypeHheaDescender'] = tt['hhea'].descent

        info['familyName']          = get_nameid(tt, 16, 1)
        info['styleName']           = get_nameid(tt, 17, 2)
        info['openTypeNameVersion'] = get_nameid(tt, 5)

        if info['openTypeNameVersion'].replace('.', '', 1).isalnum():
            info['_version'] = info['openTypeNameVersion']
        else:
            info['_version'] = round(info['fontRevision'], 4)

        info['_ascender']  = info['openTypeHheaAscender']
        info['_descender'] = info['openTypeHheaDescender']

        # Calculate the scaling factor

        scaling = FONT_SIZE / info['unitsPerEm']

        # Organize glyphs

        glyph_names_dict = parse_goadb(GOADB_PATH)

        glyphs = tt.getGlyphSet()

        if TEST_MODE:
            glyphs_to_be_dumped = ['uni0915', 'uni0948']
        else:
            glyphs_to_be_dumped = [
                i for i in tt.getGlyphOrder()
                if any([
                    glyph_names_dict[i].startswith('dv'),
                    glyph_names_dict[i] in extension,
                ])
            ]

        dump_directory = os.path.join(
            'dump',
            info['familyName'],
            info['styleName'],
            str(info['_version']),
            str(FONT_SIZE),
        )
        mkdir_p(dump_directory)

        # Glyph loop

        for production_name in glyphs_to_be_dumped:

            development_name = glyph_names_dict[production_name]
            gid = tt.getGlyphID(production_name)
            glyph = glyphs[production_name]

            # Get glyph metrics

            metrics = {}

            pen = BoundsPen(glyphs)
            glyph.draw(pen)
            bounds = pen.bounds

            if bounds is None:
                bounds = [0, 0, 0, 0]

            metrics['lsb'] = bounds[0]
            metrics['advance'] = glyph.width
            metrics['rsb'] = glyph.width - bounds[2]

            # Calculate drawing parameters

            page_width = metrics['advance'] * scaling + MARGIN_HORIZONTAL * 2
            page_height = FONT_SIZE * LINE_HEIGHT_PERCENTAGE

            metrics['advance_in_px'] = metrics['advance'] * scaling

            lhp = LINE_HEIGHT_PERCENTAGE
            vop = VERTICAL_OFFSET_PERCENTAGE
            asc = info['_ascender']
            des = abs(info['_descender'])
            origin = {
                'x': MARGIN_HORIZONTAL,
                'y': FONT_SIZE * ((lhp - 1) / 2 + des / (asc + des) + vop),
            }

            if metrics['lsb'] < 0:
                page_width += abs(metrics['lsb']) * scaling
                origin['x'] += abs(metrics['lsb']) * scaling
            if metrics['rsb'] < 0:
                page_width += abs(metrics['rsb']) * scaling

            # Rounding

            if ALIGN_TO_PIXELS:
                page_width = round(page_width / 2) * 2
                page_height = round(page_height / 2) * 2
                origin['x'] = round(origin['x'])
                origin['y'] = round(origin['y'])
                metrics['advance_in_px'] = round(metrics['advance_in_px'])

            # Initiate the page

            newPage(page_width, page_height)

            # Draw the background

            save()
            fill(1)

            rect(0, 0, width(), height())

            restore()

            # Draw metrics

            save()
            translate(0, origin['y'])
            fill(None)
            strokeWidth(STROKE_WIDTH)

            draw_metrics(metrics, origin)

            restore()

            # Draw the glyph

            save()
            translate(origin['x'], origin['y'])
            scale(scaling)

            pen = CocoaPen(glyphs)
            glyph.draw(pen)
            drawPath(pen.path)

            restore()

            # Save the file

            dump_name = str(gid).zfill(width_of_the_biggest_gid)
            if APPEND_THE_GLYPH_NAME:
                dump_name += '.' + development_name

            saveImage(os.path.join(dump_directory, dump_name + '.png'))

            if not TEST_MODE:
                newDrawing()

    end = time.clock()
    print end - start, 's'


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

def get_nameid(tt, nameid, nameid_fallback=None):

    content = ''

    for nameid in nameid, nameid_fallback:
        if nameid:
            record = tt['name'].getName(nameid, 3, 1, 0x409)
            if record:
                content = record.string.decode('UTF-16BE').encode('UTF-8')
                break

    return content

def parse_goadb(path):

    with open(path, 'r') as f:
        goadb_content = f.read()

    glyph_names_dict = {}

    for line in goadb_content.splitlines():
        content = line.partition('#')[0]
        if content:
            parts = content.split()
            glyph_names_dict[parts[0]] = parts[1]

    return glyph_names_dict

def draw_metrics(metrics, origin):

    if SHOW_BASELINE:

        stroke(0.9)

        line((0, 0), (width(), 0))

    if SHOW_ADVANCE:

        save()
        translate(origin['x'], 0)

        if metrics['advance'] == 0:

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
            translate(metrics['advance_in_px'], 0)

            if not SHOW_BASELINE:
                line((-STROKE_WIDTH/2, 0), (STROKE_WIDTH*2, 0))
            line((0, STROKE_WIDTH/2), (0, -STROKE_WIDTH*2))

            restore()

        restore()


if __name__ == '__main__':
    main()
