from buff2steam import logger

from datetime import datetime

import asyncpg
from psycopg2 import sql

import json

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException

import time

import json
from win11toast import toast

class SteamSelenium:

    def __init__(self, sessionid=None, steamLoginSecure=None):
        logger.info('SteamSelenium', sessionid, steamLoginSecure)
        self.sessionid = sessionid
        self.steamLoginSecure = steamLoginSecure
            
    async def __aenter__(self):
        try:
            options = webdriver.ChromeOptions()
            # options.add_argument('--headless')
            options.add_argument("--enable-javascript")
            options.add_argument("--allow-running-insecure-content")
            options.add_argument("--disable-web-security")
            # options.add_argument("--incognito")
            options.add_argument("--disable-cache")

            # Disable images
            prefs = {"profile.managed_default_content_settings.images": 2, "profile.default_content_setting_values.notifications": 2, "profile.managed_default_content_settings.stylesheets": 2}
            options.add_experimental_option("prefs", prefs)

            options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)")
            
            driver = webdriver.Chrome(options=options)

            driver.get('https://steamcommunity.com/market/listings/730/AWP%20%7C%20Neo-Noir%20%28Field-Tested%29') 
            
            driver.delete_all_cookies()
            driver.execute_script('window.localStorage.clear();')
            
            driver.add_cookie({'name': 'sessionid', 'value': self.sessionid})
            driver.add_cookie({'name': 'steamLoginSecure', 'value': self.steamLoginSecure})

            driver.refresh()
            time.sleep(0.5)
            
            self.driver = driver
            return self
        except Exception as e:
            logger.error(f'Failed to open Steam: {e}')
            exit(1)

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.driver.quit()

    async def open_url(self, url, listing_id):
        logger.info(f'Opening URL: {url}')
        try:
            self.driver.execute_script("window.open('{}', '_blank');".format(url))
            
            self.driver.switch_to.window(self.driver.window_handles[0])
            self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[0])
            
            try: 
                element = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.ID, 'listing_{}'.format(listing_id))))
                
                button_to_click = element.find_element(By.XPATH, './div[2]/div[1]/div[1]/a')
                self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                button_to_click.click()
                
                confirm_ssa = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.ID, 'market_buynow_dialog_accept_ssa_container')))
                confirm_ssa_button = confirm_ssa.find_element(By.XPATH, './input')
                confirm_ssa_button.click()
                
                confirm_buy = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.ID, 'market_buynow_dialog_paymentinfo_bottomactions')))
                confirm_buy_button = confirm_buy.find_element(By.XPATH, './a')
                confirm_buy_button.click()
                
            except TimeoutException:
                logger.error(f'Failed to open URL: Timeout')
                return False
            except NoSuchElementException as e:
                logger.error(f'Failed to locate element: {e}')
                return False
            except Exception as e:
                logger.error(f'Failed to perform action: {e}')
                return False

            return True
        except Exception as e:
            logger.error(f'Failed to open URL: {e}')
            return False

        try:
            id = 1
            
            async with self.pool.acquire() as connection:
                async with connection.transaction():
                                
                    existing_document = await connection.fetchrow(
                        f"SELECT * FROM exchangerates WHERE id = $1", id
                    )
                    
                    return existing_document
        except Exception as e:
            logger.error(f'Failed to insert document into PostgreSQL: {e}')