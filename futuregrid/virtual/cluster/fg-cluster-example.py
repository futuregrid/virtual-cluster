
gregor = "ABC"
hallo = "XYZ"

title = " Hello world"

filename="cluster.cfg"

string = """
a=%(hallo)s
b=%(gregor)s

<h1> %(title)s </h1>

"""

f = open (filename, w")
print>>f string % vars()
close (f)




string2 = """
a="hallo"
b="world"
""

f = open (filename, w")
print>>f string2 
close (f)

f = open (filename, "r")

with open(fname) as f:
    content = f.readlines()

eval (content)

print a # prints hallo






filename="slurm.conf.in"

the next linesa ra in the fil with the filename

ControlMachine=%(controlMachine)s
AuthType=auth/munge
....


prg to modify
open (filename, "r")

with open(fname) as f:
    content = f.readlines()
close(f)

contollMachine="gregors machine"

new_cntent = content % vars()


f open("slurm.conf","w")
print>> f new+content
close(f)
