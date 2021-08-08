#Вариант 1
#Необходимо собрать информацию о вакансиях на вводимую должность (используем input или через аргументы получаем должность) с сайтов HH(обязательно) и/или
#Superjob(по желанию). Приложение должно анализировать несколько страниц сайта (также вводим через input или аргументы). Получившийся список должен содержать
#в себе минимум:
#Наименование вакансии.
#Предлагаемую зарплату (отдельно минимальную и максимальную).
#Ссылку на саму вакансию.
#Сайт, откуда собрана вакансия.
#По желанию можно добавить ещё параметры вакансии (например, работодателя и расположение). Структура должна быть одинаковая для вакансий с обоих сайтов.
#Общий результат можно вывести с помощью dataFrame через pandas. Сохраните в json либо csv.

from bs4 import BeautifulSoup as bs
import requests
import pandas as pd

def vacancy_info_dict(vacancy) -> dict:
    """
    Функция заполнения данными о вакансии
    """
    vacancy_info = dict() # Словарь, описание вакансии

    vacancy_info['name'] = None # Имя
    vacancy_info['link'] = None # Ссылка на вакансию
    vacancy_info['pay_min'] = None # Минимальная заработная плата
    vacancy_info['pay_max'] = None # Максимальная заработная плата
    vacancy_info['pay_valuta'] = None # Валюта заработной платы
    vacancy_info['employer'] = None # Работодатель
    vacancy_info['employer_link'] = None # Ссылка на работодателя
    vacancy_info['address'] = None # Адрес работодателя

    # Заполнение словаря
    vacancy_title = vacancy.find('a',{'data-qa': 'vacancy-serp__vacancy-title'})
    vacancy_info['name'] = vacancy_title.getText().replace('\xa0', ' ')
    vacancy_info['link'] = vacancy_title['href']

    pay_min = None
    pay_max = None
    pay_valuta = None
    try:
        vacancy_pay = vacancy.find('span', {'data-qa': 'vacancy-serp__vacancy-compensation'}).getText().split()
        if vacancy_pay[0] == 'от':
            pay_min = int(f'{vacancy_pay[1]}{vacancy_pay[2]}')
        elif vacancy_pay[0] == 'до':
            pay_max = int(f'{vacancy_pay[1]}{vacancy_pay[2]}')
        else:
            pay_min = int(f'{vacancy_pay[0]}{vacancy_pay[1]}')
            pay_max = int(f'{vacancy_pay[3]}{vacancy_pay[4]}')
        pay_valuta = vacancy_pay[-1]
    except:
        pass

    vacancy_info['pay_min'] = pay_min
    vacancy_info['pay_max'] = pay_max
    vacancy_info['pay_valuta'] = pay_valuta

    try:
        vacancy_employer = vacancy.find('a', {'data-qa': 'vacancy-serp__vacancy-employer'})
        vacancy_info['employer'] = vacancy_employer.getText().replace('\xa0', ' ')
        vacancy_info['employer_link'] = f"{main_link}{vacancy_employer['href']}"
    except:
        pass

    vacancy_info['address'] = vacancy.find('span', {'data-qa': 'vacancy-serp__vacancy-address'}).getText().replace('\xa0', ' ')

    return vacancy_info



if __name__ == '__main__':

    search = 'Data+Scientist'
    main_link = 'https://hh.ru'
    link =  f'{main_link}/search/vacancy?clusters=true&enable_snippets=true&salary=&st=searchVacancy&text={search}'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.135 YaBrowser/21.6.3.757 Yowser/2.5 Safari/537.36'}
    html = requests.get(link, headers=headers).text
    soup = bs(html, 'html.parser')
    next_pager = soup.find('a', {'data-qa': 'pager-next'})

    vacancies = [] # Список всех вакансий
    # Перебор первой страницы
    vacancy_list = soup.find_all('div', {'class': 'vacancy-serp-item'})
    for vacancy in vacancy_list:
        vacancies.append(vacancy_info_dict(vacancy))

    # Перебор всех страниц
    while next_pager:

        link = f"{main_link}{next_pager['href']}"
        html = requests.get(link, headers=headers).text
        soup = bs(html, 'html.parser')

        next_pager = soup.find('a', {'data-qa': 'pager-next'})
        vacancy_list = soup.find_all('div', {'class': 'vacancy-serp-item'})

        # Перебор всех вакансий на странице
        for vacancy in vacancy_list:
            vacancies.append(vacancy_info_dict(vacancy))

    # Преобразование и сохранение
    df = pd.DataFrame(vacancies)
    df.to_json('vacancy_list.json')
    df.to_csv('vacancy_list.csv')