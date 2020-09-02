import os
import pandas as pd
import numpy as np


_DIR = os.path.dirname(os.path.realpath(__file__))

START_DATE_FC='2020-03-05'
END_DATE_FC='2020-03-12'

START_DATE_OBS='2020-03-01'
END_DATE_OBS='2020-03-12'

SF_OFFSET = 1
SF_OFFSET_MAX = 3
SF_SCALE = 10.0 # size of bump
Q_PERC = [5, 25, 50, 75, 95]

# bump function
def f_bump(x, scale, offset):
    if x <= -1 or x >= 1:
        res = 0
    else:
        res = scale * np.exp(-1.0 / (1 - x**2))
    return res + offset

vf_bump = np.vectorize(f_bump, otypes=[np.float])

def generate_bump(dt):
    L = len(dt)
    L_BUMP = int(0.9*L) - int(0.1*L)
    mid = np.linspace(start=-0.99, stop=0.99, num=L_BUMP)

    # just has to be greater than 1
    pad_start = np.array([2] * int(0.1*L))
    pad_end = np.array([2] * (L - len(mid) - len(pad_start)))
    idx = np.concatenate([pad_start, mid, pad_end])

    scale = np.abs(np.random.normal(SF_SCALE, SF_SCALE/2))
    offset = np.random.uniform(0.1, SF_OFFSET_MAX)
    res = vf_bump(idx, scale=scale, offset=offset)
    return res


def generate_obs(dt):
    scale = np.abs(np.random.normal(SF_SCALE, SF_SCALE/2))
    offset = np.random.uniform(0.1, SF_OFFSET_MAX)

    res = generate_bump(dt)

    df = pd.DataFrame(res, columns=['obs'])
    df.index = dt
    df.index.name = 'time'
    return df


def generate_fc(dt, station=None):
    scale = np.abs(np.random.normal(SF_SCALE, SF_SCALE/2))
    offset = np.random.uniform(0.1, SF_OFFSET_MAX)
    res = generate_bump(dt)

    # perturbation (401 ensemble members)
    L = len(dt)
    N_ENS = 401
    pert = np.zeros((L, N_ENS))
    std = np.linspace(start=SF_SCALE/100, stop=SF_SCALE/10, num=L)

    pert[:, 0] = res

    for idx, x in np.ndenumerate(res):
        noise = np.random.normal(x, std[idx], size=(N_ENS-1))
        pert[idx, 1:N_ENS] = noise

    pert[pert < 0] = 0

    # percentile calculation
    res = np.percentile(pert, q=Q_PERC, axis=1)

    # construct pandas array
    df = pd.DataFrame(np.transpose(res), columns=Q_PERC)
    df.index = dt
    df.index.name = 'time'

    return df


def generate():
    # generate fc date_range
    fc_dt_rng = pd.date_range(START_DATE_FC, END_DATE_FC, freq='H')
    obs_dt_rng = pd.date_range(START_DATE_OBS, END_DATE_OBS, freq='H')

    df_fc = generate_fc(fc_dt_rng)
    df_obs = generate_obs(obs_dt_rng)

    df_fc.to_csv(os.path.join(_DIR, 'fc01.csv'))
    df_obs.to_csv(os.path.join(_DIR, 'obs01.csv'))


if __name__ == '__main__':
    generate()
