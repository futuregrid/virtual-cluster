#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import ConfigParser

######################################
#change here to parameterize the test#
######################################
'''
This is Nova setting
If want to test performance in eucalyputs, need to change futuregrid.cfg and instance type and image id which should be ubuntu natty
'''
test_runs = 3
nodes_num_1 = 1
nodes_num_2 = 2
nodes_num_4 = 4
nodes_num_8 = 8
nodes_num_16 = 16
nodes_num_24 = 24
nodes_num_32 = 32
node_nums = [1,2,4,8,16,24,32]
image_id = None
instance_type_small = None
instance_type_medium = None
instance_type_large = None

def read_config():
    global image_id
    global instance_type_small
    global instance_type_medium
    global instance_type_large

    config = ConfigParser.ConfigParser()
    config.read([os.path.expanduser('~/.futuregrid/futuregrid.cfg'),
                         'futuregrid.cfg'])
    cloud = config.get('virtual-cluster', 'cloud')
    if cloud == 'nova':
        image_id = 'ami-0000001d'
        instance_type_small = 'm1.small'
        instance_type_medium = 'm1.medium'
        instance_type_large = 'm1.large'

    elif cloud == 'eucalyptus':
        image_id = 'emi-FC6A1197'
        instance_type_small = 'm1.small'
        instance_type_medium = 'c1.medium'
        instance_type_large = 'm1.large'

def process_data(create_time, run_prog, terminate_time):
    if not create_time.split()[0] == 'Performance':
        print 'Test failed'
        return
    with open('performance_test', 'aw') as pt:
        pt.write(create_time+'\t'+run_prog+'\t'+terminate_time+'\n')
    pt.close()
    
def performance_test():

    # instance type - m1.small
    for node_num in node_nums:
        for i in range(test_runs):
            print '\n\nRunning Test %d' % int(i + 1)
            print 'Node-num: %s\tInstance-type: %s' % (node_num, instance_type_small)
            print '\n\nCreating cluster'
            create_time =  create_cluster(instance_type_small, node_num)
            print '\n\nRunning MPI program'
            run_prog =  run_program(node_num)
            print '\n\nTerminating cluster'
            terminate_time =  terminate_cluster()
            print 'Adding data'
            process_data(create_time, run_prog, terminate_time)

    # instance type - m1.medium
    for node_num in node_nums:
        for i in range(test_runs):
            print '\n\nRunning Test %d' % int(i + 1)
            print 'Node-num: %s\tInstance-type: %s' % (node_num, instance_type_medium)
            print '\n\nCreating cluster'
            create_time =  create_cluster(instance_type_medium, node_num)
            print '\n\nRunning MPI program'
            run_prog =  run_program(node_num)
            print '\n\nTerminating cluster'
            terminate_time =  terminate_cluster()
            print 'Adding data'
            process_data(create_time, run_prog, terminate_time)

    # instance type - m1.large
    for node_num in node_nums:
        for i in range(test_runs):
            print '\n\nRunning Test %d' % int(i + 1)
            print 'Node-num: %s\tInstance-type: %s' % (node_num, instance_type_large)
            print '\n\nCreating cluster'
            create_time =  create_cluster(instance_type_large, node_num)
            print '\n\nRunning MPI program'
            run_prog =  run_program(node_num)
            print '\n\nTerminating cluster'
            terminate_time =  terminate_cluster()
            print 'Adding data'
            process_data(create_time, run_prog, terminate_time)

def create_cluster(instance_type, number):
    print '\nInstance type -- %s' % instance_type
    print 'Number of computation nodes -- %s' % number
    return os.popen("fg-cluster run -a test -i %s -t %s -n %s" % (image_id, instance_type, number)).read().split('\n')[-2]

def terminate_cluster():
    return os.popen("fg-cluster terminate -a test").read().split('\n')[-2]

def run_program(number):
    return os.popen("fg-cluster mpirun -p helloworld.c -a test -n %s" % number).read().split('\n')[-2]

    
def main():
    read_config()
    performance_test()

if __name__ == '__main__':
    main()