#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Oct 14 12:18:46 2018

@author: tnightengale
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
from pynput import keyboard
import os
from termcolor import colored
import sys

# workflow
def main(call_count = 0):
    # -----------
    # Set Globals
    # -----------
    
    global talking
    talking = False
    
    #-------------
    # Driver Setup
    # ------------
    
    headless = Options()
    headless.add_argument("--headless")
    headless.add_argument("---info-bars")
    headless.add_argument("--use-fake-ui-for-media-stream")
    #chrome_exe_path = os.path.abspath('chromedriver')
    chrome_exe_path = os.path.join(sys._MEIPASS, "chromedriver")
    
    # -- SIMON driver -- #
    driver = webdriver.Chrome(chrome_exe_path, options = headless)
    
    # -- Twilio webapp driver -- #
    app = webdriver.Chrome(chrome_exe_path, options = headless)
    
    # instructions
    
    call_length = instructions()
    
    # ----------
    # Logging in
    # ----------
    
    auth = simon_login(driver)   
    
    # -------------------
    # Go to phone numbers
    # -------------------
    
    go_to_unreachables(driver)
    
    # ----------------
    # load webdial app
    # ----------------
    
    #next_url(app,'https://14de8b3c.ngrok.io/')
    app_login(app, auth)
    
    # ------------------
    # Begin calling loop
    # ------------------
    
    print('Looping list calls. Current call length is {} seconds.'.format(call_length))
    
    while True:
        current_name = get_name(driver)
        
        current_number = get_number(driver)
        
        talked = False
        
        initiate_call(app,current_number)
        
        alert = colored('Press "ctrl" to pause if answered: ', 'red')
        print('\nCurrently calling {} at {}. {}'.format(current_name, current_number, alert))
        
        # initiate keyboard listener
        with keyboard.Listener(on_press=on_press) as listener:
            # listen for duration
            t_end = time.time() + call_length
            while time.time() < t_end:
                if talking == True:
                    print('talking = True. Breaking loop.')
                    break
                time.sleep(1)
                
            if talking == True:
                print('Out of loop. Currently paused while talking.')
                time_slots = driver.find_element_by_id('appointment_meeting_id').find_elements_by_tag_name('option')
                print(
                        '\n# ---------------------',
                        '\n# Time slots available:',
                        '\n# ---------------------',
                        '\n# Index | Choices'
                        )
                for i,a_time in zip(range(len(time_slots)),time_slots):
                    print('#',' [{}]   '.format(i),a_time.text)
                
                print(
                        '\nPress "y" and enter to schedule i1 appointment.',
                        '\nPress "s" and enter to adjust call length: ',
                        '\nPress any key to hang up and continue.'
                        )
                selection = input()
                if selection == 'y':
                    confirmed = False
                    while confirmed == False:
                        try:
                            slot = int(input('Enter the index of the appointment slot: '))
                            if slot not in range(len(time_slots)):
                                print('The entered index is greater than the available indices')
                                continue
                            print('You choose appointment: {}'.format(time_slots[slot].text))
                            correct = input('Enter "y" to confirm; enter any other key to change time slot: ')
                            if correct == 'y':    
                                time_slots[slot].click()
                                confirmed = True
                            else:
                                pass
                        except ValueError:
                            print('\nEnter a number of an index.')
                            pass
                ###input('### testing pause to examine schedule selection')
                if selection == 's':
                    print('\nCall length is currently {} seconds'.format(call_length))
                    call_length = int(input('Enter a new call_length and hit enter: '))
                    print('Call length is now {} seconds'.format(call_length))
                else:
                    pass
                talking = False
                talked = True
        
        # hangup
        end_call(app)
        
        # specify call type as i1 Schedule Call
        element = driver.find_element_by_id('call_east_type_id')
        all_options = element.find_elements_by_tag_name("option")
        all_options[5].click()
        
        # fill in call fields 
        element = driver.find_element_by_id('call_east_result_id')
        all_options = element.find_elements_by_tag_name("option")
        if talked:
            # click 'Talked'
            all_options[0].click()
        else:
            # click 'Did not reach'
            all_options[5].click()
        
        # log call
        buttons = driver.find_elements_by_name('commit')
        buttons[1].click()
        
        # next button for sourced call
        call_count = next_call(driver, call_count)
        
        
        print('Total calls made this session: {}'.format(call_count))
        print('Press "ctrl" then "c" at anytime to quit...')


def instructions():
    '''This function provides text-based instructions'''
    
    print(colored('###--- INSTRUCTIONS ---###', 'blue', 'on_white'),
          '\n\nThis is a text based program to automatically dial',
          'unreachables on the SIMON platform and automatically log the results.',
          '\n\nYou will be asked to login to SIMON so the program',
          'can automatically log calls for you. Once you have logged',
          'in the program will start calling unreachables for your schools,',
          'directly from your laptop.\n\n',
          colored('WHAT YOU NEED TO DO: ','white','on_red'),
          '\n\nIf someone answers press the "crtl" key on your laptop to',
          'pause the program while you talk. When you press "ctrl" a menu',
          'will appear to allow you to schedule an I1 with the press of a key.\n')
    
    print('\n\nBegin the program by entering how many seconds you would like',
          'the program to spend calling each unreachable before hanging up.',
          'The suggested time is 30 seconds. \nNote that you will be able to adjust',
          'this later by pressing "ctrl" to pause the program')
    length = int(input('\nEnter the number of seconds: '))
   
    return length
    
    
def initiate_call(driver, number_to_call, in_volume=2, out_volume=6):
    '''
    Takes in the driver for the twilio
    web app and clicks 'call', then mutes
    the initial dial ringtone by sending 
    commands to bash.
    '''
    # clear
    driver.find_element_by_id('phone-number').clear()
        
    # new number
    driver.find_element_by_id('phone-number').send_keys(number_to_call)
    
    # dial and mute tone
    driver.find_element_by_id('button-call').click() 
    os.system('osascript -e "set Volume {}"'.format(in_volume))
    time.sleep(2.5)
    os.system('osascript -e "set Volume {}"'.format(out_volume))
    return


def end_call(driver, in_volume=2, out_volume=6):
    try:
        print('Hanging up...')
        driver.find_element_by_id('button-hangup').click()
        os.system('osascript -e "set Volume {}"'.format(in_volume))
        time.sleep(.5)
        os.system('osascript -e "set Volume {}"'.format(out_volume))
    except:
        print('Call already ended...')
    
    
def next_click(driver, element_to_click):
    '''
    Takes in a driver and the element to click
    and delays until a new url is loaded, thus
    ensuring that the new page is loaded before
    proceeding.
    '''
    current = driver.current_url
    element_to_click.click()
    while current == driver.current_url:
        time.sleep(.5)
        print('loading...')
    return


def next_url(driver, url):
    '''
    Takes in a driver and a url to vist and
    delays until the new url is successfully
    loaded.
    '''
    current = driver.current_url
    driver.get(url)
    while current == driver.current_url:
        time.sleep(.5)
        print('loading..')
    return
    

def app_login(driver, simon_username):
    '''
    Takes in the app webdriver and the input
    email and attempts to login to the webapp
    based on the database of approved logins.
    '''
    next_url(driver,'https://sw-calling-app.appspot.com/login')
    
    user = driver.find_element_by_name('username')
    user.send_keys(simon_username)
    
    login_button = driver.find_element_by_css_selector('.btn.btn-default')
    login_button.click()    
    
    print('Authenticating SIMON login...')
    time.sleep(3)

    try:
        driver.find_element_by_id('phone-number')
        print('Authenicated.')

    except:
        msg_1 = '\n\nYour SIMON login {} is not registered to use this application.'.format(simon_username)
        msg_2 = '\n Please contact Teghan Nightengale at 613-484-4779 if you believe'
        msg_3 = '\n you should have privledges to use this program.'
        privledges = colored(msg_1 + msg_2 + msg_3, 'red')
        sys.exit(privledges)
    
    return
    
    
def simon_login(driver):
    '''
    Takes in a webdriver and directs
    it to the student works website
    and attemps to login until the
    website allows access.
    '''
    logged_in = False
    while logged_in == False:
        driver.get('http://www.studentworks.net/')
        
        email = input('Enter your Simon login email: ')
        password = input('Enter your Simon password: ')    
        #email = 'smorris@studentworks.com'
        #password = 'apples'
        
        email_input = driver.find_element_by_id('user_email')
        password_input = driver.find_element_by_id('user_password')
        
        email_input.send_keys(email)
        password_input.send_keys(password)
        
        current = driver.current_url
        driver.find_element_by_name('commit').click()
        time.sleep(3)
        
        if current != driver.current_url:
            logged_in = True
            continue
        else:
            print('\nInvalid login. Re-enter credentials: \n')
            continue
        
    return email


def list_elements(e):
    '''
    Prints the indices and text of a 
    list of selenium webelements.
    '''
    for i, j in zip(range(len(e)), e):
        print('#',' [{}]    '.format(i),j.get_attribute('text'))

def get_number(driver):
    '''
    Get the current applicants phone number on SIMON.
    '''
    phone_number = driver.find_element_by_id('applicant_phone1').get_attribute('value')
    return phone_number


def get_name(driver):
    '''
    Get the current applicant's name on SIMON and
    return a colourized string to be printed to bash.
    '''
    first_name = driver.find_element_by_id('applicant_first_name').get_attribute('value')
    last_name = driver.find_element_by_id('applicant_last_name').get_attribute('value')
    full_name = first_name + ' ' + last_name
    colorized = colored(full_name, 'white', 'on_magenta')
    return colorized
    


def unreachables_selection(driver):
    '''
    Presents a menu of unreachables.
    '''
    menu = driver.find_element_by_class_name('dropdown-menu')
    menu = menu.find_elements_by_tag_name('a')
    print(
            '\n# ---------------------',
            '\n# Unreachables Menu:   ',
            '\n# ---------------------',
            '\n# Index | Choices'
            )
    
    list_elements(menu)

    confirmed = False
    while confirmed == False:
        choice = int(input('\nEnter the index of the unreachables you would like to begin calling: '))
        if choice not in range(len(menu)):
            print('Invalid index selected.')
            continue
        else:
            text = menu[choice].get_attribute('text')
            print('You have selected {}. Press "y" to confirm or any other key to reselect: '.format(text))
            check = input()
            if check in ['Y','y']:
                confirmed = True
                continue
            else:
                continue 
            
    next_url(driver, menu[choice].get_attribute('href'))
    
    return text
    

def go_to_unreachables(driver):
    '''
    Navigates to the unreachables page.
    Returns an error if it doesn't work.
    '''
   
    next_url(driver,'http://www.studentworks.net/recruiting/')
    while True:
        university = unreachables_selection(driver)
        
        # find first name: 30th element in tag_names('a')
        
        try:
            unreachables = driver.find_elements_by_tag_name('a')[33]
            next_click(driver, unreachables)
            break
        except:
            msg_1 = 'There does not appear to be a list of unreachables for {}.'.format(university)
            msg_2 = '\nCheck SIMON manually to ensure that there is a list of unreachables on the {} page.'.format(university)
            error = colored('AN ERROR OCCURRED:\n' + msg_1 + msg_2, 'white', 'on_red')
            print(error)
            print('\nWould you like to call unreachables from another University?')
            selection = input('Enter "y" or any other key to exit: ')
            if selection in ['y','Y']:
                continue
            else:
                quitting = colored('You entered {}. Exiting program...'.format(selection), 'red')
                sys.exit(quitting)


def next_call(driver, call_count):
        '''
        try:
            
        next_unreachable = driver.find_element_by_css_selector(".btn.btn-success.pull-right")
        next_click(driver, next_unreachable)
        call_count += 1
        except:
            
        finally:
            sys.
        '''
        try:
            next_unreachable = driver.find_element_by_css_selector(".btn.btn-success.pull-right")
            next_click(driver, next_unreachable)
            call_count += 1
        except:
            try:
                next_unreachable = driver.find_element_by_css_selector(".btn.btn-default.pull-right")
                next_click(driver, next_unreachable)
                call_count += 1
            except:
                sys.exit(colored('Error: No button for next call.','red'))
        
        return call_count
    
def on_press(key):
    global talking
    try:
        #print('key: {0}'.format(key))
        if str(key) == 'Key.ctrl':
            print('Key.ctrl. talking = True')
            talking = True
    except AttributeError:
        print('special key {0} pressed'.format(
            key))


if __name__ == '__main__':
    main()