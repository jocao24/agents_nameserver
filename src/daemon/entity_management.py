import time
import Pyro4
from Pyro4.errors import NamingError
from src.manage_logs.manage_logs_v_2 import ManagementLogs
from src.manage_logs.manage_logs_v_2 import LogType, ComponentType
from src.utils.emmit_log import log_execution_time, log_execution_time_with_message

def remove_duplicate_entities(nameserver: Pyro4.Proxy, management_logs: ManagementLogs):
    try:
        # Inicia el tiempo para la obtención de objetos registrados
        start_time = time.perf_counter()

        # Fetch the current list of registered objects in the nameserver
        registered_objects = nameserver.list()

        # Finaliza el tiempo para la obtención de objetos registrados
        end_time = time.perf_counter()
        log_execution_time_with_message(management_logs, "Fetched registered objects from nameserver", LogType.REQUEST, ComponentType.ENTITY_MANAGEMENT, start_time, end_time)

        # Dictionary to track the seen ids and names
        seen_ids_names = {}

        # Iterate through the registered objects to identify and remove duplicates
        try:
            for name, uri in registered_objects.items():
                start_time = time.perf_counter()  # Inicia el tiempo para cada iteración

                # Extracting the id and name based on your specific identifier structure
                parts = name.split("-")
                if len(parts) <= 1:
                    continue  # Skip this element if it does not follow the expected format

                # Check if the unique identifier has already been processed
                if name in seen_ids_names:
                    # If it exists, it"s considered a duplicate and should be removed
                    try:
                        log_execution_time(management_logs, f"Removing duplicate: {name} with URI {uri}", LogType.REMOVING_ENTITY, ComponentType.ENTITY_MANAGEMENT, time=0, success=True)
                        nameserver.remove(name)
                        end_time = time.perf_counter()  # Finaliza el tiempo para la eliminación
                        log_execution_time_with_message(management_logs, f"Duplicate {name} removed", LogType.END_REMOVING_ENTITY, ComponentType.ENTITY_MANAGEMENT, start_time, end_time)
                    except NamingError as e:
                        log_execution_time(management_logs, f"Error removing duplicate {name}: {e}", LogType.ERROR, ComponentType.ENTITY_MANAGEMENT, time=0, success=False)
                else:
                    # If it"s not a duplicate, add it to the seen ids and names
                    seen_ids_names[name] = name

                end_time = time.perf_counter()  # Finaliza el tiempo para cada iteración
                log_execution_time_with_message(management_logs, f"Processed entity {name}", LogType.REQUEST, ComponentType.ENTITY_MANAGEMENT, start_time, end_time)

        except Exception as e:
            log_execution_time(management_logs, f"Error while processing registered objects: {e}", LogType.ERROR, ComponentType.ENTITY_MANAGEMENT, time=0, success=False)
    except Exception as e:
        log_execution_time(management_logs, f"Error fetching registered objects from nameserver: {e}", LogType.ERROR, ComponentType.ENTITY_MANAGEMENT, time=0, success=False)
