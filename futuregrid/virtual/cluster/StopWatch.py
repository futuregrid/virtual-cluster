#!/usr/bin/python
# -*- coding: utf-8 -*-

import time


class StopWatch(object):

    __start_data_table = {}
    __end_data_table = {}

    def __init__(self):
        self.clear()

    def start(self, start_timer_name):
        self.__start_data_table[start_timer_name] = time.time()

    def stop(self, end_timer_name):
        self.__end_data_table[end_timer_name] = time.time()

    def print_time(self, timer_name):
        time_elapsed = self.__end_data_table[timer_name] -\
            self.__start_data_table[timer_name]
        return time_elapsed

    def start_count(self, start_count_name):
        self.__start_data_table[start_count_name] = 0

    def increase(self, count_name):
        self.__start_data_table[count_name] += 1

    def decrease(self, count_name):
        self.__start_data_table[count_name] -= 1

    def print_count(self, count_name):
        return self.__start_data_table[count_name]

    def clear(self):
        self.__start_data_table.clear()
        self.__end_data_table.clear()
