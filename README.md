Example decoder and utilities for Flipnote Studio's .ppm animation format. 

**This is not remotely optimised, and is for example purposes only**

All scripts were written for Python 3.7 and require the [numpy](http://www.numpy.org/) module to be installed.

### ppmImage

Converts specific ppm frames to standard image formats such as png, gif, jpeg, etc. Requires the [Pillow](https://pillow.readthedocs.io/en/5.2.x/) module to be installed.

Usage: 

```bash
python ppmImage.py <input path> <frame index> <output path>
```

`<frame index>`:
  
 * Specific frame index (e.g. `0` for the first frame)
 * `thumb` to get the thumbnail frame
 * `gif` to encode the whole Flipnote to an animated GIF.

`<output path>`:

 * Can include placeholders: `{name}` for the input filename (without extention), `{ext}` for input extention, `{index}` for the item index and `{dirname}` for the input file directory.

`<input path>`:

 * You can pass glob patterns as the input filepath to batch convert. For example, the following will extract thumbnail images from all the ppms in a directory:

	```bash
	python ppmImage.py "/flipnotes/*.ppm" thumb /flipnotes/{name}.png
	```
