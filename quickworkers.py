import Queue
from functools import wraps
import inspect
import traceback


class _StopWorker():
    pass


class _Processor(object):
        def __init__(self, in_q=None, out_q=None, pool=None, method=None):
            self._in_q = in_q
            self._out_q = out_q
            self._pool = pool
            self._method = method

        def put(self, data):
            self._in_q.put(data)

        def map(self, iterable):
            for data in iterable:
                self._in_q.put(data)

        def get(self, block=True, timeout=None):
            output = self._out_q.get(block, timeout)
            self._out_q.task_done()
            if isinstance(output, Exception):
                raise output
            return output

        def join(self):
            self._in_q.join()
            #self._out_q.join() -> not sure if good practice to join out_q

        def stop(self):
            for worker in self._pool:
                self._in_q.put(_StopWorker())
            self.join()

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.stop()


def _worker_main_loop(func, in_q, out_q):

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
            tb = '***TRACEBACK FROM WORKER***\n' + traceback.format_exc()
            out_q.put(Exception(tb))
        finally:
            in_q.task_done()


def worker(method='process', qty=1):

    def decorated(func):

        if inspect.isgeneratorfunction(func):

            @wraps(func)
            def wrapper(*args, **kwargs):
                coro = func(*args, **kwargs)
                next(coro)
                def f(x):
                    return coro.send(x)
                f.close = coro.close
                return worker(method, qty)(f)

            return wrapper

        if method == 'thread':
            import threading
            Q = Queue.Queue
            Spawn = threading.Thread
        elif method == 'process':
            import multiprocessing
            Q = multiprocessing.JoinableQueue
            Spawn = multiprocessing.Process
        else:
            raise RuntimeError('Unknown worker spawning method. Choose between \
                            \'thread\' or \'process\'.')

        def start(workers=None, in_q=None, out_q=None):
            nb_workers = workers or qty
            in_queue = in_q or Q()
            out_queue = out_q or Q()
            pool = []
            for i in range(nb_workers):
                p = Spawn(target=_worker_main_loop,
                          args=(func, in_queue, out_queue))
                pool.append(p)
                pool[i].start()
            processor = _Processor(in_queue, out_queue, pool, method)
            return processor

        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        wrapper.start = start

        return wrapper

    return decorated


class Pipeline(_Processor):
    def __init__(self):
        super(Pipeline, self).__init__()
        self._register = []
        self._processors = []

    def register(self, worker_function):
        self._register.append(worker_function)

    def start(self):
        spawn_method = set()
        in_q = None
        for worker_function in self._register:
            processor = worker_function.start(in_q=in_q)
            self._processors.append(processor)
            in_q = processor._out_q
            spawn_method.add(processor._method)

        if len(spawn_method) > 1:
            raise Exception('a Pipeline cannot mix Threads and Processes (yet)')

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
