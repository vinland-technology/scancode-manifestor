
TEST_FILES=filter.py match.py misc.py

all: test

test:
	@for file in $(TEST_FILES)  ; do \
		echo $$file && PYTHONPATH=.. ./$$file; \
	done

