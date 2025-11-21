import sqlite3

conn = sqlite3.connect('f:/BUILATHON/ai_visibility.db')
cursor = conn.cursor()

# Get all Xentro jobs
cursor.execute('SELECT id, brand_name, status, created_at FROM analysis_jobs WHERE brand_name LIKE "%Xentro%" ORDER BY created_at DESC')
jobs = cursor.fetchall()
print(f'Found {len(jobs)} Xentro jobs:\n')

for job in jobs:
    cursor.execute('SELECT COUNT(*) FROM results WHERE job_id = ?', (job[0],))
    count = cursor.fetchone()[0]
    print(f'Job ID: {str(job[0])[:8]}... | Status: {job[2]} | Results: {count} | Created: {job[3]}')

conn.close()
