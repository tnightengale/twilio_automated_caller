# run a thread
    # thread checks for input
    # if input:
        #triggered

# run a while loop
    # if triggered:
        # input('pause')
        # break
    # do stuff

import time
import sys
import os

'''
def detect(q):
    while True:
        a = sys.stdin.readline()
        if a == '   \n':
            # 
            print('input was special key: '.format(a))
    
    while True:
        print('monitoring for pause')
        if sys.stdin.readline():
            print('input detected: '.format')
            break
    print('exited loop')
    
'''

from pynput import keyboard

def on_press(key):
    global dialing
    try:
        print('key: {0}'.format(
            key))
        if str(key) == 'Key.ctrl':
            print('if triggered. Assigning false to dialing.')
            dialing = False
            print('dialing is {}'.format(dialing))
    except AttributeError:
        print('special key {0} pressed'.format(
            key))

def main():
    global dialing
    dialing = True
    with keyboard.Listener(on_press=on_press) as listener:
        end = time.time() + 20
        while time.time() < end:
            print('Dialing is: {}'.format(dialing))
            if dialing == False:
                print('dialing = false. Breaking loop.')
                break
            print('working')
            time.sleep(2)
        if dialing == False:
            print('Out of loop. Dialing == False.')
            input('Awaiting input: ')
        print('Reached end of progream')
        
        
if __name__ == '__main__':
    main()