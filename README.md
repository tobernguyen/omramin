# omramin

## Synchronize data from _OMRON connect_ to _Garmin Connect_.

Supports weight and blood pressure measurements.

### Installing:

```
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

### Help:

```log
> python omramin
Usage: omramin.py [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  add      Add new OMRON device.
  config   Configure a device by name or MAC address.
  list     List all configured devices.
  remove   Remove a device by name or MAC address.
  sync     Sync device(s) to Garmin Connect.
  version  Show the version of the application.
```

### Adding a device:

Usually requires devices to be in pairing mode.

```log
 > python omramin.py add
[2024-11-03 09:53:34] [I] Creating default config
[2024-11-03 09:53:34] [I] Scanning for OMRON devices in pairing mode ...
[2024-11-03 09:53:34] [I] Press Ctrl+C to stop scanning
[2024-11-03 09:53:36] [I] + 00:5F:BF:xx:yy:zz None xxyyzzfeffbf5f00 -88
[?] Select device:
 > 00:5F:BF:xx:xx:xx

[?] Name of the device: my scale
[?] Type of the device:
 > SCALE
   BPM

[?] User number on the device:
 > 1
   2
   3
   4

[?] Enable device:
 > True
   False

[2024-11-03 09:54:18] [I] Device(s) added successfully.
```

### Synchronizing to Garmin Connect:

```log
> python omramin.py sync --days 5
[2024-11-03 09:56:36] [I] Garmin login
[?] > Enter email: user@garmin.connect
[?] > Enter password: ********
[?] > Is this a Chinese account? (y/N):
[2024-11-03 09:57:22] [I] Logged in to Garmin Connect
[2024-11-03 09:57:22] [I] OMRON login
[?] > Enter email: user@omron.connect
[?] > Enter password: ********
[2024-11-03 09:57:37] [I] Logged in to OMRON connect
[2024-11-03 09:57:37] [I] Start synchronizing device my scale from 2024-11-02T00:00:00 to 2024-11-03T00:00:00
[2024-11-03 09:57:38] [I] Downloaded 1 entries from 'OMRON connect' for 'my scale'
[2024-11-03 09:57:38] [I] Downloaded 1 weigh-ins from 'Garmin Connect'
[2024-11-03 09:57:38] [I]   + '2024-11-02:1730558158000' adding weigh-in: xx.y kg
[2024-11-03 09:57:38] [I] Device 'my scale' successfully synced.
[2024-11-03 09:57:38] [I] Downloaded 1 entries from 'OMRON connect' for 'my bpm'
[2024-11-03 09:57:38] [I] Downloaded 1 bpm measurements from 'Garmin Connect'
[2024-11-03 09:57:38] [I]   + '2024-11-02:1730556992000' adding blood pressure (xxx/yyy mmHg, zz bpm)
[2024-11-03 09:57:38] [I] Device 'my bpm' successfully synced.
```
