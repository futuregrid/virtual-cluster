please put your readm here
python 2.7

argparse not optparse

simple io management.

rimple parsing, e.g. replace awk, print sed with python parsing function.

make sure you define function or classes.

we want to share them ;-)

HOW TO RUN
==========

./fg-create-cluster.sh xiuwen 1 ami-00000019

wait some 30 seconds

./deploy-slurm.sh xiuwen 1

./fg-cluster-checkpoint.sh

./fg-cluster-shutdown.sh



We are developing

fg-cluster -create name number of nodes image
...


fg-cluster name "number of node" image
   does all of the abaove and returns you a working cluster




fg-cluster -service MPI




