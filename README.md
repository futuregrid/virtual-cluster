INTRODUCTION
============

System requirements
------------------

* euca2ools: verison 1.2
* python: version 2.7.2
* virtualenv (no admin rights)

Introduction
------------

Project futuregrid.virtual.cluster is a virtual cluster management
software utilizing openstack resources on FutureGrid. The software
contains several parts that could help users easily manage their
operations to virtual clusters on FutureGrid.

Managment operations include: 

* Create virtual cluster(s)
* Save currently running virtual cluster(s)
* Restore saved virtual cluster(s) 
* Show status of virtual cluster(s) 
* Terminate virtual cluster(s)


HOW TO INSTALL
==============

Installation
------------

We assume that yo do not have super user priviledges on the computer
where you like to install our tool.

### Step 0: Prerequisites (not using india.futuregrid.org machines):
    
In order to make the installation process work smoothly, please make 
sure that the computer you like to install our tool has already
installed euca2ools (version 1.2) and Python (version 2.7). If you do
not have those tools or correct version installed. you may install 
euca2ools (version 1.2) from 

* http://eucalyptussoftware.com/downloads/releases/

and install python (version 2.7.2) from 

* http://python.org

After you check all the tools with version are correctly installed,
you may proceed with following steps to start installation.


### Step 0: Prerequisites (using india.futuregrid.org machines):

india.futuregrid.org has installed every tools you may need to finish this
installation, so to activate euca2ools (version 1.2) after you login into
india futuregrid machines, just simply do:
    
    $ module load euca2ools
    
To activate python 2.7.2, simply do:

    $ module load python/2.7.2

Those commands will help you load tools with correct version you need
to finish installation. So now you may proceed with following
installation steps.

### Step 1: Download virtualenv

Since you do not have super user priviledges, you need virtualenv in
order to finish the installtion. You may download virtualenv.py by
following command:

    $ wget https://raw.github.com/pypa/virtualenv/master/virtualenv.py
    
### Step 2: Install virtualenv

After you downloaded virtualenv, you can install it by following
command:

    $ python virtualenv.py --system-site-packages ENV
    
### Step 3: Activate virtualenv

After installation of virtualenv, you can activate virtualenv by
following command:

    $ source ENV/bin/activate
    
### Step 4: install the virtual cluster with pip

Once virtualenv is activated, you can use pip to install our tool by
following command:

    $ ENV/bin/pip install futuregrid.virtual.cluster

If you already had our tool installed, and you want to upgrade to
newest version, you can do it by following command:

	$ ENV/bin/pip install --upgrade futuregrid.virtual.cluster

NOTE: For more information about virtualenv, you may see documentation
of virtualenv on

* http://www.virtualenv.org/en/latest/index.html

FutureGrid Specific Instalation
-------------------------------

### Install without admin rights on india futuregrid

Go to the futuregrid portal 

* https://portal.futuregrid.org/ 

If you do not have a futuregrid account, please apply for one at link:

* https://portal.futuregrid.org/user/register

In order for you to get access to FutureGrid resources, you need to
apply for a portal account and create a Futuregrid project. This is in
detail explained at

* https://portal.futuregrid.org/gettingstarted 

Do not forget to upload your public key.  (see also
https://portal.futuregrid.org/generating-ssh-keys-futuregrid-access)

Once you have a vaild portal account and a valid project, you can go
ahead and use FutureGrid

Our virtual cluster is best executed on our machine called
india.futuregrid.org

Please log into this machine and follow the steps that we have outlined
in the previous section to install the software and then run it while
following the instaructions from the next section


HOW TO RUN
==========

Prerequisites
-------------

In order to use our tool, you need to obatin nova credentials and
configuration files for FutureGrid system, you can obtain your nova
credentials and configuration files for the FutureGrid systems. These
should have been placed in your home directory on the INDIA
system. Log in with your FutureGrid username (and SSH public key) and
look for a file called 'username'-nova.zip. If you do not have a
portal and HPC account please create one.  The credential zip file
(username-nova.zip)contains the user keys and rc file .Unzip this
file in your hom e directory. The novarc file contains the necessary
environment variables. Add nova environment variables to your .bashrc:

    $ cat novarc >> .bashrc
    $ source .bashrc
    
Create your private key by (Recommended: Use your user name as your
private key name):

    $ euca-add-keypair youruserkey > youruserkey.pem
    $ chmod 0600 youruserkey.pem

You can also use our tool to create a userkey for you, but you need 
to specify the userkey name in confifuration file which is listed 
below. The key can be created if you use --create-key argument before 
any subcommands when you first run our tool. For more help, 

    $ fg-cluster --help
    
NOTE: For more information about nova credentials, you can refer 
to tutorial at: 

* https://portal.futuregrid.org/tutorials/openstack


Create configuration file
-------------------------

You need to create a configuration file which needs to be passed to
this tool for locating necessary files in order to run. You can create
configuration file using text editor, or using an example we provide
to you

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

You will have to modify the <PUT-YOUR-USER-NAME-HERE> occurrence
within the file with the name that you use to associate your key. The
file is to be placed at ~/.futuregrid/futuregrid.cfg or concatenated
to an already existing futuregrid.cfg file.

NOTE: Please make sure all the files are placed under the location as
you specified in configuration file. You can also find an example of
slurm.conf.in file which is used by configuring SLURM system from

* https://github.com/futuregrid/virtual-cluster/blob/master/etc/slurm.conf.in 

You can modify SLURM configuration parameters for your customized
SLURM. But please leave "controlMachine" and "COMPUTE NODES"
untouched.

After you finished all steps above, you can use our tool to manage
your virtual clusters

Create a virtual cluster
-------------------------

Run following command will create a virtual cluster of given
parameters (command example is given below):

    $ fg-cluster -f <config-file> run -n <number-of-computation-nodes> -t <instance-type> -i <image-id> -a <cluster-name>

Parameters:

* -f: Futuregrid configuration file named futuregrid.cfg.
* -n: Number of computation nodes. This number of computation nodes does not include control node, so the
actual number for virtual cluster nodes is the number of computations node plus one control node.
* -s: Instance type. Instance type includes: m1.tiny, m1.small and m1.large.
* -i: Image id. You can obtain image id by following command:

        $ euca-describe-images
        
* -a: cluster name. The virtual cluster name which uniquely identifies your cluster.

For example:

    $ fg-cluster -f futuregrid.cfg run -n 2 -t m1.small -i ami-0000001d -a mycluster1

Virtual cluster info will be saved in backup file specified in
futuregrid configuration file. Note: Cluster name should be different
as other virtual clusters which is running if you want to run multiple
virtual clusters. If you want to use default configure file, you
should put this file at ~/.futuregrid/futuregrid.cfg, then argument -f
can be omitted


Save a virtual cluster
-----------------------

Run following command will save a currently running virtual cluster into one
control image and compute image for later resotre. (Installed softwares and 
unfinished jobs will also be saved)

    $ fg-cluster -f <config-file> checkpoint -c <control-node-bucket> -t <control-node-name> -m <compute-bucket> -e  <compute-name> -a <cluster-name>

Parameters:

* -f: Futuregrid configuration file
* -c: Control node bucket name. Bucket name which you can identify control image
* -t: Control node image name. Image name which you can use to identify your control image
* -m: Compute node bucket name. Bucket name which you can identify your compute image
* -e: compute node image name. Image name which you can use to identify your compute image
* -a: Virtual cluster name

For example:

    $ fg-cluster -f futuregrid.cfg checkpoint -c myname -t c1.img -m myname -e c2.img -a mycluster1
    
If you successfully upload your control image and compute image, you
can find them in openstack image repository according to the bucker
name and image name you give to them by command:

    $ euca-describe-images


Note: Cluster name should be a name of cluster which is
currently running. Generated image ids (including one control 
node image id and one compute image id) will be registered which
are used for later restore.


Restore a virtual cluster
--------------------------

Run following command will restore a virtual cluster state including
installed softwares, unfinished jobs which was saved before, so that
you can continue your work from that saved point.

    $ fg-cluster -f <config-file> restore -a <cluster-name>

Parameters;

* -a: Cluster name. The virtual cluster name which uniquely identifies your cluster.

For example:

    $ fg-cluster -f futuregrid.cfg restore -a mycluster2

Note: Cluster name should be the name of cluster which had been saved
before.  You can check the images you saved, the images you saved will 
have the bucket name and image name you specified from checkpoint command, 
and which can be shown by following command:

    $ euca-describe-images


Shutdown a virtual cluster
---------------------------

Run following command will terminate a virtual cluster

    $ fg-cluster -f <config-file> terminate -a <cluster-name>

Parameters:

* -f: Futuregrid configuration file
* -a: Virtual cluster name

For example:

    $ fg-cluster -f futuregrid.cfg terminate -a mycluster2

Note: Cluster name should be a name of cluster which is currently
running. After executing this command, cluster info will be removed
from backup file which is specified by configuration file


Show status of virtual cluster(s)
---------------------------

Run following command will show status of currently running 
virtual cluster(s) including cluster size, image id, instance id, ip

    $ fg-cluster -f <config-file> status -a <cluster-name>

Parameters:

* -f: Futuregrid configuration file
* -a: Virtual cluster name


For example: 

Show status of one specific cluster given cluster name

    * fg-cluster -f futuregrid.cfg status -a mycluster1

Show status of all currently running clusters

    fg-cluster -f futuregrid.cfg status

Note: If argument -a is specified, then name of cluster should be 
a cluster that is currently running


List the virtual clusters
----------------------------

Run following command will give you a list of virtual clusters and their status

    $ fg-cluster -f <config-file> list
    
For example:

    $ fg-cluster -f futuregrid.cfg list


Run a simple MPI program on virtual cluster
===========================================

A simple MPI version of helloworld can be found at: 

* https://github.com/futuregrid/virtual-cluster/blob/master/etc/helloworld.c

You may use this for test purpose.

We assume that you are using helloworld.c from above link. So in order to run this MPI program 
on the cluster you created using SLURM system, you can

### Step 1: Copy helloworld.c to HOME directory on each node in virtual cluster

    $ scp -i <your-userkey-pem-file> helloworld.c ubuntu@<instance-ip>:~/

### Step 2: Login to instances, complie helloworld.c on each node, run:

    $ ssh -i <your-userkey-pem-file> ubuntu@<instance-ip>
    $ mpicc hellowrld.c -o helloworld 

### Step 3: Login to control node, run:

    $ ssh -i <yout-userkey-pem-file> ubuntu@<control-node-ip>
    $ salloc -N 2 mpirun helloworld

where -N is the number of computation nodes you want to run with. And 
should not be larger than the actual number of computation nodes

Execution result:

    Running program helloworld
    salloc: Granted job allocation 2
    Hello world from processor i-000023c8, rank 0 out of 2 processors
    Hello world from processor i-000023c9, rank 1 out of 2 processors
    salloc: Relinquishing job allocation 2

    
Using FGClusterRunprogram
---------------------------

A program which could help you to run a simple MPI program can be found at 

* https://github.com/futuregrid/virtual-cluster/blob/master/etc/FGClusterRunprogram.py

So you can simply run command:

    # python FGClusterRunprogram.py -f futuregrid.cfg -p helloworld.c -n 2 -a mycluster1

Parameters:

* -f: Futuregrid configuration file
* -p: Program source code file
* -n: Number of computaion nodes you want to run with. Make sure that the number you input is no larger 
than the acutal number of computaion node you created.
* -a: Name of virtual cluster you want to run program on


Note: Virtual cluster name should be a name of cluster which is
currently running


FOR DEVELOPERS ONLY
===================

Generating the Distribution
---------------------------

Assume that you have git correctly installed and configured on your
computer.

### Step 1: You can pull source code from github by:

    git clone git@github.com:futuregrid/virtual-cluster.git

### Step 2: Create tar file for installation

    make pip
    
This creates the tar file that you can install via pip in ./dist

### Step 3: Install

    sudo pip install --upgrade dist/*.tar.gz

This wil install the files by default into /usr/local/bin/fg-cluster  