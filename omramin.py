#!/usr/bin/env python3
########################################################################################################################

import typing as T

import sys
import logging
import logging.config
import binascii
from datetime import datetime, timedelta
import asyncio

import garth
import inquirer
import click
import bleak
import garminconnect as GC

import utils as U
import omronconnect as OC
from regionserver import get_server_for_country_code

########################################################################################################################

__VERSION__ = "0.1.0"

_writeToGarmin = True
_overwrite = False
_bleMacAddrFilter = True

########################################################################################################################

DEFAULT_CONFIG = {
    "garmin": {},
    "omron": {
        "server": "https://data-sg.omronconnect.com",
        "devices": [],
    },
}

LOGGING_CONFIG = {
    "version": 1,
    "handlers": {
        "default": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "stream": "ext://sys.stderr",
        },
        "http": {
            "class": "logging.StreamHandler",
            "formatter": "http",
            "stream": "ext://sys.stderr",
        },
    },
    "formatters": {
        "default": {
            "format": "[%(asctime)s] [%(levelname).1s] %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "http": {
            "format": "[%(asctime)s] [%(levelname).1s] (%(name)s) - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "loggers": {
        "": {
            "handlers": ["default"],
            "level": logging.INFO,
            "formatter": "root",
        },
        "omron": {
            "handlers": ["default"],
            "level": logging.INFO,
            "formatter": "root",
        },
        "httpx": {
            "handlers": ["http"],
            "level": logging.WARNING,
        },
        "httpcore": {
            "handlers": ["http"],
            "level": logging.WARNING,
        },
    },
}

########################################################################################################################

logging.config.dictConfig(LOGGING_CONFIG)
L = logging.getLogger("")
# L.setLevel(logging.DEBUG)


########################################################################################################################
class LoginError(Exception):
    pass


def garmin_login() -> T.Optional[GC.Garmin]:
    config = U.json_load("config.json")
    gcCfg = config["garmin"]

    def get_mfa():
        return inquirer.text(message="> Enter MFA/2FA code")

    logged_in = False
    try:
        tokendata = gcCfg.get("tokendata", "")
        if not tokendata:
            raise FileNotFoundError

        email = gcCfg["email"]
        is_cn = gcCfg["is_cn"]
        gc = GC.Garmin(email=email, is_cn=is_cn, prompt_mfa=get_mfa)

        logged_in = gc.login(tokendata)
        if not logged_in:
            raise FileNotFoundError

    except (FileNotFoundError, binascii.Error):
        L.info("Garmin login")
        questions = [
            inquirer.Text(
                name="email",
                message="> Enter email",
                validate=lambda _, x: x != "",
            ),
            inquirer.Password(
                name="password",
                message="> Enter password",
                validate=lambda _, x: x != "",
            ),
            inquirer.Confirm(
                "is_cn",
                message="> Is this a Chinese account?",
                default=False,
            ),
        ]
        answers = inquirer.prompt(questions)
        if not answers:
            # pylint: disable-next=raise-missing-from
            raise LoginError("Invalid input")

        email = answers["email"]
        password = answers["password"]
        is_cn = answers["is_cn"]

        gc = GC.Garmin(email=email, password=password, is_cn=is_cn, prompt_mfa=get_mfa)
        logged_in = gc.login()
        if logged_in:
            gcCfg["email"] = email
            gcCfg["is_cn"] = is_cn
            gcCfg["tokendata"] = gc.garth.dumps()
            U.json_save("config.json", config)

    except garth.exc.GarthHTTPError:
        L.error("Failed to login to Garmin Connect", exc_info=True)
        return None

    if not logged_in:
        L.error("Failed to login to Garmin Connect")
        return None

    L.info("Logged in to Garmin Connect")
    return gc


def omron_login() -> T.Optional[OC.OmronConnect]:
    config = U.json_load("config.json")
    ocCfg = config["omron"]

    authResponse = None
    try:
        server = ocCfg.get("server", "")
        tokendata = ocCfg.get("tokendata", "")
        if not tokendata:
            raise FileNotFoundError

        oc = OC.get_omron_connect(server)
        authResponse = oc.refresh_oauth2(tokendata)
        if not authResponse:
            raise FileNotFoundError

    except FileNotFoundError:
        L.info("Omron login")
        questions = [
            inquirer.Text(
                name="email",
                message="> Enter email",
                validate=lambda _, x: x != "",
            ),
            inquirer.Password(
                name="password",
                message="> Enter password",
                validate=lambda _, x: x != "",
            ),
            inquirer.Text(
                "country",
                message="> Enter country code (e.g. 'US')",
                validate=lambda _, x: get_server_for_country_code(x),
            ),
        ]
        answers = inquirer.prompt(questions)
        if not answers:
            # pylint: disable-next=raise-missing-from
            raise LoginError("Invalid input")

        email = answers["email"]
        password = answers["password"]
        country = answers["country"]
        server = get_server_for_country_code(country)

        oc = OC.get_omron_connect(server)
        refreshToken = oc.login(email=email, password=password, country=country)
        if authResponse:
            tokendata = refreshToken
            ocCfg["email"] = email
            ocCfg["server"] = server
            ocCfg["tokendata"] = tokendata
            ocCfg["country"] = country
            ocCfg["server"] = server

            U.json_save("config.json", config)

    if authResponse:
        L.info("Logged in to OMRON connect")
        return oc

    L.error("Failed to login to OMRON connect")
    return None


def omron_ble_scan(macAddrsExistig: T.List[str]) -> T.List[str]:
    devsFound = {}

    async def scan():
        L.info("Scanning for Omron devices in pairing mode ...")
        L.info("Press Ctrl+C to stop scanning")
        while True:
            devices = await bleak.BleakScanner.discover(return_adv=True, timeout=1)
            devices = list(sorted(devices.items(), key=lambda x: x[1][1].rssi, reverse=True))
            for macAddr, (bleDev, advData) in devices:
                if macAddr in devsFound:
                    continue

                if macAddr in macAddrsExistig:
                    continue

                if _bleMacAddrFilter and not macAddr.startswith("00:5F:BF"):
                    continue

                serial = OC.ble_mac_to_serial(macAddr)
                devsFound[macAddr] = serial
                L.info(f"+ {macAddr} {bleDev.name} {serial} {advData.rssi}")

    try:
        asyncio.run(scan())
    except KeyboardInterrupt:
        pass

    return list(devsFound.keys())


def device_modify(identifier: T.Optional[str], devices: T.Any) -> bool:
    if not devices:
        L.info("No devices configured.")
        return False

    if not identifier:
        macaddrs = [d["macaddr"] for d in devices]
        identifier = inquirer.list_input("Select device to configure", choices=sorted(macaddrs))

    device = next((d for d in devices if d.get("name") == identifier or d.get("macaddr") == identifier), None)
    if not device:
        device = {"macaddr": identifier}

    questions = [
        inquirer.Text(
            name="name",
            message="Name of the device",
            default=device.get("name", ""),
        ),
        inquirer.List(
            "category",
            message="Type of the device",
            choices=["SCALE", "BPM"],
            default=device.get("category", "SCALE"),
        ),
        inquirer.List(
            "user",
            message="User number on the device",
            default=device.get("user", 1),
            choices=[1, 2, 3, 4],
        ),
        inquirer.List(
            name="enabled",
            message="Enable device",
            default=device.get("enabled", True),
            choices=[True, False],
        ),
    ]

    answers = inquirer.prompt(questions)
    if not answers:
        return False

    device["name"] = answers["name"] or OC.ble_mac_to_serial(device["macaddr"])
    device["category"] = answers["category"]
    device["user"] = answers["user"]
    device["enabled"] = answers["enabled"]
    if not any(d["macaddr"] == device["macaddr"] for d in devices):
        devices.append(device)

    return True


########################################################################################################################


def omron_sync_device_to_garmin(
    oc: OC.OmronConnect, gc: GC.Garmin, ocDev: OC.OmronDevice, startLocal=int, endLocal=int
) -> None:
    if endLocal - startLocal <= 0:
        L.info("Invalid date range")
        return

    startdateStr = datetime.fromtimestamp(startLocal).isoformat(timespec="seconds")
    enddateStr = datetime.fromtimestamp(endLocal).isoformat(timespec="seconds")

    L.info(f"Start synchronizing device {ocDev.name} from {startdateStr} to {enddateStr}")

    measurements = oc.get_measurements(ocDev, searchDateFrom=int(startLocal * 1000), searchDateTo=int(endLocal * 1000))
    if not measurements:
        L.info("No new measurements")
        return

    L.info(f"Downloaded {len(measurements)} entries from 'OMRON connect' for '{ocDev.name}'")

    # get measurements from Garmin Connect for the same date range
    if ocDev.category == OC.DeviceCategory.SCALE:
        gcData = garmin_get_weighins(gc, startdateStr, enddateStr)

    elif ocDev.category == OC.DeviceCategory.BPM:
        gcData = garmin_get_bp_measurements(gc, startdateStr, enddateStr)

    for measurement in measurements:
        # omron timestamp are UTC and in milliseconds
        tz = measurement.timeZone
        ts = measurement.measurementDate / 1000
        dtUTC = U.utcfromtimestamp(ts)
        dtLocal = datetime.fromtimestamp(ts, tz=tz)

        datetimeStr = dtLocal.isoformat(timespec="seconds")
        dateStr = dtLocal.date().isoformat()
        lookup = f"{dtUTC.date().isoformat()}:{dtUTC.timestamp()}"

        if ocDev.category == OC.DeviceCategory.SCALE:
            if lookup in gcData.values():
                if _overwrite:
                    L.warning(f"  ! '{datetimeStr}': removing weigh-in")
                    for samplePk, val in gcData.items():
                        if val == lookup and _writeToGarmin:
                            gc.delete_weigh_in(weight_pk=samplePk, cdate=dateStr)
                else:
                    L.info(f"  - '{datetimeStr}' weigh-in already exists")
                    continue

            wm = T.cast(OC.WeightMeasurement, measurement)

            L.info(f"  + '{datetimeStr}' adding weigh-in: {wm.weight} kg ")
            if _writeToGarmin:
                gc.add_body_composition(
                    timestamp=datetimeStr,
                    weight=wm.weight,
                    percent_fat=wm.bodyFatPercentage if wm.bodyFatPercentage > 0 else None,
                    percent_hydration=None,
                    visceral_fat_mass=None,
                    bone_mass=None,
                    muscle_mass=(
                        (wm.skeletalMusclePercentage * wm.weight) / 100 if wm.skeletalMusclePercentage > 0 else None
                    ),
                    basal_met=wm.restingMetabolism if wm.restingMetabolism > 0 else None,
                    active_met=None,
                    physique_rating=None,
                    metabolic_age=wm.metabolicAge if wm.metabolicAge > 0 else None,
                    visceral_fat_rating=wm.visceralFatLevel if wm.visceralFatLevel > 0 else None,
                    bmi=wm.bmiValue,
                )

        elif ocDev.category == OC.DeviceCategory.BPM:
            if lookup in gcData.values():
                if _overwrite:
                    L.warning(f"  ! '{datetimeStr}': removing blood pressure measurement")
                    for version, val in gcData.items():
                        if val == lookup and _writeToGarmin:
                            gc.delete_blood_pressure(version=version, cdate=dateStr)
                else:
                    L.info(f"  - '{datetimeStr}' blood pressure already exists")
                    continue

            bpm = T.cast(OC.BPMeasurement, measurement)

            notes = ""
            if bpm.movementDetect:
                notes = "Body Movement detected"
            if bpm.irregularHB:
                notes = f"{notes}, Irregular heartbeat detected"
            if not bpm.cuffWrapDetect:
                notes = f"{notes}, Cuff wrap error"
            if notes:
                notes = notes.lstrip(", ")

            L.info(f"  + '{datetimeStr}' adding blood pressure ({bpm.systolic}/{bpm.diastolic} mmHg, {bpm.pulse} bpm)")

            if _writeToGarmin:
                gc.set_blood_pressure(
                    timestamp=datetimeStr, systolic=bpm.systolic, diastolic=bpm.diastolic, pulse=bpm.pulse, notes=notes
                )


def garmin_get_bp_measurements(gc: GC.Garmin, startdate: str, enddate: str):
    # search dates are in local time
    gcData = gc.get_blood_pressure(startdate=startdate, enddate=enddate)

    # reduce to list of measurements
    _gcMeasurements = [metric for x in gcData["measurementSummaries"] for metric in x["measurements"]]

    # map of garmin-key:omron-key
    gcMeasurements = {}
    for metric in _gcMeasurements:
        # use UTC for comparison
        dtUTC = datetime.fromisoformat(f"{metric['measurementTimestampGMT']}Z")
        gcMeasurements[metric["version"]] = f"{dtUTC.date().isoformat()}:{dtUTC.timestamp()}"

    L.info(f"Downloaded {len(gcMeasurements)} bpm measurements from 'Garmin Connect'")
    return gcMeasurements


def garmin_get_weighins(gc: GC.Garmin, startdate: str, enddate: str):
    # search dates are in local time
    gcData = gc.get_weigh_ins(startdate=startdate, enddate=enddate)

    # reduce to list of allWeightMetrics
    _gcWeighins = [metric for x in gcData["dailyWeightSummaries"] for metric in x["allWeightMetrics"]]

    # map of garmin-key:omron-key
    gcWeighins = {}
    for metric in _gcWeighins:
        # use UTC for comparison
        dtUTC = U.utcfromtimestamp(int(metric["timestampGMT"]) / 1000)
        gcWeighins[metric["samplePk"]] = f"{dtUTC.date().isoformat()}:{dtUTC.timestamp()}"

    L.info(f"Downloaded {len(gcWeighins)} weigh-ins from 'Garmin Connect'")

    return gcWeighins


########################################################################################################################
# Add missing method to Garmin Connect API
def delete_blood_pressure(self, version: str, cdate: str):
    """Delete specific blood pressure measurement."""
    url = f"{self.garmin_connect_set_blood_pressure_endpoint}/{cdate}/{version}"
    L.debug("Deleting blood pressure measurement")

    return self.garth.request(
        "DELETE",
        "connectapi",
        url,
        api=True,
    )


setattr(GC.Garmin, "delete_blood_pressure", delete_blood_pressure)
########################################################################################################################


@click.group()
@click.version_option(__VERSION__)
def cli():
    """Sync data from 'OMRON connect' to 'Garmin Connect'"""


@cli.command(name="list")
def list_devices():
    """List all configured devices."""
    config = U.json_load("config.json")
    devices = config.get("omron", {}).get("devices", [])
    if not devices:
        L.info("No devices configured.")
        return

    for device in devices:
        L.info("-" * 40)
        L.info(f"Name:{' ':<8}{device.get('name', 'Unknown')}")
        L.info(f"MAC Address:{' ':<1}{device.get('macaddr', 'Unknown')}")
        L.info(f"Category:{' ':<4}{device.get('category', 'Unknown')}")
        L.info(f"User:{' ':<8}{device.get('user', 'Unknown')}")
        L.info(f"Enabled:{' ':<5}{device.get('enabled', 'Unknown')}")

    if devices:
        L.info("-" * 40)


@cli.command(name="config")
@click.option(
    "--device",
    "-d",
    "devName",
    required=True,
    help="Name or MAC address of the device to sync.",
)
def edit_device(devName: str):
    """Configure a device by name or MAC address."""

    config = U.json_load("config.json")
    devices = config.get("omron", {}).get("devices", [])
    if device_modify(devName, devices):
        U.json_save("config.json", config)
        L.info(f"Device {devName} configured successfully.")


@cli.command(name="add")
def add_device():
    """Add new Omron device."""
    config = U.json_load("config.json")
    devices = config.get("omron", {}).get("devices", [])

    macAddrs = [d["macaddr"] for d in devices]
    bleDevices = omron_ble_scan(macAddrs)
    if not bleDevices:
        L.info("No devices found.")
        return

    config = U.json_load("config.json")

    # make sure we don't add the same device twice
    tmp = bleDevices.copy()
    for scanned in bleDevices:
        if any(d["macaddr"] == scanned for d in devices):
            tmp.remove(scanned)
    bleDevices = tmp

    if not bleDevices:
        L.info("No new devices found.")
        return

    macaddr = inquirer.list_input("Select device", choices=sorted(bleDevices))
    if macaddr:
        new_devices = []
        new_devices.append({"macaddr": macaddr})

        if device_modify(macaddr, new_devices):
            config["omron"]["devices"].extend(new_devices)
            U.json_save("config.json", config)
            L.info("Device(s) added successfully.")


@cli.command(name="remove")
@click.option(
    "--device",
    "-d",
    "devName",
    required=True,
    help="Name or MAC address of the device to sync.",
)
def remove_device(devName: str):
    """Remove a device by name or MAC address."""
    config = U.json_load("config.json")
    devices = config.get("omron", {}).get("devices", [])

    if not devName:
        macaddrs = [d["macaddr"] for d in devices]
        devName = inquirer.list_input("Select device to remove", choices=sorted(macaddrs))

    device = next((d for d in devices if d.get("name") == devName or d.get("macaddr") == devName), None)

    if not device:
        L.info(f"No device found with identifier: {devName}")
        return

    devices.remove(device)
    U.json_save("config.json", config)
    L.info(f"Device '{devName}' removed successfully.")


@cli.command(name="sync")
@click.option(
    "--device",
    "-d",
    "devName",
    required=False,
    show_default=True,
    default="ALL",
    help="Name or MAC address of the device to sync.",
)
@click.option("--days", default=0, show_default=True, type=click.INT, help="Number of days to sync from today.")
def sync_device(devName: str, days: int):
    """Sync device(s) to Garmin Connect."""
    config = U.json_load("config.json")
    devices = config.get("omron", {}).get("devices", [])

    days = max(days, 0)

    today = datetime.combine(datetime.today().date(), datetime.max.time())
    start = today - timedelta(days=days)
    start = datetime.combine(start, datetime.min.time())

    try:
        gc = garmin_login()
    except LoginError:
        L.info("Failed to login to Garmin Connect.")
        return

    try:
        oc = omron_login()
    except LoginError:
        L.info("Failed to login to OMRON connect.")
        return

    if not oc or not gc:
        L.info("Failed to login to OMRON connect or Garmin Connect.")
        return

    if devName != "ALL":
        device = next((d for d in devices if d.get("name") == devName or d.get("macaddr") == devName), None)
        if not device:
            L.info(f"No device found matching: {devName}")
            return

        if not device["enabled"]:
            L.info(f"Device '{device['name']}' is disabled.")
            return

        ocDev = OC.OmronDevice(**device)
        omron_sync_device_to_garmin(oc, gc, ocDev, start.timestamp(), today.timestamp())
        L.info(f"Device '{device['name']}' successfully synced.")

    else:
        for device in devices:
            if not device["enabled"]:
                L.debug(f"Device '{device['name']}' is disabled.")
                continue

            ocDev = OC.OmronDevice(**device)
            omron_sync_device_to_garmin(oc, gc, ocDev, start.timestamp(), today.timestamp())
            L.info(f"Device '{device['name']}' successfully synced.")


########################################################################################################################

if __name__ == "__main__":
    if len(sys.argv) > 1:
        try:
            _ = U.json_load("config.json")

        except (FileNotFoundError, ValueError):
            L.info("Creating default config")
            U.json_save("config.json", DEFAULT_CONFIG)

    cli()

########################################################################################################################
