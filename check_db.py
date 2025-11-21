import sqlite3

conn = sqlite3.connect('f:/BUILATHON/ai_visibility.db')
cursor = conn.cursor()

# Get latest job
cursor.execute('SELECT id, brand_name, created_at FROM analysis_jobs ORDER BY created_at DESC LIMIT 1')
job = cursor.fetchone()
print(f'Latest job: {job[0]} - {job[1]} at {job[2]}')

# Count results
cursor.execute('SELECT COUNT(*) as total FROM results WHERE job_id = ?', (job[0],))
print(f'Total results saved: {cursor.fetchone()[0]}')

# Show first 10 results
cursor.execute('SELECT query_text, model, brand_mentioned FROM results WHERE job_id = ? LIMIT 10', (job[0],))
results = cursor.fetchall()
print('\nFirst 10 results:')
for r in results:
    print(f'  Query: {r[0][:60]}... | Model: {r[1]} | Mentioned: {r[2]}')

conn.close()
