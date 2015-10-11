from quickworkers import worker


@worker(qty=2)
def compute(arg):
    arg = arg + 10
    return arg


with compute.start() as pool:

    pool.map(range(10))

    for _ in range(10):
        print pool.get()
