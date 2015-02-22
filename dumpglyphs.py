import os, subprocess, pprint
from fontTools import ttLib

pp = pprint.PrettyPrinter(indent = 4)

# Options

INPUT_PATH = 'input/ITFDevanagari/latest'

POINT_SIZE = 100
APPEND_THE_GLYPH_NAME = True
SHOW_BASELINE = False
SHOW_ADVANCE = True
LINE_WIDTH = 2

# Temp

gid = 123
glyph_name = 'dvX'
width_of_the_biggest_gid = 4


def main():

    for font_path in get_font_paths(INPUT_PATH):

        tt = ttLib.TTFont(font_path)
        fontinfo = get_fontinfo(tt)

        dump_directory = os.path.join(
            'dump',
            fontinfo['familyName'],
            fontinfo['styleName'],
            str(fontinfo['version']),
            str(POINT_SIZE),
        )
        mkdir_p(dump_directory)

        gid_string = str(gid).zfill(width_of_the_biggest_gid)
        if APPEND_THE_GLYPH_NAME:
            dump_name = gid_string + '.' + glyph_name + '.png'
        else:
            dump_name = gid_string + '.png'

        with open(os.path.join(dump_directory, dump_name), 'w') as f:
            f.write('testsds')


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
        content = record_fallback.string.decode('utf_16_be')
    else:
        content = ''

    return content

def get_fontinfo(tt):

    fontinfo = {}

    fontinfo['unitsPerEm'] = tt['head'].unitsPerEm

    fontinfo['familyName'] = get_nameid(tt, 16, 1)
    fontinfo['styleName'] = get_nameid(tt, 17, 2)

    openTypeNameVersion = get_nameid(tt, 5)
    if openTypeNameVersion.replace('.', '', 1).isalnum():
        fontinfo['version'] = openTypeNameVersion
    else:
        fontinfo['version'] = round(tt['head'].fontRevision, 4)

    return fontinfo


if __name__ == '__main__':
    main()
