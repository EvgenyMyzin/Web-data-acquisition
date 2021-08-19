"""
1) Написать программу, которая собирает входящие письма из своего или тестового почтового ящика
и сложить данные о письмах в базу данных (от кого, дата отправки, тема письма, текст письма полный)
Логин тестового ящика: study.ai_172@mail.ru
Пароль тестового ящика: NextPassword172!!!
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from time import sleep
import json
from pymongo import MongoClient

def get_msg_data(url):
    """Парсит информацию из сообщения"""
    try:
        date = driver.find_element_by_class_name('letter__date').text
        subject = driver.find_element_by_tag_name('h2').text
        sender_name = driver.find_element_by_class_name('letter-contact').text
        sender_email = driver.find_element_by_class_name('letter-contact').get_attribute('title')
        message_text = driver.find_element_by_class_name('letter__body').text
        data = {'date': date,
                'subject': subject,
                'sender_name': sender_name,
                'sender_email': sender_email,
                'message_text': message_text}
        return data
    except:
        return get_msg_data(url)

# ---Инициализация БД---
client = MongoClient('localhost', 27017)
db = client['mail_ru']
mail_messages = db.messages

# ---Инициализация веб драйвера---
options = Options()
options.add_argument("start-maximized")
driver = webdriver.Chrome(executable_path='./chromedriver', options=options)

# ---Авторизация---
print('Авторизация...')
driver.get('https://mail.ru/')
login = driver.find_element_by_name('login')
login.send_keys('study.ai_172@mail.ru')
passwd_button = driver.find_element_by_xpath("//button[contains(text(), 'Ввести пароль')]")
passwd_button.click()
sleep(.2)
password = driver.find_element_by_name('password')
password.send_keys('NextPassword172!!!')
enter_button = driver.find_element_by_xpath("//button[contains(@class, 'second-button')]")
enter_button.click()

# 1-я прокрутка для получения первых новых сообщений
sleep(5)
print('\rПрокрутка и получение ссылок на сообщения...', end='')
messages_block = driver.find_element_by_class_name('dataset__items')
messages = messages_block.find_elements_by_tag_name('a')

msg_links = []  # Все ссылки
for msg in messages:
    msg_links.append(msg.get_attribute('href'))
actions = ActionChains(driver)
actions.move_to_element(messages[-1])
actions.perform()

last_new_msg_links = []  # Последние ссылки из новых загруженных (не самые новые), необходимы для сравнения при скролле страницы
messages_block = driver.find_element_by_class_name('dataset__items')
messages = messages_block.find_elements_by_tag_name('a')
for msg in messages:
    last_new_msg_links.append(msg.get_attribute('href'))

msg_links.extend(last_new_msg_links)
new_msg_links = last_new_msg_links[:]  # Самые новые из новых загруженных ссылок, необходимы для сравнения при скролле страницы

# Остальные прокрутки выполняем циклом
while True:
    print(f'\rПрокрутка и получение ссылок на сообщения, получено {len(set(msg_links))} шт...' + ' ' * 100, end='')
    last_new_msg_links = new_msg_links[:]  # последние полученные сообщения стают предпоследними полученными
    new_msg_links = []  # Самые новые из новых загруженных ссылок, необходимы для сравнения при скролле страницы
    #  Прокрутим вниз
    actions = ActionChains(driver)
    actions.move_to_element(messages[-1])
    actions.perform()
    # ---Блок с имеющимеся сообщениями---
    messages_block = driver.find_element_by_class_name('dataset__items')
    # ---Объекты ссылок на сообщения, в том числе и реклама---
    messages = messages_block.find_elements_by_tag_name('a')
    for msg in messages:
        new_msg_links.append(msg.get_attribute('href'))
    # Добавляем полученные ссылки с предпоследней прокрутки
    msg_links.extend(last_new_msg_links)
    # Если новых объектов сообщений нет - выходим из цикла
    if set(last_new_msg_links) == set(new_msg_links):
        break

# Оставляем уникальные ссылки на сообщения
total_msg_links = []
print(f'\nОчистка от рекламы...')
for msg in list(set(msg_links)):
    try:  # Может возникнуть ошибка при итерации по NoneType
        if 'e.mail' in msg:  # Исключаем рекламу
            total_msg_links.append(msg)
    except:
        pass

# Возвращаем ссылки в эту переменную, мне с ней приятней работать)
msg_links = total_msg_links[:]
print(f'Очищено. Итого: {len(msg_links)} сообщений')

# Список объектов которые получим в итоге
messages_data = []
cnt = 0  # Cчетчик
for link in msg_links:
    print(f"\rОбработка письма {cnt + 1} из {len(msg_links)}", end='')
    driver.get(link)
    msg_data = get_msg_data(link)
    messages_data.append(msg_data)
    cnt += 1

# Сохраним в качестве брейкпоинта, выполняется то не быстро
with open('result.json', 'w') as file:
    file.write(json.dumps(messages_data))
print('Кладем в БД...')
# Положим в бд
mail_messages.insert_many(messages_data)
print('Готово')