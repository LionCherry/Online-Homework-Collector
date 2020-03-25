#!/usr/bin/env python3
'''
The utils for server.
'''

import json
import re
import datetime
import pytz
import default_settings
from flask import make_response

TOKENNAME_RE_BOOST = re.compile(r'[A-Za-z0-9_-]+')
DEFAULT_TAG = 'head'


def fix(s):
    if s is None: return None
    return s.replace('\r\n', '\\n').replace('\r', '\\n').replace('\n', '\\n').replace('\t', '\\t')

def json_response():
    '''
    Decorator for return json-type http response
    '''

    def _wrapper(f):
        '''
        warpper for the function
        '''
        def _wrapper_f(*args, **kwargs):
            '''
            warpper for the function
            '''
            ret = f(*args, **kwargs)
            if isinstance(ret, tuple):
                if len(ret) != 2:
                    raise Exception(
                        'Length of return tuple error, expect 2, but got: {}'.
                        format(len(ret)))
                raw_json, status_code = ret
                response = make_response(json.dumps(raw_json), status_code)
                response.headers['Content-Type'] = 'application/json'
            else:
                response = make_response(json.dumps(ret), 200)
                response.headers['Content-Type'] = 'application/json'
            return response

        _wrapper_f.__name__ = f.__name__
        return _wrapper_f

    return _wrapper


def plain_response():
    '''
    Decorator for return plain-type http response
    '''

    def _wrapper(f):
        '''
        warpper for the function
        '''
        def _wrapper_f(*args, **kwargs):
            '''
            warpper for the function
            '''
            ret = f(*args, **kwargs)
            if isinstance(ret, tuple):
                if len(ret) != 2:
                    raise Exception(
                        'Length of return tuple error, expect 2, but got: {}'.
                        format(len(ret)))
                response = make_response(*ret)
                response.headers['Content-Type'] = 'text/plain'
            else:
                response = make_response(ret, 200)
                response.headers['Content-Type'] = 'text/plain'
            return response

        _wrapper_f.__name__ = f.__name__
        return _wrapper_f

    return _wrapper


def succ(**kwargs):
    return {"succ": True, **kwargs}


def fail(**kwargs):
    return {"succ": False, **kwargs}


def is_valid_username(user):
    return TOKENNAME_RE_BOOST.fullmatch(user) != None


def is_valid_taskname(taskname):
    return TOKENNAME_RE_BOOST.fullmatch(taskname) != None


def is_valid_tag(tag):
    return TOKENNAME_RE_BOOST.fullmatch(tag) != None


def calc_requirement(task_name, user_defined_requirement,
                     server_requirement_table):
    if not isinstance(server_requirement_table, dict):
        return user_defined_requirement
    if task_name in server_requirement_table:
        return max(
            server_requirement_table.get(task_name), user_defined_requirement)
    else:
        return max(
            server_requirement_table.get('default', 0),
            user_defined_requirement)


def parse_compare_str(compare_str: str) -> tuple:
    tokens = compare_str.split('/')
    if len(tokens) == 2:
        return (tokens[0], tokens[1])
    elif len(tokens) == 1:
        return (tokens[0], DEFAULT_TAG)
    raise Exception("Compare string is not valid: {}".format(compare_str))


class SQLClause(object):
    '''
    : Helper class to build sql clause sentence
    '''

    def __init__(self):
        self.clause = ''
        self.args = []

    def add_clause(self, key: str, operator: str, value):
        if len(self.clause) > 0:
            self.clause += ' and '
        self.clause += '{} {} ${}'.format(key, operator, key)
        self.args.append(value)

    def get_clause(self):
        return "WHERE {}".format(self.clause) if len(self.clause) > 0 else ""

    def get_args(self):
        return self.args


def get_scenario_path(task_name: str, tag: str, scenario_id: str,
                      scenario_path_formatter_table: map) -> str:
    if task_name not in scenario_path_formatter_table:
        return None
    return scenario_path_formatter_table[task_name].format(
        tag=tag, scenario_id=scenario_id)


def get_proxy_url(proxy_formatter: str, url: str) -> str:
    return proxy_formatter.format(url)


def get_extra_args(task_name: str, extra_args_table: map) -> str:
    return extra_args_table.get(task_name, '')


def format_timestamp(timestamp=None,
                     include=3,
                     date_spacer='-',
                     spacer=' ',
                     time_spacer=':') -> str:
    '''
    Format the timesptamp to datetime string.
    `include`: 1 to show the time, 2 to show the date, 3 to show both.
    `spacer` is between date and time.
    '''
    if not timestamp:
        timestamp = datetime.datetime.now(tz=pytz.utc)
    form = ''
    if include >= 2:
        form += '%Y{}%m{}%d'.format(date_spacer, date_spacer)
    if include == 3:
        form += spacer
    if include % 2 == 1:
        form += '%H{}%M{}%S'.format(time_spacer, time_spacer)
    return datetime.datetime.fromtimestamp(timestamp, pytz.utc).strftime(form)


def get_timestamp_from_date_and_time(date='19700101',
                                     time='000000',
                                     timezone: str='UTC') -> int:
    tz = pytz.timezone(timezone)
    date = tz.localize(
        datetime.datetime.strptime('{}T{}'.format(date, time),
                                   '%Y%m%dT%H%M%S'))
    result = int(date.timestamp())
    return result


def get_summary_url(location):
    return default_settings.RECORD_SUMMARY_URL.format(
        location=location,
        metric_api_path=default_settings.METRIC_API_PATH.get(location))


def get_analysis_url(record_id, location):
    return default_settings.RECORD_ANALYSIS_URL.format(
        record_id,
        location=location,
        metric_api_path=default_settings.METRIC_API_PATH.get(location))
