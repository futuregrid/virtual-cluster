doc:
	cd /tmp
	rm -rf /tmp/vc
	mkdir -p /tmp/vc
	cd /tmp/vc; git clone git://github.com/futuregrid/virtual-cluster.git
	cd /tmp/vc/virtual-cluster/doc; ls; make html
	cp -r /tmp/vc/virtual-cluster/doc/build/html/* .
	git commit -a
	git push
