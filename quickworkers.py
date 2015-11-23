import sys
import Queue
from functools import wraps
import inspect
import traceback


class _StopWorker():
    pass


class _Processor(object):
        def __init__(self, pool=None, in_q=None, out_q=None):
            self._in_q = in_q
            self._out_q = out_q
            self._pool = pool

        def put(self, data):
            self._in_q.put(data)

        def map(self, iterable):
            for data in iterable:
                self.put(data)

        def get(self, block=True, timeout=None):
            output = self._out_q.get(block, timeout)
            self._out_q.task_done()
            if isinstance(output, Exception):
                raise output
            return output

        def join(self):
            self._in_q.join()

        def stop(self):
            for worker in self._pool:
                self.put(_StopWorker())

            for worker in self._pool:
                worker.join()

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.stop()


def _worker_main_loop(func, in_q, out_q):

    if isinstance(func, basestring):
        exec(func) in None  # Windows hack

    while True:
        try:
            data = in_q.get()

            if isinstance(data, _StopWorker):
                if hasattr(func, 'close'):
                    func.close()  # if func is a coroutine
                break

            result = func(data)
            if result:
                out_q.put(result)

        except KeyboardInterrupt:
            break
        except:
            tb = '***EXCEPTION IN WORKER***\n' + traceback.format_exc()
            out_q.put(Exception(tb))
            # raise Exception(tb) # debug
        finally:
            in_q.task_done()


def worker(func):

    if inspect.isgeneratorfunction(func):

        if sys.platform == 'win32':
            raise Exception('Only idempotent functions are supported on Windows')

        @wraps(func)
        def wrapper(*args, **kwargs):
            coro = func(*args, **kwargs)
            next(coro)
            def f(x):
                return coro.send(x)
            f.close = coro.close
            return worker(f)

        return wrapper


    def start(spawn='thread', workers=1, in_q=None, out_q=None):

        if spawn == 'thread':
            import threading
            Q = Queue.Queue
            Spawn = threading.Thread
        elif spawn == 'process':
            import multiprocessing
            Q = multiprocessing.JoinableQueue
            Spawn = multiprocessing.Process
        else:
            raise RuntimeError('Unknown worker spawning method. Choose between \
                            \'thread\' or \'process\'.')

        # hack for using multiprocessing module on Windows:
        # on Windows target function and args need to be picklable. As func is
        # not defined at module top level, it is not. Hence function source
        # code is passed as a string.
        # ONLY WORKS FOR IDEMPOTENT FUNCTIONS, NOT COROUTINE
        if spawn == 'process' and sys.platform == 'win32':
            lines = inspect.getsourcelines(func)[0][1:]
            # slice to remove @worker decorator line
            lines[0] = lines[0].replace(func.__name__, 'func')
            function = ''.join(lines)
        else:
            function = func

        in_queue = in_q or Q()
        out_queue = out_q or Q()
        pool = []
        for i in range(workers):
            p = Spawn(target=_worker_main_loop,
                        args=(function, in_queue, out_queue))
            pool.append(p)
            pool[i].start()
        processor = _Processor(pool, in_queue, out_queue)
        return processor

    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    wrapper.start = start

    return wrapper


class Pipeline(_Processor):
    def __init__(self):
        super(Pipeline, self).__init__()
        self._register = []
        self._processors = []

    def register(self, worker_function, workers=1):
        self._register.append((worker_function, workers))

    def start(self, spawn='thread'):
        in_q = None
        for worker_function, workers in self._register:
            processor = worker_function.start(spawn, workers, in_q)
            self._processors.append(processor)
            in_q = processor._out_q

        self._in_q = self._processors[0]._in_q
        self._out_q = self._processors[-1]._out_q

        return self

    # override join method of parent _Processor class
    def join(self):
        for p in self._processors:
            p.join()

    # override stop method of parent _Processor class
    def stop(self):
        for p in self._processors:
            p.stop()
