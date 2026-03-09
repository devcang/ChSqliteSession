"""
SQLite DB backend for CherryPy sessions.
"""

import os , json, sqlite3, datetime, threading
import cherrypy
#, hashlib

###Using pickle encode/decode json, always throw some excepion.###
###so, we use json to do encode/decode                         ###
# try:
#   import cPickle as pickle
# except ImportError:
#   import pickle

from cherrypy.lib.sessions import Session

class SqliteSession(Session):
    db_filename = "ChSqliteSession.db"
    DB_STRING   = 'NONE'
    db          = None
    locks       = {}
    sqlCreate = r'''CREATE TABLE IF NOT EXISTS session (
id INTEGER PRIMARY KEY AUTOINCREMENT,
sid TEXT NOT NULL,
data BLOB NULL,
expiration_time DATETIME DEFAULT CURRENT_TIMESTAMP
);
'''
    def __init__(self, id=None, **kwargs):
        Session.__init__(self, id=id, **kwargs)
        self.storage_path = kwargs['storage_path']
            
    def getDb(self):
        if self.db is None:
#           self.db = sqlite3.connect(self.DB_STRING) # single Thread mode
            self.db = sqlite3.connect(self.DB_STRING, check_same_thread=False)
        return self.db
    
    @classmethod
    def setup(cls, **kwargs):
        """Set up the storage system for sqlite3-based sessions.
        Called once when the built-in tool calls sessions.init.
        """
        # overwritting default settings with the config dictionary values
        for k, v in kwargs.items():
            setattr(cls, k, v)
        
        cls.db_filename = cls.db_filename if cls.storage_file is None else cls.storage_file
        
        # print("\n*setup cls.storage_path", cls.storage_path)
        #check the file-path
        if os.path.isdir(cls.storage_path):
          cls.DB_STRING = os.path.join(cls.storage_path, cls.db_filename)
        else:
            cls.storage_path = os.path.abspath(os.path.dirname(__file__))
            cls.DB_STRING    = os.path.join(cls.storage_path, cls.db_filename)
        
        #check the table
        with cls.getDb(cls) as con:
            # sql2 = "DROP TABLE session"; # for re-create table
            # con.execute(sql2)
            
            sql = "SELECT count(name) FROM sqlite_master WHERE type='table' AND name='session'"
            if con.execute(sql).fetchone()[0] == 0:
                print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'), 'create session table.........')
                con.execute(cls.sqlCreate)

        cls.pickle_protocol = 0
    
    def _exists(self):
        # Select session data from table
        sql = 'SELECT data, expiration_time FROM session where sid = ?'
        with self.getDb() as con:
            return bool(con.execute(sql, [self.id,]).fetchone())

    def _load(self):
        # Select session data from table
        sql = '''SELECT data, expiration_time FROM session WHERE sid = ?'''
        with self.getDb() as con:
            rows = con.execute(sql, [self.id,]).fetchall()
            if not rows:
                return None

            pickled_data    = rows[0][0]
            expiration_time = rows[0][1]
            
            dt   = datetime.datetime.strptime(expiration_time, '%Y-%m-%d %H:%M:%S.%f')
#           data = json.loads(pickled_data.encode('utf-8'))
            data = json.loads(pickled_data)
            return (data, dt)

    def _save(self, expiration_time):
        ### pickled_data = pickle.dumps(self._data, pickle.HIGHEST_PROTOCOL)
        pickled_data = json.dumps(self._data)

        sql0 = 'SELECT data, expiration_time FROM session WHERE sid = ?'
        sql1 = 'INSERT OR IGNORE INTO session (sid, data, expiration_time) VALUES (?, ?, ?);'
        sql2 = 'UPDATE session SET data=?, expiration_time=? WHERE sid = ?;'
        with self.getDb() as con:
            rows = con.execute(sql0, [self.id,]).fetchone()
            if rows:
                con.execute(sql2, [pickled_data, expiration_time, self.id,])
            else:
                con.execute(sql1, [self.id, pickled_data, expiration_time,])
            con.commit()

    def _delete(self):
        print('------------ DELETING ---------------')
        with self.getDb() as con:
            sql = 'DELETE FROM session WHERE sid = ?'
            con.execute(sql, [self.id,])
            con.commit()

    # session id locks as done in RamSession

    def acquire_lock(self):
        """Acquire an exclusive lock on the currently-loaded session data."""
        self.locked = True
        self.locks.setdefault(self.id, threading.RLock()).acquire()
        cherrypy.log('Lock acquired.', 'TOOLS.SESSIONS')

    def release_lock(self):
        """Release the lock on the currently-loaded session data."""
        self.locks[self.id].release()
        self.locked = False

    def clean_up(self):
        """Clean up expired sessions."""
        sql = 'DELETE FROM session WHERE expiration_time < ?'
        with self.getDb() as con:
            con.execute(sql, [datetime.datetime.now(),])
            con.commit()

r'''
  conf = {
    'global': {
          'tools.sessions.storage_path'  : os.path.abspath(os.path.dirname(__file__)),
          'tools.sessions.storage_file'  : "ChSqliteSession2.db",
          'tools.sessions.storage_class' : SqliteSession,
          'tools.sessions.timeout'       : 1, #expire, minute(s)
          'tools.sessions.clean_freq'    : 1, #expired session cleanup
          'tools.sessions.on': True,
      },
  }
'''

