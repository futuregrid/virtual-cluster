REPO=

push:
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
	make -f Makefile distall
	make -f Makefile pipinstall
	fg-cluster

gitgregor:
	git config --global user.name "Gregor von Laszewski"
	git config --global user.email laszewski@gmail.com

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
	rm -rf build dist *.egg-info *~ #*
