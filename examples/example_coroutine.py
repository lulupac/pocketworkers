from pocketworkers import worker


@worker
def save_results(filename):
    with open(filename, 'w') as f:
        while True:
            try:
                result = yield
                f.write(str(result)+'\n')
            except GeneratorExit:
                break


def example():
    with save_results('file.txt').start(workers=2) as pool:
        pool.map(range(10))


if __name__ == '__main__':
    example()
