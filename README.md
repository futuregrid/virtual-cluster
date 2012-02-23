please put your readm here
python 2.7

argparse not optparse

simple io management.

rimple parsing, e.g. replace awk, print sed with python parsing function.

make sure you define function or classes.

we want to share them ;-)

HOW TO RUN
==========

Create virtual cluster
./fg-create-cluster.py -u userkey -n number of computation nodes -s instance type -i image type -a cluster name

Save virtual cluster
./fg-cluster-checkpoint.py -u userkey -n openstack key zip -c control node bucket -t control node name -m compute bucket -e compute name

Restore virtual cluster
./fg-cluster-restore.py -u userkey -n number of computation nodes -i control node image id -c compute node image id -s type of instance -a name of cluster

Shutdown virtual cluster
./fg-cluster-shutdown.py -a cluster name



We are developing

fg-cluster -create name number of nodes image
...


fg-cluster name "number of node" image
   does all of the abaove and returns you a working cluster




fg-cluster -service MPI




