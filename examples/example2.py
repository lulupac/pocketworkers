from quickworkers import worker


@worker()
def compute(a):
    result = None
    while True:
        try:
            data = yield result
            result = data + a
        except GeneratorExit:
            break

if __name__ == '__main__':

    data = range(10)

    mycoroutine = compute(5)

    with mycoroutine.start(workers=2) as pool:

        pool.map(data)

        pool.join()

        for _ in data:
            print pool.get()
