# !apt install mongodb
# !service mongodb start

# pip install lxml
from lxml import html
from datetime import datetime
import requests
from pymongo import MongoClient
import pandas as pd

pd.set_option('display.max_columns', 5)
pd.set_option('display.width', 1000)
pd.set_option('display.max_rows', 100)


# не удалось подружить datetime с русскими названиями месяцев в дате новостей,
# поэтому меняем их на порядковый номер
def convert_ru_month_to_digit(date_str):
    RU_MONTH_VALUES = {
        'января': 1,
        'февраля': 2,
        'марта': 3,
        'апреля': 4,
        'мая': 5,
        'июня': 6,
        'июля': 7,
        'августа': 8,
        'сентября': 9,
        'октября': 10,
        'ноября': 10,
        'декабря': 12,
    }
    for k, v in RU_MONTH_VALUES.items():
        date_str = date_str.replace(k, str(v))
    return date_str


# db_news.drop()
# db_client = MongoClient('localhost', 27017)
db_client = MongoClient()
db = db_client['news']
db_news = db.news

# *************************************** MAIL ***************************************
# url = 'https://news.mail.ru/'
header = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36'}
# response = requests.get(url, headers=header)
# if response.ok:
#
#     dom = html.fromstring(response.text)
#     # в первом блоке новостей ищем все ссылки, кроме ссылок с классом banner
#     news_links_list = list(set(dom.xpath('//div[@class="js-module"][1]//a[not(contains(@class,"banner"))]/@href')))
#
#     news_list = []
#     # по каждой ссылке выполяем requests.get
#     for news_page_url in news_links_list:
#         response = requests.get(news_page_url, headers=header)
#         if response.ok:
#             news_data = {}
#             dom = html.fromstring(response.text)
#             # заголовок h1 с классом "hdr__inner"
#             news_title = dom.xpath('//h1[@class ="hdr__inner"]/text()')[0].strip()
#             if news_title:  # если заголовка новости нет, вероятно это трансляция или что-то подобное, тогда пропускаем
#                 news_data['news_title'] = news_title
#                 # преобразуем время новости в datetime, для того чтобы дату из разных источников в базу записывать в одном формате
#                 # часовой пояс не стал учитывать
#                 news_datetime = datetime.strptime(dom.xpath('//span[@class ="note"]/span/@datetime')[0][:-6],
#                                                   '%Y-%m-%dT%H:%M:%S')
#                 # формируем дату в виде 05:20 08/12/21
#                 news_data['news_date'] = news_datetime.strftime('%H:%M %D')
#                 # формируется _id в виде 'mail_<id новости из url>_<utc timestamp новости>'
#                 news_data['_id'] = 'mail_' + news_page_url[:-1].split('/')[-1] + '_' + str(
#                     int(news_datetime.timestamp()))
#                 news_data['news_url'] = news_page_url
#                 news_data['source'] = url
#
#                 # запись в базу данных
#                 # db_news.update_one({'_id': news_data['_id']}, {"$set": news_data}, upsert=True)
#                 try:
#                     db_news.insert_one(news_data)
#                 except:
#                     pass

# *************************************** LENTA ***************************************

url = 'https://lenta.ru/'
response = requests.get(url, headers=header)
if response.ok:
    news_data = {}
    dom = html.fromstring(response.text)
    # в блоке section с классом, в названии котрого есть "top", находим потомка a у которого есть ребёнок time
    news_links_list = dom.xpath('//section[contains(@class, "top")]//a/time/..')
    # отталкиваясь от a, находим другие данные
    for news_item in news_links_list:
        # заголовок новости - текст в ссылке
        news_data['news_title'] = news_item.xpath('./text()')[0].replace('\xa0', ' ')
        # преобразуем время новости в datetime, для того чтобы дату из разных источников в базу записывать в одном формате
        news_datetime = datetime.strptime(convert_ru_month_to_digit(news_item.xpath('./time/@datetime')[0]),
                                          ' %H:%M, %d %m %Y')
        # формируем дату в виде 05:20 08/12/21
        news_data['news_date'] = news_datetime.strftime('%H:%M %D')
        # формируется _id в виде 'lenta_<id новости из url>_<utc timestamp новости>'
        # news_data['_id'] = 'lenta_' + news_page_url[:-1].split('/')[-1] + '_' + str(int(news_datetime.timestamp()))
        news_data['_id'] = 'lenta_' + '_' + str(int(news_datetime.timestamp()))
        # если ссылка относительная - делаем абсолютную, но ссылка может быть уже абсолютной
        href = news_item.xpath('./@href')[0]
        news_data['news_url'] = (url[:-1] + href) if href.find('https://') == -1 else href
        news_data['source'] = url

        try:
            db_news.insert_one(news_data)
        except:
            pass

df = pd.DataFrame(db_news.find())
print(df)

