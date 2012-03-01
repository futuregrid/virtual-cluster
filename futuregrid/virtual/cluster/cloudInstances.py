#! /usr/bin/env python
import pickle, os

class CloudInstances:

    cloud_instances = []
    
    def __init__(self):
        self.clear()
        return

    def set_backup_file(self, filename):
        self.backup_file = filename

    def set_cloud_instances_by_name(self, name):
        instance = {}
        instance['name'] = name
        self.cloud_instances.append(instance)
        
    def get_cloud_instances_by_name(self, name):
        f = open(os.path.expanduser(self.backup_file), "r")
        cloud_list = pickle.load(f)
        for cloud in cloud_list:
            if cloud[0]['name'] == name:
                self.cloud_instances = cloud
                
    def get_all_cloud_instances(self):
        f = open(os.path.expanduser(self.backup_file), "r")
        cloud_list = pickle.load(f)
        return cloud_list

    def get_list(self):
        return self.cloud_instances

    def set_instance(self, instance_id, image_id, ip=''):
        instance = {}
        instance['id'] = instance_id
        instance['image'] = image_id
        instance['ip'] = ip
        self.cloud_instances.append(instance)
    
    def set_ip_by_id(self, instance_id, ip):
        for instance in self.cloud_instances:
            if len(instance) == 3:
                if instance['id'] == instance_id:
                    instance['ip'] = ip

    def clear(self):
        self.cloud_instances = []

    def get_by_id (self, cloud_id):
        return self.cloud_instances[cloud_id]

    def save_instances(self):
        try:
            f = open(os.path.expanduser(self.backup_file), "r")
            instance_list = pickle.load(f)
            instance_list.insert(0, self.cloud_instances)
            f = open(os.path.expanduser(self.backup_file), "w")
            pickle.dump(instance_list, f)    
            f.close()      
        except:
            if not os.path.exists(os.path.expanduser(os.path.split(self.backup_file)[0])):    
                os.makedirs(os.path.expanduser(os.path.split(self.backup_file)[0]))
            f = open(os.path.expanduser(self.backup_file), "w")
            pickle.dump([self.cloud_instances], f)
            f.close()

    def if_exist(self, name):
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
        f = open(os.path.expanduser(self.backup_file), "r")
        cloud_list = pickle.load(f)
        for cloud in cloud_list:
            if cloud[0]['name'] == name:
                cloud_list.remove(cloud)
                f = open(os.path.expanduser(self.backup_file), "w")
                pickle.dump(cloud_list, f)
                f.close()
                return

    def set_filename (self, name):
        self.backup_file = name
