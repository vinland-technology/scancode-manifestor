
init:
	pip3 install -r requirements.txt

install:
	pip3 install .


.PHONY: test
test:
	python -m unittest

check: test
