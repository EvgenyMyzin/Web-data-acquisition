# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import scrapy
import re
import os
from scrapy.pipelines.images import ImagesPipeline
from pymongo import MongoClient


class LeroyparserPipeline(object):
    def __init__(self):
        client = MongoClient('localhost', 27017)
        self.mongo_base = client.leroy_products

    def process_item(self, item, spider):
        item['_id'] = item['_id'][0]
        item['link'] = item['link'][0]
        item['price'] = item['price'][0]
        item['characteristic'] = {
            item['terms'][i]: item['definitions'][i] for i in range(len(item['terms']))
        }

        del item['terms'], item['definitions']

        collection = self.mongo_base[spider.name]
        collection.update_one({'link': item['link']}, {'$set': item}, upsert=True)

        return item


class LeroyImagesPipeline(ImagesPipeline):
    def get_media_requests(self, item, info):
        if item['photos']:
            for img in item['photos']:
                yield scrapy.Request(img)

    def file_path(self, request, response=None, info=None):
        pattern = re.compile('\/(\d+)')
        name = re.findall(pattern, request.url)[0]
        path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'images', name)
        if not os.path.exists(path):
            os.mkdir(path)
        tail = os.path.basename(request.url)
        result = os.path.join(name, tail)
        return result

    def item_completed(self, results, item, info):
        if results[0]:
            item['photos'] = [itm[1] for itm in results if itm[0]]
        return item
