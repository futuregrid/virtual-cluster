#! /usr/bin/env python

import getopt
import sys
import os

from futuregrid.virtual.cluster.CloudInstances import CloudInstances


class FgCheckpoint:

    def __init__(self, userkey, nova, control_b,
                 control_n, compute_b, compute_n, name):
        self.userkey = userkey
        self.nova = nova
        self.control_b = control_b
        self.control_n = control_n
        self.compute_b = compute_b
        self.compute_n = compute_n
        self.name = name
        self.cloud_instances = CloudInstances(name)

    def ssh(self, userkey, ip, command):
        os.system("ssh -i %s.pem ubuntu@%s '%s'" % (userkey, ip, command))

    def scp(self, userkey, filename, ip):
        os.system("scp -i %s.pem -r %s ubuntu@%s:~/" % (userkey, filename, ip))

    def save_instance(self, kernel_id, ramdisk_id, ip, instance_name):
        if kernel_id == None:
            return os.popen("ssh -i %s.pem ubuntu@%s '. "
                            "~/.profile; sudo euca-bundle-vol "
                            "-c ${EC2_CERT} -k ${EC2_PRIVATE_KEY} "
                            "-u ${EC2_USER_ID} --ec2cert ${EUCALYPTUS_CERT} "
                            "--no-inherit -p %s -s 1024 -d /mnt/'"
                            % (self.userkey, ip, instance_name)).read()
        elif ramdisk_id == None:
            return os.popen("ssh -i %s.pem ubuntu@%s '. "
                            "~/.profile; sudo euca-bundle-vol "
                            "-c ${EC2_CERT} -k ${EC2_PRIVATE_KEY} "
                            "-u ${EC2_USER_ID} --ec2cert ${EUCALYPTUS_CERT} "
                            "--no-inherit -p %s -s 1024 -d /mnt/ --kernel %s'"
                            % (self.userkey, ip, instance_name,
                               kernel_id)).read()
        else:
            return os.popen("ssh -i %s.pem ubuntu@%s '. "
                            "~/.profile; sudo euca-bundle-vol "
                            "-c ${EC2_CERT} -k ${EC2_PRIVATE_KEY} "
                            "-u ${EC2_USER_ID} --ec2cert ${EUCALYPTUS_CERT} "
                            "--no-inherit -p %s -s 1024 -d /mnt/ "
                            "--kernel %s --ramdisk %s'"
                            % (self.userkey, ip, instance_name,
                               kernel_id, ramdisk_id)).read()

    def upload_bundle(self, ip, bucket_name, manifest):
        return os.popen("ssh -i %s.pem ubuntu@%s '. "
                        "~/.profile; euca-upload-bundle -b %s -m %s'"
                        % (self.userkey, ip, bucket_name, manifest)).read()

    def describe_images(self, image_id):
        return os.popen("euca-describe-images %s" % image_id).read()

    def get_kernel_id(self, image_id):
        command_result = [x for x in self.describe_images(image_id).split()]
        if len(command_result) >= 8:
            return command_result[7]

    def get_ramdisk_id(self, image_id):
        command_result = [x for x in self.describe_images(image_id).split()]
        if len(command_result) == 9:
            return command_result[8]

    def save_node(self, image_id, ip, bucket_name, image_name):
        kernel_id = self.get_kernel_id(image_id)
        ramdisk_id = self.get_ramdisk_id(image_id)
        manifest = [x for x in self.save_instance
                    (kernel_id, ramdisk_id, ip, image_name).split()].pop()

        print '\nmanifest generated: %s' % manifest
        print '\n...uploading bundle......'

        image = [x for x in self.upload_bundle
                 (ip, bucket_name, manifest).split()].pop()

        print '\n...registering image......'
        self.euca_register(image)

    def euca_register(self, image):
        os.system("euca-register %s" % image)

    def checkpoint_cluster(self):

        print '\n...Saving virtual cluster......'
        print 'Virtual cluster name -- ', self.name
        print 'control node bucket  -- ', self.control_b
        print 'control node name    -- ', self.control_n
        print 'compute node bucket  -- ', self.compute_b
        print 'compute node name    -- ', self.compute_n
        print '\n'

        os.system("unzip -o %s -d keys" % self.nova)

        for instance in self.cloud_instances.list()[1:3]:
            self.scp(self.userkey, "keys", instance['ip'])
            self.ssh(self.userkey, instance['ip'], "cp keys/* ~/")
            self.ssh(self.userkey, instance['ip'], "cat novarc >> ~/.profile")
            self.ssh(self.userkey, instance['ip'], "source ~/.profile")

        #save control node
        self.save_node(self.cloud_instances.get_by_id(1)['image'],
                       self.cloud_instances.get_by_id(1)['ip'],
                       self.control_b,
                       self.control_n)
        #save compute node
        self.save_node(self.cloud_instances.get_by_id(2)['image'],
                       self.cloud_instances.get_by_id(2)['ip'],
                       self.compute_b,
                       self.compute_n)

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
        opts, args = getopt.getopt(sys.argv[1:],
                                   "hu:n:c:t:m:e:a:",
                                   ["help",
                                    "userkey=",
                                    "nova=",
                                    "controlb=",
                                    "controln=",
                                    "computeb=",
                                    "computen=",
                                    "name="])
    except getopt.GetoptError:
        usage()
        sys.exit()

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit()
        elif opt in ("-u", "--userkey"):
            userkey = arg
        elif opt in ("-n", "--nova"):
            nova = arg
        elif opt in ("-c", "--controlb"):
            control_bucket = arg
        elif opt in ("-t", "--controln"):
            control_name = arg
        elif opt in ("-m", "--computeb"):
            compute_bucket = arg
        elif opt in ("-e", "--computen"):
            compute_name = arg
        elif opt in ("-a", "--name"):
            name = arg

    fgc = FgCheckpoint(userkey, nova,
                       control_bucket, control_name,
                       compute_bucket, compute_name, name)
    fgc.checkpoint_cluster()


if __name__ == '__main__':
    main()
