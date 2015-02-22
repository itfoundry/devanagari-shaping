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

        fontinfo = {}

        fontinfo['unitsPerEm'] = tt['head'].unitsPerEm

        openTypeNameVersion = tt['name'].getName(
            nameID     = 5,
            platformID = 3,
            platEncID  = 1,
            langID     = 0x409,
        )

        openTypeNamePreferredFamilyName = tt['name'].getName(
            nameID     = 16,
            platformID = 3,
            platEncID  = 1,
            langID     = 0x409,
        )

        openTypeNamePreferredSubfamilyName = tt['name'].getName(
            nameID     = 17,
            platformID = 3,
            platEncID  = 1,
            langID     = 0x409,
        )

        if openTypeNamePreferredFamilyName:
            fontinfo['familyName'] = decode_tt_string(openTypeNamePreferredFamilyName.string)
        else:
            fontinfo['familyName'] = decode_tt_string(tt['name'].getName(
                nameID     = 1,
                platformID = 3,
                platEncID  = 1,
                langID     = 0x409,
            ).string)

        if openTypeNamePreferredSubfamilyName:
            fontinfo['styleName'] = decode_tt_string(openTypeNamePreferredSubfamilyName.string)
        else:
            fontinfo['styleName'] = decode_tt_string(tt['name'].getName(
                nameID     = 2,
                platformID = 3,
                platEncID  = 1,
                langID     = 0x409,
            ).string)

        if openTypeNameVersion and decode_tt_string(openTypeNameVersion.string).replace('.', '', 1).isalnum():
            fontinfo['version'] = decode_tt_string(openTypeNameVersion.string)
        else:
            fontinfo['version'] = round(tt['head'].fontRevision, 4)

        directory = os.path.join(
            'dump',
            fontinfo['familyName'],
            fontinfo['styleName'],
            str(fontinfo['version']),
            str(POINT_SIZE),
        )

        mkdir_p(directory)

        gid_string = str(gid).zfill(width_of_the_biggest_gid)
        if APPEND_THE_GLYPH_NAME:
            name = gid_string + '.' + glyph_name + '.png'
        else:
            name = gid_string + '.png'

        with open(os.path.join(directory, name), 'w') as f:
            f.write('testsds')


def decode_tt_string(tt_string):
    return tt_string.decode('utf_16_be')

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


if __name__ == '__main__':
    main()
