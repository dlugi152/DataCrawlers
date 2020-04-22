# -*- coding: utf-8 -*-
import scrapy
from scrapy_splash import SplashRequest


class ImdbeventsSpider(scrapy.Spider):
    name = 'imdbEvents'
    allowed_domains = ['imdb.com']
    start_urls = ['https://www.imdb.com/event/all/']

    def start_requests(self):
        for url in self.start_urls:
            yield SplashRequest(url=url, callback=self.parse, endpoint='render.html',
                                args={'wait': 1.0})

    def parse(self, response):
        events = response.xpath('//ul[@class="event-list__events"]/li/a/@href').extract()
        requests = [SplashRequest(url=event, callback=self.parse_event, args={'wait': 1.0}) for event
                    in events]
        return requests

    def parse_event(self, response):
        events_year = response.xpath('//div[@class="event-history-widget__years"]').xpath(
            '//div[@class="event-history-widget__years-row"]/span/a/@href').extract()
        requests = [SplashRequest(url="https://www.imdb.com/" + year, callback=self.parse_page, args={'wait': 1.0}) for
                    year
                    in events_year]
        return requests

    def parse_page(self, response):
        title = response.xpath('//div[@class="event-header__title"]/h1/text()').extract_first()
        title = title.replace("\"", "\\\"")
        imdb_event_id = response.url.split('/')[5]
        year = response.xpath('//div[@class="event-year-header__year"]/text()').extract_first()[:4]
        with open('dataImdbMovieEvents.json', 'a') as outfileM:
            with open('dataImdbActorEvents.json', 'a') as outfileA:
                for award in response.xpath('//div[@class="event-widgets__award"]'):
                    award_name = award.xpath('.//div[@class="event-widgets__award-name"]/text()').extract_first()
                    award_name = award_name.replace("\"", "\\\"")
                    for product in award.xpath('.//div[@class="event-widgets__award-category"]'):
                        cat_name = product.xpath(
                            './/div[@class="event-widgets__award-category-name"]/text()').extract_first()
                        if cat_name is None:
                            cat_name = ""
                        cat_name = cat_name.replace("\"", "\\\"")
                        for singleTitle in product.xpath('.//div[@class="event-widgets__nomination-details"]'):
                            imdb_id = ""
                            try:
                                imdb_id = singleTitle.xpath(
                                    './/span[@class="event-widgets__nominee-name"]/a/@href').extract_first().split('/')[2]
                            except Exception:
                                pass
                            if imdb_id is None:
                                continue
                            winner = False
                            if singleTitle.xpath(
                                    './/div[@class="event-widgets__winner-badge"]').extract_first() is not None:
                                winner = True
                            if imdb_id[:2] == 'tt':
                                my_json = "{\"movie\":\"" + imdb_id + "\",\"awardTitle\":\"" + title + "\",\"year\":\"" + str(
                                    year) + "\",\"eventId\":\"" + imdb_event_id + "\",\"category\":\"" + cat_name + "\",\"winner\":\"" + str(
                                    winner) + ",\"award_name\":\"" + award_name + "\"}\n"
                                self.log(my_json)
                                outfileM.write(my_json)
                            if imdb_id[:2] == 'nm':
                                try:
                                    movie_id = singleTitle.css(
                                        '.event-widgets__secondary-nominees span span a *::attr(href)').extract_first().split(
                                        '/')[2]
                                except Exception:
                                    movie_id = ""
                                my_json = "{\"name\":\"" + imdb_id + "\",\"awardTitle\":\"" + title + "\",\"year\":\"" + str(
                                    year) + "\",\"eventId\":\"" + imdb_event_id + "\",\"category\":\"" + cat_name + "\",\"winner\":\"" + str(
                                    winner) + "\",\"movie_id\":\"" + str(movie_id) + ",\"award_name\":\"" + award_name + "\"}\n"
                                self.log(my_json)
                                outfileA.write(my_json)
            pass
        pass
