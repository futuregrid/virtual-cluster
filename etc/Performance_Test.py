#!/usr/bin/python
# -*- coding: utf-8 -*-

import os

def process_data(create_time, run_prog, terminate_time):
    with open('performance_test', 'aw') as pt:
        pt.write(create_time+'\t'+run_prog+'\t'+terminate_time+'\n')
    pt.close()
    
def performance_test():

    ######################################
    #change here to parameterize the test#
    ######################################
    test_runs = 3
    instance_type = 'm1.small'
    nodes_num = 1

    for i in range(test_runs):
        print '\n\nRunning Test %d' % int(i + 1)
        print '\n\nCreating cluster'
        create_time =  create_cluster(instance_type, nodes_num)
        print '\n\nRunning MPI program'
        run_prog =  run_program(nodes_num)
        print '\n\nTerminating cluster'
        terminate_time =  terminate_cluster()
        print 'Adding data'
        process_data(create_time, run_prog, terminate_time)

def create_cluster(instance_type, number):
    return os.popen("fg-cluster run -a test -i ami-0000001d -t %s -n %s" % (instance_type, number)).read().split('\n')[-2]

def terminate_cluster():
    return os.popen("fg-cluster terminate -a test").read().split('\n')[-2]

def run_program(number):
    return os.popen("fg-cluster mpirun -p helloworld.c -a test -n %s" % number).read().split('\n')[-2]

    
def main():
    performance_test()

if __name__ == '__main__':
    main()