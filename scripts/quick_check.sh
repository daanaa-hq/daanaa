#!/bin/bash
echo "MERIT STATUS — $(date '+%H:%M:%S')"
A=$(pgrep -cf "merit_worker_a" 2>/dev/null || echo 0)
C=$(pgrep -cf "merit_worker_c" 2>/dev/null || echo 0)
D=$(pgrep -cf "merit_worker_d" 2>/dev/null || echo 0)
E=$(pgrep -cf "merit_worker_e" 2>/dev/null || echo 0)
F=$(pgrep -cf "merit_worker_f" 2>/dev/null || echo 0)
echo "A: $A | C: $C | D: $D | E: $E | F: $F"
sqlite3 ~/meritgiving/data/merit_state.db "SELECT 'Done: '||COUNT(*)||' | Left: '||(SELECT COUNT(*) FROM propublica_queue WHERE status='pending') FROM propublica_queue WHERE status='done';" 2>/dev/null || echo "DB locked"
echo "XML: $(ls ~/meritgiving/data/990_xml/ 2>/dev/null | wc -l) files | $(du -sh ~/meritgiving/data/990_xml/ 2>/dev/null | cut -f1)"
tail -1 ~/meritgiving/logs/worker_a.log 2>/dev/null | grep -o 'ProPublica:.*'
