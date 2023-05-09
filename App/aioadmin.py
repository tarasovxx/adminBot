from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.types import *
from aiogram.filters import Text, Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from functions import *
from filters import IsAdmin

# Считываем список админов
with open('Meta/admins.txt') as file:
    admin_list: list[int] = []
    for admin in file.readlines():
        admin_list.append(int(admin))

# список с этажами
floors = [str(i) for i in range(1, 25)]

# корпус и этаж, с которым работает в данный момент администратор
currentFF = {}
for admin in admin_list:
    currentFF[admin]={'corpus':'','flr':''}


# Считываем токен из файла
with open('Meta/token.txt') as file:
    BOT_TOKEN: str = file.readline()

# Создаем объекты бота с proxy и диспетчера
session = AiohttpSession(proxy="http://proxy.server:3128")
bot: Bot = Bot(token=BOT_TOKEN, session=session)
dp: Dispatcher = Dispatcher()


# Этот хэндлер будет срабатывать на команду "/start"
# и отправлять в чат клавиатуру
@dp.message(Command(commands=['start']), IsAdmin(admin_list))
async def process_start_command(message: Message):
    # Обнуляем выбранный корпус и этаж

    currentFF[message.from_user.id]['corpus'] = ''
    currentFF[message.from_user.id]['flr'] = ''

    # Создаем объекты кнопок
    btn1: KeyboardButton = KeyboardButton(text='Корпус 1')
    btn2: KeyboardButton = KeyboardButton(text='Корпус 2')
    btn3: KeyboardButton = KeyboardButton(text='Корпус 3')
    btn4: KeyboardButton = KeyboardButton(text='Кошка')
    # Создаем объект клавиатуры, добавляя в него кнопки
    keyboard: ReplyKeyboardMarkup = ReplyKeyboardMarkup(keyboard=[[btn1, btn2, btn3, btn4]],
                                                        resize_keyboard=True, one_time_keyboard=True)
    await message.answer(text='Привет, я админ бот магазина Food Upstairs! Выбери корпус', reply_markup=keyboard)


# Этот хэндлер будет срабатывать на имя корпуса
# Возвращать таблицу со всеми товарами корпуса в чат и предлагать выбор этажа
@dp.message(Text(text=['Корпус 1', 'Корпус 2', 'Корпус 3', 'Кошка']), IsAdmin(admin_list))
async def list_and_floors(message: Message):
    if message.text in ['Корпус 1', 'Корпус 2', 'Корпус 3', 'Кошка']:
        currentFF[message.from_user.id]['corpus'] = message.text.replace(' ', '_')

    corpus = currentFF[message.from_user.id]['corpus']
    # генерация списка продуктов
    products = [5]
    products += get_all_products(corpus)
    keyboard = create_inline_kb(products)

    # генератор кнопок с этажами и кнопками возврата, добавления этажа, удаления этажа
    kb_builder: ReplyKeyboardBuilder = ReplyKeyboardBuilder()
    level_btns = bd_levels_reader(corpus)
    level_btns += ['⏎']
    level_btns = [KeyboardButton(text=x) for x in level_btns]
    kb_builder.row(*level_btns)

    await message.answer(text='Список доступных товаров в корпусе', reply_markup=keyboard)
    await message.answer(text='''Выбери этаж, чтобы посмотреть список товаров, доступных на нем.\n/addfloor <этаж>\
    добавит новый этаж.\n/removefloor <этаж>    удалит этаж.''',
                         reply_markup=kb_builder.as_markup(resize_keyboard=True, one_time_keyboard=True))


@dp.message(Text(text=['⏎']), IsAdmin(admin_list))
async def back(message: Message):

    currentFF[message.from_user.id]['corpus'] = ''
    currentFF[message.from_user.id]['flr'] = ''

    await process_start_command(message)


@dp.message(Text(text=floors), IsAdmin(admin_list))
async def back(message: Message):
    corpus = currentFF[message.from_user.id]['corpus']
    if corpus == '':
        await message.answer(text='Сначала выберите корпус!')
        await process_start_command(message)
    else:
        products = [5]
        products += get_all_products(corpus + f'_{message.text}', flag=True)
        keyboard = create_inline_kb(products)
        currentFF[message.from_user.id]['flr'] = message.text

        await message.answer(text=f'''Список доступных товаров в {corpus} на {message.text} этаже.
Чтобы добавить имеющийся товар, используйте команду\n/Ai <id> <Сount>\nСount может выглядеть как 4, -4 что добавит и отнимет 
соответственно.\n
*Если хотите добавить товар, которого еще нет в корпусе, указывайте имя товара и url картинки: /Ai <name> <price> <Count> <img>
**Чтобы выйти на линию используйте команду /on, чтобы сойти /off
''', reply_markup=keyboard)


@dp.message(Command(commands=['Ai']), IsAdmin(admin_list))
async def no_comments(message: Message):
    corpus = currentFF[message.from_user.id]['corpus']
    flr = currentFF[message.from_user.id]['flr']

    if corpus == '' or flr == '':
        await message.answer(text='Сначала выберите корпус и этаж!')
        await process_start_command(message)
    else:
        try:
            comm = message.text.split()[1:]

            if not comm[0].isdigit():
                itemname = ' '.join(comm[:len(comm) - 2])
                count = int(comm[-2])
                price = int(comm[-3])
                url = comm[-1]
                print(comm)
                r = edit_item(frame=corpus, floor=flr, name_or_id=itemname, price=price, delta=count, url=url)
            else:
                count = int(comm[1])
                ident = comm[0]
                r = edit_item(frame=corpus, floor=flr, name_or_id=ident, delta=count)

            await message.answer(text=r)
        except AttributeError:
            await message.answer(text='URL должен быть одного из форматов:  .jpg, .png, .jpeg ')
        except:
            await message.answer(text='Something went wrong (: Прочитай внимательно описание... ')


@dp.message(Command(commands=['on','off']), IsAdmin(admin_list))
async def get_on_the_line(message: Message):
    corpus = currentFF[message.from_user.id]['corpus']
    flr = currentFF[message.from_user.id]['flr']
    if corpus == '' or flr == '':
        await message.answer(text='Сначала выберите корпус и этаж!')
        await process_start_command(message)
    else:
        try:
            change_off_on(corpus,flr,message.text[1:])
            await message.answer(text=f'Ваш этаж теперь is {message.text[1:]}')
        except:
            await message.answer(text=f'Пока в корпусе нет ни одного товара нельзя выйти на линию(')







@dp.message(Command(commands=['removefloor']), IsAdmin(admin_list))
async def rem_floor(message: Message):
    corpus = currentFF[message.from_user.id]['corpus']
    if corpus == '':
        await message.answer(text='Сначала выберите корпус!')
        await process_start_command(message)
    else:
        try:
            comm = [corpus] + message.text.split()[1:]
            remove_floor(comm[0], comm[1])
            await message.answer(text=f'Успешно удален {comm[1]} этаж!')
            await list_and_floors(message)
        except IndexError:
           await message.answer(text='Укажите этаж!... (напр. /removefloor 2)')
        except ValueError:
           await message.answer(text='Этаж должен быть числом :D (напр. /removefloor 2)')


@dp.message(Command(commands=['addfloor']), IsAdmin(admin_list))
async def ad_floor(message: Message):
    corpus = currentFF[message.from_user.id]['corpus']
    if corpus == '':
        await message.answer(text='Сначала выберите корпус!')
        await process_start_command(message)
    else:
        try:
            comm = [corpus] + message.text.split()[1:]
            comm[1] = int(comm[1])
            comm[1] = str(comm[1])
            await message.answer(text=add_floor(comm[0], comm[1]))
            await list_and_floors(message)
        except IndexError:
            await message.answer(text='Укажите этаж!... (напр. /addfloor 24)')
        except ValueError:
            await message.answer(text='Этаж должен быть числом :D (напр. /addfloor 24)')


# Если сообщение не подходит...
@dp.message(IsAdmin(admin_list))
async def no_comments(message: Message):
    await message.answer(text='Ничего не понял...')


# Неугодным прочь
@dp.message()
async def get_out_of_here(message: Message):
    await message.answer(text='Вы не зарегистрированы! Напишите админу https://t.me/Alexmansura')


if __name__ == '__main__':
    dp.run_polling(bot)
