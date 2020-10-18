from celery import group
from celery import chain

from example_proj.tasks import (
    x_, y_, d_, p_
)


def run_task_family():
    # x
    # execute on worker - wait for results
    r = x_.delay()
    fs = r.get()

    # group(d | p) [G]
    # run parallel group of download/process tasks
    s = group((d_.s(f) | p_.s()) for f in fs)
    r = s.delay()
    xs = r.get()

    # y
    # process results from G
    r = y_.delay(xs)
    out = r.get()

    print('result: {}'.format(out))

if __name__ == '__main__':
    run_task_family()
