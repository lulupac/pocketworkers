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

if __name__ == '__main__':

    thread = save_results.start('file.txt')

    for x in range(10):
        thread.put(x)

    thread.stop()
