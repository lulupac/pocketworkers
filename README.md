# quickworkers
quickworkers is a tiny lib in Python 2.x largely inspired by the "Poor man task queue" code in [Bat-belt](https://github.com/sametmax/Bat-belt). While keeping its simplicity of use, it adds a few extra  functionalities such as the ability to launch a pool of workers and support for coroutine as the worker function. It also provides a simple way to chain pools of workers together into a data pipeline. 

Examples better speaks for themselves.

## Examples

Taking the example from [Bat-belt](https://github.com/sametmax/Bat-belt), if you need to compute some values and get the results, you can launch a pool of 2 workers and feed it with data like this:

```python
from quickworkers import worker

@worker
def compute(arg):
    arg = arg + 10
    return arg

pool = compute.start(spawn='process', workers=2)

for data in range(10):
    pool.put(data)

for _ in range(10):
    print pool.get()

pool.stop()
```
By default, it uses the `threading` module to spawn workers.

You can also use a context manager and `map` method for a little bit less hassle:

```python
...
with compute.start(spawn='process', workers=2) as p:

    p.map(range(10))

    for _ in range(10):
        print p.get()
```

Now if you need to offload some I\O tasks to a worker and need to pass it a file name at execution time to keep between successive calls, you can apply the `@worker` decorator to a coroutine:

```python
from quickworkers import worker

@worker
def save_results(filename):
    with open(filename, 'w') as f:
        while True:
            try:
                result = yield
            except GeneratorExit:
                break
            f.write(str(result)+'\n')


with save_results('file.txt').start() as p:

    p.map(range(10))
```

By defaults, it starts one worker.

Finally, if you need to chain these tasks together, you can use the `Pipeline` class:

```python
from quickworkers import worker, Pipeline

@worker
def compute(arg):
    # same function as in example 1

@worker
def save_results(filename):
    # same coroutine as in example 2

    
pipeline = Pipeline()

pipeline.register(compute, workers=2)
pipeline.register(save_results('file.txt'))

with pipeline.start() as p:

    p.map(range(10))

    # wait for first set of data to be processed    
    p.join()

    # add more data
    p.put(10)
```

## Note
Comments, critics, issues, fixes are welcome as long as it aims at keeping this lib tiny, stupid and simple :-)
