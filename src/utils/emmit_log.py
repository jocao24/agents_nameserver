from src.manage_logs.manage_logs_v_2 import LogType, ManagementLogs
from src.manage_logs.manage_logs_v_2 import ComponentType

def log_execution_time(management_logs: ManagementLogs, message: str, log_type: LogType, component_type: ComponentType, uuid_agent='', time = 0,  success=True):
        # Si viene una , en el mensaje, lo reemplazo por un ;
        message = message.replace(",", ";")
        uuid_agent = str(uuid_agent).replace("'{", "").replace("'}", "")
        management_logs.log_message(component_type, message=f"{message}", log_type=log_type, success = success, time_str=f"{time}", uuid_agent=uuid_agent)

def log_execution_time_with_message(management_logs: ManagementLogs, message:str, log_type: LogType, component_type: ComponentType, start_time, end_time, uuid_agent='0', success=True):
    # Si viene una , en el mensaje, lo reemplazo por un ;
    message = message.replace(",", ";")
    uuid_agent = str(uuid_agent).replace("{'", "").replace("'}", "")
    elapsed_time = end_time - start_time
    management_logs.log_message(component_type, message=f"{message} - {elapsed_time:.9f} seconds", log_type=log_type, success=success, time_str=f"{elapsed_time:.9f}", uuid_agent=uuid_agent)
