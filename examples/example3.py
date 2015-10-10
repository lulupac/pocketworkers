from quickworkers import worker, Pipeline


@worker(method='thread', qty=2)
def compute(arg):
    arg = arg + 10
    return arg


@worker(method='thread')
def save_results(filename):
    with open(filename, 'w') as f:
        while True:
            try:
                result = yield
                f.write(str(result)+'\n')
            except GeneratorExit:
                break


if __name__ == '__main__':

    io_coroutine = save_results('results.txt')

    pipeline = Pipeline()

    pipeline.register(compute)
    pipeline.register(io_coroutine)

    with pipeline.start() as p:
        p.map(range(10))
        p.put('COMPLETED')  # raises an exception which will be flowed in pipeline
