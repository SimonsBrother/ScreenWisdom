from dataclasses import dataclass, field

import screenwisdom.core.recording as rec
from screenwisdom.core.constants import InteractionType, MOUSE_MAX_DOUBLE_CLICK_DELAY_SECONDS, \
    KEYBOARD_MAX_TYPING_DELAY_SECONDS


@dataclass
class Interaction:
    """
    Represents part of a recording at a high level, so it can be turned into coherent english.

    Base attributes:
        :var interaction_type: the type of interaction, if it is clicking, double-clicking, typing etc.
        :var interaction_start_timestamp: seconds since epoch at which the interaction began.
        :var interaction_end_timestamp: seconds since epoch at which the interaction ended.
        :var input_events_associated: the InputEvent objects associated with the interaction.
         Should be sorted in ascending order by timestamp.
    """
    interaction_type: InteractionType
    input_events_associated: list[rec.InputEvent]
    interaction_start_timestamp: float = field(init=False)
    interaction_end_timestamp: float = field(init=False)

    def __post_init__(self):
        if len(self.input_events_associated) == 0:
            raise ValueError("No events associated.")

        # Get the starting timestamp from first input event
        self.interaction_start_timestamp = self.input_events_associated[0].timestamp

        # Get the ending timestamp from the last input event
        self.interaction_end_timestamp = self.input_events_associated[-1].timestamp


def interactions_from_mouse_recording(recording: list[rec.InputEvent]) -> [Interaction]:
    """
    Analyses a recording of InputEvents related to the mouse to create meaningful Interaction objects.
    :param recording: a recording of InputEvents.
    :return: a list of Interaction objects representing the recording.
    """
    # Return empty list immediately if recording empty
    if len(recording) == 0:
        return []

    interactions = []
    recording.sort(key=lambda e: e.timestamp)  # Sort the recording by timestamp

    related_click_events = []  # Store all clicks to look for double clicks

    # Data for keeping track of related scrolls
    previous_scroll_control = None
    previous_scroll_x_dir = None
    previous_scroll_y_dir = None
    current_scroll_sequence = []

    for i, event in enumerate(recording):
        """ DRAGGING AND CLICKS
        Detect dragging first. This will occur when mouse is pressed in one location, and released at another.
        If we find a mouse press event, then look for a mouse release event of the same button.
        If found, this is a mouse dragged event. A drag probably indicates a text selection.

        Clicks that are not drags should be noted in the clicks list, which will save time re-searching for clicks.
        """
        # Look for mouse being pressed. Record index via enumerate, so we know where to search for subsequent events.
        if isinstance(event, rec.MouseClick) and event.pressed:
            # A mouse button was clicked. Find the subsequent event the same button is released,
            # searching from the current event index to only consider subsequent events
            for subseq_event in recording[i:]:
                # Check for a mouse click event that has the same button, released this time.
                if (isinstance(subseq_event, rec.MouseClick) and subseq_event.button == event.button
                        and not subseq_event.pressed):
                    # Detect drag by checking if the mouse coordinates are different. Otherwise, event is a click
                    # TODO: Comparison may need to be "fuzzy" if mouse moves very slightly between clicks.
                    if event.coords != subseq_event.coords:
                        interactions.append(Interaction(InteractionType.MOUSE_DRAGGED, [event, subseq_event]))
                    else:
                        # Record as click, and store the related events for further analysis
                        related_click_events.append([event, subseq_event])
                    break
            # Mouse hasn't been released yet.
            # TODO handle trailing events

        """ MOUSE SCROLLS
        A scroll interaction should consist of all the scroll events in a single direction over the
        same control.
        """
        if isinstance(event, rec.MouseScroll):
            # Check if the scroll event is part of a sequence of scrolls, and seeing if the vertical and horizontal
            # scrolls are the same, and the same control is being scrolled.
            if (event.vertical_direction() == previous_scroll_y_dir
                    and event.horizontal_direction() == previous_scroll_x_dir
                    and event.context.control == previous_scroll_control):
                # Add scroll event to the current sequence
                current_scroll_sequence.append(event)
            else:
                # Check if the current scroll sequence is empty. This occurs on the first iteration involving scrolling.
                if len(current_scroll_sequence) != 0:
                    # Create complete interaction
                    interactions.append(Interaction(InteractionType.MOUSE_SCROLLED, current_scroll_sequence))
                # Start new sequence
                current_scroll_sequence = [event]
                previous_scroll_control = event.context.control
                previous_scroll_y_dir = event.vertical_direction()
                previous_scroll_x_dir = event.horizontal_direction()

    """ DOUBLE CLICKS
    Apparently, the time between clicks to register a double click is generally
    500ms, and apparently that's the Windows default. In future, this could adapt to the user.
    
    Easier to remove single clicks first, then what remains are double clicks.
    """
    single_click_indexes = []  # Store the indexes rather than changing the related_click_events size during the loop
    for i, click_event_group in enumerate(related_click_events):
        # For each click, if the previous click was too long ago, and the next click isn't soon enough, that's a
        # single click.
        single_click = True

        # Check previous click if not at start
        if i > 0:
            prior_click_press_event = related_click_events[i - 1][0]
            prior_click_time_difference = prior_click_press_event.timestamp - click_event_group[0].timestamp

            same_button = prior_click_press_event.button == click_event_group[0].button

            if prior_click_time_difference <= MOUSE_MAX_DOUBLE_CLICK_DELAY_SECONDS and same_button:
                single_click = False

        # Check next click if not at end
        if i < len(related_click_events) - 1:
            next_click_press_event = related_click_events[i + 1][0]
            next_click_time_difference = next_click_press_event.timestamp - click_event_group[0].timestamp

            same_button = next_click_press_event.button == click_event_group[0].button

            if next_click_time_difference <= MOUSE_MAX_DOUBLE_CLICK_DELAY_SECONDS and same_button:
                single_click = False

        if single_click:
            single_click_indexes.append(i)

    # Now pop at each index - however, sort indexes in reverse first,
    # otherwise the indexes won't match to the right value
    single_click_indexes.sort(reverse=True)
    for single_click_index in single_click_indexes:
        interaction = Interaction(InteractionType.MOUSE_CLICKED, related_click_events[single_click_index])
        interactions.append(interaction)

    # What remains are double clicks. There should therefore be an even number of clicks at this point. As everything
    # should be chronological, we can just splice in twos.
    for i in range(0, len(related_click_events) - 1, 2):
        interactions.append(Interaction(InteractionType.MOUSE_DOUBLE_CLICKED,
                                        related_click_events[i] + related_click_events[i+1]))

    return interactions


def interactions_from_keyboard_recording(recording: list[rec.InputEvent]) -> [Interaction]:
    """
    Analyses a recording of InputEvents related to the keyboard to create meaningful Interaction objects.
    :param recording: a recording of InputEvents.
    :return: a list of interactions representing the recording.
    """
    # Return empty list immediately if recording empty
    if len(recording) == 0:
        return []

    interactions = []
    recording.sort(key=lambda e: e.timestamp)  # Sort the recording by timestamp

    related_keypress_events = []  # Store all key presses to look for typing or individual presses.
    key_being_held = False  # Used to check if the key is being held down.

    for i, event in enumerate(recording):
        """ KEY PRESSES AND KEY HELD
        Detect when a key is pressed and subsequently released.
        If a key is pressed, and when looking for the release, the key appears to be pressed again, this indicates it
        is being held.
        """
        if isinstance(event, rec.KeyPress):
            # A key was pressed. Find the subsequent event the same key is released from subsequent events. Start from
            # i+1 to avoid including "event"; however, check if we're at the end of the loop
            if i < len(recording):
                for j, subseq_event in enumerate(recording[i+1:]):
                    # Check if we find the key being released
                    if isinstance(subseq_event, rec.KeyRelease) and subseq_event.key == event.key:
                        if key_being_held:
                            interactions.append(Interaction(InteractionType.SINGLE_KEY_HELD, [event, subseq_event]))
                            key_being_held = False
                        else:
                            related_keypress_events.append([event, subseq_event])
                        break

                    # Check if the event is the same key being pressed again, which would mean there was no release
                    # in between the presses - this occurs if the key is being held.
                    elif isinstance(subseq_event, rec.KeyPress) and subseq_event.key == event.key:
                        # To avoid a key being held being seen as a key being pressed again, replace event at this index
                        # with None.
                        recording[j] = None
                        key_being_held = True

    """ INDIVIDUAL KEY PRESSES AND TYPING
    Detect typing by comparing the time between key presses, which should be within some value. I tried typing very 
    slowly and timed it using a script, and the highest time between presses was 1.5 seconds.
    Typing can only consecutively occur on one control.
    
    It may be easier to extract individual key presses to leave typing sequences. An individual key press occurs if the
    key before and after are pressed outside of the typing delay.
    """

    individual_key_press_indexes = []
    for i, keypress_event_group in enumerate(related_keypress_events):
        # For each key, if the previous key was over 1.5 seconds ago, and the next key is in over 1.5 seconds, that's
        # an individual key press.
        individual_key_press = True

        # Check previous key if not at start
        if i > 0:
            prior_key_time_difference = related_keypress_events[i - 1][0].timestamp - keypress_event_group[0].timestamp
            if prior_key_time_difference <= KEYBOARD_MAX_TYPING_DELAY_SECONDS:
                individual_key_press = False

        # Check next key if not at end
        if i < len(related_keypress_events) - 1:
            next_key_time_difference = related_keypress_events[i + 1][0].timestamp - keypress_event_group[0].timestamp
            if next_key_time_difference <= KEYBOARD_MAX_TYPING_DELAY_SECONDS:
                individual_key_press = False

        if individual_key_press:
            individual_key_press_indexes.append(i)

    # We now have the indexes of individual key presses. To remove these, we can pop them one by one. However, if the
    # indexes are popped in ascending order, the indexes will need to be subtracted appropriately.
    # Alternatively, we can sort the index in reverse order, and pop one by one without subtraction.
    individual_key_press_indexes.sort(reverse=True)
    for i in individual_key_press_indexes:
        # Pop directly into an Interaction object, and add it
        individual_key_press_events = related_keypress_events.pop(i)
        interaction = Interaction(InteractionType.SINGLE_KEY_PRESSED, individual_key_press_events)
        interactions.append(interaction)

    """ TYPING
    At this point, there's no individual key presses. We just need to find consecutive sequences of key presses that
    occur on the same control that all have a time difference of 1.5 or under.
    
    Go through the related keypress events, and note indexes that split time based sequences.
    """

    typing_sequence_break_indexes = []
    previous_control_name = None
    for i, keypress_event_group in enumerate(related_keypress_events):
        # If at end, break
        if i == len(related_keypress_events) - 1:
            # Add final index, to include the last part of typing
            typing_sequence_break_indexes.append(i+1)
            break

        next_keypress_event_group = related_keypress_events[i + 1]
        subsequent_keypress_time_difference = next_keypress_event_group[0].timestamp - keypress_event_group[0].timestamp

        # TODO temporary solution to controls being incomparable
        control_different = keypress_event_group[0].context.closest_ctrl_name != previous_control_name

        # Check if time difference is greater than max allowed for typing, or if the control is different from previous
        # Note that the first iteration will add 0, because previous_control is initially None
        if subsequent_keypress_time_difference > KEYBOARD_MAX_TYPING_DELAY_SECONDS or control_different:
            typing_sequence_break_indexes.append(i)  # This is the index of the last key in the typing interaction
            if control_different:
                previous_control_name = keypress_event_group[0].context.closest_ctrl_name

    # Iterate over sequence break indexes, and splice
    for i in range(len(typing_sequence_break_indexes) - 1):
        typing_starting_index = typing_sequence_break_indexes[i]
        typing_ending_index = typing_sequence_break_indexes[i + 1]
        combined_press_events = []

        # Add all the InputEvents from the related keypresses within the indexes indicating typing
        for related_keypress_event in related_keypress_events[typing_starting_index:typing_ending_index]:
            combined_press_events.append(related_keypress_event[0])

        interaction = Interaction(InteractionType.KEYBOARD_TYPING, combined_press_events)
        interactions.append(interaction)

    interactions.sort(key=lambda e: e.interaction_start_timestamp)
    return interactions


# NOTE: this function is no longer used. Created at a point when I thought grouping the events would be useful.
def group_recording(recording: list[rec.InputEvent], attribute: str, from_context: bool) -> list[list[rec.InputEvent]]:
    """
    Takes a recording and splits into a list of lists of InputEvents, where all the events in each sublist have
    a same attribute, while retaining the order of the recording.
    :param recording: a recording of InputEvents, or part of a recording.
    :param attribute: the attribute of the InputEvents to group by, or if from_context is true,
    the attribute of the context attribute of the InputEvents to group by.
    :param from_context: if true, an attribute of the context attribute of the InputEvents will be used instead.
    :return: a list of lists of InputEvents, where all the events in each sublist have a same attribute.
    """
    # Return immediately if no recording data
    if len(recording) == 0:
        return []

    # Define function to easily get the required attribute from the events, so they can be easily compared
    def get_event_attr(inp_event: rec.InputEvent):
        if from_context:
            return getattr(inp_event.context, attribute)
        else:
            return getattr(inp_event, attribute)

    # Split into a list of lists of events grouped by the same attribute
    rec_grouped = []
    current_group = []
    current_group_value = get_event_attr(recording[0])  # Get the first event attribute to start

    for event in recording:
        # If the event attribute is the same as the previous event...
        if get_event_attr(event) == current_group_value:
            # ...add it to the current grouping list...
            current_group.append(event)
        else:
            # ...otherwise add the current list to the list of lists...
            rec_grouped.append(rec_grouped)
            # ...and reset the current group starting with the current event
            # and set the attribute value of the current group
            current_group = [event]
            current_group_value = get_event_attr(event)

    return rec_grouped


def translate_interaction(interaction: Interaction):
    events = interaction.input_events_associated

    match interaction.interaction_type:
        case InteractionType.MOUSE_DRAGGED:
            return (f"Mouse dragged from {events[0].coords} to {events[1].coords} using {events[0].button.name} mouse "
                    f"button.")

        case InteractionType.MOUSE_CLICKED:
            return f"Mouse clicked at {events[0].coords} using {events[0].button.name} mouse button."

        case InteractionType.MOUSE_DOUBLE_CLICKED:
            return f"Mouse double clicked at {events[0].coords} using {events[0].button.name} mouse button."

        case InteractionType.MOUSE_SCROLLED:
            horizontal_scroll_total = sum([event.dx for event in events])
            vertical_scroll_total = sum([event.dy for event in events])
            return (f"Mouse scrolled on {events[0].context.closest_ctrl_name} vertically {vertical_scroll_total} units"
                    f" and horizontally {horizontal_scroll_total} units.")

        case InteractionType.SINGLE_KEY_PRESSED:
            return f"Individual keyboard key pressed: {events[0].key}"

        case InteractionType.SINGLE_KEY_HELD:
            return f"Individual keyboard key held: {events[0].key}"

        case InteractionType.KEYBOARD_TYPING:
            return f"The user is typing: {''.join([event.key.char for event in events])}"


r = rec.MouseRecorder()
r2 = rec.KeyboardRecorder()
input()
i = interactions_from_mouse_recording(r.recording)
i2 = interactions_from_keyboard_recording(r2.recording)
for t in i:
    print(translate_interaction(t))

for t in i2:
    print(translate_interaction(t))
