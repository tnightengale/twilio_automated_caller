#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Oct 25 20:08:03 2018

@author: tnightengale
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import os
import sys
import json
import urllib.request

from fbs_runtime.application_context import ApplicationContext
from PyQt5.Qt import QApplication, QClipboard
from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtWidgets import (QMainWindow, QGridLayout, QWidget, QTextEdit, QPushButton, 
                             QInputDialog, QMessageBox, QLineEdit, QLabel, QComboBox, 
                             QSlider, QLCDNumber, QVBoxLayout, QHBoxLayout, QGroupBox)
from PyQt5.QtCore import Qt, QSize, QThread, pyqtSignal, QObject, QEventLoop, QTimer



class CallThread(QThread):
    
    update_sig = pyqtSignal('PyQt_PyObject')
    name_sig = pyqtSignal('PyQt_PyObject')
    
    def __init__(self, layout):
        super().__init__()
        self.run = True
        self.talked = False
        
        #lcd
        self.lcd = QLCDNumber()
        self.lcd.display(30)
        
        # slider
        self.sld = QSlider(Qt.Horizontal)
        self.sld.setMaximum(60)
        self.sld.setMinimum(10)
        self.sld.setValue(30)
        self.sld.valueChanged.connect(self.lcd.display)
        
        # layout
        self.s_layout = QVBoxLayout()
        self.s_layout.addWidget(self.lcd)
        self.s_layout.addWidget(self.sld)
        
        # slider group
        self.s_group = QGroupBox('Call Length (seconds)')
        self.s_group.setLayout(self.s_layout)
        
        # add to main wideget layout
        self.l = layout
        self.l.addWidget(self.s_group,0,2)
        
        headless = Options()
        #headless.add_argument("--headless")
        headless.add_argument("---info-bars")
        headless.add_argument("--use-fake-ui-for-media-stream")
        chrome_exe_path = os.path.abspath('chromedriver')
        #chrome_exe_path = os.path.join(sys._MEIPASS, "chromedriver")
        self.driver = webdriver.Chrome(chrome_exe_path, options = headless)
        self.app = webdriver.Chrome(chrome_exe_path, options = headless)
        self.driver.get('http://www.studentworks.net/')
        self.app.get('https://sw-calling-app.appspot.com')
        
    def run(self):
        self.run = True
        self.talked = False
        while self.run:
            #call_length = 10
            self.current_name = get_name(self.driver)
            self.current_number = get_number(self.driver)
            self.initiate_call()
            current_call = 'Currently calling {} at {}.'.format(self.current_name, self.current_number)
            self.update_sig.emit(current_call)
            self.name_sig.emit(self.current_name)

            # pause
            QThread.sleep(self.sld.value())
            
            if self.run == False:
                while self.run == False:
                    time.sleep(1)
                    print('run == false loop')
            self.end_call()
            self.log_call()
            self.next_call()
        self.finished.emit()
    
    def initiate_call(self, in_volume=2, out_volume=5):
        '''
        Takes in the driver for the twilio
        web app and clicks 'call', then mutes
        the initial dial ringtone by sending 
        commands to bash.
        '''
        # get initial comp volume
        initial_vol = int(os.popen("osascript -e 'set ovol to output volume of (get volume settings)'").read())//10
        
        # os.system("osascript -e 'get volume settings'")
        # clear
        self.app.find_element_by_id('phone-number').clear()

        # new number
        self.app.find_element_by_id('phone-number').send_keys(self.current_number)
        
        # dial and mute tone
        self.app.find_element_by_id('button-call').click() 
        os.system('osascript -e "set Volume {}"'.format(in_volume))
        time.sleep(2.5)
        os.system('osascript -e "set Volume {}"'.format(initial_vol))
        return
    
    def next_call(self):
        '''
        Try to go to next name
        '''
        try:
            next_unreachable = self.driver.find_element_by_css_selector(".btn.btn-success.pull-right")
            self.next_click(next_unreachable)
        except:
            try:
                next_unreachable = self.driver.find_element_by_css_selector(".btn.btn-default.pull-right")
                self.next_click(next_unreachable)
            except:
                sys.exit('Error: No button for next call.','red')
        return
    
    def log_call(self):
        # specify call type as i1 Schedule Call
        element = self.driver.find_element_by_id('call_east_type_id')
        all_options = element.find_elements_by_tag_name("option")
        all_options[5].click()
        
        # fill in call fields 
        element = self.driver.find_element_by_id('call_east_result_id')
        all_options = element.find_elements_by_tag_name("option")
        if self.talked:
            # click 'Talked'
            all_options[0].click()
        else:
            # click 'Did not reach'
            all_options[5].click()
        
        # log call
        buttons = self.driver.find_elements_by_name('commit')
        buttons[1].click()
            
    def end_call(self, in_volume=2, out_volume=6):
        
        # get initial comp volume
        initial_vol = int(os.popen("osascript -e 'set ovol to output volume of (get volume settings)'").read())//10
        
        try:
            self.update_sig.emit('Hanging up...')
            self.driver.find_element_by_id('button-hangup').click()
            os.system('osascript -e "set Volume {}"'.format(in_volume))
            time.sleep(.5)
            os.system('osascript -e "set Volume {}"'.format(initial_vol))
        except:
            self.update_sig.emit('Call already ended...')
    
    
    def next_click(self, element_to_click):
        '''
        Takes in a driver and the element to click
        and delays until a new url is loaded, thus
        ensuring that the new page is loaded before
        proceeding.
        '''
        current = self.driver.current_url
        element_to_click.click()
        while current == self.driver.current_url:
            time.sleep(.5)
            print('loading...')
            self.update_sig.emit('loading..')
        return

class MainWindow(QWidget):
    
    
    stop_signal = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.initUI()
        self.thread = CallThread(self.layout)
        self.thread.update_sig.connect(self.update)
        self.thread.name_sig.connect(self.call_update)
        #self.thread.finished.connect(self.schedule)
        #self.thread.finished.connect(self.)

        
    def initUI(self):
        # window, icon, title
        self.setMinimumSize(QSize(800, 500))    
        self.setWindowTitle("Student Works Painting Autocaller")
        self.setWindowIcon(QtGui.QIcon('logo.png'))
        #self.setWindowIcon(QtGui.QIcon(os.path.join(sys._MEIPASS, "logo.png")))
        
        # updates label
        self.l_main = QLabel(self)
        self.l_main.setText('Updates:')
        
        # updates text box and scrollbar
        self.t_info = QTextEdit(self)
        self.t_info.setReadOnly(True)
    
        # login labels
        self.l_user = QLabel(self)
        self.l_pass = QLabel(self)
        self.l_user.setText('Choose Authorized Username:')
        self.l_pass.setText('Password:')
        
        # login result label
        self.l_permlog = QLabel(self)
        self.l_permlog.setText('Login Status: ')
        self.l_login = QLabel(self)
        
        # login fields
        self.d_user = self.combo_box()
        self.t_pass = QLineEdit(self)
        self.t_pass.setPlaceholderText('SIMON login password')
        self.t_pass.setEchoMode(QLineEdit.Password)
        
        # login button
        self.b_login = QPushButton("Login",self)
        self.b_login.clicked.connect(self.login_state)
        
        # Display instructions 
        self.instructions()
        
        # calling button
        self.b_calling = QPushButton("Start Calling",self)
        self.b_calling.clicked.connect(self.call_state)
        self.b_calling.setVisible(False)
        
        # schedule button
        self.b_schd = QPushButton('Schedule i1')
        self.b_schd.clicked.connect(self.schedule)
        self.b_schd.setVisible(False)
        
        # hangup button
        self.b_hang = QPushButton('Hangup')
        self.b_hang.clicked.connect(self.hangup)
        self.b_hang.setVisible(False)
        
        # skip button
        self.b_skip = QPushButton('Skip Call')
        self.b_skip.clicked.connect(self.skip_call)
        self.b_skip.setVisible(False)
        
        # name status bar
        self.l_permname = QLabel(self)
        self.l_permname.setText('<b> Current Call: </b>')
        self.l_namebar = QLabel(self)
        self.l_namebar.setText('None')
        
        # update grouping
        self.u_group = QGroupBox()
        self.u_layout = QGridLayout()
        self.u_layout.addWidget(self.l_main,0,0)
        self.u_layout.addWidget(self.t_info,1,0,10,5)
        self.u_group.setLayout(self.u_layout)
        
        # login grouping
        self.l_group = QGroupBox()
        self.l_layout = QGridLayout()
        self.l_layout.addWidget(self.l_user,0,0,1,2)
        self.l_layout.addWidget(self.d_user,1,0,1,2)
        self.l_layout.addWidget(self.l_pass,2,0,1,2)
        self.l_layout.addWidget(self.t_pass,3,0,1,2)
        self.l_layout.addWidget(self.b_login,3,3)
        self.l_layout.addWidget(self.l_permlog,4,0)
        self.l_layout.addWidget(self.l_login,4,1)
        self.l_group.setLayout(self.l_layout)
        
        # button grouping
        self.b_group = QGroupBox()
        self.b_layout = QGridLayout()
        self.b_layout.addWidget(self.b_skip,0,0)
        self.b_layout.addWidget(self.b_calling,1,0)
        self.b_layout.addWidget(self.b_hang,2,0)
        self.b_layout.addWidget(self.b_schd,3,0)
        self.b_group.setLayout(self.b_layout)
        
        # name bar gourping
        self.nb_group = QGroupBox()
        self.nb_layout = QHBoxLayout()
        self.nb_layout.addWidget(self.l_permname)
        self.nb_layout.addWidget(self.l_namebar)
        self.nb_group.setLayout(self.nb_layout)
        
        
        # layout
        self.layout = QGridLayout()
        self.layout.addWidget(self.u_group,0,0,2,1)
       
        self.layout.addWidget(self.l_group,0,1)
        self.layout.addWidget(self.b_group,1,2)
        self.layout.addWidget(self.t_instruct,1,1)
        self.layout.addWidget(self.nb_group,2,0,1,3)
        self.setLayout(self.layout)
    
    def skip_call(self):
        self.hangup()
        #self.thread.next_call()
        self.update('Skipping call... loading next name')
        self.thread.quit() # quit runs the remainder of thread.run() => hang up and next
        self.thread.start()
        
    def hangup(self):
        self.update('Hanging up...')
        end_call(self.thread.app)
        
    def visible(self,boolean):
        self.b_calling.setVisible(boolean)
        self.b_schd.setVisible(boolean)
        self.b_hang.setVisible(boolean)
        self.b_skip.setVisible(boolean)
    
    def pause_visible(self,boolean):
        self.b_schd.setVisible(boolean)
        self.b_hang.setVisible(boolean)
        self.b_skip.setVisible(not boolean)
    
    def call_state(self):
        if self.b_calling.text() == 'Start Calling':
            try:
                self.thread.start()
                self.pause_visible(False)
                self.b_calling.setText('Pause Calling')
            except:
                self.update('Error: cannot make calls at this time.')
        
        elif self.b_calling.text() == 'Pause Calling':
            self.thread.run = False
            self.pause_visible(True)
            self.b_calling.setText('Resume Calling')
        
        else:
            self.thread.run = True
            self.pause_visible(False)
            self.b_calling.setText('Pause Calling')
    
    
    def schedule(self):
        time_slots = self.thread.driver.find_element_by_id('appointment_meeting_id').find_elements_by_tag_name('option')
        options = [i.text for i in time_slots]
        item, okPressed = QInputDialog.getItem(self, "Choose List to Call", "Choose i1 slot:", options, 0, False)
        if okPressed and item:
            time_slots[options.index(item)].click()
            self.update('Scheduled i1 for {}'.format(item))
            self.thread.talked = True
    
    def login_state(self):
        if self.b_login.text() == 'Login':
            self.login()
            
        elif self.b_login.text() == 'Logout':
            self.logout()
            
    
    def logout(self):
        try:
            self.hangup()
            self.thread.terminate()
            self.l_namebar.setText('None')
            self.b_calling.setText('Start Calling')
            
        except Exception as e:
            print(e)
        lo = self.thread.driver.find_element_by_css_selector(".nav.navbar-nav.navbar-right")
        lo = lo.find_element_by_class_name('dropdown')
        lo.find_element_by_class_name('dropdown-toggle').click()
        lo = lo.find_element_by_class_name('dropdown-menu')
        lo = lo.find_elements_by_tag_name('li')
        lo = lo[2].find_element_by_tag_name('a')
        lo.click()
        self.visible(False)
        self.update('You are logged out')
        self.b_login.setText('Login')
        self.l_login.setText('Logged Out')
        
        
    def login(self):
        try:
            username = self.d_user.currentText()
            password = self.t_pass.text()
            email_input = self.thread.driver.find_element_by_id('user_email')
            password_input = self.thread.driver.find_element_by_id('user_password')
            email_input.clear()
            password_input.clear()
            email_input.send_keys(username)
            password_input.send_keys(password)    
            current = self.thread.driver.current_url
            self.thread.driver.find_element_by_name('commit').click()
            self.t_pass.clear()
            if current != self.thread.driver.current_url:
                message = 'Logged in as {}'.format(username)
                self.l_login.setText(message)
                self.b_login.setText('Logout')
                self.names_menu()
            else:
                self.l_login.setText('Invalid Login')
        except:
            error = 'Could not access page. Logging Out. Please try again.'
            self.l_login.setText('Logged Out')
            self.b_login.setText('Login')
            self.update(error)
            self.thread.driver.get('https://studentworks.net/recruiting')
    
    
    def names_menu(self):
        u_menu = self.thread.driver.find_element_by_class_name('dropdown-menu')
        u_menu = u_menu.find_elements_by_tag_name('a')
        u_items = list_elements(u_menu)
        mask = list(map(lambda e: e[0] == 'U', u_items))
        u_items = [i for (i, v) in zip(u_items, mask) if v]
        u_menu = [i for (i, v) in zip(u_menu, mask) if v]
        # names
        n_menu = self.thread.driver.find_elements_by_css_selector(".table.table-bordered.table-hover.table-condensed.table-striped")
        n_menu = n_menu[0].find_elements_by_tag_name('tr')
        schools = []
        for e in n_menu:
            try:
                a = e.find_element_by_tag_name('a')
                schools.append(a)
            except:
                pass
        n_menu = schools[1:-1]
        n_items = list_elements(n_menu)
        menu = u_menu + n_menu
        items = u_items + n_items
        item, okPressed = QInputDialog.getItem(self, "Choose List to Call","School:", items, 0, False)
        if okPressed and item:
            self.thread.driver.get(menu[items.index(item)].get_attribute('href'))
        # names nav
        try:
            nav = self.thread.driver.find_element_by_css_selector(".table.table-condensed.table-striped.table-bordered")
            nav = nav.find_element_by_tag_name('tbody')
            nav = nav.find_element_by_tag_name('tr')
            nav = nav.find_element_by_tag_name('a')
            self.thread.driver.get(nav.get_attribute('href'))
            self.update('Currently on names from {}'.format(item))
            success = 'Ready to make calls to names from {}'.format(item)
            self.update(success)
            self.b_calling.setVisible(True)
        except:
            error = 'Could not access names. Logging Out. Please try again.'
            self.l_login.setText('Logged Out')
            self.update(error)
            self.thread.driver.get('https://studentworks.net/recruiting')
    
    def new_url(self, link):
        print('new url called')
        current = self.thread.driver.current_url
        self.thread.driver.get(link)
        loop = QEventLoop()
        QTimer.singleShot(5000, loop.quit)
        loop.exec_()
        if current == self.thread.driver.current_url:
            error = 'Could not load requested page.'
            self.update(error)
    
    def call_update(self, name):
        self.l_namebar.setText('<h3> {} </h3>'.format(name))
        
    def update(self, message):
        message = '\n\n' + message
        sb = self.t_info.verticalScrollBar()
        self.t_info.insertPlainText(message)
        sb.setValue(sb.maximum())

    
    def combo_box(self):
        user_select = QComboBox(self)
        user_select.addItem('- Select Valid User -')
        with urllib.request.urlopen("https://storage.googleapis.com/logininfo/users.json") as url:
            valid_users = json.loads(url.read().decode())
        user_select.addItems(valid_users)
        return user_select
    
    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Meta:
            self.call_state()
        if e.key() == Qt.Key_Escape:
            self.close()
        
    def instructions(self):
        '''This function provides text-based instructions'''
        self.t_instruct = QTextEdit(self)
        self.t_instruct.setReadOnly(True)
        msg = ['<h2> Instructions </h2>',
              'This program automatically dials names from SIMON and logs',
              'the results of calls for you. It runs on a loop to continuously',
              'dial names on your choosen list of names. To use the program,',
              'follow these steps: ',
              '<ol>',
              '<li>',
              'Login to the program using your SIMON password.',
              '</li>',
              '<li>',
              'Once logged in, a pop up window will allow you to choose a list of names to call.',
              '</li>',
              '<li>',
              'Once you have selected a list of names to call, click the "Start Calling',
              'button to begin calling names.',
              '</li>',
              '<li>',
              'Upon pressing "Start Calling" two buttons will appear:',
              '"Skip Call" and "Pause Calling" and the call loop will begin.',
              'You will hear a dial tone and see the name of the person you are',
              'calling being displayed at the bottom of the screen.',
              '</li>',
              '<li>',
              'You can adjust the number of seconds the program calls',
              'each person by using the slider in the top right corner of the',
              'program.',
              '</li>',
              '<li>',
              'If someone answers your call, you can press "ctrl" on your keyboard',
              'or click the "Pause Calling" button to pause the calling loop.',
              'You will then have the option to hang up, or schedule an i1.',
              'If you schedule an i1 it will automatically log that you talked,',
              'and will log the call and schedule the i1 on the SIMON website.',
              '</li>',
              '</ol>',
              '<b> NOTE: </b> that if you forget to pause the program when',
              'someone picks up, the loop will continue to run, and the call will',
              'end when the amount of seconds specified by the slider has elapsed.']
        message = ' '.join(msg)
        self.t_instruct.setText(message)
        self.t_instruct.setStyleSheet("background-color: rgba(0, 0, 0, 0);")

##################
# HELPER FUNCTIONS
##################

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
    # driver.find_element_by_id('button-call').click() 
    os.system('osascript -e "set Volume {}"'.format(in_volume))
    time.sleep(2.5)
    os.system('osascript -e "set Volume {}"'.format(out_volume))
    return

def end_call(driver, in_volume=2, out_volume=6):
    
    # get initial comp volume
    initial_vol = int(os.popen("osascript -e 'set ovol to output volume of (get volume settings)'").read())//10
        
    try:
        print('Hanging up...')
        driver.find_element_by_id('button-hangup').click()
        os.system('osascript -e "set Volume {}"'.format(in_volume))
        time.sleep(.5)
        os.system('osascript -e "set Volume {}"'.format(initial_vol))
    except:
        
        print('Call already ended...')

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
        CallThread.update_sig.emit('loading..')
    return

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
    return full_name

def list_elements(selenium_list):
    '''
    Produces a list from selenium elements.
    '''
    try:
        text_list = [e.get_attribute('text') for e in selenium_list]
    except:
        text_list = [e.text for e in selenium_list]
    return text_list

def log_call(driver,talked):
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
    #buttons = driver.find_elements_by_name('commit')
    #buttons[1].click()

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
        CallThread.update_sig.emit('loading..')
    return

def next_call(driver):
    '''
    Try to go to next name
    '''
    try:
        next_unreachable = driver.find_element_by_css_selector(".btn.btn-success.pull-right")
        next_click(driver, next_unreachable)
    except:
        try:
            next_unreachable = driver.find_element_by_css_selector(".btn.btn-default.pull-right")
            next_click(driver, next_unreachable)
        except:
            sys.exit('Error: No button for next call.','red')
    return

#################
# FBS Application
#################
    
class AppContext(ApplicationContext):           # 1. Subclass ApplicationContext
    def run(self): 
        try:                                    # 2. Implement run()
            window = MainWindow()
            window.show()
            return self.app.exec_()   
        finally:                                # 3. End run() with this line
            print('finally triggered')
            window.thread.driver.close()
            window.thread.app.close()

if __name__ == '__main__':
    appctxt = AppContext()                      # 4. Instantiate the subclass
    exit_code = appctxt.run()                   # 5. Invoke run()
    sys.exit(exit_code)
   

'''
def main():
    try:
        app = QtWidgets.QApplication(sys.argv)
        mainWin = MainWindow()
        mainWin.show()
        sys.exit( app.exec_() )
    
    finally:
        print('finally triggered')
        mainWin.thread.driver.close()
        mainWin.thread.app.close()
    
if __name__ == "__main__":
    main()
'''