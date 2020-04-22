# -*- coding: utf-8 -*-
import scrapy
from datacrawlers import dbconnector
from scrapy import Request
from dateparser import parse


class ImdbBasicsSpider(scrapy.Spider):
    name = 'imdb_basics'
    allowed_domains = ['imdb.com']
    start_urls = ['http://imdb.com/']
    conn = dbconnector.dbconnector()

    def start_requests(self):
        movies = dbconnector.select(self.conn)
        for movie in movies:
            imdb_id = str(movie[0]).zfill(7)
            yield Request(url="https://www.imdb.com/title/tt" + str(imdb_id) + "/releaseinfo", callback=self.parse,
                          meta={'id': imdb_id})

    def parse(self, response):
        date = ""
        parsed_date = None
        try:
            date = response.css('.release-date-item__date::text').extract_first()
            initial_date = parse(date)
            for i in response.css('.release-date-item__date::text'):
                parsed_date = parse(i.extract(), settings={'STRICT_PARSING': True})
                if parsed_date is not None:
                    break
            if parsed_date is None or parsed_date.year != initial_date.year:
                self.log("DELETE")
                raise Exception
            dbconnector.execute(self.conn, 'UPDATE public."Movie" SET "ReleaseDate"=\'' + str(parsed_date) +
                                '\' WHERE "ID"=' + response.meta.get('id'))
        except Exception:
            self.log(parsed_date)
            dbconnector.execute(self.conn, 'delete from public."Movie" WHERE "ID"=' + response.meta.get('id'))
        pass
