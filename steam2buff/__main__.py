import asyncio
from datetime import datetime

from steam2buff.provider.steamSelenium import SteamSelenium
from steam2buff.provider.postgres import Postgres
from steam2buff import logger, config

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

async def main_loop(steamSelenium, postgres):    
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
        
            if last_entry_checked['currency'] == 'SOLD':
                continue
            
            url = last_entry_checked['link']
            listing_id = last_entry_checked['id']
            
            bought = await steamSelenium.open_url(url, listing_id)
            
            if bought:
                await notify('Steam2Buff', 'Item Bought!', True)
            else:
                await notify('Steam2Buff', 'Item Not Bought!', False)
            
        time.sleep(0.2)

async def main():
    try:
        while True:
            async with SteamSelenium(
                sessionid=config['steam']['sessionid'],
                steamLoginSecure=config['steam']['steamLoginSecure'],
            ) as steamSelenium, Postgres(
                uri=config['postgres']['uri'],
            ) as postgres:
                await main_loop(steamSelenium, postgres)
            
    except KeyboardInterrupt:
        exit('Bye~')


if __name__ == '__main__':
    asyncio.run(main())
