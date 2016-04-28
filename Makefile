test: mkresultdir clean
	WATCHER_LOG_PATH=./unitTestResults/ py.test -vvvv -s --junit-xml=unitTestResults/result.xml

test-cov: mkresultdir clean
	- rm -f .coverage
	- rm -rf htmlcov
	py.test -vvvv --cov-report html --cov-report=term \
		--cov=config \
		--cov=etcd_client \
		--cov=log \
		--cov=main \
		--cov=reloader \
		--cov=render \
		--cov=watcher \
		--cov=webrouter_conf

mkresultdir:
	- mkdir -p unitTestResults

clean:
	- find . -iname "*__pycache__" | xargs rm -rf
	- find . -iname "*.pyc" | xargs rm -rf
	- rm -rf .cache
