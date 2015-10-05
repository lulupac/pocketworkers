from quickworkers import worker, Pipeline


@worker(method='thread', qty=2)
def compute(arg):
    arg = arg + 10
    return arg


@worker(method='thread')
def custom_compute(a):
    result = None
    while True:
        try:
            data = yield result
            result = data + a
        except GeneratorExit:
            break


def test():

    mycoroutine = custom_compute(5)

    with Pipeline() as p:

        p.register(compute)
        p.register(mycoroutine)

        p.start()

        p.map(range(10))

        results = range(15, 25)

        for _ in list(results):
            # remove output from results list as it arrives
            results.remove(p.get())

        p.join()

    assert not results

if __name__ == '__main__':
    test()
