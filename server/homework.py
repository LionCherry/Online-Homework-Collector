#!/usr/bin/env python3
'''
The class.
'''

import os
import time
import flask_login


def load_array(filename: str, type) -> dict:
    res = []
    with open(filename, 'r', encoding='UTF-8') as f:
        while True:
            line = f.readline()
            if not line: break
            if line[-1] == '\n': line = line[:-1]
            if not line: continue
            print(line.split('\t'))
            res.append(type(*line.split('\t')))
    return res
def save_array(filename: str, array: list):
    with open(filename, 'w', encoding='UTF-8') as f:
        for a in array:
            f.write('\t'.join(a.as_list()))
            f.write('\n')

class User(flask_login.UserMixin):
    def __init__(self, id: str, pwd: str, name: str):
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

class Homework:
    def __init__(self, id: str, time: str, name: str, allow_ext_list: str, description: str):
        self.id, self.time, self.name, self.allow_ext_list, self.description = id, time, name, allow_ext_list, description
    def as_list(self):
        return [self.id, self.time, self.name, self.allow_ext_list, self.description]
    def get_timestamp(self):
        return int(time.mktime(time.strptime(self.time, '%Y-%m-%d %H:%M:%S')))

class Statu:
    def __init__(self, user_id, homework_id, statu: str, filename: str, score, comment):
        self.user_id = user_id
        self.homework_id = homework_id
        self.statu = statu
        self.filename = filename
        self.score = score
        self.comment = comment
    def as_list(self):
        return [self.user_id, self.homework_id, self.statu, self.filename, self.score, self.comment]