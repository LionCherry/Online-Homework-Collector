#!/usr/bin/env python3
'''
The monitor for database.
'''
import os
import threading

from homework import Item, User, Homework, Statu, Judge
import judger


class Monitor:
    def __init__(self, user_filename, homework_filename, statu_filename, judge_filename, file_judge_dir, file_save_dir):
        self.user_filename, self.homework_filename, self.statu_filename, self.judge_filename = user_filename, homework_filename, statu_filename, judge_filename
        self.file_judge_dir, self.file_save_dir = file_judge_dir, file_save_dir
        
        self.lock = threading.RLock()
        self.user_list, self.homework_list, self.statu_list, self.judge_list = self.__load_all__()

    def __load_all__(self):
        return \
            User.load_array(self.user_filename), \
            Homework.load_array(self.homework_filename), \
            Statu.load_array(self.statu_filename), \
            Judge.load_array(self.judge_filename)
    def __save_all__(self):
        Item.save_array(self.user_filename, self.user_list)
        Item.save_array(self.homework_filename, self.homework_list)
        Item.save_array(self.statu_filename, self.statu_list)
        Item.save_array(self.judge_filename, self.judge_list)
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
    def load_judge(self, homework_id):
        res = []
        for judge in self.judge_list:
            if judge.homework_id == homework_id:
                res.append(judge)
        return res
    def create_judge(self, homework_id, submit_file_type):
        self.lock.acquire()
        try:
            res = self.load_judge(homework_id)
            if res is not None: return res
            res = Judge(homework_id, submit_file_type, test_source="", test_in="", test_out="")
            self.judge_list.append(res) # 线程安全
        finally:
            self.lock.release()
        return res
    def create_statu(self, user_id, homework_id):
        self.lock.acquire()
        try:
            res = self.load_statu(user_id, homework_id)
            if res is not None: return res
            res = Statu(user_id, homework_id, statu="", filename="", score="", comment="")
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
    def count_user(self):
        return len(self.user_list)


    def judge(self, user, statu, debug=lambda a:a):
        judge_path = os.path.join(self.file_judge_dir, statu.homework_id)
        user_file = os.path.join(self.file_save_dir, statu.homework_id, statu.filename) # user submit
        judge_list = self.load_judge(statu.homework_id)
        if not judge_list:
            raise judger.EX('No Online Judger!')
        for i, judge in enumerate(judge_list):
            try:
                source = os.path.join(judge_path, judge.test_source) if judge.test_source else ''
                test_in = os.path.join(judge_path, judge.test_in) if judge.test_in else ''
                test_out = os.path.join(judge_path, judge.test_out) if judge.test_out else ''
                if judge.submit_file_type == 'in':
                    test_in = user_file
                elif judge.submit_file_type == 'source':
                    source = user_file
                elif judge.submit_file_type == 'out':
                    judger.judge_file(user_file, test_out, debug=debug) # judger
                    continue
                else:
                    continue
                file_in_filename = os.path.join(judge_path, judge.file_in) if judge.file_in else ''
                file_out_filename = os.path.join(judge_path, judge.file_out) if judge.file_out else ''
                file_generate_filename = os.path.join(judge_path, judge.file_generate_name) if judge.file_generate_name else ''
                # judger
                judger.judge(source, test_in, test_out,
                    file_in_filename=file_in_filename,
                    file_out_filename=file_out_filename,
                    file_generate_filename=file_generate_filename,
                    delete_exe=True, debug=debug)
            except judger.EX as ex:
                ex.test_id = i
                raise ex
        return True

