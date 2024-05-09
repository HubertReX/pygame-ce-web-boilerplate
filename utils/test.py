from typing import Any
from xml.etree import ElementTree

from functools import partial
from rich import inspect, pretty, print
from rich import traceback
help = partial(inspect, help=True, methods=True)
pretty.install()
traceback.install(show_locals=True, width=150,)


in_file = "DummyLevel.tmx"
out_file = "DummyLevel_MY.tmx"
new_width = 90
new_height = 30

def update_layers(in_file, out_file, new_width, new_height, layers_data: dict[str, Any]):
    root = ElementTree.parse(in_file).getroot()

    for map in root.iter("map"):
        map.attrib["width"] = str(new_width)
        map.attrib["height"] = str(new_height)
    for layer in root.iter("layer"):
        # help(layer)
        if layer.attrib["name"] in layers_data.keys():
            layer.attrib["width"] = str(new_width)
            layer.attrib["height"] = str(new_height)
            for data in layer.iter("data"):
                # print(data.text)
                data.text = "\n" + layers_data[layer.attrib["name"]] 
    et = ElementTree.ElementTree(root)
    with open(out_file, "wb") as f:
        et.write(f, encoding="utf-8")

layers = {
    "ala": "1,2,3",
    "floor": "99,98,97",
}
update_layers(in_file, out_file, new_width, new_height, layers)

