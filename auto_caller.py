#import selenium
from selenium import webdriver
#import twilio
#import subprocess
import time
from pynput import keyboard
import os
from termcolor import colored

# workflow
def main():
    global talking
    talking = False
    # ----------
    # Logging in
    # ----------
    
    logged_in = False
    while logged_in == False:
        chrome_exe_path = os.path.abspath('chromedriver')
        driver = webdriver.Chrome(chrome_exe_path)
        driver.get('http://www.studentworks.net/')
        
        email = input('Enter your Simon login email: ')
        password = input('Enter your Simon password: ')    
        #email = 'tnightengale@gmail.com'
        #password = 'j#2smn915915E'
        
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
        
    
    # -------------------
    # Go to phone numbers
    # -------------------
    
    driver.get('http://www.studentworks.net/recruiting/applicants/list?unreachables=1')
    
    # find first name: 21st element in tag_names('a')
    
    atag_elements = driver.find_elements_by_tag_name('a')
    
    atag_elements[21].click()
    
    # ----------------
    # load webdial app
    # ----------------
    
    #input('Ensure you have run the twilio app.py in another terminal.\nPress any key to continue: ')
    
    app = webdriver.Chrome(chrome_exe_path)
    app.get('http://localhost:5000/')
    
    #input('Click over to twilio app page. Then press any key to continue: ')
    
    # ------------------
    # Begin calling loop
    # ------------------
    
    #call_button = app.find_element_by_id('button-call')
    #hangup_button = app.find_element_by_id('button-hangup')
    #number_input = app.find_element_by_id('phone-number')
    
    allowances = False
    print('Call own phone to set allowances for microphone access on app')
    my_number = input('Enter 10 digit phone number, no spaces: ')
    app.find_element_by_id('phone-number').send_keys(my_number)
    app.find_element_by_id('button-call').click()
    while allowances == False:
        try:
            input('Go to webpage with the grey background and click "accept" on the microphone prompt. \nThen press enter to continue: ')      
            app.find_element_by_id('button-hangup').click()
            allowances = True
        except:
            continue
        
    
    call_count = 0
    call_length = 25
    print('Looping list calls. Current call length is {} seconds.'.format(call_length))
    
    while True:
        # current call information
        first_name = driver.find_element_by_id('applicant_first_name').get_attribute('value')
        last_name = driver.find_element_by_id('applicant_last_name').get_attribute('value')
        current_name = first_name + ' ' + last_name
        current_name = colored(current_name, 'white', 'on_magenta')
        phone_element = driver.find_element_by_id('applicant_phone1')
        current_number = phone_element.get_attribute('value')
        
        # clear old number
        app.find_element_by_id('phone-number').clear()
        
        # input number to twilio app
        app.find_element_by_id('phone-number').send_keys(current_number)
        
        # call and mute first annoying twilio dial tone
        #app.find_element_by_id('button-call').click()
        os.system('osascript -e "set Volume 0"')
        time.sleep(2.5)
        os.system('osascript -e "set Volume 10"')
        talked = False
        
        # initiate keyboard listener
        alert = colored('Press "ctrl" to pause if answered: ', 'red')
        print('\nCurrently calling {} at {}. {}'.format(current_name, current_number,alert))
        with keyboard.Listener(on_press=on_press) as listener:
            # assume 35 seconds until pick up
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
                            if slot > len(time_slots):
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
                talking = False
                talked = True
        
        # hangup
        try:
            #app.find_element_by_id('button-hangup').click()
            print('Hanging up...')
        except:
            print('Call already ended...')
        
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
        #buttons[1].click()
        
        # next button for sourced call: [23] for sheldon, [22] for next
        next_click(driver, driver.find_elements_by_tag_name('a')[23])
        
        call_count += 1
        
        print('Total calls made this session: {}'.format(call_count))
        print('Press "ctrl" then "c" at anytime to quit...')


def next_click(driver, element_to_click):
    current = driver.current_url
    element_to_click.click()
    while current == driver.current_url:
        time.sleep(.5)
    print('Next SIMON page loaded..') ###
    return
    
    
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