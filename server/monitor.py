#!/usr/bin/env python3
'''
The monitor for database.
'''
import threading
from homework import load_array, save_array
from homework import User, Homework, Statu
import judger


class Monitor:
    def __init__(self, user_filename, homework_filename, statu_filename):
        self.user_filename, self.homework_filename, self.statu_filename = user_filename, homework_filename, statu_filename
        self.lock = threading.RLock()
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
    def load_homework(self, homework_id):
        for homework in self.homework_list:
            if homework.id == homework_id:
                return homework
        return None
    def load_statu(self, user_id, homework_id):
        for statu in self.statu_list:
            if statu.user_id == user_id:
                if statu.homework_id == homework_id:
                    return statu
        return None
    def create_statu(self, user_id, homework_id):
        res = Statu(user_id, homework_id, statu="", filename="", score="", comment="")
        self.lock.acquire()
        try:
            self.statu_list.append(res) # 线程安全
        finally:
            self.lock.release()
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
    def load_user_statu(self, homework_id):
        res = []
        for user in self.user_list:
            tmp = None
            for statu in self.statu_list:
                if statu.user_id == user.id and statu.homework_id == homework_id:
                    tmp = statu
                    break
            res.append((user, tmp))
        return res

    def judge(self, user, statu):
        filepathname = statu.filename
        return judger.judge(filepathname, in_filename, out_filename, delete_exe=False)