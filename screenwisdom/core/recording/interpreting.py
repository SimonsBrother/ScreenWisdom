from screenwisdom.core.recording.recording import InputRecorder, Interaction


def interactions_from_recording(input_rec: InputRecorder) -> [Interaction]:
    """
    Pops all events in the recording of an InputRecorder, and analyses it to create meaningful Interaction objects.
    :param rec: an InputRecorder to analyse the recording of.
    :return: a list of interactions representing the recording.
    """
    # Return empty list immediately if recording empty
    if len(input_rec.recording) == 0: return []

    rec = input_rec.pop_recording()
    interactions = []

    # Go through recording - split it by the context's application, then maybe by window title etc - allow for dragging

    # Split by process name into a list of lists of events of the process name
    rec_grouped_by_application = []  # Stores the recording as a list of lists of events of the same process name
    current_application_list = []  # Stores a sequence of events that occurred in order in the same process
    current_application = rec[0].context.process_name  # Get the first event process name to start

    for event in rec:
        # If the event is the same type as the previous event...
        if event.context.process_name == current_application:
            # ...add it to the current list...
            current_application_list.append(event)
        else:
            # ...otherwise add the current list to the list of lists
            rec_grouped_by_application.append(current_application_list)

            current_application = event.context.process_name
            current_application_list = [event]


def group_recording(attribute: str, ):
    ...


#note this can be combined with keyrelease to determine if a key was held.