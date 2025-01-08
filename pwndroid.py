import json
import logging
import requests

import pwnagotchi.plugins as plugins
import pwnagotchi.ui.fonts as fonts
from pwnagotchi.ui.components import LabeledValue
from pwnagotchi.ui.view import BLACK


class GPS(plugins.Plugin):
    __author__ = "Jayofelony"
    __version__ = "1.0.1"
    __license__ = "GPL3"
    __description__ = "Plugin for the companion app PwnDroid to display GPS data on the Pwnagotchi screen. And make the BT tethering connection."

    LINE_SPACING = 10
    LABEL_SPACING = 0

    def __init__(self):
        self.running = False
        self.coordinates = None
        self.options = dict()

    def on_loaded(self):
        logging.info("[PwnDroid] Plugin loaded")

    def on_ready(self, agent):
        # Check connection to 192.168.44.1:4555
        try:
            response = requests.get("http://192.168.44.1:8080")
            response.raise_for_status()
            logging.info("Successfully connected to 192.168.44.1:8080")
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to connect to 192.168.44.1:8080")
            self.running = False
        self.running = True

    def get_location_data(self, server_url):
        try:
            response = requests.get(server_url)
            response.raise_for_status()  # Raise an exception for HTTP errors
            return response.json()  # Parse the JSON response
        except requests.exceptions.RequestException as e:
            logging.warning(f"Error connecting to the server: {e}")
            return None

    def on_handshake(self, agent, filename, access_point, client_station):
        if self.running:
            server_url = f"http://192.168.44.1:8080"
            location_data = self.get_location_data(server_url)
            if location_data:
                logging.info("Location Data:")
                logging.info(f"Latitude: {location_data['latitude']}")
                logging.info(f"Longitude: {location_data['longitude']}")
                logging.info(f"Altitude: {location_data['altitude']}")
                logging.info(f"Speed: {location_data['speed']}")
            else:
                logging.info("Failed to retrieve location data.")
            if self.running:
                self.coordinates = location_data
                gps_filename = filename.replace(".pcap", ".gps.json")

                if self.coordinates and all([
                    # avoid 0.000... measurements
                    self.coordinates["latitude"], self.coordinates["longitude"]
                ]):
                    logging.info(f"saving GPS to {gps_filename} ({self.coordinates})")
                    with open(gps_filename, "w+t") as fp:
                        json.dump(self.coordinates, fp)
                else:
                    logging.info("[PwnDroid] not saving GPS. Couldn't find location.")

    def on_ui_setup(self, ui):
        try:
            # Configure line_spacing
            line_spacing = int(self.options['linespacing'])
        except Exception:
            # Set default value
            line_spacing = self.LINE_SPACING

        try:
            # Configure position
            pos = self.options['position'].split(',')
            pos = [int(x.strip()) for x in pos]
            lat_pos = (pos[0] + 5, pos[1])
            lon_pos = (pos[0], pos[1] + line_spacing)
            alt_pos = (pos[0] + 5, pos[1] + (2 * line_spacing))
        except Exception:
            # Set default value based on display type
            lat_pos = (127, 64)
            lon_pos = (127, 74)
            alt_pos = (127, 84)

        ui.add_element(
            "latitude",
            LabeledValue(
                color=BLACK,
                label="lat:",
                value="-",
                position=lat_pos,
                label_font=fonts.Small,
                text_font=fonts.Small,
                label_spacing=self.LABEL_SPACING,
            ),
        )
        ui.add_element(
            "longitude",
            LabeledValue(
                color=BLACK,
                label="long:",
                value="-",
                position=lon_pos,
                label_font=fonts.Small,
                text_font=fonts.Small,
                label_spacing=self.LABEL_SPACING,
            ),
        )
        ui.add_element(
            "altitude",
            LabeledValue(
                color=BLACK,
                label="alt:",
                value="-",
                position=alt_pos,
                label_font=fonts.Small,
                text_font=fonts.Small,
                label_spacing=self.LABEL_SPACING,
            ),
        )

    def on_unload(self, ui):
        with ui._lock:
            ui.remove_element('latitude')
            ui.remove_element('longitude')
            ui.remove_element('altitude')

    def on_ui_update(self, ui):
        if self.options['display']:
            with ui._lock:
                server_url = f"http://192.168.44.1:8080"
                self.coordinates = self.get_location_data(server_url)
                if self.coordinates and all([
                    # avoid 0.000... measurements
                    self.coordinates["latitude"], self.coordinates["longitude"]
                ]):
                    # last char is sometimes not completely drawn ¯\_(ツ)_/¯
                    # using an ending-whitespace as workaround on each line
                    ui.set("latitude", f"{self.coordinates['latitude']:.4f} ")
                    ui.set("longitude", f"{self.coordinates['longitude']:.4f} ")
                    ui.set("altitude", f"{self.coordinates['altitude']:.1f}m ")
