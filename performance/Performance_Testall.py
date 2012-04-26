#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import ConfigParser

######################################
#change here to parameterize the test#
######################################
'''
This is Nova setting
If want to test performance in eucalyputs, need to change futuregrid.cfg accordingly
Image shoudld be ubuntu natty if u want to use IU ubuntu repository
'''
test_runs = 3
node_nums = [1,2,4,8,16,24,32]
cloud_specific_para = {'nova':{'image_id':'ami-0000001d', 'instance_type':['m1.small', 'm1.medium', 'm1.large']}, 
                       'eucalyptus':{'image_id':'emi-FC6A1197', 'instance_type':['m1.small', 'c1.medium', 'm1.large']}}

def process_data(create_time, run_prog, terminate_time):
    if not create_time.split()[0] == 'Performance':
        print 'Test failed'
        return
    with open('performance_test_raw', 'a') as pt:
        pt.write(create_time+'\t'+run_prog+'\t'+terminate_time+'\n')
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
            pt.write('\t\t\tTest name\tTotal Time\tIP association time\tInstallation time'
                     '\tConfiguration time\tIP association failure\tIP change\tTermination\tExecution time\tTermination\n')
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