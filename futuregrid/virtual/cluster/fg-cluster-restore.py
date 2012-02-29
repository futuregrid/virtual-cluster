#! /usr/bin/env python

import socket, getopt, sys, os, time, pickle

class CloudInstances:

	cloud_instances = []
	
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
			f = open("cloud_instances.dat", "r")
			instance_list = pickle.load(f)
			instance_list.insert(0, self.cloud_instances)
			f = open("cloud_instances.dat", "w")
			pickle.dump(instance_list, f)	
			f.close()		
		except:
			f = open("cloud_instances.dat", "w")
			pickle.dump([self.cloud_instances], f)
			f.close()

	def check_name(self, name):
		try:
			f = open("cloud_instances.dat", "r")
			cloud_list = pickle.load(f)
			for cloud in cloud_list:
				if cloud[0]['name'] == name:
					return False
			return True
		except:
			return True

class FgRestore:

        userkey=compute_number=control_image=compute_image=name=size=None

        def __init__(self, userkey, number, control_image, compute_image, name, size='m1.small'):
                self.userkey = userkey
                self.compute_number = number
                self.control_image = control_image
		self.compute_image = compute_image
                self.name = name
                self.size = size
		self.cloud_instances = CloudInstances(name)
	
	def get_command_result(self, command):
		return os.popen(command).read()	

	def euca_run_instance (self, userkey, cluster_size, image, instance_type):
		eui_overhead = 3
		eui_id_pos = 2
		eui_len = 8
		instances = [x for x in self.get_command_result("euca-run-instances -k %s -n %d -t %s %s"  
								% (userkey, cluster_size, instance_type, image)).split()]
		for num in range(cluster_size):
			self.cloud_instances.set(instances[num * eui_len + eui_id_pos + eui_overhead], image)
		
	def euca_associate_address (self, instance_id, ip):
		os.system("euca-associate-address -i %s %s" % (instance_id, ip))
		self.cloud_instances.set_ip_by_id(instance_id, ip)

	def euca_describe_addresses (self):
		ip_list = []
		ips = [x for x in os.popen("euca-describe-addresses").read().split('\n')]
		for ip in ips:
			if  ip.find('i-') < 0 and len(ip) > 0:
				ip_list.append(ip.split('\t')[1])
		return ip_list

	def ssh (self, userkey, ip, command):
		os.system("ssh -i %s.pem ubuntu@%s '%s'" % (userkey, ip, command))
		
	def scp (self, userkey, filename, ip):
		os.system("scp -i %s.pem %s ubuntu@%s:~/" % (userkey, filename, ip))

	def detect_port(self):
                ready = 0

                # check if shh port of all VMs are alive
                while 1:
                        for instance in self.cloud_instances.list()[1:]:
                                try:
                                    	sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                                        sk.settimeout(2)
                                        sk.connect((instance['ip'], 22))
                                        sk.close()
                                       	ready = ready + 1
					print '%s is ready', instance['ip']
                                except Exception:
                                       	print 'Waitting VMs ready to deploy...'
                                       	ready = 0
                                        time.sleep(2)

                        # check if all vms are ready
			print 'ready -- %d, len -- %d' % (ready, len(self.cloud_instances.list()[1:]))
                        if ready == len(self.cloud_instances.list()[1:]):
                                break


	def create_cluster(self):

		cluster_size = int(self.compute_number) + 1
                print '\n...Restoring virtual cluster......'
                print 'virtual cluster name   -- ', self.name
                print 'number of nodes        -- ', cluster_size
                print 'instance type          -- ', self.size
                print 'control image          -- ', self.control_image
		print 'compute image          -- ', self.compute_image
                print '\n'

		self.euca_run_instance(self.userkey, 1, self.control_image, self.size)
		self.euca_run_instance(self.userkey, int(self.compute_number), self.compute_image, self.size)	

		ip_lists = self.euca_describe_addresses ()

		# immediatly associate ip after run instance may lead to error, use sleep
		time.sleep(3)

		print '...Associating IPs......'
		for i in range(cluster_size):
			instance = self.cloud_instances.get_by_id(i+1)
			self.euca_associate_address (instance['id'], ip_lists[i])

		self.cloud_instances.save_instances()
	
		with open("slurm.conf.in") as srcf:
    			input_content = srcf.readlines()
		srcf.close()
		
		controlMachine = self.cloud_instances.get_by_id(1)['id']
		output = "".join(input_content) % vars()

		destf = open("slurm.conf","w")
		print >> destf, output
		destf.close()

		with open("slurm.conf", "a") as conf:
			for instance in self.cloud_instances.list()[2:]:
				conf.write("NodeName=%s Procs=1 State=UNKNOWN\n" % instance['id'])
				conf.write("PartitionName=debug Nodes=%s Default=YES MaxTime=INFINITE State=UP\n" 
					   % instance['id'])
		conf.close()

		self.detect_port()

		print '\n...Configuring SLURM......'
		for instance in self.cloud_instances.list()[1:]:
			# copy slurm.conf
			print '\n...copying slurm.conf to node......'
			self.scp(self.userkey, "slurm.conf", instance['ip'])
			self.ssh(self.userkey, instance['ip'], "sudo cp slurm.conf /etc/slurm-llnl")

			# start slurm
			print '\n...starting slurm......'
			self.ssh(self.userkey, instance['ip'], "sudo /etc/init.d/slurm-llnl start")
			self.ssh(self.userkey, instance['ip'], "sudo /etc/init.d/munge start")



	def clean(self):
                print '...Clearing up......'
		print '...Done......'

		
def usage():
        print '-h/--help    Display this help.'
        print '-u/--userkey provide userkey'
        print '-n/--number  provide number of nodes(control node not included)'
        print '-s/--size    provide size of cluster(control node not included) default: s1.small'
        print '-a/--name    provide name of virtual cluster.'

def main():
	userkey=number=control_image=compute_image=size=name=None

        try:
                opts, args = getopt.getopt(sys.argv[1:], "hu:n:s:i:a:c:", ["help", "userkey=", "number=", \
                        "size=", "image=", "name=", "compute="])
        except getopt.GetoptError:
                usage()
                sys.exit()

        for opt, arg in opts:
                if opt in ("-h", "--help"):
                        usage()
                        sys.exit()
                elif opt in ("-u", "--userkey"):
                        userkey = arg
                elif opt in ("-n", "--number"):
                        number = arg
                elif opt in ("-s", "--size"):
                        size = arg
                elif opt in ("-i", "--image"):
                        control_image = arg
                elif opt in ("-a", "--name"):
                        name = arg
		elif opt in ("-c", "--compute"):
			compute_image = arg

        if size == None:
                fgc=FgRestore(userkey, number, control_image, compute_image, name)
        else:
             	fgc=FgRestore(userkey, number, control_image, compute_image, name, size)

        # create cluster
        fgc.create_cluster()

if __name__ == '__main__':
    main()

