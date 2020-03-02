#!/usr/bin/env python3
'''
The monitor for database.
'''
from homework import *


class Monitor:
    def __init__(self, user_filename, homework_filename, statu_filename):
        self.user_filename, self.homework_filename, self.statu_filename = user_filename, homework_filename, statu_filename
        self.user_list, self.homework_list, self.statu_list = self.__load_all__()
    def __load_all__(self):
        return \
            load_array(self.user_filename, User), \
            load_array(self.homework_filename, Homework), \
            load_array(self.statu_filename, Statu)
    def __save_all__(self):
        save_array(self.user_filename, self.user_list)
        save_array(self.homework_filename, self.homework_list)
        save_array(self.statu_filename, self.statu_list)
    def terminate(self):
        self.__save_all__()
        

    def load_user(self, id):
        for user in self.user_list:
            if user.id == id:
                return user
        return None
    def load_homework(self):
        return self.homework_list
    def load_statu(self, user_id, homework_id):
        for statu in self.statu_list:
            if statu.user_id == user_id:
                if statu.homework_id == homework_id:
                    return statu
        return None
    def create_statu(self, user_id, homework_id):
        res = Statu(user_id, homework_id, statu="", filename="")
        self.statu_list.append(res) # 线程安全
        return res
    def load_homework_statu(self, user_id):
        res = []
        for homework in self.homework_list:
            tmp = None
            for statu in self.statu_list:
                if statu.user_id == user_id and statu.homework_id == homework.id:
                    tmp = statu
                    break
            res.append((homework, tmp))
        return res