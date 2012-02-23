#! /usr/bin/env python

import socket, time, getopt, sys, os

class FgCreate:

        userkey=compute_number=control_image=compute_image=name=size=None

        def __init__(self, userkey, number, control_image, compute_image, name, size='m1.small'):
                self.userkey = userkey
                self.compute_number = number
                self.control_image = control_image
		self.compute_image = compute_image
                self.name = name
                self.size= size


	def create_cluster(self):

		cluster_size = int(self.compute_number)+1
                print '\n...Restoring virtual cluster......'
                print 'name   -- ', self.name
                print '#nodes -- ', cluster_size
                print 'size   -- ', self.size
                print 'control image  -- ', self.control_image
		print 'compute image  -- ', self.compute_image
                print '\n'

                # create folder for cluster given name
#               try:
#                       os.makedirs("futuregrid/cluster/%s" %self.name)
#                       os.chdir("futuregrid/cluster/%s" %self.name)
#               except Exception:
#                       print "Creating directory futuregrid/cluster/%s falied. Cluster name is in use?" %self.name
#                       sys.exit()

                # size of cluster is user input + 1 control node
                # run control node given args
                os.system("euca-run-instances -k %s -n 1 -t %s %s"  %(self.userkey, self.size, self.control_image))
		# run compute nodes 
		os.system("euca-run-instances -k %s -n %d -t %s %s"  %(self.userkey, int(self.compute_number), self.size, self.compute_image))

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
                        userkey=arg
                elif opt in ("-n", "--number"):
                        number=arg
                elif opt in ("-s", "--size"):
                        size=arg
                elif opt in ("-i", "--image"):
                        control_image=arg
                elif opt in ("-a", "--name"):
                        name=arg
		elif opt in ("-c", "--compute"):
			compute_image=arg

        if size == None:
                fgc=FgCreate(userkey, number, control_image, compute_image, name)
        else:
             	fgc=FgCreate(userkey, number, control_image, compute_image, name, size)

        # create cluster
        fgc.create_cluster()
        fgc.clean()

if __name__ == '__main__':
    main()

