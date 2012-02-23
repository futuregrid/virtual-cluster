#! /usr/bin/env python
import socket, time, getopt, sys, os

class FgShutdown:

        def __init__(self, name):
                self.name = name

	def clean(self):
                print '...Clearing up......'
		os.remove('my_instances_list.txt')
                print '...Done......'

	def shut_down(self):
		f = file('my_instances_list.txt')
                while True:
                        line = f.readline()
                        if len(line) == 0:
                                break
                        line = [x for x in line.split()]
			print "...Shutting down %s" %line[0]
			os.system("euca-terminate-instances %s" %line[0])
                f.close()


def usage():
        print '-h/--help    Display this help.'
        print '-a/--name    provide name of virtual cluster.'


def main():

        try:
                opts, args = getopt.getopt(sys.argv[1:], "ha:", ["help", "name="])
        except getopt.GetoptError:
                usage()
                sys.exit()

        for opt, arg in opts:
                if opt in ("-h", "--help"):
                        usage()
                        sys.exit()
		if opt in ("-a", "--name"):
                        name=arg

        fgs=FgShutdown(name)
	fgs.shut_down()
	fgs.clean()

if __name__ == '__main__':
    main()
