# -*- coding: utf-8 -*-
import scrapy
import json
from scrapy.http.request import Request
from datacrawlers.items import Movie


class MetacriticSpider(scrapy.Spider):
    name = 'metacritic'
    allowed_domains = ['metacritic.com']
    start_urls = ['https://www.metacritic.com/browse/movies/genre/userscore/action?view=detailed']

    def parse(self, response):
        genres = [s.split()[1].split('_', 1)[1].replace("_", "-") for s in
                  response.xpath('//ul[@class="genre_nav"]/li/@class').extract()]
        genre_links = ["http://www.metacritic.com/browse/movies/genre/userscore/" + genre + "/?view=detailed" for genre in
                       genres]
        requests = [Request(url=URL, callback=self.parse_genre) for URL in genre_links]
        return requests

    def parse_genre(self, response):
        try:
            page_links = [response.url + "&page=" + str(i) for i in
                          range(int(response.xpath('//li[@class="page last_page"]/a/text()').extract()[0]))]
        except IndexError:
            page_links = [response.url]

        requests = [Request(url=URL, callback=self.parse_page) for URL in page_links]
        return requests

    def parse_page(self, response):
        product_selector = '.product'
        score_selector = '.metascore_w *::text'
        with open('dataUsers.json', 'a') as outfile:
            for product in response.css(product_selector):
                movie = Movie()
                rat = product.css(score_selector).extract_first()
                if rat is None:
                    continue
                movie['rating'] = rat
                movie['year'] = product.xpath('//li[@class="stat release_date"]/span[@class="data"]/text()').extract()[
                                    0][-4:]
                movie['title'] = product.css('.product_title *::text').extract_first()
                my_json = "{'rating':'" + rat + "','year':'" + product.xpath('//li[@class="stat release_date"]/span[@class="data"]/text()').extract()[0][-4:] + "','title':'"+product.css('.product_title *::text').extract_first() + "'},\n"
                self.log(my_json)
                outfile.write(my_json)
            pass
        pass
