# Experiments
> Note: These experiments are done on Fedora but you should be able to do it on another distribution (e.g. Raspbian, Ubuntu). Please note that I didn't tested it.

## Appair joycons

I was able to appair them via Bluetooth by pressing the SYNC button on each joycon until the LEDs start cycling.
After that, the JoyCons can be found, named respectively `Joy-Con (L)` and `Joy-Con (R)`.

You should check that your Joycons LEDs are working. If they are not working, it may mean that the side part is broken, making your Joycon unable to detect if the SYNC button is pressed.

They are detected as two distinct game controllers but the LEDs will continue blinking.
I suspect that the JoyCons are waiting for an non-standard appairing validation message (probably their attributed controller number) but they are unable to get it so they keep cycling forever. Therefore, the inputs are still sent to the computer.

They also seem to be unable to reconnect once disconnected, probably because the appairing process is considered as failed on the JoyCons side.
Therefore, I was able to connect to them again by redoing the Bluetooth appairing process.

## Retrieve their `/dev/input` file

Joycons can't be found in `/dev/input/by-id` or `/dev/input/by-path` even if they are detected as controllers.
But we can still interact with the JoyCons using their `/dev/input/eventX` identifier.

You can retrieve their device identifier by reading `/proc/bus/input/devices`. You can copy these commands to find them: 

### Left Joycon:
```sh
cat /proc/bus/input/devices | awk -F "=" '/Joy-Con \(L\)/{for(a=0;a>=0;a++){getline;{if(/Handlers/==1){ print $NF;exit 0; }}}}'
```

### Right Joycon:
```sh
cat /proc/bus/input/devices | awk -F "=" '/Joy-Con \(R\)/{for(a=0;a>=0;a++){getline;{if(/Handlers/==1){ print $NF;exit 0; }}}}'
```

In my case, I have `event20` and `event21` as handlers (20 for left, and 21 for right).

If I am able to read the `/dev/input/event20` file, I could get every inputs in real time.

## Read input in Python with evdev

I made a small script to get the input of a single Joycon:

```py
# File: experiments/evdev/wait-for-input-one.py
import evdev

joycon = evdev.InputDevice('/dev/input/eventX')

# Which Joycon we are waiting for input
# Should be "Joy-Con (R)" or "Joy-Con (L)"
print(joycon.name)

# This loop will run forever and wait for events
for event in joycon.read_loop():
    print(evdev.categorize(event))
```

For simple cases it may be great, but I want to be able to read the input of both Joycons at the same time. To make it so, I will use the asyncio library and the Python async/await support added in Python 3.5.

```py
# File: experiments/evdev/wait-for-input-both.py
import asyncio, evdev

left_joycon = evdev.InputDevice('/dev/input/eventX')
right_joycon = evdev.InputDevice('/dev/input/eventX') # must be a different device

# This method will listen to the input of each Joycon
async def listen_to_events(joycon):
    # This for loop will run forever and wait for events
    async for event in joycon.async_read_loop():
        print(joycon.name, evdev.categorize(event), sep=': ')

# Execute the method asynchronously for each Joycon
for device in left_joycon, right_joycon:
    asyncio.ensure_future(listen_to_events(device))

# We start the async loop
loop = asyncio.get_event_loop()
loop.run_forever()

```

I noticed that when pressing ZR or ZL, `evdev.categorize(event)` will fail because the default controller mapping is incorrect.


## Read each Joycon input with the correct layout

You may have noticed that the layout does not correspond to the Joycons layout and that the detected input are mostly odd, and that some are not categorized by evdev and will throw an exception when pressed.

It is due to the specific Joycon layout not corresponding to the other known game controller.
We will need to do a manual mapping of these inputs instead of using the evdev ones.

```py
# Part of file: experiments/evdev/wait-for-input-layout-single.py

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
```

After that, we can use this mapping. I made a few other functions in order to get printable informations about the input (axis direction, button state).

```py
# Part of file: experiments/evdev/wait-for-input-layout-single.py

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
```

## Read inputs with the merged Joycons layout

Have two small controllers must be fine for many usages, but using both Joycons like a single controller would be a lot better.

This case would be a bit more complex as we must do two different mappings for the right and left Joycons. These mapping must take in account that some work must be done to the axis of each Joycon to point to the wanted direction.

For each Joycon, we must rotate each axis definition (horizontal will become vertical and vertical will become horizontal) and reverse the axis to make a correct rotation: we must invert the vertical (horizontal after rotation) on the left Joycon and the horizontal (vertical after rotation) on the right one.

It should make something like this:

**On the left Joycon:**

The `horizontal` axis will become the `vertical` one.

The `vertical` axis will become the inverted `horizontal` one.

**On the right Joycon:**

The `horizontal` axis will become the inverted `vertical` one (as opposite of the left Joycon one).

The `vertical` axis will become the `horizontal` one (as opposite of the left Joycon one).


I also removed the useless mappings (home button on the left Joycon, minus button on the right one, etc.) as they will never be called and are technically unusable.

In our mapping, it will look like this:

```py
# Part of file: experiments/evdev/wait-for-input-layout-merged.py

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
```

You can notice that I added a new layout flag argument for axis definitions that can be whether `NORMAL` or `INVERT`. When the axis layout is flagged inverted, it will trigger a little condition that will invert the axis value before we use it.

We will put this condition in `get_axis_direction` as we use this method to retrieve the axis direction.

```py
# Part of file: experiments/evdev/wait-for-input-layout-merged.py

def get_axis_direction(joycon, event):
    mapping = left_mapping if joycon is left_joycon else right_mapping

    # we map event to get its name
    mapped_event = mapping[event.code]

    #...

    layout_flag = mapped_event[2]

    direction = event.value

    if layout_flag is INVERT:
        direction = -direction

    #...
```

You can also notice that I added a `joycon` argument. It corresponds to the same `joycon` argument provided by `listen_to_events`.

We will edit `listen_to_events` to provide the Joycon to `get_axis_direction`. At the same time, we will also indicate which mapping we are using at the start of the function, depending if we are currently listening to the events of the left or right Joycon.

```py
# Part of file: experiments/evdev/wait-for-input-layout-merged.py

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
```

After that, the Joycon seems to be correctly mapped: if I press any button or move a joystick, the script is able to get it whether we are using the right or left Joycon.

## Read input in Python with pybluez (failed attempt)

I also tried to retrieve inputs with the pybluez discovery.
 
```py
# File: experiments/pybluez/list-controllers.py
import bluetooth
 
print(bluetooth.discover_devices(lookup_names=True, flush_cache=True))
```

I noticed that it does not work and that pybluez is actually unable to detect the Joycons at all.

I think that the hid driver may disallow pybluez from accessing the data directly.

I might investigate later.

## Read raw input from `/dev/hidrawX`

I also noticed that both the controllers are also available at hidraw devices and that the raw input could be read as binary data.

I was able to find which hidraw device was which Joycon by using this command:
```sh
grep "Joy-Con" /sys/class/hidraw/*/device/uevent | sed -E 's/^(.*)(hidraw[0-9]+)(.*)(Joy-Con \((L|R)\))/\4 => \/dev\/\2/'
```

In my case, the Joycons were `/dev/hidraw3` and `/dev/hidraw4`.

To make it more readable, I executed `od -t x1 /dev/hidrawX` to print the hexadecimal-formatted input of one of the controllers in real time.

_ _ _

# Dependencies to execute the scripts
If you would like to run the experiment scripts, you will need to install these dependencies:

 - python3.7
 - python3.7-devel (required to build some modules)
 - pipenv
 - bluez-libs-devel

Fedora:
```sh
sudo dnf install python3.7 python3.7-devel pipenv bluez-libs-devel
```

Debian/Ubuntu (scripts are untested but should work):
```sh
sudo apt-get install python3.7 python3.7-dev pipenv bluez libbluetooth-dev
```
_ _ _

After that, you need to clone this repo and open your terminal in the cloned repo.

You need to execute the following command in order to set up the virtual environment and install the dependencies:
```sh
pipenv install
```

> Note: You should only execute `pipenv` commands in the cloned repo.
