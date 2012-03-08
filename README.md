HOW TO INSTALL
==============

System requirements
------------------

* euca2ools: verison 1.2
* python: version 2.7
* virtualenv (no admin rights)

Introduction
------------

* TODO: section that explains what this project is about
* TODO: openstack eucalyptus AWS?
* TODO: FutureGrid, where can I run this

Installation
------------

We assume that yo do not have super user priviledges on the computer
where you like to install our tool.

TODO: only for india
TODO: module load python

### Step 1: Download virtualenv.py from following link:

    wget https://raw.github.com/pypa/virtualenv/master/virtualenv.py
    
### Step 2: Install virtualenv by

    python virtualenv.py --system-site-packages ENV
    
### Step 3: Activate virtualenv by

    source ENV/bin/activate
    
### Step 4: install the virtual cluster with pip

    ENV/bin/pip install futuregrid.virtual.cluster
    
<br>

FutureGrid Specific Instalation
-------------------------------

Install without admin rights on india futuregrid

Go to the portal https://portal.futuregrid.org/ 

If you do not have an account, please apply for one
https://portal.futuregrid.org/user/register

In order for you to get access, you need to apply for a portal account
and create a FG project. This is in detail explained at
https://portal.futuregrid.org/gettingstarted Do not forget to upload
your public key. (se also https://portal.futuregrid.org/generating-ssh-keys-futuregrid-access)

Once you have a vaild portal account and a valid project, you can go
ahead and use FutureGrid

Our virtual cluster is best executed on our machine called
india.futuregrid.org

Please log into this machine and follw the steps that we have outined
in the previous sectionto installthe software and than run it while
following the instaructions from the next section


HOW TO RUN
==========

Create a virtual cluster
-------------------------

Run following command will create a virtual cluster of given name.

    fg-cluster -f config_file run -n number_of_computation_nodes -s instance_type -i image_id -a cluster_name

Parameters:

-f: Futuregrid configuration file named futuregrid.cfg. An example configuration file can be found at 

* https://github.com/futuregrid/virtual-cluster/blob/master/etc/futuregrid.cfg

It has the following format:

    [virtual-cluster]                         
    username = PUT-YOUR-USER-NAME-HERE
    # Backup file for saving and loading virtual cluster(s)  
    backup = ~/.futuregrid/virtual-cluster
    # Slurm configuration input file
    slurm = ~/.futuregrid/slurm.conf.in
    # userkey pem file
    userkey = ~/%(username).pem
    # userkey name
    user = %(username)
    # euca2ools certificate file                
    ec2_cert = ~/cert.pem
    # euca2ools private file         
    ec2_private_key = ~/pk.pem
    # nova certificate file
    eucalyptus_cert = ~/cacert.pem
    # nova environment file
    novarc = ~/novarc

You will have to modify the <PUT-YOUR-USER-NAME-HERE> occurence within the file with the name that you use to associate your key. The file is to be placed at ~/.futuregrid/futuregrid.cfg or concatenated to an already existing futuregrid.cfg file.

-n: Number of computation nodes (control node not included)

-s: Instance type

-i: Image id

-a: Virtual cluster name

For example:

    fg-cluster -f futuregrid.cfg run -n 2 -t m1.small -i ami-0000001d -a mycluster1

Virtual cluster info will be saved in backup file specified in 
futuregrid configuration file. Note: Cluster name should be different 
as other virtual clusters which had been created. If want to use 
default configure file, config file should be created as 
~/.ssh/futuregrid.cfg, then argument -f can be omitted


Save a virtual cluster
-----------------------

Run following command will save a currently running virtual cluster into one
control image and compute image for later resotre

    fg-cluster -f config_file checkpoint -c control_node_bucket -t control_node_name -m compute_bucket -e compute_name -a cluster_name

Parameters:

-f: Futuregrid configuration file

-c: Control node bucket name

-t: Control node image name

-m: Compute node bucket name

-e: compute node image name

-a: Virtual cluster name

For example:

    fg-cluster -f futuregrid.cfg -c c1 -t c1.img -m c2 -e c2.img -a mycluster1

Note: Cluster name should be a name of cluster which is
currently running. Generated image ids (including one control 
node image id and one compute image id) will be registered which
could be used for later restore


Restore a virtual cluster
--------------------------

TODO: its unclear what resore actully does 

Run following command will restore a virtual cluster which was saved before

    fg-cluster -f config_file restore -n number_of_computation_nodes -c control_node_image_id -m compute_node_image_id -s instance_type -a cluster_name

Parameters;

-f: Futuregrid configuration file

-n: Number of computaion node (control node not included)

-c: Control node image id

-m: Compute node image id

-s: Instance type (for all nodes)

-a: Virtual cluster name

For example:

    fg-cluster -f futuregrid.cfg -n 2 -c ami-0000001d -m ami-0000001d -s m1.small -a mycluster2

Note: Cluster name should be different as the names of currently running 
virtual clusters. Control node image id and compute image id should be ids which are generated 
by runing checkpoint

List the virtual clusters
----------------------------

TODO: develop a command that lists the virtual clustes and tells me in which state they are

Shutdown a virtual cluster
---------------------------

Run following command will terminate a virtual cluster

    fg-cluster -f config_file terminate -a cluster_name

Parameters:

-f: Futuregrid configuration file

-a: Virtual cluster name

For example:

    fg-cluster -f futuregrid.cfg terminate -a mycluster2

Note: Cluster name should be a name of cluster which is currently
running. After executing this command, cluster info will be removed
from backup file which specified by configuration file


Show status of virtual cluster(s)
---------------------------

Run following command will show status of currently running 
virtual cluster(s) including cluster size, image id, instance id, ip

    fg-cluster -f config_file status -a cluster_name

Parameters:

-f: Futuregrid configuration file

-a: Virtual cluster name


For example: 

Show status of one specific cluster

    fg-cluster -f futuregrid.cfg status -a mycluster1

Show status of all currently running clusters

    fg-cluster -f futuregrid.cfg status

Note: If argument -a is specified, then name of cluster should be 
a cluster that is currently running


Run a simple MPI program on virtual cluster
===========================================

Given MPI vesion of helloworld.c

step 1: Copy helloworld.c to each node in virtual cluster

step 2: Complie on each node, run:

    mpicc hellowrld.c -o helloworld 

step 3: Go to control node, run:

    salloc -N 2 mpirun helloworld

where -N is the number of computation nodes you want to run with. And 
should not be larger than the actual number of computation nodes

Execution result:

    salloc: Granted job allocation 2
    Hello world from process 0 of 3
    Hello world from process 1 of 3
    Hello world from process 2 of 3
    salloc: Relinquishing job allocation 2
    
Using fg-cluster-runprogram
---------------------------

    fg-cluster-runprogram.py -f futuregrid.cfg -p helloworld.c -n 3 -a mycluster1

-f: Futuregrid configuration file

-p: Program source code file

-n: Number of computaion nodes you want to run with

-a: Number of virtual cluster


Note: Virtual cluster name should be a name of cluster which is currently running


FOR DEVELOPERS ONLY
===================

Generating the Distribution
---------------------------

pull code from github

TODO:

make pip
this creates the tar file that you can install via pip in ./dist

sudo pip install --upgrade dist/*.tar.gz

this wil install the files by default into /usr/local/bin/fg-cluster  