#! /usr/bin/env python
import socket, time, getopt, sys, os

class FgCheckpoint:

        def __init__(self, userkey, nova, control_b, control_n, compute_b, compute_n):
                self.userkey = userkey
                self.nova = nova
		self.control_b = control_b
		self.control_n = control_n
		self.compute_b = compute_b
		self.compute_n = compute_n

	def __save_instance(self, kernel_id, ramdisk_id, line, instance_name):
		if len(kernel_id) == 1:
			result=os.popen("ssh -i %s.pem ubuntu@%s '. ~/.profile; sudo euca-bundle-vol -c ${EC2_CERT} -k ${EC2_PRIVATE_KEY} -u ${EC2_USER_ID} --ec2cert ${EUCALYPTUS_CERT} --no-inherit -p %s -s 1024 -d /mnt/'" %(self.userkey, line[1], instance_name)).read()
		elif len(ramdisk_id) == 1:
			result=os.popen("ssh -i %s.pem ubuntu@%s '. ~/.profile; sudo euca-bundle-vol -c ${EC2_CERT} -k ${EC2_PRIVATE_KEY} -u ${EC2_USER_ID} --ec2cert ${EUCALYPTUS_CERT} --no-inherit -p %s -s 1024 -d /mnt/ --kernel %s'" %(self.userkey, line[1], self.control_n, kernel_id)).read()
		else:
			result=os.popen("ssh -i %s.pem ubuntu@%s '. ~/.profile; sudo euca-bundle-vol -c ${EC2_CERT} -k ${EC2_PRIVATE_KEY} -u ${EC2_USER_ID} --ec2cert ${EUCALYPTUS_CERT} --no-inherit -p %s -s 1024 -d /mnt/ --kernel %s --ramdisk %s'" %(self.userkey, line[1], self.control_n, kernel_id, ramdisk_id)).read()
		return result

	def __upload_bundle(self, line, bucket_name, manifest):
		result=os.popen("ssh -i %s.pem ubuntu@%s '. ~/.profile; euca-upload-bundle -b %s -m %s'" %(self.userkey, line[1], bucket_name, manifest)).read()
		return result

	def checkpoint_cluster(self):
		
                print '\n...Saving virtual cluster......'
                print 'control node bucket  -- ', self.control_b
                print 'control node name    -- ', self.control_n
                print 'compute node bucket  -- ', self.compute_b
                print 'compute node name    -- ', self.compute_n
                print '\n'
	
		line_num = 0
		os.system("unzip -o %s -d keys" %self.nova)
		f = file('my_instances_list.txt')
                while True:
			line = [x for x in f.readline().split()]
                	os.system("scp -i %s.pem -r keys ubuntu@%s:~/" %(self.userkey, line[1]))
			os.system("ssh -i %s.pem ubuntu@%s 'cp keys/* ~/'" %(self.userkey, line[1]))
			#os.system("ssh -i %s.pem ubuntu@%s 'cat %s >> ~/.bashrc'" %(self.userkey, line[1], self.nova))
			#os.system("ssh -i %s.pem ubuntu@%s 'source ~/.bashrc'" %(self.userkey, line[1]))
			os.system("ssh -i %s.pem ubuntu@%s 'cat novarc >> ~/.profile'" %(self.userkey, line[1]))
			os.system("ssh -i %s.pem ubuntu@%s 'source ~/.profile'" %(self.userkey, line[1]))
			

			if line_num == 0:
				print '\n...Saving control node......'
				kernel_id = os.popen("euca-describe-images|awk {'if ($2 ~ /^%s/) print $8'}" %line[2]).read()
				ramdisk_id = os.popen("euca-describe-images|awk {'if ($2 ~ /^%s/) print $9'}" %line[2]).read()				
				reval = [x for x in self.__save_instance(kernel_id, ramdisk_id, line, self.control_n).split()]
				manifest = reval[len(reval)-1]
				print '\nmanifest: %s' %manifest
				print '\n...uploading bundle......'
				reval = [x for x in self.__upload_bundle(line, self.control_b, manifest).split()]
				image = reval[len(reval)-1]
				print 'image: %s' %image
			
			elif line_num == 1:
				print '\n...Saving compute node......'
				kernel_id=os.popen("euca-describe-images|awk {'if ($2 ~ /^%s/) print $8'}" %line[2]).read()
				ramdisk_id=os.popen("euca-describe-images|awk {'if ($2 ~ /^%s/) print $9'}" %line[2]).read()
				#self.save_instance(kernel_id, ramdisk_id, line, self.compute_n)
				reval = [x for x in self.__save_instance(kernel_id, ramdisk_id, line, self.compute_n).split()]
				manifest = reval[len(reval)-1]
				print '\nmanifest: %s' %manifest
				print '\n...uploading bundle......'
				reval = [x for x in self.__upload_bundle(line, self.control_b, manifest).split()]
				image = reval[len(reval)-1]
				print 'image: %s' %image

			print '\n...registering bundle......\n'
			os.system("euca-register %s" %image)
			print '\n'

			if line_num == 1:
				break
			line_num = line_num + 1
		f.close()
		

	def clean(self):
                print '...Clearing up......'
                print '...Done......'

def usage():
        print '-h/--help        Display this help.'
        print '-u/--userkey     provide userkey'
        print '-n/--nova        nova env file'
        print '-c/--controlb    bucket name for control node'
        print '-t/--controln    name of control node'
	print '-m/--computeb    bucket name for compute node'
	print '-e/--computen    name of compute node'

def main():

        try:
		opts, args = getopt.getopt(sys.argv[1:], "hu:n:c:t:m:e:", ["help", "userkey=", "nova=", "controlb=", "controln=", "computeb=", "computen="])
        except getopt.GetoptError:
                usage()
                sys.exit()

        for opt, arg in opts:
                if opt in ("-h", "--help"):
                        usage()
                        sys.exit()
                elif opt in ("-u", "--userkey"):
                        userkey=arg
                elif opt in ("-n", "--nova"):
			nova=arg
		elif opt in ("-c", "--controlb"):
			control_bucket=arg
		elif opt in ("-t", "--controln"):
			control_name=arg
		elif opt in ("-m", "--computeb"):
			compute_bucket=arg
		elif opt in ("-e", "--computen"):
			compute_name=arg

	fgc = FgCheckpoint(userkey, nova, control_bucket, control_name, compute_bucket, compute_name)
	fgc.checkpoint_cluster()


if __name__ == '__main__':
    main()

