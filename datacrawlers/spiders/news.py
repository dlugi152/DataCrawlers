# -*- coding: utf-8 -*-
import time

import scrapy
from scrapy import Request
from datacrawlers import dbconnector
from newspaper import Article
from nltk.sentiment.vader import SentimentIntensityAnalyzer


class NewsSpider(scrapy.Spider):
    name = 'news'
    start_urls = ['https://www.imdb.com']

    def start_requests(self):
        movies = dbconnector.select()
        for movie in movies:
            yield Request(url="https://www.imdb.com/title/"+str(movie[9])+"/news", callback=self.parse,
                          meta={'id': movie[9], 'db_id': movie[0]})

    def parse(self, response):
        id_imdb = response.meta.get('id')
        db_id = response.meta.get('db_id')

        for news in response.xpath('//article'):
            date = news.xpath('.//li[@class="ipl-inline-list__item news-article__date"]/text()').extract_first()
            url = "https://www.imdb.com" + \
                  news.xpath('.//section[@class="news-article__body"]/a/@href').extract_first()
            yield Request(url=url, callback=self.parse_article,
                          meta={'db_id': db_id, 'fallback_date': date})

        load_more = response.xpath('//span[@class="news-next-page-token"]/'
                                   '@data-news-next-page-token').extract_first()
        if load_more is not None:
            yield Request(url="https://www.imdb.com/title/" + id_imdb + "/news/_ajax/" + load_more,
                          callback=self.parse,
                          meta={'id': id_imdb, 'db_id': db_id})
        pass

    def parse_article(self, response):
        db_id = response.meta.get('db_id')
        date = response.meta.get('fallback_date')
        article = Article(response.url)
        article.download()
        article.parse()
        article.nlp()
        analyser = SentimentIntensityAnalyzer()
        pol_text = analyser.polarity_scores(article.text)
        pol_sum = analyser.polarity_scores(article.summary)
        if article.publish_date is not None:
            date = article.publish_date

        id_text = dbconnector.execute('INSERT INTO public."Polarity"(' +
                                      '"Negative", "Neutral", "Positive", "Compound") ' +
                                      'VALUES (\'' + str(pol_text['neg']) + '\', \'' +
                                      str(pol_text['neu']) + '\',' +
                                      ' \'' + str(pol_text['pos']) + '\', \'' +
                                      str(pol_text['compound']) + '\') returning "ID"')[0][0]

        id_sum = dbconnector.execute('INSERT INTO public."Polarity"(' +
                                     '"Negative", "Neutral", "Positive", "Compound") ' +
                                     'VALUES (\'' + str(pol_sum['neg']) + '\', \'' +
                                     str(pol_sum['neu']) + '\',' +
                                     ' \'' + str(pol_sum['pos']) + '\', \'' +
                                     str(pol_sum['compound']) + '\') returning "ID"')[0][0]

        keywords = [x.replace('\'', ' ') for x in article.keywords]
        dbconnector.execute('INSERT INTO "News"("Content", "IDMovie", "Date", "Summary", ' +
                            '"Keywords", "IDPolarityContent", "IDPolaritySummary", "Hyperlink") VALUES ' +
                            '(\'' + article.text.replace('\'', ' ') + '\', ' + str(db_id) + ',' +
                            '\'' + str(date) + '\', \'' + article.summary.replace('\'', ' ') + '\',' +
                            'ARRAY ' + str(keywords) + '::text[],' +
                            '\'' + str(id_text) + '\', \'' + str(id_sum) + '\', \'' + str(response.url) + '\')')
        pass

    pass
