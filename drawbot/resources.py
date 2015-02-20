def parse_goadb():

    with open('GlyphOrderAndAliasDB', 'r') as f:
        goadb_content = f.read()

    GLYPH_NAME_MAPPINGS = []

    for line in goadb_content.splitlines():

        line_with_content = line.split('#', 2)[0] # Remove comments

        if line_with_content:
            line_parts = line_with_content.split()
            if len(line_parts) == 2: # For lines with no Unicode mapping
                line_parts.append(None)
            GLYPH_NAME_MAPPINGS.append(tuple(line_parts))

    return(GLYPH_NAME_MAPPINGS)
