import os


def main() -> None:
    # path = r'project\\assets\\NinjaAdventure\\characters\\Boar'  # path to all .png images
    path = r'project\\assets'  # path to all .png images
    # file = r'C:\\Users\\user\\Downloads\\pngcrush_1_8_9_w64.exe'  # pngcrush file
    tool = r'pngcrush.exe'  # pngcrush file

    png_files = []

    for dirpath, subdirs, files in os.walk(path):
        for x in files:
            if x.endswith('.png'):
                png_files.append(os.path.join(dirpath, x))

    for name in png_files:
        cmd = r'{} -q -ow -rem allb -reduce {}'.format(tool, name)
        # cmd = r'{} -q -n -check {}'.format(tool, name)
        os.system(cmd)
        # print(cmd)


if __name__ == '__main__':
    main()
