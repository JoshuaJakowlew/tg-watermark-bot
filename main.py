import logging
from aiogram import Bot, Dispatcher, executor, types
from os.path import exists
import random
import json
from PIL import Image

API_TOKEN = None
WATERMARK = './watermark.png'
TEMP_IMAGE = './temp.png'

WEBHOOK_HOST = 'https://d16e-95-29-158-65.ngrok.io'
WEBHOOK_PATH = '/'
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

WEBAPP_HOST = 'localhost'  # or ip
WEBAPP_PORT = 3001

with open('./secrets.json') as f:
    API_TOKEN = json.load(f)['token']

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')
    
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

async def download_image(message: types.Message, file: str):
    await message.photo[-1].download(destination_file=file)
    return file

async def show_watermark(message: types.Message):
    if exists(WATERMARK):
        await message.reply_photo(caption='Your watermark', photo=types.InputFile(WATERMARK))
    else:
        await message.reply(text='Watermark is not set.')

def draw_watermark(image: Image.Image, watermark: Image.Image):
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    if watermark.mode != 'RGBA':
        watermark = watermark.convert('RGBA')

    angle = random.randint(-60, 60)
    watermark = watermark.rotate(angle=angle, expand=True)
    im_w, im_h = image.size
    w_w, w_h = watermark.size
    pos_x = random.randint(0, im_w - w_w - 1)
    pos_y = random.randint(0, im_h - w_h - 1)

    layer = Image.new('RGBA', image.size, (0, 0, 0, 0))
    layer.paste(watermark, (pos_x, pos_y))

    layer2 = layer.copy()
    layer2.putalpha(128)
    layer.paste(layer2, layer)

    image.alpha_composite(layer)
    return image

@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    await message.reply("Hi!\nI'm WatermarkBot!\nMy commands:\n/watermark - set watermark image")

@dp.message_handler(commands=['watermark'], commands_ignore_caption=False, content_types=['text', 'document'])
async def watermark(message: types.Message):
    if message.content_type == 'text':
        await show_watermark(message)
    else:
        await message.document.download(destination_file=WATERMARK)
        await message.reply(text='Watermark saved')

@dp.message_handler(content_types='photo')
async def apply_watermark(message: types.Message):
    if exists(WATERMARK):
        img_path = await download_image(message, TEMP_IMAGE)
        img = Image.open(img_path)
        watermark = Image.open(WATERMARK)
        result = draw_watermark(img, watermark)
        result.save(TEMP_IMAGE)
        await message.reply_photo(caption='Watermark applied', photo=types.InputFile(TEMP_IMAGE))
    else:
        await message.reply(text="Set watermark first")

async def on_startup(dp):
    await bot.set_webhook(WEBHOOK_URL)

if __name__ == '__main__':
    #executor.start_polling(dp, skip_updates=True)
    executor.start_webhook(dp, WEBHOOK_PATH, on_startup=on_startup, 
    host=WEBAPP_HOST,
    port=WEBAPP_PORT)