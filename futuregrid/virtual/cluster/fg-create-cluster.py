#! /usr/bin/env python

import socket
import time
import getopt
import sys
import os
import pickle


class CloudInstacnes:
    backup_file = 'cloud_instacnes.dat'
    cloud_instances = []

    def __init__(self, name):
        self.clear()
        if self.check_name(name):
            instance = {}
            instance['name'] = name
            self.cloud_instances.append(instance)
        else:
            print 'Error in creating virtual cluster. Name is in use?'
            sys.exit()
        return

    def list(self):
        return self.cloud_instances

    def set(self, instance_id, image_id, ip='ip'):
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

    def get_by_id(self, cloud_id):
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


class FgCreate:

    def __init__(self, userkey, number, image, name, size='m1.small'):
        self.userkey = userkey
        self.number = number
        self.image = image
        self.name = name
        self.size = size
        self.cloud_instances = CloudInstances(name)

    def detect_port(self):
        ready = 0
        # check if shh port of all VMs are alive
        while 1:
            for instace in self.cloud_instances.list()[1:]:
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
            if ready == len(self.cloud_instances.list()[1:]):
                break

    def get_command_result(self, command):
        return os.popen(command).read()

    def euca_run_instance(self, userkey, cluster_size, image, instance_type):
        eui_overhead = 3
        eui_id_pos = 2
        eui_len = 8
        instances = [x for x in
                    self.get_command_result(
                                        "euca-run-instances -k %s "
                                        "-n %d -t %s %s"
                                        % (userkey,
                                        cluster_size,
                                        instance_type,
                                        image)).split()]
        for num in range(cluster_size):
            self.cloud_instances.set(
                                    instances[num * eui_len +
                                            eui_id_pos + eui_overhead], image)

    def euca_associate_address(self, instance_id, ip):
        os.system("euca-associate-address -i %s %s"
                % (instance_id, ip))
        self.cloud_instances.set_ip_by_id(instance_id, ip)

    def euca_describe_addresses(self):
        ip_list = []
        ips = [x for x in
            os.popen("euca-describe-addresses").read().split('\n')]
        for ip in ips:
            if ip.find('i-') < 0 and len(ip) > 0:
                ip_list.append(ip.split('\t')[1])
                return ip_list

    def ssh(self, userkey, ip, command):
        os.system("ssh -i %s.pem ubuntu@%s '%s'" % (userkey, ip, command))

    def scp(self, userkey, fileName, ip):
        os.system("scp -i %s.pem %s ubuntu@%s:~/" % (userkey, fileName, ip))

    def create_cluster(self):
        print '\n...Creating virtual cluster......'
        print 'name   -- ', self.name
        print '#nodes -- ', self.number
        print 'size   -- ', self.size
        print 'image  -- ', self.image

        cluster_size = int(self.number) + 1
        self.euca_run_instance(
                            self.userkey,
                            cluster_size,
                            self.image,
                            self.size)
        ip_lists = self.euca_describe_addresses()
        time.sleep(3)

        print '...Associating IPs......'
        for i in range(cluster_size):
            instance = self.cloud_instances.get_by_id(i + 1)
            self.euca_associate_address(instance['id'], ip_lists[i])
        self.cloud_instances.save_instances()

    def deploy_slurm(self):
        print '\n...Deploying SLURM system......'
        for instance in self.cloud_instances.list()[1:]:
            self.ssh(self.userkey, instance['ip'],
                    "sudo apt-get update")
            self.ssh(self.userkey, instance['ip'],
                    "sudo apt-get install --yes slurm-llnl")
            self.ssh(self.userkey, instance['ip'],
                    "sudo apt-get install --yes openmpi-bin"
                    " openmpi-doc libopenmpi-dev")

        print '\n...slurm.conf......'
        with open("slurm.conf.in") as srcf:
            input_content = srcf.readlines()
            srcf.close()

        controlMachine = self.cloud_instances.get_by_id(1)['id']
        output = "".join(input_content) % vars()
        destf = open("slurm.conf", "w")
        print >> destf, output
        destf.close()

        with open("slurm.conf", "a") as conf:
            for instance in self.cloud_instances.list()[2:]:
                conf.write("NodeName=%s Procs=1 "
                        "State=UNKNOWN\n" % instance['id'])
                conf.write("PartitionName=debug "
                        "Nodes=%s Default=YES "
                        "MaxTime=INFINITE "
                        "State=UP\n" % instance['id'])
        conf.close()

        print '\n...generate munge-key......'
        # generate munge-key on control node
        self.ssh(self.userkey,
                self.cloud_instances.get_by_id(1)['ip'],
                "sudo /usr/sbin/create-munge-key")
        munge_key = open("munge.key", "w")
        print >>munge_key,\
        self.get_command_result(
                            "ssh -i %s.pem ubuntu@%s "
                            "'sudo cat /etc/munge/munge.key'"
                            % (self.userkey,
                            self.cloud_instances.get_by_id(1)['ip']))
        munge_key.close()

        for instance in self.cloud_instances.list()[1:]:
            # copy slurm.conf
            print '\n...copying slurm.conf to node......'
            self.scp(self.userkey, "slurm.conf", instance['ip'])
            self.ssh(self.userkey,
                    instance['ip'],
                    "sudo cp slurm.conf /etc/slurm-llnl")

            # copy munge key
            print '\n...copying munge-key to nodes......'
            self.scp(self.userkey,
                    "munge.key",
                    instance['ip'])
            self.ssh(self.userkey,
                    instance['ip'],
                    "sudo cp munge.key /etc/munge/munge.key")
            self.ssh(self.userkey,
                    instance['ip'],
                    "sudo chown munge /etc/munge/munge.key")
            self.ssh(self.userkey,
                    instance['ip'],
                    "sudo chgrp munge /etc/munge/munge.key")
            self.ssh(self.userkey,
                    instance['ip'],
                    "sudo chmod 400 /etc/munge/munge.key")

            # start slurm
            print '\n...starting slurm......'
            self.ssh(self.userkey, instance['ip'],
                    "sudo /etc/init.d/slurm-llnl start")
            self.ssh(self.userkey, instance['ip'],
                    "sudo /etc/init.d/munge start")


def usage():
    print '-h/--help    Display this help.'
    print '-u/--userkey provide userkey'
    print '-n/--number  provide number of nodes(control node not included)'
    print '-s/--size    provide size of cluster(control node not included) '
    'default: s1.small'
    print '-a/--name    provide name of virtual cluster.'


def main():

    size = None

    try:
        opts, args = getopt.getopt(sys.argv[1:],
                                "hu:n:s:i:a:rc:",
                                ["help",
                                "userkey=",
                                "number=",
                                "size=",
                                "image=",
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
        elif opt in ("-n", "--number"):
            number = arg
        elif opt in ("-s", "--size"):
            size = arg
        elif opt in ("-i", "--image"):
            image = arg
        elif opt in ("-a", "--name"):
            name = arg

    if size == None:
        fgc = FgCreate(userkey, number, image, name)
    else:
        fgc = FgCreate(userkey, number, image, name, size)

    # create cluster
    fgc.create_cluster()
    # check if all alive
    fgc.detect_port()
    # deploy slurm
    fgc.deploy_slurm()

if __name__ == '__main__':
    main()
