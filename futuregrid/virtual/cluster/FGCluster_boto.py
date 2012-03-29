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
from time import sleep
import threading
import ConfigParser
import random
import Queue
import boto.ec2
import boto

from boto.ec2.connection import EC2Connection
from boto.ec2.instanceinfo import InstanceInfo
from CloudInstances import CloudInstances
#from futuregrid.virtual.cluster.CloudInstances import CloudInstances
from subprocess import Popen, PIPE
from ConfigParser import NoOptionError
from ConfigParser import NoSectionError
import re

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
    ec2_cert = None
    ec2_private_key = None
    eucalyptus_cert = None
    enrc = None
    slurm = None
    
    ec2_conn = None

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

        Logic:
            Sets control flags

        No returns
        '''

        self.if_debug = args.debug
        self.if_default = args.default_repository
        self.if_create_key = args.create_key

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
            username = PUT-YOUR-USER-NAME-HERE
            # Backup file for saving and loading virtual cluster(s)
            backup = ~/.futuregrid/virtual-cluster
            # Slurm configuration input file
            slurm = ~/.futuregrid/slurm.conf.in
            # userkey pem file
            userkey = ~/%(username).pem
            # userkey name
            user = %(username)
            # euca2ools certificate file
            ec2_cert = ~/cert.pem
            # euca2ools private file
            ec2_private_key = ~/pk.pem
            # nova certificate file
            eucalyptus_cert = ~/cacert.pem
            # nova environment file
            novarc = ~/novarc

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
            self.enrc = config.get('virtual-cluster', 'enrc')
            self.debug('enrc %s' % self.enrc)
            self.slurm = config.get('virtual-cluster', 'slurm')
            self.debug('SLURM configuration input file %s' % self.slurm)

            # checking if all file are present
            self.debug('Checking if all file are present')
            if not os.path.exists(os.path.expanduser(self.userkey)):
#                if self.if_create_key:
#                    # create key for user
##                    self.add_keypair(self.user)
#                    if self.if_keypair_exits(self.user):
#                        self.msg('\nYou have userkey %s.pem, please correct'
#                                 ' its location in configuration file'
#                                 % self.user)
#                        sys.exit()
#                    else:
#                        self.add_keypair(self.user, self.userkey)
#                else:
                self.msg('ERROR: You must have userkey file')
                sys.exit(1)
            if not os.path.exists(os.path.expanduser(self.enrc)):
                self.msg('ERROR: You must have novarc file')
                sys.exit(1)
            else:
                self.debug('Reading environment')
                nova_key_dir = os.path.dirname(self.enrc)            
                if nova_key_dir.strip() == "":
                    nova_key_dir = "."
                os.environ["NOVA_KEY_DIR"] = nova_key_dir

                with open(os.path.expanduser(self.enrc)) as enrc_content:
                    for line in enrc_content:
                        if re.search("^export ", line):
                            line = line.split()[1]                    
                            parts = line.split("=")
                            value = ""
                            for i in range(1, len(parts)):
                                parts[i] = parts[i].strip()
                                parts[i] = os.path.expanduser(os.path.expandvars(parts[i]))                    
                                value += parts[i] + "="
                                value = value.rstrip("=")
                                value = value.strip('"')
                                value = value.strip("'") 
                                os.environ[parts[0]] = value

            if not os.path.exists(os.path.expanduser(self.slurm)):
                self.msg('ERROR: You must have slurm.conf.in file')
                sys.exit(1)

            self.debug('Checking backup file')
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
        except NoSectionError:
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
    
        self.user = os.path.splitext(self.userkey.split('/')[-1])[0]

# ---------------------------------------------------------------------
# METHOD TO RUN COMMANDS
# ---------------------------------------------------------------------
    def _execute_local(self, command):
        '''
        Executes a command locally

        Parameters:
            command -- shell command
        Logic:
            Executes a command locally
        No returns
        '''

        self.debug(command)
        os.system(command)
    def get_command_result(self, command):
        '''
        Gets command output

        Parameters:
            command -- shell command

        Logic:
            Gets result of command

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

        Logic:
            Executes a command on the remote host

        No returns
        '''

        self.debug("ssh -i %s ubuntu@%s '%s'" % (self.userkey,
                  instance['ip'], command))
        os.system("ssh -i %s ubuntu@%s '%s'" % (self.userkey,
                  instance['ip'], command))

    def copyto(self, instance, filename):
        '''
        Copies the named file to the instance

        Parameters:
            instance -- cloud instance
            filename -- the name of file to copy

        Logic:
            Copies the named file to the home directory of remote host

        No returns
        '''

        self.debug('scp -i %s %s ubuntu@%s:~/' % (self.userkey,
                  filename, instance['ip']))
        os.system('scp -i %s %s ubuntu@%s:~/' % (self.userkey,
                  filename, instance['ip']))

    def update(self, instance):
        '''
        Executes a software update on the specified instance

        Parameters:
            instance -- cloud instance

        Logic:
            Executes software update on a remote host

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

        Logic:
            Installs a software on a remote host

        No returns
        '''

        self.execute(instance, 'sudo apt-get install --yes '
                     + packagenames)
# ---------------------------------------------------------------------
# METHOD TO CHECK AVALIABLITY
# ---------------------------------------------------------------------

    def check_avaliable(self, instance):

        cmd = "ssh -i %s ubuntu@%s uname" % (self.userkey, instance['ip'])

        check_process = Popen(cmd, shell=True, stdout=PIPE)
        status = os.waitpid(check_process.pid, 0)[1]
        if status == 0:
            return True
        else:
            return False

    def installation(self, install=True):
        '''
        Checks if instances are ready to deploy and installs the
        softwares on the instance which is ready

        Parameters:
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

        # max retry
        max_retry = 50

        # ready list for instances who are ready to install
        ready_instances = []

        # waitting time list for instances
        wait_instances = {}

        # ip change time count for instance
        ip_change_count = {}
        # init waitting time for all instanes to 0
        # add instance to ready_instances
        for instance in self.cloud_instances.get_list().values():
            if type(instance) is dict:
                wait_instances[instance['id']] = 0
                ip_change_count[instance['id']] = 0
                ready_instances.append(instance)

        # check if ssh port of all VMs are alive for listening
        while True:
            for instance in ready_instances:
                # try to connect ssh port
                if self.check_avaliable(instance):

                    # install on instance which is ready
                    if install:
                        self.msg('Starting thread to install '
                                 'on %s' % instance['ip'])
                        process_thread = \
                                threading.Thread(target=self.deploy_services,
                                                 args=[instance])
                        process_thread.start()
                        ready_instances.remove(instance)

                else:
                    self.debug('ssh in %s is closed' % instance['ip'])
                    self.msg('Checking %s availability...' % instance['ip'])
                    self.msg('Trying %d (max try %d)'
                             % (wait_instances[instance['id']], max_retry))
                    # increase waitting time for instance
                    wait_instances[instance['id']] += 1
                    self.debug('%s waits %d' % (instance['id'],
                                            wait_instances[instance['id']]))
                    # if reaches limit
                    if wait_instances[instance['id']] > max_retry:
                        # if change IP does not help
                        # then give up this intacne
                        if ip_change_count[instance['id']] == 1:
                            
                            # get instance index
                            instance_index = \
                                self.cloud_instances.get_index(instance)
#                            # remove this instance from ready instance list
#                            ready_instances.remove(instance)
#                            self.msg('Instance %s creation failed'
#                                     % instance['id'])
#                            # delete this instance from cloud instance list
#                            self.cloud_instances.del_instance(instance)
#                            # if no control node or only control node left
#                            if self.cloud_instances.get_cluster_size() == 1:
#                                self.msg('Create cluster failed, '
#                                         'please try again')
#                                for element in \
#                                    self.cloud_instances.get_list().values():
#                                    if type(element) is dict:
#                                        self.terminate_instance(element['id'])
#                                sys.exit()
#                            else:
#                                self.terminate_instance(instance['id'])
#                                # try to create a new one
#                                self.euca_run_instance(self.user,
#                                                       1,
#                                                       instance['image'],
#                                                       instance['type'],
#                                                       instance_index)
#                                self.debug('Getting free public IPs')
#                                # get free IP list
#                                ip_lists = self.euca_describe_addresses()
#                                sleep(2)
#
#                                new_instance = \
#                                    self.cloud_instances.get_by_id(
#                                                        instance_index)
#                                self.msg('\nAssociating IP with %s'
#                                         % new_instance['id'])
#                                new_ip = ip_lists[random.randint(0,
#                                                        len(ip_lists) - 1)]
#                                while not \
#                                    self.euca_associate_address(new_instance,
#                                                                new_ip):
#                                    self.msg('Error in associating IP %s '
#                                             'with instance %s, '
#                                             'trying again'
#                                             % (new_ip, new_instance['id']))
#                                    sleep(1)
#                                wait_instances[new_instance['id']] = 0
#                                ip_change_count[new_instance['id']] = 0
#                                ready_instances.append(new_instance)

                        else:
                            self.msg('\nTrying different IP address on %s'
                                 % instance['id'])
                            self.debug('Associating new IP on %s'
                                       % instance['id'])
                            self.change_public_ip(instance['id'], instance['ip'])
                            wait_instances[instance['id']] = 0
                            ip_change_count[instance['id']] += 1

            # check if all vms are ready
            if len(ready_instances) == 0:
                # wait all threads are done
                self.debug('Waitting all thread are done')
                while threading.activeCount() > 1:
                    sleep(1)
                self.debug('All thread are done')
                break

    def show_status(self, args):
        print args

    def ec2_connect(self, cloud):

        if cloud not in ('nova', 'eucalyptus'):
            self.msg('ERROR: supports nova, eucalyptus')
            sys.exit()

        if cloud.strip() == 'nova':
            path = "/services/Cloud"
        elif cloud.strip() == 'eucalyptus':
            path = "/services/Eucalyptus"
            
        endpoint = os.getenv('EC2_URL').lstrip("http://").split(":")[0]
        try:  
            region = boto.ec2.regioninfo.RegionInfo(name=cloud, endpoint=endpoint)
        except:
            self.msg('ERROR: error in getting region information')
            sys.exit()
        
        try:
            self.ec2_conn = EC2Connection(os.getenv("EC2_ACCESS_KEY"), os.getenv("EC2_SECRET_KEY"), is_secure=False, region=region, port=8773, path=path)
        except:
            self.msg('ERROR: error in connecting to EC2')
            sys.exit()

    def get_list(self, args):
        print ''
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

        self.debug('Opening %s' % self.slurm)
        self.msg('\nConfiguring slurm.conf')
        with open(os.path.expanduser(self.slurm)) as srcf:
            input_content = srcf.readlines()
        srcf.close()

        self.debug('Getting control machie id')
        # set control machine
        controlMachine = self.cloud_instances.get_by_id(0)['id']
        output = ''.join(input_content) % vars()

        self.msg('\nControl node %s' % controlMachine)

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
                        conf.write('NodeName=%s Procs=1 State=UNKNOWN\n'
                                   % instance['id'])
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
                self.get_command_result("ssh -i %s ubuntu@%s"
                                        " 'sudo cat /etc/munge/munge.key'"
                                         % (self.userkey,
                                        self.cloud_instances.get_by_id(0)['ip'
                                        ]))
            munge_key.close()

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
            sleep(1)

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

    def get_all_public_ips(self):
        return self.ec2_conn.get_all_addresses(addresses=None, filters=None)

    def get_free_ip(self):
        for address in self.get_all_public_ips():
            address_public_ip = address.public_ip
            address_instance_id = address.instance_id
            if not address_instance_id:
                return address_public_ip

    def associate_public_ip(self, instance_id, address_public_ip):
        try:
            self.ec2_conn.associate_address(instance.id, address_public_ip)
            self.cloud_instances.
            return True
        except:
            return False

#    def change_public_ip(self, instance_id, address_public_ip):
#        rediasso = True
#        reasso = True
#        free_public_ip = self.get_free_ip()
#        while (rediasso):
#            try:
#                self.ec2_conn.disassociate_address(address_public_ip)
#                rediasso = False
#            except:
#                self.msg('ERROR: error in disassociating IP %s, trying again' % address_public_ip)
#        
#        while (reasso):
#            try:
#                self.ec2_conn.associate_address(instance_id, free_public_ip)
#                reasso = False
#            except:
#                self.msg('ERROR: error in associating IP %s, trying again' % address_public_ip)
#
#        self.cloud_instances.set_ip_by_id(instance_id, free_public_ip)

    def create_cluster(self,args):

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

        self.debug('Checking if image is avaliable')
        try:
            image = self.ec2_conn.get_image(args.image)
            if not image.state == "available":
                self.msg('Image %s is not availabe right now, please try again later' % args.image)
                self.ec2_conn.close()
                sys.exit()
        except:
            self.msg('ERROR: getting image')
            sys.exit()

        cluster_size = int(args.number) + 1
        self.debug('Cluster size is (control node included): %d'
                   % cluster_size)
        self.msg('\nCreating virtual cluster')
        self.msg('cluster name    -- %s' % args.name)
        self.msg('numbe of nodes  -- %s' % cluster_size)
        self.msg('instance type   -- %s' % args.type)
        self.msg('image id        -- %s' % args.image)

        self.debug('Creating new cloud instance %s' % args.name)
        # set cloud instance list
        self.cloud_instances.set_cloud_instances_by_name(args.name)
       
        try:
            reservation = self.ec2_conn.run_instances(args.image, cluster_size, cluster_size, self.user)
        except:
            self.msg('ERROR: Error in lunching instances, please try again')
            self.ec2_conn.close()
            sys.exit()

        self.msg('Associating public IPs')
        for instance in reservation.instances:
            sleep(1)
            free_public_ip = self.get_free_ip()
            while not self.associate_public_ip(instance, free_public_ip):
                self.msg('ERROR: error in associating IP address with %s, trying again' % instance.id)
        

        self.debug('Creating IU ubunto repo source list')
        # choose repo, by defalt, using IU ubuntu repo
#        self.define_repo()
#        self.installation()
    def shut_down(self, args):
        print ''
    def checkpoint_cluster(self, args):
        print ''
    def restore_cluster(self, args):
        print ''
        
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
                                version='0.1.8')
    parser.add_argument('--file', action='store',
                        help='Specify futuregrid configure file')
    parser.add_argument('--debug', action='store_true',
                        help='print debug message')
    parser.add_argument('--default-repository', action='store_true',
                        help='using default software repository')
    parser.add_argument('--create-key', action='store_true',
                        help='create userkey')
    parser.add_argument('--cloud', action='store',
                        required=True, help='cloud')
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

    args = parser.parse_args()

    # set flags
    virtual_cluster.set_flag(args)
    # parse config file, if config file is not specified,
    # then use default file which is ~/.futuregrid/futuregrid.cfg
    if args.file:
        virtual_cluster.parse_conf(args.file)
    else:
        virtual_cluster.parse_conf()
    virtual_cluster.ec2_connect(args.cloud)
    args.func(args)

if __name__ == '__main__':
    commandline_parser()
