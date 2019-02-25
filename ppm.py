import struct
import numpy as np

from PIL import Image

FRAMERATES = {
    1: 0.5,
    2: 1,
    3: 2,
    4: 4,
    5: 6,
    6: 12,
    7: 20,
    8: 30,
}

THUMBNAIL_PALETTE = [
  (0xFF, 0xFF, 0xFF),
  (0x52, 0x52, 0x52),
  (0xFF, 0xFF, 0xFF),
  (0x9C, 0x9C, 0x9C),
  (0xFF, 0x48, 0x44),
  (0xC8, 0x51, 0x4F),
  (0xFF, 0xAD, 0xAC),
  (0x00, 0xFF, 0x00),
  (0x48, 0x40, 0xFF),
  (0x51, 0x4F, 0xB8),
  (0xAD, 0xAB, 0xFF),
  (0x00, 0xFF, 0x00),
  (0xB6, 0x57, 0xB7),
  (0x00, 0xFF, 0x00),
  (0x00, 0xFF, 0x00),
  (0x00, 0xFF, 0x00),
]

BLACK = (0x0E, 0x0E, 0x0E)
WHITE = (0xFF, 0xFF, 0xFF)
BLUE = (0x0A, 0x39, 0xFF)
RED = (0xFF, 0x2A, 0x2A)

class PPMParser:
  @classmethod
  def open(cls, path):
    f = open(path, "rb")
    return cls(f)

  def __init__(self, stream=None):
    if stream: self.load(stream)

  def load(self, stream):
    self.stream = stream
    self.read_header()
    self.read_meta()
    self.read_animation_header()
    self.read_sound_header()
    self.layers = np.zeros((2, 192, 256), dtype=np.uint8)
    self.prev_layers = np.zeros((2, 192, 256), dtype=np.uint8)
    self.prev_frame_index = -1
  
  def unload(self):
    self.stream.close()

  def read_header(self):
    # decode header
    # https://github.com/pbsds/hatena-server/wiki/PPM-format#file-header
    self.stream.seek(0)
    magic, animation_data_size, sound_data_size, frame_count, version = struct.unpack("<4sIIHH", self.stream.read(16))
    self.animation_data_size = animation_data_size
    self.sound_data_size = sound_data_size
    self.frame_count = frame_count + 1

  def read_filename(self):
    # Parent and current filenames are stored as:
    #  - 3 bytes representing the last 6 digits of the Consoles's MAC address
    #  - 13-character string
    #  - uint16 edit counter
    mac, ident, edits = struct.unpack("<3s13sH", self.stream.read(18));
    # Filenames are formatted as <3-byte MAC as hex>_<13-character string>_<edit counter as a 3-digit number>
    # eg F78DA8_14768882B56B8_030
    return "{0}_{1}_{2:03d}".format("".join(["%02X" % c for c in mac]), ident.decode("ascii"), edits)
    
  def read_meta(self):
    # decode metadata
    # https://github.com/pbsds/hatena-server/wiki/PPM-format#file-header
    self.stream.seek(0x10)
    self.lock, self.thumb_index = struct.unpack("<HH", self.stream.read(4))
    self.root_author_name = self.stream.read(22).decode("utf-16").rstrip("\x00")
    self.parent_author_name = self.stream.read(22).decode("utf-16").rstrip("\x00")
    self.current_author_name = self.stream.read(22).decode("utf-16").rstrip("\x00")
    self.parent_author_id = "%016X" % struct.unpack("<Q", self.stream.read(8))
    self.current_author_id = "%016X" % struct.unpack("<Q", self.stream.read(8))
    self.parent_filename = self.read_filename()
    self.current_filename = self.read_filename()
    self.root_author_id = "%016X" % struct.unpack("<Q", self.stream.read(8))
    self.partial_filename = self.stream.read(0) # not really useful for anything :/
    self.timestamp = struct.unpack("<I", self.stream.read(4))

  def read_thumbnail(self):
    self.stream.seek(0xA0)
    bitmap = np.zeros((48, 64), dtype=np.uint8)
    for tile_index in range(0, 48):
      tile_x = tile_index % 8 * 8
      tile_y = tile_index // 8 * 8
      for line in range(0, 8):
        for pixel in range(0, 8, 2):
          byte = ord(self.stream.read(1))
          x = tile_x + pixel
          y = tile_y + line
          bitmap[y][x] = byte & 0x0F
          bitmap[y][x + 1] = (byte >> 4) & 0x0F
    return bitmap

  def read_animation_header(self):
    self.stream.seek(0x06A0)
    table_size, unknown, flags = struct.unpack("<HHI", self.stream.read(8))
    # unpack animation flags
    self.layer_1_visible = (flags >> 11) & 0x01
    self.layer_2_visible = (flags >> 10) & 0x01
    self.loop = (flags >> 1) & 0x01
    # read offset table into a numpy array
    offset_table = np.frombuffer(self.stream.read(table_size), dtype=np.uint32)
    self.offset_table = [offset + 0x06A0 + 8 + table_size for offset in offset_table]
  
  def read_sound_header(self):
    # https://github.com/pbsds/hatena-server/wiki/PPM-format#sound-data-section
    # offset = frame data offset + frame data length + sound effect flags
    offset = 0x06A0 + self.animation_data_size + self.frame_count;
    # account for multiple-of-4 padding
    if offset % 4 != 0: offset += 4 - (offset % 4)
    self.stream.seek(offset)
    bgm_size, se1_size, se2_size, se3_size, frame_speed, bgm_speed = struct.unpack("<IIIIBB", self.stream.read(18))
    self.frame_speed = 8 - frame_speed
    self.bgm_speed = 8 - bgm_speed
    self.framerate = FRAMERATES[self.frame_speed]
    self.bgm_framerate = FRAMERATES[self.bgm_speed]

  def is_frame_new(self, index):
    self.stream.seek(self.offset_table[index])
    return ord(self.stream.read(1)) >> 7 & 0x1
  
  def read_line_types(self, line_types):
    for index in range(192):
      line_type = line_types[index // 4] >> ((index % 4) * 2) & 0x03
      yield (index, line_type)

  def read_frame(self, index):
    if index != 0 and self.prev_frame_index != index - 1 and not self.is_frame_new(index):
      self.read_frame(index - 1)
    # copy the current layer buffers to the previous ones
    np.copyto(self.prev_layers, self.layers)
    self.prev_frame_index = index
    # clear current layer buffers by reseting them to 0
    self.layers.fill(0)
    # seek to the frame offset so we can start reading
    self.stream.seek(self.offset_table[index])
    # unpack frame header flags
    header = ord(self.stream.read(1))
    is_new_frame = (header >> 7) & 0x1
    is_translated = (header >> 5) & 0x3
    translation_x = 0
    translation_y = 0
    # if the frame is translated, we need to unpack the x and y values
    if is_translated:
      translation_x, translation_y = struct.unpack("<bb", self.stream.read(2))
    # read line encoding bytes
    line_types = [
      self.stream.read(48),
      self.stream.read(48),
    ]
    # loop through layers
    for layer in range(2):
      bitmap = self.layers[layer]
      for line, line_type in self.read_line_types(line_types[layer]):
        pixel = 0
        # no data stored for this line
        if line_type == 0:
          pass
        # compressed line
        elif line_type == 1 or line_type == 2:
          # if line type == 2, the line starts off with all the pixels set to 1
          if line_type == 2:
            for i in range(256):
              bitmap[line][i] = 1
          # unpack chunk usage
          chunk_usage = struct.unpack(">I", self.stream.read(4))[0]
          # unpack pixel chunks
          while pixel < 256:
            if chunk_usage & 0x80000000:
              chunk = ord(self.stream.read(1))
              for bit in range(8):
                bitmap[line][pixel] = chunk >> bit & 0x1
                pixel += 1
            else:
              pixel += 8
            chunk_usage <<= 1
        # raw line
        elif line_type == 3:
          # unpack pixel chunks
          while pixel < 256:
            chunk = ord(self.stream.read(1))
            for bit in range(8):
              bitmap[line][pixel] = chunk >> bit & 0x1
              pixel += 1
    
    # frame diffing
    # this is a big performance bottleneck
    if not is_new_frame:
      for y in range(192):
        # if line is out of range, skip
        if (y - translation_y >= 192) or (y - translation_y < 0): 
          continue
        for x in range(256):
          # if pixel is out of range, skip
          if (x - translation_x >= 256) or (x - translation_x < 0): 
            continue
          self.layers[0][y][x] ^= self.prev_layers[0][y - translation_y][x - translation_x]
          self.layers[1][y][x] ^= self.prev_layers[1][y - translation_y][x - translation_x]

    return self.layers

  def get_frame_palette(self, index):
    self.stream.seek(self.offset_table[index])
    header = ord(self.stream.read(1))
    paper_color = header & 0x1;
    pen = [
      None,
      BLACK if paper_color == 1 else WHITE,
      RED,
      BLUE,
    ]
    return [
      WHITE if paper_color == 1 else BLACK,
      pen[(header >> 1) & 0x3], # layer 1 color
      pen[(header >> 3) & 0x3], # layer 2 color
    ];

  def get_frame_pixels(self, index):
    layers = self.read_frame(index)
    pixels = np.zeros((192, 256), dtype=np.uint8)
    for y in range(192):
      for x in range(256):
        if layers[0][y][x] > 0: pixels[y][x] = 1
        elif layers[1][y][x] > 0: pixels[y][x] = 2
    return pixels