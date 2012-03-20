#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
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
import socket
import time
import threading
import ConfigParser
import random

from futuregrid.virtual.cluster.CloudInstances import CloudInstances
#from CloudInstances import CloudInstances
from ConfigParser import NoOptionError
from ConfigParser import MissingSectionHeaderError
from ConfigParser import NoSectionError


class Cluster(object):
    """class of methods for run, checkpoint,
    restore, terminate, show status of cluster
    """

    userkey = None
    cloud_instances = None
    backup_file = None
    user = None
    ec2_cert = None
    ec2_private_key = None
    eucalyptus_cert = None
    novarc = None
    slurm = None

    # debug switch
    if_debug = False
    # if false, using IU ubuntu repository
    if_default = False
    # repo file name
    sources_list = 'sources.list'

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
            print message

    def set_debug(self, if_debug=False):
        '''set debug flag'''

        self.if_debug = if_debug

    def set_default(self, if_default=False):
        '''set debug flag'''

        self.if_default = if_default

# ---------------------------------------------------------------------
# METHOD TO PARSE CONFIGURATION FILE
# ---------------------------------------------------------------------

    def parse_conf(self, file_name='unspecified'):
        """
        Parse configuration file if given, default location
        '~/.futuregrid/futuregrid.cfg'

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
            self.user = config.get('virtual-cluster', 'user')
            self.debug('User %s' % self.user)
            self.ec2_cert = config.get('virtual-cluster', 'ec2_cert')
            self.debug('EC2_CERT %s' % self.ec2_cert)
            self.ec2_private_key = config.get('virtual-cluster',
                    'ec2_private_key')
            self.debug('EC2_PRIVATE_KEY %s' % self.ec2_private_key)
            self.eucalyptus_cert = config.get('virtual-cluster',
                    'eucalyptus_cert')
            self.debug('EUCALYPTUS_CERT %s' % self.eucalyptus_cert)
            self.novarc = config.get('virtual-cluster', 'novarc')
            self.debug('novarc %s' % self.novarc)
            self.slurm = config.get('virtual-cluster', 'slurm')
            self.debug('SLURM configuration input file %s' % self.slurm)

            self.debug('Checking if all files are present')
            if not os.path.exists(os.path.expanduser(self.userkey)) or \
                not os.path.exists(os.path.expanduser(self.ec2_cert)) or \
                not os.path.exists(os.path.expanduser(self.ec2_private_key)) or \
                not os.path.exists(os.path.expanduser(self.eucalyptus_cert)) or \
                not os.path.exists(os.path.expanduser(self.novarc)) or \
                not os.path.exists(os.path.expanduser(self.slurm)):
                self.msg('You must have all the files present as specified in '
                         'configuration file!')
                sys.exit(1)

            self.debug('Checking backup file')
            if not self.cloud_instances.set_backup_file(self.backup_file):
                self.msg('\nBackup file is corrupted, '
                         'please delete it and try again')
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
# METHOD TO DETECT OPEN PORT
# ---------------------------------------------------------------------

    def detect_port(self, install=True):
        '''
        detect if ssh port 22 is alive for listening
        if install is set to true, installation of
        SLURM and OpenMPI will start on VM which is ready
        '''

        # ready count for VM
        ready = 0
        count = 0
        msg_len = 5
        retry = 200

        # ready list for instances who are ready to install
        ready_instances = {}

        # waitting time list for instances
        wait_instances = {}

        # init waitting time for all instanes to 0
        for instance in self.cloud_instances.get_list().values():
            if type(instance) is dict:
                wait_instances[instance['id']] = 0

        # check if ssh port of all VMs are alive for listening
        while 1:
            for instance in self.cloud_instances.get_list().values():
                if type(instance) is dict:
                    # create ready dict using ip as key
                    # if True: ready to install
                    # if False: already installed
                    if not instance['id'] in ready_instances:
                        ready_instances[instance['id']] = True
                    # try to connect ssh port
                    try:
                        self.debug('trying to connect %s'
                                   % instance['ip'])
                        socket_s = socket.socket(socket.AF_INET,
                                socket.SOCK_STREAM)
                        socket_s.settimeout(1)
                        socket_s.connect((instance['ip'], 22))
                        socket_s.close()

                        # install on instance which is ready
                        if install:
                            if ready_instances[instance['id']]:
                                # set false, block other threads
                                ready_instances[instance['id']] = False
                                # ssh may fail due to heavy load of
                                # startup in instance, use sleep
                                time.sleep(2)
                                self.msg('Starting thread to install '
                                         'on %s' % instance['ip'])
                                process_thread = \
                                threading.Thread(target=self.deploy_services,
                                                 args=[instance])
                                process_thread.start()

                        ready = ready + 1

                    except IOError:
                        self.debug('ssh in %s is closed' % instance['ip'])
                        count += 1
                        if count > msg_len:
                            count = 0
                        sys.stdout.write('\rWaiting instances ready to deploy'
                                         + '.' * count + ' ' *
                                         (msg_len - count))
                        sys.stdout.flush()
                        ready = 0
                        # increase waitting time for instance
                        wait_instances[instance['id']] += 1
                        # if reaches limit
                        if wait_instances[instance['id']] > retry:
                            self.msg('Trying different IP address on %s'
                                     % instance['id'])
                            # get free ip addresses
                            ip_lists = self.euca_describe_addresses()
                            # disassociate current one
                            self.disassociate_address(instance['ip'])
                            # associate a new random free ip
                            self.debug('Associating new IP on %s'
                                       % instance['id'])
                            self.euca_associate_address(instance['id'],
                                    ip_lists[random.randint(0,
                                                            len(ip_lists)
                                                            - 1)])
                            self.debug('New IP is %s' % instance['ip'])
                            wait_instances[instance['id']] = 0

                        time.sleep(1)

            # check if all vms are ready
            self.debug('Total number of instances %d'
                       % int(self.cloud_instances.get_cluster_size()))
            self.debug('%d instances are ready' % ready)
            if ready == self.cloud_instances.get_cluster_size():
                # wait all threads are done
                self.debug('Waitting all thread are done')
                while threading.activeCount() > 1:
                    time.sleep(1)
                self.debug('All thread are done')
                break

# ---------------------------------------------------------------------
# METHODS TO DO RPCs
# ---------------------------------------------------------------------

    def get_command_result(self, command):
        '''gets command output'''
        self.debug(command)
        return os.popen(command).read()

    def execute(self, instance, command):
        '''runs a command on the instance'''

        self.debug("ssh -i %s ubuntu@%s '%s'" % (self.userkey,
                  instance['ip'], command))
        os.system("ssh -i %s ubuntu@%s '%s'" % (self.userkey,
                  instance['ip'], command))

    def copyto(self, instance, filename):
        '''copyies the named file to the instance'''

        self.debug('scp -i %s %s ubuntu@%s:~/' % (self.userkey,
                  filename, instance['ip']))
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
        '''
        runs instances given parameters
        check if all instances are created
        correctly. program will exit if
        not all instances required are
        created, and terminate those which
        are running already
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
                self.debug('Adding instance %s' % instance_id_list[num])
                self.cloud_instances.set_instance(instance_id_list[num],
                                                  image,
                                                  instance_type)
            except:
                self.msg('\nError in creating instances.'
                         ' Program will exit')
                sys.exit()

    def euca_associate_address(self, instance, free_ip):
        '''associates instance with ip'''

        self.debug('euca-associate-address -i %s %s'
                   % (instance['id'], free_ip))
        if self.get_command_result('euca-associate-address -i %s %s'
                                   % (instance['id'],
                                      free_ip)).find('ADDRESS') < 0:
            return False
        # set ip using instance id
        self.msg('ADDRESS %s instance %s' % (free_ip, instance['id']))
        self.cloud_instances.set_ip_by_id(instance['id'], free_ip)
        # delete host from known_host file in case man-in-middle-attack
        self.debug('Deleting %s from known host if it already existed'
                   % free_ip)
        self.del_known_host(free_ip)
        return True

    def disassociate_address(self, current_ip):
        '''disassociates ip'''

        self.debug('euca-disassociate-address %s' % current_ip)
        os.system('euca-disassociate-address %s' % current_ip)

    def euca_describe_addresses(self):
        '''return list of free ips'''

        ip_list = []
        ips = [x for x in self.get_command_result('euca-describe-addresses'
               ).split('\n')]

        # store free ip into ip list for return
        for free_ip in ips:
            if free_ip.find('i-') < 0 and len(free_ip) > 0:
                ip_list.append(free_ip.split('\t')[1])
        return ip_list

    def create_cluster(self, args):
        '''
        method for creating cluster, associate ip with
        instances created, detect if they are ready to
        deploy, and then install SLURM and OpenMPI on
        them, do configure accordingly
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
        self.msg('\n...Creating virtual cluster......')
        self.msg('cluster name    -- %s' % args.name)
        self.msg('numbe of nodes  -- %s' % cluster_size)
        self.msg('instance type   -- %s' % args.type)
        self.msg('image id        -- %s' % args.image)

        self.debug('Creating new cloud instance %s' % args.name)
        # set cloud instance list
        self.cloud_instances.set_cloud_instances_by_name(args.name)

        self.debug('Creating cluster')
        # run instances given parameters
        self.euca_run_instance(self.user, cluster_size, args.image,
                               args.type)
        self.debug('Getting free public IPs')
        # get free IP list
        ip_lists = self.euca_describe_addresses()

        # immediatly associate ip after run instance
        # may lead to error, use sleep
        time.sleep(3)

        self.msg('\nAssociating IPs')
        for i in range(cluster_size):
            instance = self.cloud_instances.get_by_id(i)
            time.sleep(1)
            while not self.euca_associate_address(instance, ip_lists[i]):
                self.msg('Error in associating IP %s with instance %s, '
                     'trying again'
                     % (ip_lists[i], instance['id']))
                time.sleep(1)

        self.debug('Saving cloud instance into backup file')
        # save cloud instance
        self.cloud_instances.save_instances()

        self.debug('Creating IU ubunto repo source list')
        # choose repo, by defalt, using IU ubuntu repo
        self.define_repo()

        self.debug('Checking alive instance for deploying')
        # detect if VMs are ready for deploy
        self.detect_port()

        self.debug('Configuraing SLURM')
        # config SLURM system
        self.config_slurm()

        self.debug('Cleaning up')
        # clean repo file
        self.clean_repo()
        self.debug('Done creationg of cluster')

    def clean_repo(self):
        ''' remove source list file'''

        if not self.if_default:
            self.debug('Removing %s' % self.sources_list)
            os.remove(self.sources_list)

    def config_slurm(self, create_key=True):
        '''config slurm'''

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
        copy slurm configuration file and munge key file
        to every node, and start slurm
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
        ''' set ubuntu repo to IU repo'''

        iu_repo = 'http://ftp.ussg.iu.edu/linux/ubuntu/'

#        deb http://ftp.ussg.iu.edu/linux/ubuntu/ natty-updates main
#        deb-src http://ftp.ussg.iu.edu/linux/ubuntu/ natty-updates main
#        deb http://ftp.ussg.iu.edu/linux/ubuntu/ natty universe
#        deb-src http://ftp.ussg.iu.edu/linux/ubuntu/ natty universe
#        deb http://ftp.ussg.iu.edu/linux/ubuntu/ natty-updates universe
#        deb-src http://ftp.ussg.iu.edu/linux/ubuntu/ natty-updates universe
#        deb http://ftp.ussg.iu.edu/linux/ubuntu/ natty main
#        deb-src http://ftp.ussg.iu.edu/linux/ubuntu/ natty main

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
        '''deploy SLURM and OpenMPI services'''

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
        '''save instance given paramenters'''

        if kernel_id == None:
            self.debug("ssh -i %s ubuntu@%s '. ~/.profile;"
                       " sudo euca-bundle-vol -c ${EC2_CERT}"
                       " -k ${EC2_PRIVATE_KEY} -u ${EC2_USER_ID}"
                       " --ec2cert ${EUCALYPTUS_CERT} --no-inherit"
                       " -p %s -s 1024 -d /mnt/'"
                       % (self.userkey, instance_ip, instance_name))
            return self.get_command_result("ssh -i %s ubuntu@%s '. ~/.profile;"
                            " sudo euca-bundle-vol -c ${EC2_CERT}"
                            " -k ${EC2_PRIVATE_KEY} -u ${EC2_USER_ID}"
                            " --ec2cert ${EUCALYPTUS_CERT} --no-inherit"
                            " -p %s -s 1024 -d /mnt/'"
                             % (self.userkey, instance_ip,
                                instance_name))
        elif ramdisk_id == None:
            self.debug("ssh -i %s ubuntu@%s '. ~/.profile;"
                       " sudo euca-bundle-vol -c ${EC2_CERT}"
                       " -k ${EC2_PRIVATE_KEY} -u ${EC2_USER_ID}"
                       " --ec2cert ${EUCALYPTUS_CERT} --no-inherit"
                       " -p %s -s 1024 -d /mnt/ --kernel %s'"
                       % (self.userkey, instance_ip, instance_name,
                          kernel_id))
            return self.get_command_result("ssh -i %s ubuntu@%s '. ~/.profile;"
                            " sudo euca-bundle-vol -c ${EC2_CERT}"
                            " -k ${EC2_PRIVATE_KEY} -u ${EC2_USER_ID}"
                            " --ec2cert ${EUCALYPTUS_CERT} --no-inherit"
                            " -p %s -s 1024 -d /mnt/ --kernel %s'"
                             % (self.userkey, instance_ip, instance_name,
                            kernel_id))
        else:
            self.debug("ssh -i %s ubuntu@%s '. ~/.profile;"
                       " sudo euca-bundle-vol -c ${EC2_CERT}"
                       " -k ${EC2_PRIVATE_KEY} -u ${EC2_USER_ID}"
                       " --ec2cert ${EUCALYPTUS_CERT} --no-inherit"
                       " -p %s -s 1024 -d /mnt/ --kernel %s --ramdisk %s'"
                       % (self.userkey, instance_ip, instance_name,
                          kernel_id, ramdisk_id))
            return self.get_command_result("ssh -i %s ubuntu@%s '. ~/.profile;"
                            " sudo euca-bundle-vol -c ${EC2_CERT}"
                            " -k ${EC2_PRIVATE_KEY} -u ${EC2_USER_ID}"
                            " --ec2cert ${EUCALYPTUS_CERT} --no-inherit"
                            " -p %s -s 1024 -d /mnt/ --kernel %s --ramdisk %s'"
                             % (self.userkey, instance_ip, instance_name,
                            kernel_id, ramdisk_id))

    def upload_bundle(
        self,
        instance_ip,
        bucket_name,
        manifest,
        ):
        '''upload bundle given manifest'''

        self.debug("ssh -i %s ubuntu@%s '. ~/.profile;"
                   " euca-upload-bundle -b %s -m %s'"
                   % (self.userkey, instance_ip, bucket_name,
                      manifest))
        return self.get_command_result("ssh -i %s ubuntu@%s '. ~/.profile;"
                        " euca-upload-bundle -b %s -m %s'"
                         % (self.userkey, instance_ip, bucket_name,
                        manifest))

    def describe_images(self, image_id):
        '''get images infos'''

        self.debug('euca-describe-images %s' % image_id)
        return self.get_command_result('euca-describe-images %s' % image_id)

    def get_kernel_id(self, image_id):
        '''get kernel id'''

        command_result = [x for x in
                          self.describe_images(image_id).split()]
        if len(command_result) >= 8:
            self.debug('Kernel ID %s' % command_result[7])
            return command_result[7]

    def get_ramdisk_id(self, image_id):
        '''get ramdisk id'''

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
        ):
        '''
        save node given parameters
        upload and register
        '''

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
        return self.euca_register(image).split('\t')[1].strip()

    def euca_register(self, image):
        '''register image'''

        return self.get_command_result('euca-register %s' % image)

    def checkpoint_cluster(self, args):
        '''
        method for saving currently running instance into image
        and terminate the old one
        '''

        self.debug('Checking if %s is existed' % args.name)
        # check if cluter is existed
        if self.cloud_instances.if_exist(args.name):
            # get cluter by name
            self.debug('Getting cloud instance %s' % args.name)
            self.cloud_instances.get_cloud_instances_by_name(args.name)
            # if cluster is down, terminate the program
            if self.cloud_instances.if_status(self.cloud_instances.DOWN):
                self.msg('Error in locating virtual cluster %s, not running?'
                          % args.name)
                sys.exit()
        else:
            self.msg('Error in locating virtual cluster %s, not created?'
                     % args.name)
            sys.exit()

        self.msg('\n...Saving virtual cluster......')
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
            self.copyto(instance, self.ec2_cert)
            self.copyto(instance, self.ec2_private_key)
            self.copyto(instance, self.eucalyptus_cert)
            self.copyto(instance, self.novarc)
            self.execute(instance, 'cat novarc >> ~/.profile')
            self.execute(instance, 'source ~/.profile')

        # save control node
        self.msg('\nSaving control node %s' % control['id'])
        control_node_id = self.save_node(control['image'],
                                         control['ip'],
                                         args.controlb,
                                         args.controln)
        self.msg('\nControl node %s saved' % control['id'])

        # save compute node
        self.msg('\nSaving compute node %s' % compute['id'])
        compute_node_id = self.save_node(compute['image'],
                                         compute['ip'],
                                         args.computeb,
                                         args.computen)
        self.msg('\nCompute node %s saved' % compute['id'])

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
        '''method for restoring cluster'''

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
        self.msg('\n...Restoring virtual cluster......')
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
        self.euca_run_instance(self.user, cluster_size,
                               compute_node_id, instance_type)

        # get free ip list
        self.debug('Getting free IP list')
        ip_lists = self.euca_describe_addresses()

        time.sleep(3)

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
        self.detect_port(False)
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
        '''delete known host info from ~/.ssh/known_hosts'''

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
        os.system('euca-terminate-instances %s' % instance_id)

    def shut_down(self, args):
        '''method for shutting down a cluster'''

        # only terminate cluster which is not terminated
        self.debug('Checking if %s is existed' % args.name)
        if self.cloud_instances.if_exist(args.name):
            self.debug('Getting cloud instance %s' % args.name)
            self.cloud_instances.get_cloud_instances_by_name(args.name)
            self.debug('Checking cloud status')
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
        '''show status of cluster(s)'''

        if not args.name:
            for cloud in self.cloud_instances.get_all_cloud_instances():
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
                        self.msg('Instance %s: IP -- %s, Image id -- %s, '
                                 'Instance type -- %s'
                                 % (cloud[index]['id'], cloud[index]['ip'],
                                 cloud[index]['image'], cloud[index]['type']))
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
                for instance in self.cloud_instances.get_list().values():
                    if type(instance) is dict:
                        self.msg('Instance %s: IP -- %s, Image id -- %s, '
                                 'Instance type -- %s'
                                 % (instance['id'], instance['ip'],
                                    instance['image'], instance['type']))

# ---------------------------------------------------------------------
# METHODS TO SHOW VIRTUAL CLUSTER LIST
# ---------------------------------------------------------------------

    def get_list(self, args):
        '''list all virtual clusters and status'''

        self.msg('\n===============================')
        self.msg('Virtual Cluster list')
        self.msg('================================')
        for cloud in self.cloud_instances.get_all_cloud_instances():
            self.msg('%s: %d compute nodes; status: %s'
                     % (cloud['name'],
                        self.cloud_instances.get_cluster_size(cloud),
                        cloud['status']))

######################################################################
# MAIN
######################################################################


def commandline_parser():
    '''parse commandline'''

    if sys.version_info < (2, 7):
        print "ERROR: you must use python 2.7 or greater"
        sys.exit(1)

    virtual_cluster = Cluster()

    parser = \
        argparse.ArgumentParser(description='Virtual'
                                ' cluster management operations',
                                version='0.1.8')
    parser.add_argument('-f', '--file', action='store',
                        help='Specify futuregrid configure file')
    parser.add_argument('--debug', action='store_true',
                        help='print debug message')
    parser.add_argument('--default-repository', action='store_true',
                        help='using default software repository')
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

    # parse config file
    if args.file:
        virtual_cluster.parse_conf(args.file)
    else:
        virtual_cluster.parse_conf()

    # set debug flag
    virtual_cluster.set_debug(args.debug)
    # set default repository flag
    virtual_cluster.set_default(args.default_repository)

    args.func(args)

if __name__ == '__main__':
    commandline_parser()
