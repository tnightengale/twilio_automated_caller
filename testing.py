#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Oct 14 12:18:46 2018

@author: tnightengale
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os
import time

def main():
    
    headless = Options()
    headless.add_argument("--headless")
    headless.add_argument("---info-bars")
    headless.add_argument("--use-fake-ui-for-media-stream")
    chrome_exe_path = os.path.abspath('chromedriver')
    
    app = webdriver.Chrome(chrome_exe_path, options = headless)
    app.get('https://14de8b3c.ngrok.io/')
    
    my_number = '6134844779'
    number_field = app.find_element_by_id('phone-number')
    number_field.send_keys(my_number)
    
    call_button = app.find_element_by_id('button-call')
    call_button.click()
    
    print('calling...')
    time.sleep(15)
    
    hangup_button = app.find_element_by_id('button-hangup')
    hangup_button.click()
    
    return

def google(driver):
    ''' Sends driver to google'''
    driver.get('https://google.com')
    
def wrong():
    try: 
        [] + 3
    except Exception as e:
        return e
        

def error_test():
    try:
        driver.find_element_by_class_name('error')
    except:
        print("yay")

if __name__ == '__main__':
    main()