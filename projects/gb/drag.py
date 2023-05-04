import functools
import math
import numpy as np
import queue
import threading
import tkinter as tk
import time

from pynput.mouse import Listener
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

__lock = threading.Lock()
__STATE = None
__CANVAS = None
__WIND_LINE = None
__var_shot_type = tk.StringVar(value="normal")
__wind_drag_oval = None
__wind_drag_x = 0
__wind_drag_y = 0
__wind_center = (GB_WIDTH/2, 160)
__wind_text = None
__wp_prev = 0
__wa_prev = 0

__mouse_drag = dict(
    x_base = 0,
    y_base = 0,
    x_delta = 0,
    y_delta = 0,
)
__mouse_prev_state = (0, 0)
__draw_queue = queue.Queue()
__aim_lines = dict(
    aim_parabola=list(),
    wind_parabola=list()
)
__var_w_f = tk.DoubleVar(value=1.185)
__var_g_f = tk.DoubleVar(value=98)
__var_w_a = tk.DoubleVar(value=0)
__var_w_p = tk.DoubleVar(value=0)
__var_x_1 = tk.DoubleVar(value=0)
__var_y_1 = tk.DoubleVar(value=0)


# - wind --> copy from other file
# - keypress to set place base 'b' => set state
# - canvas_on_click if 'b' => place target
# - keypress to set drag mode 'd' => set state dragging
# - thread loop => if state == dragging
#                  - if mouse_pos change => update parabola
#                  - draw line to base
# - main loop after => get from queue => if update parabola => redraw
# - keypress to set drag mode 'd' => exit drag mode


# --- threads ---

def task_compute_path():
    global __draw_queue, __aim_lines, __mouse_drag, __mouse_prev_state, __var_shot_type
    while(True):
        if ((__mouse_drag["x_delta"], __mouse_drag["y_delta"]) != __mouse_prev_state 
            or __wp_prev != __var_w_p.get() 
            or __wa_prev != __var_w_a.get()
        ):
            match __var_shot_type.get():
                case "normal":
                    compute_path_normal()
                    __draw_queue.put("redraw_aim_lines")
                case "boomer_s1":
                    compute_path_boomer_s1()
                    __draw_queue.put("redraw_aim_lines")
                case "boomer_s2":
                    compute_path_boomer_s2()
                    __draw_queue.put("redraw_aim_lines")
                case _:
                    pass
            __mouse_prev_state = (__mouse_drag["x_delta"], __mouse_drag["y_delta"])
        time.sleep(0.1)

def compute_path_normal():
    global __mouse_drag
    v_x = __mouse_drag["x_delta"]
    v_y = __mouse_drag["y_delta"]

    g_f = float(__var_g_f.get())
    w_f = float(__var_w_f.get())
    w_a = (float(__var_w_a.get()) / 180) * math.pi
    w_p = float(__var_w_p.get())
    x_1 = float(__var_x_1.get())
    y_1 = float(__var_y_1.get())

    # 0 wind aim guide (should match up with GB aim line - for sanity check)
    t_vec = np.linspace(0, 10, num=200, endpoint=True)
    x_aim_vec = v_x * t_vec + x_1
    y_aim_vec = v_y * t_vec + 0.5 * g_f * (t_vec ** 2) + y_1
    line_vec = np.empty((x_aim_vec.size + y_aim_vec.size,), dtype=x_aim_vec.dtype)
    line_vec[0::2] = x_aim_vec
    line_vec[1::2] = y_aim_vec

    # Actual trajectory (including wind)
    x_path_vec = v_x * t_vec + 0.5*w_f*w_p*math.cos(w_a)*(t_vec ** 2) + x_1
    y_path_vec = v_y * t_vec + 0.5*(g_f - w_f*w_p*math.sin(w_a))*(t_vec ** 2) + y_1
    line_vec_wind = np.empty((x_path_vec.size + y_path_vec.size,), dtype=x_path_vec.dtype)
    line_vec_wind[0::2] = x_path_vec
    line_vec_wind[1::2] = y_path_vec

    global __lock
    __lock.acquire()
    global __aim_lines
    __aim_lines["aim_parabola"] = line_vec
    __aim_lines["wind_parabola"] = line_vec_wind
    __lock.release()

def compute_path_boomer_s1():
    pass

def compute_path_boomer_s2():
    pass

def on_mouse_click_general(x, y, button, pressed):
    # TODO: should probably use button to test for mouse button
    global __STATE, __CANVAS
    if __STATE == "base_drag_start" and pressed:
        c_x, c_y = __CANVAS.winfo_rootx(), __CANVAS.winfo_rooty()
        draw_base(x - c_x, y - c_y)
        set_state("base_drag")
        update_mouse_drag_info(x, y, set_base=True)
        # put msg in queue to set target start
    elif __STATE == "base_drag" and not pressed:
        set_state("base_drag_stopped")

def on_mouse_move_general(x, y):
    global __STATE
    if __STATE == "base_drag":
        update_mouse_drag_info(x, y)

def update_mouse_drag_info(x, y, set_base=False):
    global __lock
    __lock.acquire()
    global __mouse_drag
    if set_base:
        __mouse_drag['x_base'] = x
        __mouse_drag['y_base'] = y
    __mouse_drag['x_delta'] = __mouse_drag['x_base'] - x
    __mouse_drag['y_delta'] = __mouse_drag['y_base'] - y
    __lock.release()

def set_state(state):
    __lock.acquire()
    global __STATE
    __STATE = state
    __lock.release()
# ---

# --- draw ---

def after_loop():
    # read from draw queue and update
    pass

def update_aim_lines(aim_parabola, wind_parabola):
    pass


def overlay():
    global __CANVAS
    content = ttk.Frame(root, borderwidth=1, relief="solid", width=GB_WIDTH, height=(GB_HEIGHT+MENU_HEIGHT))
    content.grid(column=0, row=0, padx=50, pady=20)

    # gunbound
    gunbound = ttk.Frame(content, borderwidth=1, relief="solid", width=GB_WIDTH, height=GB_HEIGHT)
    gunbound.grid(column=0, row=1, sticky="nsew")

    # canvas
    canvas = tk.Canvas(gunbound, width=GB_WIDTH, height=GB_HEIGHT, background='#60b26c', borderwidth=1, relief="solid")

    # wind guage
    canvas.create_oval(
        __wind_center[0]-40,
        __wind_center[1]-40, 
        __wind_center[0]+40,
        __wind_center[1]+40,
        outline='blue',
        width=4,
    )
    canvas.create_line(0, __wind_center[1], GB_WIDTH, __wind_center[1], fill='red')
    canvas.create_line(__wind_center[0], 0, __wind_center[0], GB_HEIGHT, fill='red')
    canvas.create_rectangle(GB_WIDTH/2-20, GB_HEIGHT/2-20, GB_WIDTH/2+20, GB_HEIGHT/2+20, fill='green')
    canvas.create_rectangle(0, 0, GB_WIDTH+100, 100, fill='lightgray')
    canvas.grid(column=0, row=0, sticky="nsew")
    canvas.bind("<Button-1>", canvas_on_click)


    # wind drag token
    global __wind_drag_oval
    __wind_drag_oval = canvas.create_oval(
        __wind_center[0]-8,
        __wind_center[1]-8, 
        __wind_center[0]+8,
        __wind_center[1]+8,
        fill='green',
        tags=("wind_token",),
        width=0
    )
    wind_drag_outline = canvas.create_oval(
        __wind_center[0]-8,
        __wind_center[1]-8, 
        __wind_center[0]+8,
        __wind_center[1]+8,
        outline='green',
        width=2,
    )

    canvas.tag_bind("wind_token", "<ButtonPress-1>", wind_drag_start)
    canvas.tag_bind("wind_token", "<B1-Motion>", wind_drag)
    canvas.tag_bind("wind_token", "<ButtonRelease-1>", wind_drag_stop)


    __CANVAS = canvas

def wind_drag_start(event):
    global __CANVAS
    global __wind_drag_x, __wind_drag_y
    __SET_STATE = "wind_drag"
    __wind_drag_x = event.x
    __wind_drag_y = event.y
    
def wind_drag_stop(event):
    global __CANVAS
    global __SET_STATE
    __wind_drag_x = 0
    __wind_drag_y = 0
    __CANVAS["background"] = "#60b26c"
    __SET_STATE = None

def calculate_wind_ang(x, y):
    global __CANVAS
    global __WIND_LINE
    global __var_w_a
    if __WIND_LINE is not None:
        __CANVAS.delete(__WIND_LINE)
    x_mid = GB_WIDTH / 2
    y_mid = __wind_center[1]

    w_a_rad = 0

    if x == x_mid:
        if y_mid > y:
            w_a_rad = math.pi / 2
        else:
            w_a_rad = 3 * math.pi / 2
    else:
        w_a_rad = math.atan(abs(y_mid - y) / abs(x - x_mid))
        if y < y_mid and x > x_mid:
            pass
        elif y < y_mid and x < x_mid:
            w_a_rad = math.pi - w_a_rad
        elif y > y_mid and x < x_mid:
            w_a_rad += math.pi
        elif y > y_mid and x > x_mid:
            w_a_rad = 2 * math.pi - w_a_rad

    __var_w_a.set(float(w_a_rad * 180 / math.pi))
    __WIND_LINE = __CANVAS.create_line(__wind_center[0], y_mid, __wind_center[0] + 40 * math.cos(w_a_rad), y_mid - 40 * math.sin(w_a_rad), fill='green', width=2)

def wind_drag(event):
    global __CANVAS
    global __wind_drag_oval
    global __wind_drag_x, __wind_drag_y, __wind_center, __wind_text
    delta_x = event.x - __wind_drag_x
    delta_y = event.y - __wind_drag_y
    __CANVAS.move(__wind_drag_oval, delta_x, delta_y)
    __CANVAS.move(__wind_text, delta_x, delta_y)
    __wind_drag_x = event.x
    __wind_drag_y = event.y

    calculate_wind_ang(event.x, event.y)

    # wind power
    w_x = event.x - __wind_center[0]
    w_y = event.y - __wind_center[1]
    power_px = math.sqrt(w_x**2 + w_y**2)
    power = 0
    if power_px > 40:
        power = min(int((power_px - 40) / 10), 12)
        __var_w_p.set(power)

    __CANVAS.itemconfig(__wind_text, text=f"{power}, {int(__var_w_a.get())}",)

def canvas_on_click(event):
    global __STATE
    match __STATE:
        case "base":
            draw_base(event.x, event.y)
            set_state(None)
        case _:
            pass

def draw_base(x, y):
    global __CANVAS, __var_x_1, __var_y_1
    __CANVAS.delete("base")
    __CANVAS.create_oval(x-8, y-8, x+8, y+8, fill='green', tags=("base",))
    __var_x_1.set(x)
    __var_y_1.set(y)
    __CANVAS["background"] = "#60b26c"

def on_key_release(event):
    global __STATE
    match event.char:
        case 'd':
            set_state("base_drag_start")
        case 'D':
            set_state("base_drag_stop")
        case 'b':
            set_state("base")
            __CANVAS["background"] = "gray25"
        case 'n':
            __var_shot_type.set("normal")
        case 'm':
            __var_shot_type.set("boomer_s1")
        case 'r':
            reset()
        case 'M':
            __var_shot_type.set("boomer_s2")
        case _:
            pass

def reset():
    global __CANVAS
    global __var_w_f
    global __var_g_f
    global __var_shot_type
    global __var_w_a
    global __var_w_p
    global __wp_prev
    global __wa_prev

    __wp_prev = 0
    __wa_prev = 0

    __var_w_f.set(1.185)
    __var_g_f.set(98)
    __var_shot_type.set("normal")
    __var_w_a.set(0)
    __var_w_p.set(value=0)
    __CANVAS.delete("aim_lines")

    global __wind_drag_oval, __wind_text

    __CANVAS.delete(__wind_drag_oval)
    __wind_drag_oval = __CANVAS.create_oval(
        __wind_center[0]-8,
        __wind_center[1]-8, 
        __wind_center[0]+8,
        __wind_center[1]+8,
        fill='green',
        tags=("wind_token",),
    )
    __CANVAS.delete(__wind_text)
    __wind_text = __CANVAS.create_text(
        __wind_center[0]+40,
        __wind_center[1],
        text="0,0",
        fill="green",
        font=(12),
    )

def poll_queue():
    # polling action
    global __lock
    __lock.acquire()
    msg = None
    global __draw_queue
    if not __draw_queue.empty():
        msg = __draw_queue.get()
    __lock.release()

    if msg == "redraw_aim_lines":
        redraw_aim_lines()

    # repeat polling
    root.after(100, poll_queue)

def redraw_aim_lines():
    global __lock
    __lock.acquire()
    global __aim_lines
    __CANVAS.delete("aim_lines")
    __CANVAS.create_line(*__aim_lines["aim_parabola"], fill="yellow", tags=("aim_lines",), width=2)
    __CANVAS.create_line(*__aim_lines["wind_parabola"], fill="green", tags=("aim_lines",), width=2)
    __lock.release()

def main():
    root.title("gunbound_aim")
    overlay()
    reset()
    root.bind('<KeyRelease>', on_key_release)
    # --- create threads here ---
    # daemon compute thread
    t_compute = threading.Thread(target=task_compute_path, daemon=True)
    t_compute.start()

    t_clicks = Listener(on_move=on_mouse_move_general, on_click=on_mouse_click_general, daemon=True)
    t_clicks.start()

    # this runs in the main thread i.e. where tkinter lives
    poll_queue()

    # --- start root ---
    root.mainloop()



if __name__ == "__main__":
    main()
