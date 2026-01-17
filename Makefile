PORT=2000
HOST=golov-zephyrus

clean:
	rm *.log

controller:
	python3 controller.py $(PORT) Config/graph_3.txt

sw0:
	python3 switch.py 0 $(HOST) $(PORT)

sw1:
	python3 switch.py 1 $(HOST) $(PORT)

sw2:
	python3 switch.py 2 $(HOST) $(PORT)

