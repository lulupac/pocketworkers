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


pipeline = Pipeline()

pipeline.register(compute)
pipeline.register(save_results('file.txt'))

with pipeline.start() as p:

    p.map(range(10))

    # wait for first set of data to be processed
    p.join()

    # add more data
    p.put(10)
