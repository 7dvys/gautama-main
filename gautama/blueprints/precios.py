from flask import Blueprint, render_template, request,jsonify,url_for
from .database import Database 
import pandas as pd
from gautama.db import get_db,init_db
from datetime import datetime
import numpy
import openpyxl
import json
import requests
import re

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


        rentabilidad = f"con rentabilidad: {rentabilidad}%"
        df = df.rename(columns={'con rentabilidad':rentabilidad})
        
        return df.head(10).round(2).to_dict('records')

    def generate_prerender_submit(self, formData, formFile):
        # Recuperar db y crear copia a temporal: 
        from sqlalchemy import create_engine

        conn = get_db()

        # Recuperamos los datos que nos interesan en un dataframe
        df = pd.read_sql('select id, nombre, codigo, descripcion, codigo_barras,precio,precio_final,costo_interno,rentabilidad,iva,tipo,id_rubro,observaciones,estado from cbProducts where tipo like "Producto"',con = conn)

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
        final_profit = profit/desc

        # Primero se le aplica el descuento al costo 
        df[cost] = df[cost]*desc
        df['precio'] = df[cost]*final_profit
        df['final'] = df['precio']*iva
        
        # renombraremos las columnas para que sean mas faciles de leer    
        df = df.rename(columns={cost:'costo',sku:'sku'})

        df.to_sql('temp_sheet',con=engine)
        
        # Ahora matcheamos ambas columnas tal que cumplan alguno de los requisitos
        query = f"select cb.id, cb.codigo,cb.nombre,  cb.descripcion,cb.observaciones, cb.codigo_barras,cb.precio as 'precio anterior',cb.iva,cb.precio_final as 'final anterior', (t.final/cb.precio_final*100)-100 as 'variacion',t.final, cb.id_rubro, t.sku as 'sku_proveedor', cb.tipo, cb.estado from temp_cbProducts cb join temp_sheet t on cb.codigo = t.sku or cb.descripcion = t.sku or cb.codigo_barras = '{vendorCod}.' || t.sku"

        filtered_df = pd.read_sql(query,con=engine)

        # En este punto ya esta filtrado, necesitamos codigos, por lo tanto usaremos la funcion de cbapi que nos permite pedirle cierta cantidad de codigos nuevos :) Parte que haremos al confirmar el submit!!
        
        return filtered_df.round(2).to_dict('records')

    def submit(self,dataForm):
        endpoint = f"{request.url_root[:-1]}{url_for('cbapi.code')}?lot_codes={len(dataForm)}"
        response = requests.get(endpoint)
        codes = response.content.decode('utf-8')
        codes = json.loads(codes)
        # Aqui verificaremos los codigos y lo enviamos uwu
        # Recorda las mayusculas que usa contabilium
        # id(se pasa como parámetro en la url), nombre*, Tipo*, Codigo*, Precio*, Iva*, Estado*, IDRubro, descripcion*, codigo_barras*, costo_interno*, precio_final*
        new_dataForm = {}
        for key in dataForm:
            row=dataForm[key]
            new_row = {}

            codigo = row['codigo']
            codigo_barras = row['codigo_barras']
            descripcion = row['descripcion']
            vendorCod = row['vendorCod']
            sku_proveedor = row['sku_proveedor']

            if not re.match(r'^0*[0-9]{6}$',codigo):
                new_row['Codigo']=codes.pop()
            else:
                new_row['Codigo']=codigo

            new_codigo_barras = f"{vendorCod}.{sku_proveedor}"
            if codigo_barras != new_codigo_barras:
                new_row['CodigoBarras'] = new_codigo_barras
            else:
                new_row['CodigoBarras'] = codigo_barras

            if descripcion != sku_proveedor:
                new_row['Descripcion'] = sku_proveedor
            else:
                new_row['Descripcion'] = descripcion

            if row['estado'] == 'Activo':
                new_row['Estado'] = 'A'
            else:
                new_row['Estado'] = 'P'
                
            new_row['Iva'] = row['iva']

            if(row['tipo'] == 'Producto'):
                new_row['Tipo'] = 'P' 
            else:
                new_row['Tipo'] = 'C' 

                
            new_row['Nombre'] = row['nombre']
            new_row['PrecioFinal'] = row['final']
            new_row['Precio'] = row['precio']
            new_row['CostoInterno'] = row['costo_interno']
            new_row['IdRubro'] = row['id_rubro']
            new_row['Id'] = row['id']

            ahora = datetime.now()
            texto_fecha_hora = ahora.strftime("%d/%m/%Y %H:%M")
            new_row['Observaciones'] = f"ult. Actualizacion: {texto_fecha_hora}"

            new_row['Rentabilidad']=row['rentabilidad']
            
            new_dataForm[key]= new_row

        endpoint = f"{request.url_root[:-1]}{url_for('cbapi.update_products')}"

        response = requests.post(url=endpoint,json=new_dataForm)
        return response.ok

    
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

@bp.route('/submit',methods=['POST'])
def submit():
    precios = Precios()
    data = request.get_json()
    return json.dumps(precios.submit(data))

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

    