REPO=

######################################################################
# GIT interfaces
######################################################################
push:
	make -f Makefile clean
	git commit -a 
	git push

pull:
	git pull 

gregor:
	git config --global user.name "Gregor von Laszewski"
	git config --global user.email laszewski@gmail.com

######################################################################
# installation
######################################################################
pip:
	make -f Makefile clean
	python setup.py sdist

upload:
	make -f Makefile pip
#	python setup.py register
	python setup.py sdist upload

force:
	sudo pip install -U dist/*.tar.gz


install:
	sudo pip install dist/*.tar.gz

test:
	make -f Makefile clean	
	make -f Makefile distall
	sudo pip install --upgrade dist/*.tar.gz
	fg-cluster
	fg-local

######################################################################
# QC
######################################################################

qc-install:
	sudo pip install pep8
	sudo pip install pylint
	sudo pip install pyflakes

qc:
	pep8 ./futuregrid/virtual/cluster/
	pylint ./futuregrid/virtual/cluster/ | less
	pyflakes ./futuregrid/virtual/cluster/

# #####################################################################
# CLEAN
# #####################################################################


clean:
	find . -name "*~" -exec rm {} \;  
	find . -name "*.pyc" -exec rm {} \;  
	rm -rf build dist *.egg-info *~ #*

