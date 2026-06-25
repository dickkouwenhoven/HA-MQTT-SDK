# Async Plugin Usage Example

This example shows how to build a production async integration using
`AsyncIntegrationPlugin`. It mirrors `examples/plugin_usage/` but uses
the async path throughout — `AsyncHASDK`, `AsyncMQTTClient`, and asyncio Tasks
instead of threads.

## File structure

```
async_plugin_usage/
├── main.py                  ← entry point: wires SDK + hub + plugin together
├── my_async_hub.py          ← simulated async hub client (replace with your real hub SDK)
├── my_async_hub_plugin.py   ← AsyncIntegrationPlugin implementation
└── README.md
```

## How it works

```
asyncio.run(main())
    │
    └── await sdk.run()
            │
            ├── await sdk.start()                     # connect MQTT
            │
            ├── await AsyncPluginManager.setup_all()
            │       └── await MyAsyncHubPlugin.setup(sdk)
            │               ├── await hub.connect()
            │               ├── await hub.get_devices()   # discover
            │               └── await sdk.register(...)   # publish MQTT discovery
            │
            └── await AsyncPluginManager.start_all()
                    └── await MyAsyncHubPlugin.start()
                            └── asyncio.create_task(_listen_for_events())

# While running (concurrent asyncio tasks):
hub event arrives  →  _listen_for_events()          →  await sdk.update_state()
HA command arrives →  MyAsyncHubPlugin.handle_command()  →  await hub.set_state()

await sdk.shutdown()
    └── await AsyncPluginManager.stop_all()
            └── await MyAsyncHubPlugin.stop()
                    ├── listen_task.cancel()
                    └── await hub.disconnect()
```

## Key differences from the sync example

| | Sync (`plugin_usage/`) | Async (`async_plugin_usage/`) |
|---|---|---|
| **Hub listener** | Background `threading.Thread` | asyncio `Task` |
| **Hub I/O** | Blocking calls | `await` calls |
| **Plugin methods** | `def setup/start/stop` | `async def setup/start/stop` |
| **SDK** | `HASDK` | `AsyncHASDK` |
| **MQTT client** | `PahoMQTTClient` | `AsyncMQTTClient` |
| **Entry point** | `main()` | `asyncio.run(main())` |

## Building your own async integration

1. Copy `my_async_hub_plugin.py` and rename it (e.g. `dirigera_plugin.py`)
2. Replace `MyAsyncHub` with your actual hub SDK
3. Implement the four async methods:
   - `setup(sdk)` — connect to hub, discover devices, register entities
   - `start()` — launch asyncio Task for WebSocket listener
   - `stop()` — cancel Task, disconnect hub
   - `handle_command(topic, payload)` — forward HA commands to hub
4. Register your plugin in `main.py`:

```python
sdk = AsyncHASDK(async_mqtt_client=client)
sdk.use_plugin("dirigera", DirigeraPlugin(hub))
await sdk.run()
```

## Running the example

```bash
python -m examples.async_plugin_usage.main
```

> **Note:** This example does not connect to a real MQTT broker or hub.
> Replace `MyAsyncHub` and `MQTTSettings` with real values to run against
> actual hardware.
