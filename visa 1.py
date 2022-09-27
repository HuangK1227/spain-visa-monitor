from datetime import datetime
from utils.basic import Basic
from utils.log import logger
# from utils import config
from utils.decorators import singleton
from selenium.webdriver.common.keys import Keys
import re
import ast
import importlib
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import random
import pandas as pd
import time


class Visa(Basic):

    def __init__(self, driver, user_config):
        super().__init__(driver)
        self.user_config = importlib.import_module('utils.'+user_config)
        self.eligible_dates = self.find_eligible_date()
        print(self.eligible_dates)

    def open_page(self, page):
        self.driver.get(page)

    # def wait_for_select_time_appear(self):
    #     WebDriverWait(self.driver, 90).until(ec.invisibility_of_element_located((By.ID, "app_time")))

    def select_centre(self, county, city, category):
        self.wait_for_secs()
        self.click_el(name="JurisdictionId")
        self.click_el(xpath="//select[@name='JurisdictionId']/option[contains(text(),'{}')]".format(county))
        self.wait_for_loading()
        self.click_el(name="centerId")
        self.click_el(xpath="//select[@name='centerId']/option[contains(text(),'{}')]".format(city))
        self.wait_for_loading()
        self.click_el(name="category")
        self.click_el(xpath="//select[@name='category']/option[contains(text(),'{}')]".format(category))
        self.wait_for_loading()
        self.click_el(name='checkDate')
        logger.info("select centre finished")

    def go_to_appointment_page(self, phone='', email=''):
        self.open_page(self.user_config.OPENED_PAGE)
        # self.select_centre("England", "Manchester", "Normal")
        # self.enter_phone_and_email(phone, email)
        # self.enter_wrong_code(email, config.PASSWORD)
        # self.enter_code_from_email(email)

    def login(self):
        try:
            # self.click_el(xpath="//a[text() = 'Log in']")
            
            # element = self.driver.find_element_by_xpath("//a[contains(text(),'Log in')]")
            # element.click()
            
            self.wait_for_secs()
            self.enter_message(self.user_config.EMAIL, name='email')
            self.wait_for_secs()
            self.enter_message(self.user_config.PASSWORD, name='password')
            self.wait_for_secs()
            self.click_el(name="login")
            logger.info("log in finished")
        except Exception as e:
            logger.error(e)

    def go_to_book_appointment(self):
        unique_suffix = self.user_config.OPENED_PAGE.split('/')[-1]
        link = f'book-appointment/{unique_suffix}'
        logger.info(f"date appointment link = [{link}]")
        # open a new tab
        self.driver.execute_script(f'window.open(\"{link}\","_blank");')
        # switch to the new tab
        self.driver.switch_to.window(self.driver.window_handles[-1])
        logger.info("go to book appointment finished")

    def check_available_dates(self):
        self.click_el(id="VisaTypeId")
        self.click_el(xpath="//select[@id='VisaTypeId']/option[contains(text(),'{}')]".format(self.user_config.VISA_TYPE))
        self.driver.find_element_by_xpath("//body").click()

        self.wait_for_secs()

        
        original_script = self.driver.find_elements_by_xpath('//body/script')[1].get_attribute('innerHTML')
        available_dates_text = re.findall('var available_dates = (.+?);', original_script)[0]

        available_dates = ast.literal_eval(available_dates_text)
        
        return(available_dates)

    
    def reserve_date(self, available_dates):
        try:
            this_datetime = None
            for i in available_dates[::-1]:
                if i in self.eligible_dates:
                    this_datetime = datetime.strptime(i, '%d-%m-%Y')
                    break
            
            if this_datetime is not None:
                date_string = this_datetime.strftime('%Y-%m-%d')
                self.enter_message(date_string+Keys.ENTER, id = 'app_date')
                # self.wait_for_loading()
                self.click_el(id = "app_time")
                all_times = self.driver.find_elements_by_xpath("//select[@name='app_time']//option")
                option_select = random.randint(1, len(all_times) - 1)
                all_times[option_select].click()
                
                # self.wait_for_secs()
                self.click_el(xpath = "//button[@name='bookDate']")
                # self.wait_for_loading()
                
                try:
                    self.driver.find_element_by_xpath("//div[@class='content-body']/div[@class='alert alert-danger']")
                    logger.error('Did not beat other competitors')
                    return(1)
                
                except NoSuchElementException:
                    logger.info("Successfully made new appointment")
                    return(0)
            
            else:
                logger.info("No eligible dates")
                return(2)
        
        except Exception as e:
            logger.error(f'Cannot successfully made appointment. {e}')
            return(3)
        
    
    def find_eligible_date(self):
        
        start_datetime = datetime.strptime(self.user_config.START, '%d/%m/%Y')
        end_datetime = datetime.strptime(self.user_config.END, '%d/%m/%Y')
        
        time_range = [i.strftime('%d-%m-%Y') 
                      for i in pd.date_range(start_datetime, end_datetime, freq = 'D')]
        if hasattr(self.user_config, 'EXCEPT'):
            for date in self.user_config.EXCEPT:
                this_date = '-'.join( date.split('/') )
                time_range.remove(this_date)
        
        return(time_range)
    
    
    def wait_for_specified_time(self, start_time, end_time, wait_time):
        if end_time - start_time < wait_time:
            time.sleep(wait_time - (end_time-start_time) )
        