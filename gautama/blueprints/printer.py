from flask import Blueprint,render_template,jsonify,json,request
from .cbapi import Cbapi

bp = Blueprint('printer',__name__,url_prefix='/printer')

@bp.route('/')
def printer_index():
    return render_template('printer.html',title="gautama - impresora")


# Printer Function
class Printer:
    def create_zpl(self,data):
        zpl_code=''
        l=0
        try:
            for e in data:
                code = e
                # '0'*(8 - len(str(e)))+str(e)
                for label in range(data[e]):
                    if(l==0):
                        zpl_code+="^XA\n^MD10\n^PR4\n^MTD\n^LH0,0\n^PW720\n^LL240\n"
                        zpl_code+=f"^FO-50,70^BY2^BCN,120,Y,N,N^FD{code}^FS \n"
                        
                        l+=1
                    else:
                        zpl_code+=f"^FO440,70^BY2^BCN,120,Y,N,N^FD{code}^FS \n"
                        zpl_code+="^XZ \n"
                        l=0
            if (l==1):
                zpl_code+="^XZ \n"
            print(zpl_code)
            return zpl_code
        except Exception as e:
            return 'error interno'

    def exec(self,zpl_code,printer_name="GAINSCHA_GS-2406T"):
        import subprocess

        # Nombre de la impresora
        # printer_name = 'GAINSCHA_GS-2406T'

        try:
            # Ejecuta el comando lpr para imprimir la cadena de texto ZPL
            result = subprocess.run(['lpr','-P', printer_name, '-o', 'raw'], input=zpl_code.encode(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            # 'lp', '-d', printer_name, '-o', 'raw', '-' opcion a probar!!
            if result.returncode != 0:
                # Si el comando falló, devolver una respuesta de error
                return result.stderr.decode(), None
            else:
                # Si el comando se ejecutó correctamente, devolver una respuesta de éxito
                return result.stdout.decode()
                pass
        except Exception as e:
            # Devuelve un mensaje de error genérico en formato JSON
            return "error interno: "+e

    def cancel_work(self,printer_name,job_id):
        import subprocess

        try:
            result = subprocess.run(['lprm','-P',printer_name,job_id],stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            if result.returncode != 0:
                return result.stderr.decode(), None
            else:
                return result.stdout.decode()
        except Exception as e:
            return 'error interno: '+e

    def cancel_all_works(self):
        import subprocess

        printer_name = 'GAINSCHA_GS-2406T'

        try:
            result = subprocess.run(['lprm','-P',printer_name,'-'],stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            if result.returncode != 0:
                return result.stderr.decode(), None
            else:
                return result.stdout.decode()
        except Exception as e:
            return 'error interno: '+e


    def get_works(self):
        import subprocess

        try:
            result = subprocess.run(['lpstat'],stdout = subprocess.PIPE, stderr=subprocess.PIPE)

            if result.returncode != 0:
                return result.stderr.decode(), None
            else:
                works = result.stdout.decode()
                works = works.splitlines()
                data = {}
                for work in range(len(works)):
                    work_split = works[work].split()
                    work_id = work_split[0].rsplit('-',1)
                    work_date = f"{work_split[4]}/{work_split[5]}/{work_split[6][2:]}, {work_split[7][0:5]}"
                    data[work_id[1]]={'printer':work_id[0],'date':work_date}
                return data
        except Exception as e:
            return 'error interno: '+e



    def print_label(self,data):
        zpl = self.create_zpl(data)
        print(zpl)
        return self.exec(zpl)

    def print_zpl(self,zpl_code,printer_name="GAINSCHA_GS-2406T"):
        return self.exec(zpl_code,printer_name)
    

#Flask Routes
@bp.route('/print',methods=["POST","GET"])
def print_endpoint():
    printer = Printer()
    for arg in request.args:
        match arg:
            case 'labels':
                json_data = json.loads(request.data)
                response = json.dumps(printer.print_label(json_data))
                break
            case 'zpl':
                json_data = json.loads(request.data)
                response = json.dumps(printer.print_zpl(json_data,"GAINSCHA_BIG"))
                break
            case 'cancelWork':
                work =request.args['cancelWork'].rsplit('-',1)

                work_printer =  str(work[0])
                work_id = str(work[1])

                response = printer.cancel_work(work_printer,work_id)
                break
            case 'cancelAllWorks':
                response = printer.cancel_all_works()
                break
            case 'getWorks':
                response = printer.get_works()
                break    
                
            case 'cancelCurrentWork':   
                response = printer.exec('^XA^MNN^XZ',"GAINSCHA_BIG")
                break

    return jsonify(response)

    

@bp.route('/works',methods=['GET'])
def pruebas():
    printer = Printer()
