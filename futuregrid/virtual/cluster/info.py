from fabric.api import run

import os

def host_type():
    run('uname -s')

def info():
    host_type()

def localinfo():
    os.system('uname -s')
    
