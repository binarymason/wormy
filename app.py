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
import math

with open("./data/meta.json") as fd:
  meta = json.loads(fd.read())

CTX = dict(
    meta=meta,
    keyboard=dict(w=False, e=False),
    mouse=dict(click=False, degrees=0),
    screen=dict(),
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

    midpoint = (int(x+w/2), int(y+h/2))

    CTX['screen'] = dict(bbox=(x, y, x2, y2), shape=(w, h), midpoint=midpoint)
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

bbox = CTX['screen']['bbox']

def on_move(x, y):
  global CTX
  ox, oy = CTX['origin']['point']
  mx, my = CTX['screen']['midpoint']

  # convert point to relative from center point
  # flip Y sign so forwards is a positive number
  rx, ry = x-mx, (y-my)*-1

  # given relative point, calculate theta angle from midpoint
  h = math.hypot(rx, ry)

  C = rx # always opposite from midpoint (origin) angle
  B = h
  A = ry

  if A == 0 and C == 0: # exact midpoint
    theta = 0
  elif A == 0: # horizontal
    theta = 90
  elif C == 0: # vertical
    if ry > 0: # forwards
      theta = 0
    else:
      theta = 180
  elif A == 0 and C == 0: # exact midpoint
    theta = 0
  else:
    theta = math.degrees(math.acos((A**2+B**2-C**2)/(2*A*B)))

  if rx < 0: # left side of screen
      theta += 180

  CTX['mouse']['degrees'] = theta

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
        writer.writerow(["path", "d", "c", "w", "e"])

    with open(labels, "a") as fd:
      writer = csv.writer(fd)

      while True:
        CTX['meta']['idx'] += 1

        im = ImageGrab.grab(bbox=bbox)

        fname = '{:08d}.png'.format(CTX['meta']['idx'])
        im.save(f"data/images/{fname}")

        d = float(CTX['mouse']['degrees']) / 359
        c = float(CTX['mouse']['click'])
        w = float(CTX['keyboard']['w'])
        e = float(CTX['keyboard']['e'])

        line = [fname, d, c, w, e]
        writer.writerow(line)
        fd.flush() # don't buffer anything
        print(line)


