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
# Turn on a device (bool type: use true/false)
PYTHONIOENCODING=utf-8 mijiaAPI set --dev_name "电脑" --prop_name "on" --value true

# Turn off
PYTHONIOENCODING=utf-8 mijiaAPI set --dev_name "电脑" --prop_name "on" --value false

# Adjust brightness (for lights — value is percentage 1-100)
PYTHONIOENCODING=utf-8 mijiaAPI set --dev_name "客厅灯" --prop_name "brightness" --value 50

# Set color temperature (for lights — value in kelvin, e.g. 2700=warm, 6500=cool)
PYTHONIOENCODING=utf-8 mijiaAPI set --dev_name "客厅灯" --prop_name "color-temperature" --value 4000

# Set AC to cooling mode (enum: use the numeric value from value-list, not text)
PYTHONIOENCODING=utf-8 mijiaAPI set --dev_name "空调" --prop_name "mode" --value 1
```

### Value Format Rules

The `--value` parameter format depends on the property type returned by `--get_device_info`:

| Type | Format | Example |
|------|--------|---------|
| `bool` | `true` or `false` | `--value true` |
| `uint` / `int` / `float` | Plain number within the `range` | `--value 26` |
| `string` | Plain text string | `--value "some text"` |
| Enum (has `value-list`) | **Must use the numeric value**, never the description text | `--value 1` (not `--value "制冷"`) |

For properties with a `value-list` (like AC mode, fan level), the JSON from `--get_device_info` lists all valid numeric values and their descriptions. Always pass the number:
- AC mode: `0`=auto, `1`=cool, `2`=dry, `3`=heat, `4`=fan
- AC fan-level: `0`=auto, `1`=low, `2`=medium, `3`=high

For brightness: the API spec shows range 1-65535, but the value is treated as percentage (1-100). Use percentage values like `--value 80` for 80% brightness.

For color temperature: the value is in kelvin. Warm light ≈ 2700K, neutral ≈ 4000K, cool/daylight ≈ 6500K. The light bulb does NOT support arbitrary RGB colors — only color temperature adjustment.

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

When the user asks to control a device, follow these steps **in order, without skipping**:

1. **List devices** if you don't know the device name or model: `mijiaAPI -l`
2. **Get device info** — this step is mandatory, do not skip it even if you think you know the property names: `mijiaAPI --get_device_info <model>`
3. **Read the JSON output** from step 2 to find the exact property name, type, range/value-list, and rw permission
4. **Set/get the property** using the property name and value format from step 2's output

For simple on/off requests (打开/关闭 + device name), the property is almost always `on` with value `true`/`false` for switches, plugs, and lights. But for anything beyond on/off — brightness, color temperature, mode, fan level, battery level, etc. — you must run step 2 first because property names and value ranges vary between models and are easy to get wrong.

## Common Device Models & Properties (Quick Reference)

This table is for rough reference only. Property names can differ from what's listed here. Always run `--get_device_info <model>` to get the exact property names before calling get/set.

| Device Type | Typical Models | Likely Properties (verify!) |
|------------|----------------|----------------|
| Smart Plug | cuco.plug.v3 | `on` (bool), `electric-power` (W), `power-consumption` |
| Light Bulb | yeelink.light.mbulb3 | `on` (bool), `brightness` (percentage), `color-temperature` (kelvin) |
| AC Partner | lumi.acpartner.mcn02 | `on` (bool), `mode` (enum 0-4), `target-temperature` (16-30°C), `fan-level` (enum 0-3) |
| Temp/Humidity Sensor | miaomiaoce.sensor_ht.t9 | `temperature` (°C), `relative-humidity` (%), `battery-level` (%) |
| Door Sensor | isa.magnet.dw2hl | `contact-state` (bool), `battery-level` (%) |
| Remote Switch | lumi.remote.mcn001 | configurable actions |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MIJIA_LOG_LEVEL` | `INFO` | Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL |
| `PYTHONIOENCODING` | system default | Set to `utf-8` to fix encoding issues |
