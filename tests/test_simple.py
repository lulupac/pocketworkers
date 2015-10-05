from quickworkers import worker


@worker(method='process', qty=2)
def compute(arg):
    arg = arg + 10
    return arg


def test():

    with compute.start() as pool:

        pool.map(range(10))

        results = range(10, 20)

        # remove output from results list as it arrives
        for _ in range(10):
            results.remove(pool.get())

        assert not results

if __name__ == '__main__':
    test()
