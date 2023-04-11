from flask import Blueprint, render_template, request,jsonify
from .database import Database 
import pandas as pd
from gautama.db import get_db,init_db
import numpy
import openpyxl
import json

bp = Blueprint('precios',__name__,url_prefix='/precios')

# Funciones Generales
def getNumberForString(value):
    if not value.isnumeric():
        return int(ord(value)-97)
    else:
        return int(value)-1



class Precios:

    def update_tables(self):
        database = Database()
        database.update_tables()

    def get_sheets(self,excel_file):
        df_xlsx = pd.ExcelFile(excel_file)
        return df_xlsx.sheet_names

    def generate_prerender(self,formData,formFile):
        xlsx = formFile

        sku = getNumberForString(formData['sku'])
        cost = getNumberForString(formData['cost'])
        name = getNumberForString(formData['name'])

        df = pd.read_excel(xlsx,formData['sheet'],header=None,usecols=[sku,cost,name])

        # Convertir la columna "cost" en valores numéricos y reemplazar los valores no numéricos con NaN
        df[cost] = pd.to_numeric(df[cost], errors='coerce')

        # Rellenar los valores nan con 0
        df.fillna(value=0, inplace=True)

        profit = (float(formData['profit'])+100)/100

        rentabilidad = formData['profit']

        if(int(formData['desc']) > 0):
            desc = (100-int(formData['desc']))/100
            df['con descuento']=df[cost] * desc

            rentabilidad = round(((profit/desc*100)-100),2)
            

        if(formData['ivaCheck'] == 'false'):
            iva = (float(formData['iva'])+100)/100
            columns_names = {sku:'sku proveedor',cost:'costo',name:'nombre'}
            df['con iva']=df[cost] * iva
        else:
            columns_names = {sku:'sku proveedor',cost:'con iva',name:'nombre'}
            
        df = df.rename(columns=columns_names)

        df['con rentabilidad']=df['con iva']*profit


        rentabilidad = f"con rentabilidad: +{rentabilidad}%"
        df = df.rename(columns={'con rentabilidad':rentabilidad})
        
        return df.head(10).round(2).to_dict('records')

    def generate_prerender_submit(self, formData, formFile):
        # Recuperar db y crear copia a temporal: 
        from sqlalchemy import create_engine

        conn = get_db()

        # Recuperamos los datos que nos interesan en un dataframe
        df = pd.read_sql('select id, nombre, codigo, descripcion, codigo_barras,precio,precio_final,costo_interno,rentabilidad,iva,tipo,id_rubro,observaciones from cbProducts where tipo like "Producto"',con = conn)

        # Creamos la db in memory:
        engine = create_engine('sqlite:///:memory:')
        df.to_sql('temp_cbProducts',con=engine)

        # Agregamos la tabla de nuestro proveedor:
        xlsx = formFile

        sku = getNumberForString(formData['sku'])
        cost = getNumberForString(formData['cost'])

        df = pd.read_excel(xlsx,formData['sheet'],header=None,usecols=[sku,cost])

        # Convertir la columna "cost" en valores numéricos y reemplazar los valores no numéricos con NaN
        df[cost] = pd.to_numeric(df[cost], errors='coerce')

        # Rellenar los valores nan con 0
        df.fillna(value=0, inplace=True)

        # A partir de aqui crear tablas en funcion de las variables.
        # Constantes:
        vendorCod = formData['vendorCod']
        profit = round((float(formData['profit'])+100)/100,2)
        desc = round((100-float(formData['desc']))/100,2)
        iva = round((float(formData['iva'])+100)/100,2)
        final_profit = round(profit/desc,2)

        # Primero se le aplica el descuento al costo 
        df[cost] = df[cost]*desc
        df['precio'] = df[cost]*final_profit
        df['final'] = df['precio']*iva
        
        # renombraremos las columnas para que sean mas faciles de leer    
        df = df.rename(columns={cost:'costo',sku:'sku'})

        df.to_sql('temp_sheet',con=engine)
        
        # Ahora matcheamos ambas columnas tal que cumplan alguno de los requisitos
        query = f"select cb.id, cb.codigo,cb.nombre,  cb.descripcion, cb.codigo_barras, cb.costo_interno as 'old_costo',cb.rentabilidad,cb.precio as 'old_precio',cb.iva,cb.precio_final as 'old_final', (t.final/cb.precio_final*100)-100 as 'variacion',t.final, cb.id_rubro from temp_cbProducts cb join temp_sheet t on cb.codigo = t.sku or cb.descripcion = t.sku or cb.codigo_barras = '{vendorCod}.' || t.sku"

        filtered_df = pd.read_sql(query,con=engine)

        # En este punto ya esta filtrado, necesitamos codigos, por lo tanto usaremos la funcion de cbapi que nos permite pedirle cierta cantidad de codigos nuevos :) Parte que haremos al confirmar el submit!!
        
        return filtered_df.round(2).to_dict('records')

    def submit(self):
        pass

    
# Rutas
@bp.route('/')
def index():
    return render_template('precios.html',title='gautama - precios')

@bp.route('/upload_xlsx',methods=['POST'])
def upload():
    precios = Precios()
    file_xlsx = request.files['file']
    return jsonify(precios.get_sheets(file_xlsx))

@bp.route('/load_db')
def load():
    precios = Precios()
    precios.update_tables()
    return json.dumps('ok')

@bp.route('/submit')
def submit():
    pass

@bp.route('/prerender_submit',methods=['POST'])
def pre_render_submit():
    precios = Precios()
    formData = request.values
    formFile = request.files['file']
    return json.dumps(precios.generate_prerender_submit(formData,formFile))


@bp.route('/prerender',methods=['POST'])
def pre_render():
    precios = Precios()
    formData = request.values
    formFile = request.files['file']
    return json.dumps(precios.generate_prerender(formData,formFile))

    