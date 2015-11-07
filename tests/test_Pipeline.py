from quickworkers import worker, Pipeline


@worker
def compute(arg):
    arg = arg + 10
    return arg


@worker
def custom_compute(a):
    result = None
    while True:
        try:
            data = yield result
            result = data + a
        except GeneratorExit:
            break


def test():

    with Pipeline() as p:

        p.register(compute)
        p.register(custom_compute(5), workers=2)

        p.start(spawn='thread')

        p.map(range(10))

        results = range(15, 25)

        for _ in list(results):
            # remove output from results list as it arrives
            results.remove(p.get())

        p.join()

    assert not results

if __name__ == '__main__':
    test()
