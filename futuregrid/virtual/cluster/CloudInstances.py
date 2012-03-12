#! /usr/bin/env python
# -*- coding: utf-8 -*-

'''
class for managing currently running or saved
virtual cluster(s)
'''

import pickle
import os
import sys


class CloudInstances:
    '''
    ops for managing cloud instances
    '''

    cloud_instances = []
    RUN = 'run'
    SAVED = 'saved'
    DOWN = 'terminated'

    def __init__(self):
        self.clear()
        return

    def set_backup_file(self, filename):
        '''setting backup file for reading and writting'''

        self.backup_file = filename

    def set_cloud_instances_by_name(self, name):
        '''set and add a cloud instance into list'''

        instance = {}
        instance['name'] = name
        instance['status'] = self.RUN
        self.cloud_instances.append(instance)

    def get_cloud_instances_by_name(self, name):
        '''get cloud instance list by cluster name'''

        src_file = open(os.path.expanduser(self.backup_file), "r")
        cloud_list = pickle.load(src_file)
        for cloud in cloud_list:
            if cloud[0]['name'] == name:
                self.cloud_instances = cloud

    def get_all_cloud_instances(self):
        '''get all cloud instances lists'''
        try:
            src_file = open(os.path.expanduser(self.backup_file), "r")
            cloud_list = pickle.load(src_file)
            return cloud_list
        except IOError:
            sys.exit()

    def get_list(self):
        '''get cloud intances list'''

        return self.cloud_instances

    def set_instance(self, instance_id, image_id, instance_ip=''):
        '''set attributes of a given instance'''

        instance = {}
        instance['id'] = instance_id
        instance['image'] = image_id
        instance['ip'] = instance_ip
        self.cloud_instances.append(instance)

    def set_ip_by_id(self, instance_id, instance_ip):
        '''set ip by given instance id'''

        for instance in self.cloud_instances:
            if len(instance) == 3:
                if instance['id'] == instance_id:
                    instance['ip'] = instance_ip

    def clear(self):
        '''clear cloud intances list'''

        self.cloud_instances = []

    def get_by_id(self, cloud_id):
        '''get instance by index'''

        return self.cloud_instances[cloud_id]

    def save_instances(self):
        '''write current running cloud intances list into backup file'''

        try:
            src_file = open(os.path.expanduser(self.backup_file), "r")
            instance_list = pickle.load(src_file)
            instance_list.insert(0, self.cloud_instances)
            src_file = open(os.path.expanduser(self.backup_file), "w")
            pickle.dump(instance_list, src_file)
            src_file.close()

        except IOError:
            if not os.path.exists(os.path.expanduser
                                  (os.path.split(self.backup_file)[0])):
                os.makedirs(os.path.expanduser
                            (os.path.split(self.backup_file)[0]))
            src_file = open(os.path.expanduser(self.backup_file), "w")
            pickle.dump([self.cloud_instances], src_file)
            src_file.close()

    def if_exist(self, name):
        '''check if a given cluster name exists'''

        try:
            src_file = open(os.path.expanduser(self.backup_file), "r")
            cloud_list = pickle.load(src_file)
            for cloud in cloud_list:
                if cloud[0]['name'] == name:
                    return True
            return False

        except IOError:
            return False

    def del_by_name(self, name):
        '''delete cloud instances list from backup file given name'''

        src_file = open(os.path.expanduser(self.backup_file), "r")
        cloud_list = pickle.load(src_file)
        for cloud in cloud_list:
            if cloud[0]['name'] == name:
                cloud_list.remove(cloud)
                src_file = open(os.path.expanduser(self.backup_file), "w")
                pickle.dump(cloud_list, src_file)
                src_file.close()
                return

    def set_running(self):
        ''' set cluster status to run'''

        self.cloud_instances[0]['status'] = self.RUN

    def if_running(self):
        '''check if cluster is running'''

        return self.cloud_instances[0]['status'] == self.RUN

    def set_saved(self):
        ''' set cluster status to saved'''

        self.cloud_instances[0]['status'] = self.SAVED

    def if_saved(self):
        '''check if cluster is saved'''

        return self.cloud_instances[0]['status'] == self.SAVED

    def set_terminated(self):
        ''' set cluster status to terminated'''

        self.cloud_instances[0]['status'] = self.DOWN

    def if_terminated(self):
        '''check if cluster is terminated'''

        return self.cloud_instances[0]['status'] == self.DOWN

    def get_status(self):
        ''' get cluster staus'''

        return self.cloud_instances[0]['status']
