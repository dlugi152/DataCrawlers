# -*- coding: utf-8 -*-
import scrapy
import json
from scrapy.http.request import Request


class RottentomatoesSpider(scrapy.Spider):
    name = 'rottentomatoes'
    allowed_domains = ['rottentomatoes.com']
    start_urls = [
        'https://www.rottentomatoes.com/api/private/v2.0/browse?maxTomato=100&maxPopcorn=100&services=amazon%3Bhbo_go%3Bitunes%3Bnetflix_iw%3Bvudu%3Bamazon_prime%3Bfandango_now&genres=1&certified&sortBy=release&type=dvd-streaming-all']

    def parse(self, response):
        genres = list(range(1, 15))
        genre_links = ["https://www.rottentomatoes.com/api/private/v2.0/browse?maxTomato=100&maxPopcorn=100&services=amazon%3Bhbo_go%3Bitunes%3Bnetflix_iw%3Bvudu%3Bamazon_prime%3Bfandango_now&genres=" + str(genre) + "&certified&sortBy=release&type=dvd-streaming-all" for genre in genres]
        requests = [Request(url=URL, callback=self.parse_genre) for URL in genre_links]
        return requests

    def parse_genre(self, response):
        try:
            page_links = [response.url + "&page=" + str(i) for i in range(1, 101)]
        except IndexError:
            page_links = [response.url]

        requests = [Request(url=URL, callback=self.parse_page) for URL in page_links]
        return requests

    def parse_page(self, response):
        jsonresponse = json.loads(response.body_as_unicode())
        movie_links = ["https://www.rottentomatoes.com" + product["url"] for product in jsonresponse["results"]]

        requests = [Request(url=URL, callback=self.parse_movie) for URL in movie_links]
        return requests

    def parse_movie(self, response):
        title = response.css('#movie-title *::text').extract_first().lstrip()
        year = response.css('.year *::text').extract_first()
        with open('dataRottenCritic.json', 'a') as outfileRC:
            with open('dataRottenFans.json', 'a') as outfileRF:
                try:
                    rat_rc = response.css('.critic-score a .meter-value span *::text').extract_first()
                    rc_votes = response.css('#scoreStats div')[1].css('span *::text')[1].extract().replace(',', '')
                    my_json = "{\"rating\":\"" + str(rat_rc) + "\",\"title\":\"" + str(title) + "\",\"year\":\"" + str(year) + "\",\"votes\":\"" + str(rc_votes) + "\"}\n"
                    self.log(my_json)
                    outfileRC.write(my_json)
                except Exception:
                    pass
                try:
                    rat_rf = response.css('.audience-score a div .media-body div span *::text').extract_first().replace('%', '')
                    rf_votes = response.css('.audience-info div *::text')[5].extract().replace(',', '').lstrip()
                    my_json = "{\"rating\":\"" + str(rat_rf) + "\",\"title\":\"" + str(title) + "\",\"year\":\"" + str(
                        year) + "\",\"votes\":\"" + str(rf_votes) + "\"}\n"
                    self.log(my_json)
                    outfileRF.write(my_json)
                except Exception:
                    pass
                pass
            pass
        pass
