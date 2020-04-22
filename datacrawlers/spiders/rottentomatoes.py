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
        title = response.css('.mop-ratings-wrap__title--top *::text').extract_first().lstrip()
        year = response.css('time::text').extract_first()[-4:]
        with open('dataRottenCritic.json', 'a') as outfileRC:
            with open('dataRottenFans.json', 'a') as outfileRF:
                try:
                    rat_rc = response.css('.mop-ratings-wrap__percentage *::text').extract_first().replace('%', '').strip()
                    rc_votes = response.css('.mop-ratings-wrap__review-totals small *::text')[0].extract().replace(',', '').strip()
                    my_json = "{\"rating\":\"" + str(rat_rc) + "\",\"title\":\"" + str(title) + "\",\"year\":\"" + str(year) + "\",\"votes\":\"" + str(rc_votes) + "\"}\n"
                    self.log(my_json)
                    outfileRC.write(my_json)
                except Exception as e:
                    print(e)
                try:
                    rat_rf = response.css('.mop-ratings-wrap__percentage *::text')[1].extract().replace('%', '').strip()
                    rf_votes = response.css('.mop-ratings-wrap__review-totals strong *::text')[1].extract().split(':')[1].replace(',', '').strip()
                    my_json = "{\"rating\":\"" + str(rat_rf) + "\",\"title\":\"" + str(title) + "\",\"year\":\"" + str(
                        year) + "\",\"votes\":\"" + str(rf_votes) + "\"}\n"
                    self.log(my_json)
                    outfileRF.write(my_json)
                except Exception as e:
                    print(e)
                pass
            pass
        pass
