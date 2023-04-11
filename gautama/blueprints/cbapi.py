from flask import Blueprint,render_template,session,jsonify,request
import requests
from datetime import datetime
from .config import Config

bp = Blueprint('cbapi',__name__,url_prefix='/cbapi')

@bp.route('/')
def cbapi_index():
    return render_template('cbapi.html',title='gautama - cbapi')

class Cbapi:

    token = None
    
    def __init__(self):
        config = Config()
        self.cbUser = config.get_config()['cbUser']
        cbPassword = config.get_config()['cbPassword']
        self.cbPassword = config.decrypt(cbPassword)

        if self.token is not None:
            self.check_token()
        else:
            self.set_token()


    def get_token(self):
        endpoint = '/token'

        data = {
            'grant_type':'client_credentials',
            'client_id':self.cbUser,
            'client_secret':self.cbPassword
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


        n_pages = (total_items_count//items_per_page)+1 #entero
        return n_pages
    
    def get_cbProducts(self,filtro="",type_return="tuple"):
        n_pages = self.get_total_items_count()
        all_products = []

        for page in range(n_pages):
            endpoint = f"/api/conceptos/search?pageSize=50&page={page+1}&filtro={filtro}"
            response = self.do_request(endpoint=endpoint, token=True)
            products=response.json()['Items']
            all_products.extend(products)

        for product in all_products:
            product.pop('CodigoOem',None)
            product.pop('Stock',None)
            product.pop('StockMinimo',None)
            product.pop('Estado',None)
            product.pop('Foto',None)
            product.pop('IDMoneda',None)
            product.pop('AplicaRG5329',None)
            product.pop('ListasDePrecio',None)

        
        if(type_return == 'tuple'):
            tupla = [tuple(product.values()) for product in all_products]
            return tupla
        else:
            return all_products
        
        
    def get_cbVendors(self):
        #Queda pendiente. Quizas sea mejor crear una Db e ingresarlo manualmente junto al email. Eso seria optimo para combinarlo con IMAP!

        pass
    


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
    return cbapi.get_token().json()['access_token']
    

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



