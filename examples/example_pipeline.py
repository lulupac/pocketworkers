from pocketworkers import worker, Pipeline


@worker
def compute(arg):
    arg = arg + 10
    return arg


@worker
def save_results(filename):
    with open(filename, 'w') as f:
        while True:
            try:
                result = yield
            except GeneratorExit:
                break
            f.write(str(result)+'\n')


def example():
    pipeline = Pipeline()

    pipeline.register(compute, workers=2)
    pipeline.register(save_results('file.txt'), workers=1)

    with pipeline.start(spawn='thread') as p:
        p.map(range(10))

        # wait for first set of data to be processed
        p.join()

        # add more data
        p.put(10)


if __name__ == '__main__':
    example()
