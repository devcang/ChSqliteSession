# ChSqliteSession

SQLite DB backend for CherryPy sessions.

[Re] davidmroth/SqliteSession (https://github.com/davidmroth/SqliteSession)


### Usage:

from ChSqliteSession import SqliteSession

.............


  conf = {  
    'global': {  
          'tools.sessions.storage_path'  : os.path.abspath(os.path.dirname(__file\__)),  
          'tools.sessions.storage_file'  : "ChSqliteSession2.db",  
          'tools.sessions.storage_class' : SqliteSession,  
          'tools.sessions.timeout'       : 1, #expire, minute(s)  
          'tools.sessions.clean_freq'    : 1, #expired session cleanup  
          'tools.sessions.on': True,  
      },  
  }  
  


