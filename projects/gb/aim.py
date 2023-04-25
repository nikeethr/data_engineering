import tkinter as tk
import functools
import math
import numpy as np
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
root.geometry("+400+300")
root.wm_attributes('-transparentcolor', '#60b26c')

MENU_HEIGHT = 100
GB_WIDTH = 1280
GB_HEIGHT = 800 #720
BOOMER_ANG_REV = 35
BOOMER_ANG_FORWARD = 47

__SET_STATE=None
__CANVAS = None
__WIND_LINE = None
__BASE_CIRCLE = None
__TARGET_CIRCLE = None
__YMAX_LINE = None
__YMAX_AIM_LINE = None
__PARABOLA_AIM = None
__PARABOLA_WIND = None
__CROSSHAIR_Y = None
__CROSSHAIR_X = None
__CROSSHAIR_CIRCLE = None

__var_w_a = tk.DoubleVar(value=0)
__var_w_p = tk.DoubleVar()
__var_x_1 = tk.DoubleVar()
__var_y_1 = tk.DoubleVar()
__var_x_2 = tk.DoubleVar()
__var_y_2 = tk.DoubleVar()
__var_y_max = tk.DoubleVar()
__var_wf = tk.DoubleVar(value=1.2)
__var_gf = tk.DoubleVar(value=98)
__var_pf = tk.DoubleVar()
__var_shot_type = tk.StringVar(value="normal")


def set_state(state):
    global __SET_STATE
    print(f"setting state to {state}")
    __SET_STATE = state
    __CANVAS["background"] = "gray25"

# TODO: boomer

def calculate_power():
    match __var_shot_type.get():
        case "normal":
            calculate_power_normal()
        case "boomer_s1":
            calculate_power_boomer(reverse=False)
        case "boomer_s2":
            calculate_power_boomer(reverse=True)
        case _:
            calculate_power_normal()


def calculate_power_boomer(reverse):
    global __CANVAS
    global __PARABOLA_AIM
    global __PARABOLA_WIND
    global __YMAX_AIM_LINE
    global __CROSSHAIR_Y
    global __CROSSHAIR_X
    global __CROSSHAIR_CIRCLE

    g_f = float(__var_gf.get())
    w_f = float(__var_wf.get())
    w_a = (float(__var_w_a.get()) / 180) * math.pi
    w_p = float(__var_w_p.get())
    x_1 = float(__var_x_1.get())
    y_1 = float(__var_y_1.get())
    x_2 = float(__var_x_2.get())
    y_2 = float(__var_y_2.get())
    y_max = float(__var_y_max.get())
    y_max += (y_max - y_1) # extra weight because boomer needs high angle

    if __PARABOLA_AIM is not None:
        __CANVAS.delete(__PARABOLA_AIM)
        __CANVAS.delete(__PARABOLA_WIND)
        __CANVAS.delete(__YMAX_AIM_LINE)
        __CANVAS.delete(__CROSSHAIR_Y)
        __CANVAS.delete(__CROSSHAIR_X)
        __CANVAS.delete(__CROSSHAIR_CIRCLE)

    print(f"gf={g_f},wf={w_f},wa={w_a},wp={w_p},x1={x_1},y1={y_1},x2={x_2},y2={y_2},ymax={y_max}")

    # line segment
    # v = sqrt(2*y_max * (g-wy))

    BOOMER_ACTION_TIME = 20


    w_y = w_f*w_p*math.sin(w_a)
    w_x = w_f*w_p*math.cos(w_a)
    v_y_l = -math.sqrt((2*(y_2 - y_max)) * (g_f - w_y))
    boom_ang = BOOMER_ANG_FORWARD + w_x + w_y
    if x_1 > x_2:
        boom_ang = BOOMER_ANG_FORWARD - w_x / w_f + w_y / w_f

    v_x_l_ref = math.tan((BOOMER_ANG_FORWARD / 180) * math.pi)  * v_y_l
    v_x_l = math.tan((boom_ang / 180) * math.pi)  * v_y_l

    if reverse:
        boom_ang = BOOMER_ANG_REV - w_x / w_f + w_y / w_f
        if x_1 > x_2:
            boom_ang = BOOMER_ANG_REV + w_x + w_y
        v_y_l = -math.sqrt((2*(y_2 - y_max)) * (g_f - w_y))
        v_x_l_ref = -math.tan((BOOMER_ANG_REV / 180) * math.pi)  * v_y_l
        v_x_l = -math.tan((boom_ang / 180) * math.pi)  * v_y_l
    if x_1 > x_2:
        v_x_l *= -1
        v_x_l_ref *= -1
        
    # y_2 = y_max + vt + 1/2wt^2
    t_max = (v_y_l + math.sqrt(v_y_l**2 + 2*(y_2 - y_max)*(g_f + w_y))) / (g_f + w_y)
    x_max = x_2 + v_x_l*t_max - 0.5*w_x*(t_max ** 2)

    # quadratic segment
    y_w = y_max - y_1
    x_w = x_max - x_1
    v_y = -math.sqrt((-2*y_w) * (g_f - w_y))
    t_w = -v_y / (g_f - w_y)
    v_x = (x_w - 0.5*w_p*w_f*math.cos(w_a) * (t_w**2)) / t_w

    t_a = -v_y / g_f

    # aim vec
    t_vec = np.linspace(0, t_a, num=100, endpoint=True)
    t_vec_max = np.linspace(0, t_max, num=100, endpoint=True)

    x_aim_vec = v_x * t_vec + x_1
    x_aim_vec_max = -v_x_l_ref * t_vec_max + x_aim_vec[-1]
    y_aim_vec = v_y * t_vec + 0.5 * g_f * (t_vec ** 2) + y_1
    y_aim_vec_max = -v_y_l * t_vec_max + 0.5 * g_f * (t_vec_max ** 2) + y_aim_vec[-1]

    line_vec = np.empty((x_aim_vec.size + y_aim_vec.size,), dtype=x_aim_vec.dtype)
    line_vec[0::2] = x_aim_vec
    line_vec[1::2] = y_aim_vec

    line_vec_max = np.empty((x_aim_vec_max.size + y_aim_vec_max.size,), dtype=x_aim_vec.dtype)
    line_vec_max[0::2] = x_aim_vec_max
    line_vec_max[1::2] = y_aim_vec_max

    __PARABOLA_AIM = __CANVAS.create_line(*line_vec, *line_vec_max, fill='green')
    __YMAX_AIM_LINE = __CANVAS.create_line(0, y_1 - 0.5 * v_y**2 / g_f, GB_WIDTH, y_1 - 0.5 * v_y**2 / g_f, fill='yellow')

    print(f"v_x_l={v_x_l},v_y_l={v_y_l},t_max={t_max},t_w={t_w},v_x={v_x},v_y={v_y},x_max={x_max},y_max={y_max}")

    # actual path
    t_vec = np.linspace(0, t_w, num=300, endpoint=True)
    t_vec_max = np.linspace(0, t_max, num=300, endpoint=True)

    x_path_vec = v_x * t_vec + 0.5*w_x*(t_vec ** 2) + x_1
    x_path_vec_max = -v_x_l * t_vec_max + 0.5*w_x*(t_vec_max ** 2) + x_max
    y_path_vec = v_y * t_vec + 0.5*(g_f - w_y)*(t_vec ** 2) + y_1
    y_path_vec_max = -v_y_l * t_vec_max + 0.5*(g_f - w_y)*(t_vec_max ** 2) + y_path_vec[-1]

    path_vec = np.empty((x_path_vec.size + y_path_vec.size,), dtype=x_path_vec.dtype)
    path_vec_max = np.empty((x_path_vec_max.size + y_path_vec_max.size,), dtype=x_path_vec_max.dtype)
    path_vec[0::2] = x_path_vec
    path_vec[1::2] = y_path_vec
    path_vec_max[0::2] = x_path_vec_max
    path_vec_max[1::2] = y_path_vec_max

    __PARABOLA_WIND = __CANVAS.create_line(*path_vec, *path_vec_max, fill='magenta')
    __CROSSHAIR_X = __CANVAS.create_line(x_aim_vec[-1] - 5, y_aim_vec[-1], x_aim_vec[-1] + 5, y_aim_vec[-1], fill='green')
    __CROSSHAIR_Y = __CANVAS.create_line(x_aim_vec[-1], y_aim_vec[-1] - 5, x_aim_vec[-1], y_aim_vec[-1] + 5, fill='green')
    __CROSSHAIR_CIRCLE = __CANVAS.create_oval(x_aim_vec[-1]-5, y_aim_vec[-1]-5, x_aim_vec[-1]+5, y_aim_vec[-1]+5, outline='green', width=2)

    __CANVAS["background"] = "#60b26c"

    # 1: vy = vx
    # 1: y2 = vy t + 1/2 (g - w) t^2

    # 1: y_max = vy t + 1/2 (g - w) t^2 => t = vy / (g - w) ---> sqrt (2 y_max * (g - wy)) = vsin(theta)
    # 2: x_max = vx t + 1/2 w t^2

    # 3: y_w = vy t + 1/2 (g - w) t^2

    # a = 0.5(g-w)
    # b = vy
    # c = -y_w
    # t = -vy +- sqrt(vy^2 + 2*y_w*(g-w)) / (g-w)

    # 4: x_w = vx t + 1/2 w t^2
    # (x_w - 1/2 w t^2) / t = vx




def calculate_power_normal():
    global __CANVAS
    global __PARABOLA_AIM
    global __PARABOLA_WIND
    global __YMAX_AIM_LINE
    global __CROSSHAIR_Y
    global __CROSSHAIR_X
    global __CROSSHAIR_CIRCLE

    g_f = float(__var_gf.get())
    w_f = float(__var_wf.get())
    w_a = (float(__var_w_a.get()) / 180) * math.pi
    w_p = float(__var_w_p.get())
    x_1 = float(__var_x_1.get())
    y_1 = float(__var_y_1.get())
    x_2 = float(__var_x_2.get())
    y_2 = float(__var_y_2.get())
    y_max = float(__var_y_max.get())

    if __PARABOLA_AIM is not None:
        __CANVAS.delete(__PARABOLA_AIM)
        __CANVAS.delete(__PARABOLA_WIND)
        __CANVAS.delete(__YMAX_AIM_LINE)
        __CANVAS.delete(__CROSSHAIR_Y)
        __CANVAS.delete(__CROSSHAIR_X)
        __CANVAS.delete(__CROSSHAIR_CIRCLE)

    print(f"gf={g_f},wf={w_f},wa={w_a},wp={w_p},x1={x_1},y1={y_1},x2={x_2},y2={y_2},ymax={y_max}")

    y_w_max = y_max - y_1
    y_w = y_2 - y_1
    x_w = x_2 - x_1

    v_y = -math.sqrt((-2*y_w_max) * (g_f - w_f*w_p*math.sin(w_a)))
    t_w = (-v_y + math.sqrt(v_y**2 + 2*y_w*(g_f - w_f*w_p*math.sin(w_a)))) / (g_f - w_f*w_p*math.sin(w_a))
    v_x = (x_w - 0.5*w_p*w_f*math.cos(w_a) * (t_w**2)) / t_w

    print(f"v_y={v_y},v_x={v_x},t_w={t_w}")

    # aim vec
    t_vec = np.linspace(0, t_w, num=100, endpoint=True)
    x_aim_vec = v_x * t_vec + x_1
    y_aim_vec = v_y * t_vec + 0.5 * g_f * (t_vec ** 2) + y_1

    print(x_aim_vec)
    print(y_aim_vec)

    line_vec = np.empty((x_aim_vec.size + y_aim_vec.size,), dtype=x_aim_vec.dtype)
    line_vec[0::2] = x_aim_vec
    line_vec[1::2] = y_aim_vec

    __PARABOLA_AIM = __CANVAS.create_line(*line_vec, fill='green')
    __YMAX_AIM_LINE = __CANVAS.create_line(0, y_1 - 0.5 * v_y**2 / g_f, GB_WIDTH, y_1 - 0.5 * v_y**2 / g_f, fill='yellow')

    # actual path
    x_path_vec = v_x * t_vec + 0.5*w_f*w_p*math.cos(w_a)*(t_vec ** 2) + x_1
    y_path_vec = v_y * t_vec + 0.5*(g_f - w_f*w_p*math.sin(w_a))*(t_vec ** 2) + y_1

    line_vec = np.empty((x_path_vec.size + y_path_vec.size,), dtype=x_path_vec.dtype)
    line_vec[0::2] = x_path_vec
    line_vec[1::2] = y_path_vec

    __PARABOLA_WIND = __CANVAS.create_line(*line_vec, fill='magenta')
    __CROSSHAIR_X = __CANVAS.create_line(x_aim_vec[-1] - 5, y_aim_vec[-1], x_aim_vec[-1] + 5, y_aim_vec[-1], fill='green')
    __CROSSHAIR_Y = __CANVAS.create_line(x_aim_vec[-1], y_aim_vec[-1] - 5, x_aim_vec[-1], y_aim_vec[-1] + 5, fill='green')
    __CROSSHAIR_CIRCLE = __CANVAS.create_oval(x_aim_vec[-1]-5, y_aim_vec[-1]-5, x_aim_vec[-1]+5, y_aim_vec[-1]+5, outline='green', width=2)

    __CANVAS["background"] = "#60b26c"
    
# 1: y_max = vy t + 1/2 (g - w) t^2 => t = vy / (g - w) ---> sqrt (2 y_max * (g - wy)) = vsin(theta)
# 2: x_max = vx t + 1/2 w t^2

# 3: y_w = vy t + 1/2 (g - w) t^2

# a = 0.5(g-w)
# b = vy
# c = -y_w
# t = -vy +- sqrt(vy^2 + 2*y_w*(g-w)) / (g-w)

# 4: x_w = vx t + 1/2 w t^2
# (x_w - 1/2 w t^2) / t = vx

def calculate_wind_ang(x, y):
    global __CANVAS
    global __WIND_LINE
    global __var_w_a
    if __WIND_LINE is not None:
        __CANVAS.delete(__WIND_LINE)
    x_mid = GB_WIDTH / 2
    y_mid = 45

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
    __WIND_LINE = __CANVAS.create_line(GB_WIDTH / 2, y_mid, GB_WIDTH/2 + 40 * math.cos(w_a_rad), y_mid - 40 * math.sin(w_a_rad), fill='green', width=2)
    __CANVAS["background"] = "#60b26c"


def draw_base(x, y):
    global __BASE_CIRCLE
    global __CANVAS
    if __BASE_CIRCLE is not None:
        __CANVAS.delete(__BASE_CIRCLE)
    __BASE_CIRCLE = __CANVAS.create_oval(x-5, y-5, x+5, y+5, outline='green', width=2)
    __CANVAS["background"] = "#60b26c"
    __var_x_1.set(x)
    __var_y_1.set(y)

def draw_target(x, y):
    global __TARGET_CIRCLE
    global __CANVAS
    if __TARGET_CIRCLE is not None:
        __CANVAS.delete(__TARGET_CIRCLE)
    __TARGET_CIRCLE = __CANVAS.create_oval(x-5, y-5, x+5, y+5, outline='red', width=2)
    __CANVAS["background"] = "#60b26c"
    __var_x_2.set(x)
    __var_y_2.set(y)

def draw_ymax(x, y):
    global __YMAX_LINE
    global __CANVAS
    if __YMAX_LINE is not None:
        __CANVAS.delete(__YMAX_LINE)
    __YMAX_LINE = __CANVAS.create_line(0, y, GB_WIDTH, y, fill='violet')
    __CANVAS["background"] = "#60b26c"
    __var_y_max.set(y)

def draw_ymax_aim():
    pass

def canvas_on_click(event):
    global __SET_STATE
    print(f"clicked {event.x}, {event.y}")
    match __SET_STATE:
        case "w_a":
            calculate_wind_ang(event.x, event.y)
        case "base":
            draw_base(event.x, event.y)
        case "target":
            draw_target(event.x, event.y)
        case "y_max":
            draw_ymax(event.x, event.y)
        case _:
            pass

def overlay():
    global __SET_STATE
    global __CANVAS

    content = ttk.Frame(root, borderwidth=1, relief="solid", width=GB_WIDTH, height=(GB_HEIGHT+MENU_HEIGHT))
    content.grid(column=0, row=0)

    # --- menu ---
    menu = ttk.Frame(content, borderwidth=1, relief="solid", width=GB_WIDTH, height=MENU_HEIGHT)
    menu.grid(column=0, row=0, padx=50, pady=20)

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
    y_max = ttk.Frame(menu, borderwidth=1, relief="solid", height=MENU_HEIGHT)
    y_max.grid(column=4, row=0, rowspan=2, sticky="nsew")
    y_max_btn = ttk.Button(y_max, text='y_max', command=functools.partial(set_state, state='y_max'))
    y_max_lab = ttk.Label(y_max, textvariable=__var_y_max, borderwidth=1, relief="solid")
    y_max_btn.grid(column=0, row=0, sticky="nsew")
    y_max_lab.grid(column=0, row=1, sticky="nsew")

    ## set wind factor
    wind_factor = ttk.Frame(menu, borderwidth=1, relief="solid", height=MENU_HEIGHT)
    wind_factor.grid(column=5, row=0, rowspan=2, sticky="nsew")
    wind_factor_entry = ttk.Entry(wind_factor, textvariable=__var_wf)
    wind_factor_entry.grid(column=0, row=1)
    wind_factor_lab = ttk.Label(wind_factor, text="wf", borderwidth=1, relief="solid")
    wind_factor_lab.grid(column=0, row=0, sticky="nsew")

    ## set gravity factor
    gravity_factor = ttk.Frame(menu, borderwidth=1, relief="solid", height=MENU_HEIGHT)
    gravity_factor.grid(column=6, row=0, rowspan=2, sticky="nsew")
    gravity_factor_entry = ttk.Entry(gravity_factor, textvariable=__var_gf)
    gravity_factor_entry.grid(column=0, row=1)
    gravity_factor_lab = ttk.Label(gravity_factor, text="gf", borderwidth=1, relief="solid")
    gravity_factor_lab.grid(column=0, row=0, sticky="nsew")

    ## set power factor
    power_factor = ttk.Frame(menu, borderwidth=1, relief="solid", height=MENU_HEIGHT)
    power_factor.grid(column=7, row=0, rowspan=2, sticky="nsew")
    power_factor_entry = ttk.Entry(power_factor, textvariable=__var_pf)
    power_factor_entry.grid(column=0, row=1)
    power_factor_lab = ttk.Label(power_factor, text="pf", borderwidth=1, relief="solid")
    power_factor_lab.grid(column=0, row=0, sticky="nsew")

    ## select shot_type
    shot_type = ttk.Frame(menu, borderwidth=1, relief="solid", height=MENU_HEIGHT)
    shot_type.grid(column=8, row=0, rowspan=2, sticky="nsew")
    shot_type_list = ttk.Combobox(shot_type, textvariable=__var_shot_type)
    shot_type_lab = ttk.Label(shot_type, text="shot_type", borderwidth=1, relief="solid")
    shot_type_list["values"] = ["normal", "boomer_s1", "boomer_s2"]
    shot_type_lab.grid(column=0, row=0, sticky="nsew")
    shot_type_list.grid(column=0, row=1, sticky="nsew")

    ## calculate
    calculate = ttk.Frame(menu, borderwidth=1, relief="solid", height=MENU_HEIGHT)
    calculate.grid(column=9, row=0, rowspan=2, sticky="nsew")
    calculate_button = ttk.Button(calculate, text='calculate', command=calculate_power)
    calculate_button.grid(column=0, row=0, sticky="nsew")

    ## ... TODO

    # --- canvas ---

    # gunbound
    gunbound = ttk.Frame(content, borderwidth=1, relief="solid", width=GB_WIDTH, height=GB_HEIGHT)
    gunbound.grid(column=0, row=1, sticky="nsew")

    ## wind circle overlay
    canvas = tk.Canvas(gunbound, width=GB_WIDTH, height=GB_HEIGHT, background='#60b26c', borderwidth=1, relief="solid")
    canvas.create_oval(GB_WIDTH/2-40, 5, GB_WIDTH/2+40, 85, outline='blue', width=4)
    canvas.create_line(0, 45, GB_WIDTH, 45, fill='red')
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
