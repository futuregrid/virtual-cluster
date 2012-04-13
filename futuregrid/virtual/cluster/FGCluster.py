#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
FGCluster.py (python)
-------------------------

Operations for managing virtual clusters

Name fg-cluster

Description

usage:

    fg-cluster <parameters>

    -f -- futuregrid configuration file
          which specifies the location of
          necessary files to run program

    --debug -- show debug message

    --default-repository -- set if to use IU ubuntu repo
                            if specifyed, then not use IU
                            ubuntu repo

    --create-key -- create euca key file

    subcommands:

    run: run a virtual cluster of given parameters

    -a -- virtual cluster name
    -n -- compute node number
    -i -- image type
    -t -- instance type

    checkpoint: save the state of currently running cluster

    -a -- virtual cluster name
    -c -- control node bucket name
    -t -- control node image name
    -m -- compute node bucket name
    -e -- compute node image name

    restore: restore state of saved virtual cluster

    -a -- virtual cluster name

    terminate: terminate a virtual cluster of given name

    -a -- virtual cluster name

    status: show status of virtual cluster(s)

    -a -- virtual cluster name

    If no virtual cluster name is specified, the command will return
    status of all virtual clusters recorded

    list: list virtual clusters
'''

import argparse
import sys
import os
import time
import threading
import ConfigParser
import random
import Queue
import re
import boto.ec2

from boto.ec2.connection import EC2Connection
from futuregrid.virtual.cluster.CloudInstances import CloudInstances
#from CloudInstances import CloudInstances
from subprocess import Popen, PIPE
from ConfigParser import NoOptionError
from ConfigParser import MissingSectionHeaderError
from ConfigParser import NoSectionError


class Cluster(object):
    """
    Class Cluster
    -------------
    Methods to
        run virtual cluster
        checkpoint virtual cluster
        restore virtual cluster
        terminate virtual cluster
        show status of virtual cluster(s)
        list virtual clusters
    """

    userkey = None
    cloud_instances = None
    backup_file = None
    user = None
    enrc = None
    slurm = None
    mutex = None
    interface = None
    cloud = None
    ec2_conn = None
    user_login = None

    # debug switch
    if_debug = False
    # if false, using IU ubuntu repository
    if_default = False
    # if true, create userkey key
    if_create_key = False

    # repo file name
    sources_list = 'sources.list'

    def __init__(self):
        '''
        init method
        '''
        super(Cluster, self).__init__()
        self.cloud_instances = CloudInstances()
        self.mutex = threading.Lock()

# ---------------------------------------------------------------------
# METHODS TO PRINT HELP MESSAGES
# ---------------------------------------------------------------------

    @classmethod
    def msg(cls, message):
        '''
        Method for printing help messages

        Parameters:
            message -- message to print

        Logic:
            use print to print message

        No returns
        '''

        print message

    def print_section(self, message):
        '''
        Prints section header
        '''

        self.msg('\n=========================')
        self.msg(message)
        self.msg('=========================')

    def debug(self, message):
        '''
        Method for printing debug message

        Parameter:
            message -- message to print

        Logic:
            Checks debug flag, if debug flag is set to
            true, then prints debug message, if is set
            to false, then does not print debug message

        No returns
        '''

        if self.if_debug:
            print message

# ---------------------------------------------------------------------
# METHODS TO SET PROGRAM FLAGS
# ---------------------------------------------------------------------
    def set_interface(self, interface):
        '''
        Set interface the program to use

        Parameter:
            interface -- interface (boto or euca2ools)

        command line argument --interface will
        overwrite the configure in configuration file

        No returns
        '''

        if interface:
            self.interface = interface
        if self.interface not in ('euca2ools', 'boto'):
            self.msg('Interface should be boto or euca2ools')
            sys.exit()
        if self.interface == 'boto':
            self.ec2_connect(self.cloud)

    def set_cloud(self, cloud):
        '''
        Set cloud

        Parameter:
            cloud -- cloud (nova or eucalyptus)

        command line argument --cloud will
        overwrite the configure in configuration file

        No returns
        '''

        if cloud:
            self.cloud = cloud
        if self.cloud not in ('nova', 'eucalyptus'):
            self.msg('Cloud should be boto or euca2ools')
            sys.exit()
        if self.cloud == 'nova':
            self.user_login = 'ubuntu'
        elif self.cloud == 'eucalyptus':
            self.user_login = 'root'

    def set_flag(self, args):
        '''
        Sets control flags

        Parameter:
            args -- this method deals args.if_debug, if_default
                    if_create_key.

                    if_debug: default is false
                              true to print debug message
                              false not to print

                    if_default: default is false
                                true to use default ubuntu repository
                                false to use IU ubuntu repository

                    if_create_key: default is false
                                   true to create key for users
                                   false not to create
                    if_boto: default is false
                             true to use boto interface
                             false to use euca2ools

        Logic:
            Sets control flags

        No returns
        '''

        self.if_debug = args.debug
        self.if_default = args.default_repository
        self.if_create_key = args.create_key

# ---------------------------------------------------------------------
# METHODS ABOUT KEYPAIRS
# ---------------------------------------------------------------------
    def if_keypair_exits(self, name):
        '''
        Checks if key is already created

        Parameters:
            name -- key name

        Logic:
            Uses euca-describe-keypairs to check the keys created,
            finds name in the command result

        Return:
            true -- if finds the key given name as parameter
            false -- if does not fine the key given name as parameter
        '''

        command = 'euca-describe-keypairs'
        for element in self.get_command_result(command).split('\t'):
            if element.find(name) >= 0:
                return True
        return False

    @classmethod
    def add_keypair(cls, name, key):
        '''
        Adds keypair

        Parameter:
            name -- userkey name
            key -- location of userkey

        Logic:
            Uses euca-add-keypair to create key for user, key will
            be created under the location referred by key

        No returns
        '''

        os.system('euca-add-keypair %s > %s' % (name, key))
        os.chmod(os.path.expanduser(key), 0600)

# ---------------------------------------------------------------------
# METHOD TO PARSE CONFIGURATION FILE
# ---------------------------------------------------------------------

    def parse_conf(self, file_name='unspecified'):
        """
        Parse configuration file

        Parameters:
            file_name -- configuration file name
            default: unspecified

        Logic:
            Parse configuration file if given, default location
            '~/.futuregrid/futuregrid.cfg'. If no file is given,
            finds configuration file by following order:
                1) finds current directory 'futuregrid.cfg'
                2) finds in default location

            configuration file format:
            [virtual-cluster]
            # Backup file for saving and loading virtual cluster(s)
            backup = ~/.futuregrid/virtual-cluster
            # Slurm configuration input file
            slurm = ~/.futuregrid/slurm.conf.in
            # userkey pem file
            userkey = ~/PUT-YOUR-USER-NAME.pem
            # environment file
            enrc = ~/novarc

            Checks if all files specified in configuration
            file are present.If create-key is set to true,
            first check if key exists, if key does not exist,
            then creates key under the location where is specified
            by userkey in the configuration file

            Due to different version of this tool, back-end
            structure of backup file may change, so checks
            if backup file has the correct format before the start

            Checks all possible errors about configuration file

        No returns
        """

        config = ConfigParser.ConfigParser()
        try:
            # default location ~/.futuregrid/futuregrid.cfg
            # read[], reads begin from last to first
            # so, first reads file_name, then current directory, then default
            config.read([os.path.expanduser('~/.futuregrid/futuregrid.cfg'),
                         'futuregrid.cfg',
                         os.path.expanduser(file_name)])

            self.backup_file = config.get('virtual-cluster', 'backup')
            self.debug('Backup file %s' % self.backup_file)
            self.userkey = config.get('virtual-cluster', 'userkey')
            self.debug('Userkey %s' % self.userkey)
            self.user = os.path.splitext(self.userkey.split('/')[-1])[0]
            self.enrc = config.get('virtual-cluster', 'enrc')
            self.debug('enrc %s' % self.enrc)
            self.slurm = config.get('virtual-cluster', 'slurm')
            self.debug('SLURM configuration input file %s' % self.slurm)
            self.interface = config.get('virtual-cluster', 'interface')
            self.cloud = config.get('virtual-cluster', 'cloud')

            # checking if all file are present
            self.debug('Checking if all file are present')
            if not os.path.exists(os.path.expanduser(self.userkey)):
                if self.if_create_key:
                    # create key for user
#                    self.add_keypair(self.user)
                    if self.if_keypair_exits(self.user):
                        self.msg('\nYou have userkey %s.pem, please correct'
                                 ' its location in configuration file'
                                 % self.user)
                        sys.exit()
                    else:
                        self.add_keypair(self.user, self.userkey)
                else:
                    self.msg('ERROR: You must have userkey file')
                    sys.exit(1)
            if not os.path.exists(os.path.expanduser(self.enrc)):
                self.msg('ERROR: You must have novarc file')
                sys.exit(1)
            else:
                self.debug('Reading environment')
                key_dir = os.path.dirname(self.enrc)
                if key_dir.strip() == "":
                    key_dir = "."
                if self.cloud == 'nova':
                    os.environ["NOVA_KEY_DIR"] = key_dir
                elif self.cloud =='eucalyptus':
                    os.environ['EUCA_KEY_DIR'] = key_dir
                with open(os.path.expanduser(self.enrc)) as enrc_content:
                    for line in enrc_content:
                        if re.search("^export ", line):
                            line = line.split()[1]
                            parts = line.split("=")
                            value = ""
                            for i in range(1, len(parts)):
                                parts[i] = parts[i].strip()
                                tempvar = os.path.expandvars(parts[i])
                                parts[i] = os.path.expanduser(tempvar)
                                value += parts[i] + "="
                                value = value.rstrip("=")
                                value = value.strip('"')
                                value = value.strip("'")
                                if parts[0] == 'EC2_CERT' or \
                                    parts[0] == 'EC2_PRIVATE_KEY' or \
                                    parts[0] == 'EUCALYPTUS_CERT':
                                    if not os.path.exists(value):
                                        self.msg('%s does not exist' % value)
                                        sys.exit()
                                os.environ[parts[0]] = value

            if not os.path.exists(os.path.expanduser(self.slurm)):
                self.msg('ERROR: You must have slurm.conf.in file')
                sys.exit(1)

            self.debug('Checking backup file')
            self.backup_file += '.' + self.cloud
            if not self.cloud_instances.set_backup_file(self.backup_file):
                self.msg('\nBackup file is corrupted, or you are using an old'
                        ' version of this tool. Please delete this backup file'
                        ' and try again.')
                sys.exit(1)
            self.debug('Checking done')

        except IOError:
            self.msg('\nError in reading configuration file!'
                     ' configuration file not created?')
            sys.exit()
        except (MissingSectionHeaderError, NoSectionError):
            self.msg('\nError in reading configuratin file!'
                     ' No section header?')
            sys.exit()
        except NoOptionError:
            self.msg('\nError in reading configuration file!'
                     ' Correct configuration format?')
            sys.exit()
        except ValueError:
            self.msg('\nError in reading configuration file!'
                     ' Correct python version?')
            sys.exit()

# ---------------------------------------------------------------------
# METHOD TO INSTALL
# ---------------------------------------------------------------------

    def check_avaliable(self, instance):
        '''
        Check if instance is available

        Parameters:
            instance -- instance dictionary

        Return:
            True -- if instance is available
            False -- if instance is unavailable
        '''

        cmd = "ssh -i %s %s@%s uname" % (self.userkey,
                                         self.user_login,
                                         instance['ip'])

        check_process = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
        status = os.waitpid(check_process.pid, 0)[1]
        if status == 0:
            return True
        else:
            return False

    def euca_start_new_instance(self, instance, instance_index):
        '''
        Starts new instance given old instance info using euca2ools

        Parameter:
            instance -- old instance
            instance_index -- instance index
        Return:
            new instance
        '''
        # try to create a new one
        self.msg('Creating new instance')
        self.euca_run_instance(self.user, 1, instance['image'],
                               instance['type'], instance_index)
        self.debug('Getting free public IPs')
        # get free IP list
        ip_lists = self.euca_describe_addresses()
        time.sleep(2)
        new_instance = self.cloud_instances.get_by_id(instance_index)
        self.msg('\nAssociating IP with %s' % new_instance['id'])
        new_ip = ip_lists[random.randint(0, len(ip_lists) - 1)]
        while not self.euca_associate_address(new_instance, new_ip):
            self.msg('Error in associating IP %s with instance %s, '
                     'trying again' % (new_ip, new_instance['id']))
        return new_instance

    def boto_start_new_instance(self, instance, instance_index):
        '''
        Starts new instance given old instance info using euca2ools

        Parameter:
            instance -- old instance
            instance_index -- instance index
        Return:
            new instance
        '''

        reservation = self.boto_run_instances(instance['image'],
                                              1,
                                              instance['type'])
        new_instance = reservation.instances[0]
        arg1 = new_instance.id
        arg2 = new_instance.image_id
        arg3 = new_instance.instance_type
        self.cloud_instances.set_instance(instance_id=arg1,
                                          image_id=arg2,
                                          instance_type=arg3,
                                          index=instance_index)
        ip_list = self.boto_describe_addresses()
        free_public_ip = ip_list[random.randint(0, len(ip_list) - 1)]
        self.boto_associate_address(new_instance.id, free_public_ip)
        new_instance.update()
        return self.cloud_instances.get_by_id(instance_index)

    def euca_change_ip(self, instance):
        '''
        Changes public IP address given instance using euca2ools
        No returns
        '''

        ip_lists = self.euca_describe_addresses()
        # disassociate current one
        self.disassociate_address(instance['ip'])
        # associate a new random free ip
        self.debug('Associating new IP on %s' % instance['id'])
        self.euca_associate_address(instance, ip_lists[random.randint(0,
                                            len(ip_lists) - 1)])

    def boto_change_ip(self, instance):
        '''
        Changes public IP address given instance using boto
        No returns
        '''
        ip_list = self.boto_describe_addresses()
        free_public_ip = ip_list[random.randint(0, len(ip_list) - 1)]
        self.ec2_conn.disassociate_address(instance['ip'])
        self.get_instance_from_reservation(instance['id']).update()
        self.boto_associate_address(instance['id'], free_public_ip)

    def installation(self, instance, max_retry, install=True):
        '''
        Checks if instances are ready to deploy and installs the
        softwares on the instance which is ready

        Parameters:
            instance -- instance dictionary
            max_retry -- max number of try for checking instance
            install -- indicates if need to the installation
            default: true

        Logic:
            ssh reomote host to check if can succeed
            If install is set to true, installation of
            SLURM and OpenMPI will start on VM which is ready

            Each instances associates a count of times for trying
            If exceeds the max try limit, then gets free public IPs,
            and associates it with a random new one, reset count to 0

            Break after all threads are done

        No returns
        '''

        wait_count = 0

        ip_change = False

        # check if ssh port of all VMs are alive for listening
        while True:
            if self.check_avaliable(instance):
                self.mutex.acquire()
                self.del_known_host(instance['ip'])
                self.mutex.release()
                if install:
                    self.deploy_services(instance)
                break
            elif self.cloud == 'nova':
                self.debug('ssh in %s is closed' % instance['ip'])
                self.msg('Checking %s (%s) availability, '
                         'trying %d (max try %d)'
                         % (instance['id'], instance['ip'],
                            wait_count, max_retry))

                wait_count += 1
                if wait_count > max_retry:
                    if self.if_status(instance['id'], 'shutdown') or \
                        self.if_status(instance['id'], 'terminate') or \
                        self.if_status(instance['id'], 'terminated') or \
                        ip_change:
                        # get instance index
                        instance_index = \
                            self.cloud_instances.get_index(instance)
                        self.msg('Instance %s creation failed'
                                 % instance['id'])
                        # delete this instance from cloud instance list
                        self.cloud_instances.del_instance(instance)
                        self.terminate_instance(instance['id'])
                        self.mutex.acquire()
                        if self.interface == 'euca2ools':
                            instance = \
                                self.euca_start_new_instance(instance,
                                                             instance_index)
                        elif self.interface == 'boto':
                            instance = \
                                self.boto_start_new_instance(instance,
                                                             instance_index)
                        self.mutex.release()
                        wait_count = 0
                        ip_change = False
                    elif self.if_status(instance['id'], 'running'):
                        self.msg('\nTrying different IP address on %s'
                                 % instance['id'])
                        # get free ip addresses
                        self.mutex.acquire()
                        if self.interface == 'euca2ools':
                            self.euca_change_ip(instance)
                        elif self.interface == 'boto':
                            self.boto_change_ip(instance)
                        self.mutex.release()
                        self.debug('New IP is %s' % instance['ip'])
                        wait_count = 0
                        ip_change = True
                time.sleep(3)
            elif self.cloud == 'eucalyptus':
                self.msg('Checking %s (%s) availability' % (instance['id'], instance['ip']))
                time.sleep(3)

# ---------------------------------------------------------------------
# METHODS TO DO RPCs
# ---------------------------------------------------------------------

    def get_command_result(self, command):
        '''
        Gets command output

        Parameters:
            command -- shell command

        Return:
            Command output
        '''
        self.debug(command)
        return os.popen(command).read()

    def execute(self, instance, command):
        '''
        Executes a command on the instance

        Parameters:
            instance -- cloud instance
            command -- shell command

        No returns
        '''
        os.system("ssh -i %s %s@%s '%s'" % (self.userkey,
                                            self.user_login,
                                            instance['ip'],
                                            command))

    def copyto(self, instance, filename):
        '''
        Copies the named file to the instance

        Parameters:
            instance -- cloud instance
            filename -- the name of file to copy

        No returns
        '''
        os.system('scp -i %s %s %s@%s:~/' % (self.userkey,
                                             filename,
                                             self.user_login,
                                             instance['ip']))

    def update(self, instance):
        '''
        Executes a software update on the specified instance

        Parameters:
            instance -- cloud instance

        No returns
        '''

        self.execute(instance, 'sudo apt-get update')

    def install(self, instance, packagenames):
        '''
        Installs the package names that are specified
        (blank separated on the given instance)

        Parameter:
            instance -- cloud instance
            packagenames -- software names

        No returns
        '''

        self.execute(instance, 'sudo apt-get install --yes '
                     + packagenames)

# ---------------------------------------------------------------------
# METHODS TO CREATE A VIRTUAL CLUSTER
# ---------------------------------------------------------------------

    def ec2_connect(self, cloud):
        '''
        create connection
        '''
        if cloud.strip() == 'nova':
            path = "/services/Cloud"
        elif cloud.strip() == 'eucalyptus':
            path = "/services/Eucalyptus"

        endpoint = os.getenv('EC2_URL').lstrip("http://").split(":")[0]
        try:
            region = boto.ec2.regioninfo.RegionInfo(name=cloud,
                                                    endpoint=endpoint)
        except:
            self.msg('ERROR: error in getting region information')
            sys.exit()

        try:
            self.ec2_conn = EC2Connection(os.getenv("EC2_ACCESS_KEY"),
                                          os.getenv("EC2_SECRET_KEY"),
                                          is_secure=False,
                                          region=region,
                                          port=8773, path=path)
        except:
            self.msg('ERROR: error in connecting to EC2')
            sys.exit()

    def boto_describe_addresses(self):
        '''
        get all free ip addresses using boto
        '''

        ip_list = []
        for address in \
            self.ec2_conn.get_all_addresses(addresses=None):
            address_public_ip = address.public_ip
            address_instance_id = address.instance_id
            if not address_instance_id:
                ip_list.append(address_public_ip)
        return ip_list

    def get_instance_from_reservation(self, instance_id):
        '''
        get instance from reservation
        '''

        r_in = self.ec2_conn.get_all_instances(instance_ids=[instance_id])
        return r_in[0].instances[0]

    def boto_associate_address(self, instance_id, address_public_ip, address_private_ip):
        '''
        associate ip address using boto
        '''

        while True:
            try:
                time.sleep(2)
                self.ec2_conn.associate_address(instance_id, address_public_ip)
                break
            except:
                self.msg('ERROR: Associating ip %s with instance %s failed, '
                         'trying again' % (address_public_ip, instance_id))
        self.msg('ADDRESS: %s %s' % (address_public_ip, instance_id))
        self.cloud_instances.set_ip_by_id(instance_id, address_public_ip, address_private_ip)

    def boto_run_instances(self, image, cluster_size, instance_type):
        '''
        run instance usign boto
        '''

        try:
            return self.ec2_conn.run_instances(image_id=image,
                                               min_count=cluster_size,
                                               max_count=cluster_size,
                                               key_name=self.user,
                                               instance_type=instance_type)
        except:
            self.msg('ERROR: Error in lunching instances, please try again')
            self.ec2_conn.close()
            sys.exit()

    def euca_run_instance(
        self,
        userkey,
        cluster_size,
        image,
        instance_type,
        index=None
        ):
        '''
        runs instances given parameters

        Parameters:
            userkey -- userkey name
            cluster_size -- number of nodes
            image -- image id
            instance_type -- instance type
            index -- instance key as index
            default: None

        Logic:
            check if all instances are created
            correctly. program will exit if
            not all instances required are
            created, and terminate those which
            are running already

        No returns
        '''

        instance_id_list = []

        # get run instances store int instances list
        self.debug('euca-run-instances -k %s -n %d -t %s %s'
                   % (userkey,
                      cluster_size,
                      instance_type,
                      image))
        instances = [x for x in
                     self.get_command_result(
                                             'euca-run-instances -k %s'
                                             ' -n %d -t %s %s'
                      % (userkey, cluster_size, instance_type,
                     image)).split()]
        # find created instance, store into list
        for instance in instances:
            if instance.find('i-') == 0:
                self.debug('%s is created' % instance)
                instance_id_list.append(instance)

        self.debug('Checking if all instances are created')
        # check if all instances are created correctly
        if not len(instance_id_list) == cluster_size:
            self.msg('\nError in creating cluster, please check your input'
                     ' or instance limit exceeded?')
            for created_instance_id in instance_id_list:
                self.terminate_instance(created_instance_id)
            sys.exit()
        self.debug('Checking done')

        self.debug('Adding instances into cloud instances list')
        # add instance to instance list
        for num in range(cluster_size):
            try:
                ip_addr = instance_id_list[num]
                self.debug('Adding instance %s' % ip_addr)
                self.cloud_instances.set_instance(instance_id=ip_addr,
                                                  image_id=image,
                                                  instance_type=instance_type,
                                                  index=index)
            except:
                self.msg('\nError in creating instances.'
                         ' Program will exit')
                sys.exit()

    def euca_associate_address(self, instance, free_ip):
        '''
        Associates instance with ip

        Parameters:
            instance -- cloud instance
            free_ip -- free public IP address

        Logic:
            Associates IP with a given instance, set IP in cloud_instances
            delete host information in known_hosts if it has

        Return:
            false: if association failed
            trueL: if association succeeded
        '''

        self.debug('euca-associate-address -i %s %s'
                   % (instance['id'], free_ip))
        if self.get_command_result('euca-associate-address -i %s %s'
                                   % (instance['id'],
                                      free_ip)).find('ADDRESS') < 0:
            return False
        # set ip using instance id
        self.msg('ADDRESS %s instance %s' % (free_ip, instance['id']))
        private_ip = self.euca_get_ip(instance['id'])['private']
        self.cloud_instances.set_ip_by_id(instance['id'], free_ip, private_ip)
        # delete host from known_host file in case man-in-middle-attack
        self.debug('Deleting %s from known host if it already existed'
                   % free_ip)
        return True

    def disassociate_address(self, current_ip):
        '''
        Disassociates IP address

        Parameters:
            current_ip -- instance IP which is currently in use

        Logic:
            Uses euca-disassociates-address to disassociates a
            given IP address

        No returns
        '''

        self.msg('Disaasociating %s' % current_ip)
        self.debug('euca-disassociate-address %s' % current_ip)
        os.system('euca-disassociate-address %s' % current_ip)

    def euca_describe_addresses(self):
        '''
        Return list of free public IP addresses

        No parameters

        Logic:
            Uses euca-describe-addresses to get all the IP addresses,
            filter those which are currently in use

        Return:
            ip_list -- a list of free public IP addresses
        '''

        ip_list = []
        ips = [x for x in self.get_command_result('euca-describe-addresses'
               ).split('\n')]

        # store free ip into ip list for return
        for free_ip in ips:
            if free_ip.find('i-') < 0 and len(free_ip) > 0:
                ip_list.append(free_ip.split('\t')[1])
        return ip_list

    def if_status(self, instance_id, status):
        '''
        Check if instance is running
        '''

        result = self.get_command_result('euca-describe-instances').split('\n')

        for i in result:
            if i.find(instance_id) >= 0:
                if i.find(status) >= 0:
                    return True
                else:
                    return False
    def euca_get_ip(self, instance_id):
        '''
        Get instance public given instance id
        '''
        result = self.get_command_result('euca-describe-instances').split('\n')
        for i in result:
            if i.find(instance_id) >= 0:
                return {'public':i.split('\t')[3], 'private':i.split('\t')[4]}

    def create_cluster(self, args):
        '''
        Method for creating cluster

        Parameters:
            args -- this method deals
                    args.name: cluster name
                    args.number: cluster compute nodes number
                    args.typy: instance type
                    args,image: image id

        Logic:
            Check existence before creation of cluster
            If cluster was created before, only start creating
            if status is DOWN

            Save each instance into cloud instance list
            Associate IP with each instance
            Create source list file if using IU ubuntu repository
            Delete source list file after installtion and configuration
            of SLURM and OpenMPI

        No returns
        '''

        self.debug('Checking if %s is existed' % args.name)
        if self.cloud_instances.if_exist(args.name):
            # if exists, get cloud info by name
            self.debug('%s is existed, gettting it from backup file'
                       % args.name)
            self.cloud_instances.get_cloud_instances_by_name(args.name)
            # if cluster is terminated, delete old info, start over
            self.debug('Checking if %s is currently down' % args.name)
            if self.cloud_instances.if_status(self.cloud_instances.DOWN):
                self.debug('Deleting old info')
                self.cloud_instances.del_by_name(args.name)
                self.cloud_instances.clear()
            else:
                self.msg('\nError in creating cluster %s,name is in use'
                          % args.name)
                sys.exit()

        cluster_size = int(args.number) + 1
        self.debug('Cluster size is (control node included): %d'
                   % cluster_size)
        self.print_section('Creating virtual cluster')
        self.msg('cluster name    -- %s' % args.name)
        self.msg('numbe of nodes  -- %s' % cluster_size)
        self.msg('instance type   -- %s' % args.type)
        self.msg('image id        -- %s' % args.image)

        self.debug('Creating new cloud instance %s' % args.name)
        # set cloud instance list
        self.cloud_instances.set_cloud_instances_by_name(args.name)

        self.debug('Creating cluster')
        # run instances given parameters
        if self.interface == 'euca2ools':
            self.euca_run_instance(self.user, cluster_size, args.image,
                                   args.type)

            time.sleep(5)

            self.msg('\nAssociating public IP addresses')
            ip_lists = self.euca_describe_addresses()
            for i in range(cluster_size):
                instance = self.cloud_instances.get_by_id(i)
                time.sleep(1)
                if self.cloud == 'nova':
                    while not self.euca_associate_address(instance, ip_lists[i]):
                        self.msg('Error in associating IP %s with instance %s, '
                                 'trying again' % (ip_lists[i], instance['id']))
                elif self.cloud == 'eucalyptus':
                    addresses = self.euca_get_ip(instance['id'])
                    public_ip_address = addresses['public']
                    private_ip_address = addresses['private']
                    self.msg('ADDRESS %s' % public_ip_address)
                    self.cloud_instances.set_ip_by_id(instance['id'],
                                                      public_ip_address,
                                                      private_ip_address)

        elif self.interface == 'boto':
            reservation = \
                self.boto_run_instances(args.image, cluster_size, args.type)

            time.sleep(5)

            self.msg('\nAssociating public IP addresses')
            ip_index = 0
            ip_lists = self.boto_describe_addresses()
            for instance in reservation.instances:
                time.sleep(1)
                instance.update()
                self.cloud_instances.set_instance(instance.id,
                                                  instance.image_id,
                                                  instance.instance_type)
                if self.cloud == 'nova':
                    ip_index += 1
                    self.boto_associate_address(instance.id,
                                                ip_lists[ip_index],
                                                instance.private_dns_name)
                elif self.cloud == 'eucalyptus':
                    print instance.public_dns_name
                    self.cloud_instances.set_ip_by_id(instance.id,
                                                      instance.public_dns_name,
                                                      instance.private_dns_name)

        self.debug('Creating IU ubunto repo source list')
        # choose repo, by defalt, using IU ubuntu repo
        self.define_repo()

        self.debug('Checking alive instance for deploying')
        # detect if VMs are ready for deploy

        for instance in self.cloud_instances.get_list().values():
            if type(instance) is dict:
                threading.Thread(target=self.installation,
                                 args=[instance, 30, True]).start()

        while threading.activeCount() > 1:
            time.sleep(1)

        self.debug('Configuraing SLURM')
        # config SLURM system
        self.config_slurm()

        self.debug('Cleaning up')
        # clean repo file
        self.clean_repo()
        self.debug('Saving cloud instance into backup file')
        # save cloud instance
        self.cloud_instances.save_instances()
        self.debug('Done creation of cluster')

    def clean_repo(self):
        '''
        Remove source list file

        No parameters:

        Logic:
            If if_default flag is set to false, then delete
            source list file

        No returns
        '''

        if not self.if_default:
            self.debug('Removing %s' % self.sources_list)
            os.remove(self.sources_list)

    def config_slurm(self, create_key=True):
        '''
        Configures slurm

        Parameters:
            create_key -- indicates whether to create munge-key
            default: true, creates key

        Logic:
            Reads slurm configuration input file, substitutes controlMachine
            with control machine id. Append each computation node into
            configuration file in COMPUTE NODES section
            Generates munge-key on control node if flag is set to true
            Does configuration on each node in parallel
            After all threads are done, removes temp files

        No returns
        '''

        slurm_conf_file = 'slurm.conf'
        munge_key_file = 'munge.key'
        hosts = 'hosts'

        self.debug('Opening %s' % self.slurm)
        self.msg('\nConfiguring slurm.conf')
        with open(os.path.expanduser(self.slurm)) as srcf:
            input_content = srcf.readlines()
        srcf.close()

        self.debug('Getting control machie id')
        #set control machine
        controlMachine = self.cloud_instances.get_by_id(0)['id']
        ControlAddr = self.cloud_instances.get_by_id(0)['private_ip']
        output = ''.join(input_content) % vars()

        self.msg('\nControl node %s' % controlMachine)
        self.msg('\nControl node private IP%s' % ControlAddr)

        self.debug('Writting into %s' % slurm_conf_file)
        # write control machine into slurm.conf file
        destf = open(slurm_conf_file, 'w')
        print >> destf, output
        destf.close()

        self.debug('Openning %s for adding computation nodes'
                   % slurm_conf_file)
        # add compute machines to slurm conf file
        with open(slurm_conf_file, 'a') as conf:
            for instance in self.cloud_instances.get_list().values():
                if type(instance) is dict:
                    if not instance['id'] == controlMachine:
                        self.debug('Adding instance %s' % instance['id'])
                        conf.write('NodeName=%s Procs=1 NodeAddr=%s State=UNKNOWN\n'
                                   % (instance['id'], instance['private_ip']))
                        conf.write('PartitionName=debug Nodes=%s Default=YES'
                                   ' MaxTime=INFINITE State=UP\n'
                                   % instance['id'])
        conf.close()

        # if needs to create munge key
        if create_key:
            self.msg('\nGenerating munge-key')

            # generate munge-key on control node

            self.execute(self.cloud_instances.get_by_id(0),
                         'sudo /usr/sbin/create-munge-key')
            self.debug('Opening %s for writting munge-key' % munge_key_file)
            munge_key = open(munge_key_file, 'w')
            print >> munge_key, \
                self.get_command_result("ssh -i %s %s@%s"
                                        " 'sudo cat /etc/munge/munge.key'"
                                         % (self.userkey,
                                            self.user_login,
                                        self.cloud_instances.get_by_id(0)['ip'
                                        ]))
            munge_key.close()

        # if cloud is eucalyptus, need to change hostname
        if self.cloud == 'eucalyptus':
            # copy SLURM conf file to every node
            for instance in self.cloud_instances.get_list().values():
                if type(instance) is dict:
                    with open(hosts, 'w') as host_file:
                        host_file.write('127.0.0.1 %s' % instance['id'])
                    host_file.close()
                    self.execute(instance, 'hostname %s' % instance['id'])
                    self.copyto(instance, hosts)
                    self.execute(instance, 'cp %s /etc/' % hosts)

        # copy SLURM conf file to every node
        for instance in self.cloud_instances.get_list().values():
            if type(instance) is dict:
                self.debug('Starting SLURM on %s' % instance['id'])
                process_thread = threading.Thread(target=self.start_slurm,
                                                  args=[instance,
                                                        create_key,
                                                        slurm_conf_file,
                                                        munge_key_file])
                process_thread.start()

        # wait all threads are done
        self.debug('Waitting all threads are done')
        while threading.activeCount() > 1:
            time.sleep(1)

        # clean temp files
        if create_key:
            self.debug('Removing %s' % munge_key_file)
            os.remove(munge_key_file)
        self.debug('Removing %s' % slurm_conf_file)
        os.remove(slurm_conf_file)

    def start_slurm(self,
                    instance,
                    create_key,
                    slurm_conf_file,
                    munge_key_file):
        '''
        Copies SLURM configuration file and munge key file
        to every node, and start slurm on each node

        Parameters:
            instance -- cloud instance
            create_key -- flag indicates whether needs to create munge key
            slurm_conf_file -- SLURM configuration file name
            munge_key_file -- munge key file name

        Logic:
            Copies SLURM configuration file to each node in cluster.
            If needs to create munge key, then creates munge key on
            control node, copies it to each node in cluster. Starts
            SLURM and munge after copy is done

        No returns
        '''

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
            self.execute(instance,
                         'sudo chmod 400 /etc/munge/munge.key')

        # start slurm and munge daemon
        self.msg('\nStarting slurm on node %s' % instance['id'])
        self.execute(instance, 'sudo /etc/init.d/slurm-llnl start')
        self.msg('\nSrarting munge on node %s' % instance['id'])
        self.execute(instance, 'sudo /etc/init.d/munge start')

    def define_repo(self):
        '''
        Set ubuntu repo to IU ubuntu repository

        No parameters

        Source list file content:
        -------------------------

        deb http://ftp.ussg.iu.edu/linux/ubuntu/ natty-updates main
        deb-src http://ftp.ussg.iu.edu/linux/ubuntu/ natty-updates main
        deb http://ftp.ussg.iu.edu/linux/ubuntu/ natty universe
        deb-src http://ftp.ussg.iu.edu/linux/ubuntu/ natty universe
        deb http://ftp.ussg.iu.edu/linux/ubuntu/ natty-updates universe
        deb-src http://ftp.ussg.iu.edu/linux/ubuntu/ natty-updates universe
        deb http://ftp.ussg.iu.edu/linux/ubuntu/ natty main
        deb-src http://ftp.ussg.iu.edu/linux/ubuntu/ natty main

        Logic:
            If uses IU ubuntu repository, creates sources_list file
            which has the former content

        No returns
        '''

        iu_repo = 'http://ftp.ussg.iu.edu/linux/ubuntu/'

        if self.if_default:
            self.msg('\nUsing default repository')
        else:
            self.msg('\nUsing IU ubuntu repository')
            self.debug('Using %s' % iu_repo)
            self.debug('Opening %s for writting' % self.sources_list)
            with open(self.sources_list, 'w') as source:
                source.write('deb ' + iu_repo + ' natty-updates main\n')
                source.write('deb-src ' + iu_repo + ' natty-updates main\n')
                source.write('deb ' + iu_repo + ' natty universe\n')
                source.write('deb-src ' + iu_repo + ' natty universe\n')
                source.write('deb ' + iu_repo + ' natty-updates universe\n')
                source.write('deb-src ' + iu_repo +
                             ' natty-updates universe\n')
                source.write('deb ' + iu_repo + ' natty main\n')
                source.write('deb-src ' + iu_repo + ' natty main\n')
            source.close()

    def deploy_services(self, instance):
        '''
        Deploies SLURM and OpenMPI services

        Parameters:
            instance -- cloud instance

        Logic:
            If using IU ubuntu repository, then copies source_list
            to each instance in the cluster, installs SLURM and
            OpenMPI on the instance

        No returns
        '''

        self.msg('\nInstalling SLURM system and OpenMPI on %s\n'
                 % instance['ip'])

        if not self.if_default:
            self.debug('Copying %s to %s' % (self.sources_list,
                                             instance['id']))
            self.copyto(instance, self.sources_list)
            self.execute(instance, 'sudo cp %s /etc/apt/'
                         % self.sources_list)

        self.debug('Updating on %s' % instance['id'])
        self.update(instance)
        # install SLURM
        self.debug('Installing slrum-llnl on %s' % instance['id'])
        self.install(instance, 'slurm-llnl')
        # install OpenMPI
        self.debug('Installing openmpi on %s' % instance['id'])
        self.install(instance, "openmpi-bin libopenmpi-dev")

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
        '''
        Saves one instance

        Parameters:
            kernel_id: image kernel id
            ramdisk_id: image ramdisk id
            instance_ip: instance public IP address
            instance_name: image name

        Logic:
            Uses euca-bundle-vol to create a bundle of current image on
            a remote host. Image has the size of 1GB, and stored under /mnt/

        No returns
        '''

        if kernel_id == None:
            self.debug("ssh -i %s %s@%s '. ~/.profile;"
                       " sudo euca-bundle-vol -c ${EC2_CERT}"
                       " -k ${EC2_PRIVATE_KEY} -u ${EC2_USER_ID}"
                       " --ec2cert ${EUCALYPTUS_CERT} --no-inherit"
                       " -p %s -s 1024 -d /mnt/'"
                       % (self.userkey,
                          self.user_login,
                          instance_ip,
                          instance_name))
            return self.get_command_result("ssh -i %s %s@%s '. ~/.profile;"
                            " sudo euca-bundle-vol -c ${EC2_CERT}"
                            " -k ${EC2_PRIVATE_KEY} -u ${EC2_USER_ID}"
                            " --ec2cert ${EUCALYPTUS_CERT} --no-inherit"
                            " -p %s -s 1024 -d /mnt/'"
                             % (self.userkey,
                                self.user_login,
                                instance_ip,
                                instance_name))
        elif ramdisk_id == None:
            self.debug("ssh -i %s %s@%s '. ~/.profile;"
                       " sudo euca-bundle-vol -c ${EC2_CERT}"
                       " -k ${EC2_PRIVATE_KEY} -u ${EC2_USER_ID}"
                       " --ec2cert ${EUCALYPTUS_CERT} --no-inherit"
                       " -p %s -s 1024 -d /mnt/ --kernel %s'"
                       % (self.userkey,
                          self.user_login,
                          instance_ip,
                          instance_name,
                          kernel_id))
            return self.get_command_result("ssh -i %s %s@%s '. ~/.profile;"
                            " sudo euca-bundle-vol -c ${EC2_CERT}"
                            " -k ${EC2_PRIVATE_KEY} -u ${EC2_USER_ID}"
                            " --ec2cert ${EUCALYPTUS_CERT} --no-inherit"
                            " -p %s -s 1024 -d /mnt/ --kernel %s'"
                             % (self.userkey,
                                self.user_login,
                                instance_ip,
                                instance_name,
                            kernel_id))
        else:
            self.debug("ssh -i %s %s@%s '. ~/.profile;"
                       " sudo euca-bundle-vol -c ${EC2_CERT}"
                       " -k ${EC2_PRIVATE_KEY} -u ${EC2_USER_ID}"
                       " --ec2cert ${EUCALYPTUS_CERT} --no-inherit"
                       " -p %s -s 1024 -d /mnt/ --kernel %s --ramdisk %s'"
                       % (self.userkey,
                          self.user_login,
                          instance_ip,
                          instance_name,
                          kernel_id,
                          ramdisk_id))
            return self.get_command_result("ssh -i %s %s@%s '. ~/.profile;"
                            " sudo euca-bundle-vol -c ${EC2_CERT}"
                            " -k ${EC2_PRIVATE_KEY} -u ${EC2_USER_ID}"
                            " --ec2cert ${EUCALYPTUS_CERT} --no-inherit"
                            " -p %s -s 1024 -d /mnt/ --kernel %s --ramdisk %s'"
                             % (self.userkey,
                                self.user_login,
                                instance_ip,
                                instance_name,
                                kernel_id,
                                ramdisk_id))

    def upload_bundle(
        self,
        instance_ip,
        bucket_name,
        manifest,
        ):
        '''
        Uploads bundle image given manifest

        Parameters:
            instance_ip -- instance public IP address
            bucket_name -- bucket name for bundled image
            manifest -- manifest for bundled image

        Logic:
            Uses euca-upload-bundle to upload bundle

        No returns
        '''

        self.debug("ssh -i %s %s@%s '. ~/.profile;"
                   " euca-upload-bundle -b %s -m %s'"
                   % (self.userkey,
                      self.user_login,
                      instance_ip,
                      bucket_name,
                      manifest))
        return self.get_command_result("ssh -i %s %s@%s '. ~/.profile;"
                        " euca-upload-bundle -b %s -m %s'"
                         % (self.userkey,
                            self.user_login,
                            instance_ip,
                            bucket_name,
                            manifest))

    def describe_images(self, image_id):
        '''
        Gets image infomation

        Parameters:
            image_id -- image id

        Logic:
            Uses euca-describe-images to get all the inforamtion of image
            given image id

        Return:
            Command result of euca-describe-images of given image id
        '''

        self.debug('euca-describe-images %s' % image_id)
        return self.get_command_result('euca-describe-images %s' % image_id)

    def get_kernel_id(self, image_id):
        '''
        Gets kernel id

        Parameters:
            image_id -- image id

        Logic:
            Parses the command results returned by describe image method.
            Given that sometimes kernel id is empty for certain images,
            checks if the command returens a kernel id before return it

        Return:
            kernal id -- kernal id is the 8th element of returned command
                         result
        '''

        command_result = [x for x in
                          self.describe_images(image_id).split()]
        if len(command_result) >= 8:
            self.debug('Kernel ID %s' % command_result[7])
            return command_result[7]

    def get_ramdisk_id(self, image_id):
        '''
        Gets ramdisk id

        Parameters:
            image_id -- image id

        Logic:
            Parses the command results returned by describe image method.
            Given that sometimes ramdisk id is empty for certain images,
            checks if the command returens a ramdisk id before return it

        Return:
            ramdisk id -- ramdisk id is the 9th element of returned command
                          result
        '''

        command_result = [x for x in
                          self.describe_images(image_id).split()]
        if len(command_result) == 9:
            self.debug("Ramdisk ID %s" % command_result[8])
            return command_result[8]

    def save_node(
        self,
        image_id,
        instance_ip,
        bucket_name,
        image_name,
        node_type,
        out_queue
        ):
        '''
        Saves nodem, upload and register

        Parameters:
            image_id -- image id of instance
            instance_ip -- instance public IP address
            bucket_name -- bucket name for bundled image
            image_name -- image name for bundled image
            node_type -- control node or compute node
            out_queue -- queue in which puts output

        Logic:
            After gets all the necessary infomraion to save bundle a node,
            then saves the node, uploads the bundle

        Return:
            bundled image id -- Parses the command result, gets the bundled
                                image id, then returns it
        '''

        bundled_image_id = {}

        kernel_id = self.get_kernel_id(image_id)
        self.debug('Kernel ID %s' % kernel_id)
        ramdisk_id = self.get_ramdisk_id(image_id)
        self.debug("Ramdisk ID %s" % ramdisk_id)
        # get manifest from the last unit
        manifest = [x for x in self.save_instance(kernel_id,
                    ramdisk_id, instance_ip, image_name).split()].pop()

        self.msg('\nManifest generated: %s' % manifest)
        self.msg('\nUploading bundle')

        # upload image
        image = [x for x in self.upload_bundle(instance_ip, bucket_name,
                 manifest).split()].pop()
        self.debug(image)
        self.msg('\nUploading done')
        self.msg('\nRegistering image')

        # register image, and return image id
        bundled_image_id[node_type] = \
            self.euca_register(image).split('\t')[1].strip()
        out_queue.put(bundled_image_id)

    def euca_register(self, image):
        '''register image'''

        return self.get_command_result('euca-register %s' % image)

    def checkpoint_cluster(self, args):
        '''
        Method for saving virtual cluster

        Parameters:
            args -- this method deals with
                    args.name -- virtual cluster name
                    args.controlb -- control node bucket name
                    args.controln -- control node image name
                    args.computeb -- compute node bucket name
                    args.computen -- compute node image name

        Logic;
            Checks existence before saving virtual cluster
            Only saves cluster which is running (Because saved and
            terminated clusters are not currenly running)
            Only saves control node and one compute node into images
            Saves new control node image id and new compute node image id
            into backup file for later restore. Change status to SAVED after
            the saving. Then terminates cluster before deletes host information
            after each termination

        No returns
        '''
        if self.interface == 'boto':
            self.msg('UNIMPLEMENTED')
            sys.exit()
        if self.cloud == 'eucalyptus':
            self.msg('bugs')
            sys.exit()

        self.debug('Checking if %s is existed' % args.name)
        # check if cluter is existed
        if self.cloud_instances.if_exist(args.name):
            # get cluter by name
            self.debug('Getting cloud instance %s' % args.name)
            self.cloud_instances.get_cloud_instances_by_name(args.name)
            # if cluster is down, terminate the program
            if not self.cloud_instances.if_status(self.cloud_instances.RUN):
                self.msg('Error in locating virtual cluster %s, not running?'
                          % args.name)
                sys.exit()
        else:
            self.msg('Error in locating virtual cluster %s, not created?'
                     % args.name)
            sys.exit()

        self.print_section('Saving virtual cluster')
        self.msg('Virtual cluster name -- %s' % args.name)
        self.msg('control node bucket  -- %s' % args.controlb)
        self.msg('control node name    -- %s' % args.controln)
        self.msg('compute node bucket  -- %s' % args.computeb)
        self.msg('compute node name    -- %s' % args.computen)

        control = self.cloud_instances.get_by_id(0)
        compute = self.cloud_instances.get_by_id(1)
        self.debug('Control node %s, compute node %s'
                   % (control, compute))

        # copy necessary files to instances, and source profile
        for instance in [control, compute]:
            self.copyto(instance, os.environ['EC2_CERT'])
            self.copyto(instance, os.environ['EC2_PRIVATE_KEY'])
            self.copyto(instance, os.environ['EUCALYPTUS_CERT'])
            self.copyto(instance, self.enrc)
            self.execute(instance, 'cat %s >> ~/.profile'
                         % self.enrc.split('/')[-1])
            self.execute(instance, 'source ~/.profile')

        save_queue = Queue.Queue()
        self.msg('\nSaving control node %s' % control['id'])
        threading.Thread(target=self.save_node, args=[control['image'],
                                                      control['ip'],
                                                      args.controlb,
                                                      args.controln,
                                                      'control',
                                                      save_queue
                                                      ]).start()
        self.msg('\nSaving compute node %s' % compute['id'])
        threading.Thread(target=self.save_node, args=[compute['image'],
                                                      compute['ip'],
                                                      args.computeb,
                                                      args.computen,
                                                      'compute',
                                                      save_queue
                                                      ]).start()
        while threading.activeCount() > 1:
            time.sleep(1)

        # return values has the format:
        # {'control':'', 'compute':''}, but not sure the order
        for bundled_image_id in [save_queue.get(), save_queue.get()]:
            if 'control' in bundled_image_id:
                control_node_id = bundled_image_id['control']
            elif 'compute' in bundled_image_id:
                compute_node_id = bundled_image_id['compute']

        # get instance type
        instance_type = control['type']
        self.debug('Instance type %s' % instance_type)
        # get compute node number
        cluster_size = self.cloud_instances.get_cluster_size() - 1
        self.debug('Number of computation nodes %d' % cluster_size)
        # copy list for termination
        temp_instance_list = list(self.cloud_instances.get_list().values())

        # delete old info
        self.debug('Deleting %s from backup file' % args.name)
        self.cloud_instances.del_by_name(args.name)

        self.debug('Setting save info')
        # set saved cloud info, and change status to saved
        self.cloud_instances.checkpoint_cloud_instances(args.name,
                                                        control_node_id,
                                                        compute_node_id,
                                                        instance_type,
                                                        cluster_size)
        # save cluster
        self.debug('Saving cluster into backup file')
        self.cloud_instances.save_instances()

        # terminate instances
        for instance in temp_instance_list:
            if type(instance) is dict:
                self.terminate_instance(instance['id'])
                self.del_known_host(instance['ip'])
# ---------------------------------------------------------------------
# METHODS TO RESTORE VIRTUAL CLUSTER
# ---------------------------------------------------------------------

    def restore_cluster(self, args):
        '''
        Method for restoring cluster

        Parameters:
            args -- this method deals with
                    args.name -- virtual cluster name

        Logic:
            Loads control node id, compute node id, instance type,
            cluster size from backup file.
            Creates cluster of size one using control node id
            Creates cluster of cluster size using compute node id
            Associates IP addresses with all created instances
            Granted cluster was saved before, so no need to install
            softwares again, but need to configure SLURM accordingly
            because all host names changed. No need to create mumge-key
            because munge-key was also saved in each instance during the
            saving process.

            Change status to RUN in the end, and save this restored cluster
            infomation into backup file

        No returns
        '''
        if self.interface == 'boto':
            self.msg('UNIMPLEMENTED')
            sys.exit()
        if self.cloud == 'eucalyptus':
            self.msg('bugs')
            sys.exit()
        
        control_node_num = 1

        # only restore cluster which is saved
        self.debug('Checking if %s is existed' % args.name)
        if self.cloud_instances.if_exist(args.name):
            self.debug('Getting cloud %s' % args.name)
            self.cloud_instances.get_cloud_instances_by_name(args.name)
            if self.cloud_instances.if_status(self.cloud_instances.SAVED):
                self.debug('Cloud status: %s' % self.cloud_instances.SAVED)
                # if cluster is saved, delete old cluster, and create a
                # new cloud instance for deploying
                control_node_id = self.cloud_instances.get_list()['control']
                self.debug('control node %s' % control_node_id)
                compute_node_id = self.cloud_instances.get_list()['compute']
                self.debug('compute node %s' % compute_node_id)
                instance_type = self.cloud_instances.get_list()['type']
                self.debug('instance type %s' % instance_type)
                cluster_size = self.cloud_instances.get_list()['size']
                self.debug('cluster size %s' % cluster_size)
                self.debug('Creating new cloud instance list')
                self.cloud_instances.clear()
                self.debug('Deleting old info from backup file')
                self.cloud_instances.set_cloud_instances_by_name(args.name)
            else:
                self.msg('Error in restoring virtual cluster %s, not saved?'
                          % args.name)
                sys.exit()
        else:
            self.msg('Error in locating virtual cluster %s, not created?'
                     % args.name)
            sys.exit()

        cluster_size = int(cluster_size) + control_node_num
        self.print_section('Restoring virtual cluster')
        self.msg('cluster name      -- %s' % args.name)
        self.msg('number of nodes   -- %s' % cluster_size)
        self.msg('instance type     -- %s' % instance_type)
        self.msg('control image     -- %s' % control_node_id)
        self.msg('compute image     -- %s' % compute_node_id)

        # run control node
        self.debug('Creating control node %s' % control_node_id)
        self.euca_run_instance(self.user, control_node_num,
                               control_node_id, instance_type)
        # run compute nodes given number
        self.debug('Creating compute node %s' % compute_node_id)
        self.euca_run_instance(self.user, cluster_size - control_node_num,
                               compute_node_id, instance_type)

        # get free ip list
        self.debug('Getting free IP list')
        ip_lists = self.euca_describe_addresses()

        time.sleep(5)

        self.msg('\nAssociating IPs')
        for i in range(cluster_size):
            time.sleep(1)
            self.debug('Getting cloud from index %d' % i)
            instance = self.cloud_instances.get_by_id(i)
            while not self.euca_associate_address(instance, ip_lists[i]):
                self.msg('Error in associating IP %s with instance %s, '
                     'trying again'
                     % (ip_lists[i], instance['id']))
                time.sleep(1)

        # check ssh port but not install
        self.debug('Checking alive instance for deploying')
        for instance in self.cloud_instances.get_list().values():
            if type(instance) is dict:
                threading.Thread(target=self.installation,
                                 args=[instance, 60, False]).start()
        while threading.activeCount() > 1:
            time.sleep(1)
        # cnfig SLURM but not generating munge-keys
        self.debug('Configuating SLURM')
        self.config_slurm(False)
        # set status to run and save
        self.debug('Setting status to %s' % self.cloud_instances.RUN)
        self.cloud_instances.set_status(self.cloud_instances.RUN)
        self.debug('Deleting old cloud instance info')
        self.cloud_instances.del_by_name(args.name)
        self.debug('Saving cloud instance info')
        self.cloud_instances.save_instances()

# ---------------------------------------------------------------------
# METHODS TO TERMINATE NAD CLEANUP
# ---------------------------------------------------------------------
    @classmethod
    def del_known_host(cls, ip_addr):
        '''
        Deletes known host info from ~/.ssh/known_hosts

        Parameter:
            ip_addr -- IP address

        Logic:
            Deletes known host information from ~/.ssh/known_hosts
            in case it shows man-in-middle-attack message when starts
            different cluster but using the same IP addresses

        No returns
        '''

        known_hosts = '~/.ssh/known_hosts'
#        self.msg('Deleting host info from known_hosts')

        with open(os.path.expanduser(known_hosts)) as srcf:
            host_list = srcf.readlines()
        srcf.close()

        with open(os.path.expanduser(known_hosts), 'w') as destf:
            for host in host_list:
                if host.find(ip_addr) < 0:
                    destf.write(host)
        destf.close()

    def terminate_instance(self, instance_id):
        '''terminate instance given instance id'''

        self.msg('Terminating instance %s' % instance_id)
        if self.interface == 'euca2ools':
            os.system('euca-terminate-instances %s' % instance_id)
        elif self.interface == 'boto':
            try:
                self.ec2_conn.terminate_instances([instance_id])
            except:
                self.msg('ERROR: terminat instance %s failed' % instance_id)

    def shut_down(self, args):
        '''
        Method for shutting down a cluster

        Parameters:
            args -- this method deals with
                    args.name -- virtual cluster name

        Logic:
            Only terminates cloud instance which is not terminated
            Checking its existence before termination.
            Delete host info from ~/.ssh/known_hosts after each termination
            Change status according to following:
                If current status is SAVED, then does not change status
                If current status is RUN, then changes it to DOWN

        No returns
        '''

        # only terminate cluster which is not terminated
        self.debug('Checking if %s is existed' % args.name)
        if self.cloud_instances.if_exist(args.name):
            self.debug('Getting cloud instance %s' % args.name)
            self.cloud_instances.get_cloud_instances_by_name(args.name)
            self.debug('Checking cloud status')
            # check if cloud instance is terminated
            if self.cloud_instances.if_status(self.cloud_instances.DOWN):
                self.msg('\nError in terminating cluster %s, already down?'
                          % args.name)
                sys.exit()
        else:
            self.msg('\nError in finding virtual cluster %s, not created?'
                     % args.name)
            sys.exit()

        for instance in self.cloud_instances.get_list().values():
            if type(instance) is dict:
                self.terminate_instance(instance['id'])
                self.del_known_host(instance['ip'])

        # change status to terminated, and save
        self.debug('If status is %s' % self.cloud_instances.RUN)
        if self.cloud_instances.if_status(self.cloud_instances.RUN):
            self.debug('Setting status to %s' % self.cloud_instances.DOWN)
            self.cloud_instances.set_status(self.cloud_instances.DOWN)
            self.debug('Deleting instance old info')
            self.cloud_instances.del_by_name(args.name)
            self.debug('Saving instance into backup file')
            self.cloud_instances.save_instances()
# ---------------------------------------------------------------------
# METHODS TO SHOW VIRTUAL CLUSTER(S) STATUS
# ---------------------------------------------------------------------

    def show_status(self, args):
        '''
        Show status of cluster(s)

        Parameters:
            args -- this method deals with
                    args.name -- virtual cluster name

        Logic:
            Reads from backup file to load cluster information given
            cluster name. If cluster name is specified, then after
            checks its existence, loads it to display. If no cluster
            name is specified, then loads all cluster instances to
            display. If no clusters are saved in the backup file, after
            prints help message, then quits the program

        No returns
        '''

        if not args.name:
            # get all cloud intances
            cloud_set = self.cloud_instances.get_all_cloud_instances()
            # if no cloud instances created, then prints msg and quits
            if len(cloud_set) == 0:
                self.msg('\nYou do not have any virtual clusters')
                sys.exit()
            for cloud in cloud_set:
                self.msg('\n====================================')
                self.msg('Virtual Cluster %s (status: %s)'
                         % (cloud['name'], cloud['status']))
                self.msg('====================================')
                if cloud['status'] == self.cloud_instances.SAVED:
                    self.msg('Control node -- %s, '
                             'Compute node -- %s, '
                             'Instance type -- %s, '
                             'Cluster size -- %s'
                             % (cloud['control'], cloud['compute'],
                                cloud['type'], cloud['size']))
                else:
                    for index in range(self.cloud_instances.get_cluster_size(
                                                        cloud)):
                        if index == 0:
                            node_type = 'control node'
                        else:
                            node_type = 'compute node'
                        self.msg('%s:\t%s\t%s\t%s\t%s'
                                 % (cloud[index]['id'], node_type,
                                    cloud[index]['ip'], cloud[index]['image'],
                                    cloud[index]['type']))
        else:
            if not self.cloud_instances.if_exist(args.name):
                self.msg('Error in finding virtual cluster %s, not created.'
                          % args.name)
                sys.exit()
            self.cloud_instances.get_cloud_instances_by_name(args.name)
            self.msg('\n====================================')
            self.msg('Virtual Cluster %s (status: %s)'
                     % (args.name, self.cloud_instances.get_status()))
            self.msg('====================================')
            if self.cloud_instances.get_list()['status'] == \
                    self.cloud_instances.SAVED:
                self.msg('Control node -- %s, '
                         'Compute node -- %s, '
                         'Instance type -- %s, '
                         'Cluster size -- %s'
                         % (self.cloud_instances.get_list()['control'],
                            self.cloud_instances.get_list()['compute'],
                            self.cloud_instances.get_list()['type'],
                            self.cloud_instances.get_list()['size']))
            else:
                for index in range(self.cloud_instances.get_cluster_size()):
                    cloud = self.cloud_instances.get_by_id(index)
                    if index == 0:
                        node_type = 'control node'
                    else:
                        node_type = 'compute node'
                    self.msg('%s:\t%s\t%s\t%s\t%s'
                             % (cloud['id'], node_type,
                                cloud['ip'], cloud['image'],
                                cloud['type']))

# ---------------------------------------------------------------------
# METHODS TO SHOW VIRTUAL CLUSTER LIST
# ---------------------------------------------------------------------

    def get_list(self, _args):
        '''
        lists all virtual clusters and status

        Parameters:
            args -- this method deals with
                    None

        Logic:
            Reads from backup file to load all virtual cluster information
            If no cloud instance saved, after shows help message, then quits
            the program
        '''

        # get all cloud instances lists
        cloud_set = self.cloud_instances.get_all_cloud_instances()
        # if no cloud created, then prints msg and quits
        if len(cloud_set) == 0:
            self.msg('\nYou do not have any virtual clusters')
            sys.exit()

        self.msg('\n===============================')
        self.msg('Virtual Cluster list')
        self.msg('================================')
        for cloud in cloud_set:
            self.msg('%s: %d compute nodes, 1 control node; status: %s'
                     % (cloud['name'],
                        self.cloud_instances.get_cluster_size(cloud) - 1,
                        cloud['status']))

# ---------------------------------------------------------------------
# METHODS TO RUN MPI PROGRAM
# ---------------------------------------------------------------------
    def run_program(self, args):

        if self.cloud_instances.if_exist(args.name):
            self.debug('Getting cloud instance %s' % args.name)
            self.cloud_instances.get_cloud_instances_by_name(args.name)
            self.debug('Checking cloud status')
            # check if cloud instance is terminated
            if self.cloud_instances.if_status(self.cloud_instances.DOWN):
                self.msg('\nERROR: Cluster %s already down?'
                          % args.name)
                sys.exit()
        else:
            self.msg('\nError in finding virtual cluster %s, not created?'
                     % args.name)
            sys.exit()

        program_name = args.program.split('/')[-1].split('.')[0]
        for instance in self.cloud_instances.get_list().values():
            if type(instance) is dict:
                threading.Thread(target=self.copy_compile_prog,
                                 args=[instance, program_name]).start()

        while threading.activeCount() > 1:
            time.sleep(1)

        self.msg('\nRunning program %s\n' % program_name)
        # run program on control node
        self.execute(self.cloud_instances.get_by_id(0),
                     "salloc -N %d mpirun %s"
                     % (int(args.number), program_name))

    def copy_compile_prog(self, instance, prog):
        self.copyto(instance, prog)
        self.execute(instance, "mpicc %s.c -o %s" % (prog, prog))
######################################################################
# MAIN
######################################################################


def commandline_parser():
    '''
    Parses commandline

    Checks if python version is above 2.7
    '''

    # Check pyhon version
    if sys.version_info < (2, 7):
        print "ERROR: you must use python 2.7 or greater"
        sys.exit(1)

    virtual_cluster = Cluster()

    parser = \
        argparse.ArgumentParser(description='Virtual'
                                ' cluster management operations',
                                version='0.2.0')
    parser.add_argument('--file', action='store',
                        help='Specify futuregrid configure file')
    parser.add_argument('--debug', action='store_true',
                        help='print debug message')
    parser.add_argument('--default-repository', action='store_true',
                        help='using default software repository')
    parser.add_argument('--create-key', action='store_true',
                        help='create userkey')
    parser.add_argument('--interface', action='store',
                        help='choose interface to use')
    parser.add_argument('--cloud', action='store',
                        help='choose cloud')
    subparsers = parser.add_subparsers(help='commands')

    # status command
    status_parser = subparsers.add_parser('status',
            help='Show virtual cluster status')
    status_parser.add_argument('-a', '--name', action='store',
                               help='Show status of '
                               'virtual cluster of given name')
    status_parser.set_defaults(func=virtual_cluster.show_status)

    # list command
    list_parser = subparsers.add_parser('list',
            help='List virtual cluster and status')
    list_parser.set_defaults(func=virtual_cluster.get_list)

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
    restore_parser.set_defaults(func=virtual_cluster.restore_cluster)

    #mpirun command
    run_program_parser = subparsers.add_parser('mpirun',
            help='Run a simple MPI program')
    run_program_parser.add_argument('-a', '--name', action='store',
                                   required=True,
                                   help='Virtual cluster name')
    run_program_parser.add_argument('-p', '--program', action='store',
                                   required=True,
                                   help='Program source file')
    run_program_parser.add_argument('-n', '--number', action='store',
                                   required=True,
                                   help='Number of compute nodes to use')
    run_program_parser.set_defaults(func=virtual_cluster.run_program)
    args = parser.parse_args()

    # parse config file, if config file is not specified,
    # then use default file which is ~/.futuregrid/futuregrid.cfg
    if args.file:
        virtual_cluster.parse_conf(args.file)
    else:
        virtual_cluster.parse_conf()

    # set flags
    virtual_cluster.set_flag(args)
    # choose interface
    virtual_cluster.set_cloud(args.cloud)
    virtual_cluster.set_interface(args.interface)
    args.func(args)

if __name__ == '__main__':
    commandline_parser()

