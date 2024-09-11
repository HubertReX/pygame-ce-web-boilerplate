from pilmoji import Pilmoji
from PIL import Image, ImageFont
from pilmoji.source import GoogleEmojiSource

# pip uninstall emoji
# pip install emoji == 1.7

# use https://github.com/alexmick/emoji-data-python for emoji data search
size = 36
my_string = '''🦹🏾‍♀️'''
# 👋🎨🌊😎
# I also support Discord emoji: <:rooThink:596576798351949847>
with Image.new('RGB', (size, size), (255, 255, 255)) as image:
    font = ImageFont.truetype('Arial.ttf', size)
    # font = None  # ImageFont.truetype('Tahoma.ttf', 24)

    with Pilmoji(image, source=GoogleEmojiSource) as pilmoji:
        # If an emoji looks too small or too big, or out of place,
        # you can make fine adjustments like emoji_scale_factor=1.15, emoji_position_offset=(0, -2)
        pilmoji.text((0, 0), my_string.strip(), (0, 0, 0), font)

    image.show()
