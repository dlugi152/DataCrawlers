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
        with open('dataRottenCritic.json', 'a') as outfileRC:
            with open('dataRottenFans.json', 'a') as outfileRF:
                for product in jsonresponse["results"]:
                    rat_rc = -1
                    rat_rf = -1
                    title = ""
                    try:
                        rat_rc = product["tomatoScore"]
                        rat_rf = product["popcornScore"]
                        title = product["title"]
                    except Exception:
                        pass
                    try:
                        if rat_rc != -1 and title != "":
                            my_json = "{'rating':'" + str(rat_rc) + "','title':'" + str(title) + "'},\n"
                            self.log(my_json)
                            outfileRC.write(my_json)
                    except Exception:
                        pass
                    try:
                        if rat_rf != -1 and title != "":
                            my_json = "{'rating':'" + str(rat_rf) + "','title':'" + str(title) + "'},\n"
                            self.log(my_json)
                            outfileRF.write(my_json)
                    except Exception:
                        pass
                pass
            pass
        pass
