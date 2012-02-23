import boto
from boto.ec2.connection import EC2Connection
from boto.ec2.regioninfo import RegionInfo
from boto.exception import EC2ResponseError
import os

class Cloud:
    _ec2_conn = None
    _cloud_name = None
    
    def __init__(self):
        if os.environ.has_key("EUCALYPTUS_CERT"):
            self._cloud_name = "nova" if os.environ.has_key("NOVA_USERNAME") else "euca"
        else:
            self._cloud_name = "ec2"

        aws_access_key_id = os.environ["EC2_ACCESS_KEY"]
        aws_secret_access_key = os.environ["EC2_SECRET_KEY"]

        proxy_host, proxy_port = self.split_proxy_url()
        
        if self._cloud_name == "euca":
            self._ec2_conn = EC2Connection(aws_access_key_id=aws_access_key_id,
                                           aws_secret_access_key=aws_secret_access_key,
                                           is_secure=False,
                                           region=RegionInfo(None, "eucalyptus", "149.165.146.135"),
                                           port=8773,
                                           path="/services/Eucalyptus")
        elif self._cloud_name == "nova":
            self._ec2_conn = EC2Connection(aws_access_key_id=aws_access_key_id,
                                           aws_secret_access_key=aws_secret_access_key,
                                           is_secure=False,
                                           region=RegionInfo(None, "nova", "149.165.146.26"),
                                           port=8773,
                                           path="/services/Cloud")
        else:
            self._ec2_conn = boto.connect_ec2(aws_access_key_id=aws_access_key_id,
                                              aws_secret_access_key=aws_secret_access_key,
                                              proxy=proxy_host,
                                              proxy_port=proxy_port)


    def assign_public_ip(self, instance_id):
        addresses = self.describe_addresses()
        for address in addresses:
            address_public_ip = address.public_ip
            address_instance_id = address.instance_id
            if not address_instance_id:
                return self.associate_address(instance_id, public_ip=address_public_ip)
        
    def associate_address(self, instance_id, public_ip=None, allocation_id=None):
        # boto 1.9 does not have the allocation_id.
        return self._ec2_conn.associate_address(instance_id, public_ip)
    
        #print(boto.Version)
        #if boto.Version == "1.9b":
        #    print("instance_id: '{0}' public_ip: '{1}'".format(instance_id, public_ip))
        #    return self._ec2_conn.associate_address(instance_id, public_ip)
        #else:
        #    return self._ec2_conn.associate_address(instance_id, public_ip=public_ip, allocation_id=allocation_id)

        
    def attach_volume(self, volume_id, instance_id, device):
        return self._ec2_conn.attach_volume(volume_id, instance_id, device)
        

    def authorize_security_group(self, group_name=None, src_security_group_name=None, src_security_group_owner_id=None,
                                 ip_protocol=None, from_port=None, to_port=None, cidr_ip=None, group_id=None,
                                 src_security_group_group_id=None):
        """
        Authorize the security group information.

        REQUIRED PARAMETERS

        group_name
        """
        # If the keyword args dict has "ip_protocol" as a key then authorize the protocol, ports, and IPs.
        # Otherwise, authorize the security group to another security group.
        if ip_protocol:
            return_code = self._ec2_conn.authorize_security_group(group_name=group_name, ip_protocol=ip_protocol,
                                                                  from_port=from_port, to_port=to_port, cidr_ip=cidr_ip)
        else:
            # If the keyword args dict contains the key "src_security_group_owner_id" then use it;
            # otherwise, grab the owner_id from the security group in EC2.
            security_group = self.describe_security_group(group_name)
            owner_id = src_security_group_owner_id if src_security_group_owner_id else security_group.owner_id
            
            return_code = self._ec2_conn.authorize_security_group(group_name=group_name,
                                                                  src_security_group_name=src_security_group_name,
                                                                  src_security_group_owner_id=owner_id)

        return return_code


    def cancel_spot_instance_requests(self, request_ids):
        return self._ec2_conn.cancel_spot_instance_requests(request_ids)


    def create_security_group(self, name, description):
        return self._ec2_conn.create_security_group(name, description)


    def create_volume(self, size, availability_zone, snapshot=None):
        return self._ec2_conn.create_volume(size, availability_zone, snapshot)


    def delete_security_group(self, group_name):
        return self._ec2_conn.delete_security_group(group_name)


    def delete_volume(self, volume_id):
        """
        Delete the volume.
        
        REQUIRED PARAMETERS

        :type volume_id: string
        :param volume_id: The cloud volume-id value.
        """
        return self._ec2_conn.delete_volume(volume_id)


    def describe_addresses(self, addresses=None, filters=None, allocation_ids=None):
        # boto 1.9 does not have the filters argument.
        if boto.Version == "1.9b":
            return self._ec2_conn.get_all_addresses(addresses=addresses)
        else:
            return self._ec2_conn.get_all_addresses(addresses=addresses, filters=filters, allocation_ids=allocation_ids)

    
    def describe_instance(self, instance_id):
        reservation_list = self.describe_instances(instance_ids=[instance_id])
        # If the reservation list has this instance's reservation information then return just that reservation;
        # otherwise, return None to indicate the instance does not exist.
        return reservation_list[0] if len(reservation_list) == 1 else None

    
    def describe_instances(self, instance_ids=[], filters=None):
        # boto 1.9 does not have the filters argument.
        if boto.Version == "1.9b":
            return self._ec2_conn.get_all_instances(instance_ids=instance_ids)
        else:
            return self._ec2_conn.get_all_instances(instance_ids, filters)
    

    def describe_security_group(self, group_name):
        security_group_list = self.describe_security_groups(group_names=[group_name])
        # If the security group list has information then return just that security group;
        # otherwise, return None to indicate the security group does not exist.
        return security_group_list[0] if security_group_list is not None and len(security_group_list) == 1 else None

    
    def describe_security_groups(self, group_names=[]):
        try:
            return self._ec2_conn.get_all_security_groups(groupnames=group_names)
        except EC2ResponseError:
            return None

    def describe_volume(self, volume_id):
        try:
            volume_list = self.describe_volumes(volume_ids=[volume_id])
            # If the volume list has information then return just that volume;
            # otherwise, return None to indicate the volume does not exist.
            # NOTE: the following line will work for EC2, but not EUCA since it does not filter volumes.
            #return volume_list[0] if len(volume_list) == 1 else None
            return_volume = None
            for volume in volume_list:
                if volume.id == volume_id:
                    return_volume = volume
                    break

            return return_volume

        except EC2ResponseError:
            return None
        

    def describe_volumes(self, volume_ids=None):
        # NOTE: Eucalyptus does not filter volumes.
        return self._ec2_conn.get_all_volumes(volume_ids)
        

    def detach_volume(self, volume_id, instance_id=None, device=None, force=False):
        return self._ec2_conn.detach_volume(volume_id, instance_id, device, force)


    def get_all_spot_instance_requests(self, request_ids=None, filters=None):
        return self._ec2_conn.get_all_spot_instance_requests(request_ids, filters)

    
    def get_spot_price_history(self, start_time=None, end_time=None, instance_type=None, product_description=None):
        return self._ec2_conn.get_spot_price_history(start_time=start_time, end_time=end_time,
                                                    instance_type=instance_type, product_description=product_description)


    def get_name(self):
        return self._cloud_name
    
    def request_spot_instances(self, price, image_id, count=1, request_type="one-time", valid_from=None, valid_until=None,
                               launch_group=None, availability_zone_group=None, key_name=None, security_groups=None,
                               user_data=None, addressing_type=None, instance_type='m1.small', placement=None, kernel_id=None,
                               ramdisk_id=None, monitoring_enabled=False, subnet_id=None, block_device_map=None):
        return self._ec2_conn.request_spot_instances(price=price, image_id=image_id, count=count, type=request_type,
                                                    valid_from=valid_from, valid_until=valid_until, launch_group=launch_group,
                                                    availability_zone_group=availability_zone_group, key_name=key_name,
                                                    security_groups=security_groups, user_data=user_data,
                                                    addressing_type=addressing_type, instance_type=instance_type,
                                                    placement=placement, kernel_id=kernel_id, ramdisk_id=ramdisk_id,
                                                    monitoring_enabled=monitoring_enabled, subnet_id=subnet_id, block_device_map=block_device_map)
    
    def revoke_security_group(self, **kwargs):
        """
        Revoke the security group permissions.
        
        :type **kwargs: dict
        :param **kwargs: A keyword args dict containing the (name, value) pairs for the cloud provider.

        The **kwargs dict requires:
        group_name   The security group name.
        
        The **kwargs dict should contain either values for IP ingress or named ingress.
        IP ingress values:
        ip_protocol: The IP protocol. Valid values: "tcp" | "udp" | "icmp"
        from_port:  The from port value. int.
        to_port: The to port value. int.
        cidr_ip: The CIDR IP string. E.g., 0.0.0.0/0.

        Named ingress values:
        src_security_group_name: The source security group name. string.
        src_security_group_owner_id: The source security group id. This value is option.
            If not specified then the EC2_USER_ID environment variable is used.
        """
        # If the keyword args dict has "ip_protocol" as a key then revoke the protocol, ports, and IPs.
        # Otherwise, authorize revoke the group from another security group.
        if kwargs.has_key("ip_protocol"):
            return_code = self._ec2_conn.revoke_security_group(
                group_name=kwargs["group_name"],
                ip_protocol=kwargs["ip_protocol"],
                from_port=kwargs["from_port"],
                to_port=kwargs["to_port"],
                cidr_ip=kwargs["cidr_ip"])
        else:
            # If the keyword args dict contains the key "src_security_group_owner_id" then use it;
            # otherwise, grab the EC2_USER_ID environment variable.
            owner_id = kwargs.get("src_security_group_owner_id", os.environ["EC2_USER_ID"])
            
            return_code = self._ec2_conn.revoke_security_group(
                group_name=kwargs["group_name"],
                src_security_group_name=kwargs["src_security_group_name"],
                src_security_group_owner_id=owner_id)

        return return_code

    
    def run_instances(self, **kwargs):

        # If a file was passed in then open the file and pass the contents as user data.
        if kwargs.has_key("user_file"):
            # Open the file and set the contents to the user-data
	    f = open(kwargs["user_file"], "r")
	    kwargs["user_data"] = "".join(f.readlines())
            del kwargs["user_file"]

        # If the "count" was passed in then set min_ and max_count to this value.
        if kwargs.has_key("count"):
            count= kwargs["count"]
            kwargs["min_count"] = count
            kwargs["max_count"] = count

        
        # currently set for boto 1.9 parameters to make it compatable with Eucalyptus.
        return_code = self._ec2_conn.run_instances(
            kwargs["image_id"],
            min_count=kwargs.get("min_count", 1),
            max_count=kwargs.get("max_count", 1),
            key_name=kwargs["key_name"],
            security_groups=kwargs["security_groups"],
            user_data=kwargs.get("user_data", None),
            addressing_type=kwargs.get("addressing_type", None),
            instance_type=kwargs.get("instance_type", "m1.small"),
            placement=kwargs.get("availability_zone", kwargs.get("placement", None)),
            kernel_id=kwargs.get("kernel_id", None),
            ramdisk_id=kwargs.get("ramdisk_id", None),
            monitoring_enabled=kwargs.get("monitoring_enabled", False),
            subnet_id=kwargs.get("subnet_id", None),
            block_device_map=kwargs.get("block_device_map", None))

            # boto 2.0 parameters.
            #disable_api_termination=kwargs.get("disable_api_termination", False),
            #instance_initiated_shutdown_behavior=kwargs.get("instance_initiated_shutdown_behavior", None),
            #private_ip_address=kwargs.get("private_ip_address", None),
            #placement_group=kwargs.get("placement_group", None),
            #client_token=kwargs.get("client_token", None),
            #security_group_ids=kwargs.get("security_group_ids", None))

        return return_code


    def security_group_exists(self, group_name):
        security_group = self.describe_security_group(group_name)
        return ((security_group is not None) and (security_group.name == group_name))


    def security_group_permission_exists(self, **kwargs):
        # TODO: Check the authorizations to see if it already exists.
        return False


    def split_proxy_url(self):
        proxy = None
        proxy_port = None

        # If a proxy URL is in the environment variables then split.
        if os.environ.has_key("HTTP_PROXY"):
            proxy_url = os.environ["HTTP_PROXY"]
            
            # If the URL contains "//" then remove the "http://" or "https://"
            index = proxy_url.find("//")
            host_port = proxy_url if index < 0 else proxy_url.split("//")[1]

            # Split the host and port and return the port as an int.
            proxy, proxy_port = host_port.split(":")
            return proxy, int(proxy_port)
        else:
            # Set the values to default None values to indicate no proxy.
            return None, None
   

    def terminate_instance(self, instance_id):
        instance_list = self.terminate_instances(instance_ids=[instance_id])
        # If the instance list has information then return just that instance;
        # otherwise, return None to indicate the instance does not exist.
        return instance_list[0] if len(instance_list) == 1 else None


    def terminate_instances(self, instance_ids=None):
        return self._ec2_conn.terminate_instances(instance_ids=instance_ids)
