import csv
from datetime import datetime
from enum import Enum, auto
import os
import threading
import uuid

from src.security.access_coordinator.data_management import DataManagement

class LogType(Enum):
    ENCRYPTION = auto()
    DECRYPTION = auto()
    REGISTRATION = auto()
    PREREGISTRATION = auto()
    UPLOAD = auto()
    START_SESSION = auto()
    KEY_GENERATION = auto()
    SHARED_KEY = auto()
    SERIALIZATION = auto()
    CONNECTION = auto()
    ERROR = auto()
    DAEMON_START = auto()
    OTHER = auto()
    REQUEST = auto()
    RESPONSE = auto()
    AUTHENTICATION = auto()
    VALIDATION = auto()
    MODIFICATION = auto()
    QUERY = auto()


class ComponentType(Enum):
    SECURITY_MANAGEMENT = auto()
    AGENT_CONNECTION_HANDLER = auto()
    SESSION_MANAGER = auto()
    NAME_SERVER = auto()
    ACCESS_COORDINATOR = auto()
    IP_MANAGER = auto()
    SHARED_KEY_MANAGER = auto()
    NAMESERVER_CONTROL = auto()
    GATEWAY_MANAGER = auto()
    ENTITY_MANAGEMENT = auto()
    DAEMON = auto()
    YELLOW_PAGE_INTEGRATION = auto()
    TOTP_MANAGER = auto()
    NAMESERVER = auto()
    MENU = auto()


class LogEntry:
    def __init__(self, session_id: str, timestamp: datetime, component: ComponentType, message: str, log_type: LogType, success: bool = True):
        self.session_id = session_id
        self.timestamp = timestamp
        self.component = component
        self.message = message
        self.log_type = log_type
        self.success = success

    def __str__(self):
        return f"{self.session_id},{self.timestamp.isoformat()},{self.component.name},{self.message},{self.log_type.name},{self.success}\n"
    
    def formatted_str(self):
        success_str = "Success" if self.success else "Failure"
        return f"{self.timestamp.isoformat()} -- {self.component.name} -- {self.message} -- {self.log_type.name}, {success_str}"
    
    def display_str(self):
        time_str = self.timestamp.strftime("%H:%M:%S.%f")
        success_str = "Success" if self.success else "Failure"
        return f"{time_str} - {self.component.name} - {self.message} - {self.log_type.name}, {success_str}"


class ManagementLogs:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, data_management_instance: DataManagement):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(ManagementLogs, cls).__new__(cls)
                    cls._instance._initialize(data_management_instance)
        return cls._instance

    def _initialize(self, data_management_instance: DataManagement):
        self.data_management_instance = data_management_instance
        self.session_id = ''
        self.log_buffer = []
        self.flush_interval = 5  # time in seconds
        self._start_periodic_flush()

    def _start_periodic_flush(self):
        threading.Timer(self.flush_interval, self._flush_buffer).start()

    def _flush_buffer(self):
        with self._lock:
            if self.log_buffer:
                current_data = self.data_management_instance.load()
                if 'logs' in current_data:
                    current_data['logs'] += ''.join([str(log) for log in self.log_buffer])
                else:
                    current_data['logs'] = ''.join([str(log) for log in self.log_buffer])
                self.data_management_instance.save(current_data)
                self.log_buffer = []  # Clear the buffer after saving
        self._start_periodic_flush()  
    
    def log_message(self, component: ComponentType, message: str, log_type: LogType, success: bool = True):
        timestamp = datetime.now()
        log_entry = LogEntry(self.session_id, timestamp, component, message, log_type, success)
        with self._lock:
            self.log_buffer.append(log_entry)
        return str(log_entry)

    def start_new_session_log(self):
        """Logs the start of a new session."""
        if not self.session_id:
            self.session_id = str(uuid.uuid4())
            session_start_message = f"New session started with UUID: {self.session_id}"
            self.log_message(ComponentType.SESSION_MANAGER, session_start_message, LogType.START_SESSION, True)

    def get_all_logs(self) -> str:
        data = self.data_management_instance.load()
        logs = data.get('logs', '') + ''.join([str(log) for log in self.log_buffer])
        return logs
    
    def get_current_session_logs(self) -> str:
        """Retrieve logs of the current session."""
        data = self.data_management_instance.load()
        all_logs = data.get('logs', '') + ''.join([str(log) for log in self.log_buffer])
        current_logs = [log for log in all_logs.strip().split('\n') if log.startswith(self.session_id)]
        formatted_logs = '\n'.join(current_logs)
        return f"Logs:\n{formatted_logs}"
    
    def export_logs_to_csv(self):
        """Export all logs to a CSV file."""
        data = self.data_management_instance.load()
        all_logs = data.get('logs', '') + ''.join([str(log) for log in self.log_buffer])
        log_entries = [log.split(',') for log in all_logs.strip().split('\n')]

        headers = ["session_id", "timestamp", "component", "message", "log_type", "success"]
        # Obtén la ruta del directorio actual (el que contiene el script que se está ejecutando)
        current_dir = os.path.dirname(os.path.abspath(__file__))

        # Navega un nivel hacia atrás para ubicarte en el directorio que contiene 'src'
        project_root = os.path.abspath(os.path.join(current_dir, os.pardir, os.pardir))

        # Concatena la carpeta 'data' a la ruta del proyecto
        data_dir = os.path.join(project_root, 'data') + os.sep

        
        with open(f'{data_dir}logs_ns.csv', mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(headers)
            writer.writerows(log_entries)
