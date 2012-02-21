# Save current runing master node and one computer node into images
# Using my_instances_list.txt
# fg-cluster-checkpoint userkey nova_ticket master_bucket master_img_name node_bucket node_img_name
#!/bin/sh

lineNumber=0
unzip -o $2 -d ticket

cat my_instances_list.txt|head -n2 |while read line
do
	let "lineNumber = $lineNumber + 1"
	
	scp -i $1.pem -r ticket save-instances.sh ubuntu@`echo $line|awk {'print $2'}`:~/

	if [ $lineNumber = "1" ] ; then
		echo -e "\n...Saving master node......\n"
		master_image_id=$(head -n1 my_instances_list.txt |tail -n1|awk {'print $3'})
		ssh -i $1.pem -n ubuntu@`echo $line|awk {'print $2'}` "source /etc/profile; /bin/bash save-instances.sh $master_image_id $3 $4 $2"
	elif [ $lineNumber = "2" ] ; then
		echo -e "\n...Saveing computation node......\n"
		node_image_id=$(head -n2 my_instances_list.txt |tail -n1|awk {'print $3'})
		ssh -i $1.pem -n ubuntu@`echo $line|awk {'print $2'}` "source /etc/profile; /bin/bash save-instances.sh $node_image_id $5 $6 $2"
	fi
done
