service_monitor.zip: service_monitor/service_monitor.py
	cd service_monitor && zip -u $@ service_monitor.py
	mv service_monitor/$@ ./

test:
	python3 -m unittest service_monitor/service_monitor.py
