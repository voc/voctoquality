.PHONY: test coverage lint
test:
	python3-coverage run --source libquality -m unittest discover -s test/

coverage:
	python3-coverage report -m
	python3-coverage xml

lint:
	python3 -m flake8
