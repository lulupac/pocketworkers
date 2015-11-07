from quickworkers import worker


@worker
def compute(arg):
    arg = arg + 10
    return arg


pool = compute.start(spawn='process', workers=2)

pool.map(range(10))

for _ in range(10):
    print pool.get()

pool.stop()
