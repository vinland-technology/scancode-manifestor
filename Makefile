
init:
	pip3 install -r requirements.txt


.PHONY: test
test:
	python -m unittest

check: test
