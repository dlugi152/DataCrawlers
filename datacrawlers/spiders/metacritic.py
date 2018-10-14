# -*- coding: utf-8 -*-
import scrapy
from scrapy.http.request import Request


class MetacriticSpider(scrapy.Spider):
    name = 'metacritic'
    allowed_domains = ['metacritic.com']
    start_urls = ['https://www.metacritic.com/browse/movies/genre/name/action?view=detailed']

    def parse(self, response):
        genres = [s.split()[1].split('_', 1)[1].replace("_", "-") for s in
                  response.xpath('//ul[@class="genre_nav"]/li/@class').extract()]
        genre_links = ["http://www.metacritic.com/browse/movies/genre/name/" + genre + "/?view=detailed" for genre
                       in
                       genres]
        requests = [Request(url=URL, callback=self.parse_genre) for URL in genre_links]
        return requests

    def parse_genre(self, response):
        try:
            page_links = [response.url + "&page=" + str(i) for i in
                          range(int(response.xpath('//li[@class="page last_page"]/a/text()').extract()[0]))]
        except IndexError:
            page_links = [response.url]
        requests = [Request(url=URL, callback=self.parse_list) for URL in page_links]
        return requests

    def parse_list(self, response):
        movies_links = ["https://www.metacritic.com" + addr + "/details" for addr in
                        response.css('.product').css('.basic_stat').xpath('@href').extract()]
        requests = [Request(url=URL, callback=self.parse_movie) for URL in movies_links]
        return requests

    def parse_movie(self, response):
        title = response.css('.product_page_title a h1 *::text').extract()[0]
        title = title.replace("\"","\"\"")
        year = response.css('.release_date span')[1].css('*::text').extract()[0][-4:]
        with open('dataMetacriticUsers.json', 'a') as user_file:
            with open('dataMetacriticScore.json', 'a') as critic_file:
                for score in response.css('.score_wrapper'):
                    rat = score.css('.metascore_w *::text').extract()[0]
                    self.log(str(rat))
                    cr_num = response.css('.based_on *::text').extract()[0].replace(",", "")
                    votes = [int(s) for s in cr_num.split() if s.isdigit()][0]
                    usr_flag = score.css('.metascore_w.user *::text').extract()
                    if not usr_flag:
                        my_json = "{\"rating\":\"" + str(rat) + "\",\"year\":\"" + str(
                            year) + "\",\"title\":\"" + title + "\",\"votes\":\"" + str(votes) + "\"}\n"
                        self.log(my_json)
                        critic_file.write(my_json)
                    else:
                        if str(rat) == "tbd":
                            continue
                        my_json = "{\"rating\":\"" + str(rat) + "\",\"year\":\"" + str(
                            year) + "\",\"title\":\"" + title + "\",\"votes\":\"" + str(votes) + "\"}\n"
                        self.log(my_json)
                        user_file.write(my_json)
        pass

    pass
