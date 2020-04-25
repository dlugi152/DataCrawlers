# -*- coding: utf-8 -*-
import os
import time

import requests
import scrapy
from scrapy import Request
from scrapy_splash import SplashRequest

from datacrawlers import dbconnector
from newspaper import Article
from bs4 import BeautifulSoup
from dragnet import extract_content, extract_content_and_comments
import articleDateExtractor
from goose3 import Goose


class NewsSpider(scrapy.Spider):
    name = 'news'
    start_urls = ['https://www.imdb.com']
    conn = dbconnector.dbconnector()

    def start_requests(self):
        movies = dbconnector.select(self.conn)
        for movie in movies:
            imdb_id = str(movie[0]).zfill(7)
            yield Request(url="https://thefilmstage.com/the-100-greatest-achievements-in-cinematography-in-the-20th-century-according-to-asc/", callback=self.parse,
                          meta={'id': imdb_id})

    def parse(self, response):
        imdb_id = response.meta.get('id')

        for news in response.xpath('//article'):
            try:
                date = news.xpath('.//li[@class="ipl-inline-list__item news-article__date"]/text()').extract_first()
                url = "https://www.imdb.com" + \
                      news.xpath('.//section[@class="news-article__body"]/a/@href').extract_first()
                content = news.xpath('.//div[@class="news-article__content"]').extract_first()
                soup = BeautifulSoup(content, "lxml")
                content = soup.get_text().replace("'", "''").strip()
                r = None
                try:
                    r = requests.get(url)
                    redirect_url = '\'' + r.url + '\''
                except Exception:
                    redirect_url = 'null'

                news_id = dbconnector.execute(self.conn, 'INSERT INTO "News" ("IDMovie", "Content", "Hyperlink", ' +
                                              '"Date", "RedirectHyperlink") ' + 'VALUES (' + str(imdb_id) +
                                              ',\'' + str(content) + '\',\'' + str(url) + '\',\'' + str(date) +
                                              '\',' + redirect_url + ') returning "ID"')[0][0]
                try:
                    r.raise_for_status()  # raise if not 2XX
                    yield Request(url=redirect_url[1:-1], callback=self.parse_article,
                                  meta={'news_id': news_id})
                except Exception as ex:
                    self.log(str(ex))
                    pass
            except Exception:
                continue

        load_more = response.xpath('//span[@class="news-next-page-token"]/'
                                   '@data-news-next-page-token').extract_first()
        if load_more is not None:
            yield Request(url="https://www.imdb.com/title/tt" + str(imdb_id) + "/news/_ajax/" + load_more,
                          callback=self.parse,
                          meta={'id': imdb_id})
        pass

    def parse_article(self, response):
        news_id = 19684#response.meta.get('news_id')

        # save to file
        with open(str(news_id) + '.html', 'wb') as fh:
            fh.write(response.body)
        article = Article(response.url)
        # set html manually
        with open(str(news_id) + '.html', 'rb') as fh:
            article.html = fh.read()
        os.remove(str(news_id) + '.html')
        # need to set download_state to 2 for this to work
        article.download_state = 2
        article.parse()
        article.nlp()
        date = article.publish_date
        keywords = str([x.replace("'", "''") for x in article.keywords]).replace('"', '\'')
        content = article.text.replace("'", "''")
        summary = article.summary.replace("'", "''")
        title = article.title.replace("'", "''")
        if date is None:
            date = 'null'
        else:
            date = "'" + str(date) + "'"
        authors = str([x.replace("'", "''") for x in article.authors]).replace('"', '\'')
        tags = str([x.replace("'", "''") for x in article.meta_keywords]).replace('"', '\'')

        dbconnector.execute(self.conn,
                            'INSERT INTO "ParsedNews-newspaper"("IDNews", "Date", "Content", "Keywords", ' +
                            '"Summary", "Authors", "Tags", "Title") ' +
                            'VALUES (' + str(news_id) + ', ' + str(date) + ', \'' + content +
                            '\', ARRAY ' + str(keywords) + '::text[], \'' + summary + '\', ARRAY ' +
                            str(authors) + '::text[], ARRAY ' + str(tags) + '::text[], \'' + title + '\')')

        # get main article without comments
        content = extract_content(response.text).replace("'", "''")

        # get article and comments
        content_comments = '[\'' + extract_content_and_comments(response.text).replace("'", "''") + '\']'

        dbconnector.execute(self.conn,
                            'INSERT INTO "ParsedNews-dragnet"("IDNews", "Content", "Comments") ' +
                            'VALUES (' + str(news_id) + ', \'' + content +
                            '\', ARRAY ' + str(content_comments) + '::text[])')

        date = articleDateExtractor.extractArticlePublishedDate(articleLink=response.url, html=response.text)
        if date is not None:
            dbconnector.execute(self.conn,
                                'INSERT INTO "ParsedNews-ade"("IDNews", "Date") ' +
                                'VALUES (' + str(news_id) + ', \'' + str(date) + '\')')

        g = Goose()
        article = g.extract(raw_html=response.text)
        date = article.publish_datetime_utc
        keywords = str([x.replace("'", "''") for x in article.tags]).replace('"', '\'')
        content = article.cleaned_text.replace("'", "''")
        summary = article.meta_description.replace("'", "''")
        title = article.title.replace("'", "''")
        if date is None:
            date = 'null'
        else:
            date = "'" + str(date) + "'"
        authors = str([x.replace("'", "''") for x in article.authors]).replace('"', '\'')
        tags = str([x.replace("'", "''") for x in article.meta_keywords.split(",")]).replace('"', '\'')
        tweets = str([x.replace("'", "''") for x in article.tweets]).replace('"', '\'')

        dbconnector.execute(self.conn, 'INSERT INTO "ParsedNews-goose"(' +
                            '"IDNews", "Date", "Content", "Keywords", "Summary", ' +
                            '"Authors", "Tags", "Tweets",' +
                            '"Title") VALUES (' + str(news_id) + ', ' + date +
                            ', \'' + content + '\', ARRAY ' + str(keywords) +
                            '::text[], \'' + str(summary) + '\', ARRAY ' + str(authors) +
                            '::text[], ARRAY ' + str(tags) + '::text[], ARRAY ' +
                            str(tweets) + '::text[], \'' + str(title) + '\')')

        pass

    pass
