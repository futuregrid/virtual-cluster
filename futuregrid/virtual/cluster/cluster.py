#! /usr/bin/env python
import getopt, sys, os, pickle

from futuregrid.virtual.cluster.cloudinstances import *

class cluster (object):

    debug = True
    
    def __init__(self):
        super(cluster, self).__init__()


    def msg(self, message):
        print message

    def __init__(self, name):
        self.name = name
        self.cloud_instances = CloudInstances(name)

# ---------------------------------------------------------------------
# METHODS TO TERMINATE NAD CLEANUP
# ---------------------------------------------------------------------        

    def clean(self, name):
        self.debug('Clearing up the instance', 'progress')
        self.cloud_instances.del_by_name(name)
        print '\r Clearing up the instance: completed'
	
    def terminate_instance(self, instance_id):
        print 'terminating instance %s' %instance_id
        os.system("euca-terminate-instances %s" %instance_id)

    def shut_down(self):
        for instance in self.cloud_instances.list()[1:]:
            self.terminate_instance(instance['id'])
        self.clean(self.name)


# ---------------------------------------------------------------------
# METHODS TO PRINT HELP MESSAGES
# ---------------------------------------------------------------------        

    def debug(self, msg, status)
        if debug: 
            print '\r Clearing up the instance: completed'

    def usage():
        print '-h/--help    Display this help.'
        print '-a/--name    provide name of virtual cluster.'



######################################################################
# MAIN
######################################################################


    def commandline_parser():

        try:
                opts, args = getopt.getopt(sys.argv[1:], "ha:", ["help", "name="])
        except getopt.GetoptError:
                usage()
                sys.exit()

        for opt, arg in opts:
                if opt in ("-h", "--help"):
                        usage()
                        sys.exit()
		if opt in ("-a", "--name"):
                        name = arg

        fgs=FgShutdown(name)
	fgs.shut_down()

if __name__ == '__main__':
    commandline_parser()


