# -*- coding:UTF-8 -*-
from bs4 import BeautifulSoup
import requests, sys
import re
import time
from pybloom import BloomFilter
import os
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

features = 'lxml'


url = 'https://www.biqukan.com'
wan_ben_url = 'https://www.biqukan.com/wanben'
bf_file = 'ikantxt2'
base_dir = u'/downloads/小说'
# base_dir = u'小说'
content_f = re.compile(u'.*正文卷')

req = requests.get(url = url, timeout=10)
html = req.text
index = BeautifulSoup(html, features=features)

if os.path.exists(bf_file):
    LOG.info('bs from file')
    bf = BloomFilter.fromfile(open(bf_file, 'r'))
else:
    LOG.info('init bs')
    bf = BloomFilter(500000)


def find_title(name):
    return index.find('h2', text=name)


def find_container(name):
    return index.find('h2', text=name).find_next()


def find_wanben():
    book_urls = []
    req = requests.get(url=wan_ben_url)
    html = req.text
    wan_ben = BeautifulSoup(html, features=features)
    container = wan_ben.find('h2', text='好看的完本小说小说最近更新列表').find_next()
    for child in container.children:
        type = child.find('span', 's1').string + u'(完本)'
        a_ele = child.find('a')
        name = a_ele.string
        href = url + a_ele.get('href')
        author = child.find('span', 's4').string
        LOG.info(u'类型:{} 名称:{} 链接:{} 作者:{}'.format(type, name, href, author))
        book_urls.append((type, name, author, href))

    hot_bd = wan_ben.find('div', class_='hot bd')
    items = hot_bd.find_all('div', class_='item')
    for item in items:
        type = u'unknown(完本)'
        a_ele = item.find('a')
        href = url + a_ele.get('href')
        name = item.find('img').get('alt')
        author = 'unknown'
        LOG.info(u'类型:{} 名称:{} 链接:{} 作者:{}'.format(type, name, href, author))
        book_urls.append((type, name, author, href))
    return book_urls


def find_recommend_block(name):
    book_urls = []
    # block = index.find('h2', text=name)
    # a_container = block.find_next('ul')
    a_container = find_container(name)
    for child in a_container.children:
        type = child.find('span', 's1').string
        a_ele = child.find('a')
        name = a_ele.string
        href = url + a_ele.get('href')
        author = child.find('span', 's5').string
        LOG.info(u'类型:{} 名称:{} 链接:{} 作者:{}'.format(type, name, href, author))
        book_urls.append((type, name, author, href))
    return book_urls


def find_type_block(name):
    book_urls = []
    # title = find_title(name)
    # container = title.find_next('div')
    container = find_container(name)
    top = container.find('div', class_='top').find('a')
    top_href = top.get('href')
    LOG.info(u'top:{} url:{}'.format(top.img.get('alt'), url + top_href))
    book_urls.append((name, top.img.get('alt'), 'unknown', url + top_href))
    others = container.find_all('li')
    for other in others:
        a_ele = other.find('a')
        href = url + a_ele.get('href')
        book_name = a_ele.get('title')
        author = a_ele.next_sibling.lstrip('/')
        LOG.info(u'类型:{} 名称:{} 链接:{} 作者:{}'.format(name, book_name, href, author))
        book_urls.append((name, book_name, author, href))
    return book_urls


def find_new_update_block():
    book_urls = []
    container = find_container(re.compile(u'.*最近更新小说列表'))
    for child in container.children:
        type = child.find('span', 's1').string
        a_ele = child.find_all('a')
        name = a_ele[0].string
        href = url + a_ele[0].get('href')
        author = child.find('span', 's4').string
        section_name = a_ele[1].string
        section_href = url + a_ele[1].get('href')
        LOG.info(u'类型:{} 名称:{} 链接:{} 作者:{} 章节:{} 章节链接:{}'.format(type, name, href, author, section_name, section_href))
        book_urls.append((type, name, author, href, section_name, section_href))
    return book_urls


def find_new_storage_block():
    book_urls = []
    container = find_container('最新入库小说')
    for child in container.children:
        book_type = child.find('span', 's1').string
        a_ele = child.find('a')
        name = a_ele.string
        href = url + a_ele.get('href')
        author = 'unknown'
        LOG.info(u'类型:%s 名称:%s 链接:%s 作者:%s' % (book_type, name, href, author))
        book_urls.append((book_type, name, author, href))
    return book_urls


def download_book(type, name, author, url):
    dl = downloader(type, name, author, url, bf)
    dl.start()


def download_new_section(type, name, author, url):
    while True:
        try:
            req = requests.get(url=url)
            break
        except:
            print(url)
            time.sleep(30)

    html = req.text
    bf = BeautifulSoup(html, features=features)
    texts = bf.find_all('div', class_='showtxt')
    if texts:
        texts = texts[0].text.replace('\xa0' * 8, '\n').replace('<br>', '').replace('</br>', '')
        writer('%s%s%s' % (type, author, name), name, texts)


def writer(path, name, text):
    with codecs.open(path, 'a', 'utf-8') as f:
        f.write(name + '\n')
        f.writelines(text)
        f.write('\n\n')


class downloader(object):

    def __init__(self, type, name, author, url, bfilter):
        self.server = 'https://www.biqukan.com'
        self.target = url
        self.type = type
        self.name = name
        self.author = author
        self.urls = []
        self.bfilter = bfilter
        if not os.path.exists(base_dir):
            os.mkdir(base_dir)

        type_path = '%s/%s' % (base_dir, type)
        if not os.path.exists(type_path):
            os.mkdir(type_path)
        book_path = '%s/%s' % (type_path, author)
        if not os.path.exists(book_path):
            os.mkdir(book_path)
        LOG.info('download %s to %s/%s.txt', name, book_path, name)
        self.f = codecs.open(u'%s/%s.txt' % (book_path, name), 'a', 'utf-8')

    def get_download_url(self):
        req = requests.get(url = self.target)
        html = req.text
        div_bf = BeautifulSoup(html, features=features).find('div', class_='listmain')
        div_bf_2 = BeautifulSoup(str(div_bf), features=features)
        content_e = div_bf_2.find('dt', text=content_f)
        a = content_e.find_all_next('a')
        for each in a:
            self.urls.append((each.string, self.server + each.get('href')))

    def get_contents(self, target):
        while True:
            try:
                req = requests.get(url=target, timeout=10)
                break
            except:
                LOG.warn(target)
                time.sleep(30)

        html = req.text
        bf = BeautifulSoup(html, features=features)
        texts = bf.find_all('div', class_ = 'showtxt')
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
        self.get_download_url()
        LOG.info(u'开始下载%s:' % self.name)
        length = len(self.urls)
        for i, (section_name, url) in enumerate(self.urls):
            if not self.bfilter.add(url):
                LOG.info('section_name:[%s], url:[%s]' % (section_name, url))
                text = self.get_contents(url)
                self.writer(section_name, text)
                LOG.info(u"  已下载:%.2f%% 下载%s章 总共%s章" % (float(i + 1) / float(length) * 100, i + 1, length) + '\r')
            else:
                LOG.info('section_name:%s, url:%s' % (section_name, url))
                LOG.info(u"  已下载:%.2f%% 已下载%s章 总共%s章" % (float(i + 1) / float(length) * 100, i + 1, length) + '\r')
        LOG.info(u'下载<<%s>>完成' % self.name)
        self.close()

    def close(self):
        self.f.close()


def start():
    try:
        book_urls = find_new_storage_block()
        book_urls += find_recommend_block(u'强力推荐')
        book_urls += find_type_block(u'玄幻小说')
        book_urls += find_type_block(u'修真小说')
        book_urls += find_type_block(u'都市小说')
        book_urls += find_type_block(u'穿越小说')
        book_urls += find_type_block(u'网游小说')
        book_urls += find_type_block(u'科幻小说')
        book_urls += find_wanben()
        new_updates = find_new_update_block()
        book_num = len(book_urls) + len(new_updates)
        for i, (type, name, author, url) in enumerate(book_urls[:1]):
            download_book(type, name, author, url)
            LOG.info(u' %s 下载完成 已经下载%s本，剩余%s本', name, i+1, book_num - i -1)
            time.sleep(30)

        finished = len(book_urls)
        for i, (type, name, author, href, section_name, section_href) in enumerate(new_updates):
            download_book(type, name, author, href)
            LOG.info(u' %s 下载完成 已经下载%s本，剩余%s本', name, finished + i + 1, book_num - i - 1 - finished)
            time.sleep(30)
        LOG.info(u'下载完成')
    except Exception as e:
        LOG.exception(e)
    finally:
        bf.tofile(open(bf_file, 'w'))


if __name__ == '__main__':
    try:
        book_urls = find_new_storage_block()
        book_urls += find_recommend_block(u'强力推荐')
        book_urls += find_type_block(u'玄幻小说')
        new_updates = find_new_update_block()
        book_num = len(book_urls) + len(new_updates)
        for i, (type, name, author, url) in enumerate(book_urls):
            download_book(type, name, author, url)
            LOG.info(u' %s 下载完成 已经下载%s本，剩余%s本', name, i + 1, book_num - i - 1)
            time.sleep(30)

        finished = len(book_urls)
        for i, (type, name, author, href, section_name, section_href) in enumerate(new_updates):
            download_book(type, name, author, href)
            LOG.info(u' %s 下载完成 已经下载%s本，剩余%s本', name, finished + i + 1, book_num - i - 1 - finished)
            time.sleep(30)
        LOG.info(u'下载完成')
        bf.tofile(open(bf_file, 'w'))
    except Exception as e:
        LOG.exception(e)
    finally:
        bf.tofile(open(bf_file, 'w'))

