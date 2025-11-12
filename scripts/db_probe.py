import os
import sqlite3

def main():
    path = os.path.join('instance', 'cms.db')
    print('db_path:', os.path.abspath(path))
    print('exists:', os.path.exists(path))
    if not os.path.exists(path):
        return
    con = sqlite3.connect(path)
    cur = con.cursor()
    try:
        cur.execute("SELECT id, name, encrypted_with, password_encrypted IS NOT NULL AS has_enc, length(password_encrypted) FROM credential ORDER BY id LIMIT 50")
        rows = cur.fetchall()
        for row in rows:
            print(row)
    except Exception as e:
        print('ERR:', e)
    finally:
        con.close()

if __name__ == '__main__':
    main()


