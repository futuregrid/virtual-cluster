#! /usr/bin/env python
# Test file for detecting whether port is listening given IP

import socket, time

class DetectPort:
    def __init__(self, ip, port):
        self.ip = ip
	self.port = port

    def detect_port(self):
	 while 1:
                try:
                    sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sk.settimeout(1)
                    sk.connect((self.ip, self.port))
                    sk.close()
                    print 'ready to deploy'
                    break

                except Exception:
                    print 'not ready to deploy yet'
                    time.sleep(2)

def main():
    D = DetectPort('149.165.146.154', 22)
    D.detect_port()

if __name__ == '__main__':
    main()

