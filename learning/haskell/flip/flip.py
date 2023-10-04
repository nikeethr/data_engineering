def flip_sign(xs):
    for x in xs:
        if isinstance(x, list):
            yield flip_sign(x)
        elif isinstance(x, float):
            yield -x
