gunicorn --workers=<número de workers> --bind=<dirección IP:puerto> gautama.run:app


utilizando sc.exe:
run_script.bat
@echo off
cd C:\ruta\hacia\el\directorio\de\tu\script
python nombre_de_tu_script.py

sc.exe create nombre_del_servicio binPath= "C:\ruta\hacia\el\archivo\run_script.bat" start= auto

sc.exe start nombre_del_servicio
