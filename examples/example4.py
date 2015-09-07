from quickworkers import worker, Pipeline

@worker(method='process', qty=2, flowException=False)
def compute(arg):
    arg = arg + 10
    return arg
  
@worker(method='process')
def save_results(filename):
    with open(filename, 'w') as f:
        while True:
            try:
                result = yield
                f.write(str(result)+'\n')
            except GeneratorExit:
                break
        
     
if __name__ == '__main__':
    
    with Pipeline() as p:
    
        p.register(compute)
        p.register(save_results, coroutine_args='results.txt')
    
        p.start()
 
        for x in range(10):
            p.put(x)
    
        p.join()
    
        p.put('completed')  # compute function will raise an Exception written in result file