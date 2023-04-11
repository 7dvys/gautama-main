from flask import Blueprint
from .cbapi import Cbapi 
from gautama.db import get_db,init_db
import json


bp = Blueprint('database',__name__,url_prefix='/database')

class Database:

    def fill_cbProducts_db(self):
        cbapi = Cbapi()
        data = cbapi.get_cbProducts()
        self.exec_many_inserts(table='cbProducts',data=data)

    def exec_many_inserts(self,table,data):
        db = get_db()
        cur = db.cursor()
        n_fields = len(data[0])
        
        cur.executemany(f"insert into {table} values({('?,'*n_fields)[:-1]})",data)
        db.commit()

    def exec_sql(self,sql):
        db = get_db()
        cur = db.cursor()
        execute_sql = cur.execute(sql)
        rows =execute_sql.fetchall()
        db.commit()
        return rows

    # Posible endpoint
    def update_tables(self):
        init_db()
        self.fill_cbProducts_db()


    
