#! /usr/bin/env python

'''
Run MPI prigram on virtual cluster
'''

import sys
import os
import ConfigParser
import argparse

from futuregrid.virtual.cluster.CloudInstances import CloudInstances


class FgRunProg:
    '''run MPI program on a virtual cluster'''

    userkey = None
    cloud_instances = None
    backup_file = None

    def __init__(self):
        self.cloud_instances = CloudInstances()

    def execute(self, instance, command):
        '''runs a command on the instance'''

        os.system("ssh -i %s ubuntu@%s '%s'" % (self.userkey,
                  instance['ip'], command))

    def copyto(self, instance, filename):
        '''copyies the named file to the instance'''

        os.system('scp -i %s %s ubuntu@%s:~/' % (self.userkey,
                  filename, instance['ip']))

    def msg(self, message):
        '''method for printing messages'''

        print message

    def parse_conf(self, file_name='no file specified'):
        """
        Parse conf file if given, default location
        '~/.ssh/futuregrid.cfg'
        conf format:
        [virtual-cluster]
        backup = directory/virtual-cluster.dat
        userkey = directory/userkey.pem
        ec2_cert = directory/cert.pem
        ec2_private_key = directory/pk.pem
        eucalyptus_cert = directory/cacert.pem
        novarc = directory/novarc
        """

        config = ConfigParser.ConfigParser()

        config.read([os.path.expanduser('~/.ssh/futuregrid.cfg'),
                    file_name])

        # default location ~/.ssh/futuregrid.cfg

        self.backup_file = config.get('virtual-cluster', 'backup')
        self.userkey = config.get('virtual-cluster', 'userkey')

        self.cloud_instances.set_backup_file(self.backup_file)

    def run_program(self, args):
        '''copy program to each node, compile it and run'''

        self.parse_conf(args.file)
        if not self.cloud_instances.if_exist(args.name):
            self.msg('Error in locating virtual cluster %s, not created'
                      % args.name)
            sys.exit()
        self.cloud_instances.get_cloud_instances_by_name(args.name)

        for instance in self.cloud_instances.get_list()[1:]:
            self.copyto(instance, args.prog)
            self.execute(instance,
                     "mpicc %s -o %s" % (args.prog,
                                        args.prog.split('.')[0]))

        self.msg('\n...Running program %s......' % args.prog.split('.')[0])
        # run program on control node
        self.execute(self.cloud_instances.get_by_id(1),
                 "salloc -N %d mpirun %s"
                 % (int(args.number), args.prog.split('.')[0]))


def main():

    fg_run_prog = FgRunProg()

    parser = \
        argparse.ArgumentParser()
    parser.add_argument('-f', '--file', action='store',
                        help='Specify futuregrid configure file')
    parser.add_argument('-p', '--prog', action='store',
                        help='Specify program name')
    parser.add_argument('-n', '--number', action='store',
                        help='Numbe of computation node')
    parser.add_argument('-a', '--name', action='store',
                        help='Name of virtual cluster')
    parser.set_defaults(func=fg_run_prog.run_program)

    args = parser.parse_args()
    args.func(args)

if __name__ == '__main__':
    main()
