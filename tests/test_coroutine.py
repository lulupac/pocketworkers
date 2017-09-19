from pocketworkers import worker


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

    mycoroutine = custom_compute(5)

    with mycoroutine.start(spawn='thread', workers=3) as pool:

        pool.map(range(10))

        results = list(range(5, 15))

        for _ in list(results):
            # remove output from results list as it arrives
            results.remove(pool.get())

    assert not results

if __name__ == '__main__':
    test()
