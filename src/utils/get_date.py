from datetime import datetime


def print_current_time():
    current_time = datetime.now()
    formatted_time = current_time.strftime('%H:%M:%S.%f')[:-3]  # Hora:Minuto:Segundo.Milisegundo
    return formatted_time
