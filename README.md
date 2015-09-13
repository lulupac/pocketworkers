# quickworkers
quickworkers is a tiny lib in Python 2.7 built on top of the "Poor man task queue" code in [Bat-belt](https://github.com/sametmax/Bat-belt). It extends its functionality by providing the same easy way to launch a pool of workers (threads or processes). It adds support for coroutine as the main worker function for greater flexibility and provides a simple way to chain pools of workers together into a data pipeline. 

Examples better speaks for themselves.

## Examples

1. Say, you just need to compute some values and get the resutls. You can launch a pool of 2 workers and feed it with data like this:

```python
from quickworkers import worker

@worker(qty=2)
def compute(arg):
    arg = arg + 10
    return arg

pool = compute.start()

for x in range(10):
    pool.put(x)

for x in range(10):
    print pool.get()

pool.stop()
```

2. Now you need to offload some I\O tasks to your worker and need to pass it a file name to keep between successive calls. To do so, you can apply the `@worker` decorator to a coroutine as follows:

```python
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

thread = save_results.start('file.txt')

for x in range(10):
    thread.put(x)

thread.stop()
```

3. And if you need to chain these tasks together, you can simply use the `Pipeline` class as follows:

```python
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
pipeline.register(save_results, coroutine_args='results.txt')

pipeline.start()

for x in range(10):
    pipeline.put(x)

# wait for first set of data to be processed    
pipeline.join()

# add more data
pipeline.put(10)

pipeline.stop()
```

`Pipeline` can also be used in a context manager for a little bit less hassle:
```python
...
with Pipeline() as p:

    p.register(compute)
    p.register(save_results, coroutine_args='results.txt')

    p.start()

    for x in range(10):
        p.put(x)

    p.join()

    p.put(10)
```

Note that for the moment it is not possible to mix threads and processes in a pipeline.
