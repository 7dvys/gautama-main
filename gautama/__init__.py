import os
from flask import Flask, render_template, redirect, url_for, request
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix
from cryptography.fernet import Fernet
import json 

def create_app(test_config=None):
    
    app = Flask(__name__,instance_relative_config=True)
    app.config.from_mapping(
        DATABASE=os.path.join(app.instance_path,'gautama.sqlite')
    )
    CORS(app)

    config_flask_path = os.path.join(app.instance_path,'config-flask.json')
    config_path = os.path.join(app.instance_path,'config.json')

    # Si Flask Config no existe la crea con un secret Key
    if not os.path.exists(config_flask_path):
        with open(config_flask_path,'a') as file:
            master_key=Fernet.generate_key()
            master_key = json.dumps({'SECRET_KEY':master_key.decode()})
            file.write(master_key)
    
    # Utiliza la configuracion de Flask Config
    if test_config is None:
        config_flask_path = os.path.join(app.instance_path,'config-flask.json')
        app.config.from_file(config_flask_path,load=json.load)
    else:
        app.config.from_mapping(test_config)

    # Verificar que existan cbuser, cbpass, bigPrinter, smallPrinter
    def verify_config():
        if os.path.exists(config_path):
            with open(config_path,'r') as file:
                data = file.read()
                if data != "":
                    data = json.loads(data)
                    if(data['cbUser'] != '' and data['cbPassword'] != '' and data['bigPrinter'] != '' and data['smallPrinter'] != ''):
                        return True
                    else:
                        return False   
                else:
                    return False
        else:
            return False

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    from . import db
    db.init_app(app)

    # Blueprints 
    from .blueprints import cbapi
    from .blueprints import printer
    from .blueprints import imap
    from .blueprints import config
    from .blueprints import precios
    from .blueprints import database

    app.register_blueprint(printer.bp)
    app.register_blueprint(imap.bp)
    app.register_blueprint(cbapi.bp)
    app.register_blueprint(config.bp)
    app.register_blueprint(precios.bp)
    app.register_blueprint(database.bp)

    modules = [
        {
            'titulo':'Printer',
            'descripcion':'No gastes tiempo e imprimi todas tus etiquetas de una vez!',
            'url_endpoint':'printer.printer_index'
        },
        {
            'titulo':'Precios',
            'descripcion':'Actualiza todos tus precios a la velocidad de la luz!',
            'url_endpoint':'precios.index'
        }
        # {
        #     'titulo':'Imap',
        #     'descripcion':'Desde aqui podra controlar las facturas que llegan al email!',
        #     'url_endpoint':'imap.imap_index'
        # },
        # {
        #     'titulo':'Cbapi',
        #     'descripcion':'Integracion contabilium',
        #     'url_endpoint':'cbapi.cbapi_index'
        # }
    ]


    # función middleware checkeo de configuracion 
    @app.before_request
    def redirect_to_new_page():
        if(not verify_config()):
            redirect_url = url_for('config.index')
            post_url = url_for('config.set_config')

            if request.path != post_url and request.path != redirect_url and not (request.path.endswith('.svg') or request.path.endswith('.css')):
                return redirect(redirect_url)
  

    @app.route('/')
    def index():
        return render_template('home.html',modules=modules,title='gautama - home')
        # return redirect(url_for('config.index'))

    return app


