#!/bin/bash
case "$1" in
  start)
    tmux new-session -d -s autodev -n orchestrator
    tmux send-keys -t autodev:orchestrator "cd ~/meritgiving && python3 autodev/orchestrator.py" Enter
    echo "✅ AutoDev started in tmux session 'autodev'"
    echo "Watch: tmux attach -t autodev"
    echo "Logs: tail -f ~/meritgiving/autodev/logs/autodev.log"
    ;;
  stop)
    tmux kill-session -t autodev 2>/dev/null && echo "🛑 Stopped" || echo "Not running"
    ;;
  status)
    echo "=== Task Status ==="
    python3 -c "import json; t=json.load(open('/home/akbar/meritgiving/autodev/tasks.json')); [print(f\"{'✅' if x['status']=='done' else '⏳' if x['status']=='pending' else '❌'} {x['title']}\") for x in t]"
    echo ""
    echo "=== Live Log (last 10 lines) ==="
    tail -n 10 ~/meritgiving/autodev/logs/autodev.log 2>/dev/null || echo "No log yet"
    ;;
  logs)
    tail -f ~/meritgiving/autodev/logs/autodev.log
    ;;
  reset)
    python3 -c "
import json
with open('/home/akbar/meritgiving/autodev/tasks.json') as f: t=json.load(f)
for x in t: x['status']='pending'; x.pop('retries',None); x.pop('finished',None)
with open('/home/akbar/meritgiving/autodev/tasks.json','w') as f: json.dump(t,f,indent=2)
print('Reset all tasks to pending.')
"
    ;;
  *)
    echo "Usage: ./run.sh {start|stop|status|logs|reset}"
    ;;
esac
