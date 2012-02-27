#! /usr/bin/env python

import socket, time, getopt, sys, os

class CloudInstances:

	cloud_instances = []
	
	def __init__(self):
                self.clear()
		return

	def list(self):
		return self.cloud_instances

	def set(self, instance_id, image_id, ip = ''): #label
		instance = {}
		instance['id'] = instance_id
		instance['image'] = image_id
		instance['ip'] = ip
		self.cloud_instances.append(instance)
	
	def set_ip_by_id(self, instance_id, ip):
		for instance in self.cloud_instances:
			if instance['id'] == instance_id:
				instance['ip'] = ip

	def clear(self):
                self.size = 0
		self.cloud_instances = []

	def get_by_id (self, cloud_id):
		return self.cloud_instances[cloud_id]

	# def run_instance(self, ...)

	# def get_address(self, id)
	
	# whateve else you need

	# save() pickle

	# reload()

class FgCreate:
        def __init__(self, userkey, number, image, name, size='m1.small'):
		self.userkey = userkey
		self.number = number
		self.image = image
		self.name = name
		self.size= size
		self.cloud_instances = CloudInstances()			

        def detect_port(self):
		ready = 0
		
		# check if shh port of all VMs are alive
		while 1:
			for instace in self.cloud_instances.list():
                		try:
					sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        	                        sk.settimeout(1)
                	                sk.connect((instace['ip'], 22))
                        	        sk.close()
					ready = ready + 1					
	                        except Exception:
        	                        print 'Waitting VMs ready to deploy...'
					ready = 0
                        	        time.sleep(2)
			# check if all vms are ready			
			if ready == len(self.cloud_instances.list()):
				break

	def get_command_result(self, command):
		return os.popen(command).read()	
	
	def euca_run_instance (self, userkey, cluster_size, image, instance_type):
		eui_overhead = 3
		eui_id_pos = 2
		eui_len = 8
		instances = [x for x in self.get_command_result("euca-run-instances -k %s -n %d -t %s %s"  %(userkey, cluster_size, instance_type, image)).split()]
		for num in range(cluster_size):
			self.cloud_instances.set(instances[num * eui_len + eui_id_pos + eui_overhead], image)

		print self.cloud_instances.list()

	def euca_associate_address (self, instance_id, ip):
		os.system("euca-associate-address -i %s %s" %(instance_id, ip))
		self.cloud_instances.set_ip_by_id(instance_id, ip)

	def euca_describe_addresses (self):
		ip_list = []
		ips = [x for x in os.popen("euca-describe-addresses").read().split('\n')]
		for ip in ips:
			if  ip.find('i-') < 0 and len(ip) > 0:
				ip_list.append(ip.split('\t')[1])
		return ip_list
	
	def ssh (self, userkey, ip, command):
#		print "ssh -i %s.pem ubuntu@%s '%s'" %(userkey, ip, command)
		os.system("ssh -i %s.pem ubuntu@%s '%s'" %(userkey, ip, command))
		
	def scp (self, userkey, fileName, ip):
#		print "scp -i %s.pem %s ubuntu@%s:~/" %(userkey, fileName, ip)
		os.system("scp -i %s.pem %s ubuntu@%s:~/" %(userkey, fileName, ip))
			

        def create_cluster(self):
		print '\n...Creating virtual cluster......'
		print 'name   -- ', self.name
		print '#nodes -- ', self.number
		print 'size   -- ', self.size
		print 'image  -- ', self.image
		print '\n'		
		
		cluster_size = int(self.number) + 1
		self.euca_run_instance (self.userkey, cluster_size, self.image, self.size)
		ip_lists = self.euca_describe_addresses ()

		# immediatly associate ip after run instance may lead to error, use sleep
		time.sleep(3)

		print '...Associating IPs......'
		for i in range(cluster_size):
			instance = self.cloud_instances.get_by_id(i)
			self.euca_associate_address (instance['id'], ip_lists[i])

		
		# create folder for cluster given name
#		try:
#			os.makedirs("futuregrid/cluster/%s" %self.name)
#			os.chdir("futuregrid/cluster/%s" %self.name)
#		except Exception:
#			print "Creating directory futuregrid/cluster/%s falied. Cluster name is in use?" %self.name
#			sys.exit()


	def clean(self):
		print '...Clearing up......'
		print '...Done......'

	def deploy_slurm(self):
		print '\n...Deploying SLURM system......'

		for instance in self.cloud_instances.list():
			self.ssh(self.userkey, instance['ip'], "sudo apt-get update")
			self.ssh(self.userkey, instance['ip'], "sudo apt-get install --yes slurm-llnl")
#			self.ssh(self.userkey, instance['ip'], "sudo apt-get install --yes openmpi-bin openmpi-doc libopenmpi-dev")

		print '\n...slurm.conf......'
		with open("slurm.conf.in") as srcf:
    			input_content = srcf.readlines()
		srcf.close()
		
		controlMachine=self.cloud_instances.get_by_id(0)['id']
		output = "".join(input_content) % vars()

		destf = open("slurm.conf","w")
		print >> destf, output
		destf.close()

		with open("slurm.conf", "a") as conf:
			for instance in self.cloud_instances.list()[1:]:
				conf.write("NodeName=%s Procs=1 State=UNKNOWN\n" %instance['id'])
				conf.write("PartitionName=debug Nodes=%s Default=YES MaxTime=INFINITE State=UP\n" %instance['id'])
		conf.close()

		print '\n...generate munge-key......'
		# generate munge-key on control node
		self.ssh(self.userkey, self.cloud_instances.get_by_id(0)['ip'], "sudo /usr/sbin/create-munge-key")
		munge_key = open("munge.key","w")
		print >>munge_key, self.get_command_result("ssh -i %s.pem ubuntu@%s 'sudo cat /etc/munge/munge.key'" %(self.userkey, self.cloud_instances.get_by_id(0)['ip']))
		munge_key.close()

		for instance in self.cloud_instances.list():
			# copy slurm.conf
			print '\n...copying slurm.conf to node......'
			self.scp(self.userkey, "slurm.conf", instance['ip'])
			self.ssh(self.userkey, instance['ip'], "sudo cp slurm.conf /etc/slurm-llnl")

			# copy munge key
			print '\n...copying munge-key to nodes......'
			self.scp(self.userkey, "munge.key", instance['ip'])
			self.ssh(self.userkey, instance['ip'], "sudo cp munge.key /etc/munge/munge.key")
			self.ssh(self.userkey, instance['ip'], "sudo chown munge /etc/munge/munge.key")
			self.ssh(self.userkey, instance['ip'], "sudo chgrp munge /etc/munge/munge.key")
			self.ssh(self.userkey, instance['ip'], "sudo chmod 400 /etc/munge/munge.key")
			
			# start slurm
			print '\n...starting slurm......'
			self.ssh(self.userkey, instance['ip'], "sudo /etc/init.d/slurm-llnl start")
			self.ssh(self.userkey, instance['ip'], "sudo /etc/init.d/munge start")

def usage():
        print '-h/--help    Display this help.'
        print '-u/--userkey provide userkey'
        print '-n/--number  provide number of nodes(control node not included)'
        print '-s/--size    provide size of cluster(control node not included) default: s1.small'
	print '-a/--name    provide name of virtual cluster.' 

def main():
	
	size = None
        
	try:
                opts, args = getopt.getopt(sys.argv[1:], "hu:n:s:i:a:rc:", ["help", "userkey=", "number=", \
			"size=", "image=", "name="])
        except getopt.GetoptError:
                usage()
                sys.exit()

        for opt, arg in opts:
                if opt in ("-h", "--help"):
                        usage()
                        sys.exit()
                elif opt in ("-u", "--userkey"):
                        userkey=arg
                elif opt in ("-n", "--number"):
                        number=arg
                elif opt in ("-s", "--size"):
			size=arg
                elif opt in ("-i", "--image"):
 			image=arg
		elif opt in ("-a", "--name"):
			name=arg
		   						
	if size == None:
	        fgc=FgCreate(userkey, number, image, name)
	else: 	
		fgc=FgCreate(userkey, number, image, name, size)

	# create cluster
	fgc.create_cluster()
	# check if all alive
	fgc.detect_port()
	# deploy slurm
	fgc.deploy_slurm()
	# clean
	fgc.clean()

if __name__ == '__main__':
    main()
