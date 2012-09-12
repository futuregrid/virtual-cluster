INTRODUCTION
============

System requirements
------------------

* euca2ools: verison 2.0.2
* python: version 2.7
* virtualenv (optional, if you do not have sudo rights)

Code Repository
---------------

Our code and web page is maintained in github

* Source: https://github.com/futuregrid/virtual-cluster
* Documentation: http://futuregrid.github.com/virtual-cluster

Introduction
------------

Project futuregrid.virtual.cluster is a virtual cluster management
software utilizing OpenStack and Eucalyptus resources on FutureGrid. 
The software contains several parts that could help users easily 
manage their operations to virtual clusters on FutureGrid.

Managment operations include: 

* Create virtual cluster(s)
* Save currently running virtual cluster(s)
* Restore saved virtual cluster(s) 
* Show status of virtual cluster(s) 
* List brief information of all created clusters
* Terminate virtual cluster(s)
* Run a simple MPI program


HOW TO INSTALL
==============

First Setup
------------

We assume that yo do not have super user priviledges on the computer
where you like to install our tool.

* **Step 0: Prerequisites (not using india.futuregrid.org machines):**
    
  In order to make the installation process work smoothly, please make 
  sure that the computer you like to install our tool has already
  installed euca2ools (version 2.0.2) and Python (version 2.7). If you do
  not have those tools or correct version installed. you may install 
  euca2ools (version 2.0.2) from 
  
  * http://www.eucalyptus.com/download/euca2ools

  and install python (version 2.7) from 

  * http://python.org

  After you check all the tools with version are correctly installed,
  you may proceed with following steps to start installation.


* **Step 1: Prerequisites (using india.futuregrid.org machines):**
	
	india.futuregrid.org has installed every tools you may need to finish this
	installation, so to activate euca2ools (version 2.0.2) after you login into
	india futuregrid machines, just simply do::
    
		$ module load euca2ools
    
	To activate python 2.7, simply do::

		$ module load python
		
	Those commands will help you load tools with correct version you need
	to finish installation. So now you may proceed with following
	installation steps.

* **Step 2: Download virtualenv**
	
	Since you do not have super user priviledges, you need virtualenv in
	order to finish the installtion. You may download virtualenv.py by
	following command::

	    $ wget https://raw.github.com/pypa/virtualenv/master/virtualenv.py
 
* **Step 3: Install virtualenv**
	
	After you downloaded virtualenv, you can install it by following
	command::

	    $ python virtualenv.py --system-site-packages ENV
	  
* **Step 4: Activate virtualenv**

	After installation of virtualenv, you can activate virtualenv by
	following command::

	    $ source ENV/bin/activate
    
* **Step 5: install the virtual cluster with pip**

	Once virtualenv is activated, you can use pip to install our tool by
	following command::

	    $ ENV/bin/pip install futuregrid.virtual.cluster

	If you already had our tool installed, and you want to upgrade to
	newest version, you can do it by following command::

		$ ENV/bin/pip install --upgrade futuregrid.virtual.cluster
	
	.. note: For more information about virtualenv, you may see documentation of virtualenv at
	
		* http://www.virtualenv.org/en/latest/index.html

Repeated Use
------------

We assume that you are using the same machine as the first time you ran our tool.

* **Step 1: Environment Setup (using india.futuregrid.org machines):**
	
	india.futuregrid.org has installed every tools you may need to finish this
	installation, so to activate euca2ools (version 2.0.2) after you login into
	india futuregrid machines, just simply do::
    
		$ module load euca2ools
    
	To activate python 2.7, simply do::

		$ module load python
		
	Those commands will help you load tools with correct version you need
	to finish installation. So now you may proceed with following
	installation steps.

* **Step 2: Activate virtualenv**

	You can activate virtualenv again by following command::

	    $ source ENV/bin/activate

Now you can use our tool to manage your virtual clusters.

FutureGrid Specific Installation
-------------------------------

Install without admin rights on india futuregrid
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
ahead and use FutureGrid.

Our virtual cluster is best executed on our machine called
india.futuregrid.org

Please log into this machine and follow the steps that we have outlined
in the previous section to install the software and then run it while
following the instaructions from the next section


HOW TO RUN
==========

Prerequisites
-------------

In order to use our tool, you need to obatin nova, eucalyptus 
credentials and configuration files for FutureGrid system. These
should have been placed in your home directory on the INDIA
system. If you do not have a portal and HPC account please create one.  
The credential zip file contains the rc file. Unzip this file in your 
home directory. The novarc (OpenStack) and eucarc (Eucalyptus) file contains 
the necessary environment variables.

Create your private key by (Recommended: Use your user name as your
private key name)::

    $ euca-add-keypair youruserkey > youruserkey.pem
    $ chmod 0600 youruserkey.pem

You can also use our tool to create a userkey for you, but you need 
to specify the userkey name in configuration file which is listed 
below. The key can be created if you use --create-key argument before 
any subcommands when you first run our tool. For more help see also::

    $ fg-cluster --help
    
However, this documentation is much more comprehensive than the help message.

NOTE: For more information about credentials, you can refer 
to tutorial at:: 

* https://portal.futuregrid.org/tutorials/openstack

and::

* https://portal.futuregrid.org/using-eucalyptus-futuregrid


Create configuration file
-------------------------

You need to create a configuration file which needs to be passed to
this tool for locating necessary files in order to run. You can create
configuration file using text editor, or using an example we provide
to you

* https://raw.github.com/futuregrid/virtual-cluster/master/etc/futuregrid.cfg

It has the following format::

    [virtual-cluster]                         
    # Backup file for saving and loading virtual cluster(s)  
    backup = ~/.futuregrid/virtual-cluster
    # Slurm configuration input file
    slurm = ~/.futuregrid/slurm.conf.in
    # userkey pem file
    userkey = ~/PUT-YOUR-USER-NAME-HERE.pem
    # environment file
    enrc = ~/novarc
    # program interface
    interface = euca2ools
    # cloud to use
    cloud = nova

You will have to modify the <PUT-YOUR-USER-NAME-HERE> occurrence
within the file with the name that you use to associate your key. The
file is to be placed at ~/.futuregrid/futuregrid.cfg or concatenated
to an already existing futuregrid.cfg file. In order to use different 
interface (euca2ools/boto) or cloud to run this tool, you can change
interface or cloud parameter in the configuration file to achieve that.

If you want to use a different configuration file instead of changing 
one configuration file back and forth, you can use argument --file 
before you specify each subcommand you would like to run.::

    $ fg-cluster --file <configuration-file> <subcommands>

NOTE: Please make sure all the files are placed under the location as
you specified in configuration file. You can also find an example of
slurm.conf.in file which is used by configuring SLURM system from

*  https://raw.github.com/futuregrid/virtual-cluster/master/etc/slurm.conf.in

You can modify SLURM configuration parameters for your customized
SLURM. But please leave "controlMachine", "ControlAddr" and "COMPUTE NODES"
untouched.

In the configuration file, you can choose different interface for this tool to use 
(euca2ool or boto), just need to change interface parameter in the configuration file. 
You also need to change enrc and cloud parameters in order to switch between different 
clouds (nova/eucalyptus).

After you finished all steps above, you can use our tool to manage
your virtual clusters

* **OpenStack configuration example:**

To correctly configure the tool to use OpenStack resources, you can refer to example::

    [virtual-cluster]                         
    # Backup file for saving and loading virtual cluster(s)  
    backup = ~/.futuregrid/virtual-cluster
    # Slurm configuration input file
    slurm = ~/.futuregrid/slurm.conf.in
    # userkey pem file
    userkey = ~/PUT-YOUR-USER-NAME-HERE.pem
    # environment file
    enrc = ~/novarc
    # program interface
    interface = euca2ools
    # cloud to use
    cloud = nova
    
* **Eucalyptus configuration example:**

To correctly configure the tool to use Eucalyptus resources, you can refer to example::

    [virtual-cluster]                         
    # Backup file for saving and loading virtual cluster(s)  
    backup = ~/.futuregrid/virtual-cluster
    # Slurm configuration input file
    slurm = ~/.futuregrid/slurm.conf.in
    # userkey pem file
    userkey = ~/PUT-YOUR-USER-NAME-HERE.pem
    # environment file
    enrc = ~/eucarc
    # program interface
    interface = euca2ools
    # cloud to use
    cloud = eucalyptus
    

Create a virtual cluster
-------------------------

Run following command will create a virtual cluster of given
parameters (command example is given below)::

    $ fg-cluster run -n <number-of-computation-nodes> -t <instance-type> -i <image-id> -a <cluster-name>

Parameters:

	-n 	Number of computation nodes. 
	-t 	Instance type. 
		Instance type includes: m1.tiny, m1.small and m1.large.
	-i 	Image id. You can obtain image with a commandline tool such as ``euca-describe-images``.
	-a 	Cluster name. 
		The virtual cluster name which uniquely identifies your cluster.

Please note that the number of computation nodes does not include the control node, so the actual number for virtual cluster.
nodes is the number of computations node plus one control node.


For example::

    $ fg-cluster run -n 2 -t m1.small -i ami-0000001d -a mycluster1

Virtual cluster info will be saved in backup file specified in
futuregrid configuration file. Note: Cluster name should be different
as other virtual clusters which is running if you want to run multiple
virtual clusters. 


Save a virtual cluster
-----------------------

Run following command will save a currently running virtual cluster into one
control image and compute image for later resotre. (Installed softwares and 
unfinished jobs will also be saved)::

    $ fg-cluster checkpoint -c <control-node-bucket> -t <control-node-name> -m <compute-bucket> -e  <compute-name> -a <cluster-name> -s <image-size>

Parameters:

  -c  	Control node bucket name. Bucket name which you can identify control image
  -t  	Control node image name. Image name which you can use to identify your control image
  -m  	Compute node bucket name. Bucket name which you can identify your compute image
  -e  	Compute node image name. Image name which you can use to identify your compute image
  -a  	Virtual cluster name
  -s    Image size, in MB

For example::

    $ fg-cluster checkpoint -c myname -t c1.img -m myname -e c2.img -a mycluster1 -s 1024
    
If you successfully upload your control image and compute image, you
can find them by command::

    $ euca-describe-images


Note: Cluster name should be a name of cluster which is
currently running. Generated image ids (including one control 
node image id and one compute image id) will be registered which
are used for later restore. Please CHECK avaliable space on instances
before you save cluster, image size should be smaller than the avaliable 
space on each instance of the virtual cluster you want to save.


Restore a virtual cluster
--------------------------

Run following command will restore a virtual cluster state including
installed softwares, unfinished jobs which was saved before, so that
you can continue your work from that saved point::

    $ fg-cluster restore -a <cluster-name>

Parameters:

  -a 	Cluster name. The virtual cluster name which uniquely identifies your cluster.

For example::

    $ fg-cluster restore -a mycluster2

Note: Cluster name should be the name of cluster which had been saved
before.  You can check the images you saved, the images you saved will 
have the bucket name and image name you specified from checkpoint command, 
and which can be shown by following command::

    $ euca-describe-images


Shutdown a virtual cluster
---------------------------

Run following command will terminate a virtual cluster::

    $ fg-cluster terminate -a <cluster-name>

Parameters:

  -a 	Virtual cluster name

For example::

    $ fg-cluster terminate -a mycluster2

Note: Cluster name should be a name of cluster which is currently
running.


Show status of virtual cluster(s)
---------------------------

Run following command will show status of currently running 
virtual cluster(s) including cluster size, image id, instance id, IP addresses::

    $ fg-cluster status -a <cluster-name>

Parameters:

  -a  	Virtual cluster name


For example: 

Show status of one specific cluster given cluster name::

    fg-cluster status -a mycluster1

Show status of all currently running clusters::

    fg-cluster status

Note: If argument -a is specified, then the cluster you want to show status should be 
a cluster that is currently running. If argument -a is not specified, the tool will 
show the status of all virtual clusters.


List the virtual clusters
----------------------------

Run following command will give you a list of virtual clusters and their status::

    $ fg-cluster list
    
For example::

    $ fg-cluster list


RUN SIMPLE MPI PROGRAMS UNDER SLURM
===========================================

A simple MPI version of helloworld can be found at: 

* https://raw.github.com/futuregrid/virtual-cluster/master/etc/helloworld.c

You may use this for test purpose.

We assume that you are using helloworld.c from above link. So in order to run this MPI program 
on the cluster you created using SLURM system, you can conduct the following steps.

* **Step 1: Copy helloworld.c to HOME directory on each node in virtual cluster**

	::

	    $ scp -i <your-userkey-pem-file> helloworld.c ubuntu@<instance-ip>:~/

* **Step 2: Login to instances, complie helloworld.c on each node, run**

	::
	
	    $ ssh -i <your-userkey-pem-file> ubuntu@<instance-ip>
	    $ mpicc hellowrld.c -o helloworld 

* **Step 3: run MPI program, you need to login into control node**

	Option 1: Using salloc command::
	
	    $ salloc -N 2 mpirun helloworld

	where -N is the number of computation nodes you want to run with. And 
	should not be larger than the actual number of computation nodes

	Option 2: Using sbatch command by submitting a job script::

	    $ sbatch helloworld.sh

	You can find example helloworld.sh at

	* https://github.com/futuregrid/virtual-cluster/blob/master/etc/helloworld.sh

	
	Execution result::

	    Running program helloworld
	    salloc: Granted job allocation 2
	    Hello world from processor i-000023c8, rank 0 out of 2 processors
	    Hello world from processor i-000023c9, rank 1 out of 2 processors
	    salloc: Relinquishing job allocation 2
    
Using fg-cluster tool
---------------------------

A much simpler way to run a MPI program is to use our tool

You can choose different ways to run your MPI program, one way is to 
use salloc command in SLURM and another way is to use sbatch command. 
And you can also use our tool to achieve this.

If you want to directly run MPI program using salloc, you can simply run command::

    # fg-cluster mpirun -p <program-source-file> -n <compute-nodes-to-use> -a <cluster-name>

For example::

    # fg-cluster mpirun -p helloworld.c -n 2 -a mycluster1

If you want to submit a job script to the SLURM, you can simply run command::

    # fg-cluster mpirun -p <program-source-file> -n <compute-nodes-to-use> -a <cluster-name> -s <script-name>

For example::

    # fg-cluster mpirun -p helloworld.c -n 2 -a mycluster1 -s helloworld.sh

Parameters

  -p 	Program source code file
  -n 	Number of computaion nodes you want to run with. 
  -a 	Name of virtual cluster you want to run program on
  -s    Job script you would like to submit to SLURM

Make sure that the number you input is no larger than the acutal number of computaion node you created. 
The virtual cluster name should be a name of cluster which is currently running.

PERFORMANCE TEST
================

You can use our tool to run performance test on OpenStack and Eucalyptus.

Prerequisites
-------------

In order to use our tool to run performance test on Openstack and Eucalyptus. You must have
our tool correctly installed. You can refer to the tutorial about how to run in the pervious
sections. Once you can successfully run our tool, you can proceed with the following steps.

How to run
----------

Followings are steps you need to follow in order to successfully run performance test using our tool

* **Step 1: Download our peroformance test tool**
	
	You can download the performan test tool from

	* https://raw.github.com/futuregrid/virtual-cluster/master/performance/Performance_Testall.py

	Performance_Testall.py is the test script that you can use to run the performance test. 

	* https://raw.github.com/futuregrid/virtual-cluster/master/performance/Performance_Statistic.py

	Performance_Statistic is the data process program which could prodeuce excel sheets on data you collected

	* https://raw.github.com/futuregrid/virtual-cluster/master/performance/Performance_Plot.py

	Performance_Plot is the graph produce program which could prodeuce graphs for each cloud you tested

	* https://raw.github.com/futuregrid/virtual-cluster/master/performance/Performance_Comp.py

	Performance_Comp is the comparison graph produce program which could produce comparison graphs 
	between clouds you tested on

	Also, you can download our source code from github, and then you can find performance tool under 
	virtual-cluster/performance folder.

	NOTE: When you switch performance test between OpenStack and Eucalyptus, please make sure that you have
	futuregrid.cfg file correctly configuared. See below section about switching between clouds.

* **Step 2: Run performance test script**

	Beaucase each test involves running a MPI program, so please download our sample MPI helloworld from

	* https://raw.github.com/futuregrid/virtual-cluster/master/etc/helloworld.c

	and put it where you would like you run the test script.

	If you have done all the steps above, then you can run the test scripte by::

	$ python Performance_Testall.py -o <output-file> -i <image-id>

	This will run tests which involve creating different virtual clusters with various parameters, 
	running MPI program and terminating virtual clusters, then produces output file which contains
	all the performance test result data you collected.

	When you finish performance test, you will get result like following::

		Test Name           	Total Time     	Installation   	Configuration  	Execution      	Termination    	IP association 	IP association fail 	IP change 	Restart
		euca-m1.small-1     	115.702837944  	96.9913449287  	6.05437302589  	0.58861207962  	0.159124135971 	N/A            	N/A                 	N/A       	N/A
		euca-m1.small-1     	111.77609396   	92.9926450253  	6.03100919724  	0.55158996582  	0.157529830933 	N/A            	N/A                 	N/A       	N/A
		euca-m1.small-1     	110.741933107  	92.9937160015  	5.04305911064  	0.598108053207 	0.16206908226  	N/A            	N/A                 	N/A       	N/A 
		nova-m1.small-1     	151.426457167  	134.004024982  	2.22711896896  	0.196369886398 	1.20041799545  	4.12035417557  	0                   	0         	0         
		nova-m1.small-1     	163.470904827  	146.006072998  	2.24714803696  	0.179543972015 	1.0476629734   	4.10231184959  	0                   	0         	0         
		nova-m1.small-1     	153.810782194  	136.004303932  	2.69106817245  	0.219621181488 	1.00952887535  	4.1146697998   	0                   	0         	0

	NOTE: The script will create clusters with size 1, 2, 4, 8, 16, 24, 32; with instance type small, 
	medium, large

* **Step 3: Process performance test data**

	Once you have done the performance test and outpus the raw data file. You can create excel sheets 
	or graphs using	our tool.

	However, before you can proceed, you need to install numpy and matplotlib which are required by the tool::

	$ pip install numpy
	$ pip install matplotlib

	Then, you can creats excel sheets by the following command::

	$ python Performance_Statistic.py -f <your-performance-test-result-file>

	This will create two excels for you which you can view via excel. One is for OpenStack data, 
	and the other one is for Eucalyptus data. 

	The file has the following format (in plain text)::

		name,t_total_avg,t_total_min,t_total_max,t_total_stdev,t_setup_install_avg,t_setup_install_min,t_setup_install_max,t_setup_install_stdev,t_setup_configure_avg,t_setup_configure_min,t_setup_configure_max,t_setup_configure_stdev,t_execute_avg,t_execute_min,t_execute_max,t_execute_stdev,t_shutdown_avg,t_shutdown_min,t_shutdown_max,t_shutdown_stdev
		euca-m1.small-2,139.072920442,113.236577034,164.909263849,25.8363434075,114.992971659,85.9957351685,143.990208149,28.9972364903,6.78620207309,6.69066214561,6.88174200058,0.095539927485,0.642117619514,0.613047122955,0.671188116074,0.0290704965595,0.256532430649,0.254338026047,0.258726835251,0.002194404602
		euca-m1.small-1,112.740288337,110.741933107,115.702837944,2.13696003674,94.3259019852,92.9926450253,96.9913449287,1.88475283095,5.70948044459,5.04305911064,6.05437302589,0.471327566829,0.579436699549,0.55158996582,0.598108053207,0.0200686125267,0.159574349721,0.157529830933,0.16206908226,0.00188028720646

	You can also create graphs for each cloud by the following command::

	$ python Performance_Plot.py -f <your-performance-test-result-file>

	and create comparison graphs by::

	$ python Performance_Comp.py -ie <your-performance-test-result-about-eucalyptus-on-india> -se <your-performance-test-result-about-eucalyptus-on-sierra> -in <your-performance-test-result-about-openstack-on-india>

Switch between OpenStack and Eucalyptus
---------------------------------------

If you want to use our tool to do performance test on OpenStack and Eucalyptus, you can switch between 
clouds just by changing futuregrid.cfg configuration file. You can refer to the configuration file section 
to change your configuration file accodringly.

Before you run a test script, you need to choose to a proper image (ubuntu) before each run (You can use euca2ools 
to test the image before you run our script). To avoid output files overwritten, please use different file names, 
and later you can use these performance output files to produce nice graphs.

FOR DEVELOPERS ONLY
===================

Generating the Distribution
---------------------------

Assume that you have git correctly installed, configured on your
computer. And you also added your ssh public key on github. So you
can proceed with step 1.

If you use machines on indiana futuregrid, you can load git by

	::

	    module load git

And added ssh public key on github.

* **Step 1: You can pull source code from github by**

	::

	    git clone git@github.com:futuregrid/virtual-cluster.git

* **Step 2: Create tar file for installation**

	::
	
	    make pip
    
	This creates the tar file that you can install via pip in ./dist

* **Step 3: Install**

	::
	
	    sudo pip install --upgrade dist/*.tar.gz

	This wil install the files by default into /usr/local/bin/fg-cluster  