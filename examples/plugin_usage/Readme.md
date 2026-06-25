# Plugin Usage Example

This example shows how to build a production integration using `IntegrationPlugin`.

## File structure

```
plugin_usage/
├── main.py            ← entry point: wires SDK + hub + plugin together
├── my_hub.py          ← simulated hub client (replace with your real hub SDK)
├── my_hub_plugin.py   ← IntegrationPlugin implementation (the file to model after)
└── README.md
```

## How it works

```
HASDK.run()
    └── PluginManager.setup_all()
            └── MyHubPlugin.setup(sdk)
                    ├── hub.get_devices()           # discover devices
                    ├── sdk.create_entity(...)      # map to HA entities
                    └── sdk.register(entity, ...)   # publish MQTT discovery

    └── PluginManager.start_all()
            └── MyHubPlugin.start()
                    └── background thread started   # listen for hub events

# While running:
hub state change  →  MyHubPlugin._on_hub_state_change()  →  sdk.update_state()
HA command        →  MyHubPlugin.handle_command()         →  hub.set_state()

HASDK.shutdown()
    └── PluginManager.stop_all()
            └── MyHubPlugin.stop()
                    └── background thread stopped
```

## Building your own integration

1. Copy `my_hub_plugin.py` and rename it to match your hub (e.g. `hue_plugin.py`)
2. Replace `MyHub` with your actual hub SDK
3. Implement the four methods:
   - `setup(sdk)` — discover devices and register entities
   - `start()` — connect to hub, start listening
   - `stop()` — disconnect and clean up
   - `handle_command(topic, payload)` — forward HA commands to hub
4. Register your plugin in `main.py`:

```python
sdk.use_plugin("hue", HuePlugin(bridge))
sdk.run()
```

## Running the example

```bash
python -m examples.plugin_usage.main
```

> **Note:** This example does not connect to a real MQTT broker or hub.
> Replace `MyHub` and `MQTTSettings` with real values to run against
> actual hardware.
