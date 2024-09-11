import emoji
import emoji_data_python
# https://carpedm20.github.io/emoji/docs/

# emoji_data_python.emoji_short_names['RAINBOW'].__dict__
# name = emoji.demojize("🦹🏾‍♀️").replace("_", " ")
name = emoji.demojize("🦹").replace("_", " ").replace(":", "")
print(emoji_data_python.find_by_shortname(name))
print(emoji_data_python.find_by_name(name))
# rainbow = emoji_data_python.find_by_name("RAINBOW")[0]
# print(rainbow.sheet_x, rainbow.sheet_y,)
# print(emoji_data_python.replace_colons('Hello world ! :wave::skin-tone-3: :earth_africa: :exclamation:'))
# sheet_size = 64
# x = (rainbow.sheet_x * (sheet_size + 2)) + 1
# y = (rainbow.sheet_y * (sheet_size + 2)) + 1
# # EmojiChar("RAINBOW")
# print(x, y)


# :woman_supervillain_medium-dark_skin_tone:
print(emoji.emojize(':woman_supervillain:'))  # , language='alias' , variant="emoji_type")
print(emoji.emojize(':woman_supervillain_medium-dark_skin_tone:'))
print(emoji.is_emoji("❤️"))
print(emoji.is_emoji("🦹🏾‍♀️"))

print(emoji.emoji_list("This 🦹 text has some emojis 🦹🏾‍♀️ and not emojis"))

print(len("🦹"), emoji.demojize("🦹"), )
print(len("🦹🏾"), emoji.demojize("🦹🏾"), )
print(len("🦹‍♀️"), emoji.demojize("🦹‍♀️"), )
print(len("🦹🏾‍♀️"), emoji.demojize("🦹🏾‍♀️"), )
# print(ord(u"🦹🏾‍♀️")) # error
# print(hex(ord(u"🦹🏾‍♀️")))
