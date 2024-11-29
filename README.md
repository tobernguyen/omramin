# omramin

Sync blood pressure and weight measurements from _OMRON connect_ to _Garmin Connect_.

OMRON Connect utilizes two distinct API versions:

    API v1: Primarily used in the Asia/Pacific region
    API v2: Implemented in other global regions

Note: The current implementation has been tested mostly with API v1. Feedback and testing for API v2 integration are welcomed.  
For testing and development purposes, it is strongly recommended to use a secondary Garmin Connect account.

## Features

Supports weight and blood pressure measurements.

## Table of Contents

-   [Installation](#installation)
-   [Updating](#update)
-   [Usage](#usage)
    -   [Adding a Device](#adding-a-device)
    -   [Synchronizing to Garmin Connect](#synchronizing-to-garmin-connect)
-   [Commands](#commands)
-   [Related Projects](#related-projects)
-   [Contributing](#contributing)
-   [License](#license)

### Installation

1. Clone the repository:

```
git clone https://github.com/bugficks/omramin.git
cd omramin
```

2. Create and activate a virtual environment:

```
python -m venv .venv
source .venv/bin/activate  # On Windows, use `.venv\Scripts\activate`
```

3. Install the required dependencies:

```
pip install -Ue .
```

### Update

```
git pull
source .venv/bin/activate  # On Windows, use `.venv\Scripts\activate`
pip install -Ue .
```

## Usage

### Adding a device:

Adding a device requires the MAC address of the device.

#### Interactively:

To add a new OMRON device, ensure it's in pairing mode and run:

```sh
omramin add
```

#### By MAC address:

If MAC address is known run e.g.:

```sh
  omramin add -m 00:11:22:33:44:55
  omramin add -m 00:11:22:33:44:55 --category scale --name "My Scale" --user 3
```

### Synchronizing to Garmin Connect:

To sync data from your OMRON device to Garmin Connect:

```sh
omramin sync --days 1
```

This will synchronize data for the today and yesterday. Adjust the --days parameter as needed.  
If this is first time you will be asked to enter login information for both _Garmin Connect_ and _OMRON connect_.

```log
[2024-11-14 08:04:20] [I] Garmin login
[?] > Enter email: user@garmin.connect
[?] > Enter password: *******************
[?] > Is this a Chinese account? (y/N):
[?] > Enter MFA/2FA code: xxxxxx
[2024-11-14 08:04:58] [I] Logged in to Garmin Connect
[2024-11-14 08:04:59] [I] Omron login
[?] > Enter email: user@omron.connect
[?] > Enter password: ********************
[?] > Enter country code (e.g. 'US'): XX
[2024-11-14 08:05:31] [I] Logged in to OMRON connect
[2024-11-14 08:05:31] [I] Start synchronizing device 'Scale HBF-702T' from 2024-11-13T00:00:00 to 2024-11-14T23:59:59
[2024-11-14 08:05:31] [I] Downloaded 2 entries from 'OMRON connect' for 'Scale HBF-702T'
[2024-11-14 08:05:32] [I] Downloaded 1 weigh-ins from 'Garmin Connect'
[2024-11-14 08:05:32] [I]   + '2024-11-14T07:56:33+07:00' adding weigh-in: xy.z kg
[2024-11-14 08:05:32] [I]   - '2024-11-13T07:36:01+07:00' weigh-in already exists
[2024-11-14 08:05:32] [I] Device 'Scale HBF-702T' successfully synced.
[2024-11-14 08:05:32] [I] Start synchronizing device 'BPM HEM-7600T' from 2024-11-13T00:00:00 to 2024-11-14T23:59:59
[2024-11-14 08:05:32] [I] Downloaded 4 entries from 'OMRON connect' for 'BPM HEM-7600T'
[2024-11-14 08:05:32] [I] Downloaded 3 bpm measurements from 'Garmin Connect'
[2024-11-14 08:05:32] [I]   + '2024-11-14T07:58:23+07:00' adding blood pressure (xxx/yy mmHg, zz bpm)
[2024-11-14 08:05:33] [I]   - '2024-11-13T19:57:30+07:00' blood pressure already exists
[2024-11-14 08:05:33] [I]   - '2024-11-13T15:05:18+07:00' blood pressure already exists
[2024-11-14 08:05:33] [I]   - '2024-11-13T07:46:41+07:00' blood pressure already exists
[2024-11-14 08:05:33] [I] Device 'BPM HEM-7600T' successfully synced.
```

### Commands

| Command | Description                                       |
| ------- | ------------------------------------------------- |
| add     | Add new OMRON device                              |
| config  | Configure a device by name or MAC address         |
| export  | Export device measurements to CSV or JSON format. |
| list    | List all configured devices                       |
| remove  | Remove a device by name or MAC address            |
| sync    | Sync device(s) to Garmin Connect                  |

For more details on each command, use:

```sh
omramin [COMMAND] --help
```

## Related Projects

-   [export2garmin](https://github.com/RobertWojtowicz/export2garmin): A project that allows automatic synchronization of data from Mi Body Composition Scale 2 and Omron blood pressure monitors to Garmin Connect.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the GPLv2 License.
