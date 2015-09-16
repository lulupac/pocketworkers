import os

from quickworkers import worker, Pipeline


@worker(method='thread', qty=2)
def compute(arg):
    arg = arg + 10
    return arg


@worker(method='thread')
def save_results(filename):
    with open(filename, 'w+t') as f:
        while True:
            try:
                result = yield
                f.write(str(result)+'\n')
            except GeneratorExit:
                break


def test():
    with Pipeline() as p:

        p.register(compute)
        p.register(save_results, coroutine_args='file.txt')

        p.start()

        for x in range(10):
            p.put(x)

        p.join()

    results = range(10, 20)
    with open('file.txt') as f:
        for line in f.readlines():

            # remove output from results list as it arrives
            results.remove(int(line.rstrip()))

    assert not results

    os.remove('file.txt')

if __name__ == '__main__':
    pass
