import evdev

joycon = evdev.InputDevice('/dev/input/event20')

# Which Joycon we are waiting for input
# Should be "Joy-Con (R)" or "Joy-Con (L)"
print(joycon.name)

# We wait for input forever
for event in joycon.read_loop():
    # This for loop will run forever and wait for events
    print(evdev.categorize(event))