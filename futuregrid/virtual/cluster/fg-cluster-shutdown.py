#! /usr/bin/env python
import getopt, sys, os, pickle

class CloudInstances:

	cloud_instances = []
	
	def __init__(self, name):
		self.clear()
		if self.check_name(name):
			self.cloud_instances = self.load(name)
		else:
			print 'Error in finding virtual cluster. Not created?'
			sys.exit()
		return

	def list(self):
		return self.cloud_instances

	def clear(self):
		self.cloud_instances = []

	def check_name(self, name):
		try:
			f = open("cloud_instances.dat", "r")
			cloud_list = pickle.load(f)
			for cloud in cloud_list:	
				if cloud[0]['name'] == name:
					return True
			return False
		except:
			return False
			

	def load(self, name):
		f = open("cloud_instances.dat", "r")
		cloud_list = pickle.load(f)
		for cloud in cloud_list:
			if cloud[0]['name'] == name:
				return cloud

	def del_by_name(self, name):
		f = open("cloud_instances.dat", "r")
		cloud_list = pickle.load(f)
		for cloud in cloud_list:
			if cloud[0]['name'] == name:
				cloud_list.remove(cloud)
				f = open("cloud_instances.dat", "w")
				pickle.dump(cloud_list, f)
				f.close()
				return

class FgShutdown:

        def __init__(self, name):
                self.name = name
		self.cloud_instances = CloudInstances(name)

	def clean(self, name):
		print '...Clearing up......'
		self.cloud_instances.del_by_name(name)       
	        print '...Done......'
	
	def terminate_instance(self, instance_id):
		print 'terminating instance %s' %instance_id
		os.system("euca-terminate-instances %s" %instance_id)

	def shut_down(self):
		for instance in self.cloud_instances.list()[1:]:
			self.terminate_instance(instance['id'])
		self.clean(self.name)

def usage():
        print '-h/--help    Display this help.'
        print '-a/--name    provide name of virtual cluster.'


def main():

        try:
                opts, args = getopt.getopt(sys.argv[1:], "ha:", ["help", "name="])
        except getopt.GetoptError:
                usage()
                sys.exit()

        for opt, arg in opts:
                if opt in ("-h", "--help"):
                        usage()
                        sys.exit()
		if opt in ("-a", "--name"):
                        name=arg

        fgs=FgShutdown(name)
	fgs.shut_down()

if __name__ == '__main__':
    main()
