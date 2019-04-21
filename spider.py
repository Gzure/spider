# -*- coding:UTF-8 -*-
from flask import Flask
from flask_apscheduler import APScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
from logging.handlers import RotatingFileHandler
import logging
import codecs
from flask import request, Response, session, redirect
from flask_apscheduler.json import jsonify
from apscheduler.jobstores.base import ConflictingIdError, JobLookupError
import os
import commands
from datetime import timedelta
from apscheduler.events import EVENT_ALL

logging.basicConfig()
logging.getLogger('apscheduler').setLevel(logging.DEBUG)

app = Flask('spider', static_url_path='',
            static_folder='static')
scheduler = APScheduler()

DEBUG = 10
INFO = 20


user = 'admin'
password = 'admin'

LOG = app.logger
app.config['SECRET_KEY']= os.urandom(24)
app.config['PERMANENT_SESSION_LIFETIME']=timedelta(days=1)

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

    def my_listener(event):
        LOG.info('get scheduler event %s', event)

    scheduler.add_listener(my_listener, EVENT_ALL)

    # scheduler.add_job('crawl ikan', 'crawlers.ikantxt2:start', trigger='interval', seconds=8000)


@app.before_request
def login_filter():
    path = str(request.path)
    if path.startswith('/login') or path.startswith('/css') or path.startswith('/js') or path.startswith('/img'):
        return
    if 'username' in session:
        return
    return redirect('/login.html')


@app.route('/login', methods=['POST'])
def login():
    login_info = request.form
    if login_info['name'] == user and login_info['password'] == 'admin':
        session['username'] = login_info['name']
        return redirect('/index.html')


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
    task = request.form.copy().to_dict()
    if script:
        path = 'crawlers/' + script.filename
        script.save(path)
    else:
        del task['script']

    depends = task.get('depends', None)
    if depends:
        for depend in depends.split(','):
            c_o = commands.getoutput('pip install %s' % depend)
            LOG.info('c_o:%s', c_o)
    del task['depends']

    trigger_value = task['trigger_value']
    trigger_dict = {}
    for entry in trigger_value.split(','):
        key, value = entry.split(':', 1)
        trigger_dict[key] = int(value) if value.isdigit() else value

    del task['trigger_value']
    task.update(trigger_dict)

    try:
        if scheduler.get_job(task['id']):
            scheduler.modify_job(task['id'], **task)
            job = scheduler.get_job(task['id'])
        else:
            job = scheduler.add_job(**task)
        return redirect('/index.html')
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
    app.run('0.0.0.0', 8888, debug=False)



