#!/usr/bin/python
# -*- coding: utf-8 -*-

import os

######################################
#change here to parameterize the test#
######################################
test_runs = 3
instance_type = 'm1.small'
nodes_num = 2
image_id = 'ami-0000001d'


def process_data(create_time, run_prog, terminate_time):
    if not create_time.split()[0] == 'Performance':
        print 'Test failed'
        return
    with open('performance_test', 'aw') as pt:
        pt.write(create_time+'\t'+run_prog+'\t'+terminate_time+'\n')
    pt.close()
    
def performance_test():

    for i in range(test_runs):
        print '\n\nRunning Test %d' % int(i + 1)
        print '\n\nCreating cluster'
        create_time =  create_cluster(instance_type, nodes_num)
        print create_time
        print '\n\nRunning MPI program'
        run_prog =  run_program(nodes_num)
        print run_prog
        print '\n\nTerminating cluster'
        terminate_time =  terminate_cluster()
        print terminate_time
        print 'Adding data'
        process_data(create_time, run_prog, terminate_time)

def create_cluster(instance_type, number):
    print '\nInstance type -- %s' % instance_type
    print 'Number of computation nodes -- %s' % number
    return os.popen("python FGCluster.py run -a test -i %s -t %s -n %s" % (image_id, instance_type, number)).read().split('\n')[-2]

def terminate_cluster():
    return os.popen("python FGCluster.py terminate -a test").read().split('\n')[-2]

def run_program(number):
    return os.popen("python FGCluster.py mpirun -p helloworld.c -a test -n %s" % number).read().split('\n')[-2]

    
def main():
    performance_test()

if __name__ == '__main__':
    main()