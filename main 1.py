from bs4 import BeautifulSoup as bs
import requests
import re
import pandas as pd
from pprint import pprint


def _parser_superjob(vacancy):
    vacancy_date = []

    params = {
        'keywords': vacancy, \
        'profession_only': '1', \
        'geo[c][0]': '15', \
        'geo[c][1]': '1', \
        'geo[c][2]': '9', \
        'page': ''
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36'
    }

    link = 'https://www.superjob.ru/vacancy/search/'

    html = requests.get(link, params=params, headers=headers)

    if html.ok:
        parsed_html = bs(html.text, 'html.parser')

        page_block = parsed_html.find('a rel="next"')
 ##       print(page_block)

    if not page_block:
        last_page = 1
    else:
        page_block_parent = page_block.findParent()

#        pprint(page_block_parent)
#        print(page_block)
        children = list(page_block_parent.findChildren(recoursive=False))
#        print(children)
        print(len(children))

        last_page = int(page_block_parent.find_all('a')[-2].getText())
#        last_page = int(page_block.find_all('a', {class="icMQ_ bs_sM _3ze9n _3fOgw'})[-2].getText())

#        last_page = 6

    print(last_page)

    for page in range(0, last_page + 1):
        params['page'] = page
        html = requests.get(link, params=params, headers=headers)
        print(page)
        if html.ok:
            parsed_html = bs(html.text, 'html.parser')
            vacancy_items = parsed_html.find_all('div', {'class': 'f-test-vacancy-item'})

            for item in vacancy_items:
                vacancy_date.append(_parser_item_superjob(item))

    return vacancy_date


def _parser_item_superjob(item):
    vacancy_date = {}

    # vacancy_name
    vacancy_name = item.find_all('a')
    if len(vacancy_name) > 1:
        vacancy_name = vacancy_name[-2].getText()
    else:
        vacancy_name = vacancy_name[0].getText()
    vacancy_date['vacancy_name'] = vacancy_name

    # company_name
    company_name = item.find('span', {'class': 'f-test-text-vacancy-item-company-name'})

    if not company_name:
        company_name = item.findParent() \
            .find('span', {'class': 'f-test-text-vacancy-item-company-name'}) \
            .getText()
    else:
        company_name = company_name.getText()

    vacancy_date['company_name'] = company_name

    # city
    company_location = item.find('span', {'class': 'f-test-text-company-item-location'}) \
        .findChildren()[1] \
        .getText() \
        .split(',')

    vacancy_date['city'] = company_location[0]

    # metro station
    if len(company_location) > 1:
        metro_station = company_location[1]
    else:
        metro_station = None

    vacancy_date['metro_station'] = metro_station

    # salary
    ###    salary = item.find('span', {'class': 'f-test-text-company-item-salary'}) \
    ###        .findChildren()
    ###    if not salary:
    ###        salary_min = None
    ###        salary_max = None
    ###       salary_currency = None
    ###    else:
    ###        salary_currency = salary[-1].getText()
    ###        is_check_sarary = item.find('span', {'class': 'f-test-text-company-item-salary'}) \
    ###            .getText() \
    ###            .replace(u'\xa0', u' ') \
    ###            .split(' ', 1)[0]
    ###        if is_check_sarary == 'до' or len(salary) == 2:
    ###            salary_min = None
    ###        salary_max = int(salary[0].getText() \
    ###                         .replace(u'\xa0', u''))
    ###   elif is_check_sarary == 'от':
    ###       salary_min = int(salary[0].getText() \
    ###                            .replace(u'\xa0', u''))
    ###        salary_max = None
    ###    else:
    ###        salary_min = int(salary[0].getText() \
    ###                         .replace(u'\xa0', u''))
    ###       salary_max = int(salary[2].getText() \
    ###                        .replace(u'\xa0', u''))

    ###    vacancy_date['salary_min'] = salary_min
    ###    vacancy_date['salary_max'] = salary_max
    ###   vacancy_date['salary_currency'] = salary_currency

    # link
    vacancy_link = item.find_all('a')

    if len(vacancy_link) > 1:
        vacancy_link = vacancy_link[-2]['href']
    else:
        vacancy_link = vacancy_link[0]['href']

    vacancy_date['vacancy_link'] = f'https://www.superjob.ru{vacancy_link}'

    # site
    vacancy_date['site'] = 'www.superjob.ru'

    return vacancy_date


def parser_vacancy(vacancy):
    vacancy_date = []
    #    vacancy_date.extend(_parser_hh(vacancy))
    vacancy_date.extend(_parser_superjob(vacancy))
#    print(vacancy_date)
    df = pd.DataFrame(vacancy_date)

    return df


vacancy = 'Python'
df = parser_vacancy(vacancy)

pprint(df[0:10])
