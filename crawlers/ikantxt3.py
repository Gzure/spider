# -*- coding:UTF-8 -*-
from bs4 import BeautifulSoup
import requests
import re
import time
from pybloom import BloomFilter
import os, shutil
import codecs
from flask import current_app

try:
    LOG = current_app.logger
except:
    import logging
    from logging import handlers
    logging.basicConfig()
    logging.getLogger('apscheduler').setLevel(logging.DEBUG)
    LOG = logging.getLogger('apscheduler')

biqukan_url = 'https://www.biqukan.com'
wan_ben_url = 'https://www.biqukan.com/wanben'
features = 'html.parser'
bf_file = 'ikantxt2'
base_dir = u'/download/小说'
# base_dir = u'小说'
content_f = re.compile(u'.*正文卷')
timeout = 10


def find_title(index, name):
    return index.find('h2', text=name)


def find_container(index, name):
    return index.find('h2', text=name).find_next()


def find_wanben():
    book_urls = []
    res = request_get(wan_ben_url)
    wan_ben = BeautifulSoup(res, features=features)
    container = wan_ben.find('h2', text='好看的完本小说小说最近更新列表').find_next()
    for child in container.children:
        a_ele = child.find('a')
        href = biqukan_url + a_ele.get('href')
        book_urls.append(href)

    hot_bd = wan_ben.find('div', class_='hot bd')
    items = hot_bd.find_all('div', class_='item')
    for item in items:
        a_ele = item.find('a')
        href = biqukan_url + a_ele.get('href')
        book_urls.append(href)
    return book_urls


def find_recommend_block(index, name):
    book_urls = []
    # block = index.find('h2', text=name)
    # a_container = block.find_next('ul')
    a_container = find_container(index, name)
    for child in a_container.children:
        a_ele = child.find('a')
        href = biqukan_url + a_ele.get('href')
        book_urls.append(href)
    return book_urls


def find_type_block(index, name):
    book_urls = []
    # title = find_title(name)
    # container = title.find_next('div')
    container = find_container(index, name)
    top = container.find('div', class_='top').find('a')
    top_href = top.get('href')
    book_urls.append(biqukan_url + top_href)
    others = container.find_all('li')
    for other in others:
        a_ele = other.find('a')
        href = biqukan_url + a_ele.get('href')
        book_urls.append(href)
    return book_urls


def find_new_update_block(index):
    book_urls = []
    container = find_container(index, re.compile(u'.*最近更新小说列表'))
    for child in container.children:
        a_ele = child.find_all('a')
        href = biqukan_url + a_ele[0].get('href')
        book_urls.append(href)
    return book_urls


def find_new_storage_block(index):
    book_urls = []
    container = find_container(index, '最新入库小说')
    for child in container.children:
        a_ele = child.find('a')
        href = biqukan_url + a_ele.get('href')
        book_urls.append(href)
    return book_urls


def download_book(book_url, bf):
    dl = downloader(book_url, bf)
    dl.start()


def writer(path, name, text):
    with codecs.open(path, 'a', 'utf-8') as f:
        f.write(name + '\n')
        f.writelines(text)
        f.write('\n\n')


def request_get(url):
    count = 0
    while count < 10:
        try:
            res = requests.get(url, timeout=timeout)
            return res.text
        except Exception as e:
            LOG.exception(e)
            count += 1
            time.sleep(30)


def ensure_path(path):
    dir_path = os.path.dirname(path)
    if dir_path != '/' and dir_path != '':
        ensure_path(dir_path)
        if not os.path.exists(dir_path):
            os.mkdir(dir_path)


class downloader(object):

    def __init__(self, url, bfilter):
        self.target = url
        self.urls = []
        self.bfilter = bfilter
        self._init()
        self._path = u'%s/%s/%s/%s/%s.txt' % (
                        base_dir, self.book_type, self.book_status, self.book_author, self.book_name)
        ensure_path(self._path)
        if self.book_status == u'完结' and os:
            old_path = u'%s/%s/%s/%s/%s.txt' % (
                        base_dir, self.book_type, u'连载', self.book_author, self.book_name)
            if os.path.exists(old_path):
                shutil.move(old_path, self._path)

        LOG.info('download %s to %s', self.book_name, self._path)
        self.f = codecs.open(self._path, 'a', 'utf-8')
        self.writer(u'简介', self.book_intro)

    def _get_book_info(self, bf_view):
        book_info_div = bf_view.find('div', class_='info')
        self.book_name = book_info_div.find('h2').string
        book_info_spans = book_info_div.find('div', class_='small').find_all('span')
        self.book_author = book_info_spans[0].string.split(u'：')[1]
        self.book_type = book_info_spans[1].string.split(u'：')[1]
        self.book_status = book_info_spans[2].string.split(u'：')[1]
        for i, string in enumerate(bf_view.find('div', class_='intro').stripped_strings):
            if i == 1:
                self.book_intro = string
        LOG.info(u'类型:{} 名称:{} 状态:{} 作者:{}'.format(self.book_type, self.book_name, self.book_status, self.book_author))

    def _init(self):
        res = request_get(self.target)
        bf_view = BeautifulSoup(res, features=features)
        self._get_book_info(bf_view)
        div_bf = bf_view.find('div', class_='listmain')
        div_bf_2 = BeautifulSoup(str(div_bf), features=features)
        content_e = div_bf_2.find('dt', text=content_f)
        a = content_e.find_all_next('a')
        for each in a:
            self.urls.append((each.string, biqukan_url + each.get('href')))

    def get_contents(self, target):
        res = request_get(target)
        bf = BeautifulSoup(res, features=features)
        texts = bf.find_all('div', class_='showtxt')
        if texts:
            texts = texts[0].get_text('\n  ', strip=True)
            texts = texts.rstrip(u'\n  请记住本书首发域名：www.biqukan.com。笔趣阁手机版阅读网址：m.biqukan.com')
            texts = '  ' + texts.rstrip('\n  ' + target)
            return texts
        return ''

    def writer(self, name, text):
        self.f.write(name + '\n')
        self.f.writelines(text)
        self.f.write('\n\n')

    def start(self):
        LOG.info(u'开始下载<<%s>>:' % self.book_name)
        length = len(self.urls)
        count = 0
        for i, (section_name, url) in enumerate(self.urls):
            if not self.bfilter.add(url):
                text = self.get_contents(url)
                self.writer(section_name, text)
                percent = (float(i + 1) / float(length) * 100)
                count += 1
                if count % 10 == 0:
                    LOG.info(u" <<%s>> 已下载:%.2f%% 下载%s章 总共%s章" % (self.book_name, percent, i + 1, length) + '\r')
        LOG.info(u'下载<<%s>>完成' % self.book_name)
        self.close()

    def close(self):
        self.f.close()


def start():
    res = request_get(biqukan_url)
    index = BeautifulSoup(res, features=features)

    if os.path.exists(bf_file):
        LOG.info('bs from file')
        bf = BloomFilter.fromfile(open(bf_file, 'r'))
    else:
        LOG.info('init bs')
        bf = BloomFilter(500000)

    try:
        book_urls = find_wanben()
        book_urls += find_new_storage_block(index)
        book_urls += find_recommend_block(index, u'强力推荐')
        book_urls += find_type_block(index, u'玄幻小说')
        book_urls += find_type_block(index, u'修真小说')
        book_urls += find_type_block(index, u'都市小说')
        book_urls += find_type_block(index, u'穿越小说')
        book_urls += find_type_block(index, u'网游小说')
        book_urls += find_type_block(index, u'科幻小说')
        book_urls += find_new_update_block(index)
        book_urls += find_wanben()
        book_num = len(book_urls)
        start = time.time()
        for i, url in enumerate(book_urls[:10]):
            download_book(url, bf)
            LOG.info(u'已经下载%s本，剩余%s本', i+1, book_num - i -1)
            # time.sleep(30)

        print '%s' % (time.time() - start)
        LOG.info(u'下载完成')
    except Exception as e:
        LOG.exception(e)
    finally:
        bf.tofile(open(bf_file, 'w'))


if __name__ == '__main__':
    start()

