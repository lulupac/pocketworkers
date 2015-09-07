from quickworkers import worker


@worker(qty=2)
def compute(arg):
    arg = arg + 10
    return arg

if __name__ == '__main__':

    pool = compute.start()

    for x in range(10):
        pool.put(x)

    for x in range(10):
        print pool.get()

    pool.stop()
