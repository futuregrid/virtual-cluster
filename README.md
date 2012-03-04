HOW TO INSTALL
==============

System requirement
------------------
euca2ools: verison 1.2

python: version 2.7

Installation
------------
>>>>make egg

>>>>make install


HOW TO RUN
==========

Create a virtual cluster
-------------------------

Run following command will create a virtual cluster of given name.

>>>>fg-cluster -f config_file run -n number_of_computation_nodes -s instance_type -i image_id -a cluster_name

Parameters:

-f: Futuregrid configuration file which has the format of following:

    [virtual-cluster]                           
    backup = ~/.futuregrid/virtual-cluster    # Backup file for saving and loading virtual cluster(s)
    slurm = ~/.futuregrid/slurm.conf.in       # Slurm configuration input file
    userkey = ~/.ssh/username.pem             # userkey pem file
    user = username                           # userkey name
    ec2_cert = ~/ssh/cert.pem                 # euca2ools certificate file
    ec2_private_key = ~/.ssh/pk.pem           # euca2ools private file
    eucalyptus_cert = ~/.ssh/cacert.pem       # nova certificate file
    novarc = ~/.ssh/novarc                    # nova environment file

-n: Number of computation nodes (control node not included)
-s: Instance type
-i: Image id
-a: Virtual cluster name

For example:

>>>>fg-cluster -f futuregrid.cfg -n 2 -s m1.small -i ami-0000001d -a mycluster1

Virtual cluster info will be saved in backup file specified in 
futuregrid configuration file. Note: Cluster name should be different 
as other virtual clusters which had been created. If want to use 
default configure file, config file should be created as 
~/.ssh/futuregrid.cfg, then argument -f can be omitted


Save a virtual cluster
-----------------------

Run following command will save a currently running virtual cluster into one
control image and compute image for later resotre

>>>>fg-cluster -f config_file checkpoint -c control_node_bucket -t control_node_name -m compute_bucket -e compute_name -a cluster_name

Parameters:

-f: Futuregrid configuration file
-c: Control node bucket name
-t: Control node image name
-m: Compute node bucket name
-e: compute node image name
-a: Virtual cluster name

For example:

>>>>fg-cluster -f futuregrid.cfg -c c1 -t c1.img -m c2 -e c2.img -a mycluster1

Note: Cluster name should be a name of cluster which is
currently running. Generated image ids (including one control 
node image id and one compute image id) will be registered which
could be used for later restore


Restore a virtual cluster
--------------------------

Run following command will restore a virtual cluster which was saved before

>>>>fg-cluster -f config_file restore -n number_of_computation_nodes -c control_node_image_id -m compute_node_image_id -s instance_type -a cluster_name

Parameters;

-f: Futuregrid configuration file
-n: Number of computaion node (control node not included)
-c: Control node image id
-m: Compute node image id
-s: Instance type (for all nodes)
-a: Virtual cluster name

For example:

>>>>fg-cluster -f futuregrid.cfg -n 2 -c ami-0000001d -m ami-0000001d -s m1.small -a mycluster2

Note: Cluster name should be different as the names of currently running 
virtual clusters. Control node image id and compute image id should be ids which are generated 
by runing checkpoint


Shutdown a virtual cluster
---------------------------

Run following command will terminate a virtual cluster

>>>>fg-cluster -f config_file terminate -a cluster_name

Parameters:

-f: Futuregrid configuration file
-a: Virtual cluster name

For example:

>>>>fg-cluster -f futuregrid.cfg terminate -a mycluster2

Note: Cluster name should be a name of cluster which is currently
running. After executing this command, cluster info will be removed
from backup file which specified by configuration file


Show status of virtual cluster(s)
---------------------------

Run following command will show status of currently running 
virtual cluster(s) including cluster size, image id, instance id, ip

>>>>fg-cluster -f config_file status -a cluster_name

Parameters:

-f: Futuregrid configuration file
-a: Virtual cluster name


For example: 

Show status of one specific cluster

>>>>fg-cluster -f futuregrid.cfg status -a mycluster1

Show status of all currently running clusters

>>>>fg-cluster -f futuregrid.cfg status

Note: If argument -a is specified, then name of cluster should be 
a cluster that is currently running


Run a simple MPI program on virtual cluster
===========================================

Given MPI vesion of helloworld.c

step 1: Copy helloworld.c to each node in virtual cluster

step 2: Complie on each node, run:

>>>>mpicc hellowrld.c -o helloworld 

step 3: Go to control node, run:

>>>>salloc -N 2 mpirun helloworld

where -N is the number of computation nodes you want to run with. And 
should not be larger than the actual number of computation nodes




