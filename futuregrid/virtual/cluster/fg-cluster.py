"""

This file will containe the new fg-cluster command

While previously a lot of code redundance was introduced by keeping the logic of restor, terminate, run, and so forth in separate files, we merge this functionality in one file and eliminate the other prorams we will only have one fg-cluster command.

but it has the options

Note: please look how to best implement this, if you use a subparser, it may be best to lose the "-" alltogether for he subparser invocation e.g. it would be fg-cluster status and not fg-cluster -status. Find the simplest way to implement eith but not both


fg-cluster -status

   prints the status of all running virtual clustres

fg-clustre -status name

   prints the status of the virtual cluster with th egiven name

fg-cluster -terminate 

   terminaes all running virtual clusters

fg-cluster -terminate name

   terminates the virtual cluster with the given name

fg-clister -run ...

fg-cluster -checkpoint ...

fg-cluster -restore ...

fg-cluster -list ...


e.g. a "type" is passe dto the command to indicate what we will do.

"""
