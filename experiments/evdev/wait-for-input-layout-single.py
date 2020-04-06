import asyncio, evdev
from evdev import ecodes

left_joycon = evdev.InputDevice('/dev/input/event20')
right_joycon = evdev.InputDevice('/dev/input/event21')

# kind of input
BTN="button"
AXIS="axis"
OTHER="other"

mapping = {
#   keycode: (kind, name)
    0: (OTHER, None),
    4: (OTHER, "button press change"),
    16: (AXIS, "horizontal"),
    17: (AXIS, "vertical"),
    304: (BTN, "down"),
    305: (BTN, "right"),
    306: (BTN, "left"),
    307: (BTN, "up"),
    308: (BTN, "sl"),
    309: (BTN, "sr"),
    312: (BTN, "minus"),
    313: (BTN, "plus"),
    314: (BTN, "l joystick"),
    315: (BTN, "r joystick"),
    316: (BTN, "home"),
    317: (BTN, "screenshot"),
    318: (BTN, "r or l"),
    319: (BTN, "zr or zl"),
}

def get_button_state(event):
    if event.value is 0:
        return "keyup"
    if event.value is 1:
        return "keydown"
    if event.value is 2:
        return "keyheld"

def get_axis_direction(event):
    # we map event to get its name
    mapped_event = mapping[event.code]
    name = mapped_event[1]
    
    direction = event.value

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
    # This for loop will run forever and wait for events
    async for event in joycon.async_read_loop():
        # we map event to get its kind and name
        mapped_event = mapping[event.code]
        kind = mapped_event[0]
        name = mapped_event[1]

        if kind is BTN:
            print(joycon.name, name, get_button_state(event), sep=': ')
        elif kind is AXIS:
            print(joycon.name, get_axis_direction(event), sep=': ')


# Execute the method asynchronously for each Joycon
for device in left_joycon, right_joycon:
    asyncio.ensure_future(listen_to_events(device))

# We start the async loop
loop = asyncio.get_event_loop()
loop.run_forever()
