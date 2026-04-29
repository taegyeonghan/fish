import sqlite3
import os
import sys
import glob

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Find latest simulation with posts
for sim_dir in sorted(glob.glob('uploads/simulations/sim_*'), reverse=True):
    db = os.path.join(sim_dir, 'reddit_simulation.db')
    if not os.path.exists(db):
        continue
    conn = sqlite3.connect(db)
    c = conn.cursor()
    try:
        c.execute('SELECT content FROM post LIMIT 3')
        rows = c.fetchall()
        if rows:
            print('=== ' + sim_dir + ' ===')
            for r in rows:
                content = r[0] or ''
                backslash = chr(92)
                has_escape = (backslash + 'u') in content
                print('has_literal_\\u escape:', has_escape)
                print('length:', len(content))
                print('content:', content[:200])
                print('---')
            break
    except Exception as e:
        print('err:', e)
    conn.close()