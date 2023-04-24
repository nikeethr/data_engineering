import tkinter as tk
import functools
import math
from tkinter import ttk

# TODO:
# [ ] menu -> | set wind angle | set wind power | set base | set target | set ymax | calculate
# [ ] wind circle
# [ ] click points


# | [w_a] [60] | [w_p] [dropdown] | [xy_0] [x] [y] | [xy_t] [x] [y] | [ymax] [1000] | calculate

root = tk.Tk()
root.resizable(False,False)
# root.overrideredirect(True)
root.lift()
root.wm_attributes("-topmost", True)
root.attributes('-alpha', 0.75)
root.geometry("+400+400")
root.wm_attributes('-transparentcolor', '#60b26c')
MENU_HEIGHT = 100
GB_WIDTH = 1280
GB_HEIGHT = 800 #720
__SET_STATE=None
__CANVAS = None
__WIND_LINE = None
__var_w_a = tk.DoubleVar()
__var_w_p = tk.DoubleVar()
__var_x_1 = tk.DoubleVar()
__var_y_1 = tk.DoubleVar()
__var_x_2 = tk.DoubleVar()
__var_y_2 = tk.DoubleVar()


def calculate():
    pass

def reset():
    pass

def set_state(state):
    global __SET_STATE
    print(f"setting state to {state}")
    __SET_STATE = state
    __CANVAS["background"] = "gray25"

def calculate_wind_ang(x, y):
    global __CANVAS
    global __WIND_LINE
    global __var_w_a
    if __WIND_LINE is not None:
        __CANVAS.delete(__WIND_LINE)
    x_mid = GB_WIDTH / 2
    y_mid = 50

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

    print(f"setting w_a to {w_a_rad * 180 / math.pi}")
    __var_w_a.set(float(w_a_rad * 180 / math.pi))
    __WIND_LINE = __CANVAS.create_line(GB_WIDTH / 2, 50, GB_WIDTH/2 + 40 * math.cos(w_a_rad), 50 - 40 * math.sin(w_a_rad), fill='green', width=2)
    __CANVAS["background"] = "#60b26c"

def canvas_on_click(event):
    global __SET_STATE
    print(f"clicked {event.x}, {event.y}")
    match __SET_STATE:
        case "w_a":
            res = calculate_wind_ang(event.x, event.y)
        case _:
            pass

def overlay():
    global __SET_STATE
    global __CANVAS

    content = ttk.Frame(root, borderwidth=1, relief="solid", width=GB_WIDTH, height=(GB_HEIGHT+MENU_HEIGHT))
    content.grid(column=0, row=0)

    # --- menu ---
    menu = ttk.Frame(content, borderwidth=1, relief="solid", width=GB_WIDTH, height=MENU_HEIGHT)
    menu.grid(column=0, row=0, sticky="nsew")

    ## set wind angle
    w_a = ttk.Frame(menu, borderwidth=1, relief="solid", height=MENU_HEIGHT)
    w_a.grid(column=0, row=0, rowspan=2, sticky="nsew")
    w_a_btn = ttk.Button(w_a, text='w_a', command=functools.partial(set_state, state='w_a'))
    w_a_lab = ttk.Label(w_a, textvariable=__var_w_a, borderwidth=1, relief="solid")
    w_a_btn.grid(column=0, row=0, sticky="nsew")
    w_a_lab.grid(column=0, row=1, sticky="nsew")
 
    ## set wind power
    w_p = ttk.Frame(menu, borderwidth=1, relief="solid", height=MENU_HEIGHT)
    w_p.grid(column=1, row=0, rowspan=2, sticky="nsew")
    w_p_list = ttk.Combobox(w_p, textvariable=__var_w_p)
    w_p_lab = ttk.Label(w_p, text="w_p", borderwidth=1, relief="solid")
    w_p_list["values"] = list(range(0, 12+1))
    w_p_lab.grid(column=0, row=0, sticky="nsew")
    w_p_list.grid(column=0, row=1, sticky="nsew")

    ## set base location
    base = ttk.Frame(menu, borderwidth=1, relief="solid", height=MENU_HEIGHT)
    base.grid(column=2, row=0, rowspan=2, sticky="nsew")
    base_btn = ttk.Button(base, text='base', command=functools.partial(set_state, state='base'))
    base_lab_x = ttk.Label(base, textvariable=__var_x_1, borderwidth=1, relief="solid")
    base_lab_y = ttk.Label(base, textvariable=__var_y_1, borderwidth=1, relief="solid")
    base_btn.grid(column=0, row=0, sticky="nsew", columnspan=2)
    base_lab_x.grid(column=0, row=1, sticky="nsew")
    base_lab_y.grid(column=1, row=1, sticky="nsew")

    ## set target location
    target = ttk.Frame(menu, borderwidth=1, relief="solid", height=MENU_HEIGHT)
    target.grid(column=3, row=0, rowspan=2, sticky="nsew")
    target_btn = ttk.Button(target, text='target', command=functools.partial(set_state, state='target'))
    target_lab_x = ttk.Label(target, textvariable=__var_x_2, borderwidth=1, relief="solid")
    target_lab_y = ttk.Label(target, textvariable=__var_y_2, borderwidth=1, relief="solid")
    target_btn.grid(column=0, row=0, sticky="nsew", columnspan=2)
    target_lab_x.grid(column=0, row=1, sticky="nsew")
    target_lab_y.grid(column=1, row=1, sticky="nsew")

    ## set ymax

    ## set wind factor

    ## set gravity factor

    ## set power factor

    ## calculate

    ## ... TODO

    # --- canvas ---

    # gunbound
    gunbound = ttk.Frame(content, borderwidth=1, relief="solid", width=GB_WIDTH, height=GB_HEIGHT)
    gunbound.grid(column=0, row=1, sticky="nsew")

    ## wind circle overlay
    canvas = tk.Canvas(gunbound, width=GB_WIDTH, height=GB_HEIGHT, background='#60b26c', borderwidth=1, relief="solid")
    canvas.create_oval(GB_WIDTH/2-40, 10, GB_WIDTH/2+40, 90, outline='blue', width=4)
    canvas.create_line(0, 50, GB_WIDTH, 50, fill='red')
    canvas.create_line(GB_WIDTH / 2, 0, GB_WIDTH/2, GB_HEIGHT, fill='red')
    canvas.grid(column=0, row=0, sticky="nsew")
    canvas.bind("<Button-1>", canvas_on_click)

    __CANVAS = canvas

def main():
    root.title("gunbound_aim")
    overlay()
    root.mainloop()

if __name__ == "__main__":
    main()
