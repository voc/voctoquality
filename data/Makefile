.PHONY: test coverage lint
test:
	python3 -m coverage run --source libquality,profiles -m unittest discover -s test/

coverage:
	python3 -m coverage xml
	python3 -m coverage report -m

lint:
	python3 -m flake8
