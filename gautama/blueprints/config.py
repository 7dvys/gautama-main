from flask import render_template, Blueprint, current_app,request, redirect, url_for
from cryptography.fernet import Fernet
import subprocess
import os
import json

bp = Blueprint('config',__name__,url_prefix='/config')

class Config:
    
    def __init__(self):
        self.config_path = os.path.join(current_app.instance_path,'config.json')
        self.config_flask_path = os.path.join(current_app.instance_path,'config-flask.json')
        if not os.path.exists(self.config_path):
            with open(self.config_path,'a') as file:
                file.write(json.dumps({
                    'cbUser':'',
                    'cbPassword':'',
                    'bigPrinter':'',
                    'smallPrinter':''
                }))
        master_key = self.get_flask_config()['SECRET_KEY']
        self.encrypter = Fernet(master_key)


    def get_printers(self):
        result = subprocess.run(['lpstat','-e'],stdout=subprocess.PIPE)
        printers = result.stdout.decode().splitlines()
        return printers

    def get_config(self):
        with open(self.config_path,'r') as file:
            data = file.read()
            return json.loads(data)

    def get_flask_config(self):
        with open(self.config_flask_path,'r') as file:
            data = file.read()
            return json.loads(data)

    def set_config(self,new_config={}):
        current_config = self.get_config()
        for config in new_config:
            value = new_config[config]

            if config == 'cbPassword':
                value = self.encrypt(value).decode()
            
            current_config[config]= value

        config = json.dumps(current_config)
        
        with open(self.config_path,'w') as file:
            file.write(config)

    def encrypt(self,subject):
        string_bytes = bytes(subject,'utf-8')
        token = self.encrypter.encrypt(string_bytes)
        return token

    def decrypt(self,token):
        return self.encrypter.decrypt(token).decode()

@bp.route('/')
def index():
    config = Config()
    printers_name = config.get_printers()
    current_config=config.get_config()
    return render_template('config.html',printers=printers_name,config=current_config,title='gautama - config')

@bp.route('/set',methods=['POST'])
def set_config():
    config = Config()
    post_data = request.form
    new_config = {}
    for data in post_data:
        if post_data[data] != '':
            new_config[data] = post_data[data]
    config.set_config(new_config)
    return redirect(url_for('index'))
    

