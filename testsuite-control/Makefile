SUITE = ${DESTDIR}/var/lib/slenkins/tests-tomcat

all:

install: nodes run.py
	mkdir -p ${SUITE}/tests-control/bin
	cp nodes ${SUITE}/tests-control/
	cp run.py ${SUITE}/tests-control/bin/
	cp -R lib ${SUITE}/tests-control/bin/
