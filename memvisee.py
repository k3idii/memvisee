import pygame
import time
import argparse

KEYMAP = {}

def add_key_map(key, func):
  """ adds entry in global keymap dict """
  KEYMAP[key] = func

def keyz(keys):
  """ convert strin-of-chars into list-of-integers """
  return map(ord, keys)

def hotkey(arg):
  """ add hotkey(s) to KEYMAP list """
  def _wrap(func):
    for key in arg:
      add_key_map(key, func)
    return func
  return _wrap

def bit2raw(bits):
  return int(''.join(map(str,bits)),2)

class MasterClass(object):
  file_handle = None
  file_offset = None
  pix_per_row = 100
  max_rows = 700
  the_screen = None
  keep_working = True
  need_redraw = True

  kbd_state = {}
  
  step_small_horiz = 1
  step_big_horiz = 33
  step_small_vert = 11
  step_big_vert = 500000

  x_space = 10
  buffer = []

  put_pixel = None # func 


  def __init__(self, filename=None, bit_per_pixel=24, skip=0, xres=800, yres=800, pix_size=1):
    self.file_name = filename
    self.file_handle = open(filename, 'rb')
    self.file_offset = 0x00
    if bit_per_pixel < 1:
      bit_per_pixel = 1
    self.bit_per_pixel = bit_per_pixel
    self.skip = skip
    if xres < 100:
      xres = 100
    if yres < 100:
      yres = 100
    self.xres = xres
    self.yres = yres
    if pix_size < 1:
      pix_size = 1
    self.pix_size = pix_size
    self.the_screen = pygame.display.set_mode([self.xres * pix_size, self.yres * pix_size])
    if pix_size == 1:
      self.put_pixel = self._put_pixel_1
    else:
      self.put_pixel = self._put_pixel_n

    self.max_color = 2 << (self.bit_per_pixel - 1)
    self.color_coef = 0xFFffFF / (self.max_color-1.0)
    self.make_color = self._make_color_rgb
    if self.bit_per_pixel == 24:
        self.make_color = self._make_color_24

    print self.bit_per_pixel % 8
    if self.bit_per_pixel % 8 == 0:
      self.get_next_piexl = self._get_next_8
      self.chunk_size = self.bit_per_pixel / 8
    else:
      self.get_next_piexl = self._get_next_x
    self.keep_working = True



  def start(self):
    while self.keep_working:
      time.sleep(0.01)
      for ev in pygame.event.get():
        if ev.type == pygame.QUIT:
          print(" !! QUIT !!")
          return self.stop()
        if ev.type == pygame.KEYDOWN:
          key = ev.key
          self.kbd_state[key] = 1
          # print "KEYPRES " ,key
        if ev.type == pygame.KEYUP:
          key = ev.key
          try:
            del self.kbd_state[key]
            #print "KEYUP", key
          except Exception as err:
            print("Fail to release key: {0} reason:{1}".format(str(key), str(err)))

      for key in self.kbd_state:
        action = KEYMAP.get(key, None)
        if action and callable(action):
          action(self)

      if self.need_redraw:
        self.the_screen.fill((0, 0, 0))
        print "file_offset : ", self.file_offset, hex(self.file_offset)
        self.update_screen()
        pygame.display.flip()
        self.need_redraw = False

  def repaint(self):
    self.need_redraw = True

  @hotkey(keyz("qQ"))
  def stop(self):
    print("WILL STOP keep_workingING !")
    self.keep_working = False

  @hotkey([61])
  def inc_row_size(self):
    self.repaint()
    self.pix_per_row += self.step_big_horiz
    if self.pix_per_row >= self.xres:
      print("XRES LIMIT !")
      self.pix_per_row = self.xres - 1


  @hotkey([45])
  def dec_row_size(self):
    self.repaint()
    self.pix_per_row -= self.step_big_horiz
    if self.pix_per_row < 1:
      self.pix_per_row = 1

  @hotkey([281])
  def go_down(self):
    self.repaint()
    self.file_offset += self.step_big_vert

  @hotkey([280])
  def go_up(self):
    self.repaint()
    self.file_offset -= self.step_big_vert
    if self.file_offset < 0:
      self.file_offset = 0

  @hotkey([273])
  def go_up_1(self):
    self.repaint()
    self.file_offset -= self.step_small_vert
    if self.file_offset < 0:
      self.file_offset = 0

  @hotkey([274])
  def go_down_1(self):
    self.repaint()
    self.file_offset += self.step_small_vert

  @hotkey([276])
  def go_left_1(self):
    self.repaint()
    self.pix_per_row -= self.step_small_horiz
    if self.pix_per_row < 1:
      self.pix_per_row = 1

  @hotkey([275])
  def go_right_1(self):
    self.repaint()
    self.pix_per_row += self.step_small_horiz

  def go_to_pos(self): ## TODO <- implement me
    # read from user
    self.repaint()

  def _put_pixel_1(self, posx, posy, color): ## putpixel for 1px
    self.the_screen.set_at((posx, posy), color)

  def _put_pixel_n(self, posx, posy, color): ## generic putpixel
    self.the_screen.fill(color, rect=(posx*self.pix_size, posy*self.pix_size, self.pix_size, self.pix_size))

  def _make_color_rgb(self, idx):
    return int(idx * self.color_coef)

  def _make_color_24(self, idx):
    return idx

  def _get_next_8(self):
    tmp = self.file_handle.read(self.chunk_size)
    self.file_handle.read(self.skip)
    if len(tmp) != self.chunk_size:
      raise Exception("EOF HIT1")
    return self.make_color(int(tmp.encode('hex'),16))

  def _get_next_x(self):
    while len(self.buffer) < self.bit_per_pixel:
      one_byte = self.file_handle.read(1)
      if len(one_byte) != 1 or one_byte is None:
        raise Exception("EOF HIT2")
      self.buffer.extend(list(bin(ord(one_byte))[2:].rjust(8, '0')))
    tmp = self.buffer[:self.bit_per_pixel]
    self.buffer = self.buffer[self.bit_per_pixel+self.skip:]
    return self.make_color(bit2raw(tmp))

  def update_screen(self):
    self.file_handle.seek(self.file_offset)
    col_size = self.pix_per_row + self.x_space
    col_count = self.xres / col_size ## int rount will do the job
    t1 = time.time()
    try:
      for col_no in range(col_count):
        pad = col_no * col_size
        for row in range(self.yres):
          for pix_x in range(self.pix_per_row):
            self.put_pixel(pad + pix_x, row, self.get_next_piexl())  
    except Exception as err:
      print("Fail to render : {0}".format(str(err)))
    dt = time.time() - t1
    print("Rendered in {0} seconds ".format(dt))

def main():
  parser = argparse.ArgumentParser(description='MVS == MEMory VIsual SEEker :-) ')
  parser.add_argument("filename", action="store", help="Data file name")
  parser.add_argument("--bps", action="store", dest="bit_per_pixel", default=24, type=int, help="bits per pixel")
  parser.add_argument("--skip", action="store", default=0, type=int, help="Skipt N bits after pixel ... Usefull to skip alpha")
  parser.add_argument("--xres", action="store", default=800, type=int, help="GUI X-size of window (in pix_size), def=800")
  parser.add_argument("--yres", action="store", default=800, type=int, help="GUI Y-size of window (in pix_size), def=800")
  parser.add_argument("--pix-size", action="store", default=1, type=int, help="Pixel size (square), def=1")
  opts = parser.parse_args()
  print opts
  try:
    obj = MasterClass(**vars(opts))
  except Exception as ex:
    print("Fail to setup, reason : [{0}]".format(str(ex)))
    return
  obj.start()


if __name__ == '__main__':
  main()

