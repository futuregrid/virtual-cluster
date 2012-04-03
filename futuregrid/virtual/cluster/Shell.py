#!/usr/bin/env python

#import argparse
#import os
import pprint
import optparse
from cmd2 import Cmd
from cmd2 import make_option
from cmd2 import options
#from cmd2 import Cmd2TestCase

import unittest
import sys


class Shell(Cmd):
    #multilineCommands = ['None']
    #Cmd.shortcuts.update({'&': 'speak'})
    #maxrepeats = 3
    #Cmd.settable.append('maxrepeats')

    pp = pprint.PrettyPrinter(indent=0)

    echo = True
    timing = True
    cluster = None

    prompt = "fg> "

    logo = """
  _____       _                   ____      _     _
 |  ___|_   _| |_ _   _ _ __ ___ / ___|_ __(_) __| |
 | |_  | | | | __| | | | '__/ _ \ |  _| '__| |/ _` |
 |  _| | |_| | |_| |_| | | |  __/ |_| | |  | | (_| |
 |_|    \__,_|\__|\__,_|_|  \___|\____|_|  |_|\__,_|
----------------------------------------------------
    """

    def preloop(self):
        print self.logo

    def postloop(self):
        print "BYE FORM GREGOR"

    @options([
        make_option('-f', '--file', type="string",
                    help="cluster name"),
        make_option('-i', '--interface', type="string",
                    help="interface"),
        ])
    def do_config(self, args, opts):
        if not opts.interface == 'boto' and \
            not opts.interface == 'euca2ools':
            print 'Please specify interface (boto or euca2ools)'
            sys.exit()
        if opts.interface == 'boto':
            from futuregrid.virtual.cluster.FGCluster_boto import Cluster
#            from FGCluster_boto import Cluster
            self.cluster = Cluster()
            self.cluster.ec2_connect('nova')
        elif opts.interface == 'euca2ools':
            from futuregrid.virtual.cluster.FGCluster import Cluster
#            from FGCluster import Cluster
            self.cluster = Cluster()
        
        if not opts.file:
            self.cluster.parse_conf()
        else:
            self.cluster.parse_conf()

    def do_debug(self, debug=True):
        print "to do debug"

    @options([
        make_option('-a', '--name', type="string",
                    help="cluster name"),
        make_option('-n', '--number', type="int",
                    help="number of computation nodes"),
        make_option('-t', '--type', type="string",
                    help="instance type"),
        make_option('-i', '--image', type="string",
                    help="image id"),
        ])
    def do_run(self, args, opts):
        self.cluster.create_cluster(opts)

    @options([
        make_option('-a', '--name', type="string",
                    help="cluster name"),
        make_option('-c', '--controlb', type="string",
                    help="control node bucket"),
        make_option('-t', '--controln', type="string",
                    help="control node image"),
        make_option('-m', '--computeb', type="string",
                    help="compute node bucket"),
        make_option('-e', '--computen', type="string",
                    default='not specified',
                    help="compute node image"),
        ])
    def do_checkpoint(self, args, opts):
        self.cluster.checkpoint_cluster(opts)

    @options([
        make_option('-a', '--name', type="string",
                    help="cluster name"),
        ])
    def do_restore(self, args, opts):
        self.cluster.restore_cluster(opts)

    @options([
        make_option('-a', '--name', type="string",
                    help="cluster name"),
        ])
    def do_terminate(self, args, opts):
        self.cluster.shut_down(opts)

    @options([
        make_option('-a', '--name', type="string",
                    help="cluster name"),
        ])
    def do_status(self, args, opts):
        self.cluster.show_status(opts)

    def do_list(self, args):
        self.cluster.get_list(args)


def main():
    parser = optparse.OptionParser()
    parser.add_option('-t', '--test',
                      dest='unittests',
                      action='store_true',
                      default=False,
                      help='Run unit test suite')
    (callopts, callargs) = parser.parse_args()
    if callopts.unittests:
        sys.argv = [sys.argv[0]]  # the --test argument upsets unittest.main()
        unittest.main()
    else:
        app = Shell()
        app.cmdloop()

if __name__ == '__main__':
    main()
