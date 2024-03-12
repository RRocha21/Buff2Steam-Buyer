import asyncio
from datetime import datetime

from buff2steam.provider.buffSelenium import BuffSelenium
from buff2steam.provider.postgres import Postgres
from buff2steam import logger, config

import os

from urllib.parse import unquote

import random

import time

from urllib.parse import unquote

import json

from win11toast import toast

last_entry_checked = None

iconTrue = {
    'src': 'https://i.ibb.co/0sYG97C/checkmark-true.png',
    'placement': 'appLogoOverride'
}

iconFalse = {
    'src': 'https://i.ibb.co/mzWDY0n/checkmark-false.png',
    'placement': 'appLogoOverride'
}

async def notify(title, text, result):
    if result:
        asyncio.create_task(toast_async(title, text, icon=iconTrue, app_id='Microsoft.WindowsTerminal_8wekyb3d8bbwe!App'))
    else:
        asyncio.create_task(toast_async(title, text, icon=iconFalse, app_id='Microsoft.WindowsTerminal_8wekyb3d8bbwe!App'))

async def toast_async(title, text, icon, app_id):
    loop = asyncio.get_running_loop()
    future = loop.run_in_executor(None, lambda: toast(title, text, icon=icon, app_id=app_id))
    await future

async def main_loop(buffSelenium, postgres):    
    global last_entry_checked
    logger.info('Start')
    while True:
        last_entry = await postgres.get_last_entry()
        
        if last_entry is None:
            logger.error('Failed to get last entry from PostgreSQL')
        elif last_entry == last_entry_checked:
            logger.info('No new entry')
        elif last_entry_checked is None:
            last_entry_checked = last_entry
            logger.info('First entry')
        else:
            last_entry_checked = last_entry
            
            logger.info('New entry {}'.format(last_entry_checked))
            
            url = last_entry_checked['buffurl']
            
            min_price = last_entry_checked['buff_min_price']
            
            bought = await buffSelenium.open_url(url, min_price)
            
            if bought:
                await notify('Buff2Steam', 'Item Bought!', True)
            else:
                await notify('Buff2Steam', 'Item Not Bought!', False)
            
        time.sleep(0.2)

async def main():
    try:
        while True:
            async with BuffSelenium(
                session=config['buff']['session'],
                remember_me=config['buff']['remember_me'],
            ) as buffSelenium, Postgres(
                uri=config['postgres']['uri'],
            ) as postgres:
                await main_loop(buffSelenium, postgres)
            
    except KeyboardInterrupt:
        exit('Bye~')


if __name__ == '__main__':
    asyncio.run(main())
