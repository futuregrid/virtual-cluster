#! /usr/bin/env python

import socket, time, getopt, sys, os

"""
class CloudInstances:

	cloud_instances = {}
	
	def __init__(self):
                slef.clear()
		return

	def list(self):
		return cloud_instances

	def set(self, label, ip, id, type, image):
		instance['ip'] = ip
		instance['id'] = id
		instance['no'] = size
                coud_instances[size] = instance 
                size +=1


		# ...

	def clear(self):
                self.size = 0
		self.cloud_instances = {}

	def get (self, id):
		return cloud_instance[id]

	# def run_instance(self, ...)

	# def get_address(self, id)
	
	# whateve else you need

	# save() pickle

	# reload()
"""

class FgCreate:

	userkey=number=image=name=size=None

        def __init__(self, userkey, number, image, name, size='m1.small'):
		self.userkey = userkey
		self.number = number
		self.image = image
		self.name = name
		self.size= size			

        def detect_port(self):
		line_num = 0
		nodes_list = []
		ready = 0
		
		# save all nodes info into list
		f = file('my_instances_list.txt')
                while True:
                        line = f.readline()
                        if len(line) == 0:
                                break
                        line_num = line_num + 1
                        line = [x for x in line.split()]
                        nodes_list.append(line)
                f.close()

		# check if shh port of all VMs are alive
		while 1:
			for vm in nodes_list:
                		try:
					sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        	                        sk.settimeout(1)
                	                sk.connect((vm[1], 22))
                        	        sk.close()
					ready = ready + 1					
	                        except Exception:
        	                        print 'Waitting VMs ready to deploy...'
					ready = 0
                        	        time.sleep(2)
			# check if all vms are ready			
			if ready == len(nodes_list):
				break
"""
	def euca_run_instance (self, userkey, cluster_size, type, image)
		os.system("euca-run-instances -k %s -n %d -t %s %s"  %(userkey, cluster_size, type, image))
		#pipe output to string, take second argument and than simple reurn this
		

	def apt-get (slef, key, ip, packeName):
		# fix this next line
		os.system("ssh -i %s.pem -n ubuntu@%s 'sudo apt-get update'" %(self.userkey, line[1]))

	def ssh (self, key, ip, command)
		# fix this
"""
			
        def create_cluster(self):
		print '\n...Creating virtual cluster......'
		print 'name   -- ', self.name
		print '#nodes -- ', self.number
		print 'size   -- ', self.size
		print 'image  -- ', self.image
		print '\n'		
		
		# create folder for cluster given name
#		try:
#			os.makedirs("futuregrid/cluster/%s" %self.name)
#			os.chdir("futuregrid/cluster/%s" %self.name)
#		except Exception:
#			print "Creating directory futuregrid/cluster/%s falied. Cluster name is in use?" %self.name
#			sys.exit()

		# size of cluster is user input + 1 control node
		cluster_size = int(self.number)+1
		# run instances given args
		os.system("euca-run-instances -k %s -n %d -t %s %s"  %(self.userkey, cluster_size, self.size, self.image))

		print '\n......Associating public IPs......'	
		# save virtual cluster instances id into tmp
		os.system("euca-describe-instances|awk {'if ($2 ~ /^i/) print $2'}|sort|tail -n%d > instance_id.tmp" %cluster_size) 
		# save virtual cluster instances ip into tmp
		os.system("euca-describe-addresses |grep -v 'i' |cut -f2 |sort |head -n%d > instance_ip.tmp" %cluster_size)
		# save virtual cluster image id into tmp
		os.system("euca-describe-instances|awk {'if ($2 ~ /^i/) print $2,$3'}|sort|tail -n%d|awk {'print $2'} > image_id.tmp" %cluster_size)
		# sav virtual cluster intranet ip into tmp
		os.system("euca-describe-instances|awk {'if ($2 ~ /^i/) print $2,$5'}|sort|tail -n%d|awk {'print $2'} > inner_ip.tmp" %cluster_size)
		# combine all tmps into one file for managemnt
		os.system("paste instance_id.tmp instance_ip.tmp image_id.tmp inner_ip.tmp> my_instances_list.txt")
		
		f = file('my_instances_list.txt')	
		while True:
			line = f.readline()
			if len(line) == 0:
				break
			line = [x for x in line.split()]
			os.system("euca-associate-address -i %s %s" %(line[0], line[1]))

	def clean(self):
		print '...Clearing up......'
		os.remove('instance_id.tmp')
		os.remove('instance_ip.tmp')
		os.remove('image_id.tmp')
		os.remove('inner_ip.tmp')
		print '...Done......'

	def deploy_slurm(self):
		print '\n...Deploying SLURM system......'

		line_num = 0
		control_node = None
		compute_node_list = []

		f = file('my_instances_list.txt')
		while True:
			line = f.readline()
			if len(line) == 0:
				break
			line_num = line_num + 1
			line = [x for x in line.split()]
			compute_node_list.append(line)
			os.system("ssh -i %s.pem -n ubuntu@%s 'sudo apt-get update'" %(self.userkey, line[1]))
			os.system("ssh -i %s.pem -n ubuntu@%s 'sudo apt-get install --yes slurm-llnl'" %(self.userkey, line[1]))
			os.system("ssh -i %s.pem -n ubuntu@%s 'sudo apt-get install --yes openmpi-bin openmpi-doc libopenmpi-dev'" %(self.userkey, line[1]))
			if line_num == 1:
				control_node = line
				continue
			
		f.close()
		print control_node
		print compute_node_list
		source_file = open('slurm.conf.in')
		dest_file = open('slurm.conf', 'a')
		while True:
			line = source_file.readline()
			if len(line) == 0:
				break
			if line.find('ControlMachine') > -1:
				dest_file.write("ControlMachine=%s\n" %control_node[0])		
			else:
				dest_file.write(line)
		source_file.close()
		dest_file.close()
		# add compute nodes info
		line_num = 0
		f = file('my_instances_list.txt')
		conf_file = open('slurm.conf', 'a')
		while True:
			line = f.readline()
			if len(line) == 0:
				break
			line_num = line_num + 1
			line = [x for x in line.split()]
			if line_num == 1:
				continue
			conf_file.write("NodeName=%s Procs=1 State=UNKNOWN\n" %line[0])
			conf_file.write("PartitionName=debug Nodes=%s Default=YES MaxTime=INFINITE State=UP\n" %line[0])
		f.close()

		# copy slurm.conf to control node
		os.system("scp -i %s.pem slurm.conf ubuntu@%s:~/" %(self.userkey, control_node[1]))
		os.system("ssh -i %s.pem -n ubuntu@%s 'sudo cp slurm.conf /etc/slurm-llnl'" %(self.userkey, control_node[1]))

		# genreate munge key on control node and copy it to compute nodes
		# copy slurm.conf to every compute node
		# print control_node, compute_node_list		
		os.system("ssh -i %s.pem -n ubuntu@%s 'sudo /usr/sbin/create-munge-key'" %(self.userkey, control_node[1]))
                os.system("ssh -i %s.pem -n ubuntu@%s 'sudo cat /etc/munge/munge.key' > munge.key" %(self.userkey, control_node[1]))
		for nodes in compute_node_list:
			os.system("scp -i %s.pem munge.key ubuntu@%s:~/" %(self.userkey, nodes[1]))
			os.system("ssh -i %s.pem -n ubuntu@%s 'sudo cp munge.key /etc/munge/munge.key'" %(self.userkey, nodes[1]))
			os.system("ssh -i %s.pem -n ubuntu@%s 'sudo chown munge /etc/munge/munge.key'" %(self.userkey, nodes[1]))
			os.system("ssh -i %s.pem -n ubuntu@%s 'sudo chgrp munge /etc/munge/munge.key'" %(self.userkey, nodes[1]))
			os.system("ssh -i %s.pem -n ubuntu@%s 'sudo chmod 400 /etc/munge/munge.key'" %(self.userkey, nodes[1]))
			os.system("scp -i %s.pem slurm.conf ubuntu@%s:~/" %(self.userkey, nodes[1]))
			os.system("ssh -i %s.pem -n ubuntu@%s 'sudo cp slurm.conf /etc/slurm-llnl/slurm.conf'" %(self.userkey, nodes[1]))

		print '\n...Starting SLURM system......\n'
		# run slurm on control node
		os.system("ssh -i %s.pem -n ubuntu@%s 'sudo /etc/init.d/slurm-llnl start'" %(self.userkey, control_node[1]))
		os.system("ssh -i %s.pem -n ubuntu@%s 'sudo /etc/init.d/munge start'" %(self.userkey, control_node[1]))
		
		# run slurm on compute node
		for nodes in compute_node_list:
			os.system("ssh -i %s.pem -n ubuntu@%s 'sudo /etc/init.d/slurm-llnl start'" %(self.userkey, nodes[1]))
	                os.system("ssh -i %s.pem -n ubuntu@%s 'sudo /etc/init.d/munge start'" %(self.userkey, nodes[1]))

		


def usage():
        print '-h/--help    Display this help.'
        print '-u/--userkey provide userkey'
        print '-n/--number  provide number of nodes(control node not included)'
        print '-s/--size    provide size of cluster(control node not included) default: s1.small'
	print '-a/--name    provide name of virtual cluster.' 

def main():
	userkey=number=image=size=name=None

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
	#fgc.associate_ip()
	# check if all alive
	fgc.detect_port()
	# deploy slurm
	fgc.deploy_slurm()
	# clean
	fgc.clean()

if __name__ == '__main__':
    main()
