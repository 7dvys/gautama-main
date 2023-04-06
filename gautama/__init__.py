import os
from flask import Flask, render_template
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix

def create_app(test_config=None):
    app = Flask(__name__,instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path,'gautama.sqlite')
    )
    CORS(app)

    app.wsgi_app = ProxyFix(
        app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
    )
    
    if test_config is None:
        app.config.from_pyfile('config.py',silent=True)
    else:
        app.config.from_mapping(test_config)

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


    app.register_blueprint(printer.bp)
    app.register_blueprint(imap.bp)
    app.register_blueprint(cbapi.bp)

    modules = [
        {
            'titulo':'Printer',
            'descripcion':'No gastes tiempo e imprimi todas tus etiquetas de una vez!',
            'url_endpoint':'printer.printer_index'
        },
        # {
        #     'titulo':'Imap',
        #     'descripcion':'Desde aqui podra controlar las facturas que llegan al email!',
        #     'url_endpoint':'imap.imap_index'
        # },
        {
            'titulo':'Cbapi',
            'descripcion':'Integracion contabilium',
            'url_endpoint':'cbapi.cbapi_index'
        }
    ]

    @app.route('/')
    def index():
        return render_template('home.html',modules=modules,title='gautama - home')
    return app



