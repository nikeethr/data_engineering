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
root.overrideredirect(True)
root.lift()
root.wm_attributes("-topmost", True)
root.attributes('-alpha', 0.75)
root.geometry("+507+150")
root.wm_attributes('-transparentcolor', '#60b26c')

MENU_HEIGHT = 100
GB_WIDTH = 1440 # 1280
GB_HEIGHT = 900 #720 # 900
BOOMER_ANG_REV = 35
BOOMER_ANG_FORWARD = 45

__CANVAS = None
__SET_STATE=None
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

__PARABOLA_AIM_2 = None
__PARABOLA_WIND_2 = None
__CROSSHAIR_Y_2 = None
__CROSSHAIR_X_2 = None
__CROSSHAIR_CIRCLE_2 = None
__BASE_CIRCLE_2 = None
__TARGET_CIRCLE_2 = None

__var_w_a = tk.DoubleVar(value=0)
__var_w_p = tk.DoubleVar(value=0)
__var_x_1 = tk.DoubleVar()
__var_y_1 = tk.DoubleVar()
__var_x_2 = tk.DoubleVar()
__var_y_2 = tk.DoubleVar()

__var_x_1_2 = tk.DoubleVar()
__var_y_1_2 = tk.DoubleVar()
__var_x_2_2 = tk.DoubleVar()
__var_y_2_2 = tk.DoubleVar()

__var_y_max = tk.DoubleVar(value=150)
__var_wf = tk.DoubleVar(value=1.275)
__var_gf = tk.DoubleVar(value=98)
__var_pf = tk.DoubleVar()
__var_shot_type = tk.StringVar(value="normal")
__var_shot_type_2 = tk.StringVar(value="boomer_s2")

__cbox_shot_type = None
__cbox_shot_type_2 = None
__dummy_button = None

__var_g_blue = tk.DoubleVar(value=1)
__var_g_purple = tk.DoubleVar(value=1)
__var_t_blue = tk.DoubleVar(value=0.9) # t_blue = 0.25 # trajectory continues and then flips
__var_t_purple = tk.DoubleVar(value=3.7) # t_purple = 1 # trajectory is flipped (rather gravity is flipped (2 * g_f)
__var_v_blue = tk.DoubleVar(value=101) # t_blue = 0.25 # trajectory continues and then flips
__var_v_purple = tk.DoubleVar(value=98) # t_purple = 1 # trajectory is flipped (rather gravity is flipped (2 * g_f)
__var_v_red = tk.DoubleVar(value=24)
__var_ugwf = tk.DoubleVar(value=0) 

 
def reset():
    global __CANVAS

    global __var_w_a
    global __var_w_p
    global __var_x_1
    global __var_y_1
    global __var_x_2
    global __var_y_2
    global __var_x_1_2 
    global __var_y_1_2
    global __var_x_2_2 
    global __var_y_2_2 
    global __var_y_max
    global __var_wf
    global __var_gf
    global __var_pf
    global __var_shot_type 
    global __var_shot_type_2 
    global __SET_STATE

    global __WIND_LINE
    global __BASE_CIRCLE
    global __TARGET_CIRCLE
    global __YMAX_LINE
    global __YMAX_AIM_LINE
    global __PARABOLA_AIM
    global __PARABOLA_WIND
    global __CROSSHAIR_Y
    global __CROSSHAIR_X
    global __CROSSHAIR_CIRCLE
    global __PARABOLA_AIM_2
    global __PARABOLA_WIND_2
    global __CROSSHAIR_Y_2
    global __CROSSHAIR_X_2
    global __CROSSHAIR_CIRCLE_2
    global __BASE_CIRCLE_2
    global __TARGET_CIRCLE_2

    for i in [
        __WIND_LINE,
        __BASE_CIRCLE,
        __TARGET_CIRCLE,
        __YMAX_LINE,
        __YMAX_AIM_LINE,
        __PARABOLA_AIM,
        __PARABOLA_WIND,
        __CROSSHAIR_Y,
        __CROSSHAIR_X,
        __CROSSHAIR_CIRCLE,
        __PARABOLA_AIM_2,
        __PARABOLA_WIND_2,
        __CROSSHAIR_Y_2,
        __CROSSHAIR_X_2,
        __CROSSHAIR_CIRCLE_2,
        __BASE_CIRCLE_2,
        __TARGET_CIRCLE_2,
    ]:
        if i is not None:
            __CANVAS.delete(i)

    __var_w_a.set(0)
    __var_w_p.set(value=6)

    __var_y_max.set(150)
    __var_wf.set(1.275)
    __var_gf.set(98)
    __var_shot_type.set("normal")
    __var_shot_type_2.set("normal")

    __CANVAS.delete("aim_lines")


def set_state(state):
    global __SET_STATE
    global __CANVAS
    print(f"setting state to {state}")
    __SET_STATE = state
    __CANVAS["background"] = "gray25"

# TODO: boomer

def calculate_power(tank, show_multiple=False):
    show_multiple=True
    global __CANVAS
    __CANVAS.delete("aim_lines")
    if tank == 1:
        shot_type = __var_shot_type.get()
        y_base = __var_y_1.get()
    else: 
        shot_type = __var_shot_type_2.get()
        y_base = __var_y_2.get()
    colors = ["#223C20", "#4C8D26", "#DE60CA", "#882380", "#D5FB00"]
    if shot_type.startswith("dnak"):
        show_multiple = False
    i = 0
    if show_multiple:
        for y in np.linspace(y_base - 100, y_base - 600, num=5, endpoint=True):
            c = colors[i]
            try:
                match shot_type:
                    case "normal":
                        calculate_power_normal(tank, y, multiple=True, color=c)
                    case "boomer_s1":
                        calculate_power_boomer(reverse=False, tank=tank, y_max=y, multiple=True, color=c)
                    case "boomer_s2":
                        calculate_power_boomer(reverse=True, tank=tank, y_max=y, multiple=True, color=c)
                    case _:
                        calculate_power_normal(tank, y_max=y, multiple=True, color=c)
            except ValueError as e:
                print(e)
                continue
            i += 1
        if shot_type == "boomer_s2":
            calculate_power_boomer(reverse=True, tank=tank, y_max=y_base-800, multiple=True, color="blue")

    else:
        match shot_type:
            case "normal":
                calculate_power_normal(tank)
            case "boomer_s1":
                calculate_power_boomer(reverse=False, tank=tank)
            case "boomer_s2":
                calculate_power_boomer(reverse=True, tank=tank)
            case "dnak_s2":
                vx, vy, x, y = calculate_power_normal(tank=tank)
                calculate_dnak_trajectory(vx, vy, x, y)
            case "dnak_s2_flip":
                vx, vy, x, y = calculate_power_normal(tank=tank)
                calculate_dnak_trajectory(vx, vy, x, y, reverse=True)
            case _:
                calculate_power_normal(tank)

def calculate_dnak_trajectory(vx, vy, x, y, reverse=False):
    # ---
    # parameters to tune -- todo: add temporary inputs for these
    t_red = 5 # make this long so it shows the path
    # when trajectory is flipped backed again, v_y and v_x is always the same
    # and gravity is set back to normal
    v_x_red = -float(__var_v_red.get()) * 1
    v_y_red = -float(__var_v_red.get()) * 4.6
    # ---

    g_blue_factor = float(__var_g_blue.get())
    g_purple_factor = float(__var_g_purple.get())
    v_blue_factor = float(__var_v_blue.get())
    v_purple_factor = float(__var_v_purple.get())

    t_blue = float(__var_t_blue.get()) # t_blue = 0.25 # trajectory continues and then flips
    t_purple = float(__var_t_purple.get()) # t_purple = 1 # trajectory is flipped (rather gravity is flipped (2 * g_f)

    g_f = float(__var_gf.get())
    g_under_blue = g_blue_factor*g_f
    g_under_purple = -g_purple_factor*g_f
    w_f = float(__var_wf.get())
    w_a = (float(__var_w_a.get()) / 180) * math.pi
    w_p = float(__var_w_p.get())
    w_y = w_f*w_p*math.sin(w_a)
    w_x = w_f*w_p*math.cos(w_a)
    ugwf = float(__var_ugwf.get()) # under ground wind factor

    # reset v_y after hitting the ground
    # v_y = 400
    # proportionally adjust v_x
    # v_x = vx / vy * 400

    t_all = t_blue + t_purple + t_red
    t_vec_blue = np.linspace(0, t_blue, num=10, endpoint=True)
    t_vec_purple = np.linspace(0, t_purple, num=int((100/t_all)*t_purple), endpoint=True)
    t_vec_red = np.linspace(0, t_red, num=int((100/t_all)*t_red), endpoint=True)

    w_y = w_f*w_p*math.sin(w_a)
    w_x = w_f*w_p*math.cos(w_a)

    v_x = (vx / math.sqrt(vx**2 + vy**2)) * v_blue_factor
    v_y = (vy / math.sqrt(vx**2 + vy**2)) * v_blue_factor
    if reverse:
        # v_x is flipped
        v_x = -v_x


    # blue still affected by wind?

    x_blue = v_x*t_vec_blue + 0.5*w_x*(t_vec_blue**2) + x
    y_blue = v_y*t_vec_blue + 0.5*(g_under_blue+w_y)*(t_vec_blue**2) + y

    v_x_purple = v_x + w_x*t_vec_blue[-1]
    v_y_purple = v_y + (g_under_blue-w_y)*t_vec_blue[-1]

    mag_purple = math.sqrt(v_x_purple**2 + v_y_purple**2)
    v_x_purple = (v_x_purple / mag_purple) * v_purple_factor
    v_y_purple = (v_y_purple / mag_purple) * v_purple_factor

    # TODO add inertia on x when going under
    x_purple = v_x_purple*t_vec_purple + 0.5*w_x*0*(t_vec_purple**2) + x_blue[-1]
    y_purple = v_y_purple*t_vec_purple + 0.5*(g_under_purple-w_y*ugwf*0)*(t_vec_purple**2) + y_blue[-1]

    if reverse:
        v_x_red = -v_x_red
    x1 = __var_x_1.get() 
    x2 = __var_x_2.get() 
    if x1 > x2:
        v_x_red = -v_x_red
    RED_FUDGE = 1
    x_red = v_x_red*t_vec_red + RED_FUDGE*0.5*w_x*(t_vec_red**2) + x_purple[-1]
    y_red = v_y_red*t_vec_red + RED_FUDGE*0.5*(g_f-w_y)*(t_vec_red**2) + y_purple[-1]

    path_vec_blue = np.empty((x_blue.size + y_blue.size,), dtype=x_blue.dtype)
    path_vec_blue[0::2] = x_blue
    path_vec_blue[1::2] = y_blue

    path_vec_purple = np.empty((x_purple.size + y_purple.size,), dtype=x_purple.dtype)
    path_vec_purple[0::2] = x_purple
    path_vec_purple[1::2] = y_purple

    path_vec_red = np.empty((x_red.size + y_red.size,), dtype=x_red.dtype)
    path_vec_red[0::2] = x_red
    path_vec_red[1::2] = y_red

    __PARABOLA_WIND = __CANVAS.create_line(*path_vec_blue, fill='cyan', dash=(4,2), tags=("aim_lines"), width=2)
    __PARABOLA_WIND = __CANVAS.create_line(*path_vec_purple, fill='magenta', dash=(4,2), tags=("aim_lines"), width=2)
    __PARABOLA_WIND = __CANVAS.create_line(*path_vec_red, fill='red', dash=(4,2), tags=("aim_lines"), width=2)

    # --- rest of this part is for SS

    v_x *= 1.2
    v_y *= 1.2
    t_vec_blue_ss = t_vec_blue
    x_blue_ss = v_x*t_vec_blue_ss + 0.5*ugwf*w_x*(t_vec_blue_ss**2) + x
    y_blue_ss = v_y*t_vec_blue_ss + 0.5*(g_under_blue+w_y*ugwf)*(t_vec_blue_ss**2) + y
    path_vec_blue_ss = np.empty((x_blue_ss.size + y_blue_ss.size,), dtype=x_blue.dtype)
    path_vec_blue_ss[0::2] = x_blue_ss
    path_vec_blue_ss[1::2] = y_blue_ss

    v_x_purple_ss = v_x + w_x*ugwf*t_vec_blue_ss[-1]
    v_y_purple_ss = v_y + (g_under_blue+w_y*ugwf)*t_vec_blue_ss[-1]
    mag_purple_ss = math.sqrt(v_x_purple_ss**2 + v_y_purple_ss**2)
    v_x_purple_ss = (v_x_purple / mag_purple) * v_purple_factor
    v_y_purple_ss = (v_y_purple / mag_purple) * v_purple_factor

    t_vec_purple_ss = t_vec_purple * 1.2
    x_purple_ss = v_x_purple*t_vec_purple_ss + 0.5*w_x*ugwf*(t_vec_purple_ss**2) + x_blue_ss[-1]
    y_purple_ss = v_y_purple*t_vec_purple_ss + 0.5*(g_under_purple+w_y*ugwf)*(t_vec_purple_ss**2) + y_blue_ss[-1]
    path_vec_purple_ss = np.empty((x_purple_ss.size + y_purple_ss.size,), dtype=x_purple.dtype)
    path_vec_purple_ss[0::2] = x_purple_ss
    path_vec_purple_ss[1::2] = y_purple_ss

    parabola_ss = __CANVAS.create_line(*path_vec_blue_ss, fill='orange', dash=(4,2), tags=("aim_lines"), width=2)
    parabola_ss = __CANVAS.create_line(*path_vec_purple_ss, fill='darkorange', dash=(4,2), tags=("aim_lines"), width=2)


def calculate_power_boomer(reverse, tank=1, y_max=None, multiple=False, color="green"):
    global __CANVAS

    global __PARABOLA_AIM
    global __PARABOLA_WIND
    global __YMAX_AIM_LINE
    global __CROSSHAIR_Y
    global __CROSSHAIR_X
    global __CROSSHAIR_CIRCLE

    global __PARABOLA_AIM_2
    global __PARABOLA_WIND_2
    global __YMAX_AIM_LINE_2
    global __CROSSHAIR_Y_2
    global __CROSSHAIR_X_2
    global __CROSSHAIR_CIRCLE_2

    g_f = float(__var_gf.get())
    w_f = float(__var_wf.get())
    w_a = (float(__var_w_a.get()) / 180) * math.pi
    w_p = float(__var_w_p.get())

    if tank == 1:
        x_1 = float(__var_x_1.get())
        y_1 = float(__var_y_1.get())
        x_2 = float(__var_x_2.get())
        y_2 = float(__var_y_2.get())
    else:  # tank == 2
        x_1 = float(__var_x_1_2.get())
        y_1 = float(__var_y_1_2.get())
        x_2 = float(__var_x_2_2.get())
        y_2 = float(__var_y_2_2.get())

    if y_max is None:
        y_max = float(__var_y_max.get())

    print(f"gf={g_f},wf={w_f},wa={w_a},wp={w_p},x1={x_1},y1={y_1},x2={x_2},y2={y_2},ymax={y_max}")

    # line segment
    # v = sqrt(2*y_max * (g-wy))

    w_y = w_f*w_p*math.sin(w_a)
    w_x = w_f*w_p*math.cos(w_a)
    v_y_l = -math.sqrt((2*(y_2 - y_max)) * (g_f - w_y))
    v_y_l_ref = -math.sqrt((2*(y_2 - y_max)) * (g_f))

    SLAP_FACTOR = 2

    boom_ang_x = math.sin((BOOMER_ANG_FORWARD / 180) * math.pi)
    boom_ang_y = math.cos((BOOMER_ANG_FORWARD / 180) * math.pi)
    boom_ang_x += SLAP_FACTOR * w_x / g_f
    boom_ang_y -= SLAP_FACTOR * w_y / g_f
    boom_ang = math.atan(boom_ang_x / boom_ang_y)
    if x_1 > x_2:
        boom_ang_x = math.sin((BOOMER_ANG_FORWARD / 180) * math.pi)
        boom_ang_y = math.cos((BOOMER_ANG_FORWARD / 180) * math.pi)
        boom_ang_x -= SLAP_FACTOR * w_x / g_f
        boom_ang_y -= SLAP_FACTOR * w_y / g_f 
        boom_ang = math.atan(boom_ang_x / boom_ang_y)

    v_x_l_ref = math.tan((BOOMER_ANG_FORWARD / 180) * math.pi)  * v_y_l_ref
    v_x_l = math.tan(boom_ang)  * v_y_l

    if reverse:
        boom_ang_x = math.sin((BOOMER_ANG_REV / 180) * math.pi)
        boom_ang_y = math.cos((BOOMER_ANG_REV / 180) * math.pi)
        boom_ang_x -= SLAP_FACTOR * w_x / g_f
        boom_ang_y -= SLAP_FACTOR * w_y / g_f
        boom_ang = math.atan(boom_ang_x / boom_ang_y)
        if x_1 > x_2:
            boom_ang_x = math.sin((BOOMER_ANG_REV / 180) * math.pi)
            boom_ang_y = math.cos((BOOMER_ANG_REV / 180) * math.pi)
            boom_ang_x += SLAP_FACTOR * w_x / g_f
            boom_ang_y -= SLAP_FACTOR * w_y / g_f
            boom_ang = math.atan(boom_ang_x / boom_ang_y)
        v_y_l = -math.sqrt((2*(y_2 - y_max)) * (g_f - w_y))
        v_y_l_ref = -math.sqrt((2*(y_2 - y_max)) * (g_f))
        v_x_l_ref = -math.tan((BOOMER_ANG_REV / 180) * math.pi)  * v_y_l_ref
        v_x_l = -math.tan(boom_ang)  * v_y_l
    if x_1 > x_2:
        v_x_l *= -1
        v_x_l_ref *= -1

    print(f"boom_ang={180*boom_ang/math.pi}")
        
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
    y_aim_vec_max = -v_y_l_ref * t_vec_max + 0.5 * g_f * (t_vec_max ** 2) + y_aim_vec[-1]

    line_vec = np.empty((x_aim_vec.size + y_aim_vec.size,), dtype=x_aim_vec.dtype)
    line_vec[0::2] = x_aim_vec
    line_vec[1::2] = y_aim_vec

    line_vec_max = np.empty((x_aim_vec_max.size + y_aim_vec_max.size,), dtype=x_aim_vec.dtype)
    line_vec_max[0::2] = x_aim_vec_max
    line_vec_max[1::2] = y_aim_vec_max

    if tank == 1:
        __PARABOLA_AIM = __CANVAS.create_line(*line_vec, *line_vec_max, fill=color, tags=("aim_lines"), width=2)
    else:
        __PARABOLA_AIM_2 = __CANVAS.create_line(*line_vec, *line_vec_max, fill='blue', tags=("aim_lines"), width=2)

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

    if tank == 1:
        __PARABOLA_WIND = __CANVAS.create_line(*path_vec, *path_vec_max, fill='yellow', dash=(4,2), tags=("aim_lines"))
        __CROSSHAIR_X = __CANVAS.create_line(x_aim_vec_max[-1] - 5, y_aim_vec_max[-1], x_aim_vec_max[-1] + 5, y_aim_vec_max[-1], fill=color, tags=("aim_lines"))
        __CROSSHAIR_Y = __CANVAS.create_line(x_aim_vec_max[-1], y_aim_vec_max[-1] - 5, x_aim_vec_max[-1], y_aim_vec_max[-1] + 5, fill=color, tags=("aim_lines"))
        __CROSSHAIR_CIRCLE = __CANVAS.create_oval(x_aim_vec_max[-1]-5, y_aim_vec_max[-1]-5, x_aim_vec_max[-1]+5, y_aim_vec_max[-1]+5, outline=color, width=2, tags=("aim_lines"))
    else:
        __PARABOLA_WIND_2 = __CANVAS.create_line(*path_vec, *path_vec_max, fill='magenta', dash=(4,2), tags=("aim_lines"))
        __CROSSHAIR_X_2 = __CANVAS.create_line(x_aim_vec_max[-1] - 5, y_aim_vec_max[-1], x_aim_vec_max[-1] + 5, y_aim_vec_max[-1], fill='blue', tags=("aim_lines"))
        __CROSSHAIR_Y_2 = __CANVAS.create_line(x_aim_vec_max[-1], y_aim_vec_max[-1] - 5, x_aim_vec_max[-1], y_aim_vec_max[-1] + 5, fill='blue', tags=("aim_lines"))
        __CROSSHAIR_CIRCLE_2 = __CANVAS.create_oval(x_aim_vec_max[-1]-5, y_aim_vec_max[-1]-5, x_aim_vec_max[-1]+5, y_aim_vec_max[-1]+5, outline='blue', width=2, tags=("aim_lines"))

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


def calculate_power_normal(tank, y_max=None, multiple=False, color="green"):
    global __CANVAS
    global __PARABOLA_AIM
    global __PARABOLA_WIND
    global __YMAX_AIM_LINE
    global __CROSSHAIR_Y
    global __CROSSHAIR_X
    global __CROSSHAIR_CIRCLE

    global __PARABOLA_AIM_2
    global __PARABOLA_WIND_2
    global __YMAX_AIM_LINE_2
    global __CROSSHAIR_Y_2
    global __CROSSHAIR_X_2
    global __CROSSHAIR_CIRCLE_2


    g_f = float(__var_gf.get())
    w_f = float(__var_wf.get())
    w_a = (float(__var_w_a.get()) / 180) * math.pi
    w_p = float(__var_w_p.get())

    if y_max is None:
        y_max = float(__var_y_max.get())

    if tank == 1:
        x_1 = float(__var_x_1.get())
        y_1 = float(__var_y_1.get())
        x_2 = float(__var_x_2.get())
        y_2 = float(__var_y_2.get())
    else:  # tank == 2
        x_1 = float(__var_x_1_2.get())
        y_1 = float(__var_y_1_2.get())
        x_2 = float(__var_x_2_2.get())
        y_2 = float(__var_y_2_2.get())


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


    line_vec = np.empty((x_aim_vec.size + y_aim_vec.size,), dtype=x_aim_vec.dtype)
    line_vec[0::2] = x_aim_vec
    line_vec[1::2] = y_aim_vec

    if tank == 1:
        __PARABOLA_AIM = __CANVAS.create_line(*line_vec, fill=color, tags=("aim_lines"), width=2)
    else: # tank = 2
        __PARABOLA_AIM_2 = __CANVAS.create_line(*line_vec, fill='blue', width=2)

    # actual path
    x_path_vec = v_x * t_vec + 0.5*w_f*w_p*math.cos(w_a)*(t_vec ** 2) + x_1
    y_path_vec = v_y * t_vec + 0.5*(g_f - w_f*w_p*math.sin(w_a))*(t_vec ** 2) + y_1

    line_vec = np.empty((x_path_vec.size + y_path_vec.size,), dtype=x_path_vec.dtype)
    line_vec[0::2] = x_path_vec
    line_vec[1::2] = y_path_vec

    if tank == 1:
        __PARABOLA_WIND = __CANVAS.create_line(*line_vec, fill='yellow', dash=(4,2), tags=("aim_lines"))
        __CROSSHAIR_X = __CANVAS.create_line(x_aim_vec[-1] - 5, y_aim_vec[-1], x_aim_vec[-1] + 5, y_aim_vec[-1], fill=color, tags=("aim_lines"))
        __CROSSHAIR_Y = __CANVAS.create_line(x_aim_vec[-1], y_aim_vec[-1] - 5, x_aim_vec[-1], y_aim_vec[-1] + 5, fill=color, tags=("aim_lines"))
        __CROSSHAIR_CIRCLE = __CANVAS.create_oval(x_aim_vec[-1]-5, y_aim_vec[-1]-5, x_aim_vec[-1]+5, y_aim_vec[-1]+5, outline=color, width=2, tags=("aim_lines"))
    else:
        __PARABOLA_WIND_2 = __CANVAS.create_line(*line_vec, fill='magenta', dash=(4,2), tags=("aim_lines"))
        __CROSSHAIR_X_2 = __CANVAS.create_line(x_aim_vec[-1] - 5, y_aim_vec[-1], x_aim_vec[-1] + 5, y_aim_vec[-1], fill='blue', tags=("aim_lines"))
        __CROSSHAIR_Y_2 = __CANVAS.create_line(x_aim_vec[-1], y_aim_vec[-1] - 5, x_aim_vec[-1], y_aim_vec[-1] + 5, fill='blue', tags=("aim_lines"))
        __CROSSHAIR_CIRCLE_2 = __CANVAS.create_oval(x_aim_vec[-1]-5, y_aim_vec[-1]-5, x_aim_vec[-1]+5, y_aim_vec[-1]+5, outline='blue', width=2, tags=("aim_lines"))

    __CANVAS["background"] = "#60b26c"

    # return for dnak
    vx_end = v_x + w_f*w_p*math.cos(w_a)*t_w
    vy_end = v_y + (g_f - w_f*w_p*math.cos(w_a))*t_w

    return vx_end, vy_end, x_path_vec[-1], y_path_vec[-1]
    
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


def draw_base(x, y, tank):
    global __BASE_CIRCLE
    global __BASE_CIRCLE_2
    global __CANVAS
    if tank == 1:
        if __BASE_CIRCLE is not None:
            __CANVAS.delete(__BASE_CIRCLE)

        __BASE_CIRCLE = __CANVAS.create_oval(x-5, y-5, x+5, y+5, outline='yellow', width=2)
        __var_x_1.set(x)
        __var_y_1.set(y)
    else:
        if __BASE_CIRCLE_2 is not None:
            __CANVAS.delete(__BASE_CIRCLE_2)

        __BASE_CIRCLE_2 = __CANVAS.create_oval(x-5, y-5, x+5, y+5, outline='magenta', width=2)
        __var_x_1_2.set(x)
        __var_y_1_2.set(y)
    __CANVAS["background"] = "#60b26c"

def draw_target(x, y, tank):
    global __TARGET_CIRCLE
    global __TARGET_CIRCLE_2
    global __CANVAS
    if tank == 1:
        if __TARGET_CIRCLE is not None:
            __CANVAS.delete(__TARGET_CIRCLE)

        __TARGET_CIRCLE = __CANVAS.create_oval(x-5, y-5, x+5, y+5, outline='green', width=2)
        __var_x_2.set(x)
        __var_y_2.set(y)
    else:
        if __TARGET_CIRCLE_2 is not None:
            __CANVAS.delete(__TARGET_CIRCLE_2)

        __TARGET_CIRCLE_2 = __CANVAS.create_oval(x-5, y-5, x+5, y+5, outline='blue', width=2)
        __var_x_2_2.set(x)
        __var_y_2_2.set(y)
    __CANVAS["background"] = "#60b26c"

def draw_ymax(x, y):
    global __YMAX_LINE
    global __CANVAS
    if __YMAX_LINE is not None:
        __CANVAS.delete(__YMAX_LINE)
    __YMAX_LINE = __CANVAS.create_line(0, y, GB_WIDTH, y, fill='violet')
    __CANVAS["background"] = "#60b26c"
    __var_y_max.set(y)


def canvas_on_click(event):
    global __SET_STATE
    print(f"clicked {event.x}, {event.y}")
    match __SET_STATE:
        case "w_a":
            calculate_wind_ang(event.x, event.y)
            calculate_power(tank=1)
        case "base_1":
            draw_base(event.x, event.y, tank=1)
            calculate_power(tank=1)
        case "target_1":
            draw_target(event.x, event.y, tank=1)
            calculate_power(tank=1)
        case "base_2":
            draw_base(event.x, event.y, tank=2)
            calculate_power(tank=1)
        case "target_2":
            draw_target(event.x, event.y, tank=2)
            calculate_power(tank=1)
        case "y_max":
            draw_ymax(event.x, event.y)
            calculate_power(tank=1)
        case _:
            __CANVAS["background"] = "#60b26c"
    __SET_STATE = None
    __dummy_button.focus()

def overlay():
    global __SET_STATE
    global __CANVAS

    content = ttk.Frame(root, borderwidth=1, relief="solid", width=GB_WIDTH, height=(GB_HEIGHT+MENU_HEIGHT))
    content.grid(column=0, row=0, padx=50, pady=20)

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
    base_btn = ttk.Button(base, text='base_1', command=functools.partial(set_state, state='base_1'))
    base_btn_2 = ttk.Button(base, text='base_2', command=functools.partial(set_state, state='base_2'))
    base_btn.grid(column=0, row=0, sticky="nsew")
    base_btn_2.grid(column=0, row=1, sticky="nsew")

    ## set target location
    target = ttk.Frame(menu, borderwidth=1, relief="solid", height=MENU_HEIGHT)
    target.grid(column=3, row=0, rowspan=2, sticky="nsew")
    target_btn = ttk.Button(target, text='target_1', command=functools.partial(set_state, state='target_1'))
    target_btn_2 = ttk.Button(target, text='target_2', command=functools.partial(set_state, state='target_2'))
    target_btn.grid(column=0, row=0, sticky="nsew")
    target_btn_2.grid(column=0, row=1, sticky="nsew")

    ## set ymax
    y_max = ttk.Frame(menu, borderwidth=1, relief="solid", height=MENU_HEIGHT)
    y_max.grid(column=4, row=0, rowspan=2, sticky="nsew")
    y_max_btn = ttk.Button(y_max, text='y_max', command=functools.partial(set_state, state='y_max'))
    y_max_lab = ttk.Label(y_max, textvariable=__var_y_max, borderwidth=1, relief="solid")
    y_max_btn.grid(column=0, row=0, sticky="nsew")
    y_max_lab.grid(column=0, row=1, sticky="nsew")

    ## select shot_type
    shot_type = ttk.Frame(menu, borderwidth=1, relief="solid", height=MENU_HEIGHT)
    shot_type.grid(column=5, row=0, rowspan=2, sticky="nsew")
    global __cbox_shot_type
    __cbox_shot_type = ttk.Combobox(shot_type, textvariable=__var_shot_type)
    global __cbox_shot_type_2
    __cbox_shot_type_2 = ttk.Combobox(shot_type, textvariable=__var_shot_type_2)
    __cbox_shot_type["values"] = ["normal", "boomer_s1", "boomer_s2", "dnak_s2", "dnak_s2_flip"]
    __cbox_shot_type_2["values"] = ["normal", "boomer_s1", "boomer_s2", "dnak_s2", "dnak_s2_flip"]
    __cbox_shot_type.grid(column=0, row=0, sticky="nsew")
    __cbox_shot_type_2.grid(column=0, row=1, sticky="nsew")

    ## calculate
    calculate = ttk.Frame(menu, borderwidth=1, relief="solid", height=MENU_HEIGHT)
    calculate.grid(column=6, row=0, rowspan=2, sticky="nsew")
    calculate_button = ttk.Button(calculate, text='calculate_1', command=functools.partial(calculate_power, 1))
    calculate_button.grid(column=0, row=0, sticky="nsew")
    calculate_button = ttk.Button(calculate, text='calculate_2', command=functools.partial(calculate_power, 2))
    calculate_button.grid(column=0, row=1, sticky="nsew")

    ## reset
    reset_frame = ttk.Frame(menu, borderwidth=1, relief="solid", height=MENU_HEIGHT)
    reset_frame.grid(column=7, row=0, rowspan=1, sticky="nsew")
    reset_button = ttk.Button(reset_frame, text='reset', command=reset)
    reset_button.grid(column=0, row=1, sticky="nsew")

    ## set wind factor
    wind_factor = ttk.Frame(menu, borderwidth=1, relief="solid", height=MENU_HEIGHT)
    wind_factor.grid(column=8, row=0, rowspan=2, sticky="nsew")
    wind_factor_entry = ttk.Entry(wind_factor, textvariable=__var_wf)
    wind_factor_entry.grid(column=0, row=1)
    wind_factor_lab = ttk.Label(wind_factor, text="wf", borderwidth=1, relief="solid")
    wind_factor_lab.grid(column=0, row=0, sticky="nsew")

    ## set gravity factor
    gravity_factor = ttk.Frame(menu, borderwidth=1, relief="solid", height=MENU_HEIGHT)
    gravity_factor.grid(column=9, row=0, rowspan=2, sticky="nsew")
    gravity_factor_entry = ttk.Entry(gravity_factor, textvariable=__var_gf)
    gravity_factor_entry.grid(column=0, row=1)
    gravity_factor_lab = ttk.Label(gravity_factor, text="gf", borderwidth=1, relief="solid")
    gravity_factor_lab.grid(column=0, row=0, sticky="nsew")

    ## set dnak factors
    dnak_factor = ttk.Frame(menu, borderwidth=1, relief="solid", height=MENU_HEIGHT)
    dnak_factor.grid(column=10, row=0, columnspan=1, sticky="nsew")
    dnak_t_blue = ttk.Entry(dnak_factor, textvariable=__var_t_blue)
    dnak_t_purple = ttk.Entry(dnak_factor, textvariable=__var_t_purple)
    dnak_v_blue = ttk.Entry(dnak_factor, textvariable=__var_v_blue)
    dnak_v_purple = ttk.Entry(dnak_factor, textvariable=__var_v_purple)
    dnak_v_red = ttk.Entry(dnak_factor, textvariable=__var_v_red)
    dnak_ugwf = ttk.Entry(dnak_factor, textvariable=__var_ugwf)

    dnak_t_blue.grid(column=1, row=0)
    dnak_t_purple.grid(column=1, row=1)
    dnak_v_blue.grid(column=2, row=0)
    dnak_v_purple.grid(column=2, row=1)
    dnak_v_red.grid(column=3, row=1)
    dnak_ugwf.grid(column=3, row=0)


    ## dummy button to take off focus
    dummy = ttk.Frame(menu, borderwidth=1, relief="solid", height=MENU_HEIGHT)
    dummy.grid(column=11, row=0, rowspan=2, sticky="nsew")
    global __dummy_button
    __dummy_button = ttk.Button(dummy, text='dummy')
    __dummy_button.grid(sticky="nsew")

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
    canvas.create_rectangle(GB_WIDTH/2-20, GB_HEIGHT/2-20, GB_WIDTH/2+20, GB_HEIGHT/2+20, fill='green')
    canvas.grid(column=0, row=0, sticky="nsew")
    canvas.bind("<Button-1>", canvas_on_click)

    __CANVAS = canvas

def on_key_release(event):
    if event.char == 'r':
        reset()
    if event.char == 'b':
        set_state('base_1')
    if event.char == 't':
        set_state('target_1')
    if event.char == 'B':
        set_state('base_2')
    if event.char == 'T':
        set_state('target_2')
    if event.char == 'a':
        set_state('w_a')
    if event.char == 's':
        set_state('w_p')
    if event.char == 'y':
        set_state('y_max')
    if event.char == 'c':
        calculate_power(1)
    if event.char == 'C':
        calculate_power(2)
    if event.char == 'n':
        __var_shot_type.set("normal")
        calculate_power(1)
    if event.char == 'm':
        __var_shot_type.set("boomer_s1")
        calculate_power(1)
    if event.char == 'M':
        __var_shot_type.set("boomer_s2")
        calculate_power(1)
    if event.char == 'd':
        __var_shot_type.set("dnak_s2")
        calculate_power(1)
    if event.char == 'D':
        __var_shot_type.set("dnak_s2_flip")
        calculate_power(1)


    global __SET_STATE
    global __var_w_p
    if __SET_STATE == 'w_p' and event.char != 's':
        if event.char == "!":
            __var_w_p.set(10.0)
            calculate_power(1)
        elif event.char == "@":
            __var_w_p.set(11.0)
            calculate_power(1)
        elif event.char == "#":
            __var_w_p.set(12.0)
            calculate_power(1)
        elif int(event.char) >= 0 and int(event.char) <=9:
            __var_w_p.set(event.char)
            calculate_power(1)

        __CANVAS["background"] = "#60b26c"
        __SET_STATE = None

    __dummy_button.focus()

def main():
    root.title("gunbound_aim")
    overlay()
    reset()
    root.bind('<KeyRelease>', on_key_release)
    root.mainloop()

if __name__ == "__main__":
    main()
