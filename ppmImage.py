# =========================
# ppmImage.py version 1.0.0
# =========================
# 
# Extracts frame images from Flipnote PPMs
# 
# Usage:
# python ppmImage.py <input path> <frame index> <output path>

import glob
from sys import argv
import os
from ppm import PPMParser
from PIL import Image

def get_image(parser, index):
  frame = parser.get_frame_pixels(index)
  colors = parser.get_frame_palette(index)
  img = Image.fromarray(frame, "P")
  img.putpalette([*colors[0], *colors[1], *colors[2]])
  return img

parser = PPMParser()
filelist = glob.glob(argv[1], recursive=True)

for (index, path) in enumerate(filelist):
  with open(path, "rb") as ppm:
    basename = os.path.basename(path)
    dirname = os.path.dirname(path)
    filestem, ext = os.path.splitext(basename)
    outpath = argv[3].format(name=filestem, dirname=dirname, index=index, ext=ext)

    print("Converting", path, "->", outpath)
    parser.load(ppm)

    if argv[2] == "gif":
      frame_duration = (1 / parser.framerate) * 1000
      frames = [get_image(parser, i) for i in range(parser.frame_count)]
      frames[0].save(outpath, format="gif", save_all=True, append_images=frames[1:], duration=frame_duration, loop=False)

    elif argv[2] == "thumb":
      img = get_image(parser, parser.thumb_index)
      img.save(outpath)

    else:
      index = int(argv[2])
      img = get_image(parser, index)
      img.save(outpath)

    parser.unload()