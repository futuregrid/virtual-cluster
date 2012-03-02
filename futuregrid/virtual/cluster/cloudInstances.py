#! /usr/bin/env python
# -*- coding: utf-8 -*-

'''
class for managing currently running or saved 
virtual cluster(s)
'''

import pickle
import os


class CloudInstances:

    cloud_instances = []

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
        self.cloud_instances.append(instance)

    def get_cloud_instances_by_name(self, name):
        '''get cloud instance list by cluster name'''

        f = open(os.path.expanduser(self.backup_file), "r")
        cloud_list = pickle.load(f)
        for cloud in cloud_list:
            if cloud[0]['name'] == name:
                self.cloud_instances = cloud

    def get_all_cloud_instances(self):
        '''get all cloud instances lists'''

        f = open(os.path.expanduser(self.backup_file), "r")
        cloud_list = pickle.load(f)
        return cloud_list

    def get_list(self):
        '''get cloud intances list'''

        return self.cloud_instances

    def set_instance(self, instance_id, image_id, ip=''):
        '''set attributes of a given instance'''

        instance = {}
        instance['id'] = instance_id
        instance['image'] = image_id
        instance['ip'] = ip
        self.cloud_instances.append(instance)

    def set_ip_by_id(self, instance_id, ip):
        '''set ip by given instance id'''

        for instance in self.cloud_instances:
            if len(instance) == 3:
                if instance['id'] == instance_id:
                    instance['ip'] = ip

    def clear(self):
        '''clear cloud intances list'''

        self.cloud_instances = []

    def get_by_id(self, cloud_id):
        '''get instance by index'''

        return self.cloud_instances[cloud_id]

    def save_instances(self):
        '''write current running cloud intances list into backup file'''

        try:
            f = open(os.path.expanduser(self.backup_file), "r")
            instance_list = pickle.load(f)
            instance_list.insert(0, self.cloud_instances)
            f = open(os.path.expanduser(self.backup_file), "w")
            pickle.dump(instance_list, f)
            f.close()
        except:
            if not os.path.exists(os.path.expanduser
                                  (os.path.split(self.backup_file)[0])):
                os.makedirs(os.path.expanduser
                            (os.path.split(self.backup_file)[0]))
            f = open(os.path.expanduser(self.backup_file), "w")
            pickle.dump([self.cloud_instances], f)
            f.close()

    def if_exist(self, name):
        '''check if a given cluster name exists'''

        try:
            f = open(os.path.expanduser(self.backup_file), "r")
            cloud_list = pickle.load(f)
            for cloud in cloud_list:
                if cloud[0]['name'] == name:
                    return True
            return False
        except:
            return False

    def del_by_name(self, name):
        '''delete cloud instances list from backup file given name'''

        f = open(os.path.expanduser(self.backup_file), "r")
        cloud_list = pickle.load(f)
        for cloud in cloud_list:
            if cloud[0]['name'] == name:
                cloud_list.remove(cloud)
                f = open(os.path.expanduser(self.backup_file), "w")
                pickle.dump(cloud_list, f)
                f.close()
                return
