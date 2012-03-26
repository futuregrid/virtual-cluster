#! /usr/bin/env python
# -*- coding: utf-8 -*-

'''
CloudInstances.py (python)
-------------------------

Operations on clusters based on backup file

Backup file is the file which stores information of
a list of virtual clusters

Backup file format
-------------------------
[{cluster1}, {cluster2}, {cluster3}, {}]

Each cluster is a dictionary, it has the following format:
{'name':'cluster1', 'status':'run', '0':'{}', '1':'{}', ...}
The first two keys are name, and status, the rest are instances.
Name represents the name of virtual cluster and status represents
the status of cluster. Key '0', '1', ... represent instances, each
instance is associated with a number which can be used to refer to.
Instance key starts at 0.

Each instance is a dictionary, it has the following format:
{'id':'', 'image':'', 'type':'', 'ip':''}
'''

import pickle
import os


class CloudInstances:
    '''
    Class CloudInstances
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
        Sets backup file for reading and writing

        Parameters:
            filename -- backup file name

        Logic:
            Checks if the backup file has the correct format by
            checking if all keys are present in each dictionary.

        Return:
            true  -- If can not find backup file, so the file has not
                     been created.
            false -- If file exists, but can not find all the keys
                     which are needed.
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
        except (KeyError, TypeError):
            return False
        except IOError:
            return True
        return True

    def set_cloud_instances_by_name(self, name):
        '''
        Sets a new cloud instance

        Parameters:
            name -- virtual cluster name

        Logic:
            Granted this cluster is new and about to be created,
            sets cluster name to name, and sets status to run.

        No returns
        '''

        self.cloud_instances['name'] = name
        # if create cluster, set status to RUN
        self.cloud_instances['status'] = self.RUN

    def get_cloud_instances_by_name(self, name):
        '''
        Gets cloud instance list by cluster name

        Parameters:
            name -- virtual cluster name

        Logic:
            Granted we check cluster existence every time before
            each operation (create, save, restore, terminate, ...)
            so here no need to check if backup file is existed

            Opens backup file for reading, loads cluster lists,
            find cluster instances list given cluster name, then
            sets cloud_instances to the cluster loaded

        No returns
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
        Sets cluster saving information after actually saves it

        Parameters:
            cluster_name -- virtual cluster name
            control_node_id -- control node image id
            compute_node_id -- compute node image id
            instance_type -- instance type
            cluster_size -- size of cluster (control node not included)

        Logic:
            Sets all possible values that could be used to restore cluster
            in the future before saves it into backup file

            Sets cluster status to SAVED

        No returns
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
        Gets all cloud instances lists

        No parameters

        Logic:
            Loads all cloud instances from backup file.

        Return:
            cloud_list -- if file exists, return all the cloud lists
                          saved
            [] -- if file does not exist
        '''

        try:
            src_file = open(os.path.expanduser(self.backup_file), "r")
            cloud_list = pickle.load(src_file)
            return cloud_list
        except IOError:
            return []

    def get_cluster_size(self, cluster=None):
        '''
        Gets virtual cluster size

        Parameters:
            cluster -- virtual cluster name
            default: None

        Logic:
            Default cloud instance is the dictionary self.cloud_instances,
            if cluster is specified, then returns the size of cluster given
            name.

            Given cluster_instance has the format of:
            {'name':'', 'status':'', '0':'', '1':'',...}
            The size of cluster is the length of this dictionary subtracts
            length of name and status which is 2

        Return:
            length of self.cloud_instances -- if cluster is set to default
            length of cluster -- if cluster is set to any other clusters
        '''

        # get cluster size
        # not include name and status fileds
        if not cluster:
            return len(self.cloud_instances) - 2
        else:
            return len(cluster) - 2

    def get_list(self):
        '''
        Gets cloud instances list

        No parameters

        Return:
            cloud instances list -- self.cloud_instances
        '''

        return self.cloud_instances

    def get_index(self, instance):
        '''
        Gets instance key from cloud instance list

        Parameters:
            instance -- an instance dictionary

        Logic:
            Finds the instance matches the id
            then return the key

        Return:
            key -- instance index
        '''
        for key, element in self.cloud_instances.items():
            # if element is an instance
            if type(element) is dict:
                if element['id'] == instance['id']:
                    return key

    def set_instance(self,
                     instance_id,
                     image_id,
                     instance_type,
                     index,
                     instance_ip=''):
        '''
        Sets attributes of a given instance

        Parameters:
            instance_id -- instance id
            image_id -- image id
            instance_type -- instance type
            instance_ip -- public IP associated with instance
            default: ''

        Logic:
            Set id, image, type, IP for one instance
            Using current cluster size as key
            So first instance has key 0, second has key 1 ...

        No returns
        '''

        instance = {}
        instance['id'] = instance_id
        instance['image'] = image_id
        instance['type'] = instance_type
        instance['ip'] = instance_ip
        # instance key '0, 1, 2...'
        # can use index to get instance
        if not index:
            self.cloud_instances[self.get_cluster_size()] = instance
        else:
            self.cloud_instances[index] = instance

    def del_instance(self, instance):
        '''
        Deletes an instance from cloud instance list

        Parameters:
            instance -- an instance dictionary

        Logic:
            Find the instance matches id then delete
            the instance using key

        No returns
        '''
        for key, element in self.cloud_instances.items():
            # if element is an instance
            if type(element) is dict:
                if element['id'] == instance['id']:
                    del self.cloud_instances[key]

    def set_ip_by_id(self, instance_id, instance_ip):
        '''
        Sets IP by given instance id

        Parameters:
            instance_id -- instance id
            instance_ip -- public IP associated with instance

        Logic:
            Loop all values in cloud_instances, given an instance
            is a dictionary, if current element is a dictionary,
            check key 'id', and then set 'ip' if key 'id' matches

        No returns
        '''

        for element in self.cloud_instances.values():
            # if element is an instance
            if type(element) is dict:
                if element['id'] == instance_id:
                    element['ip'] = instance_ip

    def clear(self):
        '''
        Clears cloud instances list

        No parameters
        No returns
        '''

        self.cloud_instances = {}

    def get_by_id(self, cloud_id):
        '''
        Gets instance by index

        Parameters:
            cloud_id -- instance index, which is also the key for instance

        Logic:
            Given that we use current size of cluster as key, so we can use
            this index to get one specific instance

        Return:
            Instance dictionary -- an instance which has the format of
                                   {'id':'', 'image':'', 'type':'', 'ip':''}
        '''

        return self.cloud_instances[cloud_id]

    def save_instances(self):
        '''
        Writes current cloud instances list into backup file

        No parameters

        Logic:
            Opens backup file to save cloud_instance
            If file does not exist, then creates backup file, dumps
            cloud_instances into the file
            If file exists, then loads the content from the file,
            combine all cloud instance into list, dump this list into
            file. So the list has the format of [{cluster1},{cluster2},{}]
            (may need to change it to dictionary)

        No returns
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
        '''
        Checks if a given cluster name exists

        Parameters:
            name -- cluster name

        Logic:
            Given all clusters stored in backup file is a list, so loop
            this list, and check key 'name' in each cluster dictionary

        Return:
            true -- if find a cluster matches the cluster name given as
                    parameter
            false -- if 1) file does not exist
                        2) Cannot find a cluster matches the cluster
                           name given as parameter after checking
                           all clusters saved in the backup file
        '''

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
        Deletes cloud instances list from backup file given name

        Parameter:
            name -- cluster name

        Logic:
            Loads content from backup file, given content is list, then
            delete the cluster which matches name using remove, then
            dump the new content into backup file

        No returns
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
        '''
        Gets status of virtual cluster

        Parameters:
            status -- cluster status (run, saved, terminated)

        Logic:
            Sets the status in cloud instance list

        No returns
        '''

        self.cloud_instances['status'] = status

    def if_status(self, status):
        '''
        Checks status of virtual cluster

        Parameters:
            status -- cluster status (run, saved, terminated)

        Logic:
            checks if status in cluster instance list matches
            status given as parameter

        Return:
            true -- if status of cluster instance list matches
                    the status given as parameter
            false -- if status of cluster instance list does
                     not match the status given as parameter
        '''

        return self.cloud_instances['status'] == status

    def get_status(self):
        '''
        Gets cluster status

        Parameters:
            status -- cluster status (run, saved, terminated)

        Logic:
            Get the value of key 'status'

        Return:
            Returns the value of status
        '''

        return self.cloud_instances['status']
