# This script shuts down all vm instances
# Takes no arguments

#!/bin/sh

cat my_instances_list.txt |while read line
do
	echo "Shutting down instance: "`echo $line|awk {'print $1'}`
        euca-terminate-instances `echo $line|awk {'print $1'}`;
done

rm my_instances_list.txt 

