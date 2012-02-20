#!/bin/sh

lineNumber=0

echo "...deploying SLURM system......"
cat my_instances_list.txt|sort -r|while read line
do
	ssh -i $1.pem -n ubuntu@`echo $line|awk {'print $2'}` 'sudo dpkg --configure -a'
	ssh -i $1.pem -n ubuntu@`echo $line|awk {'print $2'}` 'sudo apt-get install --yes slurm-llnl'
	#if control node
	if [ $lineNumber = $2 ] ; then
		echo "...configure control node......"
		controlhostname=$(echo $line|awk {'print $1'})
		echo "Control host name: $controlhostname"
		
		#configure slurm.conf
		
		echo "#
ControlMachine=$controlhostname
#ControlAddr=
#BackupController=
#BackupAddr=
#
AuthType=auth/munge
CacheGroups=0
#CheckpointType=checkpoint/none
CryptoType=crypto/munge
#DisableRootJobs=NO
#EnforcePartLimits=NO
#Epilog=
#PrologSlurmctld=
#FirstJobId=1
JobCheckpointDir=/var/lib/slurm-llnl/checkpoint
#JobCredentialPrivateKey=
#JobCredentialPublicCertificate=
#JobFileAppend=0
#JobRequeue=1
#KillOnBadExit=0
#Licenses=foo*4,bar
#MailProg=/usr/bin/mail
#MaxJobCount=5000
MpiDefault=none
#MpiParams=ports:#-#
#PluginDir=
#PlugStackConfig=
#PrivateData=jobs
ProctrackType=proctrack/pgid
#Prolog=
#PrologSlurmctld=
#PropagatePrioProcess=0
#PropagateResourceLimits=
#PropagateResourceLimitsExcept=
ReturnToService=1
#SallocDefaultCommand=
SlurmctldPidFile=/var/run/slurm-llnl/slurmctld.pid
SlurmctldPort=6817
SlurmdPidFile=/var/run/slurm-llnl/slurmd.pid
SlurmdPort=6818
SlurmdSpoolDir=/var/lib/slurm-llnl/slurmd
SlurmUser=slurm
#SrunEpilog=
#SrunProlog=
StateSaveLocation=/var/lib/slurm-llnl/slurmctld
SwitchType=switch/none
#TaskEpilog=
TaskPlugin=task/none
#TaskPluginParam=
#TaskProlog=
#TopologyPlugin=topology/tree
#TmpFs=/tmp
#TrackWCKey=no
#TreeWidth=
#UnkillableStepProgram=
#UnkillableStepTimeout=
#UsePAM=0
#
#
# TIMERS
#BatchStartTimeout=10
#CompleteWait=0
#EpilogMsgTime=2000
#GetEnvTimeout=2
#HealthCheckInterval=0
#HealthCheckProgram=
InactiveLimit=0
KillWait=30
#MessageTimeout=10
#ResvOverRun=0
MinJobAge=300
#OverTimeLimit=0
SlurmctldTimeout=300
SlurmdTimeout=300
#UnkillableStepProgram=
#UnkillableStepTimeout=60
Waittime=0
#
#
# SCHEDULING
#DefMemPerCPU=0
FastSchedule=1
#MaxMemPerCPU=0
#SchedulerRootFilter=1
#SchedulerTimeSlice=30
SchedulerType=sched/backfill
SchedulerPort=7321
SelectType=select/linear
#SelectTypeParameters=
#
#
# JOB PRIORITY
#PriorityType=priority/basic
#PriorityDecayHalfLife=
#PriorityFavorSmall=		
#PriorityMaxAge=
#PriorityUsageResetPeriod=
#PriorityWeightAge=
#PriorityWeightFairshare=
#PriorityWeightJobSize=
#PriorityWeightPartition=
#PriorityWeightQOS=
#
#
# LOGGING AND ACCOUNTING
#AccountingStorageEnforce=0
#AccountingStorageHost=
#AccountingStorageLoc=
#AccountingStoragePass=
#AccountingStoragePort=
AccountingStorageType=accounting_storage/none
#AccountingStorageUser=
ClusterName=cluster
#DebugFlags=
#JobCompHost=
#JobCompLoc=
#JobCompPass=
#JobCompPort=
JobCompType=jobcomp/none
#JobCompUser=
JobAcctGatherFrequency=30
JobAcctGatherType=jobacct_gather/none
SlurmctldDebug=3
SlurmctldLogFile=/var/log/slurm-llnl/slurmctld.log
SlurmdDebug=3
SlurmdLogFile=/var/log/slurm-llnl/slurmd.log
#
#
# POWER SAVE SUPPORT FOR IDLE NODES (optional)
#SuspendProgram=
#ResumeProgram=
#SuspendTimeout=
#ResumeTimeout=
#ResumeRate=
#SuspendExcNodes=
#SuspendExcParts=
#SuspendRate=
#SuspendTime=
#
#
# COMPUTE NODES" > slurm.conf	

		#add computer node info	
		echo "...adding compute nodes info......"
		cat my_instances_list.txt|sort -r|head -n$2|while read line
		do
			computenodename=$(echo $line|awk {'print $1'})
			echo "NodeName=$computenodename Procs=1 State=UNKNOWN
PartitionName=debug Nodes=$computenodename Default=YES MaxTime=INFINITE State=UP" >> slurm.conf
		done
		
		echo -e "\n***********************
***Configuring slurm***
***************"********\n
		
		# copy munge-key to local
		echo "...generating munge-key on control node......"
		ssh -i $1.pem -n ubuntu@`echo $line|awk {'print $2'}` 'sudo /usr/sbin/create-munge-key'
		echo "...copying munge-key to local......"
		ssh -i $1.pem -n ubuntu@`echo $line|awk {'print $2'}` 'sudo cat /etc/munge/munge.key' > munge.key

		#copy munge-key to compute node
		echo "...copying munge-key to compute node......"
		cat my_instances_list.txt|sort -r|head -n$2|while read line
		do
        scp -i $1.pem munge.key ubuntu@`echo $line|awk {'print $2'}`:~/
        ssh -i $1.pem -n ubuntu@`echo $line|awk {'print $2'}` 'sudo cp munge.key /etc/munge/munge.key'
        ssh -i $1.pem -n ubuntu@`echo $line|awk {'print $2'}` 'sudo chown munge /etc/munge/munge.key'
        ssh -i $1.pem -n ubuntu@`echo $line|awk {'print $2'}` 'sudo chgrp munge /etc/munge/munge.key'
        ssh -i $1.pem -n ubuntu@`echo $line|awk {'print $2'}` 'sudo chmod 400 /etc/munge/munge.key'
		done


		echo "...starting running......"
		#copy slurm.conf to nodes
		cat my_instances_list.txt|while read line
		do
			echo "...copying slurm.conf to nodes......"
			scp -i $1.pem slurm.conf ubuntu@`echo $line|awk {'print $2'}`:~/
			ssh -i $1.pem -n ubuntu@`echo $line|awk {'print $2'}` 'sudo cp slurm.conf /etc/slurm-llnl/slurm.conf'		
			echo "...starting slurm......"
			ssh -i $1.pem -n ubuntu@`echo $line|awk {'print $2'}` 'sudo /etc/init.d/slurm-llnl start'
			echo "...starting munge......"
			ssh -i $1.pem -n ubuntu@`echo $line|awk {'print $2'}` 'sudo /etc/init.d/munge start'
		done
		
	fi
	let "lineNumber=$lineNumber+1"
done

