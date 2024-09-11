# Run this with .ttf file path as an argument, and also an encoding if you like.
# It will make 16 PNGs with all the characters drawn.
import sys
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from pilmoji import Pilmoji
from pilmoji.source import GoogleEmojiSource

size = 36
per = 64
# 65 536
chars = 4_096  # 0x10000
per_page = per * per

# if len(sys.argv) < 2:
#     print('Usage: %s font file [encoding]' % sys.argv[0])
#     sys.exit(1)

# font_file = sys.argv[1]
# encoding = sys.argv[2] if len(sys.argv) > 2 else ''

# print(font_file)
# font = ImageFont.truetype(font_file, size, encoding=encoding)
font = ImageFont.truetype('Arial.ttf', size)

for page in range(0, chars // per_page):

    # im = Image.new("RGB", (size * per + 30, size * per + 30), '#ffffc0')
    # draw = ImageDraw.Draw(im)
    with Image.new("RGB", (size * per + 30, size * per + 30), (255, 255, 255)) as image:
        with Pilmoji(image, source=GoogleEmojiSource) as pilmoji:

            for line in range(0, per):
                for col in range(0, per):
                    c = page * per_page + line * per + col
                    # draw.text((col * size, line * size), chr(c), font=font, fill='black')
                    pilmoji.text((col * size, line * size), chr(2 * chars + c), (0, 0, 0), font)

        image.save('fonts/Google_chars_%03d.png' % (page))
