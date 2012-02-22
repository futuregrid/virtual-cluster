#! /usr/bin/env python
import StringIO
import ConfigParser
import socket, time, getopt, sys, os

class FgCreate:

	userkey=number=image=name=size=None

        def __init__(self, userkey, number, image, name, size='m1.small'):
		self.userkey = userkey
		self.number = number
		self.image = image
		self.name = name
		self.size= size			

	def _run(command):
	        return os.popen(command)

        def detect_port(self, ip, host):
                while 1:
                        try:
                                sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                                sk.settimeout(1)
                                sk.connect((ip, port))
                                sk.close()
                                print 'Ready to deploy...'
                                break
                        except Exception:
                                print 'Waitting VMs ready to deploy...'
                                time.sleep(2)

        def create_cluster(self):
		print '\n...Creating virtual cluster......'
		print 'name   -- ', self.name
		print '#nodes -- ', self.number
		print 'size   -- ', self.size
		print 'image  -- ', self.image
		print '\n'		
		
#		try:
#			os.makedirs("futuregrid/cluster/%s" %self.name)
#			os.chdir("futuregrid/cluster/%s" %self.name)
#		except Exception:
#			print "Creating directory futuregrid/cluster/%s falied. Cluster name is in use?" %self.name
#			sys.exit()

		cluster_size = int(self.number)+1
		os.system("euca-run-instances -k %s -n %d -t %s %s"  %(self.userkey, cluster_size, self.size, self.image))
		os.system("euca-describe-instances|awk {'if ($2 ~ /^i/) print $2'}|sort|tail -n%d > instance_id.tmp" %cluster_size) 
		os.system("euca-describe-addresses |grep -v 'i' |cut -f2 |sort |head -n%d > instance_ip.tmp" %cluster_size)
		os.system("euca-describe-instances|awk {'if ($2 ~ /^i/) print $2,$3'}|sort|tail -n%d|awk {'print $2'} > image_id.tmp" %cluster_size)
		os.system("euca-describe-instances|awk {'if ($2 ~ /^i/) print $2,$5'}|sort|tail -n%d|awk {'print $2'} > inner_ip.tmp" %cluster_size)
		os.system("paste instance_id.tmp instance_ip.tmp image_id.tmp inner_ip.tmp> my_instances_list.txt")
		
		print '...Associating public IPs......'
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
			line = [x for x in line.split()]
#			os.system("ssh -i %s.pem -n ubuntu@%s 'sudo apt-get update'" %(self.userkey, line[1]))
#			os.system("ssh -i %s.pem -n ubuntu@%s 'sudo apt-get install --yes slurm-llnl'" %(self.userkey, line[1]))
		f.close()

#		cp = ConfigParser.ConfigParser()
		
#		config = StringIO.StringIO()
#		config.write('[dummysection]')
#		config.write(open('slurm.conf', 'r').read())
#		config.seek(0, os.SEEK_SET)

#		cp.readfp(config)
#		cp.set("dummysection","controlmachine", "aa")
#		cp.write(open('slurm.conf', 'w'))
		
#		os.system("sed -i '1d' slurm.conf")
		
		# add compute nodes info
		f = file('my_instances_list.txt')
		conf_file = open('slurm.conf', 'a')
		while True:
			line = f.readline()
			if len(line) == 0:
				break
			line_num = line_num + 1
			line = [x for x in line.split()]
			if line_num == 1:
				control_node = line
				continue
			compute_node_list.append(line)
#			line = [x for x in line.split()]
			conf_file.write("NodeName=%s Procs=1 State=UNKNOWN\n" %line[0])
			conf_file.write("PartitionName=debug Nodes=%s Default=YES MaxTime=INFINITE State=UP\n" %line[0])
		f.close()

		# copy slurm.conf to control node
		os.system("scp -i %s.pem slurm.conf ubuntu@%s:~/" %(self.userkey, control_node[1]))
		os.system("ssh -i %s.pem -n ubuntu@%s 'sudo cp slurm.conf /etc/slurm-llnl/slurm.conf'" %(self.userkey, control_node[1]))

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
		os.system("ssh -i $1.pem -n ubuntu@%s 'sudo /etc/init.d/munge start'" %(self.userkey, control_node[1]))
		
		# run slurm on compute node
		for nodes in compute_node_list:
			os.system("ssh -i %s.pem -n ubuntu@%s 'sudo /etc/init.d/slurm-llnl start'" %(self.userkey, nodes[1]))
	                os.system("ssh -i $1.pem -n ubuntu@%s 'sudo /etc/init.d/munge start'" %(self.userkey, nodes[1]))

		


def usage():
        print '-h/--help    Display this help.'
        print '-u/--userkey provide userkey'
        print '-n/--number  provide number of nodes(control node not included)'
        print '-s/--size    provide size of cluster(control node not included) default: s1.small'
	print '-a/--name    provide name of virtual cluster.' 

def main():
	userkey=number=image=size=name=None

        try:
                opts, args = getopt.getopt(sys.argv[1:], "hu:n:s:i:a:", ["help", "userkey=", "number=", "size=", "image=", "name="])
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

	fgc.create_cluster()
	fgc.deploy_slurm()
	fgc.clean()

if __name__ == '__main__':
    main()
