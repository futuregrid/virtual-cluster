#! /usr/bin/env python


class HelloWorld(object):
    def __init__(self):
        pass

    def say_hi(self, name=None):
        if name:
            print 'Hello World! My name is %s.' % name
        else:
            print 'Hello World!'


def main():
    h = HelloWorld()
    h.say_hi('johnny')

if __name__ == '__main__':
    main()
