#!/usr/bin/env python

#import argparse

import os
import pprint
import optparse
from cmd2 import Cmd
from cmd2 import make_option
from cmd2 import options
from cmd2 import Cmd2TestCase

import unittest, sys

class CmdLineAnalyzeEucaData(Cmd):
    #multilineCommands = ['None']
    #Cmd.shortcuts.update({'&': 'speak'})
    #maxrepeats = 3
    #Cmd.settable.append('maxrepeats')

    pp = pprint.PrettyPrinter(indent=0)

    echo = True
    timing = True

    def preloop(self):
        print "WELCOME"
        
    def postloop(self):
        print "BYE FORM GREGOR"

    def do_list(self):
        print "do List"

    def do_config(self, filename)
        print "do config"
    
    def do_debug(self, debug=True)
        print "do debug"

    def do_run(self, arg)
        print "do run"

    def do_checkpoint(self, arg)
        print "do checkpoint"

    def do_restore(self, arg)
        print "do restore"

    def do_terminate(self, arg)
        print "do terminate"

    def do_status(self, arg)
        print "do status"

    def do_list(self, arg)
        print "do list"



parser = optparse.OptionParser()
parser.add_option('-t', '--test', dest='unittests', action='store_true', default=False, help='Run unit test suite')
(callopts, callargs) = parser.parse_args()
if callopts.unittests:
    sys.argv = [sys.argv[0]]  # the --test argument upsets unittest.main()
    unittest.main()
else:
    app = CmdLineAnalyzeEucaData()
    app.cmdloop()
