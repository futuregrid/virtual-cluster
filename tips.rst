TIPS
====

This file contains a number of tips to consider when doing the
programming

PICKLE
------

To save data ina persitnat file one can use either

* pickle
* ZODB

Here a simple example of pickle::

  >>> import cPickle
  >>> strList = ['instane1','instance2']
  >>> pickleFile = open("insance.dat", "w")
  >>> cPickle.dump(strList, pickleFile)
  >>> pickleFile.close()

  >>> pickleFile = open("instance.dat")
  >>> unpickledList = cPickle.load(pickleFile)
  >>> print unpickledList
  ['instance1', 'instance2']
  >>> pickleFile.close()
  >>> 

Naturally we would use a dict to store that

If you like to use a calss like save method, you could use 

ZODB

a good totorial is here:
http://www.zodb.org/documentation/tutorial.html

SSH-ADD
=======

to avoid typing in all the time passwords, i recommend you use ssh add
and keyagent

a good tutorial on this is posted at http://mah.everybody.org/docs/ssh

CREATING A KEY
--------------

>>>> ssh-keygen -t dsa -f ~/.ssh/id_dsa -C "label f the key"

REMOTE HOST PREPARATION
-----------------------

Make sure the public key is in the ~/.ssh/authorized_keys file on the
hosts you wish to connect to::

  >>>> cat ~/.ssh/id_dsa.pub | ssh you@remote-host 'cat - >> ~/.ssh/authorized_keys'

ADDING TO YOUR BASH
-------------------

add the following to your .bash_profile or .bashrc file

It detects if the agent is running stats it and asks you for your
passphrase. any other shell will than use the same agent and you do
not have to retype you phrase till you have closed the shell wher you
started it::

  SSH_ENV="$HOME/.ssh/environment"

  function start_agent {
     echo "Initialising new SSH agent..."
     /usr/bin/ssh-agent | sed 's/^echo/#echo/' > "${SSH_ENV}"
     echo succeeded
     chmod 600 "${SSH_ENV}"
     . "${SSH_ENV}" > /dev/null
     /usr/bin/ssh-add;
  }

# Source SSH settings, if applicable

::

  if [ -f "${SSH_ENV}" ]; then
     . "${SSH_ENV}" > /dev/null
     #ps ${SSH_AGENT_PID} doesn't work under cywgin
     ps -ef | grep ${SSH_AGENT_PID} | grep ssh-agent$ > /dev/null || {
         start_agent;
     }
  else
     start_agent;
  fi 
	
 
