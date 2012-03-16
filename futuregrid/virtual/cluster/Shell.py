#!/usr/bin/env python

#import argparse

import os
import pprint
import optparse
from cmd2 import Cmd
from cmd2 import make_option
from cmd2 import options
from cmd2 import Cmd2TestCase

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

    def do_list(self):
        print "to do List"

    def do_config(self, filename):
        print "to do config"

    def do_debug(self, debug=True):
        print "to do debug"

    def do_run(self, arg):
        print "to do run"

    def do_checkpoint(self, arg):
        print "to do checkpoint"

    def do_restore(self, arg):
        print "to do restore"

    def do_terminate(self, arg):
        print "to do terminate"

    def do_status(self, arg):
        print "to do status"

    def do_list(self, arg):
        print "to do list"


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
