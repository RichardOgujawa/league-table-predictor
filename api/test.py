import json 
from time import sleep 

def hello(x = False):
    string = '{"hi": 0}'
    sleep(1)
    hello = json.loads(string)
    hello_return = json.dumps(hello)
    print(hello_return)

    if x == True:
        print('printing from test.py')
    else: 
        print('printing from main.py')
    

if __name__ == '__main__':
    # Example only to be run if we're running this as the main script
    hello(True)