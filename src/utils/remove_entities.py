import Pyro5


def remove_duplicate_entities(nameserver: Pyro5.nameserver.NameServer):
    # Fetch the current list of registered objects in the nameserver
    registered_objects = nameserver.list()

    # Dictionary to track the seen ids and names
    seen_ids_names = {}

    # Iterate through the registered objects to identify and remove duplicates
    for name, uri in registered_objects.items():
        # Extracting the id and name based on your specific identifier structure
        parts = name.split("-")
        if len(parts) > 1:
            id_entity, name_entity = parts[0], "-".join(parts[1:])
        else:
            continue  # Skip this element if it does not follow the expected format

        # Create a unique identifier based on id and name
        unique_identifier = f"{id_entity}-{name_entity}"

        # Check if the unique identifier has already been processed
        if unique_identifier in seen_ids_names:
            # If it exists, it's considered a duplicate and should be removed
            try:
                nameserver.remove(name)
            except NamingError as e:
                # print(f"Error removing duplicate {name}: {e}")
                log_message(f"Error removing duplicate {name}: {e}")
        else:
            # If it's not a duplicate, add it to the seen ids and names
            seen_ids_names[unique_identifier] = name
