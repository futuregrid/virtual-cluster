HOW TO RUN
==========

Create virtual cluster
----------------------

>>>> ./fg-create-cluster.py -u userkey -n number_of_computation_nodes -s instance_type -i image_id -a cluster_name

This command will return a virtual cluster with SLURM and OpenMPI
installed.  Note: Default image type is "m1.small". Cluster name
should be different as other virtual clusters that had been created.

Save virtual cluster
--------------------

>>>>./fg-cluster-checkpoint.py -u userkey -n openstack_key_zip -c control_node_bucket -t control_node_name -m compute_bucket -e compute_name -a cluster_name

This command will save current running virtual cluster into one
control image and one compute image, which could be later used for
resotring.  Note: Cluster name should be a name of cluster which is
currently running. Openstack_key_zip file is a zip file that contains
cacert.pem, cert.pem, pk.pem, novarc

Restore virtual cluster
-----------------------

>>>>./fg-cluster-restore.py -u userkey -n number_of_computation_nodes -i control_node_image_id -c compute_node_image_id -s instance_type -a cluster_name

This command will create a virtual cluster out of saved control node
and compute node with given compute node number Note: Cluster name
should be different as the names of currently running virtual clusters

Shutdown virtual cluster
------------------------

>>>>./fg-cluster-shutdown.py -a cluster_name

This command shutdown a running virtual cluster 

Note: Cluster name should be a name of cluster which is currently
running.

Run simple MPI program on virtual cluster
-----------------------------------------

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




