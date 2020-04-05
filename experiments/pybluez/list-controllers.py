import bluetooth

print(bluetooth.discover_devices(lookup_names=True, flush_cache=True))