import tkinter as tk
import functools
import math
import numpy as np
from tkinter import ttk

root = tk.Tk()
root.resizable(False,False)
root.overrideredirect(True)
root.lift()
root.wm_attributes("-topmost", True)
root.attributes('-alpha', 0.5)
root.geometry("+507+150")
root.wm_attributes('-transparentcolor', '#60b26c')

MENU_HEIGHT = 100
GB_WIDTH = 1440 # 1280
GB_HEIGHT = 900 #720 # 900
BOOMER_ANG_REV = 35
BOOMER_ANG_FORWARD = 45

__CANVAS = None
__STATE = None

__target_x = None
__target_y = None

__drag_item = None
__drag_x = 0
__drag_y = 0


def set_state(state):
    global __STATE
    __STATE = state

def overlay():
    global __CANVAS
    content = ttk.Frame(root, borderwidth=1, relief="solid", width=GB_WIDTH, height=(GB_HEIGHT+MENU_HEIGHT))
    content.grid(column=0, row=0, padx=50, pady=20)

    # gunbound
    gunbound = ttk.Frame(content, borderwidth=1, relief="solid", width=GB_WIDTH, height=GB_HEIGHT)
    gunbound.grid(column=0, row=1, sticky="nsew")

    ## wind circle overlay
    canvas = tk.Canvas(gunbound, width=GB_WIDTH, height=GB_HEIGHT, background='#60b26c', borderwidth=1, relief="solid")
    canvas.create_oval(GB_WIDTH/2-40, 5, GB_WIDTH/2+40, 85, outline='blue', width=4)
    canvas.create_line(0, 45, GB_WIDTH, 45, fill='red')
    canvas.create_line(GB_WIDTH / 2, 0, GB_WIDTH/2, GB_HEIGHT, fill='red')
    canvas.create_rectangle(GB_WIDTH/2-20, GB_HEIGHT/2-20, GB_WIDTH/2+20, GB_HEIGHT/2+20, fill='green', tags="target",)
    canvas.grid(column=0, row=0, sticky="nsew")

    # wind token
    __wind_drag_oval = canvas.create_oval(GB_WIDTH/2-10, 35, GB_WIDTH/2+10, 55, fill='green', tags=("token",))

    self.canvas.tag_bind("target", "<ButtonPress-1>", canvas_target_place)
    self.canvas.tag_bind("token", "<ButtonPress-1>", canvas_drag_start)
    self.canvas.tag_bind("token", "<ButtonRelease-1>", canvas_drag_stop)
    self.canvas.bind("<Button-1>", canvas_on_click)
    canvas.tag_bind("token", "<B1-Motion>", canvas_drag)

    __CANVAS = canvas

def canvas_on_click(event):
    if state == "place_target":
        global __TARGET
        __TARGET = canvas.create_oval(event.x-10, event.y-10, event.x+10, event.y+10, fill='green', tags=("token", "reset",))
        __target_x = event.x
        __target_y = event.y
        state = None

def canvas_target_place():
    set_state("place_target")

def canvas_drag(event):
    global __CANVAS
    global __drag_item, __drag_x, __drag_y
    __CANVAS.move(__drag_item, event.x - __drag_x, event.y - __drag_y)
    __drag_x = event.x
    __drag_y = event.y

    if __drag_item == wind:
        # calculate wind and update labels
    if __drag_item == parabola:
        # put message in queue to perform further computation

def canvas_drag_start(event):
    global __CANVAS
    global __drag_item, __drag_x, __drag_y
    __drag_item = __CANVAS.find_closest(event.x, event.y)[0]
    __drag_x = event.x
    __drag_y = event.y
    print("dragging: " + __drag_item)

def canvas_drag_stop():
    global __drag_item, __drag_x, __drag_y
    __drag_item = None
    __drag_x = 0
    __drag_y = 0

def main():
    root.title("gunbound_aim")
    overlay()
    root.bind('<KeyRelease>', on_key_release)
    root.mainloop()
