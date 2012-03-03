#! /usr/bin/env python

import getopt
import sys
import os
import pickle

from futuregrid.virtual.cluster.cloudinstances import *


class FgRunProg:

    def __init__(self, userkey, number, file_name, name):
        self.userkey = userkey
        self.number = number
        self.file_name = file_name
        self.name = name
        self.cloud_instances = CloudInstances(name)

    def ssh(self, userkey, ip, command):
        os.system("ssh -i %s.pem ubuntu@%s '%s'"
                  % (userkey, ip, command))

    def scp(self, userkey, fileName, ip):
        os.system("scp -i %s.pem %s ubuntu@%s:~/"
                  % (userkey, fileName, ip))

    def run_program(self):

        print '\n...Running program %s '
        'on virtual cluster %s......' % (self.file_name, self.name)
        for instance in self.cloud_instances.list()[1:]:
            self.scp(self.userkey, self.file_name, instance['ip'])
            self.ssh(self.userkey, instance['ip'],
                     "mpicc %s -o %s" % (self.file_name,
                                        self.file_name.split('.')[0]))

        print '\n...Running program %s......' % self.file_name.split('.')[0]
        # run program on control node
        self.ssh(self.userkey,
                 self.cloud_instances.get_by_id(1)['ip'],
                 "salloc -N %d mpirun %s"
                 % (int(self.number), self.file_name.split('.')[0]))


def usage():
    print '-h/--help        Display this help.'
    print '-u/--userkey     provide userkey'
    print '-n/--node        compute node number'
    print '-f/--file        program source file'
    print '-a/--name        virtual cluster name'


def main():
    try:
        opts, args = getopt.getopt
        (sys.argv[1:],
         "hu:n:f:a:",
         ["help", "userkey=", "number=", "file=", "name="])
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
        elif opt in ("-f", "--file"):
            file_name = arg
        elif opt in ("-a", "--name"):
            name = arg

    fgc = FgRunProg(userkey, number, file_name, name)
    fgc.run_program()

if __name__ == '__main__':
    main()
