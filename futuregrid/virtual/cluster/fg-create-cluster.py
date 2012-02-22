#! /usr/bin/env python
import socket, time, getopt, sys, os

class FgCreate:
        def __init__(self):
		pass

	def _run(command):
	        return os.popen(command)

        def detect_port(self, ip, host):
                while 1:
                        try:
                                sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                                sk.settimeout(1)
                                sk.connect((ip, port))
                                sk.close()
                                print 'Ready to deploy'
                                break
                        except Exception:
                                print 'not ready to deploy yet'
                                time.sleep(2)

        def create_cluster(self, userkey, number, image, name, size='m1.small'):
		print 'Creating virtual cluster...'
		print 'name   -- ', name
		print '#nodes -- ', number
		print 'size   -- ', size
		print 'image  -- ', image		
		
		os.makedirs("futuregrid/cluster/%s" %name)
		os.chdir("futuregrid/cluster/%s" %name)

		cluster_size = int(number)+1
#		print "euca-run-instances -k %s -n %d -t %s %s"  %(userkey, cluster_size, size, image)		
		os.system("euca-run-instances -k %s -n %d -t %s %s"  %(userkey, cluster_size, size, image))
#		result=os.popen("euca-run-instances -k %s.pem -n %d -t %s %s"  %(userkey, int(number), size, image)).read()
		os.system("euca-describe-instances|awk {'if ($2 ~ /^i/) print $2'}|sort|tail -n%d > instance_id.tmp" %cluster_size) 
		os.system("euca-describe-addresses |grep -v 'i' |cut -f2 |sort |head -n%d > instance_ip.tmp" %cluster_size)
		os.system("euca-describe-instances|awk {'if ($2 ~ /^i/) print $2,$3'}|sort|tail -n%d|awk {'print $2'} > image_id.tmp" %cluster_size)
		os.system("euca-describe-instances|awk {'if ($2 ~ /^i/) print $2,$5'}|sort|tail -n%d|awk {'print $2'} > inner_ip.tmp" %cluster_size)
		os.system("paste instance_id.tmp instance_ip.tmp image_id.tmp inner_ip.tmp> my_instances_list.txt")
	
		f = file('my_instances_list.txt')	
		while True:
			line = f.readline()
			os.system("euca-associate-address -i `echo %s|awk {'print $1'}` `echo %s|awk {'print $2'}`" %(line, line))
    			if len(line) == 0: 
				break
		f.close()

	def clean(self, name):
         	os.chdir("futuregrid/cluster/%s" %name)
		os.remove('rm instance_id.tmp')
		os.remove('rm instance_ip.tmp')
		os.remove('rm image_id.tmp')
		os.remove('rm inner_ip.tmp')

#	def deploy_slurm():
		

def usage():
        print '-h/--help    Display this help.'
        print '-u/--userkey provide userkey'
        print '-n/--number  provide number of nodes(control node not included)'
        print '-s/--size    provide size of cluster(control node not included) default: s1.small'

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
            						
        fgc=FgCreate()
	
	if size == None:
	        fgc.create_cluster(userkey, number, image, name)
	else:
		fgc.create_cluster(userkey, number, image, name, size)

	fgc.clean(name)

if __name__ == '__main__':
    main()
