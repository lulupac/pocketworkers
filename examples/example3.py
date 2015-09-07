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
        
     
if __name__ == '__main__':
    
    pipeline = Pipeline()
    
    pipeline.register(compute)
    pipeline.register(save_results, coroutine_args='results.txt')
    
    pipeline.start()
 
    for x in range(10):
        pipeline.put(x)
    
    pipeline.join()
    
    pipeline.put('completed')  # raises an Exception written in result file
    
    pipeline.stop()