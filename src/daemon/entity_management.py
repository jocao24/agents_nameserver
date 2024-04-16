import Pyro4
from Pyro4.errors import NamingError

from src.manage_logs.manage_logs import ManagementLogs


def remove_duplicate_entities(nameserver: Pyro4.Proxy, management_logs: ManagementLogs):
    try:
        # Fetch the current list of registered objects in the nameserver
        registered_objects = nameserver.list()

        # Dictionary to track the seen ids and names
        seen_ids_names = {}

        # Iterate through the registered objects to identify and remove duplicates
        try:
            for name, uri in registered_objects.items():
                # Extracting the id and name based on your specific identifier structure
                parts = name.split("-")
                if len(parts) <= 1:
                    continue  # Skip this element if it does not follow the expected format

                # Check if the unique identifier has already been processed
                if name in seen_ids_names:
                    # If it exists, it"s considered a duplicate and should be removed
                    try:
                        management_logs.log_message(f"Removing duplicate: {name} with URI {uri}")
                        nameserver.remove(name)
                    except NamingError as e:
                        # print(f"Error removing duplicate {name}: {e}")
                        management_logs.log_message(f"Error removing duplicate {name}: {e}")
                else:
                    # If it"s not a duplicate, add it to the seen ids and names
                    seen_ids_names[name] = name
        except Exception as e:
            print(e)
    except Exception as e:
        print(e)
