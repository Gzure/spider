# -*- coding:UTF-8 -*-
from bs4 import BeautifulSoup
import requests, sys
import re
import base64
import json

filter_a = re.compile('.*\d.html')
magnet = re.compile('^magnet:?.*')
ftp = re.compile('^ftp:.*')

filter_words = re.compile('获奖|奇幻|科幻|恐怖|悬疑|冒险|动作')

url = 'https://www.dytt8.net/'

features = 'html.parser'

transimission_api = 'http://gzure.tpddns.cn:9091/transmission/rpc'

def get_download_urls():
    res = requests.get(url=url)
    res.encoding = 'gb2312'
    index = res.text

    bs = BeautifulSoup(index, features=features)

    # 左侧区域
    # bd3l = bs.find_all('div', class_='bd3l')
    # 右侧区域
    bd3r = bs.find_all('div', class_='bd3r')

    first_bd3r = BeautifulSoup(str(bd3r[0]), features=features)
    # print(first_bd3r)
    co_area2s = first_bd3r.find_all('div', class_='co_area2')
    # print(co_area2s)
    co_area2 = BeautifulSoup(str(co_area2s[0]), features=features)

    hrs = co_area2.find_all('a', href=filter_a, text=filter_words)
    magnets = []
    ftps = []
    for hr in hrs:
        res = requests.get(url+hr.get('href'))
        res.encoding = 'gb2312'
        movie_page = BeautifulSoup(res.text, features=features)
        magnet_h = movie_page.find('a', href=magnet)

        ftp_h = movie_page.find(text=ftp)
        print('name: %s,\nmagnet: %s,\nftp: %s\n' % (hr.string, magnet_h.get('href'), ftp_h))
        magnets.append(magnet_h.get('href'))
        ftps.append(ftp_h)

    return magnets, ftps


def get_basic_auth_str(username, password):
    temp_str = username + ':' + password
    bytes_string = temp_str.encode(encoding="utf-8")
    encode_str = base64.b64encode(bytes_string)
    return 'Basic ' + encode_str.decode()

def get_session_id():
    headers = {'Authorization': get_basic_auth_str('zuo', 'zhang0814')}
    res = requests.post(transimission_api, headers=headers)
    bs = BeautifulSoup(res.text, features=features)
    session_id = bs.find('code')
    name, value = session_id.string.split(':')
    return name, value.strip()

def add_torrent_tasks(magnets):
    session_name, session_value = get_session_id()
    headers = {
        'Authorization': get_basic_auth_str('zuo', 'zhang0814'),
        session_name: session_value
    }

    for magnet_d in magnets:
        print('add torrent %s' % magnet_d)
        params = {
            'method': 'torrent-add',
            'arguments': {
                'download-dir': '/volume2/downloads',
                'filename': magnet_d,
                'paused': False
            }
        }
        res = requests.post(transimission_api, headers=headers, data=json.dumps(params))
        print(res.text)
        print(res.status_code)

if __name__ == '__main__':
    magnets, _ = get_download_urls()
    add_torrent_tasks(magnets)