from quickworkers import worker


@worker(method='thread')
def save_results(filename):
    with open(filename, 'w') as f:
        while True:
            try:
                result = yield
                f.write(str(result)+'\n')
            except GeneratorExit:
                break


with save_results('file.txt').start(workers=2) as pool:

    pool.map(range(10))
