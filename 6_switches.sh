#!/usr/bin/env bash

SESSION="network"
PORT=3006
HOST=127.0.0.1
GRAPH="Config/graph_6.txt"

# Kill existing session if it exists
tmux has-session -t "$SESSION" 2>/dev/null && tmux kill-session -t "$SESSION"

# Create new session with controller (pane 0)
tmux new-session -d -s "$SESSION" \
    "python3 controller.py $PORT $GRAPH"

# Create panes for switches 0–5
for i in {0..5}; do
    tmux split-window -t "$SESSION" \
        "python3 switch.py $i $HOST $PORT"
    tmux select-layout -t "$SESSION" tiled
done

# ---- Kill switch 1 after 5 seconds ----
(
    sleep 5
    echo "Killing switch 1..."
    # Pane index: controller=0, sw0=1, sw1=2, ...
    tmux send-keys -t "$SESSION":0.2 C-c
) &

# Attach to session
tmux attach -t "$SESSION"
