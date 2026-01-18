PORT=3000
HOST=127.0.0.1

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

