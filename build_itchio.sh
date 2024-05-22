# blocking (when using sounds)
# pygbag --ume_block 1 --template utils/black.tmpl --icon project/assets/icon.png --no_opt --archive project

# non blocking - quicker (when there are no sounds) --template custom, without ctx for zengl to work --no_opt so the pixel art is not distorted with optimisation
pygbag --ume_block 0 --template utils/black.tmpl --icon project/assets/icon.png --no_opt --archive project

