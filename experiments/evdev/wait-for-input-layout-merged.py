import asyncio, evdev
from evdev import ecodes

left_joycon = evdev.InputDevice('/dev/input/event20')
right_joycon = evdev.InputDevice('/dev/input/event21')

# kind of input
BTN="button"
AXIS="axis"
OTHER="other"

# axis layout flags
INVERT="inverted"
NORMAL="normal"

left_mapping = {
#   keycode: (kind, name)
#   keycode: (AXIS, name, layout flag)
    0: (OTHER, None),
    4: (OTHER, "button press change"),
    16: (AXIS, "vertical", NORMAL),
    17: (AXIS, "horizontal", INVERT),
    304: (BTN, "left"),
    305: (BTN, "down"),
    306: (BTN, "up"),
    307: (BTN, "right"),
    308: (BTN, "sl"),
    309: (BTN, "sr"),
    312: (BTN, "minus"),
    314: (BTN, "l joystick"),
    317: (BTN, "screenshot"),
    318: (BTN, "l"),
    319: (BTN, "zl"),
}

right_mapping = {
#   keycode: (kind, name)
#   keycode: (AXIS, name, layout flag)
    0: (OTHER, None),
    4: (OTHER, "button press change"),
    16: (AXIS, "vertical", INVERT),
    17: (AXIS, "horizontal", NORMAL),
    304: (BTN, "a"),
    305: (BTN, "x"),
    306: (BTN, "b"),
    307: (BTN, "y"),
    308: (BTN, "sl"),
    309: (BTN, "sr"),
    313: (BTN, "plus"),
    315: (BTN, "r joystick"),
    316: (BTN, "home"),
    318: (BTN, "r"),
    319: (BTN, "zr"),
}

def get_button_state(event):
    if event.value is 0:
        return "keyup"
    if event.value is 1:
        return "keydown"
    if event.value is 2:
        return "keyheld"

def get_axis_direction(joycon, event):
    mapping = left_mapping if joycon is left_joycon else right_mapping
    
    # we map event to get its name and flag
    mapped_event = mapping[event.code]
    name = mapped_event[1]
    layout_flag = mapped_event[2]

    direction = event.value

    if layout_flag is INVERT:
        direction = -direction

    if direction is 0:
        return "center"

    if name is "vertical":
        if direction is 1:
            return "down"
        elif direction is -1:
            return "up"

    if name is "horizontal":
        if direction is 1:
            return "right"
        elif direction is -1:
            return "left"

# This method will listen to the input of each Joycon
async def listen_to_events(joycon):
    # retrieve the correct mapping for the wanted joycon
    mapping = left_mapping if joycon is left_joycon else right_mapping
    # This for loop will run forever and wait for events
    async for event in joycon.async_read_loop():
        # we map event to get its kind and name
        mapped_event = mapping[event.code]
        kind = mapped_event[0]
        name = mapped_event[1]

        if kind is BTN:
            print(joycon.name, name, get_button_state(event), sep=': ')
        elif kind is AXIS:
            print(joycon.name, get_axis_direction(joycon, event), sep=': ')
            

# Execute the method asynchronously for each Joycon
for device in left_joycon, right_joycon:
    asyncio.ensure_future(listen_to_events(device))

# We start the async loop
loop = asyncio.get_event_loop()
loop.run_forever()
