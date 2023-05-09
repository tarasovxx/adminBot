import sqlite3
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


# Функция для генерации инлайн-клавиатур "на лету"
def create_inline_kb(ls) -> InlineKeyboardMarkup:
    width = ls[0]
    args = ls[1:]
    # Инициализируем билдер
    kb_builder: InlineKeyboardBuilder = InlineKeyboardBuilder()
    # Инициализируем список для кнопок
    buttons: list[InlineKeyboardButton] = []

    # Заполняем список кнопками из аргументов args и kwargs
    if args:
        for button in args:
            buttons.append(InlineKeyboardButton(
                text=button,
                callback_data=button))

    # Распаковываем список с кнопками в билдер методом row c параметром width
    kb_builder.row(*buttons, width=width)

    # Возвращаем объект инлайн-клавиатуры
    return kb_builder.as_markup()


# функция, которая возвращает таблицу всех продуктов, доступных в корпусе(с англ. frame)
def get_all_products(frame,flag = False):
    # Подключаемся к БД и читаем лист выбранного корпуса
    conn = sqlite3.connect('DataBase.bd')
    cur = conn.cursor()

    cur.execute(f"""CREATE TABLE IF NOT EXISTS {frame}(
    id INT PRIMARY KEY,
    product TEXT,
    price INTEGER,
    quantity INT,
    photo TEXT,
    floors TEXT,
    busy TEXT);""")
    cur.execute(f"SELECT * FROM {frame};")

    # Создаем таблицу, которую выведем в чат
    allproducts = cur.fetchall()
    result = ['ID', 'Продукт', 'Цена', 'Количество', 'На этажах']
    if not flag:
        for id, prod, price, quant, photo, floors, busy  in allproducts:
            result += [id, prod, price, quant, floors]
    else:
        for id, prod, price, quant, floors  in allproducts:
            result += [id, prod, price, quant, floors]
    conn.commit()
    conn.close()
    return result


# Добавление/изменение товара на этаже
def edit_item(frame, floor, name_or_id, delta, url="", price=-1):
    conn = sqlite3.connect('DataBase.bd')
    cur = conn.cursor()

    cur.execute(f"SELECT product from {frame}")
    prod_in_corp = cur.fetchall()

    cur.execute(f"SELECT id from {frame}")
    id_in_corp = cur.fetchall()

    cur.execute(f"SELECT id from {frame}_{floor}")
    id_in_floor = cur.fetchall()

    compare_prod = (name_or_id,)

    # Если указан ID
    if name_or_id.isdigit():
        compare_id = (int(name_or_id),)

        # Если указан ID и его нет в корпусе, то выдаем ошибку
        if compare_id not in id_in_corp:
            return 'Неизвестный ID'

        # Обновляем инфу о количестве в корпусе
        cur.execute(f"UPDATE {frame} SET quantity = quantity+{delta} WHERE id = {name_or_id}")

        # Если ID нет на этаже
        if compare_id not in id_in_floor:
            # Добавляем этаж в список этажей в таблице корпуса
            cur.execute(f"SELECT floors FROM {frame} WHERE id={name_or_id}")
            previusFLOORS = str(cur.fetchall()[0][0])
            spisfloors = str(previusFLOORS + ',' + str(floor))

            cur.execute(f"UPDATE {frame} SET floors = '{spisfloors}' WHERE id = {name_or_id}")

            # Получаем название продукта и его стоимость из таблицы корпуса
            cur.execute(f"SELECT product from {frame} WHERE id = {name_or_id}")
            name_of_prod = cur.fetchall()[0][0]
            cur.execute(f"SELECT price from {frame} WHERE id = {name_or_id}")
            price_of_prod = cur.fetchall()[0][0]

            # Вставляем в таблицу этажа данные
            insert_to_floor = [name_or_id, name_of_prod, price_of_prod, delta, floor]
            cur.execute(f"INSERT INTO {frame}_{floor} VALUES(?, ?, ?, ?, ?);", insert_to_floor)


        else:  # Если есть, то обновляем
            cur.execute(f"UPDATE {frame}_{floor} SET quantity = quantity+{delta} WHERE id = {name_or_id}")

    else:  # Если указано имя
        if compare_prod in prod_in_corp:
            return 'Если товар уже есть в корпусе, указывай ID.'

        # Присваеваем продукту новый ID
        cur.execute(f"SELECT id from {frame}")
        last_id = len(cur.fetchall())

        if url[-3:]!='jpg' and url[-3:]!='png' and url[-4:]!='jpeg':
            raise AttributeError

        if last_id==0:
            busy='0' + ',0'*25
        else:
            busy=" "

        new_item = [last_id + 1, price, name_or_id, delta, url, floor, busy]
        new_item_to_floor = [last_id +1, name_or_id, price, delta, floor]
        cur.execute(f"INSERT INTO {frame}_{floor} VALUES(?, ?, ?, ?, ?);", new_item_to_floor)
        cur.execute(f"INSERT INTO {frame} VALUES(?, ?, ?, ?, ?, ?, ?);", new_item)

    conn.commit()
    conn.close()
    return 'Успешно!'


def change_off_on(frame,flr,offon):
    conn = sqlite3.connect('DataBase.bd')
    cur = conn.cursor()
    cur.execute(f"SELECT busy from {frame} WHERE id = 1")
    busy = cur.fetchone()
    busy = busy[0]
    busy = busy.split(',')
    if offon == "off":

        busy[int(flr)] = '0'
        busy = ','.join(busy)
        cur.execute(f"UPDATE {frame} SET busy = {busy} WHERE id = 1")
    else:
        busy[int(flr)] = '1'
        busy = ','.join(busy)
        cur.execute(f"UPDATE {frame} SET busy = '{busy}' WHERE id = 1")
    print(busy)
    conn.close()




# Функция, добавляющая этаж в корпусе
def add_floor(frame, floor):
    conn = sqlite3.connect('DataBase.bd')
    cur = conn.cursor()

    cur.execute(f"""CREATE TABLE IF NOT EXISTS {frame}_{floor}(
        id INT PRIMARY KEY,
        product TEXT,
        price INT,
        quantity INT,
        floor INT);""")

    conn.commit()
    conn.close()

    return f"Успешно добавлен {floor} этаж в {frame}"


# Функция, удаляющая этаж в корпусе
def remove_floor(frame, floor):
    conn = sqlite3.connect('DataBase.bd')
    cur = conn.cursor()
    cur.execute(f"SELECT * from {frame}_{floor}")
    allDATA = cur.fetchall()
    for id, name, price, quantity, flooor in allDATA:
        cur.execute(f"SELECT floors FROM {frame} WHERE id={id}")
        spisfloors = cur.fetchall()[0][0]

        if str(floor) + ',' in spisfloors:
            spisfloors1 = spisfloors.replace(f"{floor},", "")
            cur.execute(f"UPDATE {frame} SET quantity = quantity-{quantity} WHERE id = {id}")
            cur.execute(f"UPDATE {frame} SET floors = '{spisfloors1}' WHERE id = {id}")
        elif "," + str(floor) in spisfloors:
            spisfloors1 = spisfloors.replace(f",{floor}", "")
            cur.execute(f"UPDATE {frame} SET quantity = quantity-{quantity} WHERE id = {id}")
            cur.execute(f"UPDATE {frame} SET floors = '{spisfloors1}' WHERE id = {id}")
        elif str(floor) in spisfloors:
            spisfloors1 = spisfloors.replace(f"{floor}", "")
            cur.execute(f"UPDATE {frame} SET quantity = quantity-{quantity} WHERE id = {id}")
            cur.execute(f"UPDATE {frame} SET floors = '{spisfloors1}' WHERE id = {id}")
        if spisfloors1 == '':
            cur.execute(f"""DELETE from {frame} where id = {id}""")

    cur.execute(f"""DROP TABLE IF EXISTS {frame}_{floor};""")
    conn.commit()
    conn.close()


# Функция, считывающая этажи корпуса
def bd_levels_reader(frame):
    conn = sqlite3.connect('DataBase.bd')
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    result = [x[0].split('_')[-1] for x in cur.fetchall() if frame + '_' in x[0]]
    conn.close()
    return result
