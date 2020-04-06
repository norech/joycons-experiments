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
