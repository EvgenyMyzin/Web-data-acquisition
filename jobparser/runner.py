from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings

from jobparser import settings
from jobparser.spiders.book24ru import Book24ruSpider

if __name__ == '__main__':
    crawler_settings = Settings()
    crawler_settings.setmodule(settings)  # Парсит настройки из файла

    process = CrawlerProcess(settings=crawler_settings)  # Создаем процесс, Кладем настройки

    process.crawl(Book24ruSpider)  # Кладем файл с пауком в процесс

    process.start()  # Запускаем
