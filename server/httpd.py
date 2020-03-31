#!/usr/bin/env python3
'''
The main app for website server.
'''

import signal
import sys
import os
import time
import datetime
import mimetypes
import flask
import flask_login
import logging
from utils import (json_response, succ, fail, fix)

from monitor import Monitor
from homework import User
from judger import read_file, EX

app = flask.Flask(
	__name__,
	static_folder='./static')


def get_allow_ext_list(allow_ext_list):
	if not allow_ext_list or ('all' in allow_ext_list or 'ALL' in allow_ext_list or 'All' in allow_ext_list):
		return app.config['HOMEWORK_ALLOW_EXT']
	return allow_ext_list
	

##########
# Terminate
def terminate_app(signum, frame):
	if monitor:
		monitor.terminate()
		logger.info('Monitor terminate')
	#close_persistence(None)
	sys.exit()


##########
# Setup
login_manager = flask_login.LoginManager() 
login_manager.login_view = "login"
monitor = None
logger = logging

def setup_monitor(app):
	global monitor
	monitor = Monitor(
		app.config['DB_USER'],
		app.config['DB_HOMEWORK'],
		app.config['DB_STATU'],
		app.config['DB_JUDGE'],
		file_judge_dir=app.config['FILE_JUDGE_DIR'],
		file_save_dir=app.config['FILE_SAVE_DIR']
	)
	# setup the singal
	for sig in [signal.SIGINT, signal.SIGTERM]:
		signal.signal(sig, terminate_app)

def setup_app(app, argv):
	app.config.from_object('default_settings')
	for db in ['DB_USER', 'DB_HOMEWORK', 'DB_STATU', 'DB_JUDGE']:
		app.config[db] = os.path.join(argv[1], app.config[db])
	app.config['FILE_SAVE_DIR'] = argv[2]
	app.config['FILE_JUDGE_DIR'] = argv[3]

	app.logger.addHandler(logging.StreamHandler())
	app.logger.setLevel(logging.DEBUG)
	# logger.info('STATIC_VERSION = {}'.format(app.config['STATIC_VERSION']))
	global logger
	logger = app.logger

	login_manager.init_app(app)
	app.secret_key = 'homework'
	setup_monitor(app)

##########
# Login
@login_manager.user_loader 
def load_user(user_id):
	return monitor.load_user(user_id)
	
@app.route('/login/', methods=['GET', 'POST'])
def login():
	msg = ''
	user = flask_login.current_user
	data = {
		**flask.request.args,
		**flask.request.form,
	}
	if user.is_authenticated:
		return flask.redirect(flask.url_for('home', **data))
	if flask.request.method == 'POST':
		id, pwd = flask.request.form['id'], flask.request.form['pwd']
		logger.info('login...(%s,%s)'%(id, pwd))
		user = monitor.load_user(id)
		if user is None:
			msg =  'id error!'
		elif user.pwd == pwd:
			flask_login.login_user(user)
			logger.info('login success (%s,%s,%s)'%(user.id,user.pwd,user.name))
			flask.session.permanent = True
			app.permanent_session_lifetime = app.config['SESSON_LIFETIME']
			return flask.redirect('/home')
		else:
			msg = 'password error!'
		logger.info('     ...fail (%s)' % msg)
		data['msg'] = msg
	return flask.render_template(
		'login.html',
		**data,
	)
@app.route('/logout/', methods=['GET', 'POST'])
def logout():
	user = flask_login.current_user
	logger.info('logout (%s)'%user.get_id())
	flask_login.logout_user()
	return flask.redirect('/login')
@app.route('/modify_pwd/', methods=['GET', 'POST'])
def modify_pwd():
	msg = ''
	user = flask_login.current_user
	if flask.request.method == 'POST':
		id, pwd, new_pwd = flask.request.form['id'], flask.request.form['pwd'], flask.request.form['new_pwd']
		logger.info('modify_pwd...(%s,%s->%s)'%(id, pwd, new_pwd))
		user = monitor.load_user(id)
		if user is None:
			msg =  'id error!'
		elif user.pwd == pwd:
			if not new_pwd or new_pwd.find('\n')>=0 or new_pwd.find('\r')>=0 or new_pwd.find('\t')>=0:
				msg = 'new password error!'
			else:
				user.pwd = new_pwd
				logger.info('modify_pwd success (%s,%s,%s)'%(user.id,user.pwd,user.name))
				return flask.redirect('/login')
		else:
			msg = 'password error!'
		logger.info('     ...fail (%s)'%msg)
	return flask.render_template(
		'modify_pwd.html',
		msg=msg,
		form=flask.request.form
	)


def load_current_user(current_user, should_be_admin=False):
	if not current_user.is_authenticated:
		raise Exception('请重新登录')
	user_id = current_user.get_id()
	current_user = monitor.load_user(id=user_id)
	if not current_user:
		raise Exception('未找到用户(%s)' % user_id)
	is_admin = (current_user.id in app.config['ADMIN_ID'])
	if should_be_admin and not is_admin:
		raise Exception('无管理员权限')
	return current_user, is_admin

def login_required(should_be_admin=False, redirect='login', msg='请重新登录'):
	def _wrapper(f):
		@flask_login.login_required
		def _wrapper_f(*args, **kwargs):
			try:
				current_user, is_admin = load_current_user(flask_login.current_user,
					should_be_admin=should_be_admin)
				return f(current_user=current_user, is_admin=is_admin, *args, **kwargs)
			except Exception as e:
				logger.exception('Exception: %s' % e)
				return flask.redirect(flask.url_for(redirect, msg='%s(%s)'%(msg, e)))
		_wrapper_f.__name__ = f.__name__
		return _wrapper_f
	return _wrapper

##########
# Home
@app.route('/home/', methods=["GET"])
@login_required(should_be_admin=False, redirect='login', msg='请重新登录')
def home(current_user, is_admin):
	hss = monitor.load_homework_statu(user_id=current_user.id)
	hss = [{
		'id': h.id,
		'time': h.time,
		'timestamp': h.get_timestamp(),
		'allow_ext_list': ','.join(get_allow_ext_list(h.allow_ext_list.split(','))),
		'name': h.name,
		'description_list': h.description.split('\\n'),
		# 'description_height': 24 + 20 * len(homework.description.split('\\n')),
		'score': s.score if s is not None else '',
		'comment': s.comment if s is not None else '',
		'statu': s.statu if s is not None else '',
	} for h, s in hss]
	data = {
		'user': {
			'id': current_user.id,
			'name': current_user.name,
		},
		'hss': hss,
		# 'homework_list': monitor.load_homework(),
		# 'statu_list': monitor.load_statu(user_id=user.id),
		'now_timestamp': time.time(),
		**flask.request.args,
		**flask.request.form,
	}
	if is_admin:
		# calculate the number of users who submit the homework
		data['number_of_user'] = monitor.count_user()
		for hs in data['hss']:
			submit, comment = 0, 0
			for u, statu in monitor.load_user_statu(homework_id=hs['id']):
				if statu not in [None, '', '未提交']:
					submit += 1
					if not (statu.score == ''):
						comment += 1
			hs['number_of_submit'] = submit
			hs['number_of_comment'] = comment
		return flask.render_template(
			'admin/home.html',
			**data,
		)
	return flask.render_template(
		'home.html',
		**data,
	)

##########
# Upload & Download
@app.route('/upload/', methods=["POST"])
@login_required(should_be_admin=False, redirect='home', msg='上传失败')
def upload(current_user, is_admin):
	replace = False
	try:
		file = flask.request.files['file']
	except:
		raise IOError('文件不符合要求，请确保大小小于1MB')
	if file.filename.find('.') < 0:
		raise IOError('文件需要有拓展名')
	ext = file.filename.rsplit('.', 1)[1].lower()
	# if ext not in app.config['HOMEWORK_ALLOW_EXT']:
	# 	raise IOError('文件拓展名需要在该范围内(%s)'%(','.join(app.config['HOMEWORK_ALLOW_EXT'])))
	if is_admin and 'filename' in flask.request.form: # 管理员可以指定文件名
		filename = flask.request.form['filename']
		filename = fix(filename)
	else:
		filename = '%s.%s' % (current_user.id, ext)
	# load user end
	homework_id = flask.request.form['homework_id']
	homework = monitor.load_homework(homework_id)
	if not homework:
		raise Exception('未选中作业(%s)' % homework_id)
	allow_ext_list = homework.allow_ext_list.split(',')
	allow_ext_list = get_allow_ext_list(allow_ext_list)
	if ext not in allow_ext_list:
		raise IOError('文件拓展名需要在规定范围内(%s)'%(','.join(allow_ext_list)))
	statu = monitor.load_statu(user_id=current_user.id, homework_id=homework_id)
	if not statu:
		statu = monitor.create_statu(user_id=current_user.id, homework_id=homework_id)
	logger.info("upload user(%s) homework(%s) [%s]file(%s)" % (current_user.id, homework_id, ext, file.filename))
	path = os.path.join(
		app.config['FILE_SAVE_DIR'],
		homework_id)
	if not os.path.exists(path): os.makedirs(path)
	filepath = os.path.join(path, filename)
	if statu.statu == '已提交' and os.path.exists(os.path.join(path, statu.filename)):
		logger.warning("      will replace the file(%s)" % statu.filename)
		os.remove(os.path.join(path, statu.filename))
		replace = True
	file.save(filepath)
	if not os.path.exists(filepath):
		logger.exception('No Exists: %s' % filepath)
		raise IOError('文件未储存')
	# update in statu
	if time.time() > homework.get_timestamp():
		# raise Exception('已过提交时间(截止时间%s)' % (homework.time))
		if statu.statu in [None, '', '未提交']:
			statu.statu = '已补交'
			msg = '补交成功' if not replace else '补交替换成功'
		elif statu.statu in ['已补交']: # 已补交不能替换
			raise Exception('已过提交时间(截止时间%s)' % (homework.time))
		else: # 已提交不能替换
			raise Exception('已过提交时间(截止时间%s)' % (homework.time))
			# statu.statu = '已提交'
			# msg = '提交成功' if not replace else '替换成功'
	else:
		statu.statu = '已提交'
		msg = '提交成功' if not replace else '替换成功'
	statu.filename = filename
	statu.score, statu.comment = '', '' # 清空评语
	return flask.redirect(flask.url_for('home', msg='上传成功'))
	
@app.route('/download/', methods=["POST"])
@login_required(should_be_admin=False, redirect='home', msg='下载失败')
def download(current_user, is_admin):
	user = current_user
	if is_admin and 'user_id' in flask.request.form: # 管理员可以下载给定用户的文件
		user_id = flask.request.form['user_id']
		user = monitor.load_user(id=user_id)
		if not user:
			raise Exception('未找到用户(%s)' % user_id)
	# load user end
	homework_id = flask.request.form['homework_id']
	homework = monitor.load_homework(homework_id=homework_id)
	if not homework:
		raise Exception('未找到作业(%s)' % homework_id)
	path = os.path.join(
		app.config['FILE_SAVE_DIR'],
		homework_id)
	statu = monitor.load_statu(user_id=user.id, homework_id=homework_id)
	if not statu:
		raise IOError('未找到作业提交状态(%s, %s)' % (user.id, homework_id))
	if statu.statu in [None, '', '未提交']:
		raise IOError('未提交(%s, %s)' % (user.id, homework_id))
	filename = statu.filename
	filepath = os.path.join(path, filename)
	if not filename or not os.path.exists(filepath):
		logger.exception('No Exists: %s' % filepath)
		raise IOError('未找到文件(%s)' % filename)
	ext = filename.rsplit('.', 1)[1].lower()
	# logger.info("download user(%s) homework(%s) [%s]file(%s) from path: %s" % (user.id, homework_id, ext, filename, filepath))
	download_filename = '(%s)%s.%s' % (user.name, homework.name, ext)
	return flask.send_file(
		filepath,
		mimetype=mimetypes.guess_type(filename)[0],
		attachment_filename=download_filename,
		as_attachment=True
	)



##########
# Admin
def run_judge(user, statu, debug=logger.info):
	msg, compile_res, compile_msg = None, None, None
	try:
		monitor.judge(user=user, statu=statu, debug=debug)
		statu.score, statu.comment = '1', ''
		msg = '已自动批改(user:%s,homework:%s,score:%s,comment:%s)' % (statu.user_id, statu.homework_id, statu.score, statu.comment)
		debug(msg)
	except EX as ex:
		compile_res = ex.name()
		compile_msg = ex.test_msg
	except Exception as ex:
		compile_res = type(ex)
		compile_msg = ex
	return msg, compile_res, compile_msg
	
@app.route('/comment/<homework_id>/<user_id>', methods=["GET"])
@login_required(should_be_admin=True, redirect='login', msg='请重新登录')
def comment(current_user, is_admin, homework_id, user_id):
	homework = monitor.load_homework(homework_id)
	if not homework:
		raise Exception('未选中作业(%s)' % homework_id)
	data = {
		'user': {
			'id': current_user.id,
			'name': current_user.name,
			'isAdmin': is_admin
		},
		'homework': {
			'id': homework_id,
			'name': homework.name,
		},
		**flask.request.args,
		**flask.request.form,
	}
	# get the user
	user = monitor.load_user(id=user_id)
	if not user:
		raise Exception('未找到用户(%s)' % user_id)
	statu = monitor.load_statu(user_id=user_id, homework_id=homework_id)
	if not statu:
		raise IOError('未找到作业提交状态(%s, %s)' % (user_id, homework_id))
	if statu.statu in [None, '', '未提交']:
		raise IOError('未提交(%s, %s)' % (user_id, homework_id))
	content = ''
	ext = statu.filename.rsplit('.', 1)[1].lower()
	if ext in app.config['SHOW_ALLOW_EXT']:
		path = os.path.join(
			app.config['FILE_SAVE_DIR'],
			statu.homework_id)
		filepath = os.path.join(path, statu.filename)
		try:
			content = read_file(filepath)
		except Exception as ex:
			pass
	data['statu'] = {
		'user': {
			'id': user_id,
			'name': user.name,
		},
		'statu': statu.statu,
		'score': statu.score,
		'comment': statu.comment,
		'filename': statu.filename,
		'content': content,
		'no_compile': ext not in app.config['COMPILE_ALLOW_EXT'],
	}
	return flask.render_template(
		'admin/comment.html',
		**data
	)
	
@app.route('/comment/<homework_id>', methods=["GET"])
@login_required(should_be_admin=True, redirect='login', msg='请重新登录')
def comment_search(current_user, is_admin, homework_id):
	msg = ''
	homework = monitor.load_homework(homework_id)
	if not homework:
		raise Exception('未选中作业(%s)' % homework_id)
	# for search next user
	uss = monitor.load_user_statu(homework_id=homework_id)
	user, statu, compile_res, compile_msg = None, None, None, None
	for u, s in uss:
		if s and s.score == '':
			tmp, compile_res, compile_msg = run_judge(u, s, debug=logger.info)
			if tmp is not None:
				msg += tmp + '\r\n'
				continue
			# ext = s.filename.rsplit('.', 1)[1].lower()
			# if ext not in app.config['COMPILE_ALLOW_EXT']:
			user, statu = u, s
			break
	if not user or not statu:
		msg += '已批改完作业:[%s]%s' % (homework.id, homework.name)
		return flask.redirect(flask.url_for('home', msg = msg))
	# msg += '开始批改作业:user:%s(%s)' % (user.name, user.id)
	# msg = ''
	return flask.redirect(flask.url_for(
		'comment',
		homework_id=homework_id,
		user_id=user.id,
		msg = msg,
		compile_res=compile_res,
		compile_msg=compile_msg))

@app.route('/comment/<homework_id>/<user_id>/<oper>/', methods=["POST"])
@login_required(should_be_admin=True, redirect='login', msg='请重新登录')
def comment_oper(current_user, is_admin, homework_id, user_id, oper):
	msg = ''
	homework = monitor.load_homework(homework_id)
	if not homework:
		raise Exception('未选中作业(%s)' % homework_id)
	user = monitor.load_user(id=user_id)
	if not user:
		raise Exception('未找到用户(%s)' % user_id)
	statu = monitor.load_statu(user_id=user_id, homework_id=homework_id)
	if not statu:
		raise IOError('未找到作业提交状态(%s, %s)' % (user_id, homework_id))
	if statu.statu in [None, '', '未提交']:
		raise IOError('未提交(%s, %s)' % (user_id, homework_id))
	# oper
	if oper == 'comment':
		# load score & comment
		score = flask.request.form['score']
		comment = flask.request.form['comment']
		try:
			score = float(score)
		except Exception as ex:
			raise Exception('分数输入错误(%s)(%s)' % (score, ex))
		if score < 0.00 or score > 1.00:
			raise Exception('分数输入错误(%s)(%s)' % (score, '应在[0,1]范围内'))
		if not comment: comment = ''
		comment = fix(comment)
		statu.score = str(score)
		statu.comment = comment
		msg = '已批改(user:%s,homework:%s,score:%s,comment:%s)' % (statu.user_id, statu.homework_id, statu.score, statu.comment)
		logger.info(msg)
		return flask.redirect(flask.url_for(
			'comment_search',
			homework_id=homework_id,
			msg = msg))
	elif oper == 'compile':
		# ext = statu.filename.rsplit('.', 1)[1].lower()
		# if ext not in app.config['COMPILE_ALLOW_EXT']:
		tmp, compile_res, compile_msg = run_judge(user, statu, debug=logger.info)
		if tmp is not None:
			return flask.redirect(flask.url_for(
				'comment_search',
				homework_id=homework_id,
				msg = tmp))
		return flask.redirect(flask.url_for(
			'comment',
			homework_id=homework_id,
			user_id=user_id,
			compile_res = compile_res,
			compile_msg = compile_msg,
		))
	else:
		raise Exception('Error Operation (%s)' % oper)


@app.route('/add_homework', methods=["POST"])
@login_required(should_be_admin=True, redirect='login', msg='请重新登录')
def add_homework(current_user, is_admin):


##########
# Data URL
# @app.route('/<string:page>', methods=["GET"], defaults={'page': 'index'})
# @json_response()
# def index(page):
# 	args = flask.request.get_json()
# 	logger.info(args)
# 	try:
# 		data = args
# 		return succ(data=data)
# 	except Exception as e:
# 		logger.exception('Exception: ')
# 		return fail(msg=str(e))



setup_app(app, sys.argv)

if __name__ == "__main__":
	app.run(host="0.0.0.0", port=app.config["PORT"], threaded=True)
