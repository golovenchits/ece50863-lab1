#!/usr/bin/env python

"""This is the Switch Starter Code for ECE50863 Lab Project 1
Author: Xin Du
Email: du201@purdue.edu
Last Modified Date: December 9th, 2021
"""

import sys
from datetime import date, datetime
import socket
from controller import REG_REQ, Switch, K, TIMEOUT, KEEPALIVE
import threading
import time
from typing import List, Dict

# Please do not modify the name of the log file, otherwise you will lose points because the grader won't be able to find your log file
LOG_FILE = "switch#.log" # The log file for switches are switch#.log, where # is the id of that switch (i.e. switch0.log, switch1.log). The code for replacing # with a real number has been given to you in the main function.

lock = threading.Lock()

# Those are logging functions to help you follow the correct logging standard

# "Register Request" Format is below:
#
# Timestamp
# Register Request Sent

def register_request_sent():
    log = []
    log.append(str(datetime.time(datetime.now())) + "\n")
    log.append(f"Register Request Sent\n")
    write_to_log(log)

# "Register Response" Format is below:
#
# Timestamp
# Register Response Received

def register_response_received():
    log = []
    log.append(str(datetime.time(datetime.now())) + "\n")
    log.append(f"Register Response received\n")
    write_to_log(log) 

# For the parameter "routing_table", it should be a list of lists in the form of [[...], [...], ...]. 
# Within each list in the outermost list, the first element is <Switch ID>. The second is <Dest ID>, and the third is <Next Hop>.
# "Routing Update" Format is below:
#
# Timestamp
# Routing Update 
# <Switch ID>,<Dest ID>:<Next Hop>
# ...
# ...
# Routing Complete
# 
# You should also include all of the Self routes in your routing_table argument -- e.g.,  Switch (ID = 4) should include the following entry: 		
# 4,4:4

def routing_table_update(routing_table):
    log = []
    log.append(str(datetime.time(datetime.now())) + "\n")
    log.append("Routing Update\n")
    for row in routing_table:
        log.append(f"{row[0]},{row[1]}:{row[2]}\n")
    log.append("Routing Complete\n")
    write_to_log(log)

# "Unresponsive/Dead Neighbor Detected" Format is below:
#
# Timestamp
# Neighbor Dead <Neighbor ID>

def neighbor_dead(switch_id):
    log = []
    log.append(str(datetime.time(datetime.now())) + "\n")
    log.append(f"Neighbor Dead {switch_id}\n")
    write_to_log(log) 

# "Unresponsive/Dead Neighbor comes back online" Format is below:
#
# Timestamp
# Neighbor Alive <Neighbor ID>

def neighbor_alive(switch_id):
    log = []
    log.append(str(datetime.time(datetime.now())) + "\n")
    log.append(f"Neighbor Alive {switch_id}\n")
    write_to_log(log) 

def write_to_log(log):
    with open(LOG_FILE, 'a+') as log_file:
        log_file.write("\n\n")
        # Write to log
        log_file.writelines(log)

# def send_topo_update(my_id: int, ctrl_addr: tuple, sock: socket.socket):
#     msg = f"{my_id}"
#     for sw in neighbs.values():
#         msg += f"\n{sw.id} {sw.live}"
    
#     sock.sendto(msg.encode(), ctrl_addr)

def parse_routing_table(data):
    lines = data.decode().split("\n")
    print(lines)
    if int(lines[0]) != my_id:
        raise Exception("ID mismatch!")
    
    res_routing_table = []
    for line in lines[1:]:
        dest_id, next_hop = line.split(" ")
        res_routing_table.append([my_id, int(dest_id), int(next_hop)])

    return res_routing_table


neighbs: Dict[int, Switch] = {}       

n_id_fail = None   
my_id = None     

# need to do something about link failure 
def alive_topology(my_id: int, ctrl_addr: tuple, sock: socket.socket):
    while(True):
        topology_update_msg = f"{my_id}"
        keep_looping = False
        for n_sw in neighbs.values():
            topology_update_msg += f"\n{n_sw.id} {n_sw.live}"
            if n_sw.live:
                keep_looping = True
                sock.sendto(f"{my_id} {KEEPALIVE}".encode(), n_sw.addr)
                print(f"sending alive to sw{n_sw.id}")
        # if not keep_looping:
        #     return
        sock.sendto(topology_update_msg.encode(), ctrl_addr)
        time.sleep(K)

def receive_updates(sock: socket.socket):
    sock.settimeout(TIMEOUT)
    while(True):
        msg = None
        try:
            data, addr = sock.recvfrom(1024)
            if KEEPALIVE in data.decode():
                n_id_raw, msg = data.decode().strip().split(" ")
                n_id = int(n_id_raw)
        except socket.timeout:
            print("All neighbors are dead!")

        # Link failure simulation
        # if n_id == n_id_fail:
        #     print(f"link failure with sw{n_id_fail}!")
        #     try:
        #         del neighbs[n_id_fail]
        #     except KeyError:
        #         pass
        #     continue
        
        if msg == KEEPALIVE:
            print(f"sw{n_id} is alive")
            lock.acquire()
            neighbs[n_id].last_seen = time.monotonic()
            if not neighbs[n_id].live:
                neighbs[n_id].live = True
            lock.release()
        else:
            routing_table = parse_routing_table(data)
            routing_table_update(routing_table)

        keep_looping = False
        for sw in neighbs.values():
            if sw.live:
                keep_looping = True
                if time.monotonic() - sw.last_seen > TIMEOUT:
                    lock.acquire()
                    sw.live = False
                    lock.release()
                    neighbor_dead(sw.id)
                    print(f"sw{sw.id} is dead!")

        # if not keep_looping:
        #     return




def main():

    global LOG_FILE
    global n_id_fail
    global my_id

    #Check for number of arguments and exit if host/port not provided
    num_args = len(sys.argv)
    if num_args < 4:
        print ("switch.py <Id_self> <Controller hostname> <Controller Port>\n")
        sys.exit(1)

    if '-f' in sys.argv:
        link_fail = True
        n_id_fail = int(sys.argv[5])
    else:
        link_fail = False
        n_id_fail = None

    print(link_fail, n_id_fail)
    my_id = int(sys.argv[1])
    LOG_FILE = 'switch' + str(my_id) + ".log" 

    # Write your code below or elsewhere in this file

    ctrl_host = sys.argv[2]
    ctrl_port = int(sys.argv[3])

    with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as sock: 
        sock.bind(('', 0))
        udp_host = "127.0.0.1"

        register_msg = f"{my_id} {REG_REQ}"
        sock.sendto(register_msg.encode(),(ctrl_host,ctrl_port))
        register_request_sent()

        data, addr = sock.recvfrom(1024)
        
        lines = data.decode().split("\n")
        num_neighb = int(lines[0])
        for line in lines[1:]:
            n_id, n_addr, n_port = line.split(" ")
            neighbs.update({int(n_id): Switch(int(n_id), (n_addr, int(n_port)))})

        for n in neighbs.values():
            print(n.id, n.addr)

        register_response_received()

        data, addr = sock.recvfrom(1024)

        routing_table = parse_routing_table(data)
        print("Routing table : \n" + str(routing_table) + "\n")

        routing_table_update(routing_table)

        print(neighbs)

        athread = threading.Thread(target=alive_topology, args=(my_id, (ctrl_host, ctrl_port), sock,))
        rthread = threading.Thread(target=receive_updates, args=(sock,))

        athread.start()
        rthread.start()

        athread.join()
        rthread.join()
        

if __name__ == "__main__":
    main()