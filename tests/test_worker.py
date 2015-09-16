from quickworkers import worker


@worker(qty=2)
def compute(arg):
    arg = arg + 10
    return arg


def test():

    pool = compute.start()

    for x in range(10):
        pool.put(x)

    results = range(10, 20)

    # remove output from results list as it arrives (not necessarily in order)
    for x in range(10):
        results.remove(pool.get())

    assert not results

    pool.stop()

if __name__ == '__main__':
    pass
