def record(db, actor, action, key):
    db.execute('INSERT INTO audit (actor, action, entity_key) VALUES (%s, %s, %s)',
               (actor, action, str(key)))
