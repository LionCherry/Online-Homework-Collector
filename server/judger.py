import os
import time
import signal
from subprocess import Popen, PIPE, TimeoutExpired


class RE(Exception):
	def __init__(self, msg):
		Exception.__init__(self, 'RuntimeError(%s)' % msg)
		self.msg = msg
class TLE(Exception):
	def __init__(self, msg):
		Exception.__init__(self, 'TimeLimitExceeded(%s)' % msg)
		self.msg = msg
class MLE(Exception):
	def __init__(self, msg):
		Exception.__init__(self, 'MemoryLimitExceeded(%s)' % msg)
		self.msg = msg
class WA(Exception):
	def __init__(self, msg):
		Exception.__init__(self, 'WrongAnswer(%s)' % msg)
		self.msg = msg
class CE(Exception):
	def __init__(self, msg):
		Exception.__init__(self, 'CompleError(%s)' % msg)
		self.msg = msg

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
	return p_returncode, ''.join(p_stdout)
	

def run_compile(path, filename, timeout=1.0):
	name, ext = os.path.splitext(filename)
	exe_filename = '(Compile)%s.exe' % name
	try:
		returncode, compile_stdout = run_subprocess_with_time_limit(
			'cd "%s" && gcc "%s" -w -o "%s"' % (path, filename, exe_filename),
			input=None,
			timeout=timeout)
	except TLE as tle:
		raise CE(tle.msg)
	if not os.path.exists(os.path.join(path, exe_filename)):
		raise CE('(%d)%s' % (returncode, compile_stdout))
	return exe_filename
def delete_file(path, filename):
	run_subprocess_with_time_limit(
		'cd "%s" && del "%s"' % (path, filename),
		input=None,
		timeout=1.0,
		do_when_tle=lambda :print('Delete File Error! (%s)' % os.path.join(path, filename)))
def run_exe(path, filename, input, timeout=1.0):
	returncode, stdout = run_subprocess_with_time_limit(
		'cd "%s" && "%s"' % (path, filename),
		input=input,
		timeout=timeout,
		do_when_tle=lambda :print('Run Time Limit Exceeded! (%s)' % os.path.join(path, filename)))
	if returncode != 0:
		raise RE(str(returncode))
	return stdout

def read_file(filename):
	res = ''
	with open(filename, 'r') as f:
		while True:
			line = f.readline()
			if not line: break
			res += line
	return res
def check_content(c1, c2):
	if c1 == c2: return True
	if c1.find('\r') >= 0 or c2.find('\r') >= 0:
		t1 = c1.replace('\r\n', '\n').replace('\r', '\n')
		t2 = c2.replace('\r\n', '\n').replace('\r', '\n')
		return check_content(t1, t2)
	if len(c1) < len(c2): return check_content(c2, c1)
	if len(c1) == len(c2) + 1 and c1[-1] == '\n':
		return True
	return False
def run(filename, in_filename, out_filename, delete_exe=False):
	path, filename = os.path.split(filename)
	ext = filename.rsplit('.', 1)[1].lower()
	if ext in ['cpp', 'c']:
		exe_filename = run_compile(path, filename)
		input = read_file(in_filename) if in_filename and os.path.exists(in_filename) else None
		output = run_exe(path, exe_filename, input)
		if delete_exe:
			delete_file(path, exe_filename)
	elif ext in ['txt']:
		output = read_file(os.path.join(path, filename))
	else:
		raise IOError('Ext is incorrect (%s)' % ext)
	answer = read_file(out_filename) if out_filename and os.path.exists(out_filename) else ''
	if check_content(output, answer):
		return True
	raise WA(output.replace('\n', '\\n'))




















