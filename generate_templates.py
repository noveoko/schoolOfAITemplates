#!/usr/bin/env python
import svglue
import cairosvg
#SVG templates
facebook_fanpage_header_image = 'Facebook/Facebook_fan_page_headerimage.svg'
#template variables
city_name_FBFPHI = "city_name"
city_photo_FBFPHI = "city_photo"

name_of_your_city = "Paris" #ENTER **YOUR** CITY NAME!
path_to_your_image = 'images/architecture-buildings-church-338515.jpg' #ENTER Path your your FB Fanpage header image (PNG format)

all_image_templates = [facebook_fanpage_header_image] #list of all template files

for template in all_image_templates:
    # load the template from a file
    tpl = svglue.load(file=template)

    # replace some text
    tpl.set_text("city_name", str(name_of_your_city))

    # replace the pink box with 'hello.png'. if you do not specify the mimetype,
    # the image will get linked instead of embedded
    tpl.set_image("city_photo", file=path_to_your_image, mimetype='image/png')

    # svgs are merged into the svg document (i.e. always embedded)
    tpl.set_svg('yellow-box', file='Ghostscript_Tiger.svg')

    # to render the template, cast it to a string. this also allows passing it
    # as a parameter to set_svg() of another template
    src = str(tpl)

    # write out the result as an SVG image and render it to pdf using cairosvg
    with open('output.pdf', 'w') as out, open('output.svg', 'w') as svgout:
        svgout.write(src)
        cairosvg.svg2pdf(bytestring=src, write_to=out)
