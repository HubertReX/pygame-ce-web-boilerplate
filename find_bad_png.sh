# https://stackoverflow.com/questions/22745076/libpng-warning-iccp-known-incorrect-srgb-profile#22747902
# cd project/assets/NinjaAdventure
pngcrush -n -q **/*.png 2> >(grep -v "Total")
