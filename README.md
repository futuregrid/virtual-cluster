
HOW TO RUN
==========

<p><>Create virtual cluster</p>
<pre><code>./fg-create-cluster.py -u userkey -n number_of_computation_nodes -s instance_type -i image_id -a cluster_name</code></pre>
<p>This command will return a virtual cluster with SLURM and OpenMPI installed.</p> 
<p>Note: Default image type is "m1.small". Cluster name should be different as other virtual clusters that had been created.</p> 

<P>Save virtual cluster</p>
<pre><code>./fg-cluster-checkpoint.py -u userkey -n openstack_key_zip -c control_node_bucket -t control_node_name -m compute_bucket -e compute_name -a cluster_name</code></pre>
<p>This command will save current running virtual cluster into one control image and one compute image, which could be later used for resotring.</p>
<p>Note: Cluster name should be a name of cluster which is currently running. Openstack_key_zip file is a zip file that contains cacert.pem, cert.pem, pk.pem, novarc</p>

<p>Restore virtual cluster</p>
<pre><code>./fg-cluster-restore.py -u userkey -n number_of_computation_nodes -i control_node_image_id -c compute_node_image_id -s instance_type -a cluster_name</code></pre>
<p>This command will create a virtual cluster out of saved control node and compute node with given compute node number</p>
<p>Note: Cluster name should be different as the names of currently running virtual clusters</p>

<p>Shutdown virtual cluster</p>
<pre><code>./fg-cluster-shutdown.py -a cluster_name</code></pre>
<p>This command shutdown a running virtual cluster</p>
<p>Note: Cluster name should be a name of cluster which is currently running.</p>

<p>Run simple MPI program on virtual cluster</p>
<pre><code>./fg-cluster-run-program.py -u userkey -n number_of_compute_node -f program_source_file -a cluster_name</code></pre>
<p>This command will run a MPI program on a given virtual cluster</p>
<p>Note: argument number of compute node should not be more than actual numbe of compute node in virtual cluster</p> 



We are developing

fg-cluster -create name number of nodes image
...


fg-cluster name "number of node" image
   does all of the abaove and returns you a working cluster


fg-cluster -service MPI




