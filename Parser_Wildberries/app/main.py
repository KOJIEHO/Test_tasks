from aiogram import F, Bot, Dispatcher
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, FSInputFile

import csv
import aiohttp
import asyncio
import aiofiles
import json
import gspread
from google.oauth2.service_account import Credentials

from config import TOKEN, SERVICE_ACCOUNT_JSON, GOOGLE_SHEETS_URL, PRICE_URL
import logging

SERVICE_ACCOUNT_FILE = SERVICE_ACCOUNT_JSON
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

logging.basicConfig(
    filename="error_log.log",
    filemode="a",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.ERROR,
    encoding="utf-8"
)

logger = logging.getLogger(__name__)

bot = Bot(TOKEN)
dp = Dispatcher()

class Form(StatesGroup):
    article = State()


async def get_price_rating(id):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(PRICE_URL + str(id)) as response:
                if response.status == 200:
                    data = await response.json()

                    price = data['data']['products'][0]['sizes'][0]['price']['product'] // 100
                    rating = data['data']['products'][0]['reviewRating']
                    feedbacks = data['data']['products'][0]['feedbacks']
                    return price, rating, feedbacks
    except Exception as exception:
        logger.error(f"Ошибка в функции <get_price_rating> для артикула {id}: {exception}")
            

async def get_data(id):
    try:
        vol_id = id[:3] if len(id) == 8 else id[:4]
        part_id = id[:len(vol_id) + 2]
        basket_id = 1

        while True:
            if basket_id == 100:
                return False
            try:
                if basket_id < 10:
                    url = f"https://basket-0{basket_id}.wbbasket.ru/vol{vol_id}/part{part_id}/{id}/info/ru/card.json" 
                else:
                    url = f"https://basket-{basket_id}.wbbasket.ru/vol{vol_id}/part{part_id}/{id}/info/ru/card.json"

                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as response:
                        if response.status == 200:
                            data = await response.json()
                            return data, basket_id

                basket_id += 1
            except Exception:
                basket_id += 1
    except Exception as exception:
        logger.error(f"Ошибка в функции <get_data> для артикула {id}: {exception}")


async def get_media(id, basket_id, photo_count):
    try:
        vol_id = id[:3] if len(id) == 8 else id[:4]
        part_id = id[:len(vol_id) + 2]

        if basket_id < 10:
            basket_id = f'0{basket_id}'

        media_list = []
        for photo_number in range(1, photo_count+1):
            media_list.append(f'https://basket-{basket_id}.wbbasket.ru/vol{vol_id}/part{part_id}/{id}/images/big/{photo_number}.webp')
        
        return media_list
    except Exception as exception:
        logger.error(f"Ошибка в функции <get_media> для артикула {id}: {exception}")


async def get_data_from_sheet():
    try:
        credentials = Credentials.from_service_account_info(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES
        )
        client = gspread.authorize(credentials)
        sheet = client.open_by_url(GOOGLE_SHEETS_URL)

        return sheet.sheet1
    except Exception as exception:
        logger.error(f"Ошибка в функции <get_data_from_sheet>: {exception}")


async def main():
    await dp.start_polling(bot)


@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await message.answer('Пришлите артикул товара')
    await state.set_state(Form.article)


@dp.message(Command('exp'))
async def start(message: Message, state: FSMContext):
    try:
        worksheet = await get_data_from_sheet() 
        data_from_sheet = worksheet.get_all_values()

        if not data_from_sheet:
            await message.answer("Таблица пуста или данные отсутствуют") 
        else:
            with open("data_from_sheet.csv", mode="w", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerows(data_from_sheet)

        await bot.send_document(message.chat.id, document=FSInputFile("data_from_sheet.csv"))
        await state.set_state(Form.article)
    except Exception as exception:
        logger.error(f"Ошибка при обработке сообщения {message.text}: {exception}")
        await message.answer("Произошла ошибка. Попробуйте позже.")


@dp.message(Command('logs'))
async def start(message: Message, state: FSMContext):
    try:
        await bot.send_document(message.chat.id, document=FSInputFile("error_log.log"))
        await state.set_state(Form.article)
    except Exception as exception:
        logger.error(f"Ошибка при обработке сообщения {message.text}: {exception}")
        await message.answer("Произошла ошибка. Попробуйте позже. Возможно еще не наблюдалось ошибок.")


@dp.message(F.text, Form.article)
async def state_change_form(message: Message, state: FSMContext):
    try:
        if message.text.isdigit():
            id = message.text
            data, basket_id = await get_data(id)
            
            if data != False:
                photo_count = data['media']['photo_count']
                media_list = await get_media(id, basket_id, photo_count)
                price, rating, feedbacks = await get_price_rating(id)
                
                new_data = [[
                    id,                                              # Артикул             
                    data['imt_name'],                                # Название
                    f"{data['subj_root_name']}/{data['subj_name']}", # Категория
                    str(price),                                      # Цена
                    str(media_list),                                 # Картинки
                    json.dumps(data['options']),                     # Характеристики
                    str(data['description']),                        # Описание
                    str(rating),                                     # Оценка
                    str(feedbacks)                                   # Кол-во отзывов
                ]] 

                worksheet =  await get_data_from_sheet() 
                first_column = worksheet.col_values(1)
                if id in first_column:
                    number_row = first_column.index(id) + 1   
                    worksheet.update(f"A{number_row}", new_data)
                    await message.answer("Вы уже искали товар по такому артикулу. Данные в таблице были обновлены")   
                else:
                    next_row = len(first_column) + 1
                    worksheet.update(f"A{next_row}", new_data)
                    await message.answer("Данные о товаре успешно загружены в таблицу!") 

                async with aiohttp.ClientSession() as session:
                    url = str(media_list[0])
                    async with session.get(url) as resp:
                        if resp.status == 200:
                            f = await aiofiles.open('tmp.img', mode='wb')
                            await f.write(await resp.read())
                            await f.close()

                mes = f"Название: {data['imt_name']}\nКатегория: {data['subj_root_name']}/{data['subj_name']}\nЦена: {price} рублей\nРейтинг: {rating}\nКол-во отзывов: {feedbacks}\n"
                for option in data['options']:
                    mes += f"{option['name']}: {option['value']}\n"

                await bot.send_photo(message.chat.id, photo=FSInputFile('tmp.img'))
                if len(mes) < 4000:
                    await message.answer(mes)
                else:
                    await message.answer("Слишком длинный список характеристик. Подробнее можно посмотреть в гугл таблице")

                if len(data['description']) < 4000:
                    await message.answer(data['description'])
                else:
                    await message.answer("Слишком длинное описание. Подробнее можно посмотреть в гугл таблице")
            else:
                await message.answer("Не удалось найти карточку товара по указанному артикулу")
        else:
            await message.answer("Артикул должен состоять только из цифр!")

    except Exception as exception:
        logger.error(f"Ошибка при обработке сообщения {message.text}: {exception}")
        await message.answer("Произошла ошибка. Попробуйте позже.")


if __name__ == '__main__':
    # asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
