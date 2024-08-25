
# NameServer

Este proyecto NameServer está diseñado para ser ejecutado en diferentes sistemas operativos, incluyendo Windows, Linux y macOS. A continuación, se detallan los pasos para configurar y ejecutar el proyecto en cada uno de estos sistemas.

## Requisitos previos

- Python 3.x debe estar instalado en el sistema. Puedes descargarlo desde [python.org](https://www.python.org/downloads/).
- `pip` debe estar instalado (generalmente viene preinstalado con Python).
- Un entorno virtual será utilizado para gestionar las dependencias del proyecto.

## Instrucciones para Windows

1. **Crear un entorno virtual**:

   Abre una terminal (cmd) y navega a la carpeta raíz del proyecto. Luego, ejecuta el siguiente comando:

   ```bash
   python -m venv venv
   ```

2. **Activar el entorno virtual**:

   ```bash
   .\venv\Scripts\activate
   ```

3. **Instalar las dependencias**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Ejecutar el proyecto**:

   ```bash
   python main.py
   ```

## Instrucciones para Linux

1. **Crear un entorno virtual**:

   Abre una terminal y navega a la carpeta raíz del proyecto. Luego, ejecuta el siguiente comando:

   ```bash
   python3 -m venv venv
   ```

2. **Activar el entorno virtual**:

   ```bash
   source venv/bin/activate
   ```

3. **Instalar las dependencias**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Ejecutar el proyecto**:

   ```bash
   python3 main.py
   ```

## Instrucciones para macOS

1. **Crear un entorno virtual**:

   Abre una terminal y navega a la carpeta raíz del proyecto. Luego, ejecuta el siguiente comando:

   ```bash
   python3 -m venv venv
   ```

2. **Activar el entorno virtual**:

   ```bash
   source venv/bin/activate
   ```

3. **Instalar las dependencias**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Ejecutar el proyecto**:

   ```bash
   python3 main.py
   ```

## Observaciones

- Dentro de la carpeta raíz del proyecto, se encuentra una subcarpeta llamada `data`. En esta carpeta se almacenan los códigos QR para la autenticación a través de TOTP, los cuales deben ser escaneados con Google Authenticator o Microsoft Authenticator para el proceso de registro de agentes.

- También dentro de `data`, se encuentra un archivo encriptado que contiene toda la información encriptada del NameServer, incluyendo conexiones, logs, etc.

- Los archivos de logs también se almacenan en la carpeta `data` cuando se exportan.

- Asegúrate de tener los permisos adecuados para acceder y manipular los archivos dentro de la carpeta `data`.

- Para desactivar el entorno virtual después de usarlo, simplemente ejecuta el comando `deactivate` en la terminal.

## Notas adicionales

- En caso de necesitar nuevas dependencias, recuerda añadirlas al archivo `requirements.txt` y ejecutar `pip install -r requirements.txt` nuevamente para mantener el entorno virtual actualizado.
