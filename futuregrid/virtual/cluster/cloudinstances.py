class CloudInstances:

	cloud_instances = []

	# read with configparser from file futuregrid.cfg
        backup_file = "cloud_instances.dat"
	
	def __init__(self, name):
                self.clear()
		if self.check_name(name):
			instance = {}
			instance['name'] = name
			self.cloud_instances.append(instance)
		else:
			print 'Error in restoring virtual cluster. name is in use?'
			sys.exit()
		return

	def list(self):
		return self.cloud_instances

	def set(self, instance_id, image_id, ip = ''):
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
			f = open(self.backup_file, "r")
			instance_list = pickle.load(f)
			instance_list.insert(0, self.cloud_instances)
			f = open(self.backup_file, "w")
			pickle.dump(instance_list, f)	
			f.close()		
		except:
			f = open(self.backup_file, "w")
			pickle.dump([self.cloud_instances], f)
			f.close()

	def check_name(self, name):
		try:
			f = open(self.backup_file, "r")
			cloud_list = pickle.load(f)
			for cloud in cloud_list:
				if cloud[0]['name'] == name:
					return False
			return True
		except:
			return True

## Note logic in some other files is negated 

#	def check_name(self, name):
#		try:
#			f = open("cloud_instances.dat", "r")
#			cloud_list = pickle.load(f)
#			for cloud in cloud_list:	
#				if cloud[0]['name'] == name:
#					return True
#			return False
#		except:
#			return False


	def load(self, name):
            # change logic to use config parser. default file is ~/.futuregrid/virtual-cluster.cfg
            f = open(self.backup_file, "r")
            cloud_list = pickle.load(f)
            for cloud in cloud_list:
                if cloud[0]['name'] == name:
                    return cloud


	def del_by_name(self, name):
		f = open(self.backup_file, "r")
		cloud_list = pickle.load(f)
		for cloud in cloud_list:
			if cloud[0]['name'] == name:
				cloud_list.remove(cloud)
				f = open(self.backup_file, "w")
				pickle.dump(cloud_list, f)
				f.close()
				return

        def set_filename (self, name):
            self.backup_file = name
