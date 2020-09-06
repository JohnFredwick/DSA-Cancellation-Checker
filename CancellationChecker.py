#for webdriver + interactions
from selenium import webdriver
#for explicit wait
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

#to download and display image
from PIL import Image
import os
import time
import urllib.request
#for date manipulation
from datetime import datetime

#for email
import sys
from smtplib import SMTP as SMTP
from email.mime.text import MIMEText

#load settings
from info import emailAddresses, emailSubject, emailUsername, emailPassword, emailSMTPserver
from info import licenceNumber as DR_LIC_NUM
from info import referenceNumber as APP_REF_NUM
from info import refreshInterval, chromeDriverPath

cancellations = []

#handles email notifications
def sendEmail(datetimeList):
    #should probably point out this was taken from StackOverflow
    destination = emailAddresses

    if datetimeList:
        content = "Available DSA test slots at your selected test centre:\n\n"
        for dt in datetimeList:
            content += "* %s\n" % dt.strftime("%A %d %b %Y at %H:%M")
        content += "\nChange booking at: https://www.gov.uk/change-driving-test"
    else:
        content = "All previously found cancellations have been taken.\n"
        
    content += "\nChecked at [%s]" % time.strftime("%d-%m-%Y @ %H:%M")

    try:
        msg = MIMEText(content, "plain")
        msg["Subject"] = emailSubject
        msg["From"] = emailUsername

        conn = SMTP(emailSMTPserver, 587)
        conn.set_debuglevel(False)
        conn.ehlo()
        conn.starttls()

        conn.login(emailUsername, emailPassword)
        try:
            conn.sendmail(emailUsername, destination, msg.as_string())
        finally:
            conn.close()

    except Exception as exc:
        sys.exit("Mail failed: %s" % str(exc))  # give a error message

#request user solution
#error checking?
def get_user_captcha_sol():
    sol = None
    while not sol:
        sol = input("Type Catcha Solution: ")
        if not sol:
            print("Input is blank")
    return sol

#download captcha image from src, open the image and request user solution
#delete captcha image and return user sol
def display_captcha_image_and_get_sol(captcha_image_elems):
    input()
    captcha_image = captcha_image_elems
    captcha_image_src = captcha_image.get_attribute("src")
    urllib.request.urlretrieve(captcha_image_src, "local_captcha_image")
    image = Image.open("local_captcha_image")
    image.show()
    captcha_input = get_user_captcha_sol()
    image.close()
    os.remove("local_captcha_image")
    return captcha_input

#look for captcha
#if it's there, input user solution and return true
#if not there, return false
def deal_with_captcha(driver):
    #driver.implicitly_wait(4)
    try:
        wait = WebDriverWait(driver, 0)
        captcha_image_elems = wait.until(EC.presence_of_element_located((By.ID,"recaptcha_challenge_image")))
        #captcha_image_elems = driver.find_elements_by_id("recaptcha_challenge_image")
    #if len(captcha_image_elems) > 0:
        captcha_input = display_captcha_image_and_get_sol(captcha_image_elems)
        captcha_response_field = driver.find_element_by_name("recaptcha_response_field")
        captcha_response_field.send_keys(captcha_input)
        captcha_response_field.submit()
        return True
    except TimeoutException:
    #else:
        return False

def log_in_user():
    #go to landing page, find button to next page and click
    driver.get("https://www.gov.uk/change-driving-test")
    link = driver.find_element_by_link_text("Start now")
    link.click()

    #fill out form, check if captcha, submit if deal_with_captcha didn't already submit
    username_box = driver.find_element_by_name("username")
    username_box.send_keys(DR_LIC_NUM)

    password_box = driver.find_element_by_name("password")
    password_box.send_keys(APP_REF_NUM)
    
    #if not deal_with_captcha(driver):
    continue_btn = driver.find_element_by_name("booking-login")
    continue_btn.click()

    #find and click change button
    change_button = driver.find_element_by_id("date-time-change")
    change_button.click()

    #go to third page and check the box to get earliest available tests, submit
    radio_btn = driver.find_element_by_id("test-choice-earliest")
    radio_btn.click()
    radio_btn.submit()
    deal_with_captcha(driver)

#converts each the text of each HTML tag in a_list to datime object in date_time_list
def convert_HTML_to_datetime(a_list):
    date_time_list = []
    for tag in a_list:
        tag_time = tag.get_attribute("data-datetime-label")
        tag_datetime =  datetime.strptime(tag_time, "%A %d %B %Y %I:%M%p")
        date_time_list.append(tag_datetime)
    return date_time_list

#get available and current slot data from page
def extract_raw_HTML_tag_list(driver):
    #container of slots
    button_board = driver.find_element_by_class_name("SlotPicker-days")

    #get current test slot
    checked = button_board.find_elements_by_xpath("//input[@class='SlotPicker-slot'][@checked='checked']")[:1]
    current_time = convert_HTML_to_datetime(checked)[0]
    
    #list of available tests
    a_list = button_board.find_elements_by_xpath("//input[@class='SlotPicker-slot']")
    return a_list, current_time

#returns all earliest available tests in datetime format from website
def find_earliest_available_tests():
    a_list, current_time = extract_raw_HTML_tag_list(driver)
    date_time_list = convert_HTML_to_datetime(a_list)
    return date_time_list, current_time

#filters datetimelist to only those tests before current_time
#then prints out each string in the filtered test list
def list_pre_curr_tests(date_time_list, current_time):
    pre_curr_list = []
    slots_lost = []
    slots_gained = []

    for test_datetime in date_time_list:
        if test_datetime < current_time:
            pre_curr_list.append(test_datetime)

    #see if any cancellation slots have been taken
    for test_datetime in cancellations:
        if not test_datetime in pre_curr_list:
            slots_lost.append(test_datetime)

    #notify of and remove taken cancellation slots 
    if slots_lost:
        print("Cancellation taken:")
        for test_datetime in slots_lost:
            test_str = datetime.strftime(test_datetime, "%A %d %B %Y %I:%M%p")
            print(test_str)
            cancellations.remove(test_datetime)

    #see if any cancellation slots are available
    for test_datetime in pre_curr_list:
        if not test_datetime in cancellations:
            slots_gained.append(test_datetime)
            cancellations.append(test_datetime)

    #notify of slot if new
    if slots_gained:
        print("Cancellations found:")
        for test_datetime in slots_gained:
            test_str = datetime.strftime(test_datetime, "%A %d %B %Y %I:%M%p")
            print(test_str)

    #email if there is change
    if slots_lost or slots_gained:
        sendEmail(cancellations)

#open browser
driver = webdriver.Chrome(chromeDriverPath)
log_in_user()

while True:
    #find earliest available tests from websites, then lists all tests before current_time
    try:
        date_time_list, current_time = find_earliest_available_tests()
        list_pre_curr_tests(date_time_list, current_time)
        time.sleep(refreshInterval)
        driver.refresh()
    except:
        driver.quit()
        driver = webdriver.Chrome(chromeDriverPath)
        log_in_user()
