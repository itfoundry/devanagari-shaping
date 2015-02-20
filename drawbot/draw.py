import time
import robofab.world
import resources

print "Start..."
start = time.clock()

FONT_SIZE = 100
RESIZING_FACTOR = FONT_SIZE / 1000
MARGIN_X = FONT_SIZE * 0.05
MARGIN_Y = FONT_SIZE * 0.25
DESCENDER = FONT_SIZE * 0.25
VERTICALLY_CENTERING_OFFSET = -(FONT_SIZE * 0.1)
GLYPH_NAME_MAPPINGS = resources.parse_goadb()

font = robofab.world.OpenFont('ITFDevanagari-Bold.ufo')

for (
    GID,
    (production_name, development_name, unicode_mapping)
) in enumerate(GLYPH_NAME_MAPPINGS):

    if development_name.startswith('dv') or development_name in [
        'danda',
        'doubledanda',
        'zerowidthnonjoiner',
        'zerowidthjoiner',
        'dottedcircle',
    ]:

        glyph = font[development_name]
        
        g_width = glyph.width * RESIZING_FACTOR
        g_margin_l = glyph.leftMargin * RESIZING_FACTOR
        g_margin_r = glyph.rightMargin * RESIZING_FACTOR
        
        extension_left  = 0
        extension_right = 0

        if g_margin_l < 0:
            extension_left = abs(g_margin_l)
        if g_margin_r < 0:
            extension_right = abs(g_margin_r)

        page_width  = extension_left + MARGIN_X + g_width + MARGIN_X + extension_right
        page_height = MARGIN_Y + FONT_SIZE + MARGIN_Y

        size(page_width, page_height)
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
        boundary_right = origin_x + round(g_width)
        line((boundary_right, origin_y), (boundary_right, origin_y + FONT_SIZE * 0.75))

        t = FormattedString(
            font = 'ITFDevanagari-Bold',
            fontSize = FONT_SIZE
        )
        t.appendGlyph(production_name)
        text(t, (origin_x, origin_y))

        saveImage([
            'output/png/%s-%s.png' % (str(GID).zfill(4), development_name),
            'output/png-no-gid/%s.png' % development_name,
        ])
        
        newDrawing()
        
# saveImage('output/pdf/glyphs.pdf', multipage = True)

print "Done!"
end = time.clock()
print end - start, 's'