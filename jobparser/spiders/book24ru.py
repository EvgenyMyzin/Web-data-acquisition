"""Вариант 2: Каждый паук должен собирать:
            * Ссылку на книгу
            * Наименование книги
            * Автор(ы)
            * Основную цену
            * Цену со скидкой
            * Рейтинг книги
"""

import re
import scrapy
from scrapy.http import HtmlResponse
from jobparser.items import JobparserItem

class Book24ruSpider(scrapy.Spider):
    name = 'book24ru'
    allowed_domains = ['book24.ru']
    page = 1
    search_words = 'python'
    start_urls = [f'https://book24.ru/search/page-{page}/?q={search_words}']

    def parse(self, response: HtmlResponse):
        """Первый метод в который идет паук"""
        # Получаем ссылки на книги
        if response.status != 404:  # При условии что переключимся на существующую страницу
            links = response.xpath("//div[@class='catalog__product-list-holder']//a[contains(@class, 'product-card__name')]/@href").extract()
            # Заменяем относительную ссылку на полную
            links = list(map(lambda row: f'https://book24.ru{row}', links))
            # Перед next_page прибавляем страницу
            Book24ruSpider.page += 1
            next_page = f'https://book24.ru/search/page-{Book24ruSpider.page}/?q={Book24ruSpider.search_words}'
            # Идем на следующую страницу
            yield response.follow(next_page, callback=self.parse)

            # Кидаем ссылки асинхронно в парсер
            for link in links:
                yield response.follow(link, callback=self.vacancy_parse)  # Передаем в vacancy_parse

    def vacancy_parse(self, response: HtmlResponse):
        """Парсит информацию"""
        url = response.url
        book_name = response.xpath("//h1/text()").extract_first().replace(r'\n', '').strip()
        authors = list(map(lambda row: row.replace(r'\n', '').strip(), response.xpath("//span[contains(text(), 'Автор')]/../../div[@class='product-characteristic__value']/a/text()").extract()))
        authors = ', '.join(authors)
        #           ---ЦЕНА---
        price = response.xpath("//span[contains(@class, 'product-sidebar-price__price')]/text()")
        # Если цена вообще есть
        if len(price) != 0:
            # Смотрим есть ли зачеркнутая старая цена
            old_price = response.xpath("//span[@class='app-price product-sidebar-price__price-old']/text()")
            if len(old_price) != 0:  # Если есть старая цена
                general_price = price.extract_first().replace(r'\n', '').strip()  # Цена без скидки
                general_price = int(''.join(re.findall(r'\d+', general_price)))
                discount_price = response.xpath("//span[@class='app-price product-sidebar-price__price']/text()").extract_first().replace(r'\n', '').strip()  # Цена со скидкой
                discount_price = int(''.join(re.findall(r'\d+', discount_price)))
            # Если есть только основная цена
            else:
                general_price = price.extract_first().replace(r'\n', '').strip()  # Цена без скидки
                general_price = int(''.join(re.findall(r'\d+', general_price)))
                discount_price = None   # Цена со скидкой
        # Если вместо цены "нет в наличии"
        else:
            general_price, discount_price = 'Нет в наличии', 'Нет в наличии'

        rating = float(response.xpath("//span[@class='rating-widget__main-text']/text()").extract_first().replace(r'\n', '').replace(',', '.').strip())

        yield JobparserItem(url=url,
                            book_name=book_name,
                            authors=authors,
                            general_price=general_price,
                            discount_price=discount_price,
                            rating=rating)
