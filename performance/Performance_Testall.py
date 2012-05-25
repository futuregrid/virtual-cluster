#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import ConfigParser
import time

# Before each test, please make sure you have the correct image
# to use in euca and nova, fg-cluster should run among all ubuntu images
# If it fails, please use --default-repository


######################################
#change here to parameterize the test#
######################################

test_runs = 10
node_nums = [1, 2, 4, 8, 16, 24, 32]
cloud_specific_para = {'nova':{'image_id':'ami-0000001d', 'instance_type':['m1.small', 'm1.medium', 'm1.large']}, 
                       'eucalyptus':{'image_id':'emi-D21D3F6C', 'instance_type':['m1.small', 'c1.medium', 'm1.large']}}

def process_data(create_time, run_prog, terminate_time):

    #if no output
    if not create_time.split()[0] == 'Performance':
        print 'Test failed'
        return

    data = []
    create_time_parts = create_time.split('\t')
    
    data.insert(0, create_time_parts[1])
    data.insert(1, create_time_parts[2])
    data.insert(2, create_time_parts[4])
    data.insert(3, create_time_parts[5])
    data.insert(4, run_prog)
    data.insert(5, terminate_time)
    data.insert(6, create_time_parts[3])
    data.insert(7, create_time_parts[6])
    data.insert(8, create_time_parts[7])
    data.insert(9, create_time_parts[8])
 
    with open('performance_test_raw', 'a') as pt:
        pt.write('%-20s\t%-15s\t%-15s\t%-15s\t%-15s\t%-15s\t%-15s\t%-20s\t%-10s\t%-10s\n'
                     % (data[0], data[1], data[2], data[3], data[4], data[5], data[6], data[7], data[8], data[9]))
    pt.close()
    
def performance_test():

    config = ConfigParser.ConfigParser()
    config.read([os.path.expanduser('~/.futuregrid/futuregrid.cfg'),
                         'futuregrid.cfg'])
    cloud = config.get('virtual-cluster', 'cloud')
    image_id = cloud_specific_para[cloud]['image_id']
    instance_types = cloud_specific_para[cloud]['instance_type']

    # Writes the first row
    if not os.path.isfile('performance_test_raw'):
        with open('performance_test_raw', 'w') as pt:
            pt.write('%-20s\t%-15s\t%-15s\t%-15s\t%-15s\t%-15s\t%-15s\t%-20s\t%-10s\t%-10s\n'
                     % ('Test Name',
                        'Total Time',
                        'Installation',
                        'Configuration',
                        'Execution',
                        'Termination',
                        'IP association',
                        'IP association fail',
                        'IP change',
                        'Restart'))
        pt.close()

    # Runs tests, writes data into file
    for instance_type in instance_types:
        for node_num in node_nums:
            for i in range(test_runs):
                print '\n\nRunning Test %d' % int(i + 1)
                print 'Node-num: %s\tInstance-type: %s' % (node_num, instance_type)
                print '\n\nCreating cluster'
                create_time =  create_cluster(image_id, instance_type, node_num)
                print '\n\nRunning MPI program'
                run_prog =  run_program(node_num)
                print '\n\nTerminating cluster'
                terminate_time =  terminate_cluster()
                print 'Adding data'
                process_data(create_time, run_prog, terminate_time)
                time.sleep(60)

def create_cluster(image_id, instance_type, number):
    print '\nInstance type -- %s' % instance_type
    print 'Number of computation nodes -- %s' % number
    return os.popen("fg-cluster run -a test -i %s -t %s -n %s" % (image_id, instance_type, number)).read().split('\n')[-2]

def terminate_cluster():
    return os.popen("fg-cluster terminate -a test").read().split('\n')[-2]

def run_program(number):
    return os.popen("fg-cluster mpirun -p helloworld.c -a test -n %s" % number).read().split('\n')[-2]

    
def main():
    performance_test()

if __name__ == '__main__':
    main()