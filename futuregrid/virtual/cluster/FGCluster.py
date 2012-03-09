#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Operations for managing
virtual clusters
"""

import argparse
import sys
import os
import socket
import time
import ConfigParser

from futuregrid.virtual.cluster.CloudInstances import CloudInstances
from ConfigParser import NoOptionError


class Cluster(object):
    """class of methods for run, checkpoint,
    restore, terminate, show status of cluster
    """

    userkey = None
    if_debug = False
    cloud_instances = None
    backup_file = None
    user = None
    ec2_cert = None
    ec2_private_key = None
    eucalyptus_cert = None
    novarc = None
    slurm = None

    def __init__(self):
        super(Cluster, self).__init__()
        self.cloud_instances = CloudInstances()

# ---------------------------------------------------------------------
# METHODS TO PRINT HELP MESSAGES
# ---------------------------------------------------------------------

    @classmethod
    def msg(cls, message):
        '''method for printing messages'''

        print message

    def debug(self, message):
        '''method for printing debug message'''

        if self.if_debug:
            print '\r' + message

    def set_debug(self, if_debug=False):
        '''set debug flag'''

        self.if_debug = if_debug

# ---------------------------------------------------------------------
# METHOD TO PARSE CONFIGURATION FILE
# ---------------------------------------------------------------------

    def parse_conf(self, file_name='unspecified'):
        """
        Parse conf file if given, default location
        '~/.futuregrid/futuregrid.cfg'
        conf format:
        [virtual-cluster]
        backup = directory/virtual-cluster.dat
        userkey = directory/userkey.pem
        username = userkey
        ec2_cert = directory/cert.pem
        ec2_private_key = directory/pk.pem
        eucalyptus_cert = directory/cacert.pem
        novarc = directory/novarc
        """

        config = ConfigParser.ConfigParser()

        try:
            config.read([file_name,
                         os.path.expanduser('~/.futuregrid/futuregrid.cfg')])

            # default location ~/.futuregrid/futuregrid.cfg

            self.backup_file = config.get('virtual-cluster', 'backup')
            self.userkey = config.get('virtual-cluster', 'userkey')
            self.user = config.get('virtual-cluster', 'user')
            self.ec2_cert = config.get('virtual-cluster', 'ec2_cert')
            self.ec2_private_key = config.get('virtual-cluster',
                    'ec2_private_key')
            self.eucalyptus_cert = config.get('virtual-cluster',
                    'eucalyptus_cert')
            self.novarc = config.get('virtual-cluster', 'novarc')
            self.slurm = config.get('virtual-cluster', 'slurm')

            self.cloud_instances.set_backup_file(self.backup_file)

        except NoOptionError:
            self.msg('Error in reading configuration file!')
            sys.exit()

# ---------------------------------------------------------------------
# METHOD TO DETECT OPEN PORT
# ---------------------------------------------------------------------

    def detect_port(self):
        '''detect if ssh port 22 is alive for listening'''

        ready = 0
        count = 0
        msg_len = 5

        # check if shh port of all VMs are alive

        while 1:
            for instace in self.cloud_instances.get_list()[1:]:
                try:
                    socket_s = socket.socket(socket.AF_INET,
                            socket.SOCK_STREAM)
                    socket_s.settimeout(1)
                    socket_s.connect((instace['ip'], 22))
                    socket_s.close()
                    ready = ready + 1
                except IOError:
                    count += 1
                    if count > msg_len:
                        count = 0
                    sys.stdout.write('\rWaiting VMs ready to deploy'
                                     + '.' * count + ' ' * (msg_len - count))
                    sys.stdout.flush()
                    ready = 0
                    time.sleep(1)

            # check if all vms are ready

            if ready == len(self.cloud_instances.get_list()[1:]):
                break

# ---------------------------------------------------------------------
# METHODS TO DO RPCs
# ---------------------------------------------------------------------

    @classmethod
    def get_command_result(cls, command):
        '''gets command output'''
        return os.popen(command).read()

    def execute(self, instance, command):
        '''runs a command on the instance'''

        os.system("ssh -i %s ubuntu@%s '%s'" % (self.userkey,
                  instance['ip'], command))

    def copyto(self, instance, filename):
        '''copyies the named file to the instance'''

        os.system('scp -i %s %s ubuntu@%s:~/' % (self.userkey,
                  filename, instance['ip']))

    def update(self, instance):
        '''executes a software update on the specified instance'''

        self.execute(instance, 'sudo apt-get update')

    def install(self, instance, packagenames):
        '''installs the package names
        that are specified (blank separated on the given instance'''

        self.execute(instance, 'sudo apt-get install --yes '
                     + packagenames)

# ---------------------------------------------------------------------
# METHODS TO CREATE A VIRTUAL CLUSTER
# ---------------------------------------------------------------------

    def euca_run_instance(
        self,
        userkey,
        cluster_size,
        image,
        instance_type,
        ):
        '''runs instances given parameters'''

        instance_id_list = []

        instances = [x for x in
                     self.get_command_result(
                                             'euca-run-instances -k %s'
                                             ' -n %d -t %s %s'
                      % (userkey, cluster_size, instance_type,
                     image)).split()]

        for instance in instances:
            if instance.find('i-') == 0:
                instance_id_list.append(instance)

        # check if all instances are created correctly
        if not len(instance_id_list) == cluster_size:
            self.msg('\nError in creating cluster, please check your input')
            for created_instance_id in instance_id_list:
                self.terminate_instance(created_instance_id)
            sys.exit()

        for num in range(cluster_size):
            try:
                self.cloud_instances.set_instance(instance_id_list[num], image)
            except:
                self.msg('\nError in creating instances. Program will exit'
                         )
                sys.exit()

    def euca_associate_address(self, instance, free_ip):
        '''associates instance with ip'''

        os.system('euca-associate-address -i %s %s' % (instance['id'],
                  free_ip))
        self.cloud_instances.set_ip_by_id(instance['id'], free_ip)

    @classmethod
    def euca_describe_addresses(cls):
        '''return list of free ips'''

        ip_list = []
        ips = [x for x in os.popen('euca-describe-addresses'
               ).read().split('\n')]
        for free_ip in ips:
            if free_ip.find('i-') < 0 and len(free_ip) > 0:
                ip_list.append(free_ip.split('\t')[1])
        return ip_list

    def create_cluster(self, args):
        '''method for creating cluster'''

        if self.cloud_instances.if_exist(args.name):
            self.msg('\nError in creating virtual cluster %s, name is in use'
                      % args.name)
            sys.exit()

        cluster_size = int(args.number) + 1
        self.msg('\n...Creating virtual cluster......')
        self.msg('cluster name    -- %s' % args.name)
        self.msg('numbe of nodes  -- %s' % cluster_size)
        self.msg('instance type   -- %s' % args.type)
        self.msg('image id        -- %s' % args.image)

        self.cloud_instances.set_cloud_instances_by_name(args.name)

        self.euca_run_instance(self.user, cluster_size, args.image,
                               args.type)
        ip_lists = self.euca_describe_addresses()

        # immediatly associate ip after run instance
        # may lead to error, use sleep

        time.sleep(3)

        self.msg('\nAssociating IPs')
        for i in range(cluster_size):
            instance = self.cloud_instances.get_by_id(i + 1)
            time.sleep(1)
            self.euca_associate_address(instance, ip_lists[i])

        self.cloud_instances.save_instances()
        self.detect_port()

        time.sleep(3)

        self.deploy_services()

    def config_slurm(self, create_key=True):
        '''config slurm'''

        slurm_conf_file = 'slurm.conf'
        munge_key_file = 'munge.key'

        self.msg('\nConfiguring slurm.conf')
        with open(os.path.expanduser(self.slurm)) as srcf:
            input_content = srcf.readlines()
        srcf.close()

        controlMachine = self.cloud_instances.get_by_id(1)['id']
        output = ''.join(input_content) % vars()

        self.msg('\nControl node %s' % controlMachine)

        destf = open(slurm_conf_file, 'w')
        print >> destf, output
        destf.close()

        with open(slurm_conf_file, 'a') as conf:
            for instance in self.cloud_instances.get_list()[2:]:
                conf.write('NodeName=%s Procs=1 State=UNKNOWN\n'
                           % instance['id'])
                conf.write('PartitionName=debug Nodes=%s Default=YES'
                ' MaxTime=INFINITE State=UP\n'
                            % instance['id'])
        conf.close()

        if create_key:
            self.msg('\nGenerating munge-key')

            # generate munge-key on control node

            self.execute(self.cloud_instances.get_by_id(1),
                         'sudo /usr/sbin/create-munge-key')
            munge_key = open(munge_key_file, 'w')
            print >> munge_key, \
                self.get_command_result("ssh -i %s ubuntu@%s"
                                        " 'sudo cat /etc/munge/munge.key'"
                                         % (self.userkey,
                                        self.cloud_instances.get_by_id(1)['ip'
                                        ]))
            munge_key.close()

        for instance in self.cloud_instances.get_list()[1:]:

            # copy slurm.conf

            self.msg('\nCopying slurm.conf to node %s' % instance['id'])
            self.copyto(instance, slurm_conf_file)
            self.execute(instance, 'sudo cp slurm.conf /etc/slurm-llnl')

            # copy munge key
            if create_key:
                self.msg('\nCopying munge-key to node %s' % instance['id'])
                self.copyto(instance, munge_key_file)
                self.execute(instance,
                             'sudo cp munge.key /etc/munge/munge.key')
                self.execute(instance,
                             'sudo chown munge /etc/munge/munge.key')
                self.execute(instance,
                             'sudo chgrp munge /etc/munge/munge.key')
                self.execute(instance, 'sudo chmod 400 /etc/munge/munge.key'
                             )

            # start slurm

            self.msg('\nStarting slurm on node %s' % instance['id'])
            self.execute(instance, 'sudo /etc/init.d/slurm-llnl start')
            self.execute(instance, 'sudo /etc/init.d/munge start')

        # clean
        if create_key:
            os.remove(munge_key_file)
        os.remove(slurm_conf_file)

    def deploy_services(self):
        '''deploy SLURM and OpenMPI services'''

        self.msg('\nDeploying SLURM system')

        for instance in self.cloud_instances.get_list()[1:]:
            self.update(instance)
            self.install(instance, 'slurm-llnl')
            self.install(instance, "openmpi-bin openmpi-doc libopenmpi-dev")

        self.config_slurm()

# ---------------------------------------------------------------------
# METHODS TO SAVE RUNNING VIRTUAL CLUSTER
# ---------------------------------------------------------------------

    def save_instance(
        self,
        kernel_id,
        ramdisk_id,
        instance_ip,
        instance_name,
        ):
        '''save instance given paramenters'''

        if kernel_id == None:
            return os.popen("ssh -i %s ubuntu@%s '. ~/.profile;"
                            " sudo euca-bundle-vol -c ${EC2_CERT}"
                            " -k ${EC2_PRIVATE_KEY} -u ${EC2_USER_ID}"
                            " --ec2cert ${EUCALYPTUS_CERT} --no-inherit"
                            " -p %s -s 1024 -d /mnt/'"
                             % (self.userkey, instance_ip,
                                instance_name)).read()
        elif ramdisk_id == None:
            return os.popen("ssh -i %s ubuntu@%s '. ~/.profile;"
                            " sudo euca-bundle-vol -c ${EC2_CERT}"
                            " -k ${EC2_PRIVATE_KEY} -u ${EC2_USER_ID}"
                            " --ec2cert ${EUCALYPTUS_CERT} --no-inherit"
                            " -p %s -s 1024 -d /mnt/ --kernel %s'"
                             % (self.userkey, instance_ip, instance_name,
                            kernel_id)).read()
        else:
            return os.popen("ssh -i %s ubuntu@%s '. ~/.profile;"
                            " sudo euca-bundle-vol -c ${EC2_CERT}"
                            " -k ${EC2_PRIVATE_KEY} -u ${EC2_USER_ID}"
                            " --ec2cert ${EUCALYPTUS_CERT} --no-inherit"
                            " -p %s -s 1024 -d /mnt/ --kernel %s --ramdisk %s'"
                             % (self.userkey, instance_ip, instance_name,
                            kernel_id, ramdisk_id)).read()

    def upload_bundle(
        self,
        instance_ip,
        bucket_name,
        manifest,
        ):
        '''upload bundle given manifest'''

        return os.popen("ssh -i %s ubuntu@%s '. ~/.profile;"
                        " euca-upload-bundle -b %s -m %s'"
                         % (self.userkey, instance_ip, bucket_name,
                        manifest)).read()

    @classmethod
    def describe_images(cls, image_id):
        '''get images infos'''

        return os.popen('euca-describe-images %s' % image_id).read()

    def get_kernel_id(self, image_id):
        '''get kernel id'''

        command_result = [x for x in
                          self.describe_images(image_id).split()]
        if len(command_result) >= 8:
            return command_result[7]

    def get_ramdisk_id(self, image_id):
        '''get ramdisk id'''

        command_result = [x for x in
                          self.describe_images(image_id).split()]
        if len(command_result) == 9:
            return command_result[8]

    def save_node(
        self,
        image_id,
        instance_ip,
        bucket_name,
        image_name,
        ):
        '''save node given parameters'''

        kernel_id = self.get_kernel_id(image_id)
        ramdisk_id = self.get_ramdisk_id(image_id)
        manifest = [x for x in self.save_instance(kernel_id,
                    ramdisk_id, instance_ip, image_name).split()].pop()

        self.msg('\nManifest generated: %s' % manifest)
        self.msg('\nUploading bundle')

        image = [x for x in self.upload_bundle(instance_ip, bucket_name,
                 manifest).split()].pop()

        self.msg('\nRegistering image')
        self.euca_register(image)

    @classmethod
    def euca_register(cls, image):
        '''register image'''

        os.system('euca-register %s' % image)

    def checkpoint_cluster(self, args):
        '''method for saving currently running instance into image'''

        self.msg('\n...Saving virtual cluster......')
        self.msg('Virtual cluster name -- %s' % args.name)
        self.msg('control node bucket  -- %s' % args.controlb)
        self.msg('control node name    -- %s' % args.controln)
        self.msg('compute node bucket  -- %s' % args.computeb)
        self.msg('compute node name    -- %s' % args.computen)

        if not self.cloud_instances.if_exist(args.name):
            self.msg('Error in locating virtual cluster %s, not created'
                      % args.name)
            sys.exit()
        self.cloud_instances.get_cloud_instances_by_name(args.name)

        for instance in self.cloud_instances.get_list()[1:3]:
            self.copyto(instance, self.ec2_cert)
            self.copyto(instance, self.ec2_private_key)
            self.copyto(instance, self.eucalyptus_cert)
            self.copyto(instance, self.novarc)
            self.execute(instance, 'cat novarc >> ~/.profile')
            self.execute(instance, 'source ~/.profile')

        # save control node
        self.msg('\nSaving control node %s'
                 % self.cloud_instances.get_by_id(1)['id'])
        self.save_node(self.cloud_instances.get_by_id(1)['image'],
                       self.cloud_instances.get_by_id(1)['ip'],
                       args.controlb, args.controln)

        # save compute node
        self.msg('\nSaving compute node %s'
                 % self.cloud_instances.get_by_id(2)['id'])
        self.save_node(self.cloud_instances.get_by_id(2)['image'],
                       self.cloud_instances.get_by_id(2)['ip'],
                       args.computeb, args.computen)

# ---------------------------------------------------------------------
# METHODS TO RESTORE VIRTUAL CLUSTER
# ---------------------------------------------------------------------

    def restore_cluster(self, args):
        '''method for restoring cluster'''

        if self.cloud_instances.if_exist(args.name):
            self.msg('Error in creating virtual cluster %s, name is in use'
                      % args.name)
            sys.exit()

        self.cloud_instances.set_cloud_instances_by_name(args.name)
        cluster_size = int(args.number) + 1
        self.msg('\n...Restoring virtual cluster......')
        self.msg('cluster name      -- %s' % args.name)
        self.msg('number of nodes   -- %s' % cluster_size)
        self.msg('instance type     -- %s' % args.type)
        self.msg('control image     -- %s' % args.controli)
        self.msg('compute image     -- %s' % args.computei)

        self.euca_run_instance(self.user, 1, args.controli, args.type)
        self.euca_run_instance(self.user, int(args.number),
                               args.computei, args.type)

        ip_lists = self.euca_describe_addresses()

        time.sleep(3)

        self.msg('\nAssociating IPs')
        for i in range(cluster_size):
            time.sleep(1)
            instance = self.cloud_instances.get_by_id(i + 1)
            self.euca_associate_address(instance, ip_lists[i])

        self.cloud_instances.save_instances()
        self.detect_port()
        self.config_slurm(False)

# ---------------------------------------------------------------------
# METHODS TO TERMINATE NAD CLEANUP
# ---------------------------------------------------------------------

    def clean(self, name):
        '''clean cluster record in backup file'''

        self.msg('\rClearing up the instance: progress')
        self.cloud_instances.del_by_name(name)
        self.msg('\rClearing up the instance: completed')

    def terminate_instance(self, instance_id):
        '''terminate instance given instance id'''

        self.msg('terminating instance %s' % instance_id)
        os.system('euca-terminate-instances %s' % instance_id)

    def shut_down(self, args):
        '''method for shutting down a cluster'''

        if not self.cloud_instances.if_exist(args.name):
            self.msg('\nError in finding virtual cluster %s, not created.'
                      % args.name)
            sys.exit()

        self.cloud_instances.get_cloud_instances_by_name(args.name)

        for instance in self.cloud_instances.get_list()[1:]:
            self.terminate_instance(instance['id'])
        self.clean(args.name)

# ---------------------------------------------------------------------
# METHODS TO SHOW VIRTUAL CLUSTER(S) STATUS
# ---------------------------------------------------------------------

    def show_status(self, args):
        '''show status of cluster(s)'''

        if not args.name:
            for cloud in self.cloud_instances.get_all_cloud_instances():
                self.msg('\n=============================')
                self.msg('Virtual Cluster %s' % cloud[0]['name'])
                self.msg('=============================')
                for instance in cloud[1:]:
                    self.msg('instance %s: IP -- %s, image -- %s'
                             % (instance['id'], instance['ip'],
                             instance['image']))
        else:
            if not self.cloud_instances.if_exist(args.name):
                self.msg('Error in finding virtual cluster %s, not created.'
                          % args.name)
                sys.exit()
            self.cloud_instances.get_cloud_instances_by_name(args.name)
            self.msg('=============================')
            self.msg('Virtual Cluster %s' % args.name)
            self.msg('=============================')
            for instance in self.cloud_instances.get_list()[1:]:
                self.msg('instance %s: IP -- %s, image -- %s'
                         % (instance['id'], instance['ip'],
                         instance['image']))


######################################################################
# MAIN
######################################################################


def commandline_parser():
    '''parse commandline'''

    virtual_cluster = Cluster()

    parser = \
        argparse.ArgumentParser(description='Virtual'
                                ' cluster management operations')
    parser.add_argument('-f', '--file', action='store',
                        help='Specify futuregrid configure file')
    parser.add_argument('--debug', action='store_true')
    subparsers = parser.add_subparsers(help='commands')

    # status command

    status_parser = subparsers.add_parser('status',
            help='Show virtual cluster status')
    status_parser.add_argument('-a', '--name', action='store',
                               help='Show status of '
                               'virtual cluster of given name')
    status_parser.set_defaults(func=virtual_cluster.show_status)

    # run command

    run_parser = subparsers.add_parser('run',
            help='Create a virtual cluster')
    run_parser.add_argument('-a', '--name', action='store',
                            required=True, help='Virtual cluster name')
    run_parser.add_argument('-n', '--number', action='store',
                            required=True, help='Numbe of compute nodes'
                            )
    run_parser.add_argument('-t', '--type', action='store',
                            required=True, help='Instance type')
    run_parser.add_argument('-i', '--image', action='store',
                            required=True, help='Image id')
    run_parser.set_defaults(func=virtual_cluster.create_cluster)

    # terminate command

    terminate_parser = subparsers.add_parser('terminate',
            help='Terminate virtual cluster')
    terminate_parser.add_argument('-a', '--name', action='store',
                                  required=True,
                                  help='Virtual cluster name')
    terminate_parser.set_defaults(func=virtual_cluster.shut_down)

    # checkpoint command

    checkpoint_parser = subparsers.add_parser('checkpoint',
            help='Save virtual cluster')
    checkpoint_parser.add_argument('-a', '--name', action='store',
                                   required=True,
                                   help='Virtual cluster name')
    checkpoint_parser.add_argument('-c', '--controlb', action='store',
                                   required=True,
                                   help='Control node bucket name')
    checkpoint_parser.add_argument('-t', '--controln', action='store',
                                   required=True,
                                   help='Control node image name')
    checkpoint_parser.add_argument('-m', '--computeb', action='store',
                                   required=True,
                                   help='Compute node bucket name')
    checkpoint_parser.add_argument('-e', '--computen', action='store',
                                   required=True,
                                   help='Compute node image name')
    checkpoint_parser.set_defaults(func=virtual_cluster.checkpoint_cluster)

    # restore command

    restore_parser = subparsers.add_parser('restore',
            help='Restore saved virtual cluster')
    restore_parser.add_argument('-a', '--name', action='store',
                                required=True,
                                help='Virtual cluster name')
    restore_parser.add_argument('-c', '--controli', action='store',
                                required=True,
                                help='Control node image id')
    restore_parser.add_argument('-m', '--computei', action='store',
                                required=True,
                                help='Compute node image id')
    restore_parser.add_argument('-t', '--type', action='store',
                                help='Instance type')
    restore_parser.add_argument('-n', '--number', action='store',
                                required=True,
                                help='Number of compute nodes')
    restore_parser.set_defaults(func=virtual_cluster.restore_cluster)

    args = parser.parse_args()

    # parse config file
    if args.file:
        virtual_cluster.parse_conf(args.file)
    else:
        virtual_cluster.parse_conf()

    # set debug flag
    virtual_cluster.set_debug(args.debug)

    args.func(args)

if __name__ == '__main__':
    commandline_parser()
