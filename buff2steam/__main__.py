import asyncio
import asyncpg_listen
from buff2steam.provider.buffSelenium import BuffSelenium
from buff2steam import logger, config
from urllib.parse import unquote
from win11toast import toast
from datetime import datetime

import json

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

async def handle_notifications(notification: asyncpg_listen.NotificationOrTimeout, buffSelenium: BuffSelenium) -> None:
    

    # check if the notification has a payload
    if not hasattr(notification, 'payload'):
        return 
    
    notification_payload = notification.payload
    notification_json = json.loads(notification_payload)
    notification_data = notification_json.get('data')
    
    url = notification_data['buffurl']
    min_price = notification_data['buff_min_price']
    b_o_ratio = notification_data['buff_b_o_ratio']
    updated_at = notification_data['updatedat']
    
    logger.info(f"Received notification for url: {url} with min price: {min_price} at {updated_at}")
    if b_o_ratio < 1.19:
        return
    
    bought = await buffSelenium.open_url(url, min_price)
            
    if bought:
        await notify('Buff2Steam', 'Item Bought!', True)
    else:
        await notify('Buff2Steam', 'Item Not Bought!', False)

async def listen_for_changes(buffSelenium: BuffSelenium):
    listener = asyncpg_listen.NotificationListener(
        asyncpg_listen.connect_func(
            user='postgres',
            password='benfica10',
            database='Buff_Steam',
            host='192.168.3.29'
        )
    )
    listener_task = asyncio.create_task(
        listener.run(
            {"buff2steam_table_changes": lambda notification: handle_notifications(notification, buffSelenium)},
            policy=asyncpg_listen.ListenPolicy.LAST,
            notification_timeout=30
        )
    )
    try:
        await listener_task
    finally:
        await listener.close()

async def main():
    try:
        async with BuffSelenium(
            session=config['buff']['session'],
            remember_me=config['buff']['remember_me'],
        ) as buffSelenium:
            await listen_for_changes(buffSelenium)
            
    except KeyboardInterrupt:
        exit('Bye~')


if __name__ == '__main__':
    asyncio.run(main())

