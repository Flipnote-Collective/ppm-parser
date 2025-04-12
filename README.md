>> This project has not been updated for some time and does not reflect the latest findings of our reverse-engineering efforts. For now, please refer to [flipnote.js](https://github.com/jaames/flipnote.js/blob/master/src/parsers/PpmParser.ts), as this is the closest thing to an up-to-date reference implementation.

Example decoder and utilities for Flipnote Studio's .ppm animation format. 

**This is not remotely optimised, and is for example purposes only**

All scripts were written for Python 3.7 and require the [numpy](http://www.numpy.org/) module to be installed.

### Credits

  * [jaames](https://github.com/jaames) for completing PPM reverse-engineering and writing this implementation.
  * [bricklife](http://ugomemo.g.hatena.ne.jp/bricklife/20090307/1236391313), [mirai-iro](http://mirai-iro.hatenablog.jp/entry/20090116/ugomemo_ppm), [harimau_tigris](http://ugomemo.g.hatena.ne.jp/harimau_tigris), and other members of the Japanese Flipnote community who started reverse-engineering the PPM format almost as soon as the app was released.
  * Midmad and WDLMaster for identifying the adpcm sound codec used.
  * [steven](http://www.dsibrew.org/wiki/User:Steven) and [yellows8](http://www.dsibrew.org/wiki/User:Yellows8) for the PPM documentation on DSiBrew.
  * [PBSDS](https://github.com/pbsds) for more PPM reverse-engineering, as well as writing [hatenatools](https://github.com/pbsds/Hatenatools)

## Utilities

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
