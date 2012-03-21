#! /usr/bin/env python
# -*- coding: utf-8 -*-

'''
class for managing currently running or saved
virtual cluster(s)
'''

import pickle
import os


class CloudInstances:
    '''
    Methods for managing cloud instances
    '''

    cloud_instances = {}
    backup_file = None
    RUN = 'run'
    SAVED = 'saved'
    DOWN = 'terminated'

    def __init__(self):
        self.clear()
        return

    def set_backup_file(self, filename):
        '''
        setting backup file for reading and writting

        Checks if the backup file has the correct format
        '''

        self.backup_file = filename

        # check if file is old version or corrupted
        try:
            src_file = open(os.path.expanduser(self.backup_file), "r")
            cloud_list = pickle.load(src_file)
            for cloud in cloud_list:
                # check basic info
                if not 'name' in cloud or \
                    not 'status' in cloud:
                    return False
                # if is an instance, check all the keys
                for element in cloud.values():
                    if type(element) is dict:
                        if not 'id' in element or \
                            not 'image' in element or \
                            not 'type' in element or \
                            not 'ip' in element:
                            return False
        except IOError:
            return True
        return True

    def set_cloud_instances_by_name(self, name):
        '''
        set and add a cloud instance into list

        Granted this cluster is new and about to be created
        so set status to RUN
        '''

        self.cloud_instances['name'] = name
        # if create cluster, set status to RUN
        self.cloud_instances['status'] = self.RUN

    def get_cloud_instances_by_name(self, name):
        '''
        get cloud instance list by cluster name

        Granted checking cluster existence before
        each operation (create, save, restore, terminate)
        so no need to check if backup file is existed
        '''

        # return cluster by given name
        # using key 'name'
        src_file = open(os.path.expanduser(self.backup_file), "r")
        cloud_list = pickle.load(src_file)
        for cloud in cloud_list:
            if cloud['name'] == name:
                self.cloud_instances = cloud

    def checkpoint_cloud_instances(self,
                                   cluster_name,
                                   control_node_id,
                                   compute_node_id,
                                   instance_type,
                                   cluster_size):
        '''
        set info for saved cluster

        Set all possible values that could be used to
        restore cluster in the future
        Change cluster status to SAVED
        '''

        # if save cluster, set basic info in backupfile
        # resotre this cluster based on this info
        self.clear()
        self.cloud_instances['name'] = cluster_name
        self.cloud_instances['control'] = control_node_id
        self.cloud_instances['compute'] = compute_node_id
        self.cloud_instances['type'] = instance_type
        self.cloud_instances['size'] = cluster_size
        self.cloud_instances['status'] = self.SAVED

    def get_all_cloud_instances(self):
        '''
        get all cloud instances lists

        Load all cloud instances from backup file,
        if file is not existed, return []
        '''

        try:
            src_file = open(os.path.expanduser(self.backup_file), "r")
            cloud_list = pickle.load(src_file)
            return cloud_list
        except IOError:
            return []

    def get_cluster_size(self, cluster=None):
        '''
        return cluster size

        Default cloud instance is self.cloud_instances
        Given cluster_instance has the format
        {'name':'', 'status':'', '0':'', '1':'',...}
        The size of cluster is the length of this dict subtracts
        name and status
        '''

        # get cluster size
        # not include name and status fileds
        if not cluster:
            return len(self.cloud_instances) - 2
        else:
            return len(cluster) - 2

    def get_list(self):
        '''get cloud intances list'''

        return self.cloud_instances

    def set_instance(self,
                     instance_id,
                     image_id,
                     instance_type,
                     instance_ip=''):
        '''
        set attributes of a given instance

        Set id, image, type, ip for one instance
        Using current cluster size as key
        So first instance has key 0
        second has key 1 ...
        '''

        instance = {}
        instance['id'] = instance_id
        instance['image'] = image_id
        instance['type'] = instance_type
        instance['ip'] = instance_ip
        # instance key '0, 1, 2...'
        # can use index to get instance
        self.cloud_instances[self.get_cluster_size()] = instance

    def set_ip_by_id(self, instance_id, instance_ip):
        '''set ip by given instance id'''

        for element in self.cloud_instances.values():
            # if element is an instance
            if type(element) is dict:
                if element['id'] == instance_id:
                    element['ip'] = instance_ip

    def clear(self):
        '''clear cloud intances list'''

        self.cloud_instances = {}

    def get_by_id(self, cloud_id):
        '''get instance by index'''

        return self.cloud_instances[cloud_id]

    def save_instances(self):
        '''
        write current running cloud intances list into backup file
        Open backup file to save cloud_instance
        If file is not existed, then create backup file, dump
        cloud_instances into file
        If file is existed, then load the content from the file,
        combine all cloud instance into list, dump this list into
        file. So the list has the format of [{cluster1},{cluster2},{}]
        '''

        try:
            # open file for reading
            src_file = open(os.path.expanduser(self.backup_file), "r")
            instance_list = pickle.load(src_file)
            # combine existing clusters and current cluster into list
            instance_list.insert(0, self.cloud_instances)
            src_file = open(os.path.expanduser(self.backup_file), "w")
            pickle.dump(instance_list, src_file)
            src_file.close()

        except IOError:
            # if cannot find this file, then create the file
            if not os.path.exists(os.path.expanduser
                                  (os.path.split(self.backup_file)[0])):
                os.makedirs(os.path.expanduser
                            (os.path.split(self.backup_file)[0]))
            src_file = open(os.path.expanduser(self.backup_file), "w")
            # directly save cluster into backup file
            pickle.dump([self.cloud_instances], src_file)
            src_file.close()

    def if_exist(self, name):
        '''check if a given cluster name exists'''

        try:
            src_file = open(os.path.expanduser(self.backup_file), "r")
            cloud_list = pickle.load(src_file)
            for cloud in cloud_list:
                if cloud['name'] == name:
                    return True
            return False

        except IOError:
            return False

    def del_by_name(self, name):
        '''
        delete cloud instances list from backup file given name

        Loads content from backup file, given content is list, then
        delete the cluster which matches name using remove, then
        dump the new content into backup file
        '''

        src_file = open(os.path.expanduser(self.backup_file), "r")
        cloud_list = pickle.load(src_file)
        for cloud in cloud_list:
            if cloud['name'] == name:
                # remove cluster if game matches
                cloud_list.remove(cloud)
                src_file = open(os.path.expanduser(self.backup_file), "w")
                pickle.dump(cloud_list, src_file)
                src_file.close()
                return

    def set_status(self, status):
        ''' get status of virtual cluster'''

        self.cloud_instances['status'] = status

    def if_status(self, status):
        ''' check status of virtual cluster'''

        return self.cloud_instances['status'] == status

    def get_status(self):
        ''' get cluster staus'''

        return self.cloud_instances['status']
