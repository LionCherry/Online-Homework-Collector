#!/usr/bin/env python3
'''
The class.
'''

import os
import flask_login


def load_array(filename: str, type) -> dict:
    res = []
    with open(filename, 'r', encoding='UTF-8') as f:
        while True:
            line = f.readline()
            if not line: break
            if line[-1] == '\n': line = line[:-1]
            if not line: break
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
    def __init__(self, id: str, name: str, description: str):
        self.id, self.name, self.description = id, name, description
    def as_list(self):
        return [self.id, self.name, self.description]

class Statu:
    def __init__(self, user_id, homework_id, statu: str, filename: str):
        self.user_id = user_id
        self.homework_id = homework_id
        self.statu = statu
        self.filename = filename
    def as_list(self):
        return [self.user_id, self.homework_id, self.statu, self.filename]