import os
import time
import signal
import logging
from subprocess import Popen, PIPE, TimeoutExpired

class EX(Exception):
	NAME='System Error'
	def __init__(self, msg, test_id=0):
		super().__init__()
		self.test_msg = msg
		self.test_id = test_id
	def name(self):
		if self.test_id:
			return '%s on %d' % (type(self).NAME, self.test_id)
		return type(self).NAME
class RE(EX):
	NAME='Runtime Error'
	def __init__(self, msg): super().__init__(msg)
class TLE(EX):
	NAME='Time Limit Exceeded'
	def __init__(self, msg): super().__init__(msg)
class MLE(EX):
	NAME='Memory Limit Exceeded'
	def __init__(self, msg): super().__init__(msg)
class WA(EX):
	NAME='Wrong Answer'
	def __init__(self, msg, correct=''):
		super().__init__(msg)
		self.correct = correct
class WA_File(WA):
	NAME='Wrong Answer In File'
	def __init__(self, msg, correct=''): super().__init__(msg, correct=correct)
class CE(EX):
	NAME='Compile Error'
	def __init__(self, msg): super().__init__(msg)

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
	if p_stdout is None: p_stdout = ''
	elif type(p_stdout) is list: p_stdout = ''.join(p_stdout)
	return p_returncode, p_stdout
	

def run_compile(path, filename, timeout=5.0):
	name, ext = os.path.splitext(filename)
	exe_filename = '(Compile)%s.exe' % name
	change_desk = ''
	if path[1] == ':':
		change_desk = path[0:2] + ' && '
	try:
		returncode, compile_stdout = run_subprocess_with_time_limit(
			'%scd "%s" && gcc "%s" -w -o "%s"' % (change_desk, path, filename, exe_filename),
			input=None,
			timeout=timeout)
	except TLE as tle:
		raise CE(tle.test_msg)
	if not os.path.exists(os.path.join(path, exe_filename)):
		raise CE('returncode: %d\n%s' % (returncode, compile_stdout))
	return exe_filename
def delete_file(path, filename):
	if not os.path.exists(os.path.join(path, filename)):
		return False
	print('Delete File: %s' % filename)
	change_desk = ''
	if path[1] == ':':
		change_desk = path[0:2] + ' && '
	run_subprocess_with_time_limit(
		'%scd "%s" && del "%s"' % (change_desk, path, filename),
		input=None,
		timeout=1.0,
		do_when_tle=lambda :print('Delete File Error! (%s)' % os.path.join(path, filename)))
	return True
def copy_file(from_filename, to_filename):
	if from_filename == to_filename:
		return False
	print('Copy File: %s => %s' % (from_filename, to_filename))
	with open(from_filename, 'r') as f:
		with open(to_filename, 'w') as w:
			while True:
				content = f.read(1024)
				if not content: break
				w.write(content)
	return True
def run_exe(path, filename, input, timeout=1.0):
	change_desk = ''
	if path[1] == ':':
		change_desk = path[0:2] + ' && '
	returncode, stdout = run_subprocess_with_time_limit(
		'%scd "%s" && "%s"' % (change_desk, path, filename),
		input=input,
		timeout=timeout,
		do_when_tle=lambda :print('Run Time Limit Exceeded! (%s)' % os.path.join(path, filename)))
	if returncode != 0:
		raise RE(str(returncode))
	return stdout

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
	if c1 is None: c1 = ''
	if c2 is None: c2 = ''
	if c1 == c2: return True
	if c1.find('\r') >= 0 or c2.find('\r') >= 0:
		t1 = c1.replace('\r\n', '\n').replace('\r', '\n')
		t2 = c2.replace('\r\n', '\n').replace('\r', '\n')
		return check_content(t1, t2)
	if len(c1) < len(c2): return check_content(c2, c1)
	if len(c1) == len(c2) + 1 and c1[-1] == '\n' and c1[:-1] == c2:
		return True
	return False
def read_file_or_return_none(filename):
	return read_file(filename) if filename and os.path.exists(filename) else None

def judge(source, in_filename, out_filename, file_in_filename=None, file_out_filename=None, file_generate_name=None, delete_exe=False, debug=lambda a:a):
	path, source = os.path.split(source)
	exe_filename = run_compile(path, source, timeout=5.0)
	input = read_file_or_return_none(in_filename)
	# copy file
	if file_in_filename:
		copy_file_in_filename = os.path.join(path, os.path.split(file_in_filename)[1])
		do_copy = copy_file(file_in_filename, copy_file_in_filename)
	else: do_copy = False
	# run
	stdout = run_exe(path, exe_filename, input, timeout=2.0)
	file_generate_content = read_file_or_return_none(os.path.join(path, file_generate_name))
	# delete
	if delete_exe:
		delete_file(path, exe_filename)
	if file_generate_name:
		delete_file(path, file_generate_name)
	if do_copy:
		delete_file(*os.path.split(copy_file_in_filename))
	# check answer
	answer = read_file_or_return_none(out_filename)
	if not check_content(stdout, answer):
		raise WA(stdout, correct=answer)
	file_out_content = read_file_or_return_none(os.path.join(path, file_out_filename))
	if not check_content(file_generate_content, file_out_content):
		raise WA_File(file_generate_content, correct=file_out_content)
	
def judge_file(out_filename, answer_filename, debug=lambda a:a):
	output = read_file_or_return_none(out_filename)
	answer = read_file_or_return_none(answer_filename)
	debug('x'*20)
	debug('output(%s):\n%s'%(out_filename,output))
	debug('answer(%s):\n%s'%(answer_filename,answer))
	if not check_content(output, answer):
		raise WA(output, correct=answer)



















