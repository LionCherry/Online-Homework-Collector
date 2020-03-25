#!/usr/bin/env python3
'''
The main app for website server.
'''

import signal
import sys
import os
import logging.config
import time
import datetime
import mimetypes
import flask
import flask_login
from utils import (json_response, succ, fail)

from monitor import Monitor
from homework import User

app = flask.Flask(
	__name__,
	static_folder='./static')
	

##########
# Terminate
def terminate_app(signum, frame):
	if monitor:
		monitor.terminate()
		app.logger.info('Monitor terminate')
	#close_persistence(None)
	sys.exit()


##########
# Setup
login_manager = flask_login.LoginManager() 
login_manager.login_view = "login"
monitor = None

def setup_monitor(app):
	'''
	setup the monitor
	'''
	global monitor
	monitor = Monitor(
		app.config['DB_USER'],
		app.config['DB_HOMEWORK'],
		app.config['DB_STATU']
	)
	# setup the singal
	for sig in [signal.SIGINT, signal.SIGTERM]:
		signal.signal(sig, terminate_app)
def setup_app(app, argv):
	app.config.from_object('default_settings')
	for db in ['DB_USER', 'DB_HOMEWORK', 'DB_STATU']:
		app.config[db] = os.path.join(argv[1], app.config[db])
	app.config['FILE_SAVE_DIR'] = argv[2]
		
	app.logger.addHandler(logging.StreamHandler())
	app.logger.setLevel(logging.DEBUG)
	# app.logger.info('STATIC_VERSION = {}'.format(app.config['STATIC_VERSION']))
	login_manager.init_app(app)
	app.secret_key = 'homework'
	setup_monitor(app)

##########
# Page
@login_manager.user_loader 
def load_user(user_id): 
	global monitor
	return monitor.load_user(user_id)
@app.route('/login', methods=['GET', 'POST'])
def login():
	global monitor
	msg = ''
	user = flask_login.current_user
	if user.is_authenticated:
		return flask.redirect('/home')
	if flask.request.method == 'POST':
		id, pwd = flask.request.form['id'], flask.request.form['pwd']
		app.logger.info('login...(%s,%s)'%(id, pwd))
		user = monitor.load_user(id)
		if user is None:
			msg =  'id error!'
		elif user.pwd == pwd:
			flask_login.login_user(user)
			app.logger.info('login success (%s,%s,%s)'%(user.id,user.pwd,user.name))
			flask.session.permanent = True
			app.permanent_session_lifetime = app.config['SESSON_LIFETIME']
			return flask.redirect('home')
		else:
			msg = 'password error!'
		app.logger.info('     ...fail (%s)'%msg)
	return flask.render_template(
		'login.html',
		msg=msg,
		form=flask.request.form
	)
@app.route('/logout', methods=['GET', 'POST'])
def logout():
	user = flask_login.current_user
	app.logger.info('logout (%s)'%user.get_id())
	flask_login.logout_user()
	return flask.redirect('login')
@app.route('/modify_pwd', methods=['GET', 'POST'])
def modify_pwd():
	global monitor
	msg = ''
	user = flask_login.current_user
	if flask.request.method == 'POST':
		id, pwd, new_pwd = flask.request.form['id'], flask.request.form['pwd'], flask.request.form['new_pwd']
		app.logger.info('modify_pwd...(%s,%s->%s)'%(id, pwd, new_pwd))
		user = monitor.load_user(id)
		if user is None:
			msg =  'id error!'
		elif user.pwd == pwd:
			if not new_pwd:
				msg = 'new password error!'
			else:
				user.pwd = new_pwd
				app.logger.info('modify_pwd success (%s,%s,%s)'%(user.id,user.pwd,user.name))
				return flask.redirect('login')
		else:
			msg = 'password error!'
		app.logger.info('     ...fail (%s)'%msg)
	return flask.render_template(
		'modify_pwd.html',
		msg=msg,
		form=flask.request.form
	)

@app.route('/home', methods=["GET"])
@flask_login.login_required
def home():
	try:
    	# load user
		user = flask_login.current_user
		if not user.is_authenticated:
			return flask.redirect('/login')
		user_id = user.get_id()
		global monitor
		user = monitor.load_user(id=user_id)
		if not user:
			raise IOError('未找到用户(%s)' % user_id)
		# load user end
		hss = monitor.load_homework_statu(user_id=user_id)
		hss = [{
			'id': hs[0].id,
			'time': hs[0].time,
			'timestamp': hs[0].get_timestamp(),
			'allow_ext_list': hs[0].allow_ext_list,
			'name': hs[0].name,
			'description_list': hs[0].description.split('\\n'),
			# 'description_height': 24 + 20 * len(hs[0].description.split('\\n')),
			'score': hs[1].score if hs[1] is not None else '',
			'comment': hs[1].comment if hs[1] is not None else '',
			'statu': hs[1].statu if hs[1] is not None else '',
		} for hs in hss]
		data = {
			'user': {'id': user.id, 'name': user.name},
			'hss': hss,
			# 'homework_list': monitor.load_homework(),
			# 'statu_list': monitor.load_statu(user_id=user.id),
			'now_timestamp': time.time(),
			**flask.request.args
		}
		return flask.render_template(
			'home.html',
			**data
		)
	except Exception as e:
		app.logger.exception('Exception: %s' % e)
		msg = '请重新登录(%s)' % e
	return flask.redirect(flask.url_for('login', msg = msg))

@app.route('/upload', methods=["POST"])
@flask_login.login_required
def upload():
	replace = False
	try:
		try:
			file = flask.request.files['file']
		except:
			raise IOError('文件不符合要求，请确保大小小于1MB')
		if file.filename.find('.') < 0:
			raise IOError('文件需要有拓展名')
		ext = file.filename.rsplit('.', 1)[1].lower()
		# if ext not in app.config['HOMEWORK_ALLOW_EXT']:
		# 	raise IOError('文件拓展名需要在该范围内(%s)'%(','.join(app.config['HOMEWORK_ALLOW_EXT'])))
		# load user
		user = flask_login.current_user
		if not user.is_authenticated:
			return flask.redirect('/login')
		user_id = user.get_id()
		global monitor
		user = monitor.load_user(id=user_id)
		if not user:
			raise IOError('未找到用户(%s)' % user_id)
		# load user end
		homework_id = flask.request.form['homework_id']
		homework = monitor.load_homework(homework_id)
		if not homework:
			raise IOError('未选中作业(%s)' % homework_id)
		allow_ext_list = homework.allow_ext_list.split(',')
		if not allow_ext_list or ('all' in allow_ext_list or 'ALL' in allow_ext_list or 'All' in allow_ext_list):
			allow_ext_list = app.config['HOMEWORK_ALLOW_EXT']
		if ext not in allow_ext_list:
			raise IOError('文件拓展名需要在规定范围内(%s)'%(','.join(allow_ext_list)))
		statu = monitor.load_statu(user_id=user_id, homework_id=homework_id)
		if not statu:
			statu = monitor.create_statu(user_id=user_id, homework_id=homework_id)
		app.logger.info("upload user(%s) homework(%s) [%s]file(%s)" % (user_id, homework_id, ext, file.filename))
		path = os.path.join(
			app.config['FILE_SAVE_DIR'],
			homework_id)
		if not os.path.exists(path): os.makedirs(path)
		filename = '%s.%s' % (user_id, ext)
		filepath = os.path.join(path, filename)
		if statu.statu == '已提交' and os.path.exists(os.path.join(path, statu.filename)):
			app.logger.warning("      will replace the file(%s)" % statu.filename)
			os.remove(os.path.join(path, statu.filename))
			replace = True
		file.save(filepath)
		if not os.path.exists(filepath):
			app.logger.exception('No Exists: %s' % filepath)
			raise IOError('文件未储存')
		# update in statu
		if time.time() > homework.get_timestamp():
			# raise IOError('已过提交时间(截止时间%s)' % (homework.time))
			if statu.statu in [None, '', '未提交', '已补交']:
				statu.statu = '已补交'
				msg = '补交成功' if not replace else '补交替换成功'
			else:
				statu.statu = '已提交'
				msg = '提交成功' if not replace else '替换成功'
		else:
			statu.statu = '已提交'
			msg = '提交成功' if not replace else '替换成功'
		statu.filename = filename
	except Exception as e:
		app.logger.exception('Exception: %s' % e)
		msg = '上传失败(%s)' % e
	app.logger.info('redirect msg=%s'%msg)
	return flask.redirect(flask.url_for('home', msg = msg))
	
@app.route('/download', methods=["POST"])
@flask_login.login_required
def download():
	try:
		# load user
		user = flask_login.current_user
		if not user.is_authenticated:
			return flask.redirect('/login')
		user_id = user.get_id()
		global monitor
		user = monitor.load_user(id=user_id)
		if not user:
			raise IOError('未找到用户(%s)' % user_id)
		# load user end
		homework_id = flask.request.form['homework_id']
		homework = monitor.load_homework(homework_id=homework_id)
		if not homework:
			raise IOError('未找到作业(%s)' % homework_id)
		path = os.path.join(
			app.config['FILE_SAVE_DIR'],
			homework_id)
		statu = monitor.load_statu(user_id=user_id, homework_id=homework_id)
		if not statu:
			raise IOError('未找到作业提交状态(%s, %s)' % (user_id, homework_id))
		if statu.statu == '未提交':
			raise IOError('未提交')
		filename = statu.filename
		filepath = os.path.join(path, filename)
		if not filename or not os.path.exists(filepath):
			app.logger.exception('No Exists: %s' % filepath)
			raise IOError('未找到文件(%s)' % filename)
		ext = filename.rsplit('.', 1)[1].lower()
		app.logger.info("download user(%s) homework(%s) [%s]file(%s) from path: %s" % (user_id, homework_id, ext, filename, filepath))
		download_filename = '(%s)%s.%s' % (user.name, homework.name, ext)
		return flask.send_file(
			filepath,
			mimetype=mimetypes.guess_type(filename)[0],
			attachment_filename=download_filename,
			as_attachment=True
		)
	except Exception as e:
		app.logger.exception('Exception: %s' % e)
		msg = '下载失败(%s)' % e
	return flask.redirect(flask.url_for('home', msg = msg))
##########
# Data URL
@app.route('/<string:page>', methods=["GET"], defaults={'page': 'index'})
@json_response()
def index(page):
	args = flask.request.get_json()
	app.logger.info(args)
	try:
		data = args
		return succ(data=data)
	except Exception as e:
		app.logger.exception('Exception: ')
		return fail(msg=str(e))



setup_app(app, sys.argv)

if __name__ == "__main__":
	app.run(host="0.0.0.0", port=app.config["PORT"], threaded=True)
