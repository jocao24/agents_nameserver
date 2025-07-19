import socket
import subprocess


# Devuelve la primera dirección IPv4 válida de la máquina. Intenta varios métodos para ser
# compatible con Windows, Linux y WSL.


def get_ip():
    try:
        # 1) Método habitual: socket UDP a DNS público
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            if ip and not ip.startswith("127."):
                return ip
        finally:
            s.close()

        # 2) hostname -I (Linux) -> varias IPs
        try:
            output = subprocess.check_output(["hostname", "-I"], text=True).strip()
            if output:
                # Seleccionar la primera IP que no sea loopback
                for candidate in output.split():
                    if candidate and not candidate.startswith("127."):
                        return candidate
        except Exception:
            pass

        # 3) socket.gethostbyname(hostname) (funciona en Windows)
        try:
            ip = socket.gethostbyname(socket.gethostname())
            if ip and not ip.startswith("127."):
                return ip
        except Exception:
            pass

        # Como último recurso, devolver loopback para evitar errores de None
        return "127.0.0.1"
    except Exception as e:
        print("Error obtaining local IP address:", e)
        return None
