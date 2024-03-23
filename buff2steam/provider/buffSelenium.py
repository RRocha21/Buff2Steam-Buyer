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

class BuffSelenium:

    def __init__(self, session=None, remember_me=None):
        logger.info('BuffSelenium', session, remember_me)
        self.session = session
        self.remember_me = remember_me
            
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

            driver.get('https://buff.163.com/goods/36338') 
            
            driver.delete_all_cookies()
            driver.execute_script('window.localStorage.clear();')
            
            driver.add_cookie({'name': 'session', 'value': self.session})
            driver.add_cookie({'name': 'remember_me', 'value': self.remember_me})

            driver.refresh()
            time.sleep(0.5)
            
            self.driver = driver
            return self
        except Exception as e:
            logger.error(f'Failed to open Steam: {e}')
            exit(1)

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.driver.quit()
        
        
    async def checkDivLocated(self):
        divLocated = 6
        try:
            WebDriverWait(self.driver, 3).until(EC.presence_of_element_located((By.XPATH, '/html/body/div[{}]/div/div[1]/div[2]/div[1]/h1'.format(divLocated))))
        except TimeoutException:
            divLocated += 1
            
        if divLocated == 7:
            try: 
                WebDriverWait(self.driver, 2).until(EC.presence_of_element_located((By.XPATH, '/html/body/div[{}]/div/div[1]/div[2]/div[1]/h1'.format(divLocated))))
            except TimeoutException:
                divLocated = 0
                return divLocated
        return divLocated
        
    async def checkListing(self, divLocated, min_price):
        try:
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, '/html/body/div[{}]/div/div[7]/table/tbody/tr[2]/td[5]/div[1]/strong'.format(divLocated))))
            price = self.driver.find_element(By.XPATH, '/html/body/div[{}]/div/div[7]/table/tbody/tr[2]/td[5]/div[1]/strong'.format(divLocated)) #consistent html behavior across different item links for CS:GO
        except NoSuchElementException:
            return False
        except TimeoutException:
            return False
        price_text = price.text
        price_text = price_text.replace('¥', '').strip()
        price_float = float(price_text)

        logger.info(f'price_float: {price_float}')
        logger.info(f'min_price: {min_price}')
        if price_float <= float(min_price) + 0.1:
            return True
        return False
    
    async def clickToBeginPurchase(self, divLocated):
        try:
            element = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.XPATH, '/html/body/div[{}]/div/div[7]/table/tbody/tr[2]/td[6]/a'.format(divLocated))))
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            element.click()
            return True
        except TimeoutException:
            return False

    async def clickToPurchase(self):
        divLocated = 28
        try:
            element = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.XPATH, '/html/body/div[{}]/div[2]/div[4]/a'.format(divLocated))))
        except TimeoutException:
            divLocated -= 1
        if divLocated == 27:
            try:
                element = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.XPATH, '/html/body/div[{}]/div[2]/div[4]/a'.format(divLocated))))
            except TimeoutException:
                divLocated -= 1
        if divLocated == 26:
            try:
                element = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.XPATH, '/html/body/div[{}]/div[2]/div[4]/a'.format(divLocated))))
            except TimeoutException:
                divLocated -= 1
        if divLocated == 25:
            try:
                element = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.XPATH, '/html/body/div[{}]/div[2]/div[4]/a'.format(divLocated))))
            except TimeoutException:
                divLocated == 0
        if divLocated == 0:
            return False
        else:
            element.click()
            return True

    async def open_url(self, url, min_price):
        try:
            self.driver.execute_script("window.open('{}', '_blank');".format(url))
            
            self.driver.switch_to.window(self.driver.window_handles[0])
            self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[0])

            
            divLocated = await self.checkDivLocated()
            logger.info(f'divLocated: {divLocated}')
            if divLocated != 0:
            
                listingStatus = await self.checkListing(divLocated, min_price)
                logger.info(f'listingStatus: {listingStatus}')
                if listingStatus == True:
                    beginPurchaseClicked = await self.clickToBeginPurchase(divLocated)
                    if beginPurchaseClicked == True:
                        PurchaseClicked = await self.clickToPurchase()
                        if PurchaseClicked == True:
                            return True

            return False
        except Exception as e:
            logger.error(f'Failed to open URL: {e}')
            return False