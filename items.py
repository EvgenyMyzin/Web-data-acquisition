# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
import re
from itemloaders.processors import TakeFirst, MapCompose


def get_id(values):
    pattern = re.compile('(\d+)\/')
    values = int(re.findall(pattern, values)[0])
    return values

def get_link(values):
    pattern = re.compile('<\d+ (.+)>')
    values = re.findall(pattern, values)
    return values

def edit_definitions(values):
    pattern = re.compile('\\n +')
    values = re.sub(pattern, '', values)
    try:
        return float(values)
    except ValueError:
        return values

def change_price(values):
    values = float(values)
    return values


class LeroyparserItem(scrapy.Item):
    _id = scrapy.Field(input_processor=MapCompose(get_id))
    name = scrapy.Field(output_processor=TakeFirst())
    photos = scrapy.Field(input_processor=MapCompose())
    terms = scrapy.Field(input_processor=MapCompose())
    definitions = scrapy.Field(input_processor=MapCompose(edit_definitions))
    price = scrapy.Field(input_processor=MapCompose(change_price))
    characteristic = scrapy.Field()
    link = scrapy.Field(output_processor=MapCompose(get_link))
