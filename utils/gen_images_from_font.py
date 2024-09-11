# Run this with .ttf file path as an argument, and also an encoding if you like.
# It will make 16 PNGs with all the characters drawn.
import sys
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

size = 36
per = 8  # 64
# 65 536
chars = 256  # 0x10000
per_page = per * per

if len(sys.argv) < 2:
    print('Usage: %s font file [encoding]' % sys.argv[0])
    sys.exit(1)

font_file = sys.argv[1]
encoding = sys.argv[2] if len(sys.argv) > 2 else ''

print(font_file)
font = ImageFont.truetype(font_file, size, encoding=encoding)

for page in range(0, chars // per_page):

    im = Image.new("RGB", (size * per + 30, size * per + 30), '#ffffc0')
    draw = ImageDraw.Draw(im)

    for line in range(0, per):
        for col in range(0, per):
            c = page * per_page + line * per + col
            draw.text((col * size, line * size), chr(c), font=font, fill='black')

    im.save('fonts/%s_chars_%03d.png' % (font_file[:-4], page))
