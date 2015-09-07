import sys
import threading
import multiprocessing
import Queue
from functools import wraps
import inspect
import traceback


class _StopWorker():
    pass

    
def _worker_main_loop(function, in_queue, out_queue, coroutine_args, block, timeout, flowException):
    
    if isinstance(function, basestring):
        exec(function) in None  # Windows hack
    else:
        func = function
    
    iscoroutine = inspect.isgeneratorfunction(func)    
    if iscoroutine:
        coroutine = func(coroutine_args)
        next(coroutine)
        func = lambda x: coroutine.send(x)
        
    while True:
        try:
            data = in_queue.get(block, timeout)

            if isinstance(data, _StopWorker):
                if iscoroutine: 
                    coroutine.close()
                in_queue.task_done()
                break
            
            result = func(data)
            if result:
                out_queue.put(result)
            in_queue.task_done()

        except Queue.Empty:
            pass
        except KeyboardInterrupt:
            break
        except:
            e = Exception('***TRACEBACK FROM WORKER***\n' + traceback.format_exc())
            if flowException:
                out_queue.put(e)
                in_queue.task_done()
            else:
                raise e

            
def worker(method='process', qty=1, block=True, timeout=None, flowException=False):
    
    def decorator(func):
    
        if method == 'thread':
            Q = Queue.Queue
            Manager = threading.Thread
        else:
            Q = multiprocessing.JoinableQueue
            Manager = multiprocessing.Process
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        wrapper.method = method
        
        # hack for using multiprocessing on Windows:
        if method == 'process' and sys.platform == 'win32':
            lines = inspect.getsourcelines(func)[0][1:]  # slice to remove @worker decorator line
            lines[0] = lines[0].replace(func.__name__, 'func')
            function = ''.join(lines)
        else:
            function = func
        
        def start(coroutine_args=None, in_queue=None, out_queue=None):
            if not in_queue:
                in_queue = Q()
            if not out_queue:
                out_queue = Q()
            pool = []
            for i in range(qty):
                p = Manager(target=_worker_main_loop, args=(function, in_queue, out_queue, coroutine_args, block, timeout, flowException))
                pool.append(p)
                pool[i].start()
            wrapper.pool = pool
            wrapper.in_queue = in_queue
            wrapper.out_queue = out_queue
            return wrapper
        wrapper.start = start
        
        def get(block=block, timeout=timeout):
            res = wrapper.out_queue.get(block, timeout)
            wrapper.out_queue.task_done()
            if isinstance(res, Exception):
                raise res
            return res
        wrapper.get = get
        
        wrapper.put = lambda x: wrapper.in_queue.put(x, block, timeout)
        
        def join():
            wrapper.in_queue.join()
            wrapper.out_queue.join()
        wrapper.join = join
        
        def stop():
            for worker in wrapper.pool:
                wrapper.in_queue.put(_StopWorker(), block, timeout)
            wrapper.join()
        wrapper.stop = stop

        return wrapper

    return decorator
       

class Pipeline(object):
    def __init__(self): 
        self._processors = []
        self._first_queue = None
        self._last_queue = None
        
    def register(self, processor, coroutine_args=None):
        if self._processors and processor.method != self._processors[-1][0].method:
                raise Exception('a Pipeline cannot mix Threads and Processes (for the moment)')
        self._processors.append((processor, coroutine_args))
       
    def start(self):
        in_queue = None
        for processor, coroutine_args in self._processors:
            processor.start(coroutine_args, in_queue, None)
            in_queue = processor.out_queue
        self._first_queue = self._processors[0][0].in_queue
        self._last_queue = self._processors[-1][0].out_queue
        
    def put(self, data):
        self._first_queue.put(data)
        
    def get(self, block=True, timeout=None):
        output = self._last_queue.get(block, timeout)
        self._last_queue.task_done()
        if isinstance(output, Exception):
            raise output
        return output
    
    def join(self):
        for processor,_ in self._processors:
            processor.join()
    
    def stop(self):
        for processor,_ in self._processors:
            processor.stop()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()