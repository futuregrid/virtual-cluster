# This script restores a virtual cluster
# fg-create-cluster userkey master_node_id computation_node_id computation_node_num

#!/bin/sh

echo "...Restoring master node......"
euca-run-instances -k $1 -n 1 $2

echo "...Restoring computation nodes......"
euca-run-instances -k $1 -n $4 $3

euca-describe-instances|awk {'if ($2 ~ /^i/) print $2'}|sort|tail -n$(($2+1)) > instance_id.tmp
euca-describe-addresses |grep -v 'i' |cut -f2 |sort |head -n$(($2+1)) > instance_ip.tmp
euca-describe-instances|awk {'if ($2 ~ /^i/) print $2,$3'}|sort|tail -$(($2+1))|awk {'print $2'} > image_id.tmp
euca-describe-instances|awk {'if ($2 ~ /^i/) print $2,$5'}|sort|tail -n$(($2+1))|awk {'print $2'} > inner_ip.tmp
paste instance_id.tmp instance_ip.tmp image_id.tmp inner_ip.tmp> my_instances_list.txt

echo "...associating public IPs ............."
sleep 3

cat my_instances_list.txt |while read line
do
        euca-associate-address -i `echo $line|awk {'print $1'}` `echo $line|awk {'print $2'}`;
done

rm instance_id.tmp
rm instance_ip.tmp
rm image_id.tmp
rm inner_ip.tmp

