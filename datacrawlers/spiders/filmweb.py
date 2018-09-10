# -*- coding: utf-8 -*-
import scrapy
from scrapy.http.request import Request


class FilmwebSpider(scrapy.Spider):
    name = 'filmweb'
    allowed_domains = ['filmweb.pl']
    start_urls = ['https://www.filmweb.pl/films/search?endRate=10&endYear=1888&orderBy=popularity&descending=true&startRate=1&startYear=1888']

    def parse(self, response):
        years = list(range(1988, 2019))
        year_links = ["https://www.filmweb.pl/films/search?endYear=" + str(year) + "&orderBy=popularity&startRate=1&endRate=10&descending=true&startYear=" + str(year) for year in years]
        requests = [Request(url=URL, callback=self.parse_year) for URL in year_links]
        return requests

    def parse_year(self, response):
        try:
            page_links = [response.url + "&page=" + str(i) for i in range(1001)]
        except IndexError:
            page_links = [response.url]

        requests = [Request(url=URL, callback=self.parse_page) for URL in page_links]
        return requests

    def parse_page(self, response):
        product_selector = '.filmPreview'
        score_selector = '.rateBox__rate *::text'
        with open('dataFilmweb.json', 'a') as outfile:
            for product in response.css(product_selector):
                rat = product.css(score_selector).extract_first()
                if rat is None:
                    continue
                movie_year = product.css('.filmPreview__year *::text').extract_first()
                movie_title = product.css('.filmPreview__originalTitle *::text').extract_first()
                if movie_title is None:
                    movie_title = product.css('.filmPreview__title *::text').extract_first()
                my_json = "{'rating':'" + rat + "','year':'" + movie_year + "','title':'" + movie_title + "'},\n"
                self.log(my_json)
                outfile.write(my_json)
        pass
