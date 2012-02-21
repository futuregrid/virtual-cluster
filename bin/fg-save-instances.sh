#!/bin/sh

#echo $1
#echo $2
#echo $3
#echo $4

#sudo apt-get install unzip
#unzip -o $4
cd ticket
cp * ../
cat novarc >> ~/.bashrc
source ~/.bashrc
cat novarc >> ~/.profile
source ~/.profile

kernel_id=$(euca-describe-images|awk {'if ($2 ~ /^'"${1}"'/) print $8'})
ramdisk_id=$(euca-describe-images|awk {'if ($2 ~ /^'"${1}"'/) print $9'})

echo "Kernel_id: $kernel_id"
echo "Ramdisk_id: $ramdisk_id"
#echo "sudo euca-bundle-vol -c ${EC2_CERT} -k ${EC2_PRIVATE_KEY} -u ${EC2_USER_ID} --ec2cert ${EUCALYPTUS_CERT} --no-inherit -p $3 -s 1024 -d /mnt/ --kernel $kernel_id"
echo -e "\n...bundling vol......\n"

if [ ! -n "$kernel_id" ]; then
	sudo euca-bundle-vol -c ${EC2_CERT} -k ${EC2_PRIVATE_KEY} -u ${EC2_USER_ID} --ec2cert ${EUCALYPTUS_CERT} --no-inherit -p $3 -s 1024 -d /mnt/> result.tmp1
elif [ ! -n "$ramdisk_id" ]; then
	sudo euca-bundle-vol -c ${EC2_CERT} -k ${EC2_PRIVATE_KEY} -u ${EC2_USER_ID} --ec2cert ${EUCALYPTUS_CERT} --no-inherit -p $3 -s 1024 -d /mnt/ --kernel $kernel_id > result.tmp1
else
	sudo euca-bundle-vol -c ${EC2_CERT} -k ${EC2_PRIVATE_KEY} -u ${EC2_USER_ID} --ec2cert ${EUCALYPTUS_CERT} --no-inherit -p $3 -s 1024 -d /mnt/ --kernel $kernel_id --ramdisk $ramdisk_id > result.tmp1
fi

echo -e "\n...uploading bundle......\n"
euca-upload-bundle -b $2 -m `cat result.tmp1 | tail -n1|awk {'print $3'}` > result.tmp2

echo -e "\n...register bundle......\n"
euca-register `cat result.tmp2 | tail -n1|awk {'print $4'}`

