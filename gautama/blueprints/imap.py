import imaplib
import ssl

from flask import Blueprint,render_template

bp = Blueprint('imap',__name__,url_prefix='/imap')

@bp.route('/')
def imap_index():
    return render_template('imap.html',title="gautama - imap")


def init_imap():
    imap_server = 'imap.gmail.com' # o el servidor que quieras usar
    imap_port = 993
    username = 'fdr160102@gmail.com' # o el usuario que quieras usar
    password = 'rvafzbecjxujpnzb'

    # Crear el contexto ssl y la conexion
    context = ssl.create_default_context()
    imap_connection = imaplib.IMAP4_SSL(host=imap_server, port=imap_port, ssl_context=context)

    # Log
    imap_connection.login(username, password)

    # Seleccionar bandeja
    imap_connection.select('INBOX')

    # Buscar mensajes
    _, message_numbers = imap_connection.search(None, '(SUBJECT "prueba")')
    # Ver mensajes
    # for num in message_numbers[0].split():
    #     _, msg = imap_connection.fetch(num, '(RFC822)')
    #     print('Mensaje {}: {}'.format(num.decode(), msg[0][1].decode('utf-8')))

    # cerrar conexiones
    imap_connection.close()
    imap_connection.logout()




    

