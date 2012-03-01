HOW TO RUN
==========

Create a virtual cluster
-------------------------

>>>>python fg-cluster.py -f config_file run -n number_of_computation_nodes -s instance_type -i image_id -a cluster_name

This command will return a virtual cluster with SLURM and OpenMPI
installed.  Note: Cluster nameshould be different as other virtual 
clusters that had been created. If want to use default configure file,
config file should be created as ~/.ssh/futuregrid.cfg, then argument -f
can be omitted

Save a virtual cluster
-----------------------

>>>>python fg-cluster.py -f config_file checkpoint -c control_node_bucket -t control_node_name -m compute_bucket -e compute_name -a cluster_name

This command will save current running virtual cluster into one
control image and one compute image, which could be later used for
resotring.  Note: Cluster name should be a name of cluster which is
currently running.

Restore a virtual cluster
--------------------------

>>>>python fg-cluster.py -f config_file restore -n number_of_computation_nodes -c control_node_image_id -m compute_node_image_id -s instance_type -a cluster_name

This command will create a virtual cluster out of saved control node
and compute node with given compute node number Note: Cluster name
should be different as the names of currently running virtual clusters

Shutdown a virtual cluster
---------------------------

>>>>python fg-cluster.py -f config_file shutdown -a cluster_name

This command shutdown a running virtual cluster 

Note: Cluster name should be a name of cluster which is currently
running.

Show status of virtual cluster(s)
---------------------------

>>>>python fg-cluster.py -f config_file status -a cluster_name

This command shows status of virtual cluster(s)
Note: If argument -a is specified, this command
will return status of all virtual clusters, otherwise,
it will show status of virtual cluster of given name

Run a simple MPI program on virtual cluster
--------------------------------------------

>>>>./fg-cluster-run-program.py -u userkey -n number_of_compute_node -f program_source_file -a cluster_name

This command will run a MPI program on a given virtual cluster

Note: argument number of compute node should not be more than actual
numbe of compute node in virtual cluster



We are developing
-----------------
fg-cluster -create name number of nodes image
...


fg-cluster name "number of node" image
   does all of the abaove and returns you a working cluster


fg-cluster -service MPI




