#!/usr/bin/env python3
'''
The class.
'''

import os
import time
import threading
import flask_login

class Item:
    def __init__(self):
        self.__lock__ = threading.RLock()
    def as_list(self):
        raise NotImplementedError('Item is an abstract class.')
    def acquire(self):
        self.__lock__.acquire()
    def release(self):
        self.__lock__.release()
    def __setattr__(self, name, value):
        if name == '__lock__': return super().__setattr__(name, value)
        self.acquire()
        try: return super().__setattr__(name, value)
        finally: self.release()
    @classmethod
    def load_array(cls, filename, parser=None) -> dict:
        res = []
        with open(filename, 'r', encoding='UTF-8') as f:
            while True:
                line = f.readline()
                if not line: break
                if line[-1] == '\n': line = line[:-1]
                if not line: continue
                item = line.split('\t')
                if parser: item = parser(item)
                else:      item = cls(*item)
                res.append(item)
        return res
    @staticmethod
    def save_array(filename: str, array: list):
        with open(filename, 'w', encoding='UTF-8') as f:
            for a in array:
                f.write('\t'.join(a.as_list()))
                f.write('\n')

class User(Item, flask_login.UserMixin):
    def __init__(self, id: str, pwd: str, name: str):
        super().__init__()
        self.id, self.pwd, self.name = id, pwd, name
    def as_list(self):
        return [self.id, self.pwd, self.name]
    def is_authenticated(self):
        return True
    def is_active(self):
        return True
    def is_anonymous(self):
        return False
    def get_id(self):
        return self.id
    def __repr__(self):
        return '<User %s>' % self.id

class Homework(Item):
    def __init__(self, id: str, time: str, name: str, allow_ext_list: str, description: str):
        super().__init__()
        self.id, self.time, self.name, self.allow_ext_list, self.description = id, time, name, allow_ext_list, description
    def as_list(self):
        return [self.id, self.time, self.name, self.allow_ext_list, self.description]
    def get_timestamp(self):
        return int(time.mktime(time.strptime(self.time, '%Y-%m-%d %H:%M:%S')))

class Judge(Item):
    def __init__(self, homework_id, submit_file_type, test_source, test_in, test_out, file_in, file_out, file_generate_name):
        super().__init__()
        self.homework_id, self.submit_file_type, self.test_source, self.test_in, self.test_out = homework_id, submit_file_type, test_source, test_in, test_out
        self.file_in, self.file_out, self.file_generate_name = file_in, file_out, file_generate_name
    def as_list(self):
        return [self.homework_id, self.submit_file_type, self.test_source, self.test_in, self.test_out, self.file_in, self.file_out, self.file_generate_name]

class Statu(Item):
    def __init__(self, user_id, homework_id, statu: str, filename: str, score, comment):
        super().__init__()
        self.user_id = user_id
        self.homework_id = homework_id
        self.statu = statu
        self.filename = filename
        self.score = score
        self.comment = comment
    def as_list(self):
        return [self.user_id, self.homework_id, self.statu, self.filename, self.score, self.comment]
        