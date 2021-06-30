
TEST_FILES=test_filter.py test_match.py test_misc.py test_curate_license.py

all: test

test:
	@for file in $(TEST_FILES)  ; do \
		echo "---=== $$file ===---" && echo && PYTHONPATH=.. ./$$file && echo ; \
	done

