import os, subprocess, time
from fontTools.ttLib import TTFont
from fontTools.pens.cocoaPen import CocoaPen
from fontTools.pens.boundsPen import BoundsPen


# pp = pprint.PrettyPrinter(indent = 4).pprint

# Options

INPUT_PATH = 'input/ITFDevanagari/latest/ITFDevanagari-Bold.otf'

POINT_SIZE = 100
APPEND_THE_GLYPH_NAME = True
SHOW_BASELINE = False
SHOW_ADVANCE = True
LINE_WIDTH = 2 # Pixels

ALIGN_TO_PIXELS = False

# Rasterization options

MARGIN_X = 0.05
MARGIN_Y = 0.35

VERTICALLY_CENTERING_OFFSET = -0.1

# Temp

gid = 123
glyph_name = 'dvX'
width_of_the_biggest_gid = 4

# extension = [
#     'danda',
#     'doubledanda',
#     'zerowidthnonjoiner',
#     'zerowidthjoiner',
#     'dottedcircle',
# ]

extension = [
    'dvCandrabindu',
    'dvAcandra',
]


def main():

    start = time.clock()

    bounds_top = []
    bounds_bottom = []

    for font_path in get_font_paths(INPUT_PATH):

        tt = TTFont(font_path)
        fontinfo = get_fontinfo(tt)

        resizing_factor = POINT_SIZE / fontinfo['unitsPerEm']
        baseline_height_percentage = abs(fontinfo['openTypeHheaDescender']) / (
            fontinfo['openTypeHheaAscender'] - fontinfo['openTypeHheaDescender']
        )

        glyph_names_dict = parse_goadb('GlyphOrderAndAliasDB')

        glyphs = tt.getGlyphSet()

        dump_directory = os.path.join(
            'dump',
            fontinfo['familyName'],
            fontinfo['styleName'],
            str(fontinfo['version']),
            str(POINT_SIZE),
        )
        mkdir_p(dump_directory)

        for gid, production_name, development_name in [
            (tt.getGlyphID(i), i, glyph_names_dict[i])
            for i in tt.getGlyphOrder()
            if glyph_names_dict[i].startswith('x') or
            glyph_names_dict[i] in extension
        ]:

            glyph = glyphs[production_name]
            print gid, production_name, development_name
            metrics = {}

            pen = BoundsPen(glyphs)
            glyph.draw(pen)
            metrics['lsb'] = pen.bounds[0]
            metrics['width'] = glyph.width
            metrics['rsb'] = glyph.width - pen.bounds[2]
            bounds_top.append(pen.bounds[3])
            bounds_bottom.append(pen.bounds[1])

            extension_left  = 0
            extension_right = 0
            if metrics['lsb'] < 0:
                extension_left = abs(metrics['lsb'])
            if metrics['rsb'] < 0:
                extension_right = abs(metrics['rsb'])

            page_width  = (metrics['width'] + fontinfo['unitsPerEm'] * MARGIN_X * 2 + extension_left + extension_right) * resizing_factor
            page_height = fontinfo['unitsPerEm'] * (1 + MARGIN_Y * 2) * resizing_factor

            origin_x = round(fontinfo['unitsPerEm'] * MARGIN_X + extension_left)
            origin_y = fontinfo['unitsPerEm'] * (MARGIN_Y + baseline_height_percentage + VERTICALLY_CENTERING_OFFSET)

            newPage(round(page_width / 2) * 2, page_height)
            fill(1)
            rect(0, 0, width(), height())

            pen = CocoaPen(glyphs)
            glyph.draw(pen)

            scale(resizing_factor)
            translate(origin_x, origin_y)
            fill(0)
            drawPath(pen.path)

            fill(None)
            strokeWidth(20)

            if metrics['width'] == 0:
                stroke(1, 0.3, 0.1)
                line((0, 0), (0, 0 + fontinfo['unitsPerEm'] * (1 - baseline_height_percentage)))

            else:
                stroke(0.6)
                line((0, 0 - 10), (0, 10))
                boundary_right = round((metrics['width']) * resizing_factor) / resizing_factor
                line((boundary_right, 10), (boundary_right, -40))
                line((boundary_right - 10, 0), (boundary_right + 40, 0))

            dump_name = str(gid).zfill(width_of_the_biggest_gid)
            if APPEND_THE_GLYPH_NAME:
                dump_name += '.' + development_name

            saveImage(os.path.join(dump_directory, dump_name + '.png'))
            # newDrawing()

        print max(bounds_top), min(bounds_bottom)

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
        cwd = directory_decomposed,
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

def get_nameid(tt, id, id_fallback = None):

    record = tt['name'].getName(
        nameID     = id,
        platformID = 3,
        platEncID  = 1,
        langID     = 0x409,
    )

    if record:
        content = record.string.decode('utf_16_be')
    elif id_fallback:
        record_fallback = tt['name'].getName(
            nameID     = id_fallback,
            platformID = 3,
            platEncID  = 1,
            langID     = 0x409,
        )
        content = record_fallback.string.decode('UTF-16 BE').encode('UTF-8')
    else:
        content = ''

    return content

def get_fontinfo(tt):

    fontinfo = {}

    fontinfo['unitsPerEm'] = tt['head'].unitsPerEm
    fontinfo['openTypeHheaAscender'] = tt['hhea'].ascent
    fontinfo['openTypeHheaDescender'] = tt['hhea'].descent

    fontinfo['familyName'] = get_nameid(tt, 16, 1)
    fontinfo['styleName'] = get_nameid(tt, 17, 2)

    openTypeNameVersion = get_nameid(tt, 5)
    if openTypeNameVersion.replace('.', '', 1).isalnum():
        fontinfo['version'] = openTypeNameVersion
    else:
        fontinfo['version'] = round(tt['head'].fontRevision, 4)

    print fontinfo
    return fontinfo

def parse_goadb(path):

    with open(path, 'r') as f:
        goadb_content = f.read()

    glyph_names_dict = {}

    for line in goadb_content.splitlines():
        content = line.partition('#')[0] # Remove comments
        if content:
            parts = content.split()
            glyph_names_dict[parts[0]] = parts[1]

    return glyph_names_dict


if __name__ == '__main__':
    main()
