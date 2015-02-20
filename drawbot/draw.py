from robofab.world import OpenFont
import resources

print "Working..."

FONT_SIZE = 100
RESIZING_FACTOR = FONT_SIZE / 1000
MARGIN_X = FONT_SIZE * 0.05
MARGIN_Y = FONT_SIZE * 0.25
DESCENDER = FONT_SIZE * 0.25
VERTICALLY_CENTERING_OFFSET = -(FONT_SIZE * 0.1)
GLYPH_NAME_MAPPINGS = resources.parse_goadb()

font = OpenFont('ITFDevanagari-Bold.ufo')

for (
    GID,
    (production_name, development_name, unicode_mapping)
) in enumerate(GLYPH_NAME_MAPPINGS):

    if development_name.startswith('dv'):

        glyph = font[development_name]

        extension_left  = 0
        extension_right = 0

        if glyph.leftMargin < 0:
            extension_left = abs(glyph.leftMargin) * RESIZING_FACTOR
        if glyph.rightMargin < 0:
            extension_right = abs(glyph.rightMargin) * RESIZING_FACTOR

        page_width  = extension_left + MARGIN_X + glyph.width * RESIZING_FACTOR + MARGIN_X + extension_right
        page_height = MARGIN_Y + FONT_SIZE + MARGIN_Y

        newPage(page_width, page_height)
        # fill(1)
        # rect(0, 0, width(), height())

        origin_x = round(MARGIN_X + extension_left)
        origin_y = MARGIN_Y + DESCENDER + VERTICALLY_CENTERING_OFFSET

        fill(None)
        stroke(0, 0.6, 1)
        strokeWidth(2)
        line((origin_x, origin_y), (origin_x, origin_y + FONT_SIZE * 0.75))
        lineDash(2, 2)
        stroke(0, 0.5, 1)
        boundary_right = origin_x + round(glyph.width * RESIZING_FACTOR)
        line((boundary_right, origin_y), (boundary_right, origin_y + FONT_SIZE * 0.75))

        t = FormattedString(
            font = 'ITFDevanagari-Bold',
            fontSize = FONT_SIZE
        )
        t.appendGlyph(production_name)
        text(t, (origin_x, origin_y))

        print "Saving GID: %s..." % str(GID)
        # saveImage('output/png/%s-%s.png' % (str(GID).zfill(4), development_name))

saveImage('output/pdf/glyphs.pdf', multipage = True)

print "Done!"
