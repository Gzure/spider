# -*- coding:UTF-8 -*-
from flask import Flask
from flask_apscheduler import APScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
from logging.handlers import RotatingFileHandler
import logging
import codecs
from flask import request, Response
from flask_apscheduler.json import jsonify
from apscheduler.jobstores.base import ConflictingIdError, JobLookupError
import os

app = Flask('spider', static_path='', static_url_path=None,
            static_folder='static')
scheduler = APScheduler()

DEBUG = 10
INFO = 20


LOG = app.logger
app.static_folder = 'static'


# init log
def init_log():
    app.config['info'] = True
    fmt = '%(asctime)s %(levelname)s %(module)s[line:%(lineno)d] %(message)s'
    format_str = logging.Formatter(fmt=fmt)
    file_log_hdr = RotatingFileHandler('spider.log', maxBytes=1024 * 1024 * 10, encoding='utf-8')
    file_log_hdr.setLevel(DEBUG)
    file_log_hdr.setFormatter(format_str)
    app.logger.addHandler(file_log_hdr)
    app.logger.setLevel(INFO)


# init secheduler
def init_secheduler():
    app.config['SCHEDULER_API_ENABLED'] = True
    app.config['SCHEDULER_EXECUTORS'] = {'default': ThreadPoolExecutor(2)}
    scheduler.init_app(app)
    scheduler.start()

    # scheduler.add_job('crawl ikan', 'crawlers.ikantxt2:start', trigger='interval', seconds=8000)


@app.route('/script/upload', methods=['POST'])
def upload_script():
    pass


@app.route('/log')
def log_detail():
    f = codecs.open('spider.log', 'r', 'utf-8')
    lines = f.readlines(1000)
    f.close()
    return jsonify(lines)


@app.route('/filter/add', methods=['POST'])
def add_filter():
    pass


@app.route('/filter/<string:name>/update', methods=['POST'])
def update_filter():
    pass


@app.route('/filter/<string:name>/del')
def del_filter():
    pass


@app.route('/task/add', methods=['POST'])
def add_task():
    """
    :param url: str target url
    :param name: task name
    :param url_type: desc info
    :param script: python script for handler url response
    :param start method: script scheduler method
    :param depends: requirments txt
    :param scheduler_type: interval or cron
    :return:
    """
    script = request.files.get('script')
    if script:
        path = 'crawlers/' + script.filename
        script.save(path)

    task = request.form.copy().to_dict()

    for key, value in task.items():
        print key
        print value
        if value.isdigit():
            task[key] = int(value)

    try:
        if scheduler.get_job(task['id']):
            scheduler.modify_job(task['id'], **task)
            job = scheduler.get_job(task['id'])
        else:
            job = scheduler.add_job(**task)
        return jsonify(job)
    except ConflictingIdError:
        return jsonify(dict(error_message='Job %s already exists.' % task.get('id')), status=409)
    except Exception as e:
        LOG.exception(e)
        return jsonify(dict(error_message=str(e)), status=500)


@app.route('/task/<string:name>/update', methods=['POST'])
def update_task(name):
    scheduler.remove_job(name)
    script = request.files.get('script')
    if not script:
        return jsonify(dict(error_message='script file can not be none.'), status=409)

    path = 'crawlers/' + script.filename
    script.save(path)

    task = request.form.copy().to_dict()

    for key, value in task.items():
        print key
        print value
        if value.isdigit():
            task[key] = int(value)

    try:
        job = scheduler.add_job(**task)
        return jsonify(job)
    except ConflictingIdError:
        return jsonify(dict(error_message='Job %s already exists.' % task.get('id')), status=409)
    except Exception as e:
        LOG.exception(e)
        return jsonify(dict(error_message=str(e)), status=500)


if __name__ == '__main__':
    init_log()
    init_secheduler()
    app.run('127.0.0.1', '8888')



