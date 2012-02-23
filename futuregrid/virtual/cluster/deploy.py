#! /usr/bin/env python
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
            # Issues with Nova and assigning IPs too quickly, so we're going to sleep.
            sleep(2)

    def _get_public_ips(self, instance_ids):
        public_ips = []
        for instance_id in instance_ids:
            reservation = self.cloud.describe_instance(instance_id)
            instance = reservation.instances[0] if (reservation is not None) else None
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
                instance = reservation.instances[0] if (reservation is not None) else None
                status = instance.state if (instance is not None) else deleted_status

                if status == running_status:
                    running_ids.append(instance_id)
                elif status == deleted_status:
                    print("{0} has status of {1}".format(instance_id, deleted_status))
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
""".format(self.args.name, self.args.number, self.args.instance_type, self.args.image_id))   
        
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
    parser = argparse.ArgumentParser(description='Create a virtual cluster in FutureGrid.')
    parser.add_argument('-k', '--keypair', dest='keypair')
    parser.add_argument('-f', '--key-file', dest='key_file')
    parser.add_argument('-n', '--number', dest='number', type=int)
    parser.add_argument('-t', '--instance-type', dest='instance_type', default='m1.small')
    parser.add_argument('-i', '--image-id', dest='image_id')
    parser.add_argument('-a', '--name', dest='name')
    parser.add_argument('-u', '--ssh-user', dest='ssh_user', default='root')

    args = parser.parse_args()
    
    fgc = FgCreate(args)
    fgc.create_cluster()
    #fgc.deploy_slurm()
    
if __name__ == '__main__':
    main()
