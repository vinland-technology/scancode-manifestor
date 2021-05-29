
TEST_FILES=filter.py

all: test

test:
	@for file in $(TEST_FILES)  ; do \
		echo $$file && PYTHONPATH=.. ./$$file; \
	done

