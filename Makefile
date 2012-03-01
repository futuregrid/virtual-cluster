REPO=

push:
	make -f Makefile clean
	git commit -a 
	git push

pull:
	git pull 

install:
	sudo easy_install dist/*.egg 

forceinstall:
	sudo pip install -U dist/*.tar.gz


pipinstall:
	sudo pip install dist/*.tar.gz

distall:
	make -f Makefile egg
	make -f Makefile tar
#	make -f Makefile rpm

test:
	make -f Makefile clean	
	make -f Makefile distall
	sudo pip install --upgrade dist/*.tar.gz
	fg-cluster
	fg-local

gitgregor:
	git config --global user.name "Gregor von Laszewski"
	git config --global user.email laszewski@gmail.com

qc-install:
	sudo pip install pep8
	sudo pip install pylint
	sudo pip install pyflakes

qc:
	pep8 ./futuregrid/virtual/cluster/
	pylint ./futuregrid/virtual/cluster/ | less
	pyflakes ./futuregrid/virtual/cluster/

# #####################################################################
# Creating the distribution
# #####################################################################
egg:
	python setup.py bdist_egg

tar:
	python setup.py sdist

rpm:
	python setup.py bdist_rpm


clean:
	find . -name "*~" -exec rm {} \;  
	find . -name "*.pyc" -exec rm {} \;  
	rm -rf build dist *.egg-info *~ #*
