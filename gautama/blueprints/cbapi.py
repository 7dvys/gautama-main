from flask import Blueprint,render_template,session,jsonify,request
from gautama.db import get_db,init_db
import requests
from datetime import datetime

bp = Blueprint('cbapi',__name__,url_prefix='/cbapi')

@bp.route('/')
def cbapi_index():
    return render_template('cbapi.html',title='gautama - cbapi')

class Cbapi:

    token = None
    
    def __init__(self):
        if self.token is not None:
            self.check_token()
        else:
            self.set_token()
        pass

    def get_token(self):
        endpoint = '/token'

        data = {
            'grant_type':'client_credentials',
            'client_id':'rpm.empleados@outlook.es',
            'client_secret':'123456'
        }

        headers= {'Content-Type':'application/x-www-form-urlencoded'}

        response = self.do_request(endpoint=endpoint,data=data,headers=headers,method='post')

        if(response.status_code == requests.codes.ok):
            return response
        else:
            return None

    def check_token(self):
        if(self.token['expire_time'] <= datetime.timestamp(datetime.now())):
            self.set_token()

    def set_token(self):
        token = self.get_token().json()
        expire_time = token['expires_in']+datetime.timestamp(datetime.now())
        token.update({'expire_time':expire_time})
        session['token']=token
        self.token = session['token']

    def do_request(self,endpoint,params=None,headers={},token=None,data=None,method='get'):
        if self.token is not None:
            self.check_token()
        
        location = 'https://rest.contabilium.com'+endpoint
        
        if params is not None:
            params_string = ''
            for key,value in params.items():
                param_string+=f",{key}={value}"
            location += f"?{param_string[1:]}"
            
        
        if token is True:
            headers.update({'Authorization':'Bearer '+self.token['access_token']})

        request = getattr(requests,method)
        response = request(location,headers=headers,data=data)

        return response    

    def get_total_items_count(self):
        # Conseguir cantidad por deposito
        endpoint='/api/inventarios/getDepositos'
        response = self.do_request(endpoint=endpoint, token=True)
        id_deposito = response.json()[0]['Id']

        endpoint='/api/inventarios/getStockByDeposito?id='+str(id_deposito)
        response = self.do_request(endpoint=endpoint, token=True)
        total_items_count = response.json()['TotalItems']
        items_per_page=50

        n_pages = (total_items_count//items_per_page)
        final_page=1+n_pages
        final_page_size=total_items_count%items_per_page
        return n_pages,final_page,final_page_size
    
    def get_cbProducts(self,filtro="",type_return="tuple"):
        n_pages, final_page, final_page_size= self.get_total_items_count()
        all_products = []

        for page in range(n_pages):
            endpoint = f"/api/conceptos/search?pageSize=50&page={page+1}&filtro={filtro}"
            response = self.do_request(endpoint=endpoint, token=True)
            products=response.json()['Items']
            all_products.extend(products)

        endpoint = f"/api/conceptos/search?pageSize={final_page_size}&page={final_page}&filtro={filtro}"
        response = self.do_request(endpoint=endpoint, token=True)
        products=response.json()['Items']
        all_products.extend(products)


        for product in all_products:
            product.pop('CodigoOem',None)
            product.pop('PrecioFinal',None)
            product.pop('Precio',None)
            product.pop('Stock',None)
            product.pop('StockMinimo',None)
            product.pop('Foto',None)
            product.pop('IDMoneda',None)
            product.pop('ListasDePrecio',None)
            product.pop('Items',None)
            product.pop('Descripcion',None)
        
        if(type_return == 'tuple'):
            tupla = [tuple(product.values()) for product in all_products]
            return tupla
        else:
            return all_products
        
        
    def get_cbVendors(self):
        #Queda pendiente. Quizas sea mejor crear una Db e ingresarlo manualmente junto al email. Eso seria optimo para combinarlo con IMAP!
        pass
    
    def fill_cbProducts_db(self):
        data = self.get_cbProducts()
        self.exec_many_inserts(table='cbProducts',data=data,n_fields=12)

    def exec_many_inserts(self,table,data,n_fields):
        db = get_db()
        cur = db.cursor()
        cur.executemany(f"insert into {table} values({('?,'*n_fields)[:-1]})",data)
        db.commit()

    def exec_sql(self,sql):
        db = get_db()
        cur = db.cursor()
        execute = cur.execute(sql)
        rows =execute.fetchall()
        db.commit()
        return rows

    # Posible endpoint
    def update_tables(self):
        init_db()
        self.fill_cbProducts_db()

    # Endpoint
    def get_last_codigo(self):
        items = self.get_cbProducts(type_return='list')
        code = 0
        for item in items:
            if (item['Codigo'].isnumeric()):
                item_codigo = int(item['Codigo'])
                if(item_codigo > code):
                    code = item_codigo
        return code

    def get_new_code(self):
        items = self.get_cbProducts(type_return='list')
        items_six_digits = []
        for item in items:
            if(len(item['Codigo']) == 6 and item['Codigo'].isnumeric()):
                items_six_digits.append(item['Codigo'])
        items_six_digits.sort()
        
        def recursive_test(a):
            a_len = len(str(a))
            a = f"{'0'*(6-a_len)}{a}"
            if a in items_six_digits:
                if(a == '000000'):
                    a = 1
                else:
                    a = int(a.lstrip('0'))+1
                    
                return recursive_test(a)
            else:
                return a

        return recursive_test(0)

    # Endpoint
    def search_code(self,codigo):
        items = self.get_cbProducts(filtro=codigo,type_return='list')

        for item in items:
            if (item['Codigo'] == codigo):
                return item['Nombre']
        else:
            return False




@bp.route('/token')
def token():
    cbapi = Cbapi()
    cbapi.get_new_code()
    return 'hola'

@bp.route('/code',methods=['GET'])
def code():
    cbapi = Cbapi()
    
    for arg in request.args:
        match arg:
            case 'search':
                code = request.args.get('search','')
                response = cbapi.search_code(code)
                break
            case 'new_code':
                response = cbapi.get_new_code()
                break
            
    return jsonify(response)

