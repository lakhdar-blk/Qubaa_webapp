"""Project package.

PyMySQL is registered as MySQLdb so Django's MySQL backend works without
compiling mysqlclient (which needs system development headers). This keeps
the Render build fast and dependency-free.
"""

import pymysql

pymysql.install_as_MySQLdb()
