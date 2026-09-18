"""Identical exact-computation tool for all arms; no network or filesystem SQL."""
import json
import sqlite3


def query_records(resources,sql):
    if not sql.lstrip().lower().startswith(('select','with')):raise ValueError('SELECT queries only')
    rows=json.loads(resources.get('records.json','[]'))
    if not rows:return []
    columns=list(rows[0]);db=sqlite3.connect(':memory:')
    quote=lambda s:'"'+s.replace('"','""')+'"'
    try:
        db.execute('CREATE TABLE records ('+','.join(quote(k) for k in columns)+')')
        db.executemany('INSERT INTO records VALUES ('+','.join('?' for _ in columns)+')',[[r[k] for k in columns] for r in rows])
        allowed={sqlite3.SQLITE_SELECT,sqlite3.SQLITE_READ,sqlite3.SQLITE_FUNCTION,sqlite3.SQLITE_RECURSIVE}
        db.set_authorizer(lambda action,*args:sqlite3.SQLITE_OK if action in allowed else sqlite3.SQLITE_DENY)
        ticks=[0]
        def limit():ticks[0]+=1;return int(ticks[0]>1000)
        db.set_progress_handler(limit,1000)
        cur=db.execute(sql);data=cur.fetchmany(1001)
        if len(data)>1000:raise ValueError('Too many output rows; aggregate or filter')
        return [dict(zip([c[0] for c in cur.description],r)) for r in data]
    finally:db.close()
