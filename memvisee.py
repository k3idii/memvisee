import pygame
import time

SCREEN_SIZE = [800, 800]

KEYMAP = {}

def add_key_map(key, func):
  # global KEYMAP
  KEYMAP[key] = func

def keyz(keys):
  return map(ord, keys)

def hotkey(arg):
  def _wrap(func):
    for key in arg:
      add_key_map(key, func)
    return func
  return _wrap


class MasterClass(object):
  file_handle = None
  file_offset = None
  pix_per_row = 100
  max_rows = 700
  the_screen = None
  keep_working = True
  need_redraw = True
  data_format = 'RGB'
  kbd = {}
  step_small_horiz = 1
  step_big_horiz = 33
  step_small_vert = 11
  step_big_vert = 500000


  def __init__(self, fn):
    self.file_handle = open(fn, 'rb')
    self.file_offset = 0x00
    self.keep_working = True
    self.the_screen = pygame.display.set_mode(SCREEN_SIZE)

  def start(self):
    while self.keep_working:
      time.sleep(0.01)
      for ev in pygame.event.get():
        if ev.type == pygame.QUIT:
          print " !! QUIT !!"
          self.stop()
          return
        if ev.type == pygame.KEYDOWN:
          key = ev.key
          self.kbd[key] = 1
          #print "KEYPRES " ,key
        if ev.type == pygame.KEYUP:
          key = ev.key
          try:
            del self.kbd[key]
            #print "KEYUP", key
          except Exception as err:
            print "Fail to release key: ", key, "reason:", str(err)

      for key in self.kbd:
        action = KEYMAP.get(key, None)
        if action and callable(action):
          action(self)

      if self.need_redraw:
        self.the_screen.fill((0, 0, 0))
        print "file_offset : ", self.file_offset, hex(self.file_offset)
        self.update_screen()
        pygame.display.flip()
        self.need_redraw = False

  def rd(self):
    self.need_redraw = True

  @hotkey(keyz("qQ"))
  def stop(self):
    print "WILL STOP keep_workingING !"
    self.keep_working = False

  @hotkey([61])
  def inc_row_size(self):
    self.rd()
    self.pix_per_row += self.step_big_horiz

  @hotkey([45])
  def dec_row_size(self):
    self.rd()
    self.pix_per_row -= self.step_big_horiz
    if self.pix_per_row < 1:
      self.pix_per_row = 1

  @hotkey([281])
  def go_down(self):
    self.rd()
    self.file_offset += self.step_big_vert

  @hotkey([280])
  def go_up(self):
    self.rd()
    self.file_offset -= self.step_big_vert
    if self.file_offset < 0:
      self.file_offset = 0

  @hotkey([273])
  def go_up_1(self):
    self.rd()
    self.file_offset -= self.step_small_vert
    if self.file_offset < 0:
      self.file_offset = 0

  @hotkey([274])
  def go_down_1(self):
    self.rd()
    self.file_offset += self.step_small_vert

  @hotkey([276])
  def go_left_1(self):
    self.rd()
    self.pix_per_row -= self.step_small_horiz
    if self.pix_per_row < 1:
      self.pix_per_row = 1

  @hotkey([275])
  def go_right_1(self):
    self.rd()
    self.pix_per_row += self.step_small_horiz

  @hotkey(keyz('Ff'))
  def set_format(self):
    print
    print "ENTER NEW FORMAT STRING (RBG ... ) :"
    tmp = raw_input()
    print "New format : ", `tmp`
    self.data_format = tmp
    self.rd()

  def go_to_pos(self):
    # read from user
    self.rd()


  def update_screen(self):
    self.file_handle.seek(self.file_offset)
    chunk_size = len(self.data_format)
    def put_pix(x, y, color):
      self.the_screen.set_at((x, y), color)
    pos = {}
    for c in 'RGB':
      pos[c] = self.data_format.index(c)

    row_and_space = self.pix_per_row + 20
    #              .-- 700 = 800 -100 lol ! get_SCREEN_SIZE(moron)
    num_stripes = 700 / row_and_space

    if num_stripes < 1:
      num_stripes = 1
    try:
      t1 = time.time()
      for ss in range(num_stripes):
        pad = ss * row_and_space
        for row in range(self.max_rows):
          for col in range(self.pix_per_row):
            ch = map(ord, self.file_handle.read(chunk_size))
            put_pix(pad + col, row, (ch[pos['R']], ch[pos['G']], ch[pos['B']]))
      dt = time.time() - t1
      print "Rendered in ", dt, " seconds "
    except Exception as err:
      print "Error : ", str(err)


def main():
  import sys
  if len(sys.argv) != 2:
    print "Usage : %s file.dump , use --help for help ;-)" % sys.argv[0]
    return
  if sys.argv[1] == '--help':
    print "Keys:"
  filename = sys.argv[1]
  obj = MasterClass(filename)
  obj.start()



if __name__ == '__main__':
  main()

