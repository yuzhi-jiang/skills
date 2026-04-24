---
name: mijia-control
description: |
  Control Xiaomi Mijia smart home devices via the mijiaAPI CLI tool. Use this skill whenever the user wants to:
  - List, query, or control Mijia/Xiaomi smart devices (lights, plugs, sensors, AC, fans, etc.)
  - Check device status, temperature, humidity, power consumption
  - Turn devices on/off, adjust brightness, set temperature, etc.
  - Run Mijia scenes or execute natural language commands through Xiao Ai speaker
  - Set up or troubleshoot mijiaAPI installation
  Trigger on keywords: 米家, mijia, 小米设备, 智能家居, smart home, smart plug, smart light,
  开灯, 关灯, 打开空调, 设备列表, 温湿度, or any request to control IoT/smart devices from Xiaomi ecosystem.
---

# Mijia Smart Home Device Control

This skill controls Xiaomi/Mijia smart home devices using the `mijiaAPI` CLI tool.

## Prerequisites & Installation

Before using, ensure `mijiaAPI` is available. Check with:

```bash
mijiaAPI --version
```

### Install via uv/uvx (recommended)

If `uv` is installed, you can run without permanent install:

```bash
uvx mijiaAPI --help
```

Or install permanently into a project:

```bash
uv add mijiaAPI
```

### Install via pip

```bash
pip install mijiaAPI
```

### First-time authentication

The first run requires QR code login. Execute:

```bash
mijiaAPI -l
```

This will display a QR code in the terminal — scan it with the Mijia app (米家APP) to authenticate. Auth tokens are saved to `~/.config/mijia-api/auth.json` for subsequent use.

## Important: Use UTF-8 Encoding

On some systems (especially Windows), the CLI may output garbled text. Always prefix commands with:

```bash
PYTHONIOENCODING=utf-8 mijiaAPI <command>
```

Or use `uvx` which handles encoding better:

```bash
uvx mijiaAPI <command>
```

## Command Reference

### Discover devices

```bash
# List all devices (first step for any operation)
PYTHONIOENCODING=utf-8 mijiaAPI -l

# List all homes
PYTHONIOENCODING=utf-8 mijiaAPI --list_homes

# List all scenes
PYTHONIOENCODING=utf-8 mijiaAPI --list_scenes

# List consumable items (filters, bulbs, etc.)
PYTHONIOENCODING=utf-8 mijiaAPI --list_consumable_items
```

### Get device property

Before getting/setting properties, you need to know the device's property names. Look up the device model first:

```bash
# Get device spec by model (model comes from -l output)
PYTHONIOENCODING=utf-8 mijiaAPI --get_device_info <model>
```

This returns a JSON object with all available properties and actions, including their names, types, ranges, and read/write permissions.

Then read a property:

```bash
# By device name (matching Mijia APP name)
PYTHONIOENCODING=utf-8 mijiaAPI get --dev_name "客厅灯" --prop_name "on"

# Or by device ID
PYTHONIOENCODING=utf-8 mijiaAPI get --did 1113309969 --prop_name "on"
```

### Set device property

```bash
# Turn on a device
PYTHONIOENCODING=utf-8 mijiaAPI set --dev_name "电脑" --prop_name "on" --value true

# Turn off
PYTHONIOENCODING=utf-8 mijiaAPI set --dev_name "电脑" --prop_name "on" --value false

# Adjust brightness (for lights)
PYTHONIOENCODING=utf-8 mijiaAPI set --dev_name "客厅灯" --prop_name "brightness" --value 50
```

### Run scenes

```bash
# By scene name
PYTHONIOENCODING=utf-8 mijiaAPI --run_scene "睡眠模式"

# By scene ID
PYTHONIOENCODING=utf-8 mijiaAPI --run_scene "scene_id_here"
```

### Natural language via Xiao Ai speaker

```bash
PYTHONIOENCODING=utf-8 mijiaAPI --run "打开卧室灯"
PYTHONIOENCODING=utf-8 mijiaAPI --run "把空调温度调到26度" --wifispeaker_name "小爱音箱"
PYTHONIOENCODING=utf-8 mijiaAPI --run "关闭所有灯" --quiet
```

## Workflow for Device Control Requests

When the user asks to control a device, follow these steps:

1. **List devices** if you don't know the device name or model: `mijiaAPI -l`
2. **Get device info** to find available properties: `mijiaAPI --get_device_info <model>`
3. **Set the property** using the property name from step 2: `mijiaAPI set --dev_name "<name>" --prop_name <prop> --value <value>`

For simple on/off requests (打开/关闭 + device name), the property is almost always `on` with value `true`/`false` for switches, plugs, and lights.

## Common Device Models & Properties

| Device Type | Typical Models | Key Properties |
|------------|----------------|----------------|
| Smart Plug | cuco.plug.v3 | `on` (bool), `electric-power` (W), `power-consumption` |
| Light Bulb | yeelink.light.mbulb3 | `on` (bool), `brightness`, `color-temperature` |
| AC Partner | lumi.acpartner.mcn02 | `on`, `mode`, `target_temperature`, `fan_speed` |
| Temp/Humidity Sensor | miaomiaoce.sensor_ht.t9 | `temperature`, `humidity`, `battery-level` |
| Door Sensor | isa.magnet.dw2hl | `contact-state`, `battery-level` |
| Remote Switch | lumi.remote.mcn001 | configurable actions |

Note: Always verify available properties with `--get_device_info` since they vary by model.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MIJIA_LOG_LEVEL` | `INFO` | Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL |
| `PYTHONIOENCODING` | system default | Set to `utf-8` to fix encoding issues |
