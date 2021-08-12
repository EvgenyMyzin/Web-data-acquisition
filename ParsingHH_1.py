from bs4 import BeautifulSoup as bs
import requests
from requests.exceptions import HTTPError
import pandas as pd
import json
import hashlib
import pymongo
from pymongo import MongoClient

class ParsingHH:
    """Класс для парсинга вакансий с  HeadHunter"""
    def __init__(self):
        self.main_link = 'https://hh.ru' # Ссылка на HeadHunter
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) \
                        Chrome/91.0.4472.135 YaBrowser/21.6.3.757 Yowser/2.5 Safari/537.36'} # Укажем user-agent (тип браузера)
        self.soup = None #Получим структуру данных Beautiful Soup
        self.next_pager = None # Ссылка на новую страницу
        self.vacancies = [] # Список всех вакансий
        self.client = MongoClient('localhost', 27017) # создаем клиента для подключения к серверу
        self.database = 'database' # Название по умолчанию базы
        self.collection = 'collection' # Название по умолчанию коллекции
        self.db = None # укозатель на базу данных
        self.collections = None # укозатель на имя коллекции

    def insert_one_base(self, doc):
        """Метод производит удаление одного документа из базы по ID"""
        try:
            self.db = self.client[self.database]
            self.collections = self.db[self.collection]
            self.collections.insert_one(doc)
        except:
            return f'Other error occurred: {pymongo.errors}'
    
    def delete_one_base(self, id = ' '):
        """Метод производит удаление одного документа из базы по ID"""
        try:
            self.db = self.client[self.database]
            self.collections = self.db[self.collection]
            self.collections.delete_one({ '_id': { '$eq': id}})
        except:
            return f'Other error occurred: {pymongo.errors}'

    def delete_base(self):
        """Метод производит полнeю очистку базы"""
        try:
            self.db = self.client[self.database]
            self.collections = self.db[self.collection]
            self.collections.delete_many({})
        except:
            return f'Other error occurred: {pymongo.errors}'

    def get_pay(self, number, sign = '>'):
        """Метод производит поиск и возвращает вакансии с заработной платой больше ‘>’ (меньше ‘<’) введённой суммы 'number' """
        vacancy = []
        try:
            self.db = self.client[self.database]
            self.collections = self.db[self.collection]
            if sign == '>':
                # collections_vacancy = self.collections.find({'pay_max': { '$gt': number }}, {'_id': 0})
                collections_vacancy = self.collections.find({'$or': [{'pay_max': {'$gte': number}}, {'pay_min': {'$gte': number}}]}, {'_id': 0})

            elif sign == '<':
                collections_vacancy = self.collections.find({'pay_min': { '$lt': number }}, {'_id': 0})
            else: 
                return f'Enter ‘>’ or ‘<’'
            for base_vacancy in collections_vacancy:
                vacancy.append(base_vacancy)
        except:
            return f'Other error occurred: {pymongo.errors}'
        
        return vacancy

    def set_to_base(self):
        """Метод заполнения базы, заполняет только новыми значениями"""
        number_of_new_vacancy = 0 
        number_of_closed_vacancy = 0 
        try:
            self.db = self.client[self.database]
            self.collections = self.db[self.collection]
            #Добавляем новые вакансии
            for vacancy in self.vacancies:
                new_vacancy = self.collections.find({ '_id': { '$eq': vacancy['_id']}})
                try:
                    new_vacancy.next()
                except:
                    self.insert_one_base(vacancy)
                    number_of_new_vacancy += 1
            #Удаляем  закрытые вакансии
            df = self.get_to_pandas()
            for vacancy in self.collections.find({}):
                if len(df[df['_id'] == vacancy['_id']]) == 0:    
                    self.delete_one_base(vacancy['_id'])
                    number_of_closed_vacancy += 1
        except:
            return f'Other error occurred: {pymongo.errors}'
        return f'\nДобавлено  новый вакансий {number_of_new_vacancy}\nУдалено закрытых вакансий {number_of_closed_vacancy}\n'

    # def set_client_Mongo(self, database = 'database', collection = 'collection'):
    #     """"Метод подключения к базе данных"""
    #     self.database = database
    #     self.collection = collection
    #     self.db = self.client[database]
    #     self.collections = self.db[collection]

    def get_vacancy_info(self, vacancy):
        """Метод заполнения данными о вакансии"""
        vacancy_info = dict() # Словарь, описание вакансии

        vacancy_info['name'] = '' # Имя 
        vacancy_info['link'] = '' # Ссылка на вакансию
        vacancy_info['pay_min'] = 0 # Минимальная заработная плата 
        vacancy_info['pay_max'] = 0 # Максимальная заработная плата
        vacancy_info['pay_valuta'] = '' # Валюта заработной платы
        vacancy_info['employer'] = '' # Работодатель
        vacancy_info['employer_link'] = '' # Ссылка на работодателя  
        vacancy_info['address'] = '' # Адрес работодателя

        # Заполнение словаря
        vacancy_title = vacancy.find('a',{'data-qa': 'vacancy-serp__vacancy-title'})
        vacancy_info['name'] = vacancy_title.getText().replace('\xa0', ' ')
        vacancy_info['link'] = vacancy_title['href']

        try:
            vacancy_pay = vacancy.find('span', {'data-qa': 'vacancy-serp__vacancy-compensation'}).getText().split()
            if vacancy_pay[0] == 'от':
                vacancy_info['pay_min'] = int(f'{vacancy_pay[1]}{vacancy_pay[2]}')
            elif vacancy_pay[0] == 'до':
                vacancy_info['pay_max'] = int(f'{vacancy_pay[1]}{vacancy_pay[2]}')
            else:
                vacancy_info['pay_min'] = int(f'{vacancy_pay[0]}{vacancy_pay[1]}')
                vacancy_info['pay_max'] = int(f'{vacancy_pay[3]}{vacancy_pay[4]}')
            vacancy_info['pay_valuta'] = vacancy_pay[-1]
        except:
            pass

        try:
            vacancy_employer = vacancy.find('a', {'data-qa': 'vacancy-serp__vacancy-employer'})
            vacancy_info['employer'] = vacancy_employer.getText().replace('\xa0', ' ')
            vacancy_info['employer_link'] = f"{self.main_link}{vacancy_employer['href']}"
        except:
            pass
        
        vacancy_info['address'] = vacancy.find('span', {'data-qa': 'vacancy-serp__vacancy-address'}).getText().replace('\xa0', ' ')
        vacancy_info['_id'] = hashlib.sha1(str(vacancy_info).encode()).hexdigest()

        return vacancy_info

    def vacancy_list(self):
        """Метод перебора вакассий на странице"""
        vacancy_listing = self.soup.find_all('div', {'class': 'vacancy-serp-item'})
        for vacancy in vacancy_listing:
            vacancy = self.get_vacancy_info(vacancy)
            self.vacancies.append(vacancy)

    def get_request_page(self, params= '/search/vacancy?L_save_area=true&clusters=true&enable_snippets=true&items_on_page=20&text=',search = ''):
        """"Метод запроса к стронице сервера НН"""
        link =  f'{self.main_link}{params}{search}'
        try:
            html = requests.get(link, headers=self.headers)
            # если ответ успешен, исключения задействованы не будут
            html.raise_for_status()
        except HTTPError as http_err:
            return f'HTTP error occurred: {http_err}'
        except Exception as err:
            return f'Other error occurred: {err}'  
        else:
            self.soup = bs(html.text, 'html.parser')
            self.next_pager = self.soup.find('a', {'data-qa': 'pager-next'})
            return 'OK'


    def get_request_hh(self, search = 'Data+Scientist'):
        """"Метод опроса всех строниц сервера НН"""
        flag = 'OK'
        flag = self.get_request_page(search = search)
        if flag != 'OK': return flag
        self.vacancy_list()
        while self.next_pager:
            flag = self.get_request_page(params = self.next_pager['href'])
            if flag != 'OK': return flag
            self.vacancy_list()
        flag = self.set_to_base()
        return  flag

    def get_to_pandas(self):
        """"Метод выдающий результат опроса в формате pandas"""
        return pd.DataFrame(self.vacancies)

    def save_to_json(self):
        """"Метод сохраняющий  результат опроса в файл json"""
        with open("vacancy_list.json", "w") as write_file:
            json.dump(self.vacancies, write_file)

    def save_to_csv(self):
        """"Метод сохраняющий  результат опроса в файл csv"""
        self.get_to_pandas().to_csv('vacancy_list.csv')
