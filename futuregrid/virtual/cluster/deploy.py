#! /usr/bin/env python

# TODO: gvl: maybe we want to rename to "fg-create-virtual-cluster.py ?
# TODO: gvl: maybe we want to add this to the console sript in setup.py

import argparse
from time import sleep

from StringIO import StringIO

from cloud import Cloud

from fabric.api import *
from fabric.tasks import execute
from fabric.operations import put


class FgCreate:

    def __init__(self, args):
        self.args = args
        self.cloud = Cloud()

    def _assign_public_ips(self, instance_ids):
        print("Assigning public IP addresses...")
        ip_dict = {}
        for instance_id in instance_ids:
            successful = self.cloud.assign_public_ip(instance_id)
            # Issues with Nova and assigning IPs too quickly,
            # so we're going to sleep.
            sleep(2)

    def _get_public_ips(self, instance_ids):
        public_ips = []
        for instance_id in instance_ids:
            reservation = self.cloud.describe_instance(instance_id)
            instance = reservation.instances[0]
            if (reservation is not None) else None
            if instance:
                public_ips.append(instance.public_dns_name)
        return public_ips

    def _wait_for_running_instances(self, instance_ids):
        print("Waiting for running instances...")
        running_status = "running"
        deleted_status = "deleted"

        running_ids = []
        while len(instance_ids) > 0:
            pending_ids = []

            for instance_id in instance_ids:
                reservation = self.cloud.describe_instance(instance_id)
                instance = reservation.instances[0]
                if (reservation is not None) else None
                status = instance.state
                if (instance is not None) else deleted_status

                if status == running_status:
                    running_ids.append(instance_id)
                elif status == deleted_status:
                    print("{0} has status of {1}"
                          .format(instance_id, deleted_status))
                else:
                    pending_ids.append(instance_id)

            # Reset the instance_ids to the remaining pending_ids.
            instance_ids = pending_ids
            if len(instance_ids) > 0:
                sleep(5)

        return running_ids

    def test_fabric(self, hosts):
        env.key_filename = self.args.key_file
        env.user = self.args.ssh_user
        env.parallel = True
        env.pool_size = 10
        env.connection_attempts = 3
        #TODO:
        # gvl: maybe we want to be able to give the connection time out
        #     as an argv to this prg
        #     Same with poolsize.
        #     However we make them optional and have these as default values
        env.timeout = 10

        print(hosts)
        hello_world_file = StringIO("""hello world""")
        execute(lambda: put(hello_world_file, "hello_world.txt"), hosts=hosts)
        execute(lambda: run("cat hello_world.txt"), hosts=hosts)
        execute(lambda: run("hostname"), hosts=hosts)

    def create_cluster(self):
        print("""
Creating virtual cluster......
name            -- {0}
number of nodes -- {1}
instance type   -- {2}
image id        -- {3}
""".format(self.args.name,
           self.args.number,
           self.args.instance_type,
           self.args.image_id))

        count = self.args.number + 1

        kwargs = {}
        kwargs["key_name"] = self.args.keypair
        kwargs["count"] = count
        kwargs["image_id"] = self.args.image_id
        # TODO: A security group should be used other than the default.
        kwargs["security_groups"] = ["default"]
        kwargs["instance_type"] = self.args.instance_type

        reservation = self.cloud.run_instances(**kwargs)
        instance_ids = [instance.id for instance in reservation.instances]
        running_ids = self._wait_for_running_instances(instance_ids)
        # Create a dict of {'instance_id': 'public_ip'} values
        self._assign_public_ips(running_ids)
        public_ips = self._get_public_ips(running_ids)
        self.test_fabric(public_ips)


def main():

    parser = argparse.ArgumentParser(
                                     description='Create a virtual cluster'
                                ' in FutureGrid.')
    parser.add_argument('-k', '--keypair', dest='keypair')
    parser.add_argument('-f', '--key-file', dest='key_file')
    parser.add_argument('-n', '--number', dest='number', type=int)
    parser.add_argument('-t', '--instance-type', dest='instance_type',
                        default='m1.small')
    parser.add_argument('-i', '--image-id', dest='image_id')
    parser.add_argument('-a', '--name', dest='name')
    parser.add_argument('-u', '--ssh-user', dest='ssh_user', default='root')

    args = parser.parse_args()

    fgc = FgCreate(args)
    fgc.create_cluster()
    #
    # not yet sure if the following is part of this command or part of
    # another command that puts services ino the running images as Jon
    # indicated. I think it makes sense to put it in here
    #
    # TODO: gvl: add a flag --services so we can pass a number of
    # predefined services to this command. We may want more than to
    # deploy slurm. services are simply a list. We want to handle each
    # service in a separate .py file and be able to register them wih
    # this command in some fashion. This way we can write the code
    # modular and expand easily while having one called service-mpi.py
    # service-slurm.py ... and so forth.Here the pseudo code

    # for service in a futuregrid.cluster.services
    #    register service with this command:
    #       adds a new argument to the commandline
    #       puts in a list the service so when its passed as
    #       argument we can call it.
    #

    # I realize that not everyone knows chef, so we may want to
    # consider services that are included via chef, while others could
    # use an apt-get method ... We need o discuss this in more detail
    # ...
    #
    # --services slurm mpi chef
    #
    #      slurm - will install slurm on one of the nodes and the rest
    #              become worker nodes. Jobs can be submtted from the
    #              master node to the workers via slurm commands
    #
    #      mpi - a MPI library is installed on all nodes. If slurm is
    #            one of the services only the worker nodes are
    #            typically involved in execution of the mpi
    #            program. This has to be worked out in a bt more
    #            detail if we want mpi with and without slurm. I think
    #            it does make sense to have both options.
    #
    #      chef - This is an instalation of chef in the server all
    #             other nodes are configured in such a way that they
    #             register as nodes to chef running on the
    #             master. This allows for an ideal test environment to
    #             try out chef and build new recipies.
    #
    #      others - other services I could think about are hadoop,
    #               twister, maui/torque, oracle grid engine, mysql,
    #               mongodb, drupal, wordpress, ...  I included the
    #               later to have something that classes may be
    #               interested in that not specialize in the
    #               development of parallel computing code
    #
    # --services
    #
    #      services without any additional parameters lists simply all
    #      services available the user could call.
    #
    # --chef arguments
    #
    #      besides the services parameters we have an alternative way
    #      to specify roles for the machnes. This is simply a list in
    #      which we specify a range of nodes that is associated with a
    #      role. This is for advanced users wanting to benefit from
    #      the chef repositories
    #
    #      Example: install chef_server on node 0, install
    #      slurm_master on node 0, install slurm_worker on teh rest of
    #      the nodes
    #
    #       --chef config="[0]=(slurm_master, chef_server) [1:]=(slurm_worker)"
    #
    #      in addition a chef repository can be specified while adding
    #      somewhere in the chef parameter the string
    #
    #          repo=<link to the chef repo>
    #
    # --ttl 15d
    #
    #      A time to live parameter is optionally passed along
    #      specifying the duration for how long this service is up and
    #      running. the format is specified in the usual time
    #      parameters, specifying a duration:
    #
    #         <years>y <days>d <seconds>s
    #
    #      the total time will be simply calculated by adding up these
    #      values. Once the time is reached the cluster will simple be
    #      terminated.

    #fgc.deploy_slurm()

if __name__ == '__main__':
    main()
