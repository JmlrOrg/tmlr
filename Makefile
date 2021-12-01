SHELL := /bin/bash

all: static

clean:
	rm -rf output

npm: clean
	mkdir -p output/beta/js
	mkdir -p output/beta/css

webpage: npm
	python src/gen_webpage.py

static: webpage
	cp -r static/img/ output/
	cp -r static/css/ output/

test:
	py.test -vv src/tests/test.py

develop:
	livereload -p 8001 output/
