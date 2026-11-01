"""
ADA P1 meter python plugin for Domoticz
Author: szelessavmuhely.hu,
Version: 1.1.1 (2026-11-01) 

<plugin key="ADA_P1_METER" name="ADA P1 meter - ADA P1 Bridge" author="szelessavmuhely.hu" version="1.1.1">
	<description>
		<h2>ADA P1 meter - ADA P1 Bridge</h2><br/>
		<br/>
	</description>
	<params>
		<param field="Address" label="Domoticz IP Address" width="200px" required="true" default="127.0.0.1"/>
		<param field="Port" label="Port" width="40px" required="true" default="8080"/>
		<param field="Mode1" label="Local IP Address" width="200px" required="true" default="" />
		<param field="Mode2" label="Local Port" width="200px" required="true" default="8989" />
		<param field="Mode3" label="Data interval - Frissités" width="200px">
			<options>
				<option label="10 seconds" value="10"/>
				<option label="20 seconds" value="20"/>
				<option label="30 seconds" value="30"/>
				<option label="1 minute" value="60" default="true"/>
				<option label="2 minutes" value="120"/>
				<option label="3 minutes" value="180"/>
				<option label="4 minutes" value="240"/>
				<option label="5 minutes" value="300"/>
			</options>
		</param>
		<param field="Mode4" label="Debug" width="75px">
			<options>
				<option label="True" value="Debug"/>
				<option label="False" value="Normal"  default="true" />
			</options>
		</param>
	</params>
</plugin>
"""
import Domoticz
import json
from urllib import parse, request
from datetime import datetime, timedelta
import time
import math
import base64
import itertools
import re
import os
import heapq

class deviceparam:

	def __init__(self, unit, nvalue, svalue):
		self.unit = unit
		self.nvalue = nvalue
		self.svalue = svalue

class switchparam:

	def __init__(self, idx, command):
		self.idx = idx
		self.command = command

class TranslationLoader:

	def __init__(self, language="en"):
		self.translations = self.load_translations(language)
		if not self.translations:
			Domoticz.Debug("An error occurred while loading the translations!")
			self.translations = self.load_translations("en") 

	def load_translations(self, language):
		file_path = os.path.join(Parameters["HomeFolder"], f'ada_translate_{language}.json')
		try:
			with open(file_path, 'r', encoding='utf-8') as file:
				return json.load(file)
		except (FileNotFoundError, json.JSONDecodeError) as e:
			Domoticz.Debug(f"Error loading the file '{file_path}': {e}")
			return {} 

	def t(self, text):
		return self.translations.get(text, text)  # If there is no translation, it returns with the original text

class BasePlugin:

	def __init__(self):

		self.debug = True
		self.encoded_json = None
		return


	def onStart(self):

		self.location = Settings["Location"].split(";")
		
		self.tl = TranslationLoader(Parameters["Language"])

		self.dataIntervalCount = 0
		
		if Parameters["Mode4"] == "Debug":
			Domoticz.Debugging(1)
			DumpConfigToLog()
		
		# If data interval between 10 sec. and 5 min.
		if 10 <= int(Parameters["Mode3"]) <= 300:
			self.dataInterval = int(Parameters["Mode3"])
		else:
			# If not, set to 60 sec.
			self.dataInterval = 60

		devicecreated = []
		if 1 not in Devices:
			Domoticz.Device(Name= self.tl.t("Total imported energy"), Unit=1, Type=113, Subtype=0, Used=1).Create()
			devicecreated.append(deviceparam(1, 0, "0"))
		if 2 not in Devices:
			Domoticz.Device(Name= self.tl.t("Total exported energy"), Unit=2, Type=113, Subtype=0, Used=1).Create()
			devicecreated.append(deviceparam(2, 0, "0"))
		if 3 not in Devices:
			Domoticz.Device(Name= self.tl.t("Total active energy"), Unit=3, Type=113, Subtype=0, Used=1).Create()
			devicecreated.append(deviceparam(3, 0, "0"))
		if 4 not in Devices:
			Domoticz.Device(Name= self.tl.t("Imported energy tariff 1"), Unit=4, Type=113, Subtype=0, Used=1).Create()
			devicecreated.append(deviceparam(4, 0, "0"))
		if 5 not in Devices:
			Domoticz.Device(Name= self.tl.t("Imported energy tariff 2"), Unit=5, Type=113, Subtype=0, Used=1).Create()
			devicecreated.append(deviceparam(5, 0, "0"))
		if 6 not in Devices:
			Domoticz.Device(Name= self.tl.t("Imported energy tariff 3"), Unit=6, Type=113, Subtype=0, Used=1).Create()
			devicecreated.append(deviceparam(6, 0, "0"))
		if 7 not in Devices:
			Domoticz.Device(Name= self.tl.t("Imported energy tariff 4"), Unit=7, Type=113, Subtype=0, Used=1).Create()
			devicecreated.append(deviceparam(7, 0, "0"))
		if 8 not in Devices:
			Domoticz.Device(Name= self.tl.t("Exported energy tariff 1"), Unit=8, Type=113, Subtype=0, Used=1).Create()
			devicecreated.append(deviceparam(8, 0, "0"))
		if 9 not in Devices:
			Domoticz.Device(Name= self.tl.t("Exported energy tariff 2"), Unit=9, Type=113, Subtype=0, Used=1).Create()
			devicecreated.append(deviceparam(9, 0, "0"))
		if 10 not in Devices:
			Domoticz.Device(Name= self.tl.t("Exported energy tariff 3"), Unit=10, Type=113, Subtype=0, Used=1).Create()
			devicecreated.append(deviceparam(10, 0, "0"))
		if 11 not in Devices:
			Domoticz.Device(Name= self.tl.t("Exported energy tariff 4"), Unit=11, Type=250, Subtype=1, Used=1).Create()
			devicecreated.append(deviceparam(11, 0, "0"))
		if 12 not in Devices:
			Domoticz.Device(Name= self.tl.t("Reactive imported energy"), Unit=12, Type=243, Subtype=31, Options={"Custom": "1;kVArh"}, Used=1).Create()
			devicecreated.append(deviceparam(12, 0, "0"))
		if 13 not in Devices:
			Domoticz.Device(Name= self.tl.t("Reactive exported energy"), Unit=13, Type=243, Subtype=31, Options={"Custom": "1;kVArh"}, Used=1).Create()
			devicecreated.append(deviceparam(13, 0, "0"))
		if 14 not in Devices:
			Domoticz.Device(Name= self.tl.t("Reactive energy QI"), Unit=14, Type=243, Subtype=31, Options={"Custom": "1;kVArh"}, Used=1).Create()
			devicecreated.append(deviceparam(14, 0, "0"))
		if 15 not in Devices:
			Domoticz.Device(Name= self.tl.t("Reactive energy QII"), Unit=15, Type=243, Subtype=31, Options={"Custom": "1;kVArh"}, Used=1).Create()
			devicecreated.append(deviceparam(15, 0, "0"))
		if 16 not in Devices:
			Domoticz.Device(Name= self.tl.t("Reactive energy QIII"), Unit=16, Type=243, Subtype=31, Options={"Custom": "1;kVArh"}, Used=1).Create()
			devicecreated.append(deviceparam(16, 0, "0"))
		if 17 not in Devices:
			Domoticz.Device(Name= self.tl.t("Reactive energy QIV"), Unit=17, Type=243, Subtype=31, Options={"Custom": "1;kVArh"}, Used=1).Create()
			devicecreated.append(deviceparam(17, 0, "0"))
		if 18 not in Devices:
			Domoticz.Device(Name= self.tl.t("Instantaneous imported power"), Unit=18, Type=243, Subtype=31, Options={"Custom": "1;kW"}, Used=1).Create()
			devicecreated.append(deviceparam(18, 0, "0"))
		if 19 not in Devices:
			Domoticz.Device(Name= self.tl.t("Instantaneous exported power"), Unit=19, Type=243, Subtype=31, Options={"Custom": "1;kW"}, Used=1).Create()
			devicecreated.append(deviceparam(19, 0, "0"))
		if 20 not in Devices:
			Domoticz.Device(Name= self.tl.t("Imported power L1"), Unit=20, Type=243, Subtype=31, Options={"Custom": "1;kW"}, Used=1).Create()
			devicecreated.append(deviceparam(20, 0, "0"))
		if 21 not in Devices:
			Domoticz.Device(Name= self.tl.t("Imported power L2"), Unit=21, Type=243, Subtype=31, Options={"Custom": "1;kW"}, Used=1).Create()
			devicecreated.append(deviceparam(21, 0, "0"))
		if 22 not in Devices:
			Domoticz.Device(Name= self.tl.t("Imported power L3"), Unit=22, Type=243, Subtype=31, Options={"Custom": "1;kW"}, Used=1).Create()
			devicecreated.append(deviceparam(22, 0, "0"))
		if 23 not in Devices:
			Domoticz.Device(Name= self.tl.t("Exported power L1"), Unit=23, Type=243, Subtype=31, Options={"Custom": "1;kW"}, Used=1).Create()
			devicecreated.append(deviceparam(23, 0, "0"))
		if 24 not in Devices:
			Domoticz.Device(Name= self.tl.t("Exported power L2"), Unit=24, Type=243, Subtype=31, Options={"Custom": "1;kW"}, Used=1).Create()
			devicecreated.append(deviceparam(24, 0, "0"))
		if 25 not in Devices:
			Domoticz.Device(Name= self.tl.t("Exported power L3"), Unit=25, Type=243, Subtype=31, Options={"Custom": "1;kW"}, Used=1).Create()
			devicecreated.append(deviceparam(25, 0, "0"))
		if 26 not in Devices:
			Domoticz.Device(Name= self.tl.t("Reactive power QI"), Unit=26, Type=243, Subtype=31, Options={"Custom": "1;kVArh"}, Used=1).Create()
			devicecreated.append(deviceparam(26, 0, "0"))
		if 27 not in Devices:
			Domoticz.Device(Name= self.tl.t("Reactive power QII"), Unit=27, Type=243, Subtype=31, Options={"Custom": "1;kVArh"}, Used=1).Create()
			devicecreated.append(deviceparam(27, 0, "0"))
		if 28 not in Devices:
			Domoticz.Device(Name= self.tl.t("Reactive power QIII"), Unit=28, Type=243, Subtype=31, Options={"Custom": "1;kVArh"}, Used=1).Create()
			devicecreated.append(deviceparam(28, 0, "0"))
		if 29 not in Devices:
			Domoticz.Device(Name= self.tl.t("Reactive power QIV"), Unit=29, Type=243, Subtype=31, Options={"Custom": "1;kVArh"}, Used=1).Create()
			devicecreated.append(deviceparam(29, 0, "0"))
		if 30 not in Devices:
			Domoticz.Device(Name= self.tl.t("Voltage L1"), Unit=30, Type=248, Subtype=8, Used=1).Create()
			devicecreated.append(deviceparam(30, 0, "0"))
		if 31 not in Devices:
			Domoticz.Device(Name= self.tl.t("Voltage L2"), Unit=31, Type=248, Subtype=8, Used=1).Create()
			devicecreated.append(deviceparam(31, 0, "0"))
		if 32 not in Devices:
			Domoticz.Device(Name= self.tl.t("Voltage L3"), Unit=32, Type=248, Subtype=8, Used=1).Create()
			devicecreated.append(deviceparam(32, 0, "0"))
		if 33 not in Devices:
			Domoticz.Device(Name= self.tl.t("Current L1"), Unit=33, Type=248, Subtype=23, Used=1).Create()
			devicecreated.append(deviceparam(33, 0, "0"))
		if 34 not in Devices:
			Domoticz.Device(Name= self.tl.t("Current L2"), Unit=34, Type=248, Subtype=23, Used=1).Create()
			devicecreated.append(deviceparam(34, 0, "0"))
		if 35 not in Devices:
			Domoticz.Device(Name= self.tl.t("Current L3"), Unit=35, Type=248, Subtype=23, Used=1).Create()
			devicecreated.append(deviceparam(35, 0, "0"))
		if 36 not in Devices:
			Domoticz.Device(Name= self.tl.t("Current Bl1"), Unit=36, Type=248, Subtype=23, Used=1).Create()
			devicecreated.append(deviceparam(36, 0, "0"))
		if 37 not in Devices:
			Domoticz.Device(Name= self.tl.t("Current Bl2"), Unit=37, Type=248, Subtype=23, Used=1).Create()
			devicecreated.append(deviceparam(37, 0, "0"))
		if 38 not in Devices:
			Domoticz.Device(Name= self.tl.t("Current Bl3"), Unit=38, Type=248, Subtype=23, Used=1).Create()
			devicecreated.append(deviceparam(38, 0, "0"))
		if 39 not in Devices:
			Domoticz.Device(Name= self.tl.t("Network frequency"), Unit=39, Type=243, Subtype=31, Options={"Custom": "1;Hz"}, Used=1).Create()
			devicecreated.append(deviceparam(39, 0, "0"))
		if 40 not in Devices:
			Domoticz.Device(Name= self.tl.t("Power factor"), Unit=40, Type=243, Subtype=31, Options={"Custom": "1;cos φ"}, Used=1).Create()
			devicecreated.append(deviceparam(40, 0, "0"))
		if 41 not in Devices:
			Domoticz.Device(Name= self.tl.t("Power factor L1"), Unit=41, Type=243, Subtype=31, Options={"Custom": "1;cos φ"}, Used=1).Create()
			devicecreated.append(deviceparam(41, 0, "0"))
		if 42 not in Devices:
			Domoticz.Device(Name= self.tl.t("Power factor L2"), Unit=42, Type=243, Subtype=31, Options={"Custom": "1;cos φ"}, Used=1).Create()
			devicecreated.append(deviceparam(42, 0, "0"))
		if 43 not in Devices:
			Domoticz.Device(Name= self.tl.t("Power factor L3"), Unit=43, Type=243, Subtype=31, Options={"Custom": "1;cos φ"}, Used=1).Create()
			devicecreated.append(deviceparam(43, 0, "0"))
		if 44 not in Devices:
			Domoticz.Device(Name= self.tl.t("Meter serial number"), Unit=44, Type=243, Subtype=19, Used=1).Create()
			devicecreated.append(deviceparam(44, 0, "0"))
		if 45 not in Devices:
			Domoticz.Device(Name= self.tl.t("Circuit breaker status"), Unit=45, Type=244, Subtype=73, Switchtype=0, Image=9, Used=1).Create()
			devicecreated.append(deviceparam(45, 0, "0"))
		if 46 not in Devices:
			Domoticz.Device(Name=self.tl.t("Active tariff"), Unit=46, Type=243, Subtype=19, Used=1).Create()
			devicecreated.append(deviceparam(46, 0, "-"))
			self.addfavorite(Devices[46].ID)
		if 47 not in Devices:
			Domoticz.Device(Name= self.tl.t("Current - daily consumption"), Unit=47, Type=250, Subtype=1, Used=1).Create()
			devicecreated.append(deviceparam(47, 0, "0"))
			self.addfavorite(Devices[47].ID)

		for device in devicecreated:
			Devices[device.unit].Update(nValue=device.nvalue, sValue=device.svalue)


	def onStop(self):
		Domoticz.Debugging(0)


	def onCommand(self, Unit, Command, Level, Color):

		Domoticz.Debug("onCommand called for Unit {}: Command '{}', Level: {}".format(Unit, Command, Level))


	def onHeartbeat(self):

		self.dataIntervalCount += 10

		#------- Collect data -------
		if ( self.dataIntervalCount >= self.dataInterval ):
			self.dataIntervalCount = 0
			self.readMeter()
		
		return

	def WriteLog(self, message, level="Normal"):

		if (self.loglevel == "Verbose" and level == "Verbose") or level == "Status":
			if self.statussupported:
				Domoticz.Status(message)
			else:
				Domoticz.Log(message)
		elif level == "Normal":
			Domoticz.Log(message)

	def addfavorite(self, deviceidx):

		idx = deviceidx
		DomoticzAPI("idx={}&isfavorite=1&param=makefavorite&type=command".format(idx))

	def removefavorite(self, deviceidx):

		idx = deviceidx
		DomoticzAPI("idx={}&isfavorite=0&param=makefavorite&type=command".format(idx))

	def readMeter(self):

		data = P1API()
		if not data:
			return

		self.onMessage(data, "200", "")

		return False

	def onMessage(self, data, status, extra):

		# --- összesített import / export / nettó energia (kWh) ---
		import_kwh = self._f(data, 'active_import_energy_total')
		export_kwh = self._f(data, 'active_export_energy_total')

		Devices[1].Update(0, str(import_kwh))
		Devices[2].Update(0, str(export_kwh))
		Devices[3].Update(0, str(import_kwh - export_kwh))

		# --- import energia tarifánként (kWh) ---
		Devices[4].Update(0, f"{self._f(data,'active_import_energy_tariff_1')}")
		Devices[5].Update(0, f"{self._f(data,'active_import_energy_tariff_2')}")
		Devices[6].Update(0, f"{self._f(data,'active_import_energy_tariff_3')}")
		Devices[7].Update(0, f"{self._f(data,'active_import_energy_tariff_4')}")

		# --- export energia tarifánként (kWh) ---
		Devices[8].Update(0, f"{self._f(data,'active_export_energy_tariff_1')}")
		Devices[9].Update(0, f"{self._f(data,'active_export_energy_tariff_2')}")
		Devices[10].Update(0, f"{self._f(data,'active_export_energy_tariff_3')}")
		Devices[11].Update(0, f"{self._f(data,'active_export_energy_tariff_4')}")


		# --- Meddő energiák (kVArh) ---
		Devices[12].Update(0, f"{self._f(data,'reactive_import_energy')}")
		Devices[13].Update(0, f"{self._f(data,'reactive_export_energy')}")
		Devices[14].Update(0, f"{self._f(data,'reactive_energy_qi')}")
		Devices[15].Update(0, f"{self._f(data,'reactive_energy_qii')}")
		Devices[16].Update(0, f"{self._f(data,'reactive_energy_qiii')}")
		Devices[17].Update(0, f"{self._f(data,'reactive_energy_qiv')}")

		# --- Pillanatnyi teljesítmények (kW) ---
		Devices[18].Update(0, f"{self._f(data,'instantaneous_power_import')}")
		Devices[19].Update(0, f"{self._f(data,'instantaneous_power_export')}")

		Devices[20].Update(0, f"{self._f(data,'instantaneous_power_import_l1')}")
		Devices[21].Update(0, f"{self._f(data,'instantaneous_power_import_l2')}")
		Devices[22].Update(0, f"{self._f(data,'instantaneous_power_import_l3')}")

		Devices[23].Update(0, f"{self._f(data,'instantaneous_power_export_l1')}")
		Devices[24].Update(0, f"{self._f(data,'instantaneous_power_export_l2')}")
		Devices[25].Update(0, f"{self._f(data,'instantaneous_power_export_l3')}")

		# --- Pillanatnyi meddő teljesítmény ---
		Devices[26].Update(0, f"{self._f(data,'instantaneous_reactive_power_qi')}")
		Devices[27].Update(0, f"{self._f(data,'instantaneous_reactive_power_qii')}")
		Devices[28].Update(0, f"{self._f(data,'instantaneous_reactive_power_qiii')}")
		Devices[29].Update(0, f"{self._f(data,'instantaneous_reactive_power_qiv')}")

		# --- Feszültségek ---
		Devices[30].Update(0, f"{self._f(data,'voltage_phase_l1')}")
		Devices[31].Update(0, f"{self._f(data,'voltage_phase_l2')}")
		Devices[32].Update(0, f"{self._f(data,'voltage_phase_l3')}")

		# --- Áramok ---
		Devices[33].Update(0, f"{self._f(data,'current_phase_l1')}")
		Devices[34].Update(0, f"{self._f(data,'current_phase_l2')}")
		Devices[35].Update(0, f"{self._f(data,'current_phase_l3')}")

		Devices[36].Update(0, f"{self._f(data,'current_phase_Bl1')}")
		Devices[37].Update(0, f"{self._f(data,'current_phase_Bl2')}")
		Devices[38].Update(0, f"{self._f(data,'current_phase_Bl3')}")

		# --- Frekvencia ---
		Devices[39].Update(0, f"{self._f(data,'frequency')}")

		# --- Teljesítménytényezők ---
		Devices[40].Update(0, f"{self._f(data,'power_factor')}")
		Devices[41].Update(0, f"{self._f(data,'power_factor_l1')}")
		Devices[42].Update(0, f"{self._f(data,'power_factor_l2')}")
		Devices[43].Update(0, f"{self._f(data,'power_factor_l3')}")

		# --- Mérő sorozatszám ---
		Devices[44].Update(0, self._s(data,'meter_serial_number'))

		# --- Kismegszakító ---
		cb = self._s(data,'circuit_breaker_status')
		if cb == "ON":
			Devices[45].Update(1, "On")
		else:
			Devices[45].Update(0, "Off")

		# --- AKTÍV TARIFA (Selector) ---
		tariff = data.get("current_tariff", "----")

		tariff_text = {
			"0001": "0001",
			"0002": "0002",
			"0003": "0003",
			"0004": "0004"
		}.get(tariff, tariff)

		Devices[46].Update(0, tariff_text)

		# --- kWh értékek (FLOAT kWh → INT Wh) ---
		import_t1_f = int((self._f(data, "active_import_energy_tariff_1") or 0.0) * 1000)
		import_t2_f = int((self._f(data, "active_import_energy_tariff_2") or 0.0) * 1000)
		export_t1_f = int((self._f(data, "active_export_energy_tariff_1") or 0.0) * 1000)
		export_t2_f = int((self._f(data, "active_export_energy_tariff_2") or 0.0) * 1000)


		# --- pillanatnyi teljesítmény (WATT, FLOAT!) ---
		import_w_f = (self._f(data, "instantaneous_power_import") or 0.0) * 1000
		export_w_f = (self._f(data, "instantaneous_power_export") or 0.0) * 1000

		# --- EGÉSZRE kerekítés ---
		import_w_i  = int(round(import_w_f))
		export_w_i  = int(round(export_w_f))

		# --- P1 Smart Meter sValue (CSAK EGÉSZ!) ---
		sValue = f"{import_t1_f};{import_t2_f};{export_t1_f};{export_t2_f};{import_w_i};{export_w_i}"

		Devices[47].Update(0, sValue)

		Domoticz.Debug(f"[P1 DEBUG] imp={import_t1_f}+{import_t2_f}, exp={export_t1_f}+{export_t2_f}, Wimp={import_w_i}, Wexp={export_w_i}")


	def _f(self, data, key, default=0.0):
		try:
			val = data.get(key, default)
			if val in ("", None):
				return default
			return float(val)
		except Exception:
			return default

	def _s(self, data, key, default=""):
		val = data.get(key, default)
		if val in (None, ""):
			return default
		return str(val)

	def numStr(self, s, decimals=0):
		try:
			return f"{float(s):.{decimals}f}"
		except:
			return "0"


global _plugin
_plugin = BasePlugin()


def onStart():
	global _plugin
	_plugin.onStart()


def onStop():
	global _plugin
	_plugin.onStop()


def onCommand(Unit, Command, Level, Color):
	global _plugin
	_plugin.onCommand(Unit, Command, Level, Color)


def onHeartbeat():
	global _plugin
	_plugin.onHeartbeat()


# Plugin utility functions ---------------------------------------------------

def P1API():

	resultJson = None
	url = "http://{}:{}/json".format(Parameters["Mode1"], Parameters["Mode2"])
	Domoticz.Debug("Calling ADA P1 API: {}".format(url))

	try:
		req = request.Request(url)
		response = request.urlopen(req, timeout=5)

		if response.status == 200:
			resultJson = json.loads(response.read().decode('utf-8'))
		else:
			Domoticz.Error("ADA P1 API: http error = {}".format(response.status))

	except Exception as e:
		Domoticz.Error("ADA P1 API error: {}".format(e))

	return resultJson

def DomoticzAPI(APICall):

	resultJson = None
	url = "http://{}:{}/json.htm?{}".format(Parameters["Address"], Parameters["Port"], parse.quote(APICall, safe="&="))
	Domoticz.Debug("Calling domoticz API: {}".format(url))
	try:
		req = request.Request(url)
		if Parameters["Username"] != "":
			Domoticz.Debug("Add authentification for user {}".format(Parameters["Username"]))
			credentials = ('%s:%s' % (Parameters["Username"], Parameters["Password"]))
			encoded_credentials = base64.b64encode(credentials.encode('ascii'))
			req.add_header('Authorization', 'Basic %s' % encoded_credentials.decode("ascii"))

		response = request.urlopen(req)
		if response.status == 200:
			resultJson = json.loads(response.read().decode('utf-8'))
			if resultJson["status"] != "OK":
				Domoticz.Error("Domoticz API returned an error: status = {}".format(resultJson["status"]))
				resultJson = None
		else:
			Domoticz.Error("Domoticz API: http error = {}".format(response.status))
	except:
		Domoticz.Error("Error calling '{}'".format(url))
	return resultJson


# Generic helper functions
def DumpConfigToLog():
	for x in Parameters:
		if Parameters[x] != "":
			Domoticz.Debug("'" + x + "':'" + str(Parameters[x]) + "'")
	Domoticz.Debug("Device count: " + str(len(Devices)))
	for x in Devices:
		Domoticz.Debug("Device: " + str(x) + " - " + str(Devices[x]))
		Domoticz.Debug("Device ID: '" + str(Devices[x].ID) + "'")
		Domoticz.Debug("Device Name: '" + Devices[x].Name + "'")
		Domoticz.Debug("Device nValue: " + str(Devices[x].nValue))
		Domoticz.Debug("Device sValue: '" + Devices[x].sValue + "'")
		Domoticz.Debug("Device LastLevel: " + str(Devices[x].LastLevel))
	return
