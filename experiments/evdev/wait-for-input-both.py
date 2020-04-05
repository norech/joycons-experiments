import asyncio, evdev

left_joycon = evdev.InputDevice('/dev/input/event20')
right_joycon = evdev.InputDevice('/dev/input/event21')

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
