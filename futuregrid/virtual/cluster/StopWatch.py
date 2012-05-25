#!/usr/bin/python
# -*- coding: utf-8 -*-

import time


class StopWatch(object):

    # Timer start dict
    __start_data_table = {}
    # Timer end dict
    __end_data_table = {}

    def __init__(self):
        self.clear()

    def start(self, start_timer_name):
        '''
        timer name as key, start time as value (in second)
        '''
        self.__start_data_table[start_timer_name] = time.time()

    def stop(self, end_timer_name):
        '''
        timer name as key, end time as value (in second)
        '''
        self.__end_data_table[end_timer_name] = time.time()

    def print_time(self, timer_name):
        '''
        timer name as key, read start time and end time from
        start and end timer tables
        '''
        time_elapsed = self.__end_data_table[timer_name] -\
            self.__start_data_table[timer_name]
        return time_elapsed

    def start_count(self, start_count_name):
        '''
        timer name as key, initialize value to 0
        '''
        self.__start_data_table[start_count_name] = 0

    def increase(self, count_name):
        '''
        timer name as key, increase value by 1
        '''
        self.__start_data_table[count_name] += 1

    def decrease(self, count_name):
        '''
        timer name as key, decrease value by 1
        '''
        self.__start_data_table[count_name] -= 1

    def print_count(self, count_name):
        '''
        timer name as key, print value
        '''
        return self.__start_data_table[count_name]

    def clear(self):
        '''
        clear start and end timer
        '''
        self.__start_data_table.clear()
        self.__end_data_table.clear()
