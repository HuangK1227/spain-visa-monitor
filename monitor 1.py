import time
import telebot
from utils import config
from utils.log import logger
from visa import Visa
from selenium import webdriver
import sys
import undetected_chromedriver as uc

bot = telebot.TeleBot(config.BOT_TOKEN)


def init_driver():
    # profile = {
    #     "profile.default_content_setting_values.notifications": 2  # block notifications
    # }
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--disable-popup-blocking')
    # chrome_options.add_experimental_option('prefs', profile)
    
    # firefox_options = webdriver.FirefoxOptions()
    # firefox_options.set_preference("dom.webnotifications.enabled", False)
    
    # chrome_options.add_argument('--headless')
    # chrome_options.add_argument("--user-data-dir=/Users/vxwong/Library/Application Support/Google/Chrome")
    # driver = webdriver.Chrome(options=chrome_options)
    if sys.platform == 'win32':
        driver = uc.Chrome(options=chrome_options)
    if sys.platform == 'darwin':
        driver = webdriver.Chrome('/Users/sicongli/Library/CloudStorage/OneDrive-LondonBusinessSchool/phd_life/VisaCode/USvisaLondon/chromedriver',options=chrome_options)
        # driver = webdriver.Firefox(options = firefox_options)
    driver.implicitly_wait(3)
    return driver


def monitor(user_config = 'config'):
    try:
        driver = init_driver()
        visa = Visa(driver, user_config)
        # visa.go_to_appointment_page()
        visa.driver.get("https://uk.blsspainvisa.com/visa4spain/login")
        visa.wait_for_loading()
        
        if 'Error' in driver.find_element_by_xpath('/html/body').text:
            logger.info(f"SPANISH VISA ({visa.user_config.EMAIL}): 404")
            bot.send_message(chat_id=config.CHAT_ID, text=f"SPANISH VISA ({visa.user_config.EMAIL}): 404")
            driver.quit()
            time.sleep(3600)
            monitor(user_config)
        
        visa.login()
        visa.wait_for_loading()

        if driver.find_elements_by_xpath("/html/body/center/h1"):
            logger.info(f"SPANISH VISA ({visa.user_config.EMAIL}): 403")
            bot.send_message(chat_id=config.CHAT_ID, text=f"SPANISH VISA ({visa.user_config.EMAIL}): 403")
            driver.quit()
            time.sleep(300)
            monitor(user_config)

        visa.go_to_book_appointment()
        
        if 'Error' in driver.find_element_by_xpath("//div[@id='content']//div[@class='row btm_border']//h2").text:
            bot.send_message(chat_id=config.CHAT_ID, text=f"SPANISH VISA ({visa.user_config.EMAIL}): Successfully reserved a place, but double check.")
            return(None)
        
        visa.wait_for_loading()
        
        visa.select_centre(visa.user_config.COUNTY, visa.user_config.CENTER, visa.user_config.CATEGORY)
        end_time = 1e12
        last_start_time = 0
        while True:
            dates = visa.check_available_dates()
            if dates:
                success = visa.reserve_date(dates)
                logger.info(f"SPANISH VISA ({visa.user_config.EMAIL}): DAY AVAILABLE: {dates}")
                bot.send_message(chat_id=config.CHAT_ID, text=f'SPANISH VISA ({visa.user_config.EMAIL}): DAY AVAILABLE: {dates}')
                if success == 0:
                    logger.info(f'SPANISH VISA ({visa.user_config.EMAIL}): Successfully made new appointment')
                    bot.send_message(chat_id=config.CHAT_ID, text=f'SPANISH VISA ({visa.user_config.EMAIL}): Successfully made new appointment')
                    break
                # time.sleep(config.TIMEOUT)
                # driver.refresh()
                elif success == 1:
                    logger.info(f'SPANISH VISA ({visa.user_config.EMAIL}): Did not beat other competitors')
                    bot.send_message(chat_id=config.CHAT_ID, text=f'SPANISH VISA ({visa.user_config.EMAIL}): Did not beat other competitors')
                    # time.sleep(config.TIMEOUT)
                    visa.wait_for_specified_time(last_start_time, end_time, config.TIMEOUT)
                    last_start_time = time.time()
                    visa.open_page(visa.user_config.APPOINTMENT_PAGE)
                    end_time = time.time()
                elif success == 2:
                    logger.info(f'SPANISH VISA ({visa.user_config.EMAIL}): No eligible dates')
                    # time.sleep(config.TIMEOUT)
                    visa.wait_for_specified_time(last_start_time, end_time, config.TIMEOUT)
                    # driver.refresh()
                    last_start_time = time.time()
                    visa.open_page(visa.user_config.APPOINTMENT_PAGE)
                    end_time = time.time()
                else:
                    logger.info(f'SPANISH VISA ({visa.user_config.EMAIL}): Cannot successfully make appointments')
                    bot.send_message(chat_id=config.CHAT_ID, text=f'SPANISH VISA ({visa.user_config.EMAIL}): Cannot successfully make appointments')
                    # time.sleep(config.TIMEOUT)
                    visa.wait_for_specified_time(last_start_time, end_time, config.TIMEOUT)
                    # driver.refresh()
                    last_start_time = time.time()
                    visa.open_page(visa.user_config.APPOINTMENT_PAGE)
                    end_time = time.time()
                # driver.back()
            else:
                logger.info(f"SPANISH VISA ({visa.user_config.EMAIL}): NO DAY AVAILABLE..")
                # bot.send_message(chat_id=config.CHAT_ID, text=f"NO DAY AVAILABLE..")
                # time.sleep(config.TIMEOUT)
                visa.wait_for_specified_time(last_start_time, end_time, config.TIMEOUT)
                last_start_time = time.time()
                visa.open_page(visa.user_config.APPOINTMENT_PAGE)
                end_time = time.time()

    except Exception as e:
        logger.error(f'Monitor runtime error. {e}')
        driver.quit()
        monitor(user_config)


def test_notify():
    try:
        bot.send_message(chat_id=config.CHAT_ID, text='hello, test ok')
    except Exception as e:
        logger.error(
            f'Test notify error. please make sure that you\'ve sent a message to wongs_bot if you didn\'t change the CHAT_ID in the config.\n\n {e}')
        exit(0)


def main():
    if len(sys.argv[1:]) != 1:
        test_notify()
        monitor()
    else:
        user_config = sys.argv[1:][0]
        test_notify()
        monitor(user_config)
        

if __name__ == "__main__":
    main()
