import tkinter as tk
import pyscreenshot as ImageGrab
import pyautogui
from pynput import mouse, keyboard
import time
import csv
import signal
import sys
from pathlib import Path
import json
import os
import pandas as pd

with open("./data/meta.json") as fd:
  meta = json.loads(fd.read())

CTX = dict(
    meta=meta,
    keyboard=dict(w=False, e=False),
    mouse=dict(click=False, pointer=(0,0))
    )

# Set up a TKinter window to specify capture window
root = tk.Tk()

def moved(event):
    global CTX
    x = event.x
    y = event.y
    h = event.width
    w = event.width

    x2 = int(x + w)
    y2 = int(y + h)
    CTX['screen'] = (x, y, x2, y2)
    CTX['origin'] = dict(point=(x,y), geometry=f"{w}x{h}+{x}+{y}")

root.wait_visibility(root)
root.wm_attributes('-topmost', True, '-alpha', 0.5)
root.geometry("1320x1325+2602+71") # initialize
root.bind("<Configure>", moved)
root.mainloop()

print(CTX)
print("sleeping 3 secs so you have time to start game...")
time.sleep(3)
print("ok")

bbox = CTX['screen']

def on_move(x, y):
  global CTX
  ox, oy = CTX['origin']['point']

  # convert to relative points to image frame
  rx, ry = x-ox, y-oy
  CTX['mouse']['pointer'] = (rx, ry)

def on_click(x, y, button, pressed):
  global CTX
  CTX['mouse']['click'] = pressed


def on_press(key):
  try:
    if not key.char in CTX['keyboard']: return
    CTX['keyboard'][key.char] = True
  except AttributeError:
    pass

def on_release(key):
  try:
    if not key.char in CTX['keyboard']: return
    CTX['keyboard'][key.char] = False
  except AttributeError:
    pass


def trim_last_lines_of_file(path, deletions):
  df = pd.read_csv(path)

  for image in deletions:
    row = df[df.path == image.name]

    if len(row) == 1:
        df = df.drop(row.index[0])

  #  df.drop(df.tail(nlines).index, inplace=True)
  df.to_csv(path, index=False)


# remove last 2 images on ctrl-c because I probably died
def signal_handler(sig, frame):
  global CTX
  print('You pressed Ctrl+C!')

  try:
    print("saving meta")
    with open("./data/meta.json", "w") as fd:
        fd.write(json.dumps(CTX['meta']))

    print("deleting last three frames")
    deletions = sorted(list(Path("./data/images").iterdir()))[-3:]
    for p in deletions:
        print("+ deleting", p)
        p.unlink()


    print("deleting last three labels")
    trim_last_lines_of_file("./data/labels.csv", deletions)


  except Exception as err:
      print("!", err)
  finally:
    print("done")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)


with mouse.Listener(on_move=on_move, on_click=on_click, on_press=on_press) as ml:
  with keyboard.Listener(on_press=on_press, on_release=on_release) as kbl:
    labels = Path("./data/labels.csv")
    if not labels.exists():
      with open(labels, "w") as fd:
        writer = csv.writer(fd)
        writer.writerow(["path", "x", "y", "c", "w", "e"])

    with open(labels, "a") as fd:
      writer = csv.writer(fd)

      while True:
        CTX['meta']['idx'] += 1

        im = ImageGrab.grab(bbox=bbox)

        fname = '{:08d}.png'.format(CTX['meta']['idx'])
        im.save(f"data/images/{fname}")

        rx, ry = CTX['mouse']['pointer']
        c = int(CTX['mouse']['click'])
        w = int(CTX['keyboard']['w'])
        e = int(CTX['keyboard']['e'])

        line = [fname, rx, ry, c, w, e]
        writer.writerow(line)
        fd.flush() # don't buffer anything
        print(line)


