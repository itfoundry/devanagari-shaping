import time
# import robofab.world
import resources

SAVE_A_PDF_INSTEAD_OF_PNGS = True

INCLUDE_GLYPH_NAMES_IN_FILE_NAMES = True

# Rasterization options

FONT_SIZE = 100
RESIZING_FACTOR = FONT_SIZE / 1000
MARGIN_X = FONT_SIZE * 0.05
MARGIN_Y = FONT_SIZE * 0.35
DESCENDER = FONT_SIZE * (350 / (350 + 1050))
VERTICALLY_CENTERING_OFFSET = FONT_SIZE * -0.1

print "Start..."
start = time.clock()

GLYPH_NAME_MAPPINGS = resources.parse_goadb()

# font = robofab.world.OpenFont('../resources/ITFDevanagari/ITFDevanagari-Light.ufo')

boundaries_t = []
boundaries_b = []

# print font.info.unitsPerEm
# family_name = font.info.openTypeNamePreferredFamilyName
# style_name = font.info.openTypeNamePreferredSubfamilyName
# print font.info.openTypeNameVersion


# drawPath(font['uni0915'].draw(CocoaPen(font)))

# for (
#     gid,
#     (production_name, development_name, unicode_mapping)
# ) in enumerate(GLYPH_NAME_MAPPINGS):

#     if development_name.startswith('dv') or development_name in [
#         'danda',
#         'doubledanda',
#         'zerowidthnonjoiner',
#         'zerowidthjoiner',
#         'dottedcircle',
#     ]:

#         glyph = font[development_name]
        
#         boundaries_t.append(glyph.box[3])
#         boundaries_b.append(glyph.box[1])
        
#         g_width = glyph.width * RESIZING_FACTOR
#         g_margin_l = glyph.leftMargin * RESIZING_FACTOR
#         g_margin_r = glyph.rightMargin * RESIZING_FACTOR
        
#         extension_left  = 0
#         extension_right = 0

#         if g_margin_l < 0:
#             extension_left = abs(g_margin_l)
#         if g_margin_r < 0:
#             extension_right = abs(g_margin_r)

#         page_width  = round((extension_left + MARGIN_X + g_width + MARGIN_X + extension_right) / 2) * 2
#         page_height = MARGIN_Y + FONT_SIZE + MARGIN_Y

#         newPage(page_width, page_height)
#         fill(1)
#         rect(0, 0, width(), height())

#         origin_x = round(MARGIN_X + extension_left)
#         origin_y = MARGIN_Y + DESCENDER + VERTICALLY_CENTERING_OFFSET
        
#         t = FormattedString(
#             font = 'ITFDevanagari-Bold',
#             fontSize = FONT_SIZE
#         )
#         t.appendGlyph(production_name)
#         text(t, (origin_x, origin_y))

#         fill(None)
#         strokeWidth(2)
        
#         if g_width == 0:
#             stroke(1, 0.3, 0.1)
#             line((origin_x, origin_y), (origin_x, origin_y + FONT_SIZE * 0.75))
            
#         else:
#             stroke(0.6)
#             line((origin_x, origin_y - 1), (origin_x, origin_y + 1))
#             boundary_right = round(origin_x + g_width)
#             line((boundary_right, origin_y + 1), (boundary_right, origin_y - 4))
#             line((boundary_right - 1, origin_y), (boundary_right + 4, origin_y))

#         if not SAVE_A_PDF_INSTEAD_OF_PNGS:
            
#             file_name = str(gid).zfill(4)
            
#             if INCLUDE_GLYPH_NAMES_IN_FILE_NAMES:
#                 file_name += '-' + development_name
                
#             print file_name
            
#             saveImage('output/png/' + file_name + '.png')
#             newDrawing()

# if SAVE_A_PDF_INSTEAD_OF_PNGS:
#     saveImage('output/pdf/glyphs.pdf', multipage = True)

# print max(boundaries_t), min(boundaries_b)

print "Done!"
end = time.clock()
print end - start, 's'