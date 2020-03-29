import os
import time
import signal
from subprocess import Popen, PIPE, TimeoutExpired

class EX(Exception):
	def __init__(self, msg):
		Exception.__init__(self, msg)
		self.msg = msg
class RE(EX):
	NAME='Runtime Error'
	def __init__(self, msg):
		EX.__init__(self, msg)
class TLE(EX):
	NAME='Time Limit Exceeded'
	def __init__(self, msg):
		EX.__init__(self, msg)
class MLE(EX):
	NAME='Memory Limit Exceeded'
	def __init__(self, msg):
		EX.__init__(self, msg)
class WA(EX):
	NAME='Wrong Answer'
	def __init__(self, msg):
		EX.__init__(self, msg)
class CE(EX):
	NAME='Compile Error'
	def __init__(self, msg):
		EX.__init__(self, msg)

def run_subprocess_with_time_limit(cmd, input, timeout, do_when_tle=None):
	print('run: %s' % cmd)
	with Popen(cmd, bufsize=0, shell=True, stdout=PIPE, stdin=PIPE,universal_newlines=True) as p:
		try:
			p_stdout, p_stderr = p.communicate(input=input, timeout=timeout)
			p_returncode = p.returncode
		except TimeoutExpired:
			# os.killpg(p.pid, signal.SIGINT)
			os.system('taskkill /F /T /PID %s' % str(p.pid))
			# p_stdout, p_stderr = p.communicate(input=input, timeout=timeout)
			# raise TLE(p_stdout)
			if do_when_tle: do_when_tle()
			raise TLE('')
	return p_returncode, ''.join(p_stdout), ''.join(p_stdout)
	

def run_compile(path, filename, timeout=5.0):
	name, ext = os.path.splitext(filename)
	exe_filename = '(Compile)%s.exe' % name
	change_desk = ''
	if path[1] == ':':
		change_desk = path[0:2] + ' && '
	try:
		returncode, compile_stdout, compile_stderr = run_subprocess_with_time_limit(
			'%scd "%s" && gcc "%s" -w -o "%s"' % (change_desk, path, filename, exe_filename),
			input=None,
			timeout=timeout)
	except TLE as tle:
		raise CE(tle.msg)
	if not os.path.exists(os.path.join(path, exe_filename)):
		raise CE('(%d)\n%s\nerr: %s' % (returncode, compile_stdout, compile_stderr))
	return exe_filename
def delete_file(path, filename):
	change_desk = ''
	if path[1] == ':':
		change_desk = path[0:2] + ' && '
	run_subprocess_with_time_limit(
		'%scd "%s" && del "%s"' % (change_desk, path, filename),
		input=None,
		timeout=1.0,
		do_when_tle=lambda :print('Delete File Error! (%s)' % os.path.join(path, filename)))
def run_exe(path, filename, input, timeout=1.0):
	change_desk = ''
	if path[1] == ':':
		change_desk = path[0:2] + ' && '
	returncode, stdout, stderr = run_subprocess_with_time_limit(
		'%scd "%s" && "%s"' % (change_desk, path, filename),
		input=input,
		timeout=timeout,
		do_when_tle=lambda :print('Run Time Limit Exceeded! (%s)' % os.path.join(path, filename)))
	if returncode != 0:
		raise RE(str(returncode))
	return stdout, stderr

def read_file(filename, encoding=['utf-8','gbk','utf-16']):
	if type(encoding) is str:
		encoding = [ encoding ]
	assert type(encoding) is list
	for enc in encoding:
		print('READ(%s): %s' % (enc, filename))
		res = ''
		try:
			with open(filename, 'r', encoding=enc) as f:
				while True:
					line = f.readline()
					if not line: break
					res += line
			print('READ END')
			return res
		except UnicodeDecodeError as e:
			print('UnicodeDecodeError')
		except Exception as e:
			raise e
	raise IOError('Encoding Error (not in [%s])' % (','.join(encoding)))
def check_content(c1, c2):
	if c1 == c2: return True
	if c1.find('\r') >= 0 or c2.find('\r') >= 0:
		t1 = c1.replace('\r\n', '\n').replace('\r', '\n')
		t2 = c2.replace('\r\n', '\n').replace('\r', '\n')
		return check_content(t1, t2)
	if len(c1) < len(c2): return check_content(c2, c1)
	if len(c1) == len(c2) + 1 and c1[-1] == '\n' and c1[:-1] == c2:
		return True
	return False
def judge(filename, in_filename, out_filename, delete_exe=False):
	path, filename = os.path.split(filename)
	ext = filename.rsplit('.', 1)[1].lower()
	if ext in ['cpp', 'c']:
		exe_filename = run_compile(path, filename)
		input = read_file(in_filename) if in_filename and os.path.exists(in_filename) else None
		stdout, stderr = run_exe(path, exe_filename, input)
		output = stdout
		if delete_exe:
			delete_file(path, exe_filename)
	elif ext in ['txt']:
		output = read_file(os.path.join(path, filename))
	else:
		raise IOError('Ext is incorrect (%s)' % ext)
	answer = read_file(out_filename) if out_filename and os.path.exists(out_filename) else ''
	print('check content:')
	print(output)
	print(answer)
	if check_content(output, answer):
		return True
	raise WA(output)




















