def show_separators(length=80):
    """Generates a dash separator."""
    return '-' * length


def show_center_text_with_separators(text, total_length=80):
    text_length = len(text)
    # Total space for separators
    separator_space = total_length - text_length
    # Separators on each side
    separators_left = separator_space // 2
    separators_right = separator_space - separators_left

    return ('-' * separators_left) + text + ('-' * separators_right)
