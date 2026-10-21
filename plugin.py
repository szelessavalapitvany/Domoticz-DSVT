"""
Dual Smart Virtual Thermostat + DHW + 12-Zone Valve Python Plugin for Domoticz
Further development by Szelessav:
https://www.szelessavmuhely.hu/en/heating_cooling_dhw_buffer

Weather forecast data provided by Open-Meteo:
https://open-meteo.com/

Weather data is licensed under CC BY 4.0.

Version: 1.3.0 (2026-10-20)
"""
"""
<plugin key="DSVT_HMV_ZONE_12" name="DSVT + HMV (DHW) + 12 ZONE" author="Szelessav" version="1.3.0" externallink="https://www.szelessavmuhely.hu/en/heating_cooling_dhw_buffer">
	<description>
		<h2>Dual Smart Virtual Thermostat + HMV (DHW) ZONE 12</h2><br/>
		<br/>
		<h3>Setup and configuration: | Beállítás és konfigurálás: </h3>
		<br/>
		<strong><a href="#/Custom/DSVT_HMV_ZONE_12">HTML setup!</a></strong>
		<br/>
		<br/>
	</description>
	
	<params>
		<param field="Address" label="Domoticz IP Address" width="400px" required="true" default="127.0.0.1"/>
		<param field="Port" label="Port" width="40px" required="true" default="8080"/>
		<param field="Username" label="Username" width="400px" required="false" default=""/>
		<param field="Password" label="Password" width="400px" required="false" default=""/>
		<param field="Mode1" label="List of thermometers (details in the DSVT documentation)" width="400px" required="false" default=""/>
		<param field="Mode2" label="Heating devices (details in the DSVT documentation)" width="400px" required="false" default=""/>
		<param field="Mode3" label="Cooling devices (details in the DSVT documentation)" width="400px" required="false" default=""/>
		<param field="Mode4" label="1. device control (details in the DSVT documentation)" width="400px" required="false" default=""/>
		<param field="Mode5" label="2. device control (details in the DSVT documentation)" width="400px" required="false" default=""/>
		<param field="Mode6" label="Operating parameters (details in the documentation)" width="400px" required="true" default="0,5,15,0,None"/>
	</params>
</plugin>
"""

import Domoticz
import sqlite3
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
import random

class deviceparam:

	def __init__(self, unit, nvalue, svalue):
		self.unit = unit
		self.nvalue = nvalue
		self.svalue = svalue

class switchparam:

	def __init__(self, idx, command):
		self.idx = idx
		self.command = command

class tempparam:

	def __init__(self, idx):
		self.idx = idx

class TranslationLoader:

	def __init__(self, language="en"):
		self.translations = self.load_translations(language)
		if not self.translations:
			Domoticz.Error('An error occurred while loading the translations! | Hiba történt a fordítások betöltésekor!')
			self.translations = self.load_translations("en") 

	def load_translations(self, language):
		file_path = os.path.join(Parameters["HomeFolder"], f'dsvt_translate_{language}.json')
		try:
			with open(file_path, 'r', encoding='utf-8') as file:
				return json.load(file)
		except (FileNotFoundError, json.JSONDecodeError) as e:
			Domoticz.Error(f"Error loading file {file_path}: {e} | Hiba a(z) {file_path} fájl betöltésekor: {e}")
			return {} 

	def t(self, text):
		return self.translations.get(text, text)  # If no translation exists, return the original text | Ha nincs fordítás, az eredeti szöveget adja vissza


class BasePlugin:

	def __init__(self):
		self.calculate_period = 15
		self.ActiveSensors = {}
		self.current_hc = 1
		self.current_buffer = 1
		self.Zone_TempSensors_1 = []
		self.Zone_TempSensors_2 = []
		self.Zone_TempSensors_3 = []
		self.Zone_TempSensors_4 = []
		self.Zone_TempSensors_5 = []
		self.Zone_TempSensors_6 = []
		self.Zone_TempSensors_7 = []
		self.Zone_TempSensors_8 = []
		self.Zone_TempSensors_9 = []
		self.Zone_TempSensors_10 = []
		self.Zone_TempSensors_11 = []
		self.Zone_TempSensors_12 = []
		self.KulsoTempSensors = []
		self.FrostTempSensors = []
		self.FrostSwitches = []
		self.FrostLimit = 5.0
		self.FrostHysteresis = 1.0
		self.FrostTemp = None
		self.FrostActive = False
		self.PumpProtectionSwitches = []
		self.PumpProtectionDay = None
		self.PumpProtectionHour = None
		self.PumpProtectionMinutes = None
		self.TartalyTempSensors = []
		self.PufferTempSensors = []
		self.szobaTempSensors = []
		self.Zonepluss = []
		self.Zone_1_F = []
		self.Zone_2_F = []
		self.Zone_3_F = []
		self.Zone_4_F = []
		self.Zone_5_F = []
		self.Zone_6_F = []
		self.Zone_7_F = []
		self.Zone_8_F = []
		self.Zone_9_F = []
		self.Zone_10_F = []
		self.Zone_11_F = []
		self.Zone_12_F = []
		self.Zone_1_F_V = []
		self.Zone_2_F_V = []
		self.Zone_3_F_V = []
		self.Zone_4_F_V = []
		self.Zone_5_F_V = []
		self.Zone_6_F_V = []
		self.Zone_7_F_V = []
		self.Zone_8_F_V = []
		self.Zone_9_F_V = []
		self.Zone_10_F_V = []
		self.Zone_11_F_V = []
		self.Zone_12_F_V = []
		self.Zone_1_H = []
		self.Zone_2_H = []
		self.Zone_3_H = []
		self.Zone_4_H = []
		self.Zone_5_H = []
		self.Zone_6_H = []
		self.Zone_7_H = []
		self.Zone_8_H = []
		self.Zone_9_H = []
		self.Zone_10_H = []
		self.Zone_11_H = []
		self.Zone_12_H = []
		self.Zone_1_H_V = []
		self.Zone_2_H_V = []
		self.Zone_3_H_V = []
		self.Zone_4_H_V = []
		self.Zone_5_H_V = []
		self.Zone_6_H_V = []
		self.Zone_7_H_V = []
		self.Zone_8_H_V = []
		self.Zone_9_H_V = []
		self.Zone_10_H_V = []
		self.Zone_11_H_V = []
		self.Zone_12_H_V = []
		self.ZoneTRV_1 = []
		self.ZoneTRV_2 = []
		self.ZoneTRV_3 = []
		self.ZoneTRV_4 = []
		self.ZoneTRV_5 = []
		self.ZoneTRV_6 = []
		self.ZoneTRV_7 = []
		self.ZoneTRV_8 = []
		self.ZoneTRV_9 = []
		self.ZoneTRV_10 = []
		self.ZoneTRV_11 = []
		self.ZoneTRV_12 = []
		self.ZoneConsole_1 = []
		self.ZoneConsole_2 = []
		self.ZoneConsole_3 = []
		self.ZoneConsole_4 = []
		self.ZoneConsole_5 = []
		self.ZoneConsole_6 = []
		self.ZoneConsole_7 = []
		self.ZoneConsole_8 = []
		self.ZoneConsole_9 = []
		self.ZoneConsole_10 = []
		self.ZoneConsole_11 = []
		self.ZoneConsole_12 = []
		self.Z_1_AC_F_URL = []
		self.Z_1_AC_H_URL = []
		self.Z_2_AC_F_URL = []
		self.Z_2_AC_H_URL = []
		self.Z_3_AC_F_URL = []
		self.Z_3_AC_H_URL = []
		self.Z_4_AC_F_URL = []
		self.Z_4_AC_H_URL = []
		self.Z_5_AC_F_URL = []
		self.Z_5_AC_H_URL = []
		self.Z_6_AC_F_URL = []
		self.Z_6_AC_H_URL = []
		self.Z_7_AC_F_URL = []
		self.Z_7_AC_H_URL = []
		self.Z_8_AC_F_URL = []
		self.Z_8_AC_H_URL = []
		self.Z_9_AC_F_URL = []
		self.Z_9_AC_H_URL = []
		self.Z_10_AC_F_URL = []
		self.Z_10_AC_H_URL = []
		self.Z_11_AC_F_URL = []
		self.Z_11_AC_H_URL = []
		self.Z_12_AC_F_URL = []
		self.Z_12_AC_H_URL = []
		self.LAST_Z_1_AC_F_URL = []
		self.LAST_Z_1_AC_H_URL = []
		self.LAST_Z_2_AC_F_URL = []
		self.LAST_Z_2_AC_H_URL = []
		self.LAST_Z_3_AC_F_URL = []
		self.LAST_Z_3_AC_H_URL = []
		self.LAST_Z_4_AC_F_URL = []
		self.LAST_Z_4_AC_H_URL = []
		self.LAST_Z_5_AC_F_URL = []
		self.LAST_Z_5_AC_H_URL = []
		self.LAST_Z_6_AC_F_URL = []
		self.LAST_Z_6_AC_H_URL = []
		self.LAST_Z_7_AC_F_URL = []
		self.LAST_Z_7_AC_H_URL = []
		self.LAST_Z_8_AC_F_URL = []
		self.LAST_Z_8_AC_H_URL = []
		self.LAST_Z_9_AC_F_URL = []
		self.LAST_Z_9_AC_H_URL = []
		self.LAST_Z_10_AC_F_URL = []
		self.LAST_Z_10_AC_H_URL = []
		self.LAST_Z_11_AC_F_URL = []
		self.LAST_Z_11_AC_H_URL = []
		self.LAST_Z_12_AC_F_URL = []
		self.LAST_Z_12_AC_H_URL = []
		self.Elsodleges_F = []
		self.Masodlagos_F = []
		self.Elsodleges_M = []
		self.Masodlagos_M = []
		self.Elsodleges_E = []
		self.Masodlagos_E = []
		self.Elsodleges_H = []
		self.Masodlagos_H = []
		self.Keveroszelep_1_plusz = []
		self.Keveroszelep_1_minusz = []
		self.Keveroszelep_2_plusz = []
		self.Keveroszelep_2_minusz = []
		self.Kevero_1_szorzo = 100
		self.Kevero_2_szorzo = 100
		self.Kevero_1_TempSensor = []
		self.Kevero_2_TempSensor = []
		self.Kevero_1_temp_aktual = 20.0
		self.Kevero_2_temp_aktual = 20.0
		self.Kevero_1_temp_target = 20.0
		self.Kevero_2_temp_target = 20.0
		self.zone_1_aktual_temp = None
		self.zone_2_aktual_temp = None
		self.zone_3_aktual_temp = None
		self.zone_4_aktual_temp = None
		self.zone_5_aktual_temp = None
		self.zone_6_aktual_temp = None
		self.zone_7_aktual_temp = None
		self.zone_8_aktual_temp = None
		self.zone_9_aktual_temp = None
		self.zone_10_aktual_temp = None
		self.zone_11_aktual_temp = None
		self.zone_12_aktual_temp = None
		self.Kevero_1_harmatkorr = 2.0
		self.Kevero_2_harmatkorr = 2.0
		self.Kevero_1_temp_max = 40.0
		self.Kevero_2_temp_max = 40.0
		self.Kevero_1_temp_min = 40.0
		self.Kevero_2_temp_min = 40.0
		self.ftargettemp_1 = 22.0
		self.ftargettemp_2 = 22.0
		self.ftargettemp_3 = 22.0
		self.ftargettemp_4 = 22.0
		self.ftargettemp_5 = 22.0
		self.ftargettemp_6 = 22.0
		self.ftargettemp_7 = 22.0
		self.ftargettemp_8 = 22.0
		self.ftargettemp_9 = 22.0
		self.ftargettemp_10 = 22.0
		self.ftargettemp_11 = 22.0
		self.ftargettemp_12 = 22.0
		self.htargettemp_1 = 24.0
		self.htargettemp_2 = 24.0
		self.htargettemp_3 = 24.0
		self.htargettemp_4 = 24.0
		self.htargettemp_5 = 24.0
		self.htargettemp_6 = 24.0
		self.htargettemp_7 = 24.0
		self.htargettemp_8 = 24.0
		self.htargettemp_9 = 24.0
		self.htargettemp_10 = 24.0
		self.htargettemp_11 = 24.0
		self.htargettemp_12 = 24.0
		self.ftargettemp_1_also = 22.0
		self.ftargettemp_2_also = 22.0
		self.ftargettemp_3_also = 22.0
		self.ftargettemp_4_also = 22.0
		self.ftargettemp_5_also = 22.0
		self.ftargettemp_6_also = 22.0
		self.ftargettemp_7_also = 22.0
		self.ftargettemp_8_also = 22.0
		self.ftargettemp_9_also = 22.0
		self.ftargettemp_10_also = 22.0
		self.ftargettemp_11_also = 22.0
		self.ftargettemp_12_also = 22.0
		self.htargettemp_1_also = 24.0
		self.htargettemp_2_also = 24.0
		self.htargettemp_3_also = 24.0
		self.htargettemp_4_also = 24.0
		self.htargettemp_5_also = 24.0
		self.htargettemp_6_also = 24.0
		self.htargettemp_7_also = 24.0
		self.htargettemp_8_also = 24.0
		self.htargettemp_9_also = 24.0
		self.htargettemp_10_also = 24.0
		self.htargettemp_11_also = 24.0
		self.htargettemp_12_also = 24.0
		self.ftargettemp_1_felso = 22.0
		self.ftargettemp_2_felso = 22.0
		self.ftargettemp_3_felso = 22.0
		self.ftargettemp_4_felso = 22.0
		self.ftargettemp_5_felso = 22.0
		self.ftargettemp_6_felso = 22.0
		self.ftargettemp_7_felso = 22.0
		self.ftargettemp_8_felso = 22.0
		self.ftargettemp_9_felso = 22.0
		self.ftargettemp_10_felso = 22.0
		self.ftargettemp_11_felso = 22.0
		self.ftargettemp_12_felso = 22.0
		self.htargettemp_1_felso = 24.0
		self.htargettemp_2_felso = 24.0
		self.htargettemp_3_felso = 24.0
		self.htargettemp_4_felso = 24.0
		self.htargettemp_5_felso = 24.0
		self.htargettemp_6_felso = 24.0
		self.htargettemp_7_felso = 24.0
		self.htargettemp_8_felso = 24.0
		self.htargettemp_9_felso = 24.0
		self.htargettemp_10_felso = 24.0
		self.htargettemp_11_felso = 24.0
		self.htargettemp_12_felso = 24.0
		self.zone_1_window = None
		self.zone_2_window = None
		self.zone_3_window = None
		self.zone_4_window = None
		self.zone_5_window = None
		self.zone_6_window = None
		self.zone_7_window = None
		self.zone_8_window = None
		self.zone_9_window = None
		self.zone_10_window = None
		self.zone_11_window = None
		self.zone_12_window = None
		self.zone_1_window_closed = True
		self.zone_2_window_closed = True
		self.zone_3_window_closed = True
		self.zone_4_window_closed = True
		self.zone_5_window_closed = True
		self.zone_6_window_closed = True
		self.zone_7_window_closed = True
		self.zone_8_window_closed = True
		self.zone_9_window_closed = True
		self.zone_10_window_closed = True
		self.zone_11_window_closed = True
		self.zone_12_window_closed = True
		self.Kevero_1_hiszterezis = 2.0
		self.Kevero_2_hiszterezis = 2.0
		self.TartalySensorTemp = 20.0
		self.TartalyAktual = 20.0
		self.TartalyAktualDiff = 20.0
		self.PufferSensorTemp = 20.0
		self.PufferAktual = 20.0
		self.M_celhomerseklet = 20.0
		self.P_celhomerseklet = 20.0
		self.dhw_ValtasTemp = 20.0
		self.PufferValtasTemp = 20.0
		self.M_hiszterezis = 3.0
		self.operation = False
		self.Hutes = []
		self.intemp = 20.0
		self.LastInT = 20.0
		self.LastOutT = 2.0
		self.LastConstC = 60.0
		self.IntConstT = 1.0
		self.LastConstT = 1.0
		self.intemp_avg = 20.0
		self.indewpoint = 0.0
		self.outtemp = 0.0
		self.outdewpoint = 0.0
		self.minoutdewpoint = 0.0
		self.maxoutdewpoint = 0.0
		self.minintemp = 20.0
		self.maxintemp = 20.0
		self.minindewpoint = 20.0
		self.maxindewpoint = 20.0
		self.minszoba = 20.0
		self.maxszoba = 21.0
		self.diffszoba = 1.0
		self.Fsetpoint = 20.0
		self.DualFsetpoint = 20.0
		self.Hsetpoint = 24.0
		self.DualHsetpoint = 24.0
		self.felsohatar = 23.00
		self.alsohatar = 23.00
		self.power = 50
		self.LastPwr = 50.0
		self.npower = 10.0
		self.hutespowerlimit = 0
		self.F_hiszterezis = 0.0
		self.H_hiszterezis = 0.0
		self.automatic_range = 0.0
		self.szoba_on = []
		self.szoba_off = []
		self.nextcalc = datetime.now() - timedelta(minutes=1)
		self.lastcalc = self.nextcalc
		self.nextupdate = datetime.now()
		self.nextupdatetime = 5
		self.loglevel = None
		self.switchcreated = []
		self.statuscreated = []
		self.napelem = []
		self.jelenlet = None
		self.jelenletInfo = None
		self.lastjelenletInfo = None
		self.Latitude = None
		self.Longitude = None
		self.ido = 0
		self.FutureTemp = 0.0
		self.nowtemp = None
		self.f1works = False
		self.f2works = False
		self.h1works = False
		self.h2works = False
		self.p1works = False
		self.p2works = False
		self.P1_name = None
		self.P1_unit = None
		self.P1_nth = None
		self.Tank_1_N = None
		self.Tank_0_O = None
		self.Tank_2_N = None
		self.Tank_2_O = None
		self.F_last_mode_state = 0
		self.H_last_mode_state = 0
		self.D_last_mode_state = 0
		self.P_last_mode_state = 0
		self.solar_dhw_limit = 0
		self.solar_puffer_limit = 0
		self.device_dhw_max_time = 0
		self.device_dhw_max_time = 0
		self.solar_hc_limit = 0
		self.hc_external_time_F_limit = None
		self.hc_external_time_H_limit = None
		self.hc_external_time_limit = None
		self.debug = False
		self.TartalyLast = False
		self.PufferLast = False
		self.heating_colling = False
		self.dhw = False
		self.buffer = False
		self.statussupported = True
		self.intemperror = False
		self.tartalytemperror = False
		self.puffertemperror = False
		self.device_1_solar_dhw_on = False
		self.device_2_solar_dhw_on = False
		self.device_1_solar_dhw_time = datetime.now()
		self.device_2_solar_dhw_time = datetime.now()
		self.dhw_external_limit = None
		self.dhw_external_time_limit = None
		self._fav_actions = {}
		self._ac_variables_cache = None
		self._ac_variables_cache_until = 0.0

		self.InternalsDefaults = {
			'fjelenstatus' : 0,
			'dhwjelenstatus' : 0,
			'switchTimer_dhw' : 0,
			'power_dhw_consumption' : 0,
			'power_buffer_consumption' : 0,
			'power_hc_consumption' : 0,
			'pump_protection_run': 0}
		self.Internals = self.InternalsDefaults.copy()
		self.AutocallibDefaults = {
			'LastPwr': 0,
			'LastFutureTemps': [0, 0, 0, 0],
			'LastInT': 0,
			'LastOutT': 0
		}
		self.AutoPower = self.AutocallibDefaults.copy()
		
		# ------------------------------
		# Default AC values for zones 1–12 | AC alapértékek az 1–12. zónához
		# ------------------------------

		self.AC_1_F = {
			'type': 0,
			'IP': '0.0.0.0',
			'fanspeed': 0,
			'swingv': 0,
			'swingh': 0,
			'komp': 0,
			'hatar_low': 0,
			'hatar_top': 0,
			'target_off': True,
			'AC_jelenlet': None
		}
		self.Z_1_AC_F = self.AC_1_F.copy()

		self.AC_1_H = {
			'type': 0,
			'IP': '0.0.0.0',
			'fanspeed': 0,
			'swingv': 0,
			'swingh': 0,
			'komp': 0,
			'hatar_low': 0,
			'hatar_top': 0,
			'target_off': True,
			'AC_jelenlet': None
		}
		self.Z_1_AC_H = self.AC_1_H.copy()


		self.AC_2_F = {
			'type': 0,
			'IP': '0.0.0.0',
			'fanspeed': 0,
			'swingv': 0,
			'swingh': 0,
			'komp': 0,
			'hatar_low': 0,
			'hatar_top': 0,
			'target_off': True,
			'AC_jelenlet': None
		}
		self.Z_2_AC_F = self.AC_2_F.copy()

		self.AC_2_H = {
			'type': 0,
			'IP': '0.0.0.0',
			'fanspeed': 0,
			'swingv': 0,
			'swingh': 0,
			'komp': 0,
			'hatar_low': 0,
			'hatar_top': 0,
			'target_off': True,
			'AC_jelenlet': None
		}
		self.Z_2_AC_H = self.AC_2_H.copy()


		self.AC_3_F = {
			'type': 0,
			'IP': '0.0.0.0',
			'fanspeed': 0,
			'swingv': 0,
			'swingh': 0,
			'komp': 0,
			'hatar_low': 0,
			'hatar_top': 0,
			'target_off': True,
			'AC_jelenlet': None
		}
		self.Z_3_AC_F = self.AC_3_F.copy()

		self.AC_3_H = {
			'type': 0,
			'IP': '0.0.0.0',
			'fanspeed': 0,
			'swingv': 0,
			'swingh': 0,
			'komp': 0,
			'hatar_low': 0,
			'hatar_top': 0,
			'target_off': True,
			'AC_jelenlet': None
		}
		self.Z_3_AC_H = self.AC_3_H.copy()


		self.AC_4_F = {
			'type': 0,
			'IP': '0.0.0.0',
			'fanspeed': 0,
			'swingv': 0,
			'swingh': 0,
			'komp': 0,
			'hatar_low': 0,
			'hatar_top': 0,
			'target_off': True,
			'AC_jelenlet': None
		}
		self.Z_4_AC_F = self.AC_4_F.copy()

		self.AC_4_H = {
			'type': 0,
			'IP': '0.0.0.0',
			'fanspeed': 0,
			'swingv': 0,
			'swingh': 0,
			'komp': 0,
			'hatar_low': 0,
			'hatar_top': 0,
			'target_off': True,
			'AC_jelenlet': None
		}
		self.Z_4_AC_H = self.AC_4_H.copy()


		self.AC_5_F = {
			'type': 0,
			'IP': '0.0.0.0',
			'fanspeed': 0,
			'swingv': 0,
			'swingh': 0,
			'komp': 0,
			'hatar_low': 0,
			'hatar_top': 0,
			'target_off': True,
			'AC_jelenlet': None
		}
		self.Z_5_AC_F = self.AC_5_F.copy()

		self.AC_5_H = {
			'type': 0,
			'IP': '0.0.0.0',
			'fanspeed': 0,
			'swingv': 0,
			'swingh': 0,
			'komp': 0,
			'hatar_low': 0,
			'hatar_top': 0,
			'target_off': True,
			'AC_jelenlet': None
		}
		self.Z_5_AC_H = self.AC_5_H.copy()


		self.AC_6_F = {
			'type': 0,
			'IP': '0.0.0.0',
			'fanspeed': 0,
			'swingv': 0,
			'swingh': 0,
			'komp': 0,
			'hatar_low': 0,
			'hatar_top': 0,
			'target_off': True,
			'AC_jelenlet': None
		}
		self.Z_6_AC_F = self.AC_6_F.copy()

		self.AC_6_H = {
			'type': 0,
			'IP': '0.0.0.0',
			'fanspeed': 0,
			'swingv': 0,
			'swingh': 0,
			'komp': 0,
			'hatar_low': 0,
			'hatar_top': 0,
			'target_off': True,
			'AC_jelenlet': None
		}
		self.Z_6_AC_H = self.AC_6_H.copy()


		self.AC_7_F = {
			'type': 0,
			'IP': '0.0.0.0',
			'fanspeed': 0,
			'swingv': 0,
			'swingh': 0,
			'komp': 0,
			'hatar_low': 0,
			'hatar_top': 0,
			'target_off': True,
			'AC_jelenlet': None
		}
		self.Z_7_AC_F = self.AC_7_F.copy()

		self.AC_7_H = {
			'type': 0,
			'IP': '0.0.0.0',
			'fanspeed': 0,
			'swingv': 0,
			'swingh': 0,
			'komp': 0,
			'hatar_low': 0,
			'hatar_top': 0,
			'target_off': True,
			'AC_jelenlet': None
		}
		self.Z_7_AC_H = self.AC_7_H.copy()


		self.AC_8_F = {
			'type': 0,
			'IP': '0.0.0.0',
			'fanspeed': 0,
			'swingv': 0,
			'swingh': 0,
			'komp': 0,
			'hatar_low': 0,
			'hatar_top': 0,
			'target_off': True,
			'AC_jelenlet': None
		}
		self.Z_8_AC_F = self.AC_8_F.copy()

		self.AC_8_H = {
			'type': 0,
			'IP': '0.0.0.0',
			'fanspeed': 0,
			'swingv': 0,
			'swingh': 0,
			'komp': 0,
			'hatar_low': 0,
			'hatar_top': 0,
			'target_off': True,
			'AC_jelenlet': None
		}
		self.Z_8_AC_H = self.AC_8_H.copy()


		self.AC_9_F = {
			'type': 0,
			'IP': '0.0.0.0',
			'fanspeed': 0,
			'swingv': 0,
			'swingh': 0,
			'komp': 0,
			'hatar_low': 0,
			'hatar_top': 0,
			'target_off': True,
			'AC_jelenlet': None
		}
		self.Z_9_AC_F = self.AC_9_F.copy()

		self.AC_9_H = {
			'type': 0,
			'IP': '0.0.0.0',
			'fanspeed': 0,
			'swingv': 0,
			'swingh': 0,
			'komp': 0,
			'hatar_low': 0,
			'hatar_top': 0,
			'target_off': True,
			'AC_jelenlet': None
		}
		self.Z_9_AC_H = self.AC_9_H.copy()


		self.AC_10_F = {
			'type': 0,
			'IP': '0.0.0.0',
			'fanspeed': 0,
			'swingv': 0,
			'swingh': 0,
			'komp': 0,
			'hatar_low': 0,
			'hatar_top': 0,
			'target_off': True,
			'AC_jelenlet': None
		}
		self.Z_10_AC_F = self.AC_10_F.copy()

		self.AC_10_H = {
			'type': 0,
			'IP': '0.0.0.0',
			'fanspeed': 0,
			'swingv': 0,
			'swingh': 0,
			'komp': 0,
			'hatar_low': 0,
			'hatar_top': 0,
			'target_off': True,
			'AC_jelenlet': None
		}
		self.Z_10_AC_H = self.AC_10_H.copy()


		self.AC_11_F = {
			'type': 0,
			'IP': '0.0.0.0',
			'fanspeed': 0,
			'swingv': 0,
			'swingh': 0,
			'komp': 0,
			'hatar_low': 0,
			'hatar_top': 0,
			'target_off': True,
			'AC_jelenlet': None
		}
		self.Z_11_AC_F = self.AC_11_F.copy()

		self.AC_11_H = {
			'type': 0,
			'IP': '0.0.0.0',
			'fanspeed': 0,
			'swingv': 0,
			'swingh': 0,
			'komp': 0,
			'hatar_low': 0,
			'hatar_top': 0,
			'target_off': True,
			'AC_jelenlet': None
		}
		self.Z_11_AC_H = self.AC_11_H.copy()


		self.AC_12_F = {
			'type': 0,
			'IP': '0.0.0.0',
			'fanspeed': 0,
			'swingv': 0,
			'swingh': 0,
			'komp': 0,
			'hatar_low': 0,
			'hatar_top': 0,
			'target_off': True,
			'AC_jelenlet': None
		}
		self.Z_12_AC_F = self.AC_12_F.copy()

		self.AC_12_H = {
			'type': 0,
			'IP': '0.0.0.0',
			'fanspeed': 0,
			'swingv': 0,
			'swingh': 0,
			'komp': 0,
			'hatar_low': 0,
			'hatar_top': 0,
			'target_off': True,
			'AC_jelenlet': None
		}
		self.Z_12_AC_H = self.AC_12_H.copy()

		self.switchTimer_dhw = 0
		self.dhw_time_run = False
		self.Elsodleges_M_On = False
		self.Masodlagos_M_On = False
		self.setVarDhwTimer = False
		self.HF_dif_felements = 3
		self.dhw_dif_felements = 3
		self.P_dif_felements = 3
		self.P_hiszterezis = 3.0
		self.disinfection_complete = False
		self.intemp_avglist = []
		self.TartalyAktuallist = []
		self.PufferAktuallist = []
		self.before_switch_1_time = 300
		self.before_switch_2_time = 300
		self.after_switch_1_time = 300
		self.after_switch_2_time = 300
		self.delayedActions = {} 
		self.buffer_external_F_limit = None
		self.buffer_external_H_limit = None
		self.hc_external_F_limit = None
		self.hc_external_H_limit = None
		self.buffer_external_time_F_limit = None
		self.buffer_external_time_H_limit = None
		self.hc_external_time_F_limit = None
		self.hc_external_time_H_limit = None
		self.callib_intemp = None
		self.callib_outtemp = None
		self.callib_heating_target = None
		self.callib_cooling_target = None
		self.callib_power = None
		self.heat_source_1 = None
		self.heat_source_2 = None
		self.met_data_string = []
		self.warmest_hours_dhw = []
		self.warmest_hours_buffer = []
		self.coldest_hours_buffer = []
		self.warmest_hours_hc = []
		self.coldest_hours_hc = []
		self.closest_temp = 0
		self.current_hour = datetime.now().hour
		self.p1_meter_actual = 0
		self.tartaly_max = 85.0
		self.buffer_max = 85.0
		self.buffer_min = 7.0
		self.F_max = 35.0
		self.H_min = 12.0
		self.kevero_max = 90.0
		self.kevero_min = 7.0
		self.hardware_id = None
		self.intemp_data = []
		self.outtemp_data = []
		self.heating_target_data = []
		self.cooling_target_data = []
		self.heat_source_1_data = []
		self.heat_source_2_data = []
		self.inertia = None
		self.dhwprior_F_H = False
		self.dhwprior_P = False
		self.heating_active = False
		self.cooling_active = False
		self.Elsodleges_P_F = []
		self.Elsodleges_P_H = []
		self.Elsodleges_PE = []
		self.Masodlagos_P_F = []
		self.Masodlagos_P_H = []
		self.Masodlagos_PE = []
		self.power_p_1 = 0
		self.ir_resend = 1
		self.ir_resend_counter = 0
		self.AktualTemp = []
		self.AktualThermostat = []
		self.aktual_watt = 0
		self.zone_1_heating_state = False
		self.zone_2_heating_state = False
		self.zone_3_heating_state = False
		self.zone_4_heating_state = False
		self.zone_5_heating_state = False
		self.zone_6_heating_state = False
		self.zone_7_heating_state = False
		self.zone_8_heating_state = False
		self.zone_9_heating_state = False
		self.zone_10_heating_state = False
		self.zone_11_heating_state = False
		self.zone_12_heating_state = False
		self.zone_1_cooling_state = False
		self.zone_2_cooling_state = False
		self.zone_3_cooling_state = False
		self.zone_4_cooling_state = False
		self.zone_5_cooling_state = False
		self.zone_6_cooling_state = False
		self.zone_7_cooling_state = False
		self.zone_8_cooling_state = False
		self.zone_9_cooling_state = False
		self.zone_10_cooling_state = False
		self.zone_11_cooling_state = False
		self.zone_12_cooling_state = False
		self.base_ids = {
			1: (4, 5, 8, 9, 126, 127, 128, 129),
			2: (38, 39, 40, 41, 132, 133, 134, 135),
			3: (42, 43, 44, 45, 136, 137, 138, 139),
			4: (46, 47, 48, 49, 140, 141, 142, 143),
			5: (50, 51, 52, 53, 144, 145, 146, 147),
			6: (54, 55, 56, 57, 148, 149, 150, 151),
			7: (162, 163, 164, 165, 166, 167, 168, 169),
			8: (170, 171, 172, 173, 174, 175, 176, 177),
			9: (178, 179, 180, 181, 182, 183, 184, 185),
			10: (186, 187, 188, 189, 190, 191, 192, 193),
			11: (194, 195, 196, 197, 198, 199, 200, 201),
			12: (202, 203, 204, 205, 206, 207, 208, 209),
		}
		return

	def onStart(self) :

		global tl
		tl = TranslationLoader(Parameters["Language"])

		self.location = Settings["Location"].split(";")

		self.hardware_id = Parameters["HardwareID"]

		# Unpack parameters | Paraméterek kibontása
		params = parseCSVparams(Parameters["Mode6"])
		self.lenparams = parseCSVparams(Parameters["Mode6"])
		self.debuglevel = int(params[0])
		self.nextupdatetime = int(params[1])
		self.calculate_period = int(params[2])
		self.power_p_1 = int(params[3])
		if len(params) > 4 :
			self.jelenlet = params[4]

		# Set logging level | Naplózási szint beállítása
		try:
			debuglevel = self.debuglevel
		except ValueError:
			debuglevel = 0
			self.loglevel = "None"
		if debuglevel != 0:
			self.debug = True
			Domoticz.Debugging(debuglevel)
			DumpConfigToLog()
			self.loglevel = "Verbose"
		else:
			self.debug = False
			Domoticz.Debugging(0)

		# Create devices if they do not already exist | Eszközök létrehozása, ha még nem léteznek
		devicecreated = []
		if 88 not in Devices:
			Options = {"LevelActions": "||",
				"LevelNames": tl.t("Off|Heating-Cooling|Heating-Cooling + DHW|Heating-Cooling + Buffer|Heating-Cooling + DHW + Buffer|DHW"),
				"LevelOffHidden": "true",
				"SelectorStyle": "1"}
			Domoticz.Device(Name= tl.t("System mode"), Unit=88, TypeName="Selector Switch", Switchtype=18, Image=15, Options=Options, Used=1).Create()
			devicecreated.append(deviceparam(88, 0, "10"))
		if 1 not in Devices:
			Options = {"LevelActions": "||",
				"LevelNames": tl.t("Off|Device 1|Device 2|Switch mode based on indoor temperature|Switch mode based on outdoor temperature|Switch mode based on outdoor dew point|Dual mode based on indoor temperature|Dual mode based on outdoor temperature|Dual mode based on outdoor dew point|Saver mode based on indoor and outdoor temperature|Saver mode based on indoor temperature and outdoor dew point|Switch mode min. 500 W for return|Switch mode min. 1000 W for return|Switch mode min. 1500 W for return|Switch mode min. 2000 W for return|Switch mode min. 3000 W for return|Switch mode min. 4000 W for return|Switch mode min. 5000 W for return|Dual mode min. 500 W for return|Dual mode min. 1000 W for return|Dual mode min. 1500 W for return|Dual mode min. 2000 W for return|Dual mode min. 3000 W for return|Dual mode min. 4000 W for return|Dual mode min. 5000 W for return"),
				"LevelOffHidden": "false",
				"SelectorStyle": "1"}
			Domoticz.Device(Name= tl.t("Heating thermostat"), Unit=1, TypeName="Selector Switch", Switchtype=18, Image=15, Options=Options, Used=1).Create()
			devicecreated.append(deviceparam(1, 0, "0"))
			self.addfavorite(Devices[1].ID)
		if 22 not in Devices:
			Options = {"LevelActions": "||",
				"LevelNames": tl.t("Off|Device 1|Device 2|Switch mode based on indoor temperature|Switch mode based on outdoor temperature|Dual mode based on indoor temperature|Dual mode based on outdoor temperature|Saver mode based on indoor and outdoor temperature|Switch mode min. 500 W for return|Switch mode min. 1000 W for return|Switch mode min. 1500 W for return|Switch mode min. 2000 W for return|Switch mode min. 3000 W for return|Switch mode min. 4000 W for return|Switch mode min. 5000 W for return|Dual mode min. 500 W for return|Dual mode min. 1000 W for return|Dual mode min. 1500 W for return|Dual mode min. 2000 W for return|Dual mode min. 3000 W for return|Dual mode min. 4000 W for return|Dual mode min. 5000 W for return"),
				"LevelOffHidden": "false",
				"SelectorStyle": "1"}
			Domoticz.Device(Name= tl.t("Cooling thermostat"), Unit=22, TypeName="Selector Switch", Switchtype=18, Image=15, Options=Options, Used=1).Create()
			devicecreated.append(deviceparam(22, 0, "0"))
			self.addfavorite(Devices[22].ID)
		if 58 not in Devices:
			Options = {"LevelActions": "||",
					   "LevelNames": tl.t("Off|Heating|Cooling"),
					   "LevelOffHidden": "true",
					   "SelectorStyle": "0"}
			Domoticz.Device(Name= tl.t("Mode"), Unit=58, TypeName="Selector Switch", Switchtype=18, Image=15, Options=Options, Used=1).Create()
			devicecreated.append(deviceparam(58, 0, "10"))
			self.addfavorite(Devices[58].ID)
		if 2 not in Devices:
			Options = {"LevelActions": "||",
					   "LevelNames": tl.t("Off|Normal|Economy"),
					   "LevelOffHidden": "true",
					   "SelectorStyle": "0"}
			Domoticz.Device(Name= tl.t("Heating - Cooling mode"), Unit=2, TypeName="Selector Switch", Switchtype=18, Image=15, Options=Options, Used=1).Create()
			devicecreated.append(deviceparam(2, 0, "10"))
			self.addfavorite(Devices[2].ID)
		if 112 not in Devices:
			Options = {"LevelActions": "||",
					   "LevelNames": tl.t("Off| x 1| x 2| x 3| x 4| x 5"),
					   "LevelOffHidden": "true",
					   "SelectorStyle": "0"}
			Domoticz.Device(Name= tl.t("Cooling-heating secondary differential elements"), Unit=112, TypeName="Selector Switch", Switchtype=18, Image=15, Options=Options, Used=0).Create()
			devicecreated.append(deviceparam(112, 0, "30"))
		if 124 not in Devices:
			Options = {"LevelActions": "||",
					   "LevelNames": tl.t("Off|-5°C|0°C|7°C|15°C|20°C|aut 6 hour|aut 8 hour|aut 12 hour"),
					   "SelectorStyle": "1"}
			Domoticz.Device(Name= tl.t("Heating target external temperature dependent"), Unit=124, TypeName="Selector Switch", Switchtype=18, Image=15, Options=Options, Used=0).Create()
			devicecreated.append(deviceparam(124, 0, "0"))
		if 130 not in Devices:
			Options = {"LevelActions": "||",
					   "LevelNames": tl.t("Off|20°C|22°C|24°C|26°C|28°C|aut 6 hour|aut 8 hour|aut 12 hour"),
					   "SelectorStyle": "1"}
			Domoticz.Device(Name= tl.t("Cooling target external temperature dependent"), Unit=130, TypeName="Selector Switch", Switchtype=18, Image=15, Options=Options, Used=0).Create()
			devicecreated.append(deviceparam(130, 0, "0"))
		if 125 not in Devices:
			Options = {"LevelActions": "||",
					   "LevelNames": tl.t("Off|500|1000|2000|3000|4000|5000"),
					   "SelectorStyle": "0"}
			Domoticz.Device(Name= tl.t("Solar limit, Heating - Cooling (Watt)"), Unit=125, TypeName="Selector Switch", Switchtype=18, Image=15, Options=Options, Used=0).Create()
			devicecreated.append(deviceparam(125, 0, "0"))
		if 3 not in Devices:
			Domoticz.Device(Name= tl.t("Heating-colling, dual temperature difference value"), Unit=3, Type=242, Subtype=1, Options={"ValueMin": "0", "ValueMax": "15", "ValueStep": "0.1", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(3, 0, "1"))
		if 7 not in Devices:
			Domoticz.Device(Name= tl.t("Heating 2. device switching limit"), Unit=7, Type=242, Subtype=1, Options={"ValueMin": "-40", "ValueMax": "50", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(7, 0, "-5"))
		if 252 not in Devices:
			Domoticz.Device(Name= tl.t("Cooling 2. device switching limit"), Unit=252, Type=242, Subtype=1, Options={"ValueMin": "-40", "ValueMax": "50", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(252, 0, "28"))
		if 225 not in Devices:
			Domoticz.Device(Name= tl.t("DHW 2. device switching limit"), Unit=225, Type=242, Subtype=1, Options={"ValueMin": "-40", "ValueMax": "50", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(225, 0, "-5"))
		if 227 not in Devices:
			Domoticz.Device(Name= tl.t("Buffer 2. device switching limit"), Unit=227, Type=242, Subtype=1, Options={"ValueMin": "-40", "ValueMax": "50", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(227, 0, "-5"))
		if 6 not in Devices:
			Domoticz.Device(Name= tl.t("Calculated current temperature"), Unit=6, TypeName="Temperature", Used=1).Create()
			devicecreated.append(deviceparam(6, 0, "20"))
		
		if 10 not in Devices:
			Domoticz.Device(Name= tl.t("Heating target temperature"), Unit=10, TypeName="Temperature", Used=1).Create()
			devicecreated.append(deviceparam(10, 0, "20"))
		if 18 not in Devices:
			Domoticz.Device(Name= tl.t("Cooling-heating external hysteresis"), Unit=18, Type=242, Subtype=1, Options={"ValueMin": "0", "ValueMax": "5", "ValueStep": "0.1", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(18, 0, "0.5"))
		if 12 not in Devices:
			Options = {"LevelActions": "||",
					"LevelNames": tl.t("Off|Turned Off|Turned On"),
					"LevelOffHidden": "true",
					"SelectorStyle": "0"}
			Domoticz.Device(Name= tl.t("Heating presence detection mode"), Unit=12, TypeName="Selector Switch", Switchtype=18, Image=18, Options=Options, Used=1).Create()
			devicecreated.append(deviceparam(12, 0, "10"))
		if 13 not in Devices:
			Options = {"LevelActions": "||",
					   "LevelNames": tl.t("Off|Device 1|Device 2|Switch mode based on tank temperature|Switch mode based on outdoor temperature|Switch mode based on outdoor dew point|Dual mode based on tank temperature|Dual mode based on outdoor temperature|Dual mode based on outdoor dew point|Saver mode based on tank temperature and outdoor temperature|Saver mode based on tank temperature and outdoor dew point|Switch mode min. 500 W for return|Switch mode min. 1000 W for return|Switch mode min. 1500 W for return|Switch mode min. 2000 W for return|Switch mode min. 3000 W for return|Switch mode min. 4000 W for return|Switch mode min. 5000 W for return|Dual mode min. 500 W for return|Dual mode min. 1000 W for return|Dual mode min. 1500 W for return|Dual mode min. 2000 W for return|Dual mode min. 3000 W for return|Dual mode min. 4000 W for return|Dual mode min. 5000 W for return"),
					   "LevelOffHidden": "false",
					   "SelectorStyle": "1"}
			Domoticz.Device(Name= tl.t("DHW (Domestic Hot Water)"), Unit=13, TypeName="Selector Switch", Switchtype=18, Image=15, Options=Options, Used=1).Create()
			devicecreated.append(deviceparam(13, 0, "0"))
			self.addfavorite(Devices[13].ID)
		if 221 not in Devices:
			Domoticz.Device(Name= tl.t("Cooling-Heating 1st dew point compensation"), Unit=221, Type=242, Subtype=1, Options={"ValueMin": "-15", "ValueMax": "15", "ValueStep": "0.1", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(221, 0, "0"))
		if 222 not in Devices:
			Domoticz.Device(Name= tl.t("DHW dew point compensation"), Unit=222, Type=242, Subtype=1, Options={"ValueMin": "-15", "ValueMax": "15", "ValueStep": "0.1", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(222, 0, "0"))
		if 223 not in Devices:
			Domoticz.Device(Name= tl.t("Buffer dew point compensation"), Unit=223, Type=242, Subtype=1, Options={"ValueMin": "-15", "ValueMax": "15", "ValueStep": "0.1", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(223, 0, "0"))
		if 11 not in Devices:
			Domoticz.Device(Name= tl.t("Current power value"), Unit=11, Type=243, Subtype=6, Used=0).Create()
			devicecreated.append(deviceparam(11, 0, "0"))
		if 14 not in Devices:
			Domoticz.Device(Name= tl.t("DHW normal tank temperature"), Unit=14, Type=242, Subtype=1, Options={"ValueMin": "20", "ValueMax": "85", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=0).Create()
			devicecreated.append(deviceparam(14, 0, "45"))
		if 30 not in Devices:
			Domoticz.Device(Name= tl.t("DHW economical tank temperature"), Unit=30, Type=242, Subtype=1, Options={"ValueMin": "20", "ValueMax": "85", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(30, 0, "40"))
		if 76 not in Devices:
			Domoticz.Device(Name= tl.t("DHW disinfection temperature"), Unit=76, Type=242, Subtype=1, Options={"ValueMin": "50", "ValueMax": "85", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(76 ,0, "65"))
		if 15 not in Devices:
			Domoticz.Device(Name= tl.t("DHW external hysteresis"), Unit=15, Type=242, Subtype=1, Options={"ValueMin": "0", "ValueMax": "5", "ValueStep": "0.1", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(15, 0, "0.5"))
		if 16 not in Devices:
			Domoticz.Device(Name= tl.t("DHW 1. device switching temperature"), Unit=16, Type=242, Subtype=1, Options={"ValueMin": "-40", "ValueMax": "50", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(16 ,0, "-5.0"))
		if 17 not in Devices:
			Domoticz.Device(Name= tl.t("DHW tank hysteresis"), Unit=17, Type=242, Subtype=1, Options={"ValueMin": "0", "ValueMax": "5", "ValueStep": "0.1", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(17 ,0, "3"))
		if 80 not in Devices:
			Domoticz.Device(Name= tl.t("DHW hysteresis solar panel"), Unit=80, Type=242, Subtype=1, Options={"ValueMin": "0", "ValueMax": "5", "ValueStep": "0.1", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(80 ,0, "0.5"))
		if 81 not in Devices:
			Domoticz.Device(Name= tl.t("DHW temperature at solar panel"), Unit=81, Type=242, Subtype=1, Options={"ValueMin": "20", "ValueMax": "85", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(81 ,0, "50"))
		if 79 not in Devices:
			Domoticz.Device(Name= tl.t("DHW heating purpose depends on outside temperature"), Unit=79, Type=242, Subtype=1, Options={"ValueMin": "20", "ValueMax": "85", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(79, 0, "45"))
		if 31 not in Devices:
			Domoticz.Device(Name= tl.t("DHW target external switching hysteresis"), Unit=31, Type=242, Subtype=1, Options={"ValueMin": "0", "ValueMax": "5", "ValueStep": "0.1", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(31, 0, "1"))
		if 19 not in Devices:
			Domoticz.Device(Name= tl.t("Calculated current tank temperature"), Unit=19, TypeName="Temperature", Used=0).Create()
			devicecreated.append(deviceparam(19, 0, "20"))
		if 20 not in Devices:
			Domoticz.Device(Name= tl.t("Cooling target temperature"), Unit=20, TypeName="Temperature", Used=0).Create()
			devicecreated.append(deviceparam(20, 0, "24"))
		if 21 not in Devices:
			Domoticz.Device(Name= tl.t("Tank current target temperature"), Unit=21, TypeName="Temperature", Used=0).Create()
			devicecreated.append(deviceparam(21, 0, "50"))
		if 23 not in Devices:
			Domoticz.Device(Name="1 F", Unit=23, Type=244, Subtype=73, Switchtype=0, Used=0).Create()
			devicecreated.append(deviceparam(23, 0, "Off"))
		if 24 not in Devices:
			Domoticz.Device(Name="1 M", Unit=24, Type=244, Subtype=73, Switchtype=0, Used=0).Create()
			devicecreated.append(deviceparam(24, 0, "Off"))
		if 25 not in Devices:
			Domoticz.Device(Name="1 H", Unit=25, Type=244, Subtype=73, Switchtype=0, Used=0).Create()
			devicecreated.append(deviceparam(25, 0, "Off"))
		if 26 not in Devices:
			Domoticz.Device(Name="2 F", Unit=26, Type=244, Subtype=73, Switchtype=0, Used=0).Create()
			devicecreated.append(deviceparam(26, 0, "Off"))
		if 27 not in Devices:
			Domoticz.Device(Name="2 M", Unit=27, Type=244, Subtype=73, Switchtype=0, Used=0).Create()
			devicecreated.append(deviceparam(27, 0, "Off"))
		if 28 not in Devices:
			Domoticz.Device(Name="2 H", Unit=28, Type=244, Subtype=73, Switchtype=0, Used=0).Create()
			devicecreated.append(deviceparam(28, 0, "Off"))
		if 32 not in Devices:
			Options = {"LevelActions": "||",
					   "LevelNames": tl.t("Off|Normal|Economy"),
					   "LevelOffHidden": "true",
					   "SelectorStyle": "0"}
			Domoticz.Device(Name= tl.t("DHW mode"), Unit=32, TypeName="Selector Switch", Switchtype=18, Image=15, Options=Options, Used=1).Create()
			devicecreated.append(deviceparam(32, 0, "10"))
			self.addfavorite(Devices[32].ID)
		if 29 not in Devices:
			Options = {"LevelActions": "||",
					   "LevelNames": tl.t("Off|Turned Off|Turned On"),
					   "LevelOffHidden": "true",
					   "SelectorStyle": "0"}
			Domoticz.Device(Name= tl.t("DHW presence detection mode"), Unit=29, TypeName="Selector Switch", Switchtype=18, Image=18, Options=Options, Used=1).Create()
			devicecreated.append(deviceparam(29, 0, "10"))
		if 113 not in Devices:
			Options = {"LevelActions": "||",
					   "LevelNames": tl.t("Off|x1|x2|x3|x4|x5|x6|x7|x8|x9|x10"),
					   "LevelOffHidden": "true",
					   "SelectorStyle": "1"}
			Domoticz.Device(Name= tl.t("DHW secondary differential elements"), Unit=113, TypeName="Selector Switch", Switchtype=18, Image=15, Options=Options, Used=0).Create()
			devicecreated.append(deviceparam(113, 0, "30"))
		if 33 not in Devices:
			Domoticz.Device(Name="1 E", Unit=33, Type=244, Subtype=73, Switchtype=0, Used=0).Create()
			devicecreated.append(deviceparam(33, 0, "Off"))
		if 34 not in Devices:
			Domoticz.Device(Name="2 E", Unit=34, Type=244, Subtype=73, Switchtype=0, Used=0).Create()
			devicecreated.append(deviceparam(34, 0, "Off"))
		if 160 not in Devices:
			Domoticz.Device(Name="1 PE", Unit=160, Type=244, Subtype=73, Switchtype=0, Used=0).Create()
			devicecreated.append(deviceparam(160, 0, "Off"))
		if 161 not in Devices:
			Domoticz.Device(Name="2 PE", Unit=161, Type=244, Subtype=73, Switchtype=0, Used=0).Create()
			devicecreated.append(deviceparam(161, 0, "Off"))
		if 35 not in Devices:
			Domoticz.Device(Name= tl.t("DHW device 1 external E cartridge switching limit"), Unit=35, Type=242, Subtype=1, Options={"ValueMin": "-40", "ValueMax": "50", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(35, 0, "15"))
		if 36 not in Devices:
			Domoticz.Device(Name= tl.t("DHW device 2 external E cartridge switching limit"), Unit=36, Type=242, Subtype=1, Options={"ValueMin": "-40", "ValueMax": "50", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(36, 0, "15"))
		if 115 not in Devices:
			Domoticz.Device(Name= tl.t("DHW device 1 tank E cartridge switching limit"), Unit=115, Type=242, Subtype=1, Options={"ValueMin": "-40", "ValueMax": "50", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(115, 0, "45"))
		if 116 not in Devices:
			Domoticz.Device(Name= tl.t("DHW device 2 tank E cartridge switching limit"), Unit=116, Type=242, Subtype=1, Options={"ValueMin": "-40", "ValueMax": "50", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(116, 0, "45"))
		if 37 not in Devices:
			Domoticz.Device(Name= tl.t("DHW dual temperature diff"), Unit=37, Type=242, Subtype=1, Options={"ValueMin": "0", "ValueMax": "15", "ValueStep": "0.1", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(37, 0, "2"))
		if 101 not in Devices:
			Options = {"LevelActions": "||",
					   "LevelNames": tl.t("Off|Mixing valve|Buffer"),
					   "LevelOffHidden": "false",
					   "SelectorStyle": "0"}
			Domoticz.Device(Name= tl.t("Dew point based regulation"), Unit=101, TypeName="Selector Switch", Switchtype=18, Image=16, Options=Options, Used=1).Create()
			devicecreated.append(deviceparam(101, 0, "10"))

		if 64 not in Devices:
			Domoticz.Device(Name=tl.t("Heating hysteresis"), Unit=64, Type=242, Subtype=1, Options={"ValueMin": "0", "ValueMax": "5", "ValueStep": "0.1", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(64 ,0, "0.1"))
		if 216 not in Devices:
			Domoticz.Device(Name=tl.t("Cooling hysteresis"), Unit=216, Type=242, Subtype=1, Options={"ValueMin": "0", "ValueMax": "5", "ValueStep": "0.1", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(216 ,0, "0.2"))
		if 155 not in Devices:
			Domoticz.Device(Name=tl.t("Automatic target value + -"), Unit=155, Type=242, Subtype=1, Options={"ValueMin": "0", "ValueMax": "10", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(155 ,0, "1"))
		if 67 not in Devices:
			Domoticz.Device(Name= tl.t("Room max. difference"), Unit=67, Type=242, Subtype=1, Options={"ValueMin": "0", "ValueMax": "15", "ValueStep": "0.1", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(67 ,0, "1"))
		if 213 not in Devices:
			Domoticz.Device(Name= tl.t("Health cooling value"), Unit=213, Type=242, Subtype=1, Options={"ValueMin": "0", "ValueMax": "20", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(213 ,0, "10"))
		if 214 not in Devices:
			Options = {"LevelActions": "||",
					   "LevelNames": tl.t("Off|On"),
					   "LevelOffHidden": "false",
					   "SelectorStyle": "0"}
			Domoticz.Device(Name= tl.t("Sanitary cooling limit"), Unit=214, TypeName="Selector Switch", Switchtype=18, Image=15, Options=Options, Used=1).Create()
			devicecreated.append(deviceparam(214, 0, "0"))
		if 215 not in Devices:
			Options = {"LevelActions": "||",
					   "LevelNames": tl.t("Off|Device 1|Device 2"),
					   "LevelOffHidden": "true",
					   "SelectorStyle": "0"}
			Domoticz.Device(Name= tl.t("Air conditioning operation device"), Unit=215, TypeName="Selector Switch", Switchtype=18, Image=15, Options=Options, Used=1).Create()
			devicecreated.append(deviceparam(215, 0, "10"))
		
		# Zone 1 | 1. zóna
		if 4 not in Devices:
			Domoticz.Device(Name= tl.t("Zone 1 normal heating temperature"), Unit=4, Type=242, Subtype=1, Options={"ValueMin": "5", "ValueMax": "35", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(4, 0, "22"))
		if 5 not in Devices:
			Domoticz.Device(Name= tl.t("Zone 1 economical heating temperature"), Unit=5, Type=242, Subtype=1, Options={"ValueMin": "5", "ValueMax": "35", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(5 ,0, "20"))
		if 8 not in Devices:
			Domoticz.Device(Name= tl.t("Zone 1 normal cooling temperature"), Unit=8, Type=242, Subtype=1, Options={"ValueMin": "5", "ValueMax": "35", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(8, 0, "24"))
		if 9 not in Devices:
			Domoticz.Device(Name= tl.t("Zone 1 economical cooling temperature"), Unit=9, Type=242, Subtype=1, Options={"ValueMin": "5", "ValueMax": "35", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(9, 0, "26"))
		if 126 not in Devices:
			Domoticz.Device(Name= tl.t("Zone 1 heating + at solar limit"), Unit=126, Type=242, Subtype=1, Options={"ValueMin": "-10", "ValueMax": "10", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(126, 0, "2"))
		if 127 not in Devices:
			Domoticz.Device(Name= tl.t("Zone 1 cooling - at solar limit"), Unit=127, Type=242, Subtype=1, Options={"ValueMin": "-10", "ValueMax": "10", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(127, 0, "-2"))
		if 128 not in Devices:
			Domoticz.Device(Name= tl.t("Zone 1 heating + at external temperature dependent"), Unit=128, Type=242, Subtype=1, Options={"ValueMin": "-10", "ValueMax": "10", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(128, 0, "1"))
		if 129 not in Devices:
			Domoticz.Device(Name= tl.t("Zone 1 cooling - at external temperature dependent"), Unit=129, Type=242, Subtype=1, Options={"ValueMin": "-10", "ValueMax": "10", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(129, 0, "-1"))
		# Zone 2 | 2. zóna
		if 38 not in Devices:
			Domoticz.Device(Name=tl.t("Zone 2 normal heating temperature"), Unit=38, Type=242, Subtype=1, Options={"ValueMin": "5", "ValueMax": "35", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(38, 0, "22"))
		if 39 not in Devices:
			Domoticz.Device(Name= tl.t("Zone 2 economical heating temperature"), Unit=39, Type=242, Subtype=1, Options={"ValueMin": "5", "ValueMax": "35", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(39 ,0, "20"))
		if 40 not in Devices:
			Domoticz.Device(Name= tl.t("Zone 2 normal cooling temperature"), Unit=40, Type=242, Subtype=1, Options={"ValueMin": "5", "ValueMax": "35", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(40, 0, "24"))
		if 41 not in Devices:
			Domoticz.Device(Name= tl.t("Zone 2 economical cooling temperature"), Unit=41, Type=242, Subtype=1, Options={"ValueMin": "5", "ValueMax": "35", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(41, 0, "26"))
		if 132 not in Devices:
			Domoticz.Device(Name= tl.t("Zone 2 heating + at solar limit"), Unit=132, Type=242, Subtype=1, Options={"ValueMin": "-10", "ValueMax": "10", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(132, 0, "2"))
		if 133 not in Devices:
			Domoticz.Device(Name= tl.t("Zone 2 cooling - at solar limit"), Unit=133, Type=242, Subtype=1, Options={"ValueMin": "-10", "ValueMax": "10", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(133, 0, "-2"))
		if 134 not in Devices:
			Domoticz.Device(Name= tl.t("Zone 2 heating + at external temperature dependent"), Unit=134, Type=242, Subtype=1, Options={"ValueMin": "-10", "ValueMax": "10", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(134, 0, "1"))
		if 135 not in Devices:
			Domoticz.Device(Name= tl.t("Zone 2 cooling - at external temperature dependent"), Unit=135, Type=242, Subtype=1, Options={"ValueMin": "-10", "ValueMax": "10", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(135, 0, "-1"))
		# Zone 3 | 3. zóna
		if 42 not in Devices:
			Domoticz.Device(Name=tl.t("Zone 3 normal heating temperature"), Unit=42, Type=242, Subtype=1, Options={"ValueMin": "5", "ValueMax": "35", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(42, 0, "22"))
		if 43 not in Devices:
			Domoticz.Device(Name= tl.t("Zone 3 economical heating temperature"), Unit=43, Type=242, Subtype=1, Options={"ValueMin": "5", "ValueMax": "35", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(43 ,0, "20"))
		if 44 not in Devices:
			Domoticz.Device(Name= tl.t("Zone 3 normal cooling temperature"), Unit=44, Type=242, Subtype=1, Options={"ValueMin": "5", "ValueMax": "35", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(44, 0, "24"))
		if 45 not in Devices:
			Domoticz.Device(Name= tl.t("Zone 3 economical cooling temperature"), Unit=45, Type=242, Subtype=1, Options={"ValueMin": "5", "ValueMax": "35", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(45, 0, "26"))
		if 136 not in Devices:
			Domoticz.Device(Name= tl.t("Zone 3 heating + at solar limit"), Unit=136, Type=242, Subtype=1, Options={"ValueMin": "-10", "ValueMax": "10", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(136, 0, "2"))
		if 137 not in Devices:
			Domoticz.Device(Name= tl.t("Zone 3 cooling - at solar limit"), Unit=137, Type=242, Subtype=1, Options={"ValueMin": "-10", "ValueMax": "10", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(137, 0, "-2"))
		if 138 not in Devices:
			Domoticz.Device(Name= tl.t("Zone 3 heating + at external temperature dependent"), Unit=138, Type=242, Subtype=1, Options={"ValueMin": "-10", "ValueMax": "10", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(138, 0, "1"))
		if 139 not in Devices:
			Domoticz.Device(Name= tl.t("Zone 3 cooling - at external temperature dependent"), Unit=139, Type=242, Subtype=1, Options={"ValueMin": "-10", "ValueMax": "10", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(139, 0, "-1"))
		# Zone 4 | 4. zóna
		if 46 not in Devices:
			Domoticz.Device(Name= tl.t("Zone 4 normal heating temperature"), Unit=46, Type=242, Subtype=1, Options={"ValueMin": "5", "ValueMax": "35", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(46, 0, "22"))
		if 47 not in Devices:
			Domoticz.Device(Name= tl.t("Zone 4 economical heating temperature"), Unit=47, Type=242, Subtype=1, Options={"ValueMin": "5", "ValueMax": "35", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(47 ,0, "20"))
		if 48 not in Devices:
			Domoticz.Device(Name= tl.t("Zone 4 normal cooling temperature"), Unit=48, Type=242, Subtype=1, Options={"ValueMin": "5", "ValueMax": "35", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(48, 0, "24"))
		if 49 not in Devices:
			Domoticz.Device(Name= tl.t("Zone 4 economical cooling temperature"), Unit=49, Type=242, Subtype=1, Options={"ValueMin": "5", "ValueMax": "35", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(49, 0, "26"))
		if 140 not in Devices:
			Domoticz.Device(Name= tl.t("Zone 4 heating + at solar limit"), Unit=140, Type=242, Subtype=1, Options={"ValueMin": "-10", "ValueMax": "10", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(140, 0, "2"))
		if 141 not in Devices:
			Domoticz.Device(Name= tl.t("Zone 4 cooling - at solar limit"), Unit=141, Type=242, Subtype=1, Options={"ValueMin": "-10", "ValueMax": "10", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(141, 0, "-2"))
		if 142 not in Devices:
			Domoticz.Device(Name= tl.t("Zone 4 heating + at external temperature dependent"), Unit=142, Type=242, Subtype=1, Options={"ValueMin": "-10", "ValueMax": "10", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(142, 0, "1"))
		if 143 not in Devices:
			Domoticz.Device(Name= tl.t("Zone 4 cooling - at external temperature dependent"), Unit=143, Type=242, Subtype=1, Options={"ValueMin": "-10", "ValueMax": "10", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(143, 0, "-1"))
		# Zone 5 | 5. zóna
		if 50 not in Devices:
			Domoticz.Device(Name=tl.t("Zone 5 normal heating temperature"), Unit=50, Type=242, Subtype=1, Options={"ValueMin": "5", "ValueMax": "35", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(50, 0, "22"))
		if 51 not in Devices:
			Domoticz.Device(Name= tl.t("Zone 5 economical heating temperature"), Unit=51, Type=242, Subtype=1, Options={"ValueMin": "5", "ValueMax": "35", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(51 ,0, "20"))
		if 52 not in Devices:
			Domoticz.Device(Name= tl.t("Zone 5 normal cooling temperature"), Unit=52, Type=242, Subtype=1, Options={"ValueMin": "5", "ValueMax": "35", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(52, 0, "24"))
		if 53 not in Devices:
			Domoticz.Device(Name= tl.t("Zone 5 economical cooling temperature"), Unit=53, Type=242, Subtype=1, Options={"ValueMin": "5", "ValueMax": "35", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(53, 0, "26"))
		if 144 not in Devices:
			Domoticz.Device(Name= tl.t("Zone 5 heating + at solar limit"), Unit=144, Type=242, Subtype=1, Options={"ValueMin": "-10", "ValueMax": "10", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(144, 0, "2"))
		if 145 not in Devices:
			Domoticz.Device(Name= tl.t("Zone 5 cooling - at solar limit"), Unit=145, Type=242, Subtype=1, Options={"ValueMin": "-10", "ValueMax": "10", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(145, 0, "-2"))
		if 146 not in Devices:
			Domoticz.Device(Name= tl.t("Zone 5 heating + at external temperature dependent"), Unit=146, Type=242, Subtype=1, Options={"ValueMin": "-10", "ValueMax": "10", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(146, 0, "1"))
		if 147 not in Devices:
			Domoticz.Device(Name= tl.t("Zone 5 cooling - at external temperature dependent"), Unit=147, Type=242, Subtype=1, Options={"ValueMin": "-10", "ValueMax": "10", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(147, 0, "-1"))
		# Zone 6 | 6. zóna
		if 54 not in Devices:
			Domoticz.Device(Name=tl.t("Zone 6 normal heating temperature"), Unit=54, Type=242, Subtype=1, Options={"ValueMin": "5", "ValueMax": "35", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(54, 0, "22"))
		if 55 not in Devices:
			Domoticz.Device(Name= tl.t("Zone 6 economical heating temperature"), Unit=55, Type=242, Subtype=1, Options={"ValueMin": "5", "ValueMax": "35", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(55 ,0, "20"))
		if 56 not in Devices:
			Domoticz.Device(Name= tl.t("Zone 6 normal cooling temperature"), Unit=56, Type=242, Subtype=1, Options={"ValueMin": "5", "ValueMax": "35", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(56, 0, "24"))
		if 57 not in Devices:
			Domoticz.Device(Name= tl.t("Zone 6 economical cooling temperature"), Unit=57, Type=242, Subtype=1, Options={"ValueMin": "5", "ValueMax": "35", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(57, 0, "26"))
		if 148 not in Devices:
			Domoticz.Device(Name= tl.t("Zone 6 heating + at solar limit"), Unit=148, Type=242, Subtype=1, Options={"ValueMin": "-10", "ValueMax": "10", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(148, 0, "2"))
		if 149 not in Devices:
			Domoticz.Device(Name= tl.t("Zone 6 cooling - at solar limit"), Unit=149, Type=242, Subtype=1, Options={"ValueMin": "-10", "ValueMax": "10", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(149, 0, "-2"))
		if 150 not in Devices:
			Domoticz.Device(Name= tl.t("Zone 6 heating + at external temperature dependent"), Unit=150, Type=242, Subtype=1, Options={"ValueMin": "-10", "ValueMax": "10", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(150, 0, "1"))
		if 151 not in Devices:
			Domoticz.Device(Name= tl.t("Zone 6 cooling - at external temperature dependent"), Unit=151, Type=242, Subtype=1, Options={"ValueMin": "-10", "ValueMax": "10", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(151, 0, "-1"))
		# Zone 7 | 7. zóna
		if 162 not in Devices:
			Domoticz.Device(Name=tl.t("Zone 7 normal heating temperature"), Unit=162, Type=242, Subtype=1, Options={"ValueMin": "5", "ValueMax": "35", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(162, 0, "22"))
		if 163 not in Devices:
			Domoticz.Device(Name= tl.t("Zone 7 economical heating temperature"), Unit=163, Type=242, Subtype=1, Options={"ValueMin": "5", "ValueMax": "35", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(163 ,0, "20"))
		if 164 not in Devices:
			Domoticz.Device(Name= tl.t("Zone 7 normal cooling temperature"), Unit=164, Type=242, Subtype=1, Options={"ValueMin": "5", "ValueMax": "35", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(164, 0, "24"))
		if 165 not in Devices:
			Domoticz.Device(Name= tl.t("Zone 7 economical cooling temperature"), Unit=165, Type=242, Subtype=1, Options={"ValueMin": "5", "ValueMax": "35", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(165, 0, "26"))
		if 166 not in Devices:
			Domoticz.Device(Name= tl.t("Zone 7 heating + at solar limit"), Unit=166, Type=242, Subtype=1, Options={"ValueMin": "-10", "ValueMax": "10", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(166, 0, "2"))
		if 167 not in Devices:
			Domoticz.Device(Name= tl.t("Zone 7 cooling - at solar limit"), Unit=167, Type=242, Subtype=1, Options={"ValueMin": "-10", "ValueMax": "10", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(167, 0, "-2"))
		if 168 not in Devices:
			Domoticz.Device(Name= tl.t("Zone 7 heating + at external temperature dependent"), Unit=168, Type=242, Subtype=1, Options={"ValueMin": "-10", "ValueMax": "10", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(168, 0, "1"))
		if 169 not in Devices:
			Domoticz.Device(Name= tl.t("Zone 7 cooling - at external temperature dependent"), Unit=169, Type=242, Subtype=1, Options={"ValueMin": "-10", "ValueMax": "10", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(169, 0, "-1"))
		# Zone 8 | 8. zóna
		if 170 not in Devices:
			Domoticz.Device(Name=tl.t("Zone 8 normal heating temperature"), Unit=170, Type=242, Subtype=1, Options={"ValueMin": "5", "ValueMax": "35", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(170, 0, "22"))
		if 171 not in Devices:
			Domoticz.Device(Name= tl.t("Zone 8 economical heating temperature"), Unit=171, Type=242, Subtype=1, Options={"ValueMin": "5", "ValueMax": "35", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(171 ,0, "20"))
		if 172 not in Devices:
			Domoticz.Device(Name= tl.t("Zone 8 normal cooling temperature"), Unit=172, Type=242, Subtype=1, Options={"ValueMin": "5", "ValueMax": "35", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(172, 0, "24"))
		if 173 not in Devices:
			Domoticz.Device(Name= tl.t("Zone 8 economical cooling temperature"), Unit=173, Type=242, Subtype=1, Options={"ValueMin": "5", "ValueMax": "35", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(173, 0, "26"))
		if 174 not in Devices:
			Domoticz.Device(Name= tl.t("Zone 8 heating + at solar limit"), Unit=174, Type=242, Subtype=1, Options={"ValueMin": "-10", "ValueMax": "10", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(174, 0, "2"))
		if 175 not in Devices:
			Domoticz.Device(Name= tl.t("Zone 8 cooling - at solar limit"), Unit=175, Type=242, Subtype=1, Options={"ValueMin": "-10", "ValueMax": "10", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(175, 0, "-2"))
		if 176 not in Devices:
			Domoticz.Device(Name= tl.t("Zone 8 heating + at external temperature dependent"), Unit=176, Type=242, Subtype=1, Options={"ValueMin": "-10", "ValueMax": "10", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(176, 0, "1"))
		if 177 not in Devices:
			Domoticz.Device(Name= tl.t("Zone 8 cooling - at external temperature dependent"), Unit=177, Type=242, Subtype=1, Options={"ValueMin": "-10", "ValueMax": "10", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(177, 0, "-1"))
		# Zone 9 | 9. zóna
		if 178 not in Devices:
			Domoticz.Device(Name=tl.t("Zone 9 normal heating temperature"), Unit=178, Type=242, Subtype=1, Options={"ValueMin": "5", "ValueMax": "35", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(178, 0, "22"))
		if 179 not in Devices:
			Domoticz.Device(Name= tl.t("Zone 9 economical heating temperature"), Unit=179, Type=242, Subtype=1, Options={"ValueMin": "5", "ValueMax": "35", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(179 ,0, "20"))
		if 180 not in Devices:
			Domoticz.Device(Name= tl.t("Zone 9 normal cooling temperature"), Unit=180, Type=242, Subtype=1, Options={"ValueMin": "5", "ValueMax": "35", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(180, 0, "24"))
		if 181 not in Devices:
			Domoticz.Device(Name= tl.t("Zone 9 economical cooling temperature"), Unit=181, Type=242, Subtype=1, Options={"ValueMin": "5", "ValueMax": "35", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(181, 0, "26"))
		if 182 not in Devices:
			Domoticz.Device(Name= tl.t("Zone 9 heating + at solar limit"), Unit=182, Type=242, Subtype=1, Options={"ValueMin": "-10", "ValueMax": "10", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(182, 0, "2"))
		if 183 not in Devices:
			Domoticz.Device(Name= tl.t("Zone 9 cooling - at solar limit"), Unit=183, Type=242, Subtype=1, Options={"ValueMin": "-10", "ValueMax": "10", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(183, 0, "-2"))
		if 184 not in Devices:
			Domoticz.Device(Name= tl.t("Zone 9 heating + at external temperature dependent"), Unit=184, Type=242, Subtype=1, Options={"ValueMin": "-10", "ValueMax": "10", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(184, 0, "1"))
		if 185 not in Devices:
			Domoticz.Device(Name= tl.t("Zone 9 cooling - at external temperature dependent"), Unit=185, Type=242, Subtype=1, Options={"ValueMin": "-10", "ValueMax": "10", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(185, 0, "-1"))
		# Zone 10 | 10. zóna
		if 186 not in Devices:
			Domoticz.Device(Name=tl.t("Zone 10 normal heating temperature"), Unit=186, Type=242, Subtype=1, Options={"ValueMin": "5", "ValueMax": "35", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(186, 0, "22"))
		if 187 not in Devices:
			Domoticz.Device(Name= tl.t("Zone 10 economical heating temperature"), Unit=187, Type=242, Subtype=1, Options={"ValueMin": "5", "ValueMax": "35", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(187,0, "20"))
		if 188 not in Devices:
			Domoticz.Device(Name= tl.t("Zone 10 normal cooling temperature"), Unit=188, Type=242, Subtype=1, Options={"ValueMin": "5", "ValueMax": "35", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(188, 0, "24"))
		if 189 not in Devices:
			Domoticz.Device(Name= tl.t("Zone 10 economical cooling temperature"), Unit=189, Type=242, Subtype=1, Options={"ValueMin": "5", "ValueMax": "35", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(189, 0, "26"))
		if 190 not in Devices:
			Domoticz.Device(Name= tl.t("Zone 10 heating + at solar limit"), Unit=190, Type=242, Subtype=1, Options={"ValueMin": "-10", "ValueMax": "10", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(190, 0, "2"))
		if 191 not in Devices:
			Domoticz.Device(Name= tl.t("Zone 10 cooling - at solar limit"), Unit=191, Type=242, Subtype=1, Options={"ValueMin": "-10", "ValueMax": "10", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(191, 0, "-2"))
		if 192 not in Devices:
			Domoticz.Device(Name= tl.t("Zone 10 heating + at external temperature dependent"), Unit=192, Type=242, Subtype=1, Options={"ValueMin": "-10", "ValueMax": "10", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(192, 0, "1"))
		if 193 not in Devices:
			Domoticz.Device(Name= tl.t("Zone 10 cooling - at external temperature dependent"), Unit=193, Type=242, Subtype=1, Options={"ValueMin": "-10", "ValueMax": "10", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(193, 0, "-1"))
		# Zone 11 | 11. zóna
		if 194 not in Devices:
			Domoticz.Device(Name=tl.t("Zone 11 normal heating temperature"), Unit=194, Type=242, Subtype=1, Options={"ValueMin": "5", "ValueMax": "35", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(194, 0, "22"))
		if 195 not in Devices:
			Domoticz.Device(Name= tl.t("Zone 11 economical heating temperature"), Unit=195, Type=242, Subtype=1, Options={"ValueMin": "5", "ValueMax": "35", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(195,0, "20"))
		if 196 not in Devices:
			Domoticz.Device(Name= tl.t("Zone 11 normal cooling temperature"), Unit=196, Type=242, Subtype=1, Options={"ValueMin": "5", "ValueMax": "35", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(196, 0, "24"))
		if 197 not in Devices:
			Domoticz.Device(Name= tl.t("Zone 11 economical cooling temperature"), Unit=197, Type=242, Subtype=1, Options={"ValueMin": "5", "ValueMax": "35", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(197, 0, "26"))
		if 198 not in Devices:
			Domoticz.Device(Name= tl.t("Zone 11 heating + at solar limit"), Unit=198, Type=242, Subtype=1, Options={"ValueMin": "-10", "ValueMax": "10", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(198, 0, "2"))
		if 199 not in Devices:
			Domoticz.Device(Name= tl.t("Zone 11 cooling - at solar limit"), Unit=199, Type=242, Subtype=1, Options={"ValueMin": "-10", "ValueMax": "10", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(199, 0, "-2"))
		if 200 not in Devices:
			Domoticz.Device(Name= tl.t("Zone 11 heating + at external temperature dependent"), Unit=200, Type=242, Subtype=1, Options={"ValueMin": "-10", "ValueMax": "10", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(200, 0, "1"))
		if 201 not in Devices:
			Domoticz.Device(Name= tl.t("Zone 11 cooling - at external temperature dependent"), Unit=201, Type=242, Subtype=1, Options={"ValueMin": "-10", "ValueMax": "10", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(201, 0, "-1"))
		# Zone 12 | 12. zóna
		if 202 not in Devices:
			Domoticz.Device(Name=tl.t("Zone 12 normal heating temperature"), Unit=202, Type=242, Subtype=1, Options={"ValueMin": "5", "ValueMax": "35", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(202, 0, "22"))
		if 203 not in Devices:
			Domoticz.Device(Name= tl.t("Zone 12 economical heating temperature"), Unit=203, Type=242, Subtype=1, Options={"ValueMin": "5", "ValueMax": "35", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(203,0, "20"))
		if 204 not in Devices:
			Domoticz.Device(Name= tl.t("Zone 12 normal cooling temperature"), Unit=204, Type=242, Subtype=1, Options={"ValueMin": "5", "ValueMax": "35", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(204, 0, "24"))
		if 205 not in Devices:
			Domoticz.Device(Name= tl.t("Zone 12 economical cooling temperature"), Unit=205, Type=242, Subtype=1, Options={"ValueMin": "5", "ValueMax": "35", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(205, 0, "26"))
		if 206 not in Devices:
			Domoticz.Device(Name= tl.t("Zone 12 heating + at solar limit"), Unit=206, Type=242, Subtype=1, Options={"ValueMin": "-10", "ValueMax": "10", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(206, 0, "2"))
		if 207 not in Devices:
			Domoticz.Device(Name= tl.t("Zone 12 cooling - at solar limit"), Unit=207, Type=242, Subtype=1, Options={"ValueMin": "-10", "ValueMax": "10", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(207, 0, "-2"))
		if 208 not in Devices:
			Domoticz.Device(Name= tl.t("Zone 12 heating + at external temperature dependent"), Unit=208, Type=242, Subtype=1, Options={"ValueMin": "-10", "ValueMax": "10", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(208, 0, "1"))
		if 209 not in Devices:
			Domoticz.Device(Name= tl.t("Zone 12 cooling - at external temperature dependent"), Unit=209, Type=242, Subtype=1, Options={"ValueMin": "-10", "ValueMax": "10", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(209, 0, "-1"))

		if 65 not in Devices:
			Options = {"LevelActions": "||",
					   "LevelNames": tl.t("Off|Heating-Cooling|Heating-Cooling - 1/2 hour|Heating-Cooling - 1 hour|Heating-Cooling - 2 hours|Heating-Cooling - 3 hours|Buffer|Buffer - 1/2 hour|Buffer - 1 hour|Buffer - 2 hours|Buffer - 3 hours|Heating-Cooling + Buffer|Heating-Cooling + Buffer - 1/2 hour|Heating-Cooling + Buffer - 1 hour|Heating-Cooling + Buffer - 2 hours|Heating-Cooling + Buffer - 3 hours"),
					   "LevelOffHidden": "false",
					   "SelectorStyle": "1"}
			Domoticz.Device(Name= tl.t("DHW priority"), Unit=65, TypeName="Selector Switch", Switchtype=18, Image=15, Options=Options, Used=1).Create()
			devicecreated.append(deviceparam(65, 0, "0"))
		if 66 not in Devices:
			Options = {"LevelActions": "||",
					   "LevelNames": tl.t("Off|Room compensation"),
					   "LevelOffHidden": "false",
					   "SelectorStyle": "0"}
			Domoticz.Device(Name= tl.t("Room leveling"), Unit=66, TypeName="Selector Switch", Switchtype=18, Image=15, Options=Options, Used=1).Create()
			devicecreated.append(deviceparam(66, 0, "0"))
		if 68 not in Devices:
			Domoticz.Device(Name= tl.t("Compensation"), Unit=68, Type=244, Subtype=73, Switchtype=0, Used=0).Create()
			devicecreated.append(deviceparam(68, 0, "Off"))
		
		
		# Mixing valves | Keverőszelepek
		if 61 not in Devices:
			Domoticz.Device(Name= tl.t("1. mixing valve hysteresis"), Unit=61, Type=242, Subtype=1, Options={"ValueMin": "0", "ValueMax": "5", "ValueStep": "0.1", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(61 ,0, "1"))
		if 62 not in Devices:
			Domoticz.Device(Name=tl.t("2. mixing valve hysteresis"), Unit=62, Type=242, Subtype=1, Options={"ValueMin": "0", "ValueMax": "5", "ValueStep": "0.1", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(62 ,0, "1"))
		if 59 not in Devices:
			Domoticz.Device(Name= tl.t("1. mixing heating valve max. temperature"), Unit=59, Type=242, Subtype=1, Options={"ValueMin": "5", "ValueMax": "90", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(59 ,0, "40"))
		if 60 not in Devices:
			Domoticz.Device(Name= tl.t("2. mixing heating valve max. temperature"), Unit=60, Type=242, Subtype=1, Options={"ValueMin": "5", "ValueMax": "90", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(60 ,0, "40"))
		if 70 not in Devices:
			Domoticz.Device(Name= tl.t("1. mixing heating valve min. temperature"), Unit=70, Type=242, Subtype=1, Options={"ValueMin": "5", "ValueMax": "90", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(70 ,0, "40"))
		if 71 not in Devices:
			Domoticz.Device(Name= tl.t("2. mixing heating valve min. temperature"), Unit=71, Type=242, Subtype=1, Options={"ValueMin": "5", "ValueMax": "90", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(71 ,0, "40"))
		if 119 not in Devices:
			Domoticz.Device(Name= tl.t("1. mixing cooling valve max. temperature"), Unit=119, Type=242, Subtype=1, Options={"ValueMin": "5", "ValueMax": "90", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(119 ,0, "15"))
		if 120 not in Devices:
			Domoticz.Device(Name= tl.t("2. mixing cooling valve max. temperature"), Unit=120, Type=242, Subtype=1, Options={"ValueMin": "5", "ValueMax": "90", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(120 ,0, "15"))
		if 121 not in Devices:
			Domoticz.Device(Name= tl.t("1. mixing cooling valve min. temperature"), Unit=121, Type=242, Subtype=1, Options={"ValueMin": "5", "ValueMax": "90", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(121 ,0, "15"))
		if 122 not in Devices:
			Domoticz.Device(Name= tl.t("2. mixing cooling valve min. temperature"), Unit=122, Type=242, Subtype=1, Options={"ValueMin": "5", "ValueMax": "90", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(122 ,0, "15"))
		if 72 not in Devices:
			Domoticz.Device(Name= tl.t("1. mixing valve current target temperature"), Unit=72, TypeName="Temperature", Used=1).Create()
			devicecreated.append(deviceparam(72, 0, "20"))
		if 73 not in Devices:
			Domoticz.Device(Name= tl.t("2. mixing valve current target temperature"), Unit=73, TypeName="Temperature", Used=1).Create()
			devicecreated.append(deviceparam(73, 0, "20"))
		if 74 not in Devices:
			Options = {"LevelActions": "||",
					   "LevelNames": tl.t("Off|1 hour|2 hour|3 hour|4 hour|5 hour|6 hour"),
					   "SelectorStyle": "0"}
			Domoticz.Device(Name= tl.t("Future external temperature"), Unit=74, TypeName="Selector Switch", Switchtype=18, Image=15, Options=Options, Used=0).Create()
			devicecreated.append(deviceparam(74, 0, "0"))
		if 63 not in Devices:
			Domoticz.Device(Name= tl.t("Mixing 1 valves dew point correction"), Unit=63, Type=242, Subtype=1, Options={"ValueMin": "-10", "ValueMax": "10", "ValueStep": "0.1", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(63 ,0, "2"))
		if 75 not in Devices:
			Domoticz.Device(Name= tl.t("Mixing 2 valves dew point correction"), Unit=75, Type=242, Subtype=1, Options={"ValueMin": "-10", "ValueMax": "10", "ValueStep": "0.1", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(75 ,0, "2"))
		
		
		# Domestic hot water (DHW) | HMV
		if 78 not in Devices:
			Options = {"LevelActions": "||",
					   "LevelNames": tl.t("Off|500|1000|2000|3000|4000|5000"),
					   "SelectorStyle": "0"}
			Domoticz.Device(Name= tl.t("Solar production DHW (Watt)"), Unit=78, TypeName="Selector Switch", Switchtype=18, Image=15, Options=Options, Used=0).Create()
			devicecreated.append(deviceparam(78, 0, "0"))
		
		if 83 not in Devices:
			Options = {"LevelActions": "||",
					   "LevelNames": tl.t("Off|-5°C|0°C|7°C|15°C|20°C|aut 6 hour|aut 8 hour|aut 12 hour"),
					   "SelectorStyle": "1"}
			Domoticz.Device(Name= tl.t("DHW target external switching limit"), Unit=83, TypeName="Selector Switch", Switchtype=18, Image=15, Options=Options, Used=0).Create()
			devicecreated.append(deviceparam(83, 0, "0"))
		if 90 not in Devices:
			Domoticz.Device(Name= tl.t("Buffer heating temperature"), Unit=90, Type=242, Subtype=1, Options={"ValueMin": "5", "ValueMax": "85", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(90, 0, "40"))
		if 91 not in Devices:
			Domoticz.Device(Name= tl.t("Buffer cooling temperature"), Unit=91, Type=242, Subtype=1, Options={"ValueMin": "5", "ValueMax": "85", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(91, 0, "15"))
		if 92 not in Devices:
			Domoticz.Device(Name= tl.t("Buffer heating hysteresis"), Unit=92, Type=242, Subtype=1, Options={"ValueMin": "0", "ValueMax": "5", "ValueStep": "0.1", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(92, 0, "3"))
		if 123 not in Devices:
			Domoticz.Device(Name= tl.t("Buffer cooling hysteresis"), Unit=123, Type=242, Subtype=1, Options={"ValueMin": "0", "ValueMax": "5", "ValueStep": "0.1", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(123, 0, "3"))
		if 82 not in Devices:
			Domoticz.Device(Name= tl.t("Buffer target heating external temperature dependent"), Unit=82, Type=242, Subtype=1, Options={"ValueMin": "5", "ValueMax": "85", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(82, 0, "45"))
		if 77 not in Devices:
			Domoticz.Device(Name= tl.t("Buffer external hysteresis"), Unit=77, Type=242, Subtype=1, Options={"ValueMin": "0", "ValueMax": "5", "ValueStep": "0.1", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(77, 0, "0.5"))
		if 95 not in Devices:
			Domoticz.Device(Name= tl.t("Buffer heating 2nd device switching limit"), Unit=95, Type=242, Subtype=1, Options={"ValueMin": "-40", "ValueMax": "50", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(95, 0, "7"))
		if 226 not in Devices:
			Domoticz.Device(Name= tl.t("Buffer cooling 2nd device switching limit"), Unit=226, Type=242, Subtype=1, Options={"ValueMin": "-40", "ValueMax": "50", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(226, 0, "27"))
		if 94 not in Devices:
			Domoticz.Device(Name= tl.t("Solar heating buffer temperature"), Unit=94, Type=242, Subtype=1, Options={"ValueMin": "5", "ValueMax": "85", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(94, 0, "45"))
		if 93 not in Devices:
			Domoticz.Device(Name= tl.t("Solar cooling buffer temperature"), Unit=93, Type=242, Subtype=1, Options={"ValueMin": "5", "ValueMax": "85", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(93, 0, "7"))
		if 96 not in Devices:
			Domoticz.Device(Name= tl.t("Solar buffer hysteresis"), Unit=96, Type=242, Subtype=1, Options={"ValueMin": "0", "ValueMax": "5", "ValueStep": "0.1", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(96, 0, "1"))
		if 104 not in Devices:
			Options = {"LevelActions": "||",
					   "LevelNames": tl.t("Off|Device 1|Device 2|Switch mode based on buffer tank temperature|Switch mode based on outdoor temperature|Switch mode based on outdoor dew point|Dual mode based on buffer tank temperature|Dual mode based on outdoor temperature|Dual mode based on outdoor dew point|Saver mode based on buffer tank temperature and outdoor temperature|Saver mode based on buffer tank temperature and outdoor dew point|Switch mode min. 500 W for return|Switch mode min. 1000 W for return|Switch mode min. 1500 W for return|Switch mode min. 2000 W for return|Switch mode min. 3000 W for return|Switch mode min. 4000 W for return|Switch mode min. 5000 W for return|Dual mode min. 500 W for return|Dual mode min. 1000 W for return|Dual mode min. 1500 W for return|Dual mode min. 2000 W for return|Dual mode min. 3000 W for return|Dual mode min. 4000 W for return|Dual mode min. 5000 W for return"),
					   "LevelOffHidden": "false",
					   "SelectorStyle": "1"}
			Domoticz.Device(Name= tl.t("Buffer heating"), Unit=104, TypeName="Selector Switch", Switchtype=18, Image=15, Options=Options, Used=1).Create()
			devicecreated.append(deviceparam(104, 0, "0"))
			self.addfavorite(Devices[104].ID)
		if 224 not in Devices:
			Options = {"LevelActions": "||",
				"LevelNames": tl.t("Off|Device 1|Device 2|Switch mode based on buffer temperature|Switch mode based on outdoor temperature|Dual mode based on buffer temperature|Dual mode based on outdoor temperature|Switch mode min. 500 W for return|Switch mode min. 1000 W for return|Switch mode min. 1500 W for return|Switch mode min. 2000 W for return|Switch mode min. 3000 W for return|Switch mode min. 4000 W for return|Switch mode min. 5000 W for return|Dual mode min. 500 W for return|Dual mode min. 1000 W for return|Dual mode min. 1500 W for return|Dual mode min. 2000 W for return|Dual mode min. 3000 W for return|Dual mode min. 4000 W for return|Dual mode min. 5000 W for return"),
				"LevelOffHidden": "false",
				"SelectorStyle": "1"}
			Domoticz.Device(Name= tl.t("Buffer cooling"), Unit=224, TypeName="Selector Switch", Switchtype=18, Image=15, Options=Options, Used=1).Create()
			devicecreated.append(deviceparam(224, 0, "0"))
			self.addfavorite(Devices[224].ID)
		if 98 not in Devices:
			Options = {"LevelActions": "||",
					   "LevelNames": tl.t("Off|500|1000|2000|3000|4000|5000"),
					   "SelectorStyle": "0"}
			Domoticz.Device(Name= tl.t("Solar buffer (Watt)"), Unit=98, TypeName="Selector Switch", Switchtype=18, Image=15, Options=Options, Used=0).Create()
			devicecreated.append(deviceparam(98, 0, "0"))
		if 100 not in Devices:
			Domoticz.Device(Name= tl.t("Buffer current target temperature"), Unit=100, TypeName="Temperature", Used=0).Create()
			devicecreated.append(deviceparam(100, 0, "40"))
		if 102 not in Devices:
			Domoticz.Device(Name="1 P", Unit=102, Type=244, Subtype=73, Switchtype=0, Used=0).Create()
			devicecreated.append(deviceparam(102, 0, "Off"))
		if 103 not in Devices:
			Domoticz.Device(Name="2 P", Unit=103, Type=244, Subtype=73, Switchtype=0, Used=0).Create()
			devicecreated.append(deviceparam(103, 0, "Off"))
		if 114 not in Devices:
			Options = {"LevelActions": "||",
					   "LevelNames": tl.t("Off|x1|x2|x3|x4|x5|x6|x7|x8|x9|x10"),
					   "LevelOffHidden": "true",
					   "SelectorStyle": "0"}
			Domoticz.Device(Name= tl.t("Buffer secondary differential elements"), Unit=114, TypeName="Selector Switch", Switchtype=18, Image=15, Options=Options, Used=0).Create()
			devicecreated.append(deviceparam(114, 0, "30"))
		if 105 not in Devices:
			Domoticz.Device(Name= tl.t("Calculated current buffer temperature"), Unit=105, TypeName="Temperature", Used=0).Create()
			devicecreated.append(deviceparam(105, 0, "20"))
		if 106 not in Devices:
			Domoticz.Device(Name="1 PE", Unit=106, Type=244, Subtype=73, Switchtype=0, Used=0).Create()
			devicecreated.append(deviceparam(106, 0, "Off"))
		if 107 not in Devices:
			Domoticz.Device(Name="2 PE", Unit=107, Type=244, Subtype=73, Switchtype=0, Used=0).Create()
			devicecreated.append(deviceparam(107, 0, "Off"))
		if 108 not in Devices:
			Domoticz.Device(Name= tl.t("Buffer 2. device switching temperature"), Unit=108, Type=242, Subtype=1, Options={"ValueMin": "-40", "ValueMax": "50", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(108 ,0, "-5"))
		if 109 not in Devices:
			Domoticz.Device(Name= tl.t("Buffer dual temperature diff"), Unit=109, Type=242, Subtype=1, Options={"ValueMin": "0", "ValueMax": "15", "ValueStep": "0.1", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(109, 0, "2"))
		if 110 not in Devices:
			Domoticz.Device(Name= tl.t("Buffer device 1 external E cartridge switching limit"), Unit=110, Type=242, Subtype=1, Options={"ValueMin": "-40", "ValueMax": "50", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(110, 0, "15"))
		if 111 not in Devices:
			Domoticz.Device(Name= tl.t("Buffer device 2 external E cartridge switching limit"), Unit=111, Type=242, Subtype=1, Options={"ValueMin": "-40", "ValueMax": "50", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(111, 0, "15"))
		if 117 not in Devices:
			Domoticz.Device(Name= tl.t("Buffer device 1 tank E cartridge switching limit"), Unit=117, Type=242, Subtype=1, Options={"ValueMin": "-40", "ValueMax": "50", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(117, 0, "45"))
		if 118 not in Devices:
			Domoticz.Device(Name= tl.t("Buffer device 2 tank E cartridge switching limit"), Unit=118, Type=242, Subtype=1, Options={"ValueMin": "-40", "ValueMax": "50", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(118, 0, "45"))
		if 84 not in Devices:
			Options = {"LevelActions": "||",
					   "LevelNames": tl.t("Off|-5°C|0°C|7°C|15°C|20°C|aut 6 hour|aut 8 hour|aut 12 hour"),
					   "SelectorStyle": "0"}
			Domoticz.Device(Name= tl.t("Buffer target heating external temperature dependent"), Unit=84, TypeName="Selector Switch", Switchtype=18, Image=15, Options=Options, Used=0).Create()
			devicecreated.append(deviceparam(84, 0, "0"))
		if 99 not in Devices:
			Options = {"LevelActions": "||",
					   "LevelNames": tl.t("Off|-5°C|0°C|7°C|15°C|20°C|aut 6 hour|aut 8 hour|aut 12 hour"),
					   "SelectorStyle": "1"}
			Domoticz.Device(Name= tl.t("Buffer target cooling external temperature dependent"), Unit=99, TypeName="Selector Switch", Switchtype=18, Image=15, Options=Options, Used=0).Create()
			devicecreated.append(deviceparam(99, 0, "0"))
		if 131 not in Devices:
			Domoticz.Device(Name= tl.t("Calculated outside closest temp"), Unit=131, TypeName="Temperature", Used=1).Create()
			devicecreated.append(deviceparam(131, 0, "0"))
		if 69 not in Devices:
			Domoticz.Device(Name= tl.t("Calculated outside temperature"), Unit=69, TypeName="Temperature", Used=1).Create()
			devicecreated.append(deviceparam(69, 0, "20"))
		if 152 not in Devices:
			Domoticz.Device(Name= tl.t("1. mixing valve current temperature"), Unit=152, TypeName="Temperature", Used=0).Create()
			devicecreated.append(deviceparam(152, 0, "0"))
		if 153 not in Devices:
			Domoticz.Device(Name= tl.t("2. mixing valve current temperature"), Unit=153, TypeName="Temperature", Used=0).Create()
			devicecreated.append(deviceparam(153, 0, "0"))
		if 154 not in Devices:
			Domoticz.Device(Name= tl.t("hiszterezis"), Unit=154, TypeName="Temperature", Used=0).Create()
			devicecreated.append(deviceparam(154, 0, "0"))
		if 158 not in Devices:
			Domoticz.Device(Name= tl.t("Target value upper limit"), Unit=158, TypeName="Temperature", Used=1).Create()
			devicecreated.append(deviceparam(158, 0, "0"))
		if 159 not in Devices:
			Domoticz.Device(Name= tl.t("Target value lower limit"), Unit=159, TypeName="Temperature", Used=1).Create()
			devicecreated.append(deviceparam(159, 0, "0"))
		if 210 not in Devices:
			Options = {"LevelActions": "||",
					   "LevelNames": tl.t("Off|On"),
					   "LevelOffHidden": "false",
					   "SelectorStyle": "0"}
			Domoticz.Device(Name= tl.t("Current target temperature to home page"), Unit=210, TypeName="Selector Switch", Switchtype=18, Image=15, Options=Options, Used=1).Create()
			devicecreated.append(deviceparam(210, 0, "10"))
			self.addfavorite(Devices[210].ID)
		if 211 not in Devices:
			Options = {"LevelActions": "||",
					   "LevelNames": tl.t("Off|TRV Static Setpoint heating|TRV Dynamic Setpoint heating|TRV Dynamic Setpoint heating and cooling"),
					   "LevelOffHidden": "true",
					   "SelectorStyle": "1"}
			Domoticz.Device(Name= tl.t("TRV SetPoint"), Unit=211, TypeName="Selector Switch", Switchtype=18, Image=15, Options=Options, Used=1).Create()
			devicecreated.append(deviceparam(211, 0, "10"))
		if 212 not in Devices:
			Options = {"LevelActions": "||",
					   "LevelNames": tl.t("Off|1x|2x|3x|4x|5x|10x"),
					   "LevelOffHidden": "false",
					   "SelectorStyle": "0"}
			Domoticz.Device(Name= tl.t("IR command resend"), Unit=212, TypeName="Selector Switch", Switchtype=18, Image=15, Options=Options, Used=1).Create()
			devicecreated.append(deviceparam(212, 0, "0"))
		if 217 not in Devices:
			Options = {"LevelActions": "||",
					   "LevelNames": tl.t("Off|Only normal setpoint|Aktual setpoint"),
					   "LevelOffHidden": "false",
					   "SelectorStyle": "0"}
			Domoticz.Device(Name= tl.t("Update target value based on console"), Unit=217, TypeName="Selector Switch", Switchtype=18, Image=15, Options=Options, Used=1).Create()
			devicecreated.append(deviceparam(217, 0, "0"))

		if 86 not in Devices:
			Domoticz.Device(Name=tl.t("Virtual hydraulic shifter"), Unit=86, Type=243, Subtype=22, Used=1).Create()
			devicecreated.append(deviceparam(86, 0, tl.t("Not active")))

		if 228 not in Devices:
			Domoticz.Device(Name=tl.t("Heating target, outdoor temperature dependent, indication"), Unit=228, Type=243, Subtype=22, Used=1).Create()
			devicecreated.append(deviceparam(228, 0, tl.t("Not active")))

		if 229 not in Devices:
			Domoticz.Device(Name=tl.t("Cooling target, outdoor temperature dependent, indication"), Unit=229, Type=243, Subtype=22, Used=1).Create()
			devicecreated.append(deviceparam(229, 0, tl.t("Not active")))
		
		if 230 not in Devices:
			Domoticz.Device(Name=tl.t("Solar energy limit, Heating - Cooling (Watt), indication"), Unit=230, Type=243, Subtype=22, Used=1).Create()
			devicecreated.append(deviceparam(230, 0, tl.t("Not active")))
		
		if 231 not in Devices:
			Domoticz.Device(Name=tl.t("Future time at automatic target temperature, indication"), Unit=231, Type=243, Subtype=22, Used=1).Create()
			devicecreated.append(deviceparam(231, 0, tl.t("Not active")))

		if 233 not in Devices:
			Domoticz.Device(Name=tl.t("Solar panel production DHW (Watt), indication"), Unit=233, Type=243, Subtype=22, Used=1).Create()
			devicecreated.append(deviceparam(233, 0, tl.t("Not active")))

		if 234 not in Devices:
			Domoticz.Device(Name=tl.t("DHW target external switching limit, indication"), Unit=234, Type=243, Subtype=22, Used=1).Create()
			devicecreated.append(deviceparam(234, 0, tl.t("Not active")))

		if 235 not in Devices:
			Domoticz.Device(Name=tl.t("Buffer solar panel min. limit (Watt), indication"), Unit=235, Type=243, Subtype=22, Used=1).Create()
			devicecreated.append(deviceparam(235, 0, tl.t("Not active")))

		if 236 not in Devices:
			Domoticz.Device(Name=tl.t("Buffer heating target dependent on outside temperature, indication"), Unit=236, Type=243, Subtype=22, Used=1).Create()
			devicecreated.append(deviceparam(236, 0, tl.t("Not active")))

		if 237 not in Devices:
			Domoticz.Device(Name=tl.t("Buffer cooling target dependent on external temperature, indication"), Unit=237, Type=243, Subtype=22, Used=1).Create()
			devicecreated.append(deviceparam(237, 0, tl.t("Not active")))

		if 238 not in Devices:
			Domoticz.Device(Name=tl.t("Heating-cooling presence detection mode, indication"), Unit=238, Type=243, Subtype=22, Used=1).Create()
			devicecreated.append(deviceparam(238, 0, tl.t("Not active")))

		if 239 not in Devices:
			Domoticz.Device(Name=tl.t("DHW presence detection mode, indication"), Unit=239, Type=243, Subtype=22, Used=1).Create()
			devicecreated.append(deviceparam(239, 0, tl.t("Not active")))

		if 240 not in Devices:
			Domoticz.Device(Name=tl.t("Zone_1 doors and windows"), Unit=240, Type=243, Subtype=22, Used=1).Create()
			devicecreated.append(deviceparam(240, 1, tl.t("Closed")))

		if 241 not in Devices:
			Domoticz.Device(Name=tl.t("Zone_2 doors and windows"), Unit=241, Type=243, Subtype=22, Used=1).Create()
			devicecreated.append(deviceparam(241, 1, tl.t("Closed")))

		if 242 not in Devices:
			Domoticz.Device(Name=tl.t("Zone_3 doors and windows"), Unit=242, Type=243, Subtype=22, Used=1).Create()
			devicecreated.append(deviceparam(242, 1, tl.t("Closed")))

		if 243 not in Devices:
			Domoticz.Device(Name=tl.t("Zone_4 doors and windows"), Unit=243, Type=243, Subtype=22, Used=1).Create()
			devicecreated.append(deviceparam(243, 1, tl.t("Closed")))

		if 244 not in Devices:
			Domoticz.Device(Name=tl.t("Zone_5 doors and windows"), Unit=244, Type=243, Subtype=22, Used=1).Create()
			devicecreated.append(deviceparam(244, 1, tl.t("Closed")))

		if 245 not in Devices:
			Domoticz.Device(Name=tl.t("Zone_6 doors and windows"), Unit=245, Type=243, Subtype=22, Used=1).Create()
			devicecreated.append(deviceparam(245, 1, tl.t("Closed")))

		if 246 not in Devices:
			Domoticz.Device(Name=tl.t("Zone_7 doors and windows"), Unit=246, Type=243, Subtype=22, Used=1).Create()
			devicecreated.append(deviceparam(246, 1, tl.t("Closed")))

		if 247 not in Devices:
			Domoticz.Device(Name=tl.t("Zone_8 doors and windows"), Unit=247, Type=243, Subtype=22, Used=1).Create()
			devicecreated.append(deviceparam(247, 1, tl.t("Closed")))

		if 248 not in Devices:
			Domoticz.Device(Name=tl.t("Zone_9 doors and windows"), Unit=248, Type=243, Subtype=22, Used=1).Create()
			devicecreated.append(deviceparam(248, 1, tl.t("Closed")))

		if 249 not in Devices:
			Domoticz.Device(Name=tl.t("Zone_10 doors and windows"), Unit=249, Type=243, Subtype=22, Used=1).Create()
			devicecreated.append(deviceparam(249, 1, tl.t("Closed")))

		if 250 not in Devices:
			Domoticz.Device(Name=tl.t("Zone_11 doors and windows"), Unit=250, Type=243, Subtype=22, Used=1).Create()
			devicecreated.append(deviceparam(250, 1, tl.t("Closed")))

		if 251 not in Devices:
			Domoticz.Device(Name=tl.t("Zone_12 doors and windows"), Unit=251, Type=243, Subtype=22, Used=1).Create()
			devicecreated.append(deviceparam(251, 1, tl.t("Closed")))

		if 218 not in Devices:
			Options = {"LevelActions": "||",
					   "LevelNames": tl.t("Off|1|2|3|4|5|10|15|30|60|120|240|480|720|1440|2880"),
					   "LevelOffHidden": "true",
					   "SelectorStyle": "1"}
			Domoticz.Device(Name= tl.t("Device 1: On delay (minutes)"), Unit=218, TypeName="Selector Switch", Switchtype=18, Image=21, Options=Options, Used=1).Create()
			devicecreated.append(deviceparam(218, 0, "50"))

		if 219 not in Devices:
			Options = {"LevelActions": "||",
					   "LevelNames": tl.t("Off|1|2|3|4|5|10|15|30|60|120|240|480|720|1440|2880"),
					   "LevelOffHidden": "true",
					   "SelectorStyle": "1"}
			Domoticz.Device(Name= tl.t("Device 1: Off delay (minutes)"), Unit=219, TypeName="Selector Switch", Switchtype=18, Image=21, Options=Options, Used=1).Create()
			devicecreated.append(deviceparam(219, 0, "50"))

		if 220 not in Devices:
			Options = {"LevelActions": "||",
					   "LevelNames": tl.t("Off|1|2|3|4|5|10|15|30|60|120|240|480|720|1440|2880"),
					   "LevelOffHidden": "true",
					   "SelectorStyle": "1"}
			Domoticz.Device(Name= tl.t("Device 2: On delay (minutes)"), Unit=220, TypeName="Selector Switch", Switchtype=18, Image=21, Options=Options, Used=1).Create()
			devicecreated.append(deviceparam(220, 0, "50"))

		if 232 not in Devices:
			Options = {"LevelActions": "||",
					   "LevelNames": tl.t("Off|1|2|3|4|5|10|15|30|60|120|240|480|720|1440|2880"),
					   "LevelOffHidden": "true",
					   "SelectorStyle": "1"}
			Domoticz.Device(Name= tl.t("Device 2: Off delay (minutes)"), Unit=232, TypeName="Selector Switch", Switchtype=18, Image=21, Options=Options, Used=1).Create()
			devicecreated.append(deviceparam(232, 0, "50"))

		if 97 not in Devices:
			Domoticz.Device(Name= tl.t("Outdewpoint"), Unit=97, TypeName="Temperature", Used=0).Create()
			devicecreated.append(deviceparam(97, 0, "0"))

		if 157 not in Devices:
			Domoticz.Device(Name= tl.t("Indewpoint"), Unit=157, TypeName="Temperature", Used=0).Create()
			devicecreated.append(deviceparam(157, 0, "0"))

		if 85 not in Devices:
			Domoticz.Device(Name= tl.t("Watt limit hysteresis"), Unit=85,  Type=243, Subtype=6, Used=1).Create()
			devicecreated.append(deviceparam(85, 0, "5"))

		# Plugin readiness status | Plugin készenléti állapota
		if 87 not in Devices:
			Domoticz.Device(Name="DSVT Plugin Status", Unit=87, Type=243, Subtype=22, Used=0).Create()
			devicecreated.append(deviceparam(87, 0, "STARTING"))

		if 89 not in Devices:
			Domoticz.Device(Name=tl.t("Frost protection temperature limit"), Unit=89, Type=242, Subtype=1, Options={"ValueMin": "-10", "ValueMax": "15", "ValueStep": "0.5", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(89, 0, "5"))

		if 156 not in Devices:
			Domoticz.Device(Name=tl.t("Frost protection hysteresis"), Unit=156, Type=242, Subtype=1, Options={"ValueMin": "0", "ValueMax": "5", "ValueStep": "0.1", "ValueUnit": "°C"}, Used=1).Create()
			devicecreated.append(deviceparam(156, 0, "1"))

		# Available IDs: 158, 159; maximum: 252 | Szabad azonosítók: 158, 159; maximum: 252

		# If any devices were created in onStart(), update their default settings here | Ha az onStart() eszközt hozott létre, itt frissítjük az alapértelmezett beállításait
		for device in devicecreated:
			Devices[device.unit].Update(nValue=device.nvalue, sValue=device.svalue)

		# Mark plugin as starting | Plugin indulásának jelzése
		Devices[87].Update(nValue=0, sValue="STARTING")

		# Create a list of sensors and switches | Lista készítése az érzékelőkről és kapcsolókról

		self.Zone_TempSensors_1 = parse_Z_1(Parameters["Mode1"])

		self.Zone_TempSensors_2 = parse_Z_2(Parameters["Mode1"])

		self.Zone_TempSensors_3 = parse_Z_3(Parameters["Mode1"])

		self.Zone_TempSensors_4 = parse_Z_4(Parameters["Mode1"])

		self.Zone_TempSensors_5 = parse_Z_5(Parameters["Mode1"])

		self.Zone_TempSensors_6 = parse_Z_6(Parameters["Mode1"])

		self.Zone_TempSensors_7 = parse_Z_7(Parameters["Mode1"])

		self.Zone_TempSensors_8 = parse_Z_8(Parameters["Mode1"])

		self.Zone_TempSensors_9 = parse_Z_9(Parameters["Mode1"])

		self.Zone_TempSensors_10 = parse_Z_10(Parameters["Mode1"])

		self.Zone_TempSensors_11 = parse_Z_11(Parameters["Mode1"])

		self.Zone_TempSensors_12 = parse_Z_12(Parameters["Mode1"])

		self.zone_1_window = parse_A_1(Parameters["Mode1"])

		self.zone_2_window = parse_A_2(Parameters["Mode1"])

		self.zone_3_window = parse_A_3(Parameters["Mode1"])

		self.zone_4_window = parse_A_4(Parameters["Mode1"])

		self.zone_5_window = parse_A_5(Parameters["Mode1"])

		self.zone_6_window = parse_A_6(Parameters["Mode1"])

		self.zone_7_window = parse_A_7(Parameters["Mode1"])

		self.zone_8_window = parse_A_8(Parameters["Mode1"])

		self.zone_9_window = parse_A_9(Parameters["Mode1"])

		self.zone_10_window = parse_A_10(Parameters["Mode1"])

		self.zone_11_window = parse_A_11(Parameters["Mode1"])

		self.zone_12_window = parse_A_12(Parameters["Mode1"])

		self.Kevero_1_TempSensor = parse_S_1(Parameters["Mode1"])

		self.Kevero_2_TempSensor = parse_S_2(Parameters["Mode1"])

		self.KulsoTempSensors = parse_K(Parameters["Mode1"])

		self.TartalyTempSensors = parse_T(Parameters["Mode1"])

		self.PufferTempSensors = parse_P(Parameters["Mode1"])

		self.szobaTempSensors = parse_L(Parameters["Mode1"])

		self.Kevero_1_szorzo = parse_S_1M(Parameters["Mode1"])

		self.Kevero_2_szorzo = parse_S_2M(Parameters["Mode1"])

		self.Zone_1_F = parse_Z_1_F(Parameters["Mode2"])

		self.Zone_2_F = parse_Z_2_F(Parameters["Mode2"])

		self.Zone_3_F = parse_Z_3_F(Parameters["Mode2"])

		self.Zone_4_F = parse_Z_4_F(Parameters["Mode2"])

		self.Zone_5_F = parse_Z_5_F(Parameters["Mode2"])

		self.Zone_6_F = parse_Z_6_F(Parameters["Mode2"])

		self.Zone_7_F = parse_Z_7_F(Parameters["Mode2"])

		self.Zone_8_F = parse_Z_8_F(Parameters["Mode2"])

		self.Zone_9_F = parse_Z_9_F(Parameters["Mode2"])

		self.Zone_10_F = parse_Z_10_F(Parameters["Mode2"])

		self.Zone_11_F = parse_Z_11_F(Parameters["Mode2"])

		self.Zone_12_F = parse_Z_12_F(Parameters["Mode2"])

		self.Zone_1_F_V = parse_Z_1_F_V(Parameters["Mode2"])

		self.Zone_2_F_V = parse_Z_2_F_V(Parameters["Mode2"])

		self.Zone_3_F_V = parse_Z_3_F_V(Parameters["Mode2"])

		self.Zone_4_F_V = parse_Z_4_F_V(Parameters["Mode2"])

		self.Zone_5_F_V = parse_Z_5_F_V(Parameters["Mode2"])

		self.Zone_6_F_V = parse_Z_6_F_V(Parameters["Mode2"])

		self.Zone_7_F_V = parse_Z_7_F_V(Parameters["Mode2"])

		self.Zone_8_F_V = parse_Z_8_F_V(Parameters["Mode2"])

		self.Zone_9_F_V = parse_Z_9_F_V(Parameters["Mode2"])

		self.Zone_10_F_V = parse_Z_10_F_V(Parameters["Mode2"])

		self.Zone_11_F_V = parse_Z_11_F_V(Parameters["Mode2"])

		self.Zone_12_F_V = parse_Z_12_F_V(Parameters["Mode2"])

		self.Zone_1_H = parse_Z_1_H(Parameters["Mode3"])

		self.Zone_2_H = parse_Z_2_H(Parameters["Mode3"])

		self.Zone_3_H = parse_Z_3_H(Parameters["Mode3"])

		self.Zone_4_H = parse_Z_4_H(Parameters["Mode3"])

		self.Zone_5_H = parse_Z_5_H(Parameters["Mode3"])

		self.Zone_6_H = parse_Z_6_H(Parameters["Mode3"])

		self.Zone_7_H = parse_Z_7_H(Parameters["Mode3"])

		self.Zone_8_H = parse_Z_8_H(Parameters["Mode3"])

		self.Zone_9_H = parse_Z_9_H(Parameters["Mode3"])

		self.Zone_10_H = parse_Z_10_H(Parameters["Mode3"])

		self.Zone_11_H = parse_Z_11_H(Parameters["Mode3"])

		self.Zone_12_H = parse_Z_12_H(Parameters["Mode3"])

		self.Zone_1_H_V = parse_Z_1_H_V(Parameters["Mode3"])

		self.Zone_2_H_V = parse_Z_2_H_V(Parameters["Mode3"])

		self.Zone_3_H_V = parse_Z_3_H_V(Parameters["Mode3"])

		self.Zone_4_H_V = parse_Z_4_H_V(Parameters["Mode3"])

		self.Zone_5_H_V = parse_Z_5_H_V(Parameters["Mode3"])

		self.Zone_6_H_V = parse_Z_6_H_V(Parameters["Mode3"])

		self.Zone_7_H_V = parse_Z_7_H_V(Parameters["Mode3"])

		self.Zone_8_H_V = parse_Z_8_H_V(Parameters["Mode3"])

		self.Zone_9_H_V = parse_Z_9_H_V(Parameters["Mode3"])

		self.Zone_10_H_V = parse_Z_10_H_V(Parameters["Mode3"])

		self.Zone_11_H_V = parse_Z_11_H_V(Parameters["Mode3"])

		self.Zone_12_H_V = parse_Z_12_H_V(Parameters["Mode3"])

		self.ZoneTRV_1 = parse_V_1(Parameters["Mode1"])

		self.ZoneTRV_2 = parse_V_2(Parameters["Mode1"])

		self.ZoneTRV_3 = parse_V_3(Parameters["Mode1"])

		self.ZoneTRV_4 = parse_V_4(Parameters["Mode1"])

		self.ZoneTRV_5 = parse_V_5(Parameters["Mode1"])

		self.ZoneTRV_6 = parse_V_6(Parameters["Mode1"])

		self.ZoneTRV_7 = parse_V_7(Parameters["Mode1"])

		self.ZoneTRV_8 = parse_V_8(Parameters["Mode1"])

		self.ZoneTRV_9 = parse_V_9(Parameters["Mode1"])

		self.ZoneTRV_10 = parse_V_10(Parameters["Mode1"])

		self.ZoneTRV_11 = parse_V_11(Parameters["Mode1"])

		self.ZoneTRV_12 = parse_V_12(Parameters["Mode1"])

		self.ZoneConsole_1 = parse_C_1(Parameters["Mode1"])

		self.ZoneConsole_2 = parse_C_2(Parameters["Mode1"])

		self.ZoneConsole_3 = parse_C_3(Parameters["Mode1"])

		self.ZoneConsole_4 = parse_C_4(Parameters["Mode1"])

		self.ZoneConsole_5 = parse_C_5(Parameters["Mode1"])

		self.ZoneConsole_6 = parse_C_6(Parameters["Mode1"])

		self.ZoneConsole_7 = parse_C_7(Parameters["Mode1"])

		self.ZoneConsole_8 = parse_C_8(Parameters["Mode1"])

		self.ZoneConsole_9 = parse_C_9(Parameters["Mode1"])

		self.ZoneConsole_10 = parse_C_10(Parameters["Mode1"])

		self.ZoneConsole_11 = parse_C_11(Parameters["Mode1"])

		self.ZoneConsole_12 = parse_C_12(Parameters["Mode1"])

		self.Elsodleges_F = parse_F(Parameters["Mode4"])

		self.Masodlagos_F = parse_F(Parameters["Mode5"])

		self.Elsodleges_M = parse_M(Parameters["Mode4"])

		self.Masodlagos_M = parse_M(Parameters["Mode5"])

		self.Tank_1_N = parse_N(Parameters["Mode4"])

		self.Tank_1_O = parse_O(Parameters["Mode4"])

		self.Elsodleges_P_F = parse_P_F(Parameters["Mode4"])

		self.Elsodleges_P_H = parse_P_H(Parameters["Mode4"])

		self.Elsodleges_PE = parse_PE(Parameters["Mode4"])
		
		self.Masodlagos_P_F = parse_P_F(Parameters["Mode5"])

		self.Masodlagos_P_H = parse_P_H(Parameters["Mode5"])

		self.Masodlagos_PE = parse_PE(Parameters["Mode5"])

		self.Elsodleges_E = parse_E(Parameters["Mode4"])

		self.Masodlagos_E = parse_E(Parameters["Mode5"])

		self.Elsodleges_H = parse_H(Parameters["Mode4"])

		self.Masodlagos_H = parse_H(Parameters["Mode5"])

		self.Tank_2_N = parse_N(Parameters["Mode5"])

		self.Tank_2_O = parse_O(Parameters["Mode5"])

		self.Keveroszelep_1_plusz = parse_S_1(Parameters["Mode2"])

		self.Keveroszelep_1_minusz = parse_S_1(Parameters["Mode3"])

		self.Keveroszelep_2_plusz = parse_S_2(Parameters["Mode2"])

		self.Keveroszelep_2_minusz = parse_S_2(Parameters["Mode3"])

		self.before_switch_1 = parse_BK(Parameters["Mode4"])

		self.before_switch_2 = parse_BK(Parameters["Mode5"])

		self.after_switch_1 = parse_UK(Parameters["Mode4"])

		self.after_switch_2 = parse_UK(Parameters["Mode5"])

		self.szoba_on = parse_L(Parameters["Mode1"])

		self.FrostTempSensors = parse_FG_T(Parameters["Mode1"])

		self.FrostSwitches = parse_FG_S(Parameters["Mode2"])

		self.FrostLimit = float(Devices[89].sValue)

		self.PumpProtectionSwitches = parse_SV_P(Parameters["Mode2"])

		self.PumpProtectionDay = parse_SV_D(Parameters["Mode2"])

		self.PumpProtectionHour = parse_SV_H(Parameters["Mode2"])

		self.PumpProtectionMinutes = parse_SV_M(Parameters["Mode2"])

		# Build temperature sensor state when handling timeouts | Hőmérséklet-érzékelő állapotának előállítása időtúllépések kezelésekor
		for sensor in itertools.chain(self.Zone_TempSensors_1, self.Zone_TempSensors_2, self.Zone_TempSensors_3, self.Zone_TempSensors_4, self.Zone_TempSensors_5, self.Zone_TempSensors_6, self.KulsoTempSensors):
			self.ActiveSensors[sensor] = True

		self.parameter_change()


	def onStop(self):
		Domoticz.Debugging(0)

	def onCommand(self, Unit, Command, Level, Color):

		Domoticz.Debug("Command received for unit {0}: command '{1}', level {2} | Egységparancs érkezett: egység={0}, parancs='{1}', szint={2}".format(Unit, Command, Level))

		nvalue = 1 if Level > 0 else 0
		svalue = str(Level)

		Devices[Unit].Update(nValue=nvalue, sValue=svalue)

		if Unit in (12, 29) :
			saveUserVar(self)

		if Devices[65].sValue != "0":
			self.setVarDhwTimer = True
		else:
			self.setVarDhwTimer = False

		if Unit in (3, 7, 18, 14, 30, 31, 76, 15, 16, 17, 21, 22, 35, 36, 37, 4, 5, 8, 9, 39, 40, 41,  43, 45, 47, 49, 51, 53, 55, 64, 67, 61, 62, 59, 60, 70, 71, 72, 73, 63, 75, 77, 79, 80, 81, 82, 90, 92, 93, 94, 96, 100, 102, 103, 105, 106, 107, 108, 109, 110, 111, 112, 115, 116, 117, 118, 119, 120, 121, 122, 155, 162, 163, 164, 165, 166, 167, 168, 169, 170, 171, 172, 173, 174, 175, 176, 178, 179, 180, 181, 182, 183, 184, 185, 186, 187, 188, 189, 190, 191, 192, 193, 194, 195, 196, 197, 198, 199, 200, 201, 202, 203, 204, 205, 206, 207, 208, 209) :
			Domoticz.Debug(f"Unit change detected: {Unit} | Egységváltozás észlelve: {Unit}")
			Domoticz.Debug("Unit changed; calling self.onHeartbeat | Egységváltozás; a self.onHeartbeat hívása")
			self.nextcalc = datetime.now()
			self.nextupdate = datetime.now()
			self.onHeartbeat()
		
		if Unit in (1, 2, 12, 13, 22, 29, 58, 32, 83, 84, 88, 65, 66, 74, 78, 89, 98, 99, 101, 104, 124, 125, 126, 130, 4, 38, 42, 46, 50, 54, 8, 40, 44, 48, 52, 56, 128, 127, 129, 40, 57, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143, 144, 145, 146, 147, 148, 149, 150, 151, 210, 211, 212, 218, 219, 220, 224, 232) :
			Domoticz.Debug(f"Unit change detected: {Unit} | Egységváltozás észlelve: {Unit}")
			Domoticz.Debug("Unit changed; calling self.parameter_change | Egységváltozás; a self.parameter_change hívása")
			self.nextcalc = datetime.now()
			self.nextupdate = datetime.now()
			self.parameter_change()

	def parameter_change(self):

		Domoticz.Debug("Parameter change detected | Paraméterváltozás észlelve")
		
		self.debug = False
		self.TartalyLast = False
		self.PufferLast = False
		self.heating_colling = False
		self.dhw = False
		self.buffer = False
		self.statussupported = True
		self.intemperror = False
		self.tartalytemperror = False
		self.puffertemperror = False
		self.device_1_solar_dhw_on = False
		self.device_2_solar_dhw_on = False
		self.FrostLimit = float(Devices[89].sValue)
		self.FrostHysteresis = float(Devices[156].sValue)
		
		if Devices[88].sValue == "10" :
			self.heating_colling = True
		elif Devices[88].sValue == "20" :
			self.heating_colling = True
			self.dhw = True
		elif Devices[88].sValue == "30" :
			self.heating_colling = True
			self.buffer = True
		elif Devices[88].sValue == "40" :
			self.heating_colling = True
			self.dhw = True
			self.buffer = True
		elif Devices[88].sValue == "50" :
			self.dhw = True

		# If the mode is off, ensure all outputs are off | Ha az üzemmód kikapcsolt, akkor minden legyen kikapcsolva
		if Devices[1].sValue == "0":
			self.switchElsodleges_F(False)
			self.switchMasodlagos_F(False)
			self.switchElsodleges_H(False)
			self.switchMasodlagos_H(False)

			for i in range(1, 13):
				self.switchzone_F(i, False)
				self.send_AC_command(i, "F", "Off")
				self.switchzone_H(i, False)
				self.send_AC_command(i, "H", "Off")

		if Devices[13].sValue == "0":
			self.switchElsodleges_M(False)
			self.switchMasodlagos_M(False)
			self.switchElsodleges_E(False)
			self.switchMasodlagos_E(False)

		if self.Tank_1_N :
			Devices[76].Update(nValue=Devices[76].nValue, sValue=Devices[76].sValue, Used=1)
		else :
			Devices[76].Update(nValue=Devices[76].nValue, sValue=Devices[76].sValue, Used=0)

		if self.dhw :
			Domoticz.Debug("DHW mode enabled (hmv_mod_on) | HMV üzemmód bekapcsolva (hmv_mod_on)")
			Devices[13].Update(nValue=Devices[13].nValue, sValue=Devices[13].sValue, Used=1)
			Devices[29].Update(nValue=Devices[29].nValue, sValue=Devices[29].sValue, Used=1)
			Devices[32].Update(nValue=Devices[32].nValue, sValue=Devices[32].sValue, Used=1)
			Devices[14].Update(nValue=Devices[14].nValue, sValue=Devices[14].sValue, Used=1)
			Devices[30].Update(nValue=Devices[30].nValue, sValue=Devices[30].sValue, Used=1)
			Devices[76].Update(nValue=Devices[76].nValue, sValue=Devices[76].sValue, Used=1)
			Devices[16].Update(nValue=Devices[16].nValue, sValue=Devices[16].sValue, Used=1)
			Devices[15].Update(nValue=Devices[15].nValue, sValue=Devices[15].sValue, Used=1)
			Devices[17].Update(nValue=Devices[17].nValue, sValue=Devices[17].sValue, Used=1)
			Devices[19].Update(nValue=Devices[19].nValue, sValue=Devices[19].sValue, Used=1)
			Devices[35].Update(nValue=Devices[35].nValue, sValue=Devices[35].sValue, Used=1)
			Devices[36].Update(nValue=Devices[36].nValue, sValue=Devices[36].sValue, Used=1)
			Devices[37].Update(nValue=Devices[37].nValue, sValue=Devices[37].sValue, Used=1)
			Devices[78].Update(nValue=Devices[78].nValue, sValue=Devices[78].sValue, Used=1)
			Devices[80].Update(nValue=Devices[80].nValue, sValue=Devices[80].sValue, Used=1)
			Devices[81].Update(nValue=Devices[81].nValue, sValue=Devices[81].sValue, Used=1)
			Devices[113].Update(nValue=Devices[113].nValue, sValue=Devices[113].sValue, Used=1)
			Devices[115].Update(nValue=Devices[115].nValue, sValue=Devices[115].sValue, Used=1)
			Devices[116].Update(nValue=Devices[116].nValue, sValue=Devices[116].sValue, Used=1)
			Devices[83].Update(nValue=Devices[83].nValue, sValue=Devices[83].sValue, Used=1)
			Devices[79].Update(nValue=Devices[79].nValue, sValue=Devices[79].sValue, Used=1)
			Devices[31].Update(nValue=Devices[31].nValue, sValue=Devices[31].sValue, Used=1)
			Devices[225].Update(nValue=Devices[225].nValue, sValue=Devices[225].sValue, Used=1)
			Devices[222].Update(nValue=Devices[222].nValue, sValue=Devices[222].sValue, Used=1)
			Devices[233].Update(nValue=Devices[233].nValue, sValue=Devices[233].sValue, Used=1)
			Devices[234].Update(nValue=Devices[234].nValue, sValue=Devices[234].sValue, Used=1)
			Devices[239].Update(nValue=Devices[239].nValue, sValue=Devices[239].sValue, Used=1)
		else :
			Domoticz.Debug("DHW mode disabled (hmv_mod_off) | HMV üzemmód kikapcsolva (hmv_mod_off)")
			Devices[13].Update(nValue=Devices[13].nValue, sValue="0", Used=0)
			Devices[29].Update(nValue=Devices[29].nValue, sValue=Devices[29].sValue, Used=0)
			Devices[32].Update(nValue=Devices[32].nValue, sValue=Devices[32].sValue, Used=0)
			Devices[14].Update(nValue=Devices[14].nValue, sValue=Devices[14].sValue, Used=0)
			Devices[30].Update(nValue=Devices[30].nValue, sValue=Devices[30].sValue, Used=0)
			Devices[76].Update(nValue=Devices[76].nValue, sValue=Devices[76].sValue, Used=0)
			Devices[15].Update(nValue=Devices[15].nValue, sValue=Devices[15].sValue, Used=0)
			Devices[16].Update(nValue=Devices[16].nValue, sValue=Devices[16].sValue, Used=0)
			Devices[17].Update(nValue=Devices[17].nValue, sValue=Devices[17].sValue, Used=0)
			Devices[19].Update(nValue=Devices[19].nValue, sValue=Devices[19].sValue, Used=0)
			Devices[35].Update(nValue=Devices[35].nValue, sValue=Devices[35].sValue, Used=0)
			Devices[36].Update(nValue=Devices[36].nValue, sValue=Devices[36].sValue, Used=0)
			Devices[37].Update(nValue=Devices[37].nValue, sValue=Devices[37].sValue, Used=0)
			Devices[78].Update(nValue=Devices[78].nValue, sValue=Devices[78].sValue, Used=0)
			Devices[80].Update(nValue=Devices[80].nValue, sValue=Devices[80].sValue, Used=0)
			Devices[81].Update(nValue=Devices[81].nValue, sValue=Devices[81].sValue, Used=0)
			Devices[113].Update(nValue=Devices[113].nValue, sValue=Devices[113].sValue, Used=0)
			Devices[115].Update(nValue=Devices[115].nValue, sValue=Devices[115].sValue, Used=0)
			Devices[116].Update(nValue=Devices[116].nValue, sValue=Devices[116].sValue, Used=0)
			Devices[83].Update(nValue=Devices[83].nValue, sValue=Devices[83].sValue, Used=0)
			Devices[79].Update(nValue=Devices[79].nValue, sValue=Devices[79].sValue, Used=0)
			Devices[31].Update(nValue=Devices[31].nValue, sValue=Devices[31].sValue, Used=0)
			Devices[91].Update(nValue=Devices[91].nValue, sValue=Devices[91].sValue, Used=0)
			Devices[58].Update(nValue=Devices[58].nValue, sValue=Devices[58].sValue, Used=0)
			Devices[225].Update(nValue=Devices[225].nValue, sValue=Devices[225].sValue, Used=0)
			Devices[222].Update(nValue=Devices[222].nValue, sValue=Devices[222].sValue, Used=0)
			Devices[233].Update(nValue=Devices[233].nValue, sValue=Devices[233].sValue, Used=0)
			Devices[234].Update(nValue=Devices[234].nValue, sValue=Devices[234].sValue, Used=0)
			Devices[239].Update(nValue=Devices[239].nValue, sValue=Devices[239].sValue, Used=0)

		if self.buffer :
			Domoticz.Debug("Buffer mode enabled (buffer_mod_on) | Puffer üzemmód bekapcsolva (buffer_mod_on)")
			if Devices[58].sValue == "10":
				Devices[104].Update(nValue=Devices[104].nValue, sValue=Devices[104].sValue, Used=1)
				Devices[224].Update(nValue=Devices[224].nValue, sValue=Devices[224].sValue, Used=0)
			else:
				Devices[224].Update(nValue=Devices[224].nValue, sValue=Devices[224].sValue, Used=1)
				Devices[104].Update(nValue=Devices[104].nValue, sValue=Devices[104].sValue, Used=0)
			Devices[90].Update(nValue=Devices[90].nValue, sValue=Devices[90].sValue, Used=1)
			Devices[92].Update(nValue=Devices[92].nValue, sValue=Devices[92].sValue, Used=1)
			Devices[94].Update(nValue=Devices[94].nValue, sValue=Devices[94].sValue, Used=1)
			Devices[96].Update(nValue=Devices[96].nValue, sValue=Devices[96].sValue, Used=1)
			Devices[98].Update(nValue=Devices[98].nValue, sValue=Devices[98].sValue, Used=1)
			Devices[108].Update(nValue=Devices[108].nValue, sValue=Devices[108].sValue, Used=1)
			Devices[109].Update(nValue=Devices[109].nValue, sValue=Devices[109].sValue, Used=1)
			Devices[110].Update(nValue=Devices[110].nValue, sValue=Devices[110].sValue, Used=1)
			Devices[111].Update(nValue=Devices[111].nValue, sValue=Devices[111].sValue, Used=1)
			Devices[114].Update(nValue=Devices[114].nValue, sValue=Devices[114].sValue, Used=1)
			Devices[117].Update(nValue=Devices[117].nValue, sValue=Devices[117].sValue, Used=1)
			Devices[118].Update(nValue=Devices[118].nValue, sValue=Devices[118].sValue, Used=1)
			Devices[123].Update(nValue=Devices[123].nValue, sValue=Devices[123].sValue, Used=1)
			Devices[84].Update(nValue=Devices[84].nValue, sValue=Devices[84].sValue, Used=1)
			Devices[82].Update(nValue=Devices[82].nValue, sValue=Devices[82].sValue, Used=1)
			Devices[77].Update(nValue=Devices[77].nValue, sValue=Devices[77].sValue, Used=1)
			Devices[91].Update(nValue=Devices[91].nValue, sValue=Devices[91].sValue, Used=1)
			Devices[95].Update(nValue=Devices[95].nValue, sValue=Devices[95].sValue, Used=1)
			Devices[99].Update(nValue=Devices[99].nValue, sValue=Devices[99].sValue, Used=1)
			Devices[93].Update(nValue=Devices[93].nValue, sValue=Devices[93].sValue, Used=1)
			Devices[58].Update(nValue=Devices[58].nValue, sValue=Devices[58].sValue, Used=1)
			Devices[223].Update(nValue=Devices[223].nValue, sValue=Devices[223].sValue, Used=1)
			Devices[226].Update(nValue=Devices[226].nValue, sValue=Devices[226].sValue, Used=1)
			Devices[227].Update(nValue=Devices[227].nValue, sValue=Devices[227].sValue, Used=1)
			Devices[235].Update(nValue=Devices[235].nValue, sValue=Devices[235].sValue, Used=1)
			Devices[236].Update(nValue=Devices[236].nValue, sValue=Devices[236].sValue, Used=1)
			Devices[237].Update(nValue=Devices[237].nValue, sValue=Devices[237].sValue, Used=1)
		else :
			Domoticz.Debug("Buffer mode disabled (puffer_mod_off) | Puffer üzemmód kikapcsolva (puffer_mod_off)")
			Devices[104].Update(nValue=Devices[104].nValue, sValue="0", Used=0)
			Devices[224].Update(nValue=Devices[224].nValue, sValue="0", Used=0)
			Devices[90].Update(nValue=Devices[90].nValue, sValue=Devices[90].sValue, Used=0)
			Devices[92].Update(nValue=Devices[92].nValue, sValue=Devices[92].sValue, Used=0)
			Devices[94].Update(nValue=Devices[94].nValue, sValue=Devices[94].sValue, Used=0)
			Devices[96].Update(nValue=Devices[96].nValue, sValue=Devices[96].sValue, Used=0)
			Devices[98].Update(nValue=Devices[98].nValue, sValue=Devices[98].sValue, Used=0)
			Devices[108].Update(nValue=Devices[108].nValue, sValue=Devices[108].sValue, Used=0)
			Devices[109].Update(nValue=Devices[109].nValue, sValue=Devices[109].sValue, Used=0)
			Devices[110].Update(nValue=Devices[110].nValue, sValue=Devices[110].sValue, Used=0)
			Devices[111].Update(nValue=Devices[111].nValue, sValue=Devices[111].sValue, Used=0)
			Devices[114].Update(nValue=Devices[114].nValue, sValue=Devices[114].sValue, Used=0)
			Devices[117].Update(nValue=Devices[117].nValue, sValue=Devices[117].sValue, Used=0)
			Devices[118].Update(nValue=Devices[118].nValue, sValue=Devices[118].sValue, Used=0)
			Devices[123].Update(nValue=Devices[123].nValue, sValue=Devices[123].sValue, Used=0)
			Devices[84].Update(nValue=Devices[84].nValue, sValue=Devices[84].sValue, Used=0)
			Devices[82].Update(nValue=Devices[82].nValue, sValue=Devices[82].sValue, Used=0)
			Devices[77].Update(nValue=Devices[77].nValue, sValue=Devices[77].sValue, Used=0)
			Devices[95].Update(nValue=Devices[95].nValue, sValue=Devices[95].sValue, Used=0)
			Devices[99].Update(nValue=Devices[99].nValue, sValue=Devices[99].sValue, Used=0)
			Devices[93].Update(nValue=Devices[93].nValue, sValue=Devices[93].sValue, Used=0)
			Devices[223].Update(nValue=Devices[223].nValue, sValue=Devices[223].sValue, Used=0)
			Devices[226].Update(nValue=Devices[226].nValue, sValue=Devices[226].sValue, Used=0)
			Devices[227].Update(nValue=Devices[227].nValue, sValue=Devices[227].sValue, Used=0)
			Devices[235].Update(nValue=Devices[235].nValue, sValue=Devices[235].sValue, Used=0)
			Devices[236].Update(nValue=Devices[236].nValue, sValue=Devices[236].sValue, Used=0)
			Devices[237].Update(nValue=Devices[237].nValue, sValue=Devices[237].sValue, Used=0)

		if self.heating_colling :
			Domoticz.Debug("Heating/cooling enabled (heating_colling_on) | Fűtés/hűtés bekapcsolva (heating_colling_on)")
			if Devices[58].sValue == "10":
				Devices[1].Update(nValue=Devices[1].nValue, sValue=Devices[1].sValue, Used=1)
				Devices[22].Update(nValue=Devices[22].nValue, sValue=Devices[22].sValue, Used=0)
			else:
				Devices[22].Update(nValue=Devices[22].nValue, sValue=Devices[22].sValue, Used=1)
				Devices[1].Update(nValue=Devices[1].nValue, sValue=Devices[1].sValue, Used=0)
			Devices[2].Update(nValue=Devices[2].nValue, sValue=Devices[2].sValue, Used=1)
			Devices[3].Update(nValue=Devices[3].nValue, sValue=Devices[3].sValue, Used=1)
			Devices[6].Update(nValue=Devices[6].nValue, sValue=Devices[6].sValue, Used=1)
			Devices[7].Update(nValue=Devices[7].nValue, sValue=Devices[7].sValue, Used=1)
			Devices[10].Update(nValue=Devices[10].nValue, sValue=Devices[10].sValue, Used=1)
			Devices[18].Update(nValue=Devices[18].nValue, sValue=Devices[18].sValue, Used=1)
			Devices[12].Update(nValue=Devices[12].nValue, sValue=Devices[12].sValue, Used=1)
			Devices[64].Update(nValue=Devices[64].nValue, sValue=Devices[64].sValue, Used=1)
			Devices[66].Update(nValue=Devices[66].nValue, sValue=Devices[66].sValue, Used=1)
			Devices[67].Update(nValue=Devices[67].nValue, sValue=Devices[67].sValue, Used=1)
			Devices[62].Update(nValue=Devices[62].nValue, sValue=Devices[62].sValue, Used=1)
			Devices[60].Update(nValue=Devices[60].nValue, sValue=Devices[60].sValue, Used=1)
			Devices[74].Update(nValue=Devices[74].nValue, sValue=Devices[74].sValue, Used=1)
			Devices[63].Update(nValue=Devices[63].nValue, sValue=Devices[63].sValue, Used=1)
			Devices[85].Update(nValue=Devices[85].nValue, sValue=Devices[85].sValue, Used=1)
			Devices[112].Update(nValue=Devices[112].nValue, sValue=Devices[112].sValue, Used=1)
			Devices[58].Update(nValue=Devices[58].nValue, sValue=Devices[58].sValue, Used=1)
			Devices[101].Update(nValue=Devices[101].nValue, sValue=Devices[101].sValue, Used=1)
			Devices[124].Update(nValue=Devices[124].nValue, sValue=Devices[124].sValue, Used=1)
			Devices[125].Update(nValue=Devices[125].nValue, sValue=Devices[125].sValue, Used=1)
			Devices[126].Update(nValue=Devices[126].nValue, sValue=Devices[126].sValue, Used=1)
			Devices[127].Update(nValue=Devices[127].nValue, sValue=Devices[127].sValue, Used=1)
			Devices[128].Update(nValue=Devices[128].nValue, sValue=Devices[128].sValue, Used=1)
			Devices[129].Update(nValue=Devices[129].nValue, sValue=Devices[129].sValue, Used=1)
			Devices[130].Update(nValue=Devices[130].nValue, sValue=Devices[130].sValue, Used=1)
			Devices[216].Update(nValue=Devices[216].nValue, sValue=Devices[216].sValue, Used=1)
			Devices[58].Update(nValue=Devices[58].nValue, sValue=Devices[58].sValue, Used=1)
			Devices[214].Update(nValue=Devices[214].nValue, sValue=Devices[214].sValue, Used=1)
			Devices[215].Update(nValue=Devices[215].nValue, sValue=Devices[215].sValue, Used=1)
			Devices[211].Update(nValue=Devices[211].nValue, sValue=Devices[211].sValue, Used=1)
			Devices[212].Update(nValue=Devices[212].nValue, sValue=Devices[212].sValue, Used=1)
			Devices[217].Update(nValue=Devices[217].nValue, sValue=Devices[217].sValue, Used=1)
			Devices[221].Update(nValue=Devices[221].nValue, sValue=Devices[221].sValue, Used=1)
			Devices[155].Update(nValue=Devices[155].nValue, sValue=Devices[155].sValue, Used=1)
			Devices[213].Update(nValue=Devices[213].nValue, sValue=Devices[213].sValue, Used=1)
			Devices[86].Update(nValue=Devices[86].nValue, sValue=Devices[86].sValue, Used=1)
			Devices[228].Update(nValue=Devices[228].nValue, sValue=Devices[228].sValue, Used=1)
			Devices[229].Update(nValue=Devices[229].nValue, sValue=Devices[229].sValue, Used=1)
			Devices[230].Update(nValue=Devices[230].nValue, sValue=Devices[230].sValue, Used=1)
			Devices[231].Update(nValue=Devices[231].nValue, sValue=Devices[231].sValue, Used=1)
			Devices[238].Update(nValue=Devices[238].nValue, sValue=Devices[238].sValue, Used=1)
			Devices[252].Update(nValue=Devices[252].nValue, sValue=Devices[252].sValue, Used=1)

		else :
			Domoticz.Debug("Heating/cooling disabled (heating_colling_off) | Fűtés/hűtés kikapcsolva (heating_colling_off)")
			Devices[1].Update(nValue=Devices[1].nValue, sValue="0", Used=0)
			Devices[22].Update(nValue=Devices[22].nValue, sValue="0", Used=0)
			Devices[2].Update(nValue=Devices[2].nValue, sValue=Devices[2].sValue, Used=0)
			Devices[3].Update(nValue=Devices[3].nValue, sValue=Devices[3].sValue, Used=0)
			Devices[6].Update(nValue=Devices[6].nValue, sValue=Devices[6].sValue, Used=0)
			Devices[7].Update(nValue=Devices[7].nValue, sValue=Devices[7].sValue, Used=0)
			Devices[10].Update(nValue=Devices[10].nValue, sValue=Devices[10].sValue, Used=0)
			Devices[18].Update(nValue=Devices[18].nValue, sValue=Devices[18].sValue, Used=0)
			Devices[12].Update(nValue=Devices[12].nValue, sValue=Devices[12].sValue, Used=0)
			Devices[64].Update(nValue=Devices[64].nValue, sValue=Devices[64].sValue, Used=0)
			Devices[66].Update(nValue=Devices[66].nValue, sValue=Devices[66].sValue, Used=0)
			Devices[67].Update(nValue=Devices[67].nValue, sValue=Devices[67].sValue, Used=0)
			Devices[62].Update(nValue=Devices[62].nValue, sValue=Devices[62].sValue, Used=0)
			Devices[60].Update(nValue=Devices[60].nValue, sValue=Devices[60].sValue, Used=0)
			Devices[74].Update(nValue=Devices[74].nValue, sValue=Devices[74].sValue, Used=0)
			Devices[63].Update(nValue=Devices[63].nValue, sValue=Devices[63].sValue, Used=0)
			Devices[85].Update(nValue=Devices[85].nValue, sValue=Devices[85].sValue, Used=0)
			Devices[112].Update(nValue=Devices[112].nValue, sValue=Devices[112].sValue, Used=0)
			Devices[101].Update(nValue=Devices[101].nValue, sValue=Devices[101].sValue, Used=0)
			Devices[124].Update(nValue=Devices[124].nValue, sValue=Devices[124].sValue, Used=0)
			Devices[125].Update(nValue=Devices[125].nValue, sValue=Devices[125].sValue, Used=0)
			Devices[126].Update(nValue=Devices[126].nValue, sValue=Devices[126].sValue, Used=0)
			Devices[127].Update(nValue=Devices[127].nValue, sValue=Devices[127].sValue, Used=0)
			Devices[128].Update(nValue=Devices[128].nValue, sValue=Devices[128].sValue, Used=0)
			Devices[129].Update(nValue=Devices[129].nValue, sValue=Devices[129].sValue, Used=0)
			Devices[130].Update(nValue=Devices[130].nValue, sValue=Devices[130].sValue, Used=0)
			Devices[216].Update(nValue=Devices[216].nValue, sValue=Devices[216].sValue, Used=0)
			Devices[58].Update(nValue=Devices[58].nValue, sValue=Devices[58].sValue, Used=0)
			Devices[214].Update(nValue=Devices[214].nValue, sValue=Devices[214].sValue, Used=0)
			Devices[215].Update(nValue=Devices[215].nValue, sValue=Devices[215].sValue, Used=0)
			Devices[211].Update(nValue=Devices[211].nValue, sValue=Devices[211].sValue, Used=0)
			Devices[212].Update(nValue=Devices[212].nValue, sValue=Devices[212].sValue, Used=0)
			Devices[217].Update(nValue=Devices[217].nValue, sValue=Devices[217].sValue, Used=0)
			Devices[221].Update(nValue=Devices[221].nValue, sValue=Devices[221].sValue, Used=0)
			Devices[155].Update(nValue=Devices[155].nValue, sValue=Devices[155].sValue, Used=0)
			Devices[213].Update(nValue=Devices[213].nValue, sValue=Devices[213].sValue, Used=0)
			Devices[86].Update(nValue=Devices[86].nValue, sValue=Devices[86].sValue, Used=0)
			Devices[228].Update(nValue=Devices[228].nValue, sValue=Devices[228].sValue, Used=0)
			Devices[229].Update(nValue=Devices[229].nValue, sValue=Devices[229].sValue, Used=0)
			Devices[230].Update(nValue=Devices[230].nValue, sValue=Devices[230].sValue, Used=0)
			Devices[231].Update(nValue=Devices[231].nValue, sValue=Devices[231].sValue, Used=0)
			Devices[238].Update(nValue=Devices[238].nValue, sValue=Devices[238].sValue, Used=0)
			Devices[252].Update(nValue=Devices[252].nValue, sValue=Devices[252].sValue, Used=0)


		if self.dhw and (self.heating_colling or self.buffer):
			Devices[65].Update(nValue=Devices[65].nValue, sValue=Devices[65].sValue, Used=1)
		else :
			Devices[65].Update(nValue=Devices[65].nValue, sValue="0", Used=0)

		if self.Zone_TempSensors_1 and self.heating_colling:
			Devices[4].Update(nValue=Devices[4].nValue, sValue=Devices[4].sValue, Used=1)
			Devices[5].Update(nValue=Devices[5].nValue, sValue=Devices[5].sValue, Used=1)
			Devices[8].Update(nValue=Devices[8].nValue, sValue=Devices[8].sValue, Used=1)
			Devices[9].Update(nValue=Devices[9].nValue, sValue=Devices[9].sValue, Used=1)
			Devices[126].Update(nValue=Devices[126].nValue, sValue=Devices[126].sValue, Used=1)
			Devices[127].Update(nValue=Devices[127].nValue, sValue=Devices[127].sValue, Used=1)
			Devices[128].Update(nValue=Devices[128].nValue, sValue=Devices[128].sValue, Used=1)
			Devices[129].Update(nValue=Devices[129].nValue, sValue=Devices[129].sValue, Used=1)
			if self.zone_1_window:
				Devices[240].Update(nValue=Devices[240].nValue, sValue=Devices[240].sValue, Used=1)
				if ((Devices[1].Used == 1 and Devices[1].sValue != "0") or (Devices[22].Used == 1 and Devices[22].sValue != "0")) and Devices[210].sValue == "10" :
					self.addfavorite(Devices[240].ID)
				elif Devices[210].sValue == "10" :
					self.removefavorite(Devices[240].ID)
			else:
				Devices[240].Update(nValue=Devices[240].nValue, sValue=Devices[240].sValue, Used=0)
		else :
			Devices[4].Update(nValue=Devices[4].nValue, sValue=Devices[4].sValue, Used=0)
			Devices[5].Update(nValue=Devices[5].nValue, sValue=Devices[5].sValue, Used=0)
			Devices[8].Update(nValue=Devices[8].nValue, sValue=Devices[8].sValue, Used=0)
			Devices[9].Update(nValue=Devices[9].nValue, sValue=Devices[9].sValue, Used=0)
			Devices[126].Update(nValue=Devices[126].nValue, sValue=Devices[126].sValue, Used=0)
			Devices[127].Update(nValue=Devices[127].nValue, sValue=Devices[127].sValue, Used=0)
			Devices[128].Update(nValue=Devices[128].nValue, sValue=Devices[128].sValue, Used=0)
			Devices[129].Update(nValue=Devices[129].nValue, sValue=Devices[129].sValue, Used=0)
			Devices[240].Update(nValue=Devices[240].nValue, sValue=Devices[240].sValue, Used=0)

		if self.Zone_TempSensors_2 and self.heating_colling:
			Devices[38].Update(nValue=Devices[38].nValue, sValue=Devices[38].sValue, Used=1)
			Devices[39].Update(nValue=Devices[39].nValue, sValue=Devices[39].sValue, Used=1)
			Devices[40].Update(nValue=Devices[40].nValue, sValue=Devices[40].sValue, Used=1)
			Devices[41].Update(nValue=Devices[41].nValue, sValue=Devices[41].sValue, Used=1)
			Devices[132].Update(nValue=Devices[132].nValue, sValue=Devices[132].sValue, Used=1)
			Devices[133].Update(nValue=Devices[133].nValue, sValue=Devices[133].sValue, Used=1)
			Devices[134].Update(nValue=Devices[134].nValue, sValue=Devices[134].sValue, Used=1)
			Devices[135].Update(nValue=Devices[135].nValue, sValue=Devices[135].sValue, Used=1)
			if self.zone_2_window:
				Devices[241].Update(nValue=Devices[241].nValue, sValue=Devices[241].sValue, Used=1)
				if ((Devices[1].Used == 1 and Devices[1].sValue != "0") or (Devices[22].Used == 1 and Devices[22].sValue != "0")) and Devices[210].sValue == "10" :
					self.addfavorite(Devices[241].ID)
				elif Devices[210].sValue == "10" :
					self.removefavorite(Devices[241].ID)
			else:
				Devices[241].Update(nValue=Devices[241].nValue, sValue=Devices[241].sValue, Used=0)
		else :
			Devices[38].Update(nValue=Devices[38].nValue, sValue=Devices[38].sValue, Used=0)
			Devices[39].Update(nValue=Devices[39].nValue, sValue=Devices[39].sValue, Used=0)
			Devices[40].Update(nValue=Devices[40].nValue, sValue=Devices[40].sValue, Used=0)
			Devices[41].Update(nValue=Devices[41].nValue, sValue=Devices[41].sValue, Used=0)
			Devices[132].Update(nValue=Devices[132].nValue, sValue=Devices[132].sValue, Used=0)
			Devices[133].Update(nValue=Devices[133].nValue, sValue=Devices[133].sValue, Used=0)
			Devices[134].Update(nValue=Devices[134].nValue, sValue=Devices[134].sValue, Used=0)
			Devices[135].Update(nValue=Devices[135].nValue, sValue=Devices[135].sValue, Used=0)
			Devices[241].Update(nValue=Devices[241].nValue, sValue=Devices[241].sValue, Used=0)

		if self.Zone_TempSensors_3 and self.heating_colling:
			Devices[42].Update(nValue=Devices[42].nValue, sValue=Devices[42].sValue, Used=1)
			Devices[43].Update(nValue=Devices[43].nValue, sValue=Devices[43].sValue, Used=1)
			Devices[44].Update(nValue=Devices[44].nValue, sValue=Devices[44].sValue, Used=1)
			Devices[45].Update(nValue=Devices[45].nValue, sValue=Devices[45].sValue, Used=1)
			Devices[136].Update(nValue=Devices[136].nValue, sValue=Devices[136].sValue, Used=1)
			Devices[137].Update(nValue=Devices[137].nValue, sValue=Devices[137].sValue, Used=1)
			Devices[138].Update(nValue=Devices[138].nValue, sValue=Devices[138].sValue, Used=1)
			Devices[139].Update(nValue=Devices[139].nValue, sValue=Devices[139].sValue, Used=1)
			if self.zone_3_window:
				Devices[242].Update(nValue=Devices[242].nValue, sValue=Devices[242].sValue, Used=1)
				if ((Devices[1].Used == 1 and Devices[1].sValue != "0") or (Devices[22].Used == 1 and Devices[22].sValue != "0")) and Devices[210].sValue == "10" :
					self.addfavorite(Devices[242].ID)
				elif Devices[210].sValue == "10" :
					self.removefavorite(Devices[242].ID)
			else:
				Devices[242].Update(nValue=Devices[242].nValue, sValue=Devices[242].sValue, Used=0)
		else :
			Devices[42].Update(nValue=Devices[42].nValue, sValue=Devices[42].sValue, Used=0)
			Devices[43].Update(nValue=Devices[43].nValue, sValue=Devices[43].sValue, Used=0)
			Devices[44].Update(nValue=Devices[44].nValue, sValue=Devices[44].sValue, Used=0)
			Devices[45].Update(nValue=Devices[45].nValue, sValue=Devices[45].sValue, Used=0)
			Devices[136].Update(nValue=Devices[136].nValue, sValue=Devices[136].sValue, Used=0)
			Devices[137].Update(nValue=Devices[137].nValue, sValue=Devices[137].sValue, Used=0)
			Devices[138].Update(nValue=Devices[138].nValue, sValue=Devices[138].sValue, Used=0)
			Devices[139].Update(nValue=Devices[139].nValue, sValue=Devices[139].sValue, Used=0)
			Devices[242].Update(nValue=Devices[242].nValue, sValue=Devices[242].sValue, Used=0)
		
		if self.Zone_TempSensors_4 and self.heating_colling:
			Devices[46].Update(nValue=Devices[46].nValue, sValue=Devices[46].sValue, Used=1)
			Devices[47].Update(nValue=Devices[47].nValue, sValue=Devices[47].sValue, Used=1)
			Devices[48].Update(nValue=Devices[48].nValue, sValue=Devices[48].sValue, Used=1)
			Devices[49].Update(nValue=Devices[49].nValue, sValue=Devices[49].sValue, Used=1)
			Devices[140].Update(nValue=Devices[140].nValue, sValue=Devices[140].sValue, Used=1)
			Devices[141].Update(nValue=Devices[141].nValue, sValue=Devices[141].sValue, Used=1)
			Devices[142].Update(nValue=Devices[142].nValue, sValue=Devices[142].sValue, Used=1)
			Devices[143].Update(nValue=Devices[143].nValue, sValue=Devices[143].sValue, Used=1)
			if self.zone_4_window:
				Devices[243].Update(nValue=Devices[243].nValue, sValue=Devices[243].sValue, Used=1)
				if ((Devices[1].Used == 1 and Devices[1].sValue != "0") or (Devices[22].Used == 1 and Devices[22].sValue != "0")) and Devices[210].sValue == "10" :
					self.addfavorite(Devices[243].ID)
				elif Devices[210].sValue == "10" :
					self.removefavorite(Devices[243].ID)
			else:
				Devices[243].Update(nValue=Devices[243].nValue, sValue=Devices[243].sValue, Used=0)
		else :
			Devices[46].Update(nValue=Devices[46].nValue, sValue=Devices[46].sValue, Used=0)
			Devices[47].Update(nValue=Devices[47].nValue, sValue=Devices[47].sValue, Used=0)
			Devices[48].Update(nValue=Devices[48].nValue, sValue=Devices[48].sValue, Used=0)
			Devices[49].Update(nValue=Devices[49].nValue, sValue=Devices[49].sValue, Used=0)
			Devices[140].Update(nValue=Devices[140].nValue, sValue=Devices[140].sValue, Used=0)
			Devices[141].Update(nValue=Devices[141].nValue, sValue=Devices[141].sValue, Used=0)
			Devices[142].Update(nValue=Devices[142].nValue, sValue=Devices[142].sValue, Used=0)
			Devices[143].Update(nValue=Devices[143].nValue, sValue=Devices[143].sValue, Used=0)
			Devices[243].Update(nValue=Devices[243].nValue, sValue=Devices[243].sValue, Used=0)
		
		if self.Zone_TempSensors_5 and self.heating_colling:
			Devices[50].Update(nValue=Devices[50].nValue, sValue=Devices[50].sValue, Used=1)
			Devices[51].Update(nValue=Devices[51].nValue, sValue=Devices[51].sValue, Used=1)
			Devices[52].Update(nValue=Devices[52].nValue, sValue=Devices[52].sValue, Used=1)
			Devices[53].Update(nValue=Devices[53].nValue, sValue=Devices[53].sValue, Used=1)
			Devices[144].Update(nValue=Devices[144].nValue, sValue=Devices[144].sValue, Used=1)
			Devices[145].Update(nValue=Devices[145].nValue, sValue=Devices[145].sValue, Used=1)
			Devices[146].Update(nValue=Devices[146].nValue, sValue=Devices[146].sValue, Used=1)
			Devices[147].Update(nValue=Devices[147].nValue, sValue=Devices[147].sValue, Used=1)
			if self.zone_5_window:
				Devices[244].Update(nValue=Devices[244].nValue, sValue=Devices[244].sValue, Used=1)
				if ((Devices[1].Used == 1 and Devices[1].sValue != "0") or (Devices[22].Used == 1 and Devices[22].sValue != "0")) and Devices[210].sValue == "10" :
					self.addfavorite(Devices[244].ID)
				elif Devices[210].sValue == "10" :
					self.removefavorite(Devices[244].ID)
			else:
				Devices[244].Update(nValue=Devices[244].nValue, sValue=Devices[244].sValue, Used=0)
		else :
			Devices[50].Update(nValue=Devices[50].nValue, sValue=Devices[50].sValue, Used=0)
			Devices[51].Update(nValue=Devices[51].nValue, sValue=Devices[51].sValue, Used=0)
			Devices[52].Update(nValue=Devices[52].nValue, sValue=Devices[52].sValue, Used=0)
			Devices[53].Update(nValue=Devices[53].nValue, sValue=Devices[53].sValue, Used=0)
			Devices[144].Update(nValue=Devices[144].nValue, sValue=Devices[144].sValue, Used=0)
			Devices[145].Update(nValue=Devices[145].nValue, sValue=Devices[145].sValue, Used=0)
			Devices[146].Update(nValue=Devices[146].nValue, sValue=Devices[146].sValue, Used=0)
			Devices[147].Update(nValue=Devices[147].nValue, sValue=Devices[147].sValue, Used=0)
			Devices[244].Update(nValue=Devices[244].nValue, sValue=Devices[244].sValue, Used=0)

		if self.Zone_TempSensors_6 and self.heating_colling:
			Devices[54].Update(nValue=Devices[54].nValue, sValue=Devices[54].sValue, Used=1)
			Devices[55].Update(nValue=Devices[55].nValue, sValue=Devices[55].sValue, Used=1)
			Devices[56].Update(nValue=Devices[56].nValue, sValue=Devices[56].sValue, Used=1)
			Devices[57].Update(nValue=Devices[57].nValue, sValue=Devices[57].sValue, Used=1)
			Devices[148].Update(nValue=Devices[148].nValue, sValue=Devices[148].sValue, Used=1)
			Devices[149].Update(nValue=Devices[149].nValue, sValue=Devices[149].sValue, Used=1)
			Devices[150].Update(nValue=Devices[150].nValue, sValue=Devices[150].sValue, Used=1)
			Devices[151].Update(nValue=Devices[151].nValue, sValue=Devices[151].sValue, Used=1)
			if self.zone_6_window:
				Devices[245].Update(nValue=Devices[245].nValue, sValue=Devices[245].sValue, Used=1)
				if ((Devices[1].Used == 1 and Devices[1].sValue != "0") or (Devices[22].Used == 1 and Devices[22].sValue != "0")) and Devices[210].sValue == "10" :
					self.addfavorite(Devices[245].ID)
				elif Devices[210].sValue == "10" :
					self.removefavorite(Devices[245].ID)
			else:
				Devices[245].Update(nValue=Devices[245].nValue, sValue=Devices[245].sValue, Used=0)
		else :
			Devices[54].Update(nValue=Devices[54].nValue, sValue=Devices[54].sValue, Used=0)
			Devices[55].Update(nValue=Devices[55].nValue, sValue=Devices[55].sValue, Used=0)
			Devices[56].Update(nValue=Devices[56].nValue, sValue=Devices[56].sValue, Used=0)
			Devices[57].Update(nValue=Devices[57].nValue, sValue=Devices[57].sValue, Used=0)
			Devices[148].Update(nValue=Devices[148].nValue, sValue=Devices[148].sValue, Used=0)
			Devices[149].Update(nValue=Devices[149].nValue, sValue=Devices[149].sValue, Used=0)
			Devices[150].Update(nValue=Devices[150].nValue, sValue=Devices[150].sValue, Used=0)
			Devices[151].Update(nValue=Devices[151].nValue, sValue=Devices[151].sValue, Used=0)
			Devices[245].Update(nValue=Devices[245].nValue, sValue=Devices[245].sValue, Used=0)

		if self.Zone_TempSensors_7 and self.heating_colling:
			Devices[162].Update(nValue=Devices[162].nValue, sValue=Devices[162].sValue, Used=1)
			Devices[163].Update(nValue=Devices[163].nValue, sValue=Devices[163].sValue, Used=1)
			Devices[164].Update(nValue=Devices[164].nValue, sValue=Devices[164].sValue, Used=1)
			Devices[165].Update(nValue=Devices[165].nValue, sValue=Devices[165].sValue, Used=1)
			Devices[166].Update(nValue=Devices[166].nValue, sValue=Devices[166].sValue, Used=1)
			Devices[167].Update(nValue=Devices[167].nValue, sValue=Devices[167].sValue, Used=1)
			Devices[168].Update(nValue=Devices[168].nValue, sValue=Devices[168].sValue, Used=1)
			Devices[169].Update(nValue=Devices[169].nValue, sValue=Devices[169].sValue, Used=1)
			if self.zone_7_window:
				Devices[246].Update(nValue=Devices[246].nValue, sValue=Devices[246].sValue, Used=1)
				if ((Devices[1].Used == 1 and Devices[1].sValue != "0") or (Devices[22].Used == 1 and Devices[22].sValue != "0")) and Devices[210].sValue == "10" :
					self.addfavorite(Devices[246].ID)
				elif Devices[210].sValue == "10" :
					self.removefavorite(Devices[246].ID)
			else:
				Devices[246].Update(nValue=Devices[246].nValue, sValue=Devices[246].sValue, Used=0)
		else :
			Devices[162].Update(nValue=Devices[162].nValue, sValue=Devices[162].sValue, Used=0)
			Devices[163].Update(nValue=Devices[163].nValue, sValue=Devices[163].sValue, Used=0)
			Devices[164].Update(nValue=Devices[164].nValue, sValue=Devices[164].sValue, Used=0)
			Devices[165].Update(nValue=Devices[165].nValue, sValue=Devices[165].sValue, Used=0)
			Devices[166].Update(nValue=Devices[166].nValue, sValue=Devices[166].sValue, Used=0)
			Devices[167].Update(nValue=Devices[167].nValue, sValue=Devices[167].sValue, Used=0)
			Devices[168].Update(nValue=Devices[168].nValue, sValue=Devices[168].sValue, Used=0)
			Devices[169].Update(nValue=Devices[169].nValue, sValue=Devices[169].sValue, Used=0)
			Devices[246].Update(nValue=Devices[246].nValue, sValue=Devices[246].sValue, Used=0)

		if self.Zone_TempSensors_8 and self.heating_colling:
			Devices[170].Update(nValue=Devices[170].nValue, sValue=Devices[170].sValue, Used=1)
			Devices[171].Update(nValue=Devices[171].nValue, sValue=Devices[171].sValue, Used=1)
			Devices[172].Update(nValue=Devices[172].nValue, sValue=Devices[172].sValue, Used=1)
			Devices[173].Update(nValue=Devices[173].nValue, sValue=Devices[173].sValue, Used=1)
			Devices[174].Update(nValue=Devices[174].nValue, sValue=Devices[174].sValue, Used=1)
			Devices[175].Update(nValue=Devices[175].nValue, sValue=Devices[175].sValue, Used=1)
			Devices[176].Update(nValue=Devices[176].nValue, sValue=Devices[176].sValue, Used=1)
			Devices[177].Update(nValue=Devices[177].nValue, sValue=Devices[177].sValue, Used=1)
			if self.zone_8_window:
				Devices[247].Update(nValue=Devices[247].nValue, sValue=Devices[247].sValue, Used=1)
				if ((Devices[1].Used == 1 and Devices[1].sValue != "0") or (Devices[22].Used == 1 and Devices[22].sValue != "0")) and Devices[210].sValue == "10" :
					self.addfavorite(Devices[247].ID)
				elif Devices[210].sValue == "10" :
					self.removefavorite(Devices[247].ID)
			else:
				Devices[247].Update(nValue=Devices[247].nValue, sValue=Devices[247].sValue, Used=0)
		else :
			Devices[170].Update(nValue=Devices[170].nValue, sValue=Devices[170].sValue, Used=0)
			Devices[171].Update(nValue=Devices[171].nValue, sValue=Devices[171].sValue, Used=0)
			Devices[172].Update(nValue=Devices[172].nValue, sValue=Devices[172].sValue, Used=0)
			Devices[173].Update(nValue=Devices[173].nValue, sValue=Devices[173].sValue, Used=0)
			Devices[174].Update(nValue=Devices[174].nValue, sValue=Devices[174].sValue, Used=0)
			Devices[175].Update(nValue=Devices[175].nValue, sValue=Devices[175].sValue, Used=0)
			Devices[176].Update(nValue=Devices[176].nValue, sValue=Devices[176].sValue, Used=0)
			Devices[177].Update(nValue=Devices[177].nValue, sValue=Devices[177].sValue, Used=0)
			Devices[247].Update(nValue=Devices[247].nValue, sValue=Devices[247].sValue, Used=0)

		if self.Zone_TempSensors_9 and self.heating_colling:
			Devices[178].Update(nValue=Devices[178].nValue, sValue=Devices[178].sValue, Used=1)
			Devices[179].Update(nValue=Devices[179].nValue, sValue=Devices[179].sValue, Used=1)
			Devices[180].Update(nValue=Devices[180].nValue, sValue=Devices[180].sValue, Used=1)
			Devices[181].Update(nValue=Devices[181].nValue, sValue=Devices[181].sValue, Used=1)
			Devices[182].Update(nValue=Devices[182].nValue, sValue=Devices[182].sValue, Used=1)
			Devices[183].Update(nValue=Devices[183].nValue, sValue=Devices[183].sValue, Used=1)
			Devices[184].Update(nValue=Devices[184].nValue, sValue=Devices[184].sValue, Used=1)
			Devices[185].Update(nValue=Devices[185].nValue, sValue=Devices[185].sValue, Used=1)
			if self.zone_9_window:
				Devices[248].Update(nValue=Devices[248].nValue, sValue=Devices[248].sValue, Used=1)
				if ((Devices[1].Used == 1 and Devices[1].sValue != "0") or (Devices[22].Used == 1 and Devices[22].sValue != "0")) and Devices[210].sValue == "10" :
					self.addfavorite(Devices[248].ID)
				elif Devices[210].sValue == "10" :
					self.removefavorite(Devices[248].ID)
			else:
				Devices[248].Update(nValue=Devices[248].nValue, sValue=Devices[248].sValue, Used=0)
		else :
			Devices[178].Update(nValue=Devices[178].nValue, sValue=Devices[178].sValue, Used=0)
			Devices[179].Update(nValue=Devices[179].nValue, sValue=Devices[179].sValue, Used=0)
			Devices[180].Update(nValue=Devices[180].nValue, sValue=Devices[180].sValue, Used=0)
			Devices[181].Update(nValue=Devices[181].nValue, sValue=Devices[181].sValue, Used=0)
			Devices[182].Update(nValue=Devices[182].nValue, sValue=Devices[182].sValue, Used=0)
			Devices[183].Update(nValue=Devices[183].nValue, sValue=Devices[183].sValue, Used=0)
			Devices[184].Update(nValue=Devices[184].nValue, sValue=Devices[184].sValue, Used=0)
			Devices[185].Update(nValue=Devices[185].nValue, sValue=Devices[185].sValue, Used=0)
			Devices[248].Update(nValue=Devices[248].nValue, sValue=Devices[248].sValue, Used=0)

		if self.Zone_TempSensors_10 and self.heating_colling:
			Devices[186].Update(nValue=Devices[186].nValue, sValue=Devices[186].sValue, Used=1)
			Devices[187].Update(nValue=Devices[187].nValue, sValue=Devices[187].sValue, Used=1)
			Devices[188].Update(nValue=Devices[188].nValue, sValue=Devices[188].sValue, Used=1)
			Devices[189].Update(nValue=Devices[189].nValue, sValue=Devices[189].sValue, Used=1)
			Devices[190].Update(nValue=Devices[190].nValue, sValue=Devices[190].sValue, Used=1)
			Devices[191].Update(nValue=Devices[191].nValue, sValue=Devices[191].sValue, Used=1)
			Devices[192].Update(nValue=Devices[192].nValue, sValue=Devices[192].sValue, Used=1)
			Devices[193].Update(nValue=Devices[193].nValue, sValue=Devices[193].sValue, Used=1)
			if self.zone_10_window:
				Devices[249].Update(nValue=Devices[249].nValue, sValue=Devices[249].sValue, Used=1)
				if ((Devices[1].Used == 1 and Devices[1].sValue != "0") or (Devices[22].Used == 1 and Devices[22].sValue != "0")) and Devices[210].sValue == "10" :
					self.addfavorite(Devices[249].ID)
				elif Devices[210].sValue == "10" :
					self.removefavorite(Devices[249].ID)
			else:
				Devices[249].Update(nValue=Devices[249].nValue, sValue=Devices[249].sValue, Used=0)
		else :
			Devices[186].Update(nValue=Devices[186].nValue, sValue=Devices[186].sValue, Used=0)
			Devices[187].Update(nValue=Devices[187].nValue, sValue=Devices[187].sValue, Used=0)
			Devices[188].Update(nValue=Devices[188].nValue, sValue=Devices[188].sValue, Used=0)
			Devices[189].Update(nValue=Devices[189].nValue, sValue=Devices[189].sValue, Used=0)
			Devices[190].Update(nValue=Devices[190].nValue, sValue=Devices[190].sValue, Used=0)
			Devices[191].Update(nValue=Devices[191].nValue, sValue=Devices[191].sValue, Used=0)
			Devices[192].Update(nValue=Devices[192].nValue, sValue=Devices[192].sValue, Used=0)
			Devices[193].Update(nValue=Devices[193].nValue, sValue=Devices[193].sValue, Used=0)
			Devices[249].Update(nValue=Devices[249].nValue, sValue=Devices[249].sValue, Used=0)

		if self.Zone_TempSensors_11 and self.heating_colling:
			Devices[194].Update(nValue=Devices[194].nValue, sValue=Devices[194].sValue, Used=1)
			Devices[195].Update(nValue=Devices[195].nValue, sValue=Devices[195].sValue, Used=1)
			Devices[196].Update(nValue=Devices[196].nValue, sValue=Devices[196].sValue, Used=1)
			Devices[198].Update(nValue=Devices[198].nValue, sValue=Devices[198].sValue, Used=1)
			Devices[199].Update(nValue=Devices[199].nValue, sValue=Devices[199].sValue, Used=1)
			Devices[200].Update(nValue=Devices[200].nValue, sValue=Devices[200].sValue, Used=1)
			Devices[201].Update(nValue=Devices[201].nValue, sValue=Devices[201].sValue, Used=1)
			if self.zone_11_window:
				Devices[250].Update(nValue=Devices[250].nValue, sValue=Devices[250].sValue, Used=1)
				if ((Devices[1].Used == 1 and Devices[1].sValue != "0") or (Devices[22].Used == 1 and Devices[22].sValue != "0")) and Devices[210].sValue == "10" :
					self.addfavorite(Devices[250].ID)
				elif Devices[210].sValue == "10" :
					self.removefavorite(Devices[250].ID)
			else:
				Devices[250].Update(nValue=Devices[250].nValue, sValue=Devices[250].sValue, Used=0)
		else :
			Devices[194].Update(nValue=Devices[194].nValue, sValue=Devices[194].sValue, Used=0)
			Devices[195].Update(nValue=Devices[195].nValue, sValue=Devices[195].sValue, Used=0)
			Devices[196].Update(nValue=Devices[196].nValue, sValue=Devices[196].sValue, Used=0)
			Devices[198].Update(nValue=Devices[198].nValue, sValue=Devices[198].sValue, Used=0)
			Devices[199].Update(nValue=Devices[199].nValue, sValue=Devices[199].sValue, Used=0)
			Devices[200].Update(nValue=Devices[200].nValue, sValue=Devices[200].sValue, Used=0)
			Devices[201].Update(nValue=Devices[201].nValue, sValue=Devices[201].sValue, Used=0)
			Devices[250].Update(nValue=Devices[250].nValue, sValue=Devices[250].sValue, Used=0)

		if self.Zone_TempSensors_12 and self.heating_colling:
			Devices[202].Update(nValue=Devices[202].nValue, sValue=Devices[202].sValue, Used=1)
			Devices[203].Update(nValue=Devices[203].nValue, sValue=Devices[203].sValue, Used=1)
			Devices[204].Update(nValue=Devices[204].nValue, sValue=Devices[204].sValue, Used=1)
			Devices[205].Update(nValue=Devices[205].nValue, sValue=Devices[205].sValue, Used=1)
			Devices[206].Update(nValue=Devices[206].nValue, sValue=Devices[206].sValue, Used=1)
			Devices[207].Update(nValue=Devices[207].nValue, sValue=Devices[207].sValue, Used=1)
			Devices[208].Update(nValue=Devices[208].nValue, sValue=Devices[208].sValue, Used=1)
			Devices[209].Update(nValue=Devices[209].nValue, sValue=Devices[209].sValue, Used=1)
			if self.zone_12_window:
				Devices[251].Update(nValue=Devices[251].nValue, sValue=Devices[251].sValue, Used=1)
				if ((Devices[1].Used == 1 and Devices[1].sValue != "0") or (Devices[22].Used == 1 and Devices[22].sValue != "0")) and Devices[210].sValue == "10" :
					self.addfavorite(Devices[251].ID)
				elif Devices[210].sValue == "10" :
					self.removefavorite(Devices[251].ID)
			else:
				Devices[251].Update(nValue=Devices[251].nValue, sValue=Devices[251].sValue, Used=0)
		else :
			Devices[202].Update(nValue=Devices[202].nValue, sValue=Devices[202].sValue, Used=0)
			Devices[203].Update(nValue=Devices[203].nValue, sValue=Devices[203].sValue, Used=0)
			Devices[204].Update(nValue=Devices[204].nValue, sValue=Devices[204].sValue, Used=0)
			Devices[205].Update(nValue=Devices[205].nValue, sValue=Devices[205].sValue, Used=0)
			Devices[206].Update(nValue=Devices[206].nValue, sValue=Devices[206].sValue, Used=0)
			Devices[207].Update(nValue=Devices[207].nValue, sValue=Devices[207].sValue, Used=0)
			Devices[208].Update(nValue=Devices[208].nValue, sValue=Devices[208].sValue, Used=0)
			Devices[209].Update(nValue=Devices[209].nValue, sValue=Devices[209].sValue, Used=0)
			Devices[251].Update(nValue=Devices[251].nValue, sValue=Devices[251].sValue, Used=0)

		if self.Kevero_1_TempSensor and self.heating_colling:
			Devices[61].Update(nValue=Devices[61].nValue, sValue=Devices[61].sValue, Used=1)
			Devices[59].Update(nValue=Devices[59].nValue, sValue=Devices[59].sValue, Used=1)
			Devices[70].Update(nValue=Devices[70].nValue, sValue=Devices[70].sValue, Used=1)
			Devices[72].Update(nValue=Devices[72].nValue, sValue=Devices[72].sValue, Used=1)
			Devices[63].Update(nValue=Devices[63].nValue, sValue=Devices[63].sValue, Used=1)
			Devices[119].Update(nValue=Devices[119].nValue, sValue=Devices[119].sValue, Used=1)
			Devices[121].Update(nValue=Devices[121].nValue, sValue=Devices[121].sValue, Used=1)
			Devices[152].Update(nValue=Devices[152].nValue, sValue=Devices[152].sValue, Used=1)
			Devices[153].Update(nValue=Devices[153].nValue, sValue=Devices[153].sValue, Used=1)
		else :
			Devices[61].Update(nValue=Devices[61].nValue, sValue=Devices[61].sValue, Used=0)
			Devices[59].Update(nValue=Devices[59].nValue, sValue=Devices[59].sValue, Used=0)
			Devices[70].Update(nValue=Devices[70].nValue, sValue=Devices[70].sValue, Used=0)
			Devices[72].Update(nValue=Devices[72].nValue, sValue=Devices[72].sValue, Used=0)
			Devices[63].Update(nValue=Devices[63].nValue, sValue=Devices[63].sValue, Used=0)
			Devices[119].Update(nValue=Devices[119].nValue, sValue=Devices[119].sValue, Used=0)
			Devices[121].Update(nValue=Devices[121].nValue, sValue=Devices[121].sValue, Used=0)
			Devices[152].Update(nValue=Devices[152].nValue, sValue=Devices[152].sValue, Used=0)
			Devices[153].Update(nValue=Devices[153].nValue, sValue=Devices[153].sValue, Used=0)

		if self.Kevero_2_TempSensor and self.heating_colling:
			Devices[62].Update(nValue=Devices[62].nValue, sValue=Devices[62].sValue, Used=1)
			Devices[60].Update(nValue=Devices[60].nValue, sValue=Devices[60].sValue, Used=1)
			Devices[71].Update(nValue=Devices[71].nValue, sValue=Devices[71].sValue, Used=1)
			Devices[73].Update(nValue=Devices[73].nValue, sValue=Devices[73].sValue, Used=1)
			Devices[75].Update(nValue=Devices[75].nValue, sValue=Devices[75].sValue, Used=1)
			Devices[120].Update(nValue=Devices[120].nValue, sValue=Devices[120].sValue, Used=1)
			Devices[122].Update(nValue=Devices[122].nValue, sValue=Devices[122].sValue, Used=1)
		else :
			Devices[62].Update(nValue=Devices[62].nValue, sValue=Devices[62].sValue, Used=0)
			Devices[60].Update(nValue=Devices[60].nValue, sValue=Devices[60].sValue, Used=0)
			Devices[71].Update(nValue=Devices[71].nValue, sValue=Devices[71].sValue, Used=0)
			Devices[73].Update(nValue=Devices[73].nValue, sValue=Devices[73].sValue, Used=0)
			Devices[75].Update(nValue=Devices[75].nValue, sValue=Devices[75].sValue, Used=0)
			Devices[120].Update(nValue=Devices[120].nValue, sValue=Devices[120].sValue, Used=0)
			Devices[122].Update(nValue=Devices[122].nValue, sValue=Devices[122].sValue, Used=0)

		if self.FrostTempSensors :
			Devices[89].Update(nValue=Devices[89].nValue, sValue=Devices[89].sValue, Used=1)
			Devices[156].Update(nValue=Devices[156].nValue, sValue=Devices[156].sValue, Used=1)
		else :
			Devices[89].Update(nValue=Devices[89].nValue, sValue=Devices[89].sValue, Used=0)
			Devices[156].Update(nValue=Devices[156].nValue, sValue=Devices[156].sValue, Used=0)
			
		
		if Devices[78].sValue == "0" :
			self.solar_dhw_limit = 0
		elif Devices[78].sValue == "10" :
			self.solar_dhw_limit = 500
		elif Devices[78].sValue == "20" :
			self.solar_dhw_limit = 1000
		elif Devices[78].sValue == "30" :
			self.solar_dhw_limit = 2000
		elif Devices[78].sValue == "40" :
			self.solar_dhw_limit = 3000
		elif Devices[78].sValue == "50" :
			self.solar_dhw_limit = 4000
		elif Devices[78].sValue == "60" :
			self.solar_dhw_limit = 5000

		if Devices[112].sValue == "10" :
			self.HF_dif_felements = 1
		elif Devices[112].sValue == "20" :
			self.HF_dif_felements = 2
		elif Devices[112].sValue == "30" :
			self.HF_dif_felements = 3
		elif Devices[112].sValue == "40" :
			self.HF_dif_felements = 4
		elif Devices[112].sValue == "50" :
			self.HF_dif_felements = 5

		if Devices[114].sValue == "10" :
			self.P_dif_felements = 1
		elif Devices[114].sValue == "20" :
			self.P_dif_felements = 2
		elif Devices[114].sValue == "30" :
			self.P_dif_felements = 3
		elif Devices[114].sValue == "40" :
			self.P_dif_felements = 4
		elif Devices[114].sValue == "50" :
			self.P_dif_felements = 5
		elif Devices[114].sValue == "60" :
			self.P_dif_felements = 6
		elif Devices[114].sValue == "70" :
			self.P_dif_felements = 7
		elif Devices[114].sValue == "80" :
			self.P_dif_felements = 8
		elif Devices[114].sValue == "90" :
			self.P_dif_felements = 9
		elif Devices[114].sValue == "100" :
			self.P_dif_felements = 10

		if Devices[113].sValue == "10" :
			self.dhw_dif_felements = 1
		elif Devices[113].sValue == "20" :
			self.dhw_dif_felements = 2
		elif Devices[113].sValue == "30" :
			self.dhw_dif_felements = 3
		elif Devices[113].sValue == "40" :
			self.dhw_dif_felements = 4
		elif Devices[113].sValue == "50" :
			self.dhw_dif_felements = 5
		elif Devices[113].sValue == "60" :
			self.dhw_dif_felements = 6
		elif Devices[113].sValue == "70" :
			self.dhw_dif_felements = 7
		elif Devices[113].sValue == "80" :
			self.dhw_dif_felements = 8
		elif Devices[113].sValue == "90" :
			self.dhw_dif_felements = 9
		elif Devices[113].sValue == "100" :
			self.dhw_dif_felements = 10


		if self.setVarDhwTimer :
			if self.device_dhw_max_time > 0 :
				self.Internals['switchTimer_dhw'] = datetime.now() + timedelta(minutes=self.device_dhw_max_time)
			else :
				self.Internals['switchTimer_dhw'] = 0

		if Devices[83].sValue == "0" :
			self.dhw_external_limit = None
			self.dhw_external_time_limit = None
		elif Devices[83].sValue == "10" :
			self.dhw_external_limit = float(-5)
			self.dhw_external_time_limit = None
		elif Devices[83].sValue == "20" :
			self.dhw_external_limit = 0
			self.dhw_external_time_limit = None
		elif Devices[83].sValue == "30" :
			self.dhw_external_limit = float(7)
			self.dhw_external_time_limit = None
		elif Devices[83].sValue == "40" :
			self.dhw_external_limit = float(15)
			self.dhw_external_time_limit = None
		elif Devices[83].sValue == "50" :
			self.dhw_external_limit = float(20)
			self.dhw_external_time_limit = None
		elif Devices[83].sValue == "60" :
			self.dhw_external_time_limit = 6
			self.dhw_external_limit = None
		elif Devices[83].sValue == "70" :
			self.dhw_external_time_limit = 8
			self.dhw_external_limit = None
		elif Devices[83].sValue == "80" :
			self.dhw_external_time_limit = 12
			self.dhw_external_limit = None
			
		if Devices[98].sValue == "0" :
			self.solar_puffer_limit = 0
		elif Devices[98].sValue == "10" :
			self.solar_puffer_limit = 500
		elif Devices[98].sValue == "20" :
			self.solar_puffer_limit = 1000
		elif Devices[98].sValue == "30" :
			self.solar_puffer_limit = 2000
		elif Devices[98].sValue == "40" :
			self.solar_puffer_limit = 3000
		elif Devices[98].sValue == "50" :
			self.solar_puffer_limit = 4000
		elif Devices[98].sValue == "60" :
			self.solar_puffer_limit = 5000

		if  Devices[58].sValue == "10" :
			self.buffer_external_H_limit = None
			self.buffer_external_time_H_limit = None

			if Devices[84].sValue == "0" :
				self.buffer_external_F_limit = None
				self.buffer_external_time_F_limit = None
			elif Devices[84].sValue == "10" :
				self.buffer_external_F_limit = float(-5)
				self.buffer_external_time_F_limit = None
			elif Devices[84].sValue == "20" :
				self.buffer_external_F_limit = 0
				self.buffer_external_time_F_limit = None
			elif Devices[84].sValue == "30" :
				self.buffer_external_F_limit = float(7)
				self.buffer_external_time_F_limit = None
			elif Devices[84].sValue == "40" :
				self.buffer_external_F_limit = float(15)
				self.buffer_external_time_F_limit = None
			elif Devices[84].sValue == "50" :
				self.buffer_external_F_limit = float(20)
				self.buffer_external_time_F_limit = None
			elif Devices[84].sValue == "60" :
				self.buffer_external_time_F_limit = 6
				self.buffer_external_F_limit = None
			elif Devices[84].sValue == "70" :
				self.buffer_external_time_F_limit = 8
				self.buffer_external_F_limit = None
			elif Devices[84].sValue == "80" :
				self.buffer_external_time_F_limit = 12
				self.buffer_external_F_limit = None

		else :
			self.buffer_external_F_limit = None
			self.buffer_external_time_F_limit = None

			if Devices[99].sValue == "0" :
				self.buffer_external_H_limit = None
				self.buffer_external_time_H_limit = None
			elif Devices[99].sValue == "10" :
				self.buffer_external_H_limit = float(-5)
				self.buffer_external_time_H_limit = None
			elif Devices[99].sValue == "20" :
				self.buffer_external_H_limit = 0
				self.buffer_external_time_H_limit = None
			elif Devices[99].sValue == "30" :
				self.buffer_external_H_limit = float(7)
				self.buffer_external_time_H_limit = None
			elif Devices[99].sValue == "40" :
				self.buffer_external_H_limit = float(15)
				self.buffer_external_time_H_limit = None
			elif Devices[99].sValue == "50" :
				self.buffer_external_H_limit = float(20)
				self.buffer_external_time_H_limit = None
			elif Devices[99].sValue == "60" :
				self.buffer_external_time_H_limit = 6
				self.buffer_external_H_limit = None
			elif Devices[99].sValue == "70" :
				self.buffer_external_time_H_limit = 8
				self.buffer_external_H_limit = None
			elif Devices[99].sValue == "80" :
				self.buffer_external_time_H_limit = 12
				self.buffer_external_H_limit = None

		self.dhw_ValtasTemp = float(Devices[16].sValue)

		self.PufferValtasTemp = float(Devices[108].sValue)

		self.Kevero_1_hiszterezis = float(Devices[61].sValue)

		self.Kevero_2_hiszterezis = float(Devices[62].sValue)

		self.Kevero_1_harmatkorr = float(Devices[63].sValue)

		self.Kevero_2_harmatkorr = float(Devices[75].sValue)

		self.F_hiszterezis = float(Devices[64].sValue)

		self.H_hiszterezis = float(Devices[216].sValue)

		self.automatic_range = float(Devices[155].sValue)

		self.diffszoba = float(Devices[67].sValue)

		if Devices[74].sValue == "0" :
			self.ido = 0
		elif Devices[74].sValue == "10" :
			self.ido = 1
		elif Devices[74].sValue == "20" :
			self.ido = 2
		elif Devices[74].sValue == "30" :
			self.ido = 3
		elif Devices[74].sValue == "40" :
			self.ido = 4
		elif Devices[74].sValue == "50" :
			self.ido = 5
		elif Devices[74].sValue == "60" :
			self.ido = 6

		if Devices[65].sValue == "0" :
			self.dhwprior_F_H = False
			self.dhwprior_P = False
			self.device_dhw_max_time = 0
		elif Devices[65].sValue == "10" :
			self.dhwprior_F_H = True
			self.dhwprior_P = False
			self.device_dhw_max_time = 0
		elif Devices[65].sValue == "20" :
			self.dhwprior_F_H = True
			self.dhwprior_P = False
			self.device_dhw_max_time = 30
		elif Devices[65].sValue == "30" :
			self.dhwprior_F_H = True
			self.dhwprior_P = False
			self.device_dhw_max_time = 60
		elif Devices[65].sValue == "40" :
			self.dhwprior_F_H = True
			self.dhwprior_P = False
			self.device_dhw_max_time = 120
		elif Devices[65].sValue == "50" :
			self.dhwprior_F_H = True
			self.dhwprior_P = False
			self.device_dhw_max_time = 180
		elif Devices[65].sValue == "60" :
			self.dhwprior_F_H = False
			self.dhwprior_P = True
			self.device_dhw_max_time = 0
		elif Devices[65].sValue == "70" :
			self.dhwprior_F_H = False
			self.dhwprior_P = True
			self.device_dhw_max_time = 30
		elif Devices[65].sValue == "80" :
			self.dhwprior_F_H = False
			self.dhwprior_P = True
			self.device_dhw_max_time = 60
		elif Devices[65].sValue == "90" :
			self.dhwprior_F_H = False
			self.dhwprior_P = True
			self.device_dhw_max_time = 120
		elif Devices[65].sValue == "100" :
			self.dhwprior_F_H = False
			self.dhwprior_P = True
			self.device_dhw_max_time = 180
		elif Devices[65].sValue == "110" :
			self.dhwprior_F_H = True
			self.dhwprior_P = True
			self.device_dhw_max_time = 0
		elif Devices[65].sValue == "120" :
			self.dhwprior_F_H = True
			self.dhwprior_P = True
			self.device_dhw_max_time = 30
		elif Devices[65].sValue == "130" :
			self.dhwprior_F_H = True
			self.dhwprior_P = True
			self.device_dhw_max_time = 60
		elif Devices[65].sValue == "140" :
			self.dhwprior_F_H = True
			self.dhwprior_P = True
			self.device_dhw_max_time = 120
		elif Devices[65].sValue == "150" :
			self.dhwprior_F_H = True
			self.dhwprior_P = True
			self.device_dhw_max_time = 180

		if Devices[212].sValue == "0" :
			self.ir_resend = 0
		elif Devices[212].sValue == "10" :
			self.ir_resend = 1
		elif Devices[212].sValue == "20" :
			self.ir_resend = 2
		elif Devices[212].sValue == "30" :
			self.ir_resend = 3
		elif Devices[212].sValue == "40" :
			self.ir_resend = 4
		elif Devices[212].sValue == "50" :
			self.ir_resend = 5
		elif Devices[212].sValue == "60" :
			self.ir_resend = 10

		if Devices[218].sValue == "10" :
			self.before_switch_1_time = 60
		elif Devices[218].sValue == "20" :
			self.before_switch_1_time = 120
		elif Devices[218].sValue == "30" :
			self.before_switch_1_time = 180
		elif Devices[218].sValue == "40" :
			self.before_switch_1_time = 240
		elif Devices[218].sValue == "50" :
			self.before_switch_1_time = 300
		elif Devices[218].sValue == "60" :
			self.before_switch_1_time = 600
		elif Devices[218].sValue == "70" :
			self.before_switch_1_time = 900
		elif Devices[218].sValue == "80" :
			self.before_switch_1_time = 1800
		elif Devices[218].sValue == "90" :
			self.before_switch_1_time = 3600
		elif Devices[218].sValue == "100" :
			self.before_switch_1_time = 7200
		elif Devices[218].sValue == "110" :
			self.before_switch_1_time = 14400
		elif Devices[218].sValue == "120" :
			self.before_switch_1_time = 28800
		elif Devices[218].sValue == "130" :
			self.before_switch_1_time = 43200
		elif Devices[218].sValue == "140" :
			self.before_switch_1_time = 86400
		elif Devices[218].sValue == "150" :
			self.before_switch_1_time = 172800

		if Devices[220].sValue == "10" :
			self.before_switch_2_time = 60
		elif Devices[220].sValue == "20" :
			self.before_switch_2_time = 120
		elif Devices[220].sValue == "30" :
			self.before_switch_2_time = 180
		elif Devices[220].sValue == "40" :
			self.before_switch_2_time = 240
		elif Devices[220].sValue == "50" :
			self.before_switch_2_time = 300
		elif Devices[220].sValue == "60" :
			self.before_switch_2_time = 600
		elif Devices[220].sValue == "70" :
			self.before_switch_2_time = 900
		elif Devices[220].sValue == "80" :
			self.before_switch_2_time = 1800
		elif Devices[220].sValue == "90" :
			self.before_switch_2_time = 3600
		elif Devices[220].sValue == "100" :
			self.before_switch_2_time = 7200
		elif Devices[220].sValue == "110" :
			self.before_switch_2_time = 14400
		elif Devices[220].sValue == "120" :
			self.before_switch_2_time = 28800
		elif Devices[220].sValue == "130" :
			self.before_switch_2_time = 43200
		elif Devices[220].sValue == "140" :
			self.before_switch_2_time = 86400
		elif Devices[220].sValue == "150" :
			self.before_switch_2_time = 172800

		if Devices[219].sValue == "10" :
			self.after_switch_1_time = 60
		elif Devices[219].sValue == "20" :
			self.after_switch_1_time = 120
		elif Devices[219].sValue == "30" :
			self.after_switch_1_time = 180
		elif Devices[219].sValue == "40" :
			self.after_switch_1_time = 240
		elif Devices[219].sValue == "50" :
			self.after_switch_1_time = 300
		elif Devices[219].sValue == "60" :
			self.after_switch_1_time = 600
		elif Devices[219].sValue == "70" :
			self.after_switch_1_time = 900
		elif Devices[219].sValue == "80" :
			self.after_switch_1_time = 1800
		elif Devices[219].sValue == "90" :
			self.after_switch_1_time = 3600
		elif Devices[219].sValue == "100" :
			self.after_switch_1_time = 7200
		elif Devices[219].sValue == "110" :
			self.after_switch_1_time = 14400
		elif Devices[219].sValue == "120" :
			self.after_switch_1_time = 28800
		elif Devices[219].sValue == "130" :
			self.after_switch_1_time = 43200
		elif Devices[219].sValue == "140" :
			self.after_switch_1_time = 86400
		elif Devices[219].sValue == "150" :
			self.after_switch_1_time = 172800

		if Devices[232].sValue == "10" :
			self.after_switch_2_time = 60
		elif Devices[232].sValue == "20" :
			self.after_switch_2_time = 120
		elif Devices[232].sValue == "30" :
			self.after_switch_2_time = 180
		elif Devices[232].sValue == "40" :
			self.after_switch_2_time = 240
		elif Devices[232].sValue == "50" :
			self.after_switch_2_time = 300
		elif Devices[232].sValue == "60" :
			self.after_switch_2_time = 600
		elif Devices[232].sValue == "70" :
			self.after_switch_2_time = 900
		elif Devices[232].sValue == "80" :
			self.after_switch_2_time = 1800
		elif Devices[232].sValue == "90" :
			self.after_switch_2_time = 3600
		elif Devices[232].sValue == "100" :
			self.after_switch_2_time = 7200
		elif Devices[232].sValue == "110" :
			self.after_switch_2_time = 14400
		elif Devices[232].sValue == "120" :
			self.after_switch_2_time = 28800
		elif Devices[232].sValue == "130" :
			self.after_switch_2_time = 43200
		elif Devices[232].sValue == "140" :
			self.after_switch_2_time = 86400
		elif Devices[219].sValue == "150" :
			self.after_switch_2_time = 172800

		# Switch everything off at startup to prevent valves from remaining active during mode changes. | Induláskor minden kimenetet kikapcsolunk, hogy üzemmódváltáskor ne maradjon aktív szelepnk.

		for idx in self.Zone_1_F:
			self.switchappend(idx,"Off")

		for idx in self.Zone_1_H:
			self.switchappend(idx,"Off")

		for idx in self.Zone_1_F:
			self.switchappend(idx,"Off")

		for idx in self.Zone_1_H:
			self.switchappend(idx,"Off")

		for idx in self.Zone_2_F:
			self.switchappend(idx,"Off")

		for idx in self.Zone_2_H:
			self.switchappend(idx,"Off")

		for idx in self.Zone_2_F:
			self.switchappend(idx,"Off")

		for idx in self.Zone_2_H:
			self.switchappend(idx,"Off")

		for idx in self.Zone_3_F:
			self.switchappend(idx,"Off")

		for idx in self.Zone_3_H:
			self.switchappend(idx,"Off")

		for idx in self.Zone_3_F:
			self.switchappend(idx,"Off")

		for idx in self.Zone_3_H:
			self.switchappend(idx,"Off")

		for idx in self.Zone_4_F:
			self.switchappend(idx,"Off")

		for idx in self.Zone_4_H:
			self.switchappend(idx,"Off")

		for idx in self.Zone_4_F:
			self.switchappend(idx,"Off")

		for idx in self.Zone_4_H:
			self.switchappend(idx,"Off")

		for idx in self.Zone_5_F:
			self.switchappend(idx,"Off")

		for idx in self.Zone_5_H:
			self.switchappend(idx,"Off")

		for idx in self.Zone_5_F:
			self.switchappend(idx,"Off")

		for idx in self.Zone_5_H:
			self.switchappend(idx,"Off")

		for idx in self.Zone_6_F:
			self.switchappend(idx,"Off")

		for idx in self.Zone_6_H:
			self.switchappend(idx,"Off")

		for idx in self.Zone_6_F:
			self.switchappend(idx,"Off")

		for idx in self.Zone_6_H:
			self.switchappend(idx,"Off")

		for idx in self.Zone_7_F:
			self.switchappend(idx,"Off")

		for idx in self.Zone_7_H:
			self.switchappend(idx,"Off")

		for idx in self.Zone_7_F:
			self.switchappend(idx,"Off")

		for idx in self.Zone_7_H:
			self.switchappend(idx,"Off")

		for idx in self.Zone_8_F:
			self.switchappend(idx,"Off")

		for idx in self.Zone_8_H:
			self.switchappend(idx,"Off")

		for idx in self.Zone_8_F:
			self.switchappend(idx,"Off")

		for idx in self.Zone_8_H:
			self.switchappend(idx,"Off")

		for idx in self.Zone_9_F:
			self.switchappend(idx,"Off")

		for idx in self.Zone_9_H:
			self.switchappend(idx,"Off")

		for idx in self.Zone_9_F:
			self.switchappend(idx,"Off")

		for idx in self.Zone_9_H:
			self.switchappend(idx,"Off")

		for idx in self.Zone_10_F:
			self.switchappend(idx,"Off")

		for idx in self.Zone_10_H:
			self.switchappend(idx,"Off")

		for idx in self.Zone_10_F:
			self.switchappend(idx,"Off")

		for idx in self.Zone_10_H:
			self.switchappend(idx,"Off")

		for idx in self.Zone_11_F:
			self.switchappend(idx,"Off")

		for idx in self.Zone_11_H:
			self.switchappend(idx,"Off")

		for idx in self.Zone_11_F:
			self.switchappend(idx,"Off")

		for idx in self.Zone_11_H:
			self.switchappend(idx,"Off")

		for idx in self.Zone_12_F:
			self.switchappend(idx,"Off")

		for idx in self.Zone_12_H:
			self.switchappend(idx,"Off")

		for idx in self.Zone_12_F:
			self.switchappend(idx,"Off")

		for idx in self.Zone_12_H:
			self.switchappend(idx,"Off")

# Show heating on the dashboard | Fűtés megjelenítése a kezdőlapon

		if (Devices[1].Used == 1 and Devices[1].sValue != "0") and Devices[210].sValue != "0" :  # Dashboard enabled and heating/cooling enabled | Kezdőlapi megjelenítés és fűtés–hűtés bekapcsolva

			Domoticz.Debug("Home screen ON, heating ON: add favorites | Kezdőlapon bekapcsolva, fűtés bekapcsolva: kedvencek hozzáadása")


			self.addfavorite(Devices[64].ID)
			self.removefavorite(Devices[216].ID)

			self.Zone_F_V = [[] for _ in range(12)]

			self.Zone_F_V = [self.Zone_1_F_V, self.Zone_2_F_V, self.Zone_3_F_V, self.Zone_4_F_V, self.Zone_5_F_V, self.Zone_6_F_V, self.Zone_7_F_V, self.Zone_8_F_V, self.Zone_9_F_V, self.Zone_10_F_V, self.Zone_11_F_V, self.Zone_12_F_V,]

			if any(self.Zone_F_V):
				self.addfavorite(Devices[86].ID)
			else:
				self.removefavorite(Devices[86].ID)

			self.addfavorite(Devices[74].ID)
			
			if Devices[12].sValue == "20":
				self.addfavorite(Devices[238].ID)
			else:
				self.removefavorite(Devices[238].ID)

			if Devices[29].sValue == "20":
				self.addfavorite(Devices[239].ID)
			else:
				self.removefavorite(Devices[239].ID)


			if Devices[78].sValue != "0":
				self.addfavorite(Devices[233].ID)
			else:
				self.removefavorite(Devices[233].ID)

			if Devices[83].sValue != "0":
				self.addfavorite(Devices[234].ID)
			else:
				self.removefavorite(Devices[234].ID)

			if Devices[84].sValue != "0":
				self.addfavorite(Devices[236].ID)
			else:
				self.removefavorite(Devices[236].ID)

			if Devices[98].sValue != "0":
				self.addfavorite(Devices[235].ID)
			else:
				self.removefavorite(Devices[235].ID)

			if Devices[99].sValue != "0":
				self.addfavorite(Devices[237].ID)
			else:
				self.removefavorite(Devices[237].ID)

			if Devices[125].sValue != "0":
				self.addfavorite(Devices[230].ID)
			else:
				self.removefavorite(Devices[230].ID)

			if Devices[1].sValue == "10" or Devices[1].sValue == "20" :  # Device 1 and device 2 | 1. eszköz és 2. eszköz
				self.removefavorite(Devices[3].ID)
				self.removefavorite(Devices[7].ID)
				self.removefavorite(Devices[18].ID)
				self.removefavorite(Devices[85].ID)
				self.removefavorite(Devices[221].ID)
				self.removefavorite(Devices[225].ID)
			elif Devices[1].sValue == "30" : # Switching mode based on indoor temperature | Váltó mód belső hőmérséklet alapján
				self.addfavorite(Devices[3].ID)
				self.removefavorite(Devices[7].ID)
				self.removefavorite(Devices[18].ID)
				self.removefavorite(Devices[85].ID)
				self.removefavorite(Devices[221].ID)
				self.removefavorite(Devices[225].ID)
			elif Devices[1].sValue == "40" : # Switching mode based on outdoor temperature | Váltó üzemmód külső hőmérséklet alapján
				self.addfavorite(Devices[7].ID)
				self.addfavorite(Devices[225].ID)
				self.removefavorite(Devices[3].ID)
				self.removefavorite(Devices[85].ID)
				self.addfavorite(Devices[18].ID)
				self.removefavorite(Devices[221].ID)
			elif Devices[1].sValue == "50" : # Switching mode based on outdoor dew point | Váltó mód külső harmatpont alapján
				self.addfavorite(Devices[18].ID)
				self.addfavorite(Devices[221].ID)
				self.removefavorite(Devices[3].ID)
				self.removefavorite(Devices[7].ID)
				self.removefavorite(Devices[85].ID)
				self.removefavorite(Devices[225].ID)
			elif Devices[1].sValue == "60" : # Dual mode based on indoor temperature | Dual mód belső hőmérséklet alapján
				self.addfavorite(Devices[3].ID)
				self.removefavorite(Devices[7].ID)
				self.removefavorite(Devices[18].ID)
				self.removefavorite(Devices[221].ID)
				self.removefavorite(Devices[85].ID)
				self.removefavorite(Devices[225].ID)
			elif Devices[1].sValue == "70" : # Dual mode based on outdoor temperature | Dual üzemmód külső hőmérséklet alapján
				self.addfavorite(Devices[7].ID)
				self.addfavorite(Devices[18].ID)
				self.addfavorite(Devices[225].ID)
				self.removefavorite(Devices[3].ID)
				self.removefavorite(Devices[85].ID)
				self.removefavorite(Devices[221].ID)
			elif Devices[1].sValue == "80" : # Dual mode based on outdoor dew point | Dual mód külső harmatpont alapján
				self.addfavorite(Devices[18].ID)
				self.addfavorite(Devices[221].ID)
				self.removefavorite(Devices[3].ID)
				self.removefavorite(Devices[7].ID)
				self.removefavorite(Devices[85].ID)
				self.removefavorite(Devices[225].ID)
			elif Devices[1].sValue == "90" : # Saver mode based on indoor and outdoor temperatures | Saver mód belső hőmérséklet és külsőhőmérséklet alapján
				self.addfavorite(Devices[3].ID)
				self.addfavorite(Devices[7].ID)
				self.addfavorite(Devices[18].ID)
				self.addfavorite(Devices[225].ID)
				self.removefavorite(Devices[85].ID)
				self.removefavorite(Devices[221].ID)
			elif Devices[1].sValue == "100" : # Saver mode based on indoor temperature and outdoor dew point | Saver mód belső hőmérséklet és külső harmatpont alapján
				self.addfavorite(Devices[3].ID)
				self.addfavorite(Devices[7].ID)
				self.addfavorite(Devices[18].ID)
				self.addfavorite(Devices[221].ID)
				self.removefavorite(Devices[85].ID)
				self.addfavorite(Devices[225].ID)
				self.removefavorite(Devices[225].ID)
			elif 110 <= int(Devices[1].sValue):  # Electrical limit | Elektromos teljesítménykorlát
				self.addfavorite(Devices[85].ID)
				self.removefavorite(Devices[3].ID)
				self.removefavorite(Devices[7].ID)
				self.removefavorite(Devices[18].ID)
				self.removefavorite(Devices[221].ID)
				self.removefavorite(Devices[225].ID)

# Show cooling on the dashboard | Hűtés megjelenítése a kezdőlapon

		if (Devices[22].Used == 1 and Devices[22].sValue != "0") and Devices[210].sValue != "0" :  # Dashboard enabled and cooling enabled | Kezdőlapi megjelenítés és hűtés bekapcsolva

			Domoticz.Debug("Home screen ON, cooling ON: add favorites | Kezdőlapon bekapcsolva, hűtés bekapcsolva: kedvencek hozzáadása")

			self.removefavorite(Devices[64].ID)
			self.addfavorite(Devices[216].ID)

			self.Zone_H_V = [self.Zone_1_H_V, self.Zone_2_H_V, self.Zone_3_H_V, self.Zone_4_H_V, self.Zone_5_H_V, self.Zone_6_H_V, self.Zone_7_H_V, self.Zone_8_H_V, self.Zone_9_H_V, self.Zone_10_H_V, self.Zone_11_H_V, self.Zone_12_H_V,]

			if any(self.Zone_H_V):
				self.addfavorite(Devices[86].ID)
			else:
				self.removefavorite(Devices[86].ID)

			self.addfavorite(Devices[74].ID)
			
			if Devices[12].sValue == "20":
				self.addfavorite(Devices[238].ID)
			else:
				self.removefavorite(Devices[238].ID)

			if Devices[29].sValue == "20":
				self.addfavorite(Devices[239].ID)
			else:
				self.removefavorite(Devices[239].ID)


			if Devices[78].sValue != "0":
				self.addfavorite(Devices[233].ID)
			else:
				self.removefavorite(Devices[233].ID)

			if Devices[83].sValue != "0":
				self.addfavorite(Devices[234].ID)
			else:
				self.removefavorite(Devices[234].ID)

			if Devices[84].sValue != "0":
				self.addfavorite(Devices[236].ID)
			else:
				self.removefavorite(Devices[236].ID)

			if Devices[98].sValue != "0":
				self.addfavorite(Devices[235].ID)
			else:
				self.removefavorite(Devices[235].ID)

			if Devices[99].sValue != "0":
				self.addfavorite(Devices[237].ID)
			else:
				self.removefavorite(Devices[237].ID)

			if Devices[125].sValue != "0":
				self.addfavorite(Devices[230].ID)
			else:
				self.removefavorite(Devices[230].ID)

			if Devices[22].sValue == "10" or Devices[22].sValue == "20" :  # Device 1 and device 2 | 1. eszköz és 2. eszköz
				self.addfavorite(Devices[216].ID)
				self.removefavorite(Devices[85].ID)
				self.removefavorite(Devices[252].ID)
			elif Devices[22].sValue == "30" : # Switching mode based on indoor temperature | Váltó mód belső hőmérséklet alapján
				self.addfavorite(Devices[3].ID)
				self.removefavorite(Devices[252].ID)
				self.removefavorite(Devices[18].ID)
				self.removefavorite(Devices[85].ID)
				self.removefavorite(Devices[221].ID)
				self.removefavorite(Devices[225].ID)
			elif Devices[22].sValue == "40" : # Switching mode based on outdoor temperature | Váltó üzemmód külső hőmérséklet alapján
				self.addfavorite(Devices[18].ID)
				self.addfavorite(Devices[252].ID)
				self.addfavorite(Devices[225].ID)
				self.removefavorite(Devices[3].ID)
				self.removefavorite(Devices[85].ID)
				self.removefavorite(Devices[221].ID)
			elif Devices[22].sValue == "50" : # Dual mode based on indoor temperature | Dual mód belső hőmérséklet alapján
				self.addfavorite(Devices[3].ID)
				self.addfavorite(Devices[18].ID)
				self.addfavorite(Devices[221].ID)
				self.removefavorite(Devices[252].ID)
				self.removefavorite(Devices[85].ID)
				self.removefavorite(Devices[225].ID)
			elif Devices[22].sValue == "60" : # Dual mode based on outdoor temperature | Dual üzemmód külső hőmérséklet alapján
				self.addfavorite(Devices[18].ID)
				self.addfavorite(Devices[252].ID)
				self.addfavorite(Devices[225].ID)
				self.removefavorite(Devices[3].ID)
				self.removefavorite(Devices[85].ID)
				self.removefavorite(Devices[221].ID)
			elif 70 <= int(Devices[1].sValue):  # Electrical limit | Elektromos teljesítménykorlát
				self.addfavorite(Devices[85].ID)
				self.removefavorite(Devices[225].ID)
			

# Show heating/cooling zones and shared devices on the dashboard | Fűtési–hűtési zónák és közös eszközök megjelenítése a kezdőlapon

		Domoticz.Debug("Home screen: zones | Kezdőlap: zónák")

		for zone in range(1, 13):

			normal_futes, takarekos_futes, normal_hutes, takarekos_hutes, energieatermelesfuggo_futes, energieatermelesfuggo_hutes, kulsohomersekletfuggo_futes, kulsohomersekletfuggo_hutes = self.base_ids[zone]

			if getattr(self, f'Zone_TempSensors_{zone}'):
			
				if (Devices[1].Used == 1 and Devices[1].sValue != "0"):  # Heating | fűtés

					Domoticz.Debug("Home screen: heating | Kezdőlap: fűtés")

					self.removefavorite(Devices[normal_hutes].ID)
					self.removefavorite(Devices[takarekos_hutes].ID)
					self.removefavorite(Devices[kulsohomersekletfuggo_hutes].ID)
					self.removefavorite(Devices[energieatermelesfuggo_hutes].ID)
					
					if Devices[124].sValue != "0" :
						self.addfavorite(Devices[kulsohomersekletfuggo_futes].ID)
					else:
						self.removefavorite(Devices[kulsohomersekletfuggo_futes].ID)

					if Devices[125].sValue != "0" :
						self.addfavorite(Devices[energieatermelesfuggo_futes].ID)
					else:
						self.removefavorite(Devices[energieatermelesfuggo_futes].ID)

					if Devices[2].sValue == "10":  # Normal | normál
						
						Domoticz.Debug("Home screen: normal heating | Kezdőlap: normál fűtés")

						self.addfavorite(Devices[normal_futes].ID)
						self.removefavorite(Devices[takarekos_futes].ID)
						self.removefavorite(Devices[normal_hutes].ID)
						self.removefavorite(Devices[takarekos_hutes].ID)
					
					else:  # Economy | takarékos

						Domoticz.Debug("Home screen: economy heating | Kezdőlap: takarékos fűtés")

						self.removefavorite(Devices[normal_futes].ID)
						self.addfavorite(Devices[takarekos_futes].ID)
						self.removefavorite(Devices[normal_hutes].ID)
						self.removefavorite(Devices[takarekos_hutes].ID)
				
				elif (Devices[22].Used == 1 and Devices[22].sValue != "0"):  # Cooling | hűtés

					Domoticz.Debug("Home screen: cooling | Kezdőlap: hűtés")

					self.removefavorite(Devices[normal_futes].ID)
					self.removefavorite(Devices[takarekos_futes].ID)
					self.removefavorite(Devices[energieatermelesfuggo_futes].ID)
					self.removefavorite(Devices[kulsohomersekletfuggo_futes].ID)
					
					if Devices[125].sValue != "0":
						self.addfavorite(Devices[energieatermelesfuggo_hutes].ID)
					else:
						self.removefavorite(Devices[energieatermelesfuggo_hutes].ID)

					if Devices[130].sValue != "0":
						self.addfavorite(Devices[kulsohomersekletfuggo_hutes].ID)
					else:
						self.removefavorite(Devices[kulsohomersekletfuggo_hutes].ID)
					
					if Devices[2].sValue == "10":  # Normal | normál
						
						Domoticz.Debug("Home screen: normal cooling | Kezdőlap: normál hűtés")
						
						self.removefavorite(Devices[normal_futes].ID)
						self.removefavorite(Devices[takarekos_futes].ID)
						self.addfavorite(Devices[normal_hutes].ID)
						self.removefavorite(Devices[takarekos_hutes].ID)
					else:  # Economy | takarékos
						
						Domoticz.Debug("Home screen: economy cooling | Kezdőlap: takarékos hűtés")
						
						self.removefavorite(Devices[normal_futes].ID)
						self.removefavorite(Devices[takarekos_futes].ID)
						self.removefavorite(Devices[normal_hutes].ID)
						self.addfavorite(Devices[takarekos_hutes].ID)

				else:
					self.removefavorite(Devices[normal_futes].ID)
					self.removefavorite(Devices[takarekos_futes].ID)
					self.removefavorite(Devices[normal_hutes].ID)
					self.removefavorite(Devices[takarekos_hutes].ID)
					self.removefavorite(Devices[kulsohomersekletfuggo_futes].ID)
					self.removefavorite(Devices[kulsohomersekletfuggo_hutes].ID)
					self.removefavorite(Devices[energieatermelesfuggo_futes].ID)
					self.removefavorite(Devices[energieatermelesfuggo_hutes].ID)
			else:
				self.removefavorite(Devices[normal_futes].ID)
				self.removefavorite(Devices[takarekos_futes].ID)
				self.removefavorite(Devices[normal_hutes].ID)
				self.removefavorite(Devices[takarekos_hutes].ID)
				self.removefavorite(Devices[kulsohomersekletfuggo_futes].ID)
				self.removefavorite(Devices[kulsohomersekletfuggo_hutes].ID)
				self.removefavorite(Devices[energieatermelesfuggo_futes].ID)
				self.removefavorite(Devices[energieatermelesfuggo_hutes].ID)


		if (Devices[1].Used == 1 and Devices[1].sValue != "0") and Devices[124].sValue != "0" and Devices[210].sValue == "10" : # If heating and dashboard display are enabled and the setpoint depends on outdoor temperature | Ha a fűtés és a kezdőlapi megjelenítés aktív, a célérték a külső hőmérséklettől függ
			self.addfavorite(Devices[228].ID)
		else:
			self.removefavorite(Devices[228].ID)

		if (Devices[22].Used == 1 and Devices[22].sValue != "0") and Devices[130].sValue != "0" and Devices[210].sValue == "10" : # If cooling and dashboard display are enabled and the setpoint depends on outdoor temperature | Ha a hűtés és a kezdőlapi megjelenítés aktív, a célérték a külső hőmérséklettől függ
			self.addfavorite(Devices[229].ID)
		else:
			self.removefavorite(Devices[229].ID)

		if ((Devices[1].Used == 1 and Devices[1].sValue != "0") or (Devices[22].Used == 1 and Devices[22].sValue != "0")) and Devices[74].sValue != "0" and Devices[210].sValue == "10":  # If a future target temperature is configured | Ha jövőbeli célhőmérséklet van beállítva
			self.addfavorite(Devices[155].ID)
			self.addfavorite(Devices[231].ID)
			out_time_msg = tl.t("Future time active at automatic target temperature")
		else:
			self.removefavorite(Devices[155].ID)
			self.removefavorite(Devices[231].ID)
			out_time_msg = tl.t("Not active")

		# Assign nValue to the message | Az nValue hozzárendelése az üzenethez
		if out_time_msg.strip() == tl.t("Not active").strip():
			out_time_nvalue = 0
		elif out_time_msg.strip() == tl.t("Future time active at automatic target temperature").strip():
			out_time_nvalue = 1
		else:
			out_time_nvalue = 0  # Default | alapértelmezett

		# Update only when a change has occurred | Csak változás esetén frissít
		if Devices[231].sValue.strip() != out_time_msg.strip() or Devices[231].nValue != out_time_nvalue:
			Domoticz.Debug(f"Updating scheduled advance target temperature: nValue={out_time_nvalue}, sValue='{out_time_msg}' | Frissítés: célhőmérséklet előre időpont alapján: nValue={out_time_nvalue}, sValue='{out_time_msg}'")
			Devices[231].Update(nValue=out_time_nvalue, sValue=out_time_msg)
		else:
			Domoticz.Debug("Scheduled future state unchanged; no update | Jövőbeli időpont állapota nem változott; nincs frissítés")

# Show heating/cooling off on the dashboard | Kikapcsolt fűtés–hűtés megjelenítése a kezdőlapon

		if (Devices[1].Used == 0 or Devices[1].sValue == "0") and (Devices[22].Used == 0 or Devices[22].sValue == "0") and Devices[210].sValue != "0" :
				
			Domoticz.Debug("Home screen ON, heating/cooling OFF: remove favorites | Kezdőlapon bekapcsolva, fűtés/hűtés kikapcsolva: kedvencek eltávolítása")

			self.removefavorite(Devices[3].ID)
			self.removefavorite(Devices[7].ID)
			self.removefavorite(Devices[18].ID)
			self.removefavorite(Devices[64].ID)
			self.removefavorite(Devices[85].ID)
			self.removefavorite(Devices[86].ID)
			self.removefavorite(Devices[216].ID)
			self.removefavorite(Devices[221].ID)
			self.removefavorite(Devices[225].ID)
			self.removefavorite(Devices[252].ID)

# Show domestic hot water on the dashboard | HMV megjelenítése a kezdőlapon

		if Devices[13].sValue == "0" and Devices[210].sValue == "10": # DHW mode off | HMV üzemmód Off
			
			Domoticz.Debug("DHW mode OFF: remove favorites | HMV üzemmód kikapcsolva: kedvencek eltávolítása")

			self.removefavorite(Devices[14].ID)
			self.removefavorite(Devices[15].ID)
			self.removefavorite(Devices[17].ID)
			self.removefavorite(Devices[30].ID)
			self.removefavorite(Devices[31].ID)
			self.removefavorite(Devices[32].ID)
			self.removefavorite(Devices[35].ID)
			self.removefavorite(Devices[36].ID)
			self.removefavorite(Devices[37].ID)
			self.removefavorite(Devices[65].ID)
			self.removefavorite(Devices[79].ID)
			self.removefavorite(Devices[80].ID)
			self.removefavorite(Devices[81].ID)
			self.removefavorite(Devices[83].ID)
			self.removefavorite(Devices[85].ID)
			self.removefavorite(Devices[115].ID)
			self.removefavorite(Devices[116].ID)
			self.removefavorite(Devices[210].ID)
			self.removefavorite(Devices[222].ID)
			self.removefavorite(Devices[225].ID)
			self.removefavorite(Devices[233].ID)
			self.removefavorite(Devices[234].ID)
			self.removefavorite(Devices[239].ID)

		elif Devices[13].sValue == "10" and Devices[210].sValue == "10" : # DHW device 1 | HMV 1. eszköz

			self.addfavorite(Devices[17].ID)
			self.addfavorite(Devices[65].ID)

			if self.Elsodleges_E :
				self.addfavorite(Devices[35].ID)
				self.addfavorite(Devices[115].ID)
			else:
				self.removefavorite(Devices[35].ID)
				self.removefavorite(Devices[115].ID)

			self.removefavorite(Devices[15].ID)
			self.removefavorite(Devices[37].ID)
			self.removefavorite(Devices[36].ID)
			self.removefavorite(Devices[85].ID)
			self.removefavorite(Devices[116].ID)
			self.removefavorite(Devices[222].ID)
			self.removefavorite(Devices[225].ID)
 
			if Devices[32].sValue == "10" : # Economy–normal | takarékos-normál
				self.addfavorite(Devices[14].ID)
				self.removefavorite(Devices[30].ID)
			else :
				self.addfavorite(Devices[30].ID)
				self.removefavorite(Devices[14].ID)

		elif Devices[13].sValue == "20" and Devices[210].sValue == "10" : # DHW device 2 | HMV 2. eszköz

			self.addfavorite(Devices[17].ID)
			self.addfavorite(Devices[65].ID)
			
			if self.Masodlagos_E :
				self.addfavorite(Devices[36].ID)
				self.addfavorite(Devices[116].ID)
			else:
				self.removefavorite(Devices[36].ID)
				self.removefavorite(Devices[116].ID)

			self.removefavorite(Devices[15].ID)
			self.removefavorite(Devices[35].ID)
			self.removefavorite(Devices[37].ID)
			self.removefavorite(Devices[85].ID)
			self.removefavorite(Devices[115].ID)
			self.removefavorite(Devices[222].ID)
			self.removefavorite(Devices[225].ID)
 
			if Devices[32].sValue == "10" : # Economy–normal | takarékos-normál
				self.addfavorite(Devices[14].ID)
				self.removefavorite(Devices[30].ID)
			else :
				self.addfavorite(Devices[30].ID)
				self.removefavorite(Devices[14].ID)

		elif Devices[13].sValue == "30" and Devices[210].sValue == "10" : # DHW switching mode based on tank temperature | HMV Váltó mód tartály hőmérséklet alapján

			self.removefavorite(Devices[15].ID)
			self.addfavorite(Devices[17].ID)
			self.addfavorite(Devices[37].ID)
			self.addfavorite(Devices[65].ID)
			self.removefavorite(Devices[85].ID)
			self.removefavorite(Devices[222].ID)
			self.removefavorite(Devices[225].ID)
 
			if Devices[32].sValue == "10" : # Economy–normal | takarékos-normál
				self.addfavorite(Devices[14].ID)
				self.removefavorite(Devices[30].ID)
			else :
				self.addfavorite(Devices[30].ID)
				self.removefavorite(Devices[14].ID)

			if self.Elsodleges_E :
				self.addfavorite(Devices[35].ID)
				self.addfavorite(Devices[115].ID)
			else:
				self.removefavorite(Devices[35].ID)
				self.removefavorite(Devices[115].ID)

			if self.Masodlagos_E :
				self.addfavorite(Devices[36].ID)
				self.addfavorite(Devices[116].ID)
			else:
				self.removefavorite(Devices[36].ID)
				self.removefavorite(Devices[116].ID)

		elif Devices[13].sValue == "40" and Devices[210].sValue == "10" : # DHW switching mode based on outdoor temperature | HMV Váltó üzemmód külső hőmérséklet alapján

			self.addfavorite(Devices[15].ID)
			self.addfavorite(Devices[17].ID)
			self.addfavorite(Devices[65].ID)
			self.removefavorite(Devices[85].ID)
			self.addfavorite(Devices[225].ID)
			self.removefavorite(Devices[37].ID)
			self.removefavorite(Devices[222].ID)
 
			if Devices[32].sValue == "10" : # Economy–normal | takarékos-normál
				self.addfavorite(Devices[14].ID)
				self.removefavorite(Devices[30].ID)
			else :
				self.addfavorite(Devices[30].ID)
				self.removefavorite(Devices[14].ID)

			if self.Elsodleges_E :
				self.addfavorite(Devices[35].ID)
				self.addfavorite(Devices[115].ID)
			else:
				self.removefavorite(Devices[35].ID)
				self.removefavorite(Devices[115].ID)

			if self.Masodlagos_E :
				self.addfavorite(Devices[36].ID)
				self.addfavorite(Devices[116].ID)
			else:
				self.removefavorite(Devices[36].ID)
				self.removefavorite(Devices[116].ID)

		elif Devices[13].sValue == "50" and Devices[210].sValue == "10" : # DHW switching mode based on outdoor dew point | HMV Váltó mód külső harmatpont alapján

			self.addfavorite(Devices[15].ID)
			self.addfavorite(Devices[17].ID)
			self.addfavorite(Devices[65].ID)
			self.removefavorite(Devices[85].ID)
			self.addfavorite(Devices[222].ID)
			self.removefavorite(Devices[37].ID)
			self.removefavorite(Devices[225].ID)
 
			if Devices[32].sValue == "10" : # Economy–normal | takarékos-normál
				self.addfavorite(Devices[14].ID)
				self.removefavorite(Devices[30].ID)
			else :
				self.addfavorite(Devices[30].ID)
				self.removefavorite(Devices[14].ID)

			if self.Elsodleges_E :
				self.addfavorite(Devices[35].ID)
				self.addfavorite(Devices[115].ID)
			else:
				self.removefavorite(Devices[35].ID)
				self.removefavorite(Devices[115].ID)

			if self.Masodlagos_E :
				self.addfavorite(Devices[36].ID)
				self.addfavorite(Devices[116].ID)
			else:
				self.removefavorite(Devices[36].ID)
				self.removefavorite(Devices[116].ID)

		elif Devices[13].sValue == "60" and Devices[210].sValue == "10" : # DHW dual mode based on tank temperature | HMV Dual mód tartály hőmérséklet alapján

			self.addfavorite(Devices[17].ID)
			self.addfavorite(Devices[37].ID)
			self.removefavorite(Devices[15].ID)
			self.addfavorite(Devices[65].ID)
			self.removefavorite(Devices[85].ID)
			self.removefavorite(Devices[222].ID)
			self.removefavorite(Devices[225].ID)
 
			if Devices[32].sValue == "10" : # Economy–normal | takarékos-normál
				self.addfavorite(Devices[14].ID)
				self.removefavorite(Devices[30].ID)
			else :
				self.addfavorite(Devices[30].ID)
				self.removefavorite(Devices[14].ID)

		elif Devices[13].sValue == "70" and Devices[210].sValue == "10" : # DHW dual mode based on outdoor temperature | HMV Dual üzemmód külső hőmérséklet alapján

			self.addfavorite(Devices[15].ID)
			self.addfavorite(Devices[17].ID)
			self.removefavorite(Devices[37].ID)
			self.addfavorite(Devices[65].ID)
			self.addfavorite(Devices[225].ID)
 
			if Devices[32].sValue == "10" : # Economy–normal | takarékos-normál
				self.addfavorite(Devices[14].ID)
				self.removefavorite(Devices[30].ID)
			else :
				self.addfavorite(Devices[30].ID)
				self.removefavorite(Devices[14].ID)

			if self.Elsodleges_E :
				self.addfavorite(Devices[35].ID)
				self.addfavorite(Devices[115].ID)
			else:
				self.removefavorite(Devices[35].ID)
				self.removefavorite(Devices[115].ID)

			if self.Masodlagos_E :
				self.addfavorite(Devices[36].ID)
				self.addfavorite(Devices[116].ID)
			else:
				self.removefavorite(Devices[36].ID)
				self.removefavorite(Devices[116].ID)

		elif Devices[13].sValue == "80" and Devices[210].sValue == "10" : # DHW dual mode based on outdoor dew point | HMV Dual mód külső harmatpont alapján

			self.addfavorite(Devices[15].ID)
			self.addfavorite(Devices[17].ID)
			self.addfavorite(Devices[222].ID)
			self.removefavorite(Devices[37].ID)
			self.addfavorite(Devices[65].ID)
			self.removefavorite(Devices[85].ID)
			self.removefavorite(Devices[225].ID)
 
			if Devices[32].sValue == "10" : # Economy–normal | takarékos-normál
				self.addfavorite(Devices[14].ID)
				self.removefavorite(Devices[30].ID)
			else :
				self.addfavorite(Devices[30].ID)
				self.removefavorite(Devices[14].ID)

		elif Devices[13].sValue == "90" and Devices[210].sValue == "10" : # DHW saver mode based on tank and outdoor temperatures | HMV Saver mód tartály hőmérséklet és külsőhőmérséklet alapján

			self.addfavorite(Devices[15].ID)
			self.addfavorite(Devices[17].ID)
			self.addfavorite(Devices[37].ID)
			self.addfavorite(Devices[65].ID)
			self.removefavorite(Devices[85].ID)
			self.removefavorite(Devices[222].ID)
			self.addfavorite(Devices[225].ID)
 
			if Devices[32].sValue == "10" : # Economy–normal | takarékos-normál
				self.addfavorite(Devices[14].ID)
				self.removefavorite(Devices[30].ID)
			else :
				self.addfavorite(Devices[30].ID)
				self.removefavorite(Devices[14].ID)

			if self.Elsodleges_E :
				self.addfavorite(Devices[35].ID)
				self.addfavorite(Devices[115].ID)
			else:
				self.removefavorite(Devices[35].ID)
				self.removefavorite(Devices[115].ID)

			if self.Masodlagos_E :
				self.addfavorite(Devices[36].ID)
				self.addfavorite(Devices[116].ID)
			else:
				self.removefavorite(Devices[36].ID)
				self.removefavorite(Devices[116].ID)

		elif Devices[13].sValue == "100" and Devices[210].sValue == "10" : # DHW saver mode based on tank temperature and outdoor dew point | HMV Saver mód tartály hőmérséklet és külső harmatpont alapján

			self.addfavorite(Devices[15].ID)
			self.addfavorite(Devices[17].ID)
			self.addfavorite(Devices[37].ID)
			self.addfavorite(Devices[65].ID)
			self.addfavorite(Devices[222].ID)
			self.removefavorite(Devices[85].ID)
			self.removefavorite(Devices[225].ID)
 
			if Devices[32].sValue == "10" : # Economy–normal | takarékos-normál
				self.addfavorite(Devices[14].ID)
				self.removefavorite(Devices[30].ID)
			else :
				self.addfavorite(Devices[30].ID)
				self.removefavorite(Devices[14].ID)

			if self.Elsodleges_E :
				self.addfavorite(Devices[35].ID)
				self.addfavorite(Devices[115].ID)
			else:
				self.removefavorite(Devices[35].ID)
				self.removefavorite(Devices[115].ID)

			if self.Masodlagos_E :
				self.addfavorite(Devices[36].ID)
				self.addfavorite(Devices[116].ID)
			else:
				self.removefavorite(Devices[36].ID)
				self.removefavorite(Devices[116].ID)

		elif Devices[13].sValue <= "110" and Devices[210].sValue == "10" : # DHW power limit | HMV Watt limit

			self.addfavorite(Devices[17].ID)
			self.addfavorite(Devices[65].ID)
			self.addfavorite(Devices[85].ID)

			if self.Elsodleges_E :
				self.addfavorite(Devices[35].ID)
				self.addfavorite(Devices[115].ID)
			else:
				self.removefavorite(Devices[35].ID)
				self.removefavorite(Devices[115].ID)

			self.removefavorite(Devices[15].ID)
			self.removefavorite(Devices[37].ID)
			self.removefavorite(Devices[36].ID)
			self.removefavorite(Devices[116].ID)
			self.removefavorite(Devices[222].ID)
			self.removefavorite(Devices[225].ID)
 
			if Devices[32].sValue == "10" : # Economy–normal | takarékos-normál
				self.addfavorite(Devices[14].ID)
				self.removefavorite(Devices[30].ID)
			else :
				self.addfavorite(Devices[30].ID)
				self.removefavorite(Devices[14].ID)

		
		if self.solar_dhw_limit != 0 and Devices[210].sValue == "10" and Devices[13].sValue != "0": # DHW solar power generation (watts) | HMV Napelemes termelés HMV (Watt)
			self.addfavorite(Devices[80].ID)
			self.addfavorite(Devices[81].ID)
			self.addfavorite(Devices[233].ID)
		else:
			self.removefavorite(Devices[80].ID)
			self.removefavorite(Devices[81].ID)
			self.removefavorite(Devices[233].ID)


		if Devices[83].sValue != "0" and Devices[210].sValue == "10" and Devices[13].sValue != "0": # DHW target external switching threshold | HMV cél külső kapcsolási határ
			self.addfavorite(Devices[31].ID)
			self.addfavorite(Devices[79].ID)
			self.addfavorite(Devices[234].ID)
		else:
			self.removefavorite(Devices[31].ID)
			self.removefavorite(Devices[79].ID)
			self.removefavorite(Devices[234].ID)


# Show buffer heating on the dashboard | Pufferfűtés megjelenítése a kezdőlapon

		if (Devices[104].Used == 1 and Devices[104].sValue != "0") and Devices[210].sValue != "0" :  # Dashboard enabled and buffer heating enabled | Kezdőlapi megjelenítés és pufferfűtés bekapcsolva

			self.removefavorite(Devices[91].ID)
			self.removefavorite(Devices[123].ID)

			if Devices[98].sValue != "0": # Energy limit | Energiakorlát
				self.addfavorite(Devices[94].ID)
				self.addfavorite(Devices[96].ID)
				self.addfavorite(Devices[235].ID)

			else:
				self.removefavorite(Devices[94].ID)
				self.removefavorite(Devices[96].ID)
				self.removefavorite(Devices[235].ID)

			if Devices[84].sValue != "0": # Based on outdoor temperature | külső hőmérséklet alapján
				self.addfavorite(Devices[77].ID)
				self.addfavorite(Devices[82].ID)
				self.addfavorite(Devices[236].ID)

			else:
				self.removefavorite(Devices[77].ID)
				self.removefavorite(Devices[82].ID)
				self.removefavorite(Devices[236].ID)

			if Devices[104].sValue == "10": # Buffer device 1 | Puffer 1. eszköz

				self.addfavorite(Devices[90].ID)
				self.addfavorite(Devices[92].ID)
				self.removefavorite(Devices[85].ID)
				self.removefavorite(Devices[77].ID)
				self.removefavorite(Devices[108].ID)
				self.removefavorite(Devices[109].ID)
				self.removefavorite(Devices[223].ID)

				if self.Elsodleges_PE:
					self.addfavorite(Devices[110].ID)
					self.addfavorite(Devices[117].ID)
				else:
					self.removefavorite(Devices[110].ID)
					self.removefavorite(Devices[117].ID)
			
			elif Devices[104].sValue == "20": # Buffer device 2 for heating | Puffer 2. eszköz futes

				self.addfavorite(Devices[90].ID)
				self.addfavorite(Devices[92].ID)
				self.removefavorite(Devices[85].ID)
				self.removefavorite(Devices[77].ID)
				self.removefavorite(Devices[108].ID)
				self.removefavorite(Devices[109].ID)
				self.removefavorite(Devices[223].ID)

				if self.Elsodleges_PE:
					self.addfavorite(Devices[110].ID)
					self.addfavorite(Devices[117].ID)
				else:
					self.removefavorite(Devices[110].ID)
					self.removefavorite(Devices[117].ID)

			elif Devices[104].sValue == "30" : # Buffer heating switching mode based on buffer tank temperature | Puffer Váltó mód puffer tartály hőmérséklet alapján futes
				
				self.addfavorite(Devices[109].ID)
				self.removefavorite(Devices[85].ID)
				self.removefavorite(Devices[77].ID)
				self.removefavorite(Devices[90].ID)
				self.removefavorite(Devices[108].ID)
				self.removefavorite(Devices[223].ID)

				if self.Elsodleges_PE:
					self.addfavorite(Devices[110].ID)
					self.addfavorite(Devices[117].ID)
				else:
					self.removefavorite(Devices[110].ID)
					self.removefavorite(Devices[117].ID)

				if self.Masodlagos_PE:
					self.addfavorite(Devices[111].ID)
					self.addfavorite(Devices[118].ID)
				else:
					self.removefavorite(Devices[111].ID)
					self.removefavorite(Devices[118].ID)

			elif Devices[104].sValue == "40" : # Buffer heating switching mode based on outdoor temperature | Puffer Váltó üzemmód külső hőmérséklet alapján futes

				self.addfavorite(Devices[77].ID)
				self.addfavorite(Devices[108].ID)
				self.removefavorite(Devices[85].ID)
				self.removefavorite(Devices[90].ID)
				self.removefavorite(Devices[92].ID)
				self.removefavorite(Devices[109].ID)
				self.removefavorite(Devices[223].ID)

				if self.Elsodleges_PE:
					self.addfavorite(Devices[110].ID)
					self.addfavorite(Devices[117].ID)
				else:
					self.removefavorite(Devices[110].ID)
					self.removefavorite(Devices[117].ID)

				if self.Masodlagos_PE:
					self.addfavorite(Devices[111].ID)
					self.addfavorite(Devices[118].ID)
				else:
					self.removefavorite(Devices[111].ID)
					self.removefavorite(Devices[118].ID)

			elif Devices[104].sValue == "50" : # Buffer heating switching mode based on outdoor dew point | Puffer Váltó mód külső harmatpont alapján futes

				self.addfavorite(Devices[77].ID)
				self.addfavorite(Devices[223].ID)
				self.removefavorite(Devices[85].ID)
				self.removefavorite(Devices[90].ID)
				self.removefavorite(Devices[92].ID)
				self.removefavorite(Devices[108].ID)
				self.removefavorite(Devices[109].ID)

				if self.Elsodleges_PE:
					self.addfavorite(Devices[110].ID)
					self.addfavorite(Devices[117].ID)
				else:
					self.removefavorite(Devices[110].ID)
					self.removefavorite(Devices[117].ID)

				if self.Masodlagos_PE:
					self.addfavorite(Devices[111].ID)
					self.addfavorite(Devices[118].ID)
				else:
					self.removefavorite(Devices[111].ID)
					self.removefavorite(Devices[118].ID)

			elif Devices[104].sValue == "60" : # Buffer heating dual mode based on buffer tank temperature | Puffer Dual mód puffer tartály hőmérséklet alapján futes

				self.addfavorite(Devices[109].ID)
				self.removefavorite(Devices[77].ID)
				self.removefavorite(Devices[85].ID)
				self.removefavorite(Devices[90].ID)
				self.removefavorite(Devices[92].ID)
				self.removefavorite(Devices[108].ID)
				self.removefavorite(Devices[223].ID)

				if self.Elsodleges_PE:
					self.addfavorite(Devices[110].ID)
					self.addfavorite(Devices[117].ID)
				else:
					self.removefavorite(Devices[110].ID)
					self.removefavorite(Devices[117].ID)

				if self.Masodlagos_PE:
					self.addfavorite(Devices[111].ID)
					self.addfavorite(Devices[118].ID)
				else:
					self.removefavorite(Devices[111].ID)
					self.removefavorite(Devices[118].ID)

			elif Devices[104].sValue == "70" : # Buffer heating dual mode based on outdoor temperature | Puffer Dual üzemmód külső hőmérséklet alapján futes

				self.addfavorite(Devices[77].ID)
				self.addfavorite(Devices[108].ID)
				self.removefavorite(Devices[85].ID)
				self.removefavorite(Devices[90].ID)
				self.removefavorite(Devices[92].ID)
				self.removefavorite(Devices[109].ID)
				self.removefavorite(Devices[223].ID)

				if self.Elsodleges_PE:
					self.addfavorite(Devices[110].ID)
					self.addfavorite(Devices[117].ID)
				else:
					self.removefavorite(Devices[110].ID)
					self.removefavorite(Devices[117].ID)

				if self.Masodlagos_PE:
					self.addfavorite(Devices[111].ID)
					self.addfavorite(Devices[118].ID)
				else:
					self.removefavorite(Devices[111].ID)
					self.removefavorite(Devices[118].ID)

			elif Devices[104].sValue == "80" : # Buffer heating dual mode based on outdoor dew point | Puffer Dual mód külső harmatpont alapján futes

				self.addfavorite(Devices[77].ID)
				self.addfavorite(Devices[223].ID)
				self.removefavorite(Devices[85].ID)
				self.removefavorite(Devices[90].ID)
				self.removefavorite(Devices[92].ID)
				self.removefavorite(Devices[108].ID)
				self.removefavorite(Devices[109].ID)

				if self.Elsodleges_PE:
					self.addfavorite(Devices[110].ID)
					self.addfavorite(Devices[117].ID)
				else:
					self.removefavorite(Devices[110].ID)
					self.removefavorite(Devices[117].ID)

				if self.Masodlagos_PE:
					self.addfavorite(Devices[111].ID)
					self.addfavorite(Devices[118].ID)
				else:
					self.removefavorite(Devices[111].ID)
					self.removefavorite(Devices[118].ID)

			elif Devices[104].sValue == "90" : # Buffer heating saver mode based on buffer tank and outdoor temperatures | Puffer Saver mód puffer tartály hőmérséklet és külsőhőmérséklet alapján futes

				self.addfavorite(Devices[77].ID)
				self.addfavorite(Devices[108].ID)
				self.addfavorite(Devices[109].ID)
				self.removefavorite(Devices[85].ID)
				self.removefavorite(Devices[90].ID)
				self.removefavorite(Devices[92].ID)
				self.removefavorite(Devices[223].ID)

				if self.Elsodleges_PE:
					self.addfavorite(Devices[110].ID)
					self.addfavorite(Devices[117].ID)
				else:
					self.removefavorite(Devices[110].ID)
					self.removefavorite(Devices[117].ID)

				if self.Masodlagos_PE:
					self.addfavorite(Devices[111].ID)
					self.addfavorite(Devices[118].ID)
				else:
					self.removefavorite(Devices[111].ID)
					self.removefavorite(Devices[118].ID)

			elif Devices[104].sValue == "100" : # Buffer heating saver mode based on buffer tank temperature and outdoor dew point | Puffer Saver mód puffer tartály hőmérséklet és külső harmatpont alapján futes

				self.addfavorite(Devices[77].ID)
				self.addfavorite(Devices[109].ID)
				self.addfavorite(Devices[223].ID)
				self.removefavorite(Devices[85].ID)
				self.removefavorite(Devices[90].ID)
				self.removefavorite(Devices[92].ID)
				self.removefavorite(Devices[108].ID)

				if self.Elsodleges_PE:
					self.addfavorite(Devices[110].ID)
					self.addfavorite(Devices[117].ID)
				else:
					self.removefavorite(Devices[110].ID)
					self.removefavorite(Devices[117].ID)

				if self.Masodlagos_PE:
					self.addfavorite(Devices[111].ID)
					self.addfavorite(Devices[118].ID)
				else:
					self.removefavorite(Devices[111].ID)
					self.removefavorite(Devices[118].ID)

			elif Devices[104].sValue <= "110": # Buffer power limit | Puffer teljesítménykorlát (W)

				self.addfavorite(Devices[85].ID)
				self.addfavorite(Devices[90].ID)
				self.addfavorite(Devices[92].ID)
				self.removefavorite(Devices[77].ID)
				self.removefavorite(Devices[108].ID)
				self.removefavorite(Devices[109].ID)
				self.removefavorite(Devices[223].ID)

				if self.Elsodleges_PE:
					self.addfavorite(Devices[110].ID)
					self.addfavorite(Devices[117].ID)
				else:
					self.removefavorite(Devices[110].ID)
					self.removefavorite(Devices[117].ID)

# Show buffer cooling on the dashboard | Pufferhűtés megjelenítése a kezdőlapon

		if (Devices[224].Used == 1 and Devices[224].sValue != "0") and Devices[210].sValue != "0" :  # Dashboard enabled and buffer cooling enabled | Kezdőlapi megjelenítés és pufferhűtés bekapcsolva

			self.addfavorite(Devices[91].ID)
			self.addfavorite(Devices[123].ID)
			self.removefavorite(Devices[77].ID)
			self.removefavorite(Devices[85].ID)
			self.removefavorite(Devices[95].ID)
			self.removefavorite(Devices[109].ID)
			self.removefavorite(Devices[110].ID)
			self.removefavorite(Devices[111].ID)
			self.removefavorite(Devices[117].ID)
			self.removefavorite(Devices[118].ID)
			self.removefavorite(Devices[223].ID)

			if Devices[98].sValue != "0": # Energy limit | Energiakorlát
				self.addfavorite(Devices[93].ID)
				self.addfavorite(Devices[96].ID)
				self.addfavorite(Devices[235].ID)

			else:
				self.removefavorite(Devices[93].ID)
				self.removefavorite(Devices[96].ID)
				self.removefavorite(Devices[235].ID)

			if Devices[99].sValue != "0": # Based on outdoor temperature | külső hőmérséklet alapján
				self.addfavorite(Devices[77].ID)
				self.addfavorite(Devices[99].ID)
				self.addfavorite(Devices[236].ID)

			else:
				self.removefavorite(Devices[77].ID)
				self.removefavorite(Devices[99].ID)
				self.removefavorite(Devices[236].ID)

			if Devices[224].sValue == "10": # Buffer device 1 cooling | 1. puffereszköz hűtése

				self.removefavorite(Devices[77].ID)
				self.removefavorite(Devices[90].ID)
				self.removefavorite(Devices[92].ID)
				self.removefavorite(Devices[85].ID)
				self.removefavorite(Devices[226].ID)
				self.removefavorite(Devices[109].ID)
			
			elif Devices[224].sValue == "20": # Buffer device 2 cooling | 2. puffereszköz hűtése

				self.removefavorite(Devices[77].ID)
				self.removefavorite(Devices[85].ID)
				self.removefavorite(Devices[90].ID)
				self.removefavorite(Devices[92].ID)
				self.removefavorite(Devices[226].ID)
				self.removefavorite(Devices[109].ID)

			elif Devices[224].sValue == "30" : # Buffer switching mode by tank temperature during cooling | Puffer váltó módja tartályhőmérséklet alapján, hűtéskor

				self.addfavorite(Devices[109].ID)
				self.removefavorite(Devices[85].ID)
				self.removefavorite(Devices[92].ID)
				self.removefavorite(Devices[77].ID)
				self.removefavorite(Devices[226].ID)

			elif Devices[224].sValue == "40" : # Buffer switching mode by outdoor temperature during cooling | Puffer váltó módja külső hőmérséklet alapján, hűtéskor

				self.addfavorite(Devices[77].ID)
				self.removefavorite(Devices[85].ID)
				self.addfavorite(Devices[226].ID)
				self.removefavorite(Devices[109].ID)

			elif Devices[224].sValue == "50" : # Buffer dual mode by tank temperature during cooling | Puffer dual módja tartályhőmérséklet alapján, hűtéskor

				self.removefavorite(Devices[92].ID)
				self.addfavorite(Devices[109].ID)
				self.removefavorite(Devices[77].ID)
				self.removefavorite(Devices[85].ID)
				self.removefavorite(Devices[226].ID)

			elif Devices[224].sValue == "60" : # Buffer dual mode by outdoor temperature during cooling | Puffer dual módja külső hőmérséklet alapján, hűtéskor

				self.addfavorite(Devices[77].ID)
				self.addfavorite(Devices[226].ID)
				self.removefavorite(Devices[85].ID)
				self.removefavorite(Devices[109].ID)

			elif Devices[224].sValue <= "70": # Buffer power limit | Puffer teljesítménykorlát

				self.removefavorite(Devices[77].ID)
				self.removefavorite(Devices[90].ID)
				self.removefavorite(Devices[92].ID)
				self.addfavorite(Devices[85].ID)
				self.removefavorite(Devices[226].ID)
				self.removefavorite(Devices[109].ID)


# Turn off buffer on home page | Puffer kikapcsolása a kezdőlapon

		if (Devices[104].Used == 0 or Devices[104].sValue == "0") and (Devices[224].Used == 0 or Devices[224].sValue == "0") and Devices[210].sValue != "0" :

			Domoticz.Debug("Buffer mode OFF: remove favorites | Puffer üzemmód kikapcsolva: kedvencek eltávolítása")

			self.removefavorite(Devices[77].ID)
			self.removefavorite(Devices[82].ID)
			self.removefavorite(Devices[85].ID)
			self.removefavorite(Devices[90].ID)
			self.removefavorite(Devices[91].ID)
			self.removefavorite(Devices[92].ID)
			self.removefavorite(Devices[93].ID)
			self.removefavorite(Devices[94].ID)
			self.removefavorite(Devices[96].ID)
			self.removefavorite(Devices[99].ID)
			self.removefavorite(Devices[109].ID)
			self.removefavorite(Devices[110].ID)
			self.removefavorite(Devices[111].ID)
			self.removefavorite(Devices[117].ID)
			self.removefavorite(Devices[118].ID)
			self.removefavorite(Devices[123].ID)
			self.removefavorite(Devices[223].ID)
			self.removefavorite(Devices[226].ID)
			self.removefavorite(Devices[235].ID)
			self.removefavorite(Devices[236].ID)

		if self.FrostTempSensors :
				self.addfavorite(Devices[89].ID)
				self.addfavorite(Devices[156].ID)
		else :
			self.removefavorite(Devices[89].ID)
			self.removefavorite(Devices[156].ID)

		self.applyfavorites()
		
		saveUserVar(self)

		getUserVar(self)

		self.switchcommand()

		self.get_AC_zone_var(1, "F")
		self.get_AC_zone_var(2, "F")
		self.get_AC_zone_var(3, "F")
		self.get_AC_zone_var(4, "F")
		self.get_AC_zone_var(5, "F")
		self.get_AC_zone_var(6, "F")
		self.get_AC_zone_var(7, "F")
		self.get_AC_zone_var(8, "F")
		self.get_AC_zone_var(9, "F")
		self.get_AC_zone_var(10, "F")
		self.get_AC_zone_var(11, "F")
		self.get_AC_zone_var(12, "F")


		self.get_AC_zone_var(1, "H")
		self.get_AC_zone_var(2, "H")
		self.get_AC_zone_var(3, "H")
		self.get_AC_zone_var(4, "H")
		self.get_AC_zone_var(5, "H")
		self.get_AC_zone_var(6, "H")
		self.get_AC_zone_var(7, "H")
		self.get_AC_zone_var(8, "H")
		self.get_AC_zone_var(9, "H")
		self.get_AC_zone_var(10, "H")
		self.get_AC_zone_var(11, "H")
		self.get_AC_zone_var(12, "H")



	def onHeartbeat(self):

		self.sync_zone_console_and_setpoints()

		now = time.time()


		Domoticz.Debug(f"Delayed actions snapshot: {self.delayedActions} | Késleltetett műveletek pillanatképe: {self.delayedActions}")

		for idx, data in list(self.delayedActions.items()):
			execute_time = data["time"]
			command = data["command"]

			Domoticz.Debug(
				f"Delayed action check: idx={idx}, now={now:.0f}, execute={execute_time:.0f}, difference={now - execute_time:.1f}s | Késleltetett művelet ellenőrzése: idx={idx}, most={now:.0f}, végrehajtás={execute_time:.0f}, eltérés={now - execute_time:.1f}s"
			)

			# Execute when scheduled time arrives | Ha elérkezett az idő, végre kell hajtani
			if now >= execute_time:
				Domoticz.Debug(f"Executing delayed command: idx={idx}, command={command} | Késleltetett kapcsolás végrehajtása: idx={idx}, parancs={command}")

				res = DomoticzAPI(
					"type=command&param=switchlight&idx={}&switchcmd={}".format(idx, command)
				)

				Domoticz.Debug(f"API response: idx={idx}, result={res} | API-válasz: idx={idx}, eredmény={res}")

				# Remove from delayed-action list | Eltávolítás a késleltetett műveletek listájából
				del self.delayedActions[idx]
				Domoticz.Debug(f"Delayed action removed: idx={idx} | Késleltetett művelet törölve: idx={idx}")

		if self.nextupdate <= datetime.now() or self.lastjelenletInfo != self.jelenletInfo:

			self.lastjelenletInfo = self.jelenletInfo

			self.current_hour = datetime.now().hour

			self.met_date_load()

			self.AktualThermostat =  DomoticzAPI(
				"type=devices&filter=thermostat&order=Name"
				if float(Parameters["DomoticzVersion"]) <= 2023.1
				else "type=command&param=getdevices&filter=thermostat&order=Name"
			)

			self.get_total_watt()
			
			self.readTemps()

			self.update_window_states()

			if self.heating_colling :
				if (self.Zone_TempSensors_1 or self.Zone_TempSensors_2 or self.Zone_TempSensors_3 or self.Zone_TempSensors_4 or self.Zone_TempSensors_5 or self.Zone_TempSensors_6):
					self.zone_temp_read()
					self.AutoCallib()
					Domoticz.Debug("At least one zone temperature sensor is configured | Legalább egy zónahőmérő be van állítva")
				else :
					Domoticz.Error('No zone temperature sensor is configured! | Nincs egyetlen zóna hőmérő sem beállítva!')

			if self.dhw or self.heating_colling or self.buffer :
				self.switchJelenlet()

			self.switchcreated.clear()
			self.statuscreated.clear()

			self.pump_protection()

			self.f1works = False
			self.h1works = False
			self.p1works = False
			self.f2works = False
			self.h2works = False
			self.p2works = False

			self.frost_protection()

			if self.dhw and Devices[13].sValue != "0" and (Devices[13].Used == 1):
				
				Domoticz.Debug("DHW mode and operation enabled | HMV mód és működés bekapcsolva")

				self.dhw_temp_read()

				mode = Devices[13].sValue
				dhw_limit = float(Devices[225].sValue)      # DHW device 2 switching threshold | HMV 2. eszközének kapcsolási küszöbértéke
				dhw_diff = float(Devices[37].sValue)       # DHW dual temperature differential | HMV dual hőmérséklet-különbsége
				dhw_dualkomp = float(Devices[222].sValue)    # DHW dew-point compensation | HMV harmatpont-kompenzációja
				dhw_hysteresis = float(Devices[15].sValue)  # Hysteresis | Hiszterézis

				Domoticz.Debug("DHW parameters: | HMV-paraméterek:")
				Domoticz.Debug(f"  Mode = {mode} | Üzemmód = {mode}")
				Domoticz.Debug(f"  Tank measured temperature = {self.TartalyAktual:.1f} °C | Tartály mért hőmérséklete = {self.TartalyAktual:.1f} °C")
				Domoticz.Debug(f"  Tank target temperature = {self.M_celhomerseklet:.1f} °C | Tartály célhőmérséklete = {self.M_celhomerseklet:.1f} °C")
				Domoticz.Debug(f"  Outdoor temperature = {self.outtemp:.1f} °C | Külső hőmérséklet = {self.outtemp:.1f} °C")
				Domoticz.Debug(f"  Dew point = {self.outdewpoint:.1f} °C | Harmatpont = {self.outdewpoint:.1f} °C")
				Domoticz.Debug(f"  DHW dual correction = {dhw_dualkomp:.1f} | HMV dual korrekció = {dhw_dualkomp:.1f}")
				Domoticz.Debug(f"  Outdoor hysteresis = {dhw_hysteresis:.1f} | Külső hiszterézis = {dhw_hysteresis:.1f}")
				Domoticz.Debug(f"  Outdoor limit = {dhw_limit:.1f} | Külső határérték = {dhw_limit:.1f}")

				
				# Primary mode | Elsődleges mód
				if Devices[13].sValue == "10" and not Devices[13].TimedOut:
					Domoticz.Debug("Primary DHW mode | Elsődleges HMV-üzemmód")
					self.dhw_1()

				# Secondary mode | Másodlagos mód
				elif Devices[13].sValue == "20" and not Devices[13].TimedOut:
					Domoticz.Debug("Secondary DHW mode; primary DHW disabled | Másodlagos HMV-üzemmód; elsődleges HMV kikapcsolva")
					self.dhw_2()

				# Switching mode: tank temperature | Váltó mód: tartályhőmérséklet
				elif Devices[13].sValue == "30" and not Devices[13].TimedOut:
					Domoticz.Debug("Switching mode based on tank temperature | Váltó üzemmód tartályhőmérséklet alapján")

					# Calculate thresholds | --- Határok kiszámítása ---
					# Lower threshold: turn on dhw_2 | Alsó határ: dhw_2 bekapcsolása
					lower_limit = self.M_celhomerseklet - dhw_diff - dhw_hysteresis

					# Upper threshold: switch back to dhw_1 | Felső határ: dhw_1 visszakapcsolása
					upper_limit = self.M_celhomerseklet - dhw_diff + dhw_hysteresis

					Domoticz.Debug(
						(f'DEBUG: tank actual={self.TartalyAktual:.1f}, target={self.M_celhomerseklet}, lower={lower_limit:.1f}, upper={upper_limit:.1f}' + " | " + (f"DEBUG: TartalyAktual={self.TartalyAktual:.1f}, "
						f"cel={self.M_celhomerseklet}, "
						f"alsó határ={lower_limit:.1f}, felső határ={upper_limit:.1f}"))
					)

					# Determine operating mode | --- Üzemmód meghatározása ---
					# 0 = dhw_1 | 0 = dhw_1 (első HMV-üzemmód)
					# 1 = dhw_2 | 1 = dhw_2 (második HMV-üzemmód)

					# Tank too cold: switch to dhw_2 | Tartály túl hideg, váltás dhw_2-re
					if self.TartalyAktual < lower_limit:
						Domoticz.Debug(
							f"Tank temperature {self.TartalyAktual:.1f} below lower limit ({lower_limit:.1f}): switching to dhw_2 | Tartályhőmérséklet {self.TartalyAktual:.1f} az alsó határ ({lower_limit:.1f}) alatt: váltás dhw_2 módra"
						)
						self.D_last_mode_state = 1

					# Tank warm enough → return to dhw_1 | Tartály elég meleg → vissza dhw_1-re
					elif self.TartalyAktual > upper_limit:
						Domoticz.Debug(
							f"Tank temperature {self.TartalyAktual:.1f} above upper limit ({upper_limit:.1f}): switching to dhw_1 | Tartályhőmérséklet {self.TartalyAktual:.1f} a felső határ ({upper_limit:.1f}) felett: váltás dhw_1 módra"
						)
						self.D_last_mode_state = 0

					# Intermediate range → no switching | Köztes tartomány → nincs váltás
					else:
						Domoticz.Debug(
							(f'Tank temperature {self.TartalyAktual:.1f} is within the hysteresis band ({lower_limit:.1f}–{upper_limit:.1f}); maintaining mode: {self.D_last_mode_state}' + " | " + (f"Tartály {self.TartalyAktual:.1f} a hiszterézis sávban "
							f"({lower_limit:.1f}–{upper_limit:.1f}) → üzemmód tartása: {self.D_last_mode_state}"))
						)

					# Execution | --- VÉGREHAJTÁS ---
					if self.D_last_mode_state == 0:
						self.dhw_1()
					else:
						self.dhw_2()

				# Switching mode: outdoor temperature | Váltó mód: külső hőmérséklet
				elif Devices[13].sValue == "40" and not Devices[13].TimedOut:
					Domoticz.Debug("Switching mode based on outdoor temperature | Váltó üzemmód külső hőmérséklet alapján")

					# Hysteresis thresholds | Hiszterézis határok
					lower_limit = dhw_limit - dhw_hysteresis	# Below this → dhw_2 | ez alatt → dhw_2
					upper_limit = dhw_limit + dhw_hysteresis	# Above this → dhw_1 | ez felett → dhw_1

					Domoticz.Debug(
						(f'DEBUG: outside temperature={self.outtemp:.1f}, limit={dhw_limit}, lower={lower_limit:.1f}, upper={upper_limit:.1f}' + " | " + (f"HIBAKERESÉS: külső hőmérséklet={self.outtemp:.1f}, határérték={dhw_limit}, "
						f"alsó határ={lower_limit:.1f}, felső határ={upper_limit:.1f}"))
					)

					# Determine operating mode | --- Üzemmód meghatározás ---
					# 0 = dhw_1 | 0 = dhw_1 (első HMV-üzemmód)
					# 1 = dhw_2 | 1 = dhw_2 (második HMV-üzemmód)

					# Too cold outside → switch to mode 2 | Túl hideg kint → váltás 2-re
					if self.outtemp < lower_limit:
						Domoticz.Debug(
							f"Outdoor temperature {self.outtemp:.1f} below lower limit ({lower_limit:.1f}): dhw_2 | Külső hőmérséklet {self.outtemp:.1f} az alsó határ ({lower_limit:.1f}) alatt: dhw_2"
						)
						self.D_last_mode_state = 1

					# Warm enough outside → switch to mode 1 | Elég meleg kint → váltás 1-re
					elif self.outtemp > upper_limit:
						Domoticz.Debug(
							f"Outdoor temperature {self.outtemp:.1f} above upper limit ({upper_limit:.1f}): dhw_1 | Külső hőmérséklet {self.outtemp:.1f} a felső határ ({upper_limit:.1f}) felett: dhw_1"
						)
						self.D_last_mode_state = 0

					# Hysteresis range → NO switching | Hiszterézis tartomány → NINCS váltás
					else:
						Domoticz.Debug(
							(f'Outside temperature {self.outtemp:.1f} is within the hysteresis band ({lower_limit:.1f}–{upper_limit:.1f}); maintaining mode: {self.D_last_mode_state}' + " | " + (f"Külső hőmérséklet {self.outtemp:.1f} a hiszterézis sávban "
							f"({lower_limit:.1f}–{upper_limit:.1f}) → mód tartása: {self.D_last_mode_state}"))
						)

					# Execution | --- VÉGREHAJTÁS ---
					if self.D_last_mode_state == 0:
						self.dhw_1()
					else:
						self.dhw_2()

				# Switching mode: outdoor dew point | Váltó mód: külső harmatpont
				elif Devices[13].sValue == "50" and not Devices[13].TimedOut:
					Domoticz.Debug("Switching mode based on outdoor dew point (DHW, with hysteresis, unmodified) | Váltó üzemmód külső harmatpont alapján (HMV, hiszterézissel, módosítás nélkül)")

					# Only dew point + compensation + hysteresis matter | Csak dewpoint + kompenzáció + hiszterézis számít
					Tcorr = self.outtemp + dhw_dualkomp

					upper_limit = Tcorr - dhw_hysteresis     # Dew point >= upper_limit → danger → mode 1 | harmatpont >= upper_limit → veszély → 1
					lower_limit = Tcorr + dhw_hysteresis     # Dew point <= lower_limit → very dry → mode 2 | harmatpont <= lower_limit → nagyon száraz → 2

					Domoticz.Debug(
						(f'DHW mode 50 dew-point check: outside temperature={self.outtemp:.1f}, dew point={self.outdewpoint:.1f}, correction={Tcorr:.1f}, lower={lower_limit:.1f}, upper={upper_limit:.1f}' + " | " + (f"HMV 50-es mód harmatpont-ellenőrzése: külső hőmérséklet={self.outtemp:.1f}, "
						f"harmatpont={self.outdewpoint:.1f}, korrekció={Tcorr:.1f}, "
						f"alsó határ={lower_limit:.1f}, felső határ={upper_limit:.1f}"))
					)

					# Decide based only on dew point | --- Csak harmatpont alapján döntünk ---
					# High dew point → mode 1 (safety mode) | Harmatpont magas → 1 (biztonsági üzem)
					if self.outdewpoint >= upper_limit:
						Domoticz.Debug(
							(f'Dew point {self.outdewpoint:.1f} >= upper limit {upper_limit:.1f} → dhw_1' + " | " + (f"Harmatpont {self.outdewpoint:.1f} >= felső határ {upper_limit:.1f} → dhw_1"))
						)
						self.D_last_mode_state = 0

					# Low dew point → mode 2 (favorable conditions) | Harmatpont alacsony → 2 (jó körülmények)
					elif self.outdewpoint <= lower_limit:
						Domoticz.Debug(
							(f'Dew point {self.outdewpoint:.1f} <= lower limit {lower_limit:.1f} → dhw_2' + " | " + (f"Harmatpont {self.outdewpoint:.1f} <= alsó határ {lower_limit:.1f} → dhw_2"))
						)
						self.D_last_mode_state = 1

					# Hysteresis band | Hiszterézis sáv
					else:
						Domoticz.Debug(
							(f'Dew point {self.outdewpoint:.1f} is within the hysteresis band ({lower_limit:.1f}–{upper_limit:.1f}); maintaining mode: {self.D_last_mode_state}' + " | " + (f"Harmatpont {self.outdewpoint:.1f} a hiszterézis tartományban "
							f"({lower_limit:.1f}–{upper_limit:.1f}) → tartjuk: {self.D_last_mode_state}"))
						)

					# Execution | --- Végrehajtás ---
					if self.D_last_mode_state == 0:
						self.dhw_1()
					else:
						self.dhw_2()

				# Dual mode: tank temperature | Dual mód: tartályhőmérséklet
				elif Devices[13].sValue == "60" and not Devices[13].TimedOut:
					Domoticz.Debug(('Dual mode based on tank temperature' + " | " + ("Dual mód tartályhőmérséklet alapján!")))

					# Calculate thresholds | --- Határok kiszámítása ---
					# Lower threshold: activate dual mode | Alsó határ: dual bekapcsolása
					lower_limit = self.M_celhomerseklet - dhw_diff - dhw_hysteresis

					# Upper threshold: switch back to dhw_1 | Felső határ: dhw_1 visszakapcsolása
					upper_limit = self.M_celhomerseklet - dhw_diff + dhw_hysteresis

					Domoticz.Debug(
						(f'DEBUG: tank actual={self.TartalyAktual:.1f}, target={self.M_celhomerseklet}, lower={lower_limit:.1f}, upper={upper_limit:.1f}' + " | " + (f"DEBUG: TartalyAktual={self.TartalyAktual:.1f}, "
						f"cel={self.M_celhomerseklet}, "
						f"alsó határ={lower_limit:.1f}, felső határ={upper_limit:.1f}"))
					)

					# Determine operating mode | --- Üzemmód meghatározása ---
					# 0 = dhw_1 | 0 = dhw_1 (első HMV-üzemmód)
					# 1 = dhw_2 | 1 = dhw_2 (második HMV-üzemmód)

					# Tank too cold → switch to dual mode | Tartály túl hideg → menjünk dual-ra
					if self.TartalyAktual < lower_limit:
						Domoticz.Debug(
							(f'Tank temperature {self.TartalyAktual:.1f} < lower limit ({lower_limit:.1f}) → switch to dual mode' + " | " + (f"Tartályhőmérséklet {self.TartalyAktual:.1f} < alsó határ ({lower_limit:.1f}) → váltás dual üzemmódra"))
						)
						self.D_last_mode_state = 1

					# Tank warm enough → return to dhw_1 | Tartály elég meleg → vissza dhw_1-re
					elif self.TartalyAktual > upper_limit:
						Domoticz.Debug(
							(f'Tank temperature {self.TartalyAktual:.1f} > upper limit ({upper_limit:.1f}) → switch to dhw_1' + " | " + (f"Tartályhőmérséklet {self.TartalyAktual:.1f} > felső határ ({upper_limit:.1f}) → váltás dhw_1 üzemmódra"))
						)
						self.D_last_mode_state = 0

					# Intermediate range → no switching | Köztes tartomány → nincs váltás
					else:
						Domoticz.Debug(
							(f'Tank temperature {self.TartalyAktual:.1f} is within the hysteresis band ({lower_limit:.1f}–{upper_limit:.1f}); maintaining mode: {self.D_last_mode_state}' + " | " + (f"Tartály {self.TartalyAktual:.1f} a hiszterézis sávban "
							f"({lower_limit:.1f}–{upper_limit:.1f}) → üzemmód tartása: {self.D_last_mode_state}"))
						)

					# Execution | --- VÉGREHAJTÁS ---
					if self.D_last_mode_state == 0:
						self.dhw_1()
					else:
						self.dhw_1()
						self.dhw_2()

				# Dual mode: outdoor temperature | Dual mód: külső hőmérséklet
				elif Devices[13].sValue == "70" and not Devices[13].TimedOut:
					Domoticz.Debug(('Dual mode based on outdoor temperature (DHW)' + " | " + ("Dual mód külső hőmérséklet alapján (HMV)!")))

					# Hysteresis thresholds | Hiszterézis határok
					lower_limit = dhw_limit - dhw_hysteresis	# Below this → dhw_2 | ez alatt → dhw_2
					upper_limit = dhw_limit + dhw_hysteresis	# Above this → dhw_1 | ez felett → dhw_1

					Domoticz.Debug(
						(f'DEBUG: outside temperature={self.outtemp:.1f}, limit={dhw_limit}, lower={lower_limit:.1f}, upper={upper_limit:.1f}' + " | " + (f"HIBAKERESÉS: külső hőmérséklet={self.outtemp:.1f}, határérték={dhw_limit}, "
						f"alsó határ={lower_limit:.1f}, felső határ={upper_limit:.1f}"))
					)

					# Determine operating mode | --- Üzemmód meghatározás ---
					# 0 = dhw_1 | 0 = dhw_1 (első HMV-üzemmód)
					# 1 = dhw_2 | 1 = dhw_2 (második HMV-üzemmód)

					# Too cold outside → switch to mode 2 | Túl hideg kint → váltás 2-re
					if self.outtemp < lower_limit:
						Domoticz.Debug(
							(f'Outside temperature {self.outtemp:.1f} < lower limit ({lower_limit:.1f}) → dual mode' + " | " + (f"Külső hőmérséklet {self.outtemp:.1f} < alsó határ ({lower_limit:.1f}) → dual üzemmód"))
						)
						self.D_last_mode_state = 1

					# Warm enough outside → switch to mode 1 | Elég meleg kint → váltás 1-re
					elif self.outtemp > upper_limit:
						Domoticz.Debug(
							(f'Outside temperature {self.outtemp:.1f} > upper limit ({upper_limit:.1f}) → dhw_1' + " | " + (f"Külső hőmérséklet {self.outtemp:.1f} > felső határ ({upper_limit:.1f}) → dhw_1 üzemmód"))
						)
						self.D_last_mode_state = 0

					# Hysteresis range → NO switching | Hiszterézis tartomány → NINCS váltás
					else:
						Domoticz.Debug(
							(f'Outside temperature {self.outtemp:.1f} is within the hysteresis band ({lower_limit:.1f}–{upper_limit:.1f}); maintaining mode: {self.D_last_mode_state}' + " | " + (f"Külső hőmérséklet {self.outtemp:.1f} a hiszterézis sávban "
							f"({lower_limit:.1f}–{upper_limit:.1f}) → mód tartása: {self.D_last_mode_state}"))
						)

					# Execution | --- VÉGREHAJTÁS ---
					if self.D_last_mode_state == 0:
						self.dhw_1()
					else:
						self.dhw_1()
						self.dhw_2()

				# Dual mode: outdoor dew point | Dual mód: külső harmatpont
				elif Devices[13].sValue == "80" and not Devices[13].TimedOut:
					Domoticz.Debug(('Dual mode based on outdoor dew point (DHW)' + " | " + ("Dual mód külső harmatpont alapján (HMV)!")))

					# Only dew point + compensation + hysteresis matter | Csak dewpoint + kompenzáció + hiszterézis számít
					Tcorr = self.outtemp + dhw_dualkomp

					upper_limit = Tcorr - dhw_hysteresis     # Dew point >= upper_limit → danger → mode 1 | harmatpont >= upper_limit → veszély → 1
					lower_limit = Tcorr + dhw_hysteresis     # Dew point <= lower_limit → very dry → mode 2 | harmatpont <= lower_limit → nagyon száraz → 2

					Domoticz.Debug(
						(f'DHW mode 50 dew-point check: outside temperature={self.outtemp:.1f}, dew point={self.outdewpoint:.1f}, correction={Tcorr:.1f}, lower={lower_limit:.1f}, upper={upper_limit:.1f}' + " | " + (f"HMV 50-es mód harmatpont-ellenőrzése: külső hőmérséklet={self.outtemp:.1f}, "
						f"harmatpont={self.outdewpoint:.1f}, korrekció={Tcorr:.1f}, "
						f"alsó határ={lower_limit:.1f}, felső határ={upper_limit:.1f}"))
					)

					# Decide based only on dew point | --- Csak harmatpont alapján döntünk ---
					# High dew point → mode 1 (safety mode) | Harmatpont magas → 1 (biztonsági üzem)
					if self.outdewpoint >= upper_limit:
						Domoticz.Debug(
							(f'Dew point {self.outdewpoint:.1f} >= upper limit {upper_limit:.1f} → dhw_1' + " | " + (f"Harmatpont {self.outdewpoint:.1f} >= felső határ {upper_limit:.1f} → dhw_1"))
						)
						self.D_last_mode_state = 0

					# Low dew point → mode 2 (favorable conditions) | Harmatpont alacsony → 2 (jó körülmények)
					elif self.outdewpoint <= lower_limit:
						Domoticz.Debug(
							(f'Dew point {self.outdewpoint:.1f} <= lower limit {lower_limit:.1f} → dual mode' + " | " + (f"Harmatpont {self.outdewpoint:.1f} <= alsó határ {lower_limit:.1f} → dual"))
						)
						self.D_last_mode_state = 1

					# Hysteresis band | Hiszterézis sáv
					else:
						Domoticz.Debug(
							(f'Dew point {self.outdewpoint:.1f} is within the hysteresis band ({lower_limit:.1f}–{upper_limit:.1f}); maintaining mode: {self.D_last_mode_state}' + " | " + (f"Harmatpont {self.outdewpoint:.1f} a hiszterézis tartományban "
							f"({lower_limit:.1f}–{upper_limit:.1f}) → tartjuk: {self.D_last_mode_state}"))
						)

					# Execution | --- VÉGREHAJTÁS ---
					if self.D_last_mode_state == 0:
						self.dhw_1()
					else:
						self.dhw_1()
						self.dhw_2()

				# Saver mode: temperature + outdoor temperature | Saver mód: hőmérséklet + külsőhőmérséklet
				elif Devices[13].sValue == "90" and not Devices[13].TimedOut:
					Domoticz.Debug(('Saver mode based on tank temperature and outdoor temperature (DHW)' + " | " + ("Saver mód tartályhőmérséklet + külső hőmérséklet alapján (HMV)!")))

					# Tank hysteresis thresholds | --- Tartály hiszterézis határok ---
					t_lower = self.M_celhomerseklet - dhw_diff - dhw_hysteresis	# Below this → cold → mode 2 requested | ez alatt → hideg → igény a 2-es módra
					t_upper = self.M_celhomerseklet - dhw_diff + dhw_hysteresis	# Above this → warm enough → mode 1 | ez felett → elég meleg → 1-es mód

					# Outdoor temperature hysteresis thresholds | --- Külső hőmérséklet hiszterézis határok ---
					o_lower = dhw_limit - dhw_hysteresis	# Below this → cold outdoors → mode 2 permitted | ez alatt → kint is hideg → engedi 2-es módot
					o_upper = dhw_limit + dhw_hysteresis	# Above this → too warm outdoors → return to mode 1 | ez felett → kint túl meleg → vissza 1-esre

					Domoticz.Debug(
						(f'DEBUG: tank={self.TartalyAktual:.1f}, tank lower={t_lower:.1f}, tank upper={t_upper:.1f}, outside temperature={self.outtemp:.1f}, outdoor lower={o_lower:.1f}, outdoor upper={o_upper:.1f}' + " | " + (f"DEBUG: Tartaly={self.TartalyAktual:.1f}, "
						f"t_lower={t_lower:.1f}, t_upper={t_upper:.1f}, "
						f"outtemp={self.outtemp:.1f}, o_lower={o_lower:.1f}, o_upper={o_upper:.1f}"))
					)

					# Determine operating mode | --- Üzemmód meghatározása ---
					# 0 = dhw_1 (normal) | 0 = dhw_1 (normál)
					# 1 = dhw_2 (saver + auxiliary) | 1 = dhw_2 (takarékos + kiegészítő)

					# Conditions for mode 2: tank cold AND outdoor conditions permit | Feltételek a 2-es módra: tartály hideg ÉS kint engedi
					if self.TartalyAktual < t_lower and self.outtemp < o_lower:
						Domoticz.Debug(
							(f'Tank cold ({self.TartalyAktual:.1f} < {t_lower:.1f}) AND outside cold ({self.outtemp:.1f} < {o_lower:.1f}) → dhw_2' + " | " + (f"Tartály hideg ({self.TartalyAktual:.1f} < {t_lower:.1f}) "
							f"ÉS kint hideg ({self.outtemp:.1f} < {o_lower:.1f}) → dhw_2"))
						)
						self.D_last_mode_state = 1

					# Condition to revert → tank sufficiently warm (outdoor temperature ignored) | Feltétel a visszaállásra → elég meleg tartály (külsőt ilyenkor nem vesszük figyelembe)
					elif self.TartalyAktual > t_upper:
						Domoticz.Debug(
							(f'Tank sufficiently warm ({self.TartalyAktual:.1f} > {t_upper:.1f}) → dhw_1' + " | " + (f"Tartály elég meleg ({self.TartalyAktual:.1f} > {t_upper:.1f}) → dhw_1"))
						)
						self.D_last_mode_state = 0

					# Hysteresis range → NO switching | Hiszterézis tartomány → NINCS váltás
					else:
						Domoticz.Debug(
							(f'Within hysteresis band → maintaining mode: {self.D_last_mode_state}' + " | " + (f"Hiszterézis tartományban → tartjuk: {self.D_last_mode_state}"))
						)

					# Execution | --- VÉGREHAJTÁS ---
					if self.D_last_mode_state == 0:
						self.dhw_1()
					else:
						self.dhw_2()

				# Saver mode: hőmérséklet + outdoor dew point | Saver mód: hőmérséklet + külső harmatpont
				elif Devices[13].sValue == "100" and not Devices[13].TimedOut:
					Domoticz.Debug(('Saver mode (DHW): switch if source 1 would freeze due to dew-point conditions' + " | " + ("Saver mód (HMV): váltás, ha az 1-es lefagyna a harmattól!")))

					# Adjusted outdoor temperature | --- Korrigált külső hőmérséklet ---
					Tcorr = self.outtemp + dhw_dualkomp

					# Dew point hysteresis thresholds | --- Harmatpont hiszterézis határok ---
					# Freezing risk occurs when dewpoint ≥ Tcorr | fagyveszély akkor van, ha dewpoint ≥ Tcorr
					upper_limit = Tcorr			# Above this → danger → switch to mode 2 | fölötte → veszély → 2-re váltás
					lower_limit = Tcorr - dhw_hysteresis	# Below this → safe → return to mode 1 | alatta → biztonság → vissza 1-re

					Domoticz.Debug(
						(f'DEBUG: dew point={self.outdewpoint:.1f}, correction={Tcorr:.1f}, lower={lower_limit:.1f}, upper={upper_limit:.1f}' + " | " + (f"DEBUG: harmatpont={self.outdewpoint:.1f}, korrekció={Tcorr:.1f}, "
						f"alsó határ={lower_limit:.1f}, felső határ={upper_limit:.1f}"))
					)

					# Operating mode state | --- Üzemmód állapota ---
					# 0 = dhw_1 (base) | 0 = dhw_1 (alap)
					# 1 = dhw_2 (safety / auxiliary) | 1 = dhw_2 (biztonsági / kiegészítő)
					# THE ONLY REASON TO SWITCH: mode 1 would freeze! | A VÁLTÁS EGYETLEN OKA: az 1-es lefagyna!

					# → Freezing risk: mode 1 is NOT safe → must switch to mode 2 | → Fagyveszély: az 1-es üzem NEM biztonságos → kötelező váltás 2-re
					if self.outdewpoint >= upper_limit:
						Domoticz.Debug(
							(f'Dew point {self.outdewpoint:.1f} >= critical limit {upper_limit:.1f} → source 1 would freeze → dhw_2' + " | " + (f"Harmatpont {self.outdewpoint:.1f} >= kritikus határ {upper_limit:.1f} → "
							f"1-es lefagyna → dhw_2"))
						)
						self.D_last_mode_state = 1

					# → Safe: mode 1 can be used again → return to mode 1 | → Biztonság: az 1-es üzem újra használható → vissza 1-re
					elif self.outdewpoint <= lower_limit:
						Domoticz.Debug(
							(f'Dew point {self.outdewpoint:.1f} <= safety limit {lower_limit:.1f} → source 1 safe again → dhw_1' + " | " + (f"Harmatpont {self.outdewpoint:.1f} <= biztonsági határ {lower_limit:.1f} → "
							f"1-es újra biztonságos → dhw_1"))
						)
						self.D_last_mode_state = 0

					# → Hysteresis range | → Hiszterézis tartomány
					else:
						Domoticz.Debug(
							(f'Dew point {self.outdewpoint:.1f} within {lower_limit:.1f}–{upper_limit:.1f} → maintaining mode: {self.D_last_mode_state}' + " | " + (f"Harmatpont {self.outdewpoint:.1f} a sávban {lower_limit:.1f}–{upper_limit:.1f} → "
							f"üzemmód tartása: {self.D_last_mode_state}"))
						)

					# Execution | --- VÉGREHAJTÁS ---
					if self.D_last_mode_state == 0:
						self.dhw_1()
					else:
						self.dhw_2()

								# Switching mode (based on 500 W energy threshold, with hysteresis) | --- Váltó mód (500W energetika alapján, hiszterézissel) ---
				elif Devices[13].sValue == "110" and not Devices[13].TimedOut:
					Domoticz.Debug(('BUFFER switching mode (500 W, percentage hysteresis)' + " | " + ("Váltó mód puffer (500W, % hiszterézis)")))
					power = self.aktual_watt
					base = 500
					if self.D_last_mode_state == 0:
						power += base
					h = int(base * int(Devices[85].sValue) / 100)
					Domoticz.Debug(f"Power={power} W, base={base} W, hysteresis=±{h} W | Teljesítmény={power} W, alapérték={base} W, hiszterézis=±{h} W")

					if power >= base + h:
						self.D_last_mode_state = 0
					elif power <= base - h:
						self.D_last_mode_state = 1

					if self.D_last_mode_state == 0:
						self.dhw_1()
					else:
						self.dhw_2()

				# Switching mode (based on 1000 W energy threshold, with hysteresis) | --- Váltó mód (1000W energetika alapján, hiszterézissel) ---
				elif Devices[13].sValue == "120" and not Devices[13].TimedOut:
					Domoticz.Debug(('BUFFER switching mode (1000 W, percentage hysteresis)' + " | " + ("Váltó mód puffer (1000W, % hiszterézis)")))
					power = self.aktual_watt
					base = 1000
					if self.D_last_mode_state == 0:
						power += base
					h = int(base * int(Devices[85].sValue) / 100)
					Domoticz.Debug(f"Power={power} W, base={base} W, hysteresis=±{h} W | Teljesítmény={power} W, alapérték={base} W, hiszterézis=±{h} W")

					if power >= base + h:
						self.D_last_mode_state = 0
					elif power <= base - h:
						self.D_last_mode_state = 1

					if self.D_last_mode_state == 0:
						self.dhw_1()
					else:
						self.dhw_2()

				# Switching mode (based on 1500 W energy threshold, with hysteresis) | --- Váltó mód (1500W energetika alapján, hiszterézissel) ---
				elif Devices[13].sValue == "130" and not Devices[13].TimedOut:
					Domoticz.Debug(('BUFFER switching mode (1500 W, percentage hysteresis)' + " | " + ("Váltó mód puffer (1500W, % hiszterézis)")))
					power = self.aktual_watt
					base = 1500
					if self.D_last_mode_state == 0:
						power += base
					h = int(base * int(Devices[85].sValue) / 100)
					Domoticz.Debug(f"Power={power} W, base={base} W, hysteresis=±{h} W | Teljesítmény={power} W, alapérték={base} W, hiszterézis=±{h} W")

					if power >= base + h:
						self.D_last_mode_state = 0
					elif power <= base - h:
						self.D_last_mode_state = 1

					if self.D_last_mode_state == 0:
						self.dhw_1()
					else:
						self.dhw_2()

				# Switching mode (based on 2000 W energy threshold, with hysteresis) | --- Váltó mód (2000W energetika alapján, hiszterézissel) ---
				elif Devices[13].sValue == "140" and not Devices[13].TimedOut:
					Domoticz.Debug(('BUFFER switching mode (2000 W, percentage hysteresis)' + " | " + ("Váltó mód puffer (2000W, % hiszterézis)")))
					power = self.aktual_watt
					base = 2000
					if self.D_last_mode_state == 0:
						power += base
					h = int(base * int(Devices[85].sValue) / 100)
					Domoticz.Debug(f"Power={power} W, base={base} W, hysteresis=±{h} W | Teljesítmény={power} W, alapérték={base} W, hiszterézis=±{h} W")

					if power >= base + h:
						self.D_last_mode_state = 0
					elif power <= base - h:
						self.D_last_mode_state = 1

					if self.D_last_mode_state == 0:
						self.dhw_1()
					else:
						self.dhw_2()

				# Switching mode (based on 3000 W energy threshold, with hysteresis) | --- Váltó mód (3000W energetika alapján, hiszterézissel) ---
				elif Devices[13].sValue == "150" and not Devices[13].TimedOut:
					Domoticz.Debug(('BUFFER switching mode (3000 W, percentage hysteresis)' + " | " + ("Váltó mód puffer (3000W, % hiszterézis)")))
					power = self.aktual_watt
					base = 3000
					if self.D_last_mode_state == 0:
						power += base
					h = int(base * int(Devices[85].sValue) / 100)
					Domoticz.Debug(f"Power={power} W, base={base} W, hysteresis=±{h} W | Teljesítmény={power} W, alapérték={base} W, hiszterézis=±{h} W")

					if power >= base + h:
						self.D_last_mode_state = 0
					elif power <= base - h:
						self.D_last_mode_state = 1

					if self.D_last_mode_state == 0:
						self.dhw_1()
					else:
						self.dhw_2()

				# Switching mode (based on 4000 W energy threshold, with hysteresis) | --- Váltó mód (4000W energetika alapján, hiszterézissel) ---
				elif Devices[13].sValue == "160" and not Devices[13].TimedOut:
					Domoticz.Debug(('BUFFER switching mode (4000 W, percentage hysteresis)' + " | " + ("Váltó mód puffer (4000W, % hiszterézis)")))
					power = self.aktual_watt
					base = 4000
					if self.D_last_mode_state == 0:
						power += base
					h = int(base * int(Devices[85].sValue) / 100)
					Domoticz.Debug(f"Power={power} W, base={base} W, hysteresis=±{h} W | Teljesítmény={power} W, alapérték={base} W, hiszterézis=±{h} W")

					if power >= base + h:
						self.D_last_mode_state = 0
					elif power <= base - h:
						self.D_last_mode_state = 1

					if self.D_last_mode_state == 0:
						self.dhw_1()
					else:
						self.dhw_2()

				# Switching mode (based on 5000 W energy threshold, with hysteresis) | --- Váltó mód (5000W energetika alapján, hiszterézissel) ---
				elif Devices[13].sValue == "170" and not Devices[13].TimedOut:
					Domoticz.Debug(('BUFFER switching mode (5000 W, percentage hysteresis)' + " | " + ("Váltó mód puffer (5000W, % hiszterézis)")))
					power = self.aktual_watt
					base = 5000
					if self.D_last_mode_state == 0:
						power += base
					h = int(base * int(Devices[85].sValue) / 100)
					Domoticz.Debug(f"Power={power} W, base={base} W, hysteresis=±{h} W | Teljesítmény={power} W, alapérték={base} W, hiszterézis=±{h} W")

					if power >= base + h:
						self.D_last_mode_state = 0
					elif power <= base - h:
						self.D_last_mode_state = 1

					if self.D_last_mode_state == 0:
						self.dhw_1()
					else:
						self.dhw_2()

				# Dual mode (based on 500 W energy threshold, with hysteresis) | --- Dual mód (500W energetika alapján, hiszterézissel) ---
				elif Devices[13].sValue == "180" and not Devices[13].TimedOut:
					Domoticz.Debug(('BUFFER dual mode (500 W, percentage hysteresis)' + " | " + ("Dual mód puffer (500W, % hiszterézis)")))
					power = self.aktual_watt
					base = 500
					if self.D_last_mode_state == 0:
						power += base
					h = int(base * int(Devices[85].sValue) / 100)
					Domoticz.Debug(f"Power={power} W, base={base} W, hysteresis=±{h} W | Teljesítmény={power} W, alapérték={base} W, hiszterézis=±{h} W")

					if power >= base + h:
						self.D_last_mode_state = 0
					elif power <= base - h:
						self.D_last_mode_state = 1

					if self.D_last_mode_state == 0:
						self.dhw_1()
						self.dhw_2()
					else:
						self.dhw_2()

				# Dual mode (based on 1000 W energy threshold, with hysteresis) | --- Dual mód (1000W energetika alapján, hiszterézissel) ---
				elif Devices[13].sValue == "190" and not Devices[13].TimedOut:
					Domoticz.Debug(('BUFFER dual mode (1000 W, percentage hysteresis)' + " | " + ("Dual mód puffer (1000W, % hiszterézis)")))
					power = self.aktual_watt
					base = 1000
					if self.D_last_mode_state == 0:
						power += base
					h = int(base * int(Devices[85].sValue) / 100)
					Domoticz.Debug(f"Power={power} W, base={base} W, hysteresis=±{h} W | Teljesítmény={power} W, alapérték={base} W, hiszterézis=±{h} W")

					if power >= base + h:
						self.D_last_mode_state = 0
					elif power <= base - h:
						self.D_last_mode_state = 1

					if self.D_last_mode_state == 0:
						self.dhw_1()
						self.dhw_2()
					else:
						self.dhw_2()

				# Dual mode (based on 1500 W energy threshold, with hysteresis) | --- Dual mód (1500W energetika alapján, hiszterézissel) ---
				elif Devices[13].sValue == "200" and not Devices[13].TimedOut:
					Domoticz.Debug(('BUFFER dual mode (1500 W, percentage hysteresis)' + " | " + ("Dual mód puffer (1500W, % hiszterézis)")))
					power = self.aktual_watt
					base = 1500
					if self.D_last_mode_state == 0:
						power += base
					h = int(base * int(Devices[85].sValue) / 100)
					Domoticz.Debug(f"Power={power} W, base={base} W, hysteresis=±{h} W | Teljesítmény={power} W, alapérték={base} W, hiszterézis=±{h} W")

					if power >= base + h:
						self.D_last_mode_state = 0
					elif power <= base - h:
						self.D_last_mode_state = 1

					if self.D_last_mode_state == 0:
						self.dhw_1()
						self.dhw_2()
					else:
						self.dhw_2()

				# Dual mode (based on 2000 W energy threshold, with hysteresis) | --- Dual mód (2000W energetika alapján, hiszterézissel) ---
				elif Devices[13].sValue == "210" and not Devices[13].TimedOut:
					Domoticz.Debug(('BUFFER dual mode (2000 W, percentage hysteresis)' + " | " + ("Dual mód puffer (2000W, % hiszterézis)")))
					power = self.aktual_watt
					base = 2000
					if self.D_last_mode_state == 0:
						power += base
					h = int(base * int(Devices[85].sValue) / 100)
					Domoticz.Debug(f"Power={power} W, base={base} W, hysteresis=±{h} W | Teljesítmény={power} W, alapérték={base} W, hiszterézis=±{h} W")

					if power >= base + h:
						self.D_last_mode_state = 0
					elif power <= base - h:
						self.D_last_mode_state = 1

					if self.D_last_mode_state == 0:
						self.dhw_1()
						self.dhw_2()
					else:
						self.dhw_2()

				# Dual mode (based on 3000 W energy threshold, with hysteresis) | --- Dual mód (3000W energetika alapján, hiszterézissel) ---
				elif Devices[13].sValue == "220" and not Devices[13].TimedOut:
					Domoticz.Debug(('BUFFER dual mode (3000 W, percentage hysteresis)' + " | " + ("Dual mód puffer (3000W, % hiszterézis)")))
					power = self.aktual_watt
					base = 3000
					if self.D_last_mode_state == 0:
						power += base
					h = int(base * int(Devices[85].sValue) / 100)
					Domoticz.Debug(f"Power={power} W, base={base} W, hysteresis=±{h} W | Teljesítmény={power} W, alapérték={base} W, hiszterézis=±{h} W")

					if power >= base + h:
						self.D_last_mode_state = 0
					elif power <= base - h:
						self.D_last_mode_state = 1

					if self.D_last_mode_state == 0:
						self.dhw_1()
						self.dhw_2()
					else:
						self.dhw_2()

				# Dual mode (based on 4000 W energy threshold, with hysteresis) | --- Dual mód (4000W energetika alapján, hiszterézissel) ---
				elif Devices[13].sValue == "230" and not Devices[13].TimedOut:
					Domoticz.Debug(('BUFFER dual mode (4000 W, percentage hysteresis)' + " | " + ("Dual mód puffer (4000W, % hiszterézis)")))
					power = self.aktual_watt
					base = 4000
					if self.D_last_mode_state == 0:
						power += base
					h = int(base * int(Devices[85].sValue) / 100)
					Domoticz.Debug(f"Power={power} W, base={base} W, hysteresis=±{h} W | Teljesítmény={power} W, alapérték={base} W, hiszterézis=±{h} W")

					if power >= base + h:
						self.D_last_mode_state = 0
					elif power <= base - h:
						self.D_last_mode_state = 1

					if self.D_last_mode_state == 0:
						self.dhw_1()
						self.dhw_2()
					else:
						self.dhw_2()

				# Dual mode (based on 5000 W energy threshold, with hysteresis) | --- Dual mód (5000W energetika alapján, hiszterézissel) ---
				elif Devices[13].sValue == "240" and not Devices[13].TimedOut:
					Domoticz.Debug(('BUFFER dual mode (5000 W, percentage hysteresis)' + " | " + ("Dual mód puffer (5000W, % hiszterézis)")))
					power = self.aktual_watt
					base = 5000
					if self.D_last_mode_state == 0:
						power += base
					h = int(base * int(Devices[85].sValue) / 100)
					Domoticz.Debug(f"Power={power} W, base={base} W, hysteresis=±{h} W | Teljesítmény={power} W, alapérték={base} W, hiszterézis=±{h} W")

					if power >= base + h:
						self.D_last_mode_state = 0
					elif power <= base - h:
						self.D_last_mode_state = 1

					if self.D_last_mode_state == 0:
						self.dhw_1()
						self.dhw_2()
					else:
						self.dhw_2()

			
			else :
				Domoticz.Debug(('DHW OFF: switching everything off' + " | " + ("HMV Off, minden kikapcsolva!")))
				self.switchElsodleges_M(False)
				self.switchMasodlagos_M(False)
				self.switchElsodleges_E(False)
				self.switchMasodlagos_E(False)
				Devices[21].Update(nValue=0, sValue=str(0), TimedOut=False)
				self.Internals['power_dhw_consumption'] = 0
				saveUserVar(self)

# Cooling-heating control | Hűtés–fűtés vezérlése

			if Devices[1].sValue == "0" or (Devices[1].Used == 0):  # Heating disabled | A fűtés kikapcsolva
				Domoticz.Debug(('Heating switches OFF' + " | " + ("Fűtés kapcsolók Off!")))
				self.switchElsodleges_F(False)
				self.switchMasodlagos_F(False)

				for i in range(1, 13):
					self.switchzone_F(i, False)
					self.send_AC_command(i, "F", "Off")

			if Devices[2].sValue == "0" or (Devices[2].Used == 0):  # Cooling disabled | A hűtés kikapcsolva
				Domoticz.Debug(('Cooling switches OFF' + " | " + ("Hűtés kapcsolók Off!")))
				self.switchElsodleges_H(False)
				self.switchMasodlagos_H(False)

				for i in range(1, 13):
					self.switchzone_H(i, False)
					self.send_AC_command(i, "H", "Off")

			if self.heating_colling :

				if Devices[58].sValue == "10" and Devices[1].sValue != "0" and Devices[1].Used == 1 and Devices[1].TimedOut == False :
					self.HeatMode()
				
				elif Devices[58].sValue == "20" and Devices[22].sValue != "0" and Devices[22].Used == 1 and Devices[22].TimedOut == False :
					self.CoolMode()
					
				else:
					Domoticz.Debug(('No heating or cooling demand' + " | " + ("Nincs hűtés-fűtés feladat")))
					self.switchElsodleges_F(False)
					self.switchMasodlagos_F(False)
					self.switchElsodleges_H(False)
					self.switchMasodlagos_H(False)

					for i in range(1, 13):
						self.switchzone_F(i, False)
						self.send_AC_command(i, "F", "Off")
						self.switchzone_H(i, False)
						self.send_AC_command(i, "H", "Off")

			else :
				Domoticz.Debug(('Heating and cooling OFF' + " | " + ("Fűtés és hűtés kikapcsolva")))
				self.switchElsodleges_F(False)
				self.switchMasodlagos_F(False)
				self.switchElsodleges_H(False)
				self.switchMasodlagos_H(False)

				for i in range(1, 13):
					self.switchzone_F(i, False)
					self.send_AC_command(i, "F", "Off")
					self.switchzone_H(i, False)
					self.send_AC_command(i, "H", "Off")


# Buffer heating mode | Puffer fűtési üzemmódja

			if self.buffer and Devices[104].sValue != "0" and (Devices[104].Used == 1) :
				
				Domoticz.Debug(('Buffer mode and operation enabled' + " | " + ("Puffer mód és üzem bekapcsolva")))

				self.buffer_temp_read()

				buffer_limit = float(Devices[95].sValue)      # Switching threshold for buffer device 2 | PUFFER 2. készülék kapcsolási határértéke
				buffer_diff = float(Devices[109].sValue)       # Buffer dual temperature differential | Puffer dual hőmérséklet-különbsége
				buffer_dualkomp = float(Devices[223].sValue)    # Buffer dew-point compensation | Puffer harmatpont-kompenzációja
				buffer_hysteresis = float(Devices[18].sValue)  # Hysteresis | Hiszterézis

				Domoticz.Debug((f'BUFFER parameters:' + " | " + (f"PUFFER paraméterek:")))
				Domoticz.Debug((f'    Tank = {self.PufferAktual:.1f} °C' + " | " + (f"    Tartály = {self.PufferAktual:.1f} °C")))
				Domoticz.Debug((f'    Target = {self.P_celhomerseklet:.1f} °C' + " | " + (f"    Cél = {self.P_celhomerseklet:.1f} °C")))
				Domoticz.Debug((f'    Outdoor temperature = {self.outtemp:.1f} °C' + " | " + (f"    Külső hőmérséklet = {self.outtemp:.1f} °C")))
				Domoticz.Debug((f'    Dew point = {self.outdewpoint:.1f} °C' + " | " + (f"    Harmatpont = {self.outdewpoint:.1f} °C")))
				Domoticz.Debug((f'    Buffer dual correction = {buffer_dualkomp:.1f}' + " | " + (f"    Puffer dual korrekció = {buffer_dualkomp:.1f}")))
				Domoticz.Debug((f'    Hysteresis = {buffer_hysteresis:.1f}' + " | " + (f"    Hiszterézis = {buffer_hysteresis:.1f}")))
				Domoticz.Debug((f'    Outdoor limit = {buffer_limit:.1f}' + " | " + (f"    Külső határérték = {buffer_limit:.1f}")))

				# Primary mode HEATING | Elsődleges mód FŰTÉS
				if Devices[104].sValue == "10" and not Devices[104].TimedOut:
					Domoticz.Debug(('Primary BUFFER mode' + " | " + ("Elsődleges PUFFER mód!")))
					self.buffer_1()

				# Secondary mode HEATING | Másodlagos mód FŰTÉS
				elif Devices[104].sValue == "20" and not Devices[104].TimedOut:
					Domoticz.Debug(('Secondary BUFFER mode' + " | " + ("Másodlagos PUFFER mód!")))
					self.buffer_2()

				# Switching mode: tank temperature HEATING | Váltó mód: tartályhőmérséklet FŰTÉS
				elif Devices[104].sValue == "30" and not Devices[104].TimedOut:
					Domoticz.Debug(('Switching mode based on tank temperature' + " | " + ("Váltó mód tartályhőmérséklet alapján!")))

					# Calculate thresholds | --- Határok kiszámítása ---
					# Lower threshold: enable buffer_2 | Alsó határ: buffer_2 bekapcsolása
					lower_limit = self.P_celhomerseklet - buffer_diff - buffer_hysteresis

					# Upper threshold: switch back to buffer_1 | Felső határ: buffer_1 visszakapcsolása
					upper_limit = self.P_celhomerseklet - buffer_diff + buffer_hysteresis

					Domoticz.Debug(
						(f'DEBUG: tank actual={self.PufferAktual:.1f}, target={self.P_celhomerseklet}, lower={lower_limit:.1f}, upper={upper_limit:.1f}' + " | " + (f"DEBUG: TartalyAktual={self.PufferAktual:.1f}, "
						f"cel={self.P_celhomerseklet}, "
						f"alsó határ={lower_limit:.1f}, felső határ={upper_limit:.1f}"))
					)

					# Determine operating mode | --- Üzemmód meghatározása ---
					# 0 = buffer_1 | 0 = buffer_1 (első pufferüzemmód)
					# 1 = buffer_2 | 1 = buffer_2 (második pufferüzemmód)

					# Tank too cold: switch to buffer_2 | A tartály túl hideg, váltás buffer_2-re
					if self.PufferAktual < lower_limit:
						Domoticz.Debug(
							(f'Tank temperature {self.PufferAktual:.1f} < lower limit ({lower_limit:.1f}) → switch to buffer_2' + " | " + (f"Tartályhőmérséklet {self.PufferAktual:.1f} < alsó határ ({lower_limit:.1f}) → váltás buffer_2 módra"))
						)
						self.P_last_mode_state = 1

					# Tank warm enough: switch back to buffer_1 | A tartály elég meleg, visszaváltás buffer_1-re
					elif self.PufferAktual > upper_limit:
						Domoticz.Debug(
							(f'Tank temperature {self.PufferAktual:.1f} > upper limit ({upper_limit:.1f}) → switch to buffer_1' + " | " + (f"Tartályhőmérséklet {self.PufferAktual:.1f} > felső határ ({upper_limit:.1f}) → váltás buffer_1 módra"))
						)
						self.P_last_mode_state = 0

					# Intermediate range → no switching | Köztes tartomány → nincs váltás
					else:
						Domoticz.Debug(
							(f'Tank temperature {self.PufferAktual:.1f} is within hysteresis band ({lower_limit:.1f}–{upper_limit:.1f}); maintaining mode: {self.P_last_mode_state}' + " | " + (f"Tartály {self.PufferAktual:.1f} a hiszterézis sávban "
							f"({lower_limit:.1f}–{upper_limit:.1f}) → üzemmód tartása: {self.P_last_mode_state}"))
						)

					# Execution | --- VÉGREHAJTÁS ---
					if self.P_last_mode_state == 0:
						self.buffer_1()
					else:
						self.buffer_2()

				# Switching mode: outdoor temperature HEATING | Váltó mód: külső hőmérséklet FŰTÉS
				elif Devices[104].sValue == "40" and not Devices[104].TimedOut:
					Domoticz.Debug(('Switching mode based on outdoor temperature' + " | " + ("Váltó mód külső hőmérséklet alapján!")))

					# Hysteresis thresholds | Hiszterézis határok
					lower_limit = buffer_limit - buffer_hysteresis	# Below this: buffer_2 | Ez alatt: buffer_2
					upper_limit = buffer_limit + buffer_hysteresis	# Above this: buffer_1 | Ez felett: buffer_1

					Domoticz.Debug(
						(f'DEBUG: outside temperature={self.outtemp:.1f}, limit={buffer_limit}, lower={lower_limit:.1f}, upper={upper_limit:.1f}' + " | " + (f"DEBUG: outtemp={self.outtemp:.1f}, limit={buffer_limit}, "
						f"alsó határ={lower_limit:.1f}, felső határ={upper_limit:.1f}"))
					)

					# Determine operating mode | --- Üzemmód meghatározás ---
					# 0 = buffer_1 | 0 = buffer_1 (első pufferüzemmód)
					# 1 = buffer_2 | 1 = buffer_2 (második pufferüzemmód)

					# Too cold outside → switch to mode 2 | Túl hideg kint → váltás 2-re
					if self.outtemp < lower_limit:
						Domoticz.Debug(
							(f'Outside temperature {self.outtemp:.1f} < lower limit ({lower_limit:.1f}) → buffer_2' + " | " + (f"Külső hőmérséklet {self.outtemp:.1f} < alsó határ ({lower_limit:.1f}) → buffer_2 mód"))
						)
						self.P_last_mode_state = 1

					# Warm enough outside → switch to mode 1 | Elég meleg kint → váltás 1-re
					elif self.outtemp > upper_limit:
						Domoticz.Debug(
							(f'Outside temperature {self.outtemp:.1f} > upper limit ({upper_limit:.1f}) → buffer_1' + " | " + (f"Külső hőmérséklet {self.outtemp:.1f} > felső határ ({upper_limit:.1f}) → buffer_1 mód"))
						)
						self.P_last_mode_state = 0

					# Hysteresis range → NO switching | Hiszterézis tartomány → NINCS váltás
					else:
						Domoticz.Debug(
							(f'Outside temperature {self.outtemp:.1f} is within hysteresis band ({lower_limit:.1f}–{upper_limit:.1f}); maintaining mode: {self.P_last_mode_state}' + " | " + (f"Külső hőmérséklet {self.outtemp:.1f} a hiszterézis sávban "
							f"({lower_limit:.1f}–{upper_limit:.1f}) → mód tartása: {self.P_last_mode_state}"))
						)

					# Execution | --- VÉGREHAJTÁS ---
					if self.P_last_mode_state == 0:
						self.buffer_1()
					else:
						self.buffer_2()

				# Switching mode: outdoor dew point HEATING | Váltó mód: külső harmatpont FŰTÉS
				elif Devices[104].sValue == "50" and not Devices[104].TimedOut:
					Domoticz.Debug(('Switching mode based on outdoor dew point (BUFFER, with hysteresis, unmodified)' + " | " + ("Váltó mód külső harmatpont alapján (PUFFER, hiszterézissel, módosítás nélkül)!")))

					# Only dew point + compensation + hysteresis matter | Csak dewpoint + kompenzáció + hiszterézis számít
					Tcorr = self.outtemp + buffer_dualkomp

					upper_limit = Tcorr - buffer_hysteresis     # Dew point >= upper_limit → danger → mode 1 | harmatpont >= upper_limit → veszély → 1
					lower_limit = Tcorr + buffer_hysteresis     # Dew point <= lower_limit → very dry → mode 2 | harmatpont <= lower_limit → nagyon száraz → 2

					Domoticz.Debug(
						(f'BUFFER mode 50 dew-point check: outdoor temperature={self.outtemp:.1f}, dew point={self.outdewpoint:.1f}, correction={Tcorr:.1f}, lower={lower_limit:.1f}, upper={upper_limit:.1f}' + " | " + (f"PUFFER 50-es mód harmatpont-ellenőrzése: külső hőmérséklet={self.outtemp:.1f}, "
						f"harmatpont={self.outdewpoint:.1f}, korrekció={Tcorr:.1f}, "
						f"alsó határ={lower_limit:.1f}, felső határ={upper_limit:.1f}"))
					)

					# Decide based only on dew point | --- Csak harmatpont alapján döntünk ---
					# High dew point → mode 1 (safety mode) | Harmatpont magas → 1 (biztonsági üzem)
					if self.outdewpoint >= upper_limit:
						Domoticz.Debug(
							(f'Dew point {self.outdewpoint:.1f} >= upper limit {upper_limit:.1f} → buffer_1' + " | " + (f"Harmatpont {self.outdewpoint:.1f} >= felső határ {upper_limit:.1f} → buffer_1"))
						)
						self.P_last_mode_state = 0

					# Low dew point → mode 2 (favorable conditions) | Harmatpont alacsony → 2 (jó körülmények)
					elif self.outdewpoint <= lower_limit:
						Domoticz.Debug(
							(f'Dew point {self.outdewpoint:.1f} <= lower limit {lower_limit:.1f} → buffer_2' + " | " + (f"Harmatpont {self.outdewpoint:.1f} <= alsó határ {lower_limit:.1f} → buffer_2"))
						)
						self.P_last_mode_state = 1

					# Hysteresis band | Hiszterézis sáv
					else:
						Domoticz.Debug(
							(f'Dew point {self.outdewpoint:.1f} is within hysteresis band ({lower_limit:.1f}–{upper_limit:.1f}); maintaining mode: {self.P_last_mode_state}' + " | " + (f"Harmatpont {self.outdewpoint:.1f} a hiszterézis tartományban "
							f"({lower_limit:.1f}–{upper_limit:.1f}) → tartjuk: {self.P_last_mode_state}"))
						)

					# Execution | --- Végrehajtás ---
					if self.P_last_mode_state == 0:
						self.buffer_1()
					else:
						self.buffer_2()

				# Dual mode: tank temperature HEATING | Dual mód: tartályhőmérséklet FŰTÉS
				elif Devices[104].sValue == "60" and not Devices[104].TimedOut:
					Domoticz.Debug(('Dual mode based on tank temperature' + " | " + ("Dual mód tartályhőmérséklet alapján!")))

					# Calculate thresholds | --- Határok kiszámítása ---
					# Lower threshold: activate dual mode | Alsó határ: dual bekapcsolása
					lower_limit = self.P_celhomerseklet - buffer_diff - buffer_hysteresis

					# Upper threshold: switch back to buffer_1 | Felső határ: buffer_1 visszakapcsolása
					upper_limit = self.P_celhomerseklet - buffer_diff + buffer_hysteresis

					Domoticz.Debug(
						(f'DEBUG: tank actual={self.PufferAktual:.1f}, target={self.P_celhomerseklet}, lower={lower_limit:.1f}, upper={upper_limit:.1f}' + " | " + (f"DEBUG: TartalyAktual={self.PufferAktual:.1f}, "
						f"cel={self.P_celhomerseklet}, "
						f"alsó határ={lower_limit:.1f}, felső határ={upper_limit:.1f}"))
					)

					# Determine operating mode | --- Üzemmód meghatározása ---
					# 0 = buffer_1 | 0 = buffer_1 (első pufferüzemmód)
					# 1 = buffer_2 | 1 = buffer_2 (második pufferüzemmód)

					# Tank too cold → switch to dual mode | Tartály túl hideg → menjünk dual-ra
					if self.PufferAktual < lower_limit:
						Domoticz.Debug(
							(f'Tank temperature {self.PufferAktual:.1f} < lower limit ({lower_limit:.1f}) → switch to dual mode' + " | " + (f"Tartályhőmérséklet {self.PufferAktual:.1f} < alsó határ ({lower_limit:.1f}) → váltás dual módra"))
						)
						self.P_last_mode_state = 1

					# Tank warm enough: switch back to buffer_1 | A tartály elég meleg, visszaváltás buffer_1-re
					elif self.PufferAktual > upper_limit:
						Domoticz.Debug(
							(f'Tank temperature {self.PufferAktual:.1f} > upper limit ({upper_limit:.1f}) → switch to buffer_1' + " | " + (f"Tartályhőmérséklet {self.PufferAktual:.1f} > felső határ ({upper_limit:.1f}) → váltás buffer_1 módra"))
						)
						self.P_last_mode_state = 0

					# Intermediate range → no switching | Köztes tartomány → nincs váltás
					else:
						Domoticz.Debug(
							(f'Tank temperature {self.PufferAktual:.1f} is within hysteresis band ({lower_limit:.1f}–{upper_limit:.1f}); maintaining mode: {self.P_last_mode_state}' + " | " + (f"Tartály {self.PufferAktual:.1f} a hiszterézis sávban "
							f"({lower_limit:.1f}–{upper_limit:.1f}) → üzemmód tartása: {self.P_last_mode_state}"))
						)

					# Execution | --- VÉGREHAJTÁS ---
					if self.P_last_mode_state == 0:
						self.buffer_1()
					else:
						self.buffer_1()
						self.buffer_2()

				# Dual mode: outdoor temperature HEATING | Dual mód: külső hőmérséklet FŰTÉS
				elif Devices[104].sValue == "70" and not Devices[104].TimedOut:
					Domoticz.Debug(('Dual mode based on outdoor temperature (BUFFER)' + " | " + ("Dual mód külső hőmérséklet alapján (PUFFER)!")))

					# Hysteresis thresholds | Hiszterézis határok
					lower_limit = buffer_limit - buffer_hysteresis	# Below this: buffer_2 | Ez alatt: buffer_2
					upper_limit = buffer_limit + buffer_hysteresis	# Above this: buffer_1 | Ez felett: buffer_1

					Domoticz.Debug(
						(f'DEBUG: outdoor temperature={self.outtemp:.1f}, limit={buffer_limit}, lower={lower_limit:.1f}, upper={upper_limit:.1f}' + " | " + (f"DEBUG: outtemp={self.outtemp:.1f}, limit={buffer_limit}, "
						f"alsó határ={lower_limit:.1f}, felső határ={upper_limit:.1f}"))
					)

					# Determine operating mode | --- Üzemmód meghatározás ---
					# 0 = buffer_1 | 0 = buffer_1 (első pufferüzemmód)
					# 1 = buffer_2 | 1 = buffer_2 (második pufferüzemmód)

					# Too cold outside → switch to mode 2 | Túl hideg kint → váltás 2-re
					if self.outtemp < lower_limit:
						Domoticz.Debug(
							(f'Outdoor temperature {self.outtemp:.1f} < lower limit ({lower_limit:.1f}) → dual mode' + " | " + (f"Külső hőmérséklet {self.outtemp:.1f} < alsó határ ({lower_limit:.1f}) → dual üzemmód"))
						)
						self.P_last_mode_state = 1

					# Warm enough outside → switch to mode 1 | Elég meleg kint → váltás 1-re
					elif self.outtemp > upper_limit:
						Domoticz.Debug(
							(f'Outdoor temperature {self.outtemp:.1f} > upper limit ({upper_limit:.1f}) → buffer_1' + " | " + (f"Külső hőmérséklet {self.outtemp:.1f} > felső határ ({upper_limit:.1f}) → buffer_1 mód"))
						)
						self.P_last_mode_state = 0

					# Hysteresis range → NO switching | Hiszterézis tartomány → NINCS váltás
					else:
						Domoticz.Debug(
							(f'Outdoor temperature {self.outtemp:.1f} is within hysteresis band ({lower_limit:.1f}–{upper_limit:.1f}); maintaining mode: {self.P_last_mode_state}' + " | " + (f"Külső hőmérséklet {self.outtemp:.1f} a hiszterézis sávban "
							f"({lower_limit:.1f}–{upper_limit:.1f}) → mód tartása: {self.P_last_mode_state}"))
						)

					# Execution | --- VÉGREHAJTÁS ---
					if self.P_last_mode_state == 0:
						self.buffer_1()
					else:
						self.buffer_1()
						self.buffer_2()

				# Dual mode: outdoor dew point HEATING | Dual mód: külső harmatpont FŰTÉS
				elif Devices[104].sValue == "80" and not Devices[104].TimedOut:
					Domoticz.Debug(('Dual mode based on outdoor dew point (BUFFER)' + " | " + ("Dual mód külső harmatpont alapján (PUFFER)!")))

					# Only dew point + compensation + hysteresis matter | Csak dewpoint + kompenzáció + hiszterézis számít
					Tcorr = self.outtemp + buffer_dualkomp

					upper_limit = Tcorr - buffer_hysteresis     # Dew point >= upper_limit → danger → mode 1 | harmatpont >= upper_limit → veszély → 1
					lower_limit = Tcorr + buffer_hysteresis     # Dew point <= lower_limit → very dry → mode 2 | harmatpont <= lower_limit → nagyon száraz → 2

					Domoticz.Debug(
						(f'BUFFER mode 50 dew-point check: outdoor temperature={self.outtemp:.1f}, dew point={self.outdewpoint:.1f}, correction={Tcorr:.1f}, lower={lower_limit:.1f}, upper={upper_limit:.1f}' + " | " + (f"PUFFER 50-es mód harmatpont-ellenőrzése: külső hőmérséklet={self.outtemp:.1f}, "
						f"harmatpont={self.outdewpoint:.1f}, korrekció={Tcorr:.1f}, "
						f"alsó határ={lower_limit:.1f}, felső határ={upper_limit:.1f}"))
					)

					# Decide based only on dew point | --- Csak harmatpont alapján döntünk ---
					# High dew point → mode 1 (safety mode) | Harmatpont magas → 1 (biztonsági üzem)
					if self.outdewpoint >= upper_limit:
						Domoticz.Debug(
							(f'Dew point {self.outdewpoint:.1f} >= upper limit {upper_limit:.1f} → buffer_1' + " | " + (f"Harmatpont {self.outdewpoint:.1f} >= felső határ {upper_limit:.1f} → buffer_1"))
						)
						self.P_last_mode_state = 0

					# Low dew point → mode 2 (favorable conditions) | Harmatpont alacsony → 2 (jó körülmények)
					elif self.outdewpoint <= lower_limit:
						Domoticz.Debug(
							(f'Dew point {self.outdewpoint:.1f} <= lower limit {lower_limit:.1f} → dual mode' + " | " + (f"Harmatpont {self.outdewpoint:.1f} <= alsó határ {lower_limit:.1f} → dual"))
						)
						self.P_last_mode_state = 1

					# Hysteresis band | Hiszterézis sáv
					else:
						Domoticz.Debug(
							(f'Dew point {self.outdewpoint:.1f} is within hysteresis band ({lower_limit:.1f}–{upper_limit:.1f}); maintaining mode: {self.P_last_mode_state}' + " | " + (f"Harmatpont {self.outdewpoint:.1f} a hiszterézis tartományban "
							f"({lower_limit:.1f}–{upper_limit:.1f}) → tartjuk: {self.P_last_mode_state}"))
						)

					# Execution | --- VÉGREHAJTÁS ---
					if self.P_last_mode_state == 0:
						self.buffer_1()
					else:
						self.buffer_1()
						self.buffer_2()

				# Saver mode: temperature + outdoor temperature HEATING | Saver mód: hőmérséklet + külsőhőmérséklet FŰTÉS
				elif Devices[104].sValue == "90" and not Devices[104].TimedOut:
					Domoticz.Debug(('Saver mode based on tank temperature and outdoor temperature (BUFFER)' + " | " + ("Saver mód tartályhőmérséklet + külső hőmérséklet alapján (PUFFER)!")))

					# Tank hysteresis thresholds | --- Tartály hiszterézis határok ---
					t_lower = self.P_celhomerseklet - buffer_diff - buffer_hysteresis	# Below this → cold → mode 2 requested | ez alatt → hideg → igény a 2-es módra
					t_upper = self.P_celhomerseklet - buffer_diff + buffer_hysteresis	# Above this → warm enough → mode 1 | ez felett → elég meleg → 1-es mód

					# Outdoor temperature hysteresis thresholds | --- Külső hőmérséklet hiszterézis határok ---
					o_lower = buffer_limit - buffer_hysteresis	# Below this → cold outdoors → mode 2 permitted | ez alatt → kint is hideg → engedi 2-es módot
					o_upper = buffer_limit + buffer_hysteresis	# Above this → too warm outdoors → return to mode 1 | ez felett → kint túl meleg → vissza 1-esre

					Domoticz.Debug(
						(f'DEBUG: tank={self.PufferAktual:.1f}, tank lower={t_lower:.1f}, tank upper={t_upper:.1f}, outdoor temperature={self.outtemp:.1f}, outdoor lower={o_lower:.1f}, outdoor upper={o_upper:.1f}' + " | " + (f"DEBUG: Tartaly={self.PufferAktual:.1f}, "
						f"t_lower={t_lower:.1f}, t_upper={t_upper:.1f}, "
						f"outtemp={self.outtemp:.1f}, o_lower={o_lower:.1f}, o_upper={o_upper:.1f}"))
					)

					# Determine operating mode | --- Üzemmód meghatározása ---
					# 0 = buffer_1 (normal) | 0 = buffer_1 (normál)
					# 1 = buffer_2 (saver + auxiliary) | 1 = buffer_2 (takarékos + kiegészítő)

					# Conditions for mode 2: tank cold AND outdoor conditions permit | Feltételek a 2-es módra: tartály hideg ÉS kint engedi
					if self.PufferAktual < t_lower and self.outtemp < o_lower:
						Domoticz.Debug(
							(f'Tank cold ({self.PufferAktual:.1f} < {t_lower:.1f}) AND outside cold ({self.outtemp:.1f} < {o_lower:.1f}) → buffer_2' + " | " + (f"Tartály hideg ({self.PufferAktual:.1f} < {t_lower:.1f}) "
							f"ÉS kint hideg ({self.outtemp:.1f} < {o_lower:.1f}) → buffer_2"))
						)
						self.P_last_mode_state = 1

					# Condition to revert → tank sufficiently warm (outdoor temperature ignored) | Feltétel a visszaállásra → elég meleg tartály (külsőt ilyenkor nem vesszük figyelembe)
					elif self.PufferAktual > t_upper:
						Domoticz.Debug(
							(f'Tank sufficiently warm ({self.PufferAktual:.1f} > {t_upper:.1f}) → buffer_1' + " | " + (f"Tartály elég meleg ({self.PufferAktual:.1f} > {t_upper:.1f}) → buffer_1"))
						)
						self.P_last_mode_state = 0

					# Hysteresis range → NO switching | Hiszterézis tartomány → NINCS váltás
					else:
						Domoticz.Debug(
							(f'Within hysteresis band → maintaining mode: {self.P_last_mode_state}' + " | " + (f"Hiszterézis tartományban → tartjuk: {self.P_last_mode_state}"))
						)

					# Execution | --- VÉGREHAJTÁS ---
					if self.P_last_mode_state == 0:
						self.buffer_1()
					else:
						self.buffer_2()

				# Saver mode: hőmérséklet + outdoor dew point HEATING | Saver mód: hőmérséklet + külső harmatpont FŰTÉS
				elif Devices[104].sValue == "100" and not Devices[104].TimedOut:
					Domoticz.Debug(('Saver mode (BUFFER): switch if source 1 would freeze due to dew-point conditions' + " | " + ("Saver mód (PUFFER): váltás, ha az 1-es lefagyna a harmattól!")))

					# Adjusted outdoor temperature | --- Korrigált külső hőmérséklet ---
					Tcorr = self.outtemp + buffer_dualkomp

					# Dew point hysteresis thresholds | --- Harmatpont hiszterézis határok ---
					# Freezing risk occurs when dewpoint ≥ Tcorr | fagyveszély akkor van, ha dewpoint ≥ Tcorr
					upper_limit = Tcorr			# Above this → danger → switch to mode 2 | fölötte → veszély → 2-re váltás
					lower_limit = Tcorr - buffer_hysteresis	# Below this → safe → return to mode 1 | alatta → biztonság → vissza 1-re

					Domoticz.Debug(
						(f'DEBUG: dew point={self.outdewpoint:.1f}, correction={Tcorr:.1f}, lower={lower_limit:.1f}, upper={upper_limit:.1f}' + " | " + (f"DEBUG: harmatpont={self.outdewpoint:.1f}, korrekció={Tcorr:.1f}, "
						f"alsó határ={lower_limit:.1f}, felső határ={upper_limit:.1f}"))
					)

					# Operating mode state | --- Üzemmód állapota ---
					# 0 = buffer_1 (base) | 0 = buffer_1 (alap)
					# 1 = buffer_2 (safety / auxiliary) | 1 = buffer_2 (biztonsági / kiegészítő)
					# THE ONLY REASON TO SWITCH: mode 1 would freeze! | A VÁLTÁS EGYETLEN OKA: az 1-es lefagyna!

					# → Freezing risk: mode 1 is NOT safe → must switch to mode 2 | → Fagyveszély: az 1-es üzem NEM biztonságos → kötelező váltás 2-re
					if self.outdewpoint >= upper_limit:
						Domoticz.Debug(
							(f'Dew point {self.outdewpoint:.1f} >= critical limit {upper_limit:.1f} → source 1 would freeze → buffer_2' + " | " + (f"Harmatpont {self.outdewpoint:.1f} >= kritikus határ {upper_limit:.1f} → "
							f"1-es lefagyna → buffer_2"))
						)
						self.P_last_mode_state = 1

					# → Safe: mode 1 can be used again → return to mode 1 | → Biztonság: az 1-es üzem újra használható → vissza 1-re
					elif self.outdewpoint <= lower_limit:
						Domoticz.Debug(
							(f'Dew point {self.outdewpoint:.1f} <= safety limit {lower_limit:.1f} → source 1 safe again → buffer_1' + " | " + (f"Harmatpont {self.outdewpoint:.1f} <= biztonsági határ {lower_limit:.1f} → "
							f"1-es újra biztonságos → buffer_1"))
						)
						self.P_last_mode_state = 0

					# → Hysteresis range | → Hiszterézis tartomány
					else:
						Domoticz.Debug(
							(f'Dew point {self.outdewpoint:.1f} within {lower_limit:.1f}–{upper_limit:.1f} → maintaining mode: {self.P_last_mode_state}' + " | " + (f"Harmatpont {self.outdewpoint:.1f} a sávban {lower_limit:.1f}–{upper_limit:.1f} → "
							f"üzemmód tartása: {self.P_last_mode_state}"))
						)

					# Execution | --- VÉGREHAJTÁS ---
					if self.P_last_mode_state == 0:
						self.buffer_1()
					else:
						self.buffer_2()

				# Switching mode (based on 500 W energy threshold, with hysteresis) | --- Váltó mód (500W energetika alapján, hiszterézissel) ---
				elif Devices[104].sValue == "110" and not Devices[104].TimedOut:
					Domoticz.Debug(('BUFFER switching mode (500 W, percentage hysteresis)' + " | " + ("Váltó mód puffer (500W, % hiszterézis)")))
					power = self.aktual_watt
					base = 500
					if self.P_last_mode_state == 0:
						power += base
					h = int(base * int(Devices[85].sValue) / 100)
					Domoticz.Debug(f"Power={power} W, base={base} W, hysteresis=±{h} W | Teljesítmény={power} W, alapérték={base} W, hiszterézis=±{h} W")

					if power >= base + h:
						self.P_last_mode_state = 0
					elif power <= base - h:
						self.P_last_mode_state = 1

					if self.P_last_mode_state == 0:
						self.buffer_1()
					else:
						self.buffer_2()

				# Switching mode (based on 1000 W energy threshold, with hysteresis) | --- Váltó mód (1000W energetika alapján, hiszterézissel) ---
				elif Devices[104].sValue == "120" and not Devices[104].TimedOut:
					Domoticz.Debug(('BUFFER switching mode (1000 W, percentage hysteresis)' + " | " + ("Váltó mód puffer (1000W, % hiszterézis)")))
					power = self.aktual_watt
					base = 1000
					if self.P_last_mode_state == 0:
						power += base
					h = int(base * int(Devices[85].sValue) / 100)
					Domoticz.Debug(f"Power={power} W, base={base} W, hysteresis=±{h} W | Teljesítmény={power} W, alapérték={base} W, hiszterézis=±{h} W")

					if power >= base + h:
						self.P_last_mode_state = 0
					elif power <= base - h:
						self.P_last_mode_state = 1

					if self.P_last_mode_state == 0:
						self.buffer_1()
					else:
						self.buffer_2()

				# Switching mode (based on 1500 W energy threshold, with hysteresis) | --- Váltó mód (1500W energetika alapján, hiszterézissel) ---
				elif Devices[104].sValue == "130" and not Devices[104].TimedOut:
					Domoticz.Debug(('BUFFER switching mode (1500 W, percentage hysteresis)' + " | " + ("Váltó mód puffer (1500W, % hiszterézis)")))
					power = self.aktual_watt
					base = 1500
					if self.P_last_mode_state == 0:
						power += base
					h = int(base * int(Devices[85].sValue) / 100)
					Domoticz.Debug(f"Power={power} W, base={base} W, hysteresis=±{h} W | Teljesítmény={power} W, alapérték={base} W, hiszterézis=±{h} W")

					if power >= base + h:
						self.P_last_mode_state = 0
					elif power <= base - h:
						self.P_last_mode_state = 1

					if self.P_last_mode_state == 0:
						self.buffer_1()
					else:
						self.buffer_2()

				# Switching mode (based on 2000 W energy threshold, with hysteresis) | --- Váltó mód (2000W energetika alapján, hiszterézissel) ---
				elif Devices[104].sValue == "140" and not Devices[104].TimedOut:
					Domoticz.Debug(('BUFFER switching mode (2000 W, percentage hysteresis)' + " | " + ("Váltó mód puffer (2000W, % hiszterézis)")))
					power = self.aktual_watt
					base = 2000
					if self.P_last_mode_state == 0:
						power += base
					h = int(base * int(Devices[85].sValue) / 100)
					Domoticz.Debug(f"Power={power} W, base={base} W, hysteresis=±{h} W | Teljesítmény={power} W, alapérték={base} W, hiszterézis=±{h} W")

					if power >= base + h:
						self.P_last_mode_state = 0
					elif power <= base - h:
						self.P_last_mode_state = 1

					if self.P_last_mode_state == 0:
						self.buffer_1()
					else:
						self.buffer_2()

				# Switching mode (based on 3000 W energy threshold, with hysteresis) | --- Váltó mód (3000W energetika alapján, hiszterézissel) ---
				elif Devices[104].sValue == "150" and not Devices[104].TimedOut:
					Domoticz.Debug(('BUFFER switching mode (3000 W, percentage hysteresis)' + " | " + ("Váltó mód puffer (3000W, % hiszterézis)")))
					power = self.aktual_watt
					base = 3000
					if self.P_last_mode_state == 0:
						power += base
					h = int(base * int(Devices[85].sValue) / 100)
					Domoticz.Debug(f"Power={power} W, base={base} W, hysteresis=±{h} W | Teljesítmény={power} W, alapérték={base} W, hiszterézis=±{h} W")

					if power >= base + h:
						self.P_last_mode_state = 0
					elif power <= base - h:
						self.P_last_mode_state = 1

					if self.P_last_mode_state == 0:
						self.buffer_1()
					else:
						self.buffer_2()

				# Switching mode (based on 4000 W energy threshold, with hysteresis) | --- Váltó mód (4000W energetika alapján, hiszterézissel) ---
				elif Devices[104].sValue == "160" and not Devices[104].TimedOut:
					Domoticz.Debug(('BUFFER switching mode (4000 W, percentage hysteresis)' + " | " + ("Váltó mód puffer (4000W, % hiszterézis)")))
					power = self.aktual_watt
					base = 4000
					if self.P_last_mode_state == 0:
						power += base
					h = int(base * int(Devices[85].sValue) / 100)
					Domoticz.Debug(f"Power={power} W, base={base} W, hysteresis=±{h} W | Teljesítmény={power} W, alapérték={base} W, hiszterézis=±{h} W")

					if power >= base + h:
						self.P_last_mode_state = 0
					elif power <= base - h:
						self.P_last_mode_state = 1

					if self.P_last_mode_state == 0:
						self.buffer_1()
					else:
						self.buffer_2()

				# Switching mode (based on 5000 W energy threshold, with hysteresis) | --- Váltó mód (5000W energetika alapján, hiszterézissel) ---
				elif Devices[104].sValue == "170" and not Devices[104].TimedOut:
					Domoticz.Debug(('BUFFER switching mode (5000 W, percentage hysteresis)' + " | " + ("Váltó mód puffer (5000W, % hiszterézis)")))
					power = self.aktual_watt
					base = 5000
					if self.P_last_mode_state == 0:
						power += base
					h = int(base * int(Devices[85].sValue) / 100)
					Domoticz.Debug(f"Power={power} W, base={base} W, hysteresis=±{h} W | Teljesítmény={power} W, alapérték={base} W, hiszterézis=±{h} W")

					if power >= base + h:
						self.P_last_mode_state = 0
					elif power <= base - h:
						self.P_last_mode_state = 1

					if self.P_last_mode_state == 0:
						self.buffer_1()
					else:
						self.buffer_2()

				# Dual mode (based on 500 W energy threshold, with hysteresis) | --- Dual mód (500W energetika alapján, hiszterézissel) ---
				elif Devices[104].sValue == "180" and not Devices[104].TimedOut:
					Domoticz.Debug(('BUFFER dual mode (500 W, percentage hysteresis)' + " | " + ("Dual mód puffer (500W, % hiszterézis)")))
					power = self.aktual_watt
					base = 500
					if self.P_last_mode_state == 0:
						power += base
					h = int(base * int(Devices[85].sValue) / 100)
					Domoticz.Debug(f"Power={power} W, base={base} W, hysteresis=±{h} W | Teljesítmény={power} W, alapérték={base} W, hiszterézis=±{h} W")

					if power >= base + h:
						self.P_last_mode_state = 0
					elif power <= base - h:
						self.P_last_mode_state = 1

					if self.P_last_mode_state == 0:
						self.buffer_1()
						self.buffer_2()
					else:
						self.buffer_2()

				# Dual mode (based on 1000 W energy threshold, with hysteresis) | --- Dual mód (1000W energetika alapján, hiszterézissel) ---
				elif Devices[104].sValue == "190" and not Devices[104].TimedOut:
					Domoticz.Debug(('BUFFER dual mode (1000 W, percentage hysteresis)' + " | " + ("Dual mód puffer (1000W, % hiszterézis)")))
					power = self.aktual_watt
					base = 1000
					if self.P_last_mode_state == 0:
						power += base
					h = int(base * int(Devices[85].sValue) / 100)
					Domoticz.Debug(f"Power={power} W, base={base} W, hysteresis=±{h} W | Teljesítmény={power} W, alapérték={base} W, hiszterézis=±{h} W")

					if power >= base + h:
						self.P_last_mode_state = 0
					elif power <= base - h:
						self.P_last_mode_state = 1

					if self.P_last_mode_state == 0:
						self.buffer_1()
						self.buffer_2()
					else:
						self.buffer_2()

				# Dual mode (based on 1500 W energy threshold, with hysteresis) | --- Dual mód (1500W energetika alapján, hiszterézissel) ---
				elif Devices[104].sValue == "200" and not Devices[104].TimedOut:
					Domoticz.Debug(('BUFFER dual mode (1500 W, percentage hysteresis)' + " | " + ("Dual mód puffer (1500W, % hiszterézis)")))
					power = self.aktual_watt
					base = 1500
					if self.P_last_mode_state == 0:
						power += base
					h = int(base * int(Devices[85].sValue) / 100)
					Domoticz.Debug(f"Power={power} W, base={base} W, hysteresis=±{h} W | Teljesítmény={power} W, alapérték={base} W, hiszterézis=±{h} W")

					if power >= base + h:
						self.P_last_mode_state = 0
					elif power <= base - h:
						self.P_last_mode_state = 1

					if self.P_last_mode_state == 0:
						self.buffer_1()
						self.buffer_2()
					else:
						self.buffer_2()

				# Dual mode (based on 2000 W energy threshold, with hysteresis) | --- Dual mód (2000W energetika alapján, hiszterézissel) ---
				elif Devices[104].sValue == "210" and not Devices[104].TimedOut:
					Domoticz.Debug(('BUFFER dual mode (2000 W, percentage hysteresis)' + " | " + ("Dual mód puffer (2000W, % hiszterézis)")))
					power = self.aktual_watt
					base = 2000
					if self.P_last_mode_state == 0:
						power += base
					h = int(base * int(Devices[85].sValue) / 100)
					Domoticz.Debug(f"Power={power} W, base={base} W, hysteresis=±{h} W | Teljesítmény={power} W, alapérték={base} W, hiszterézis=±{h} W")

					if power >= base + h:
						self.P_last_mode_state = 0
					elif power <= base - h:
						self.P_last_mode_state = 1

					if self.P_last_mode_state == 0:
						self.buffer_1()
						self.buffer_2()
					else:
						self.buffer_2()

				# Dual mode (based on 3000 W energy threshold, with hysteresis) | --- Dual mód (3000W energetika alapján, hiszterézissel) ---
				elif Devices[104].sValue == "220" and not Devices[104].TimedOut:
					Domoticz.Debug(('BUFFER dual mode (3000 W, percentage hysteresis)' + " | " + ("Dual mód puffer (3000W, % hiszterézis)")))
					power = self.aktual_watt
					base = 3000
					if self.P_last_mode_state == 0:
						power += base
					h = int(base * int(Devices[85].sValue) / 100)
					Domoticz.Debug(f"Power={power} W, base={base} W, hysteresis=±{h} W | Teljesítmény={power} W, alapérték={base} W, hiszterézis=±{h} W")

					if power >= base + h:
						self.P_last_mode_state = 0
					elif power <= base - h:
						self.P_last_mode_state = 1

					if self.P_last_mode_state == 0:
						self.buffer_1()
						self.buffer_2()
					else:
						self.buffer_2()

				# Dual mode (based on 4000 W energy threshold, with hysteresis) | --- Dual mód (4000W energetika alapján, hiszterézissel) ---
				elif Devices[104].sValue == "230" and not Devices[104].TimedOut:
					Domoticz.Debug(('BUFFER dual mode (4000 W, percentage hysteresis)' + " | " + ("Dual mód puffer (4000W, % hiszterézis)")))
					power = self.aktual_watt
					base = 4000
					if self.P_last_mode_state == 0:
						power += base
					h = int(base * int(Devices[85].sValue) / 100)
					Domoticz.Debug(f"Power={power} W, base={base} W, hysteresis=±{h} W | Teljesítmény={power} W, alapérték={base} W, hiszterézis=±{h} W")

					if power >= base + h:
						self.P_last_mode_state = 0
					elif power <= base - h:
						self.P_last_mode_state = 1

					if self.P_last_mode_state == 0:
						self.buffer_1()
						self.buffer_2()
					else:
						self.buffer_2()

				# Dual mode (based on 5000 W energy threshold, with hysteresis) | --- Dual mód (5000W energetika alapján, hiszterézissel) ---
				elif Devices[104].sValue == "240" and not Devices[104].TimedOut:
					Domoticz.Debug(('BUFFER dual mode (5000 W, percentage hysteresis)' + " | " + ("Dual mód puffer (5000W, % hiszterézis)")))
					power = self.aktual_watt
					base = 5000
					if self.P_last_mode_state == 0:
						power += base
					h = int(base * int(Devices[85].sValue) / 100)
					Domoticz.Debug(f"Power={power} W, base={base} W, hysteresis=±{h} W | Teljesítmény={power} W, alapérték={base} W, hiszterézis=±{h} W")

					if power >= base + h:
						self.P_last_mode_state = 0
					elif power <= base - h:
						self.P_last_mode_state = 1

					if self.P_last_mode_state == 0:
						self.buffer_1()
						self.buffer_2()
					else:
						self.buffer_2()

			else:
				Domoticz.Debug(('BUFFER F OFF → turn everything off' + " | " + ("PUFFER F Off → minden kikapcs")))
				self.switchElsodleges_P_F(False)
				self.switchMasodlagos_P_F(False)

# Buffer cooling mode | Puffer hűtési üzemmódja

			if self.buffer and Devices[224].sValue != "0" and (Devices[224].Used == 1) :
			
				Domoticz.Debug(('Buffer mode and operation enabled' + " | " + ("Puffer mód és üzem bekapcsolva")))

				self.buffer_temp_read()

				buffer_limit = float(Devices[226].sValue)      # Switching threshold for buffer device 2 | PUFFER 2. készülék kapcsolási határértéke
				buffer_diff = float(Devices[109].sValue)       # Buffer dual temperature differential | Puffer dual hőmérséklet-különbsége
				buffer_dualkomp = float(Devices[223].sValue)    # Buffer dew-point compensation | Puffer harmatpont-kompenzációja
				buffer_hysteresis = float(Devices[18].sValue)  # Hysteresis | Hiszterézis

				Domoticz.Debug((f'BUFFER parameters:' + " | " + (f"PUFFER paraméterek:")))
				Domoticz.Debug((f'    Tank = {self.PufferAktual:.1f} °C' + " | " + (f"    Tartály = {self.PufferAktual:.1f} °C")))
				Domoticz.Debug((f'    Target = {self.P_celhomerseklet:.1f} °C' + " | " + (f"    Cél = {self.P_celhomerseklet:.1f} °C")))
				Domoticz.Debug((f'    Outdoor temperature = {self.outtemp:.1f} °C' + " | " + (f"    Külső hőmérséklet = {self.outtemp:.1f} °C")))
				Domoticz.Debug((f'    Dew point = {self.outdewpoint:.1f} °C' + " | " + (f"    Harmatpont = {self.outdewpoint:.1f} °C")))
				Domoticz.Debug((f'    Dual-source buffer correction = {buffer_dualkomp:.1f}' + " | " + (f"    Puffer dual korrekció = {buffer_dualkomp:.1f}")))
				Domoticz.Debug((f'    Hysteresis = {buffer_hysteresis:.1f}' + " | " + (f"    Hiszterézis = {buffer_hysteresis:.1f}")))
				Domoticz.Debug((f'    Outdoor limit = {buffer_limit:.1f}' + " | " + (f"    Külső határérték = {buffer_limit:.1f}")))
				
				# Primary mode COOLING | Elsődleges mód (HŰTÉS)

				if Devices[224].sValue == "10" and not Devices[224].TimedOut:
					Domoticz.Debug(('Primary BUFFER mode (COOLING)!' + " | " + ("Elsődleges PUFFER mód (HŰTÉS)!")))
					self.buffer_1()

				# Secondary mode COOLING | Másodlagos mód (HŰTÉS)
				elif Devices[224].sValue == "20" and not Devices[224].TimedOut:
					Domoticz.Debug(('Secondary BUFFER mode (COOLING)!' + " | " + ("Másodlagos PUFFER mód (HŰTÉS)!")))
					self.buffer_2()

				# Switching mode: tank temperature (COOLING) | Váltó mód: tartályhőmérséklet (HŰTÉS)
				elif Devices[224].sValue == "30" and not Devices[224].TimedOut:
					Domoticz.Debug(('Switching mode based on tank temperature (COOLING)!' + " | " + ("Váltó mód tartályhőmérséklet alapján (HŰTÉS)!")))

					# Thresholds | Határértékek
					lower_limit = self.P_celhomerseklet + buffer_diff - buffer_hysteresis
					upper_limit = self.P_celhomerseklet + buffer_diff + buffer_hysteresis

					Domoticz.Debug(
						(f'DEBUG: Buffer={self.PufferAktual:.1f}, target={self.P_celhomerseklet}, lower={lower_limit:.1f}, upper={upper_limit:.1f}' + " | " + (f"DEBUG: Puffer={self.PufferAktual:.1f}, "
						f"cel={self.P_celhomerseklet}, "
						f"alsó határ={lower_limit:.1f}, felső határ={upper_limit:.1f}"))
					)

					# 0 = buffer_1 | 0 = buffer_1 (első pufferüzemmód)
					# 1 = buffer_2 | 1 = buffer_2 (második pufferüzemmód)

					# Too warm: switch to buffer_2 | Túl meleg, váltás buffer_2-re
					if self.PufferAktual > upper_limit:
						Domoticz.Debug(
							(f'Buffer temperature {self.PufferAktual:.1f} > upper limit ({upper_limit:.1f}) → buffer_2' + " | " + (f"Puffer {self.PufferAktual:.1f} > upper({upper_limit:.1f}) → buffer_2"))
						)
						self.P_last_mode_state = 1

					# Cold enough: switch to buffer_1 | Elég hideg, váltás buffer_1-re
					elif self.PufferAktual < lower_limit:
						Domoticz.Debug(
							(f'Buffer temperature {self.PufferAktual:.1f} < lower limit ({lower_limit:.1f}) → buffer_1' + " | " + (f"Puffer {self.PufferAktual:.1f} < lower({lower_limit:.1f}) → buffer_1"))
						)
						self.P_last_mode_state = 0

					else:
						Domoticz.Debug(
							(f'Buffer temperature {self.PufferAktual:.1f} within hysteresis band ({lower_limit:.1f}–{upper_limit:.1f}) → holding mode: {self.P_last_mode_state}' + " | " + (f"Puffer {self.PufferAktual:.1f} hiszterézis sávban "
							f"({lower_limit:.1f}–{upper_limit:.1f}) → mód tartása: {self.P_last_mode_state}"))
						)

					if self.P_last_mode_state == 0:
						self.buffer_1()
					else:
						self.buffer_2()

				# Switching mode: outdoor temperature (COOLING) | Váltó mód: külső hőmérséklet (HŰTÉS)
				elif Devices[224].sValue == "40" and not Devices[224].TimedOut:
					Domoticz.Debug(('Switching mode based on outdoor temperature (COOLING)!' + " | " + ("Váltó mód külső hőmérséklet alapján (HŰTÉS)!")))

					lower_limit = buffer_limit - buffer_hysteresis
					upper_limit = buffer_limit + buffer_hysteresis

					Domoticz.Debug(
						(f'DEBUG: outdoor temperature={self.outtemp:.1f}, limit={buffer_limit}, lower={lower_limit:.1f}, upper={upper_limit:.1f}' + " | " + (f"DEBUG: outtemp={self.outtemp:.1f}, "
						f"limit={buffer_limit}, "
						f"alsó határ={lower_limit:.1f}, felső határ={upper_limit:.1f}"))
					)

					# Outdoor temperature too high: switch to buffer_2 | Túl meleg van kint, váltás buffer_2-re
					if self.outtemp > upper_limit:
						Domoticz.Debug(
							(f'Outdoor temperature {self.outtemp:.1f} > upper limit ({upper_limit:.1f}) → buffer_2' + " | " + (f"Külső {self.outtemp:.1f} > upper({upper_limit:.1f}) → buffer_2"))
						)
						self.P_last_mode_state = 1

					# Outdoor temperature sufficiently low: switch to buffer_1 | Elég hideg van kint, váltás buffer_1-re
					elif self.outtemp < lower_limit:
						Domoticz.Debug(
							(f'Outdoor temperature {self.outtemp:.1f} < lower limit ({lower_limit:.1f}) → buffer_1' + " | " + (f"Külső {self.outtemp:.1f} < lower({lower_limit:.1f}) → buffer_1"))
						)
						self.P_last_mode_state = 0

					else:
						Domoticz.Debug(
							(f'Outdoor temperature {self.outtemp:.1f} within hysteresis band ({lower_limit:.1f}–{upper_limit:.1f}) → holding mode: {self.P_last_mode_state}' + " | " + (f"Külső {self.outtemp:.1f} hiszterézis sávban "
							f"({lower_limit:.1f}–{upper_limit:.1f}) → mód tartása: {self.P_last_mode_state}"))
						)

					if self.P_last_mode_state == 0:
						self.buffer_1()
					else:
						self.buffer_2()

				# Dual mode: tank temperature (COOLING) | Dual mód: tartályhőmérséklet (HŰTÉS)
				elif Devices[224].sValue == "50" and not Devices[224].TimedOut:
					Domoticz.Debug(('Dual mode based on tank temperature (COOLING)!' + " | " + ("Dual mód tartályhőmérséklet alapján (HŰTÉS)!")))

					lower_limit = self.P_celhomerseklet + buffer_diff - buffer_hysteresis
					upper_limit = self.P_celhomerseklet + buffer_diff + buffer_hysteresis

					if self.PufferAktual > upper_limit:
						self.P_last_mode_state = 1
					elif self.PufferAktual < lower_limit:
						self.P_last_mode_state = 0

					if self.P_last_mode_state == 0:
						self.buffer_1()
					else:
						self.buffer_1()
						self.buffer_2()

				# Dual mode: outdoor temperature (COOLING) | Dual mód: külső hőmérséklet (HŰTÉS)
				elif Devices[224].sValue == "60" and not Devices[224].TimedOut:
					Domoticz.Debug(('Dual mode based on outdoor temperature (COOLING)!' + " | " + ("Dual mód külső hőmérséklet alapján (HŰTÉS)!")))

					lower_limit = buffer_limit - buffer_hysteresis
					upper_limit = buffer_limit + buffer_hysteresis

					if self.outtemp > upper_limit:
						self.P_last_mode_state = 1
					elif self.outtemp < lower_limit:
						self.P_last_mode_state = 0

					if self.P_last_mode_state == 0:
						self.buffer_1()
					else:
						self.buffer_1()
						self.buffer_2()

				# Switching mode (based on 500 W energy threshold, with hysteresis) | --- Váltó mód (500W energetika alapján, hiszterézissel) ---
				elif Devices[224].sValue == "70" and not Devices[224].TimedOut:
					Domoticz.Debug(('BUFFER switching mode (500 W, percentage hysteresis)' + " | " + ("Váltó mód puffer (500W, % hiszterézis)")))
					power = self.aktual_watt
					base = 500
					if self.P_last_mode_state == 0:
						power += base
					h = int(base * int(Devices[85].sValue) / 100)
					Domoticz.Debug(f"Power={power} W, base={base} W, hysteresis=±{h} W | Teljesítmény={power} W, alapérték={base} W, hiszterézis=±{h} W")

					if power >= base + h:
						self.P_last_mode_state = 0
					elif power <= base - h:
						self.P_last_mode_state = 1

					if self.P_last_mode_state == 0:
						self.buffer_1()
					else:
						self.buffer_2()

				# Switching mode (based on 1000 W energy threshold, with hysteresis) | --- Váltó mód (1000W energetika alapján, hiszterézissel) ---
				elif Devices[224].sValue == "80" and not Devices[224].TimedOut:
					Domoticz.Debug(('BUFFER switching mode (1000 W, percentage hysteresis)' + " | " + ("Váltó mód puffer (1000W, % hiszterézis)")))
					power = self.aktual_watt
					base = 1000
					if self.P_last_mode_state == 0:
						power += base
					h = int(base * int(Devices[85].sValue) / 100)
					Domoticz.Debug(f"Power={power} W, base={base} W, hysteresis=±{h} W | Teljesítmény={power} W, alapérték={base} W, hiszterézis=±{h} W")

					if power >= base + h:
						self.P_last_mode_state = 0
					elif power <= base - h:
						self.P_last_mode_state = 1

					if self.P_last_mode_state == 0:
						self.buffer_1()
					else:
						self.buffer_2()

				# Switching mode (based on 1500 W energy threshold, with hysteresis) | --- Váltó mód (1500W energetika alapján, hiszterézissel) ---
				elif Devices[224].sValue == "90" and not Devices[224].TimedOut:
					Domoticz.Debug(('BUFFER switching mode (1500 W, percentage hysteresis)' + " | " + ("Váltó mód puffer (1500W, % hiszterézis)")))
					power = self.aktual_watt
					base = 1500
					if self.P_last_mode_state == 0:
						power += base
					h = int(base * int(Devices[85].sValue) / 100)
					Domoticz.Debug(f"Power={power} W, base={base} W, hysteresis=±{h} W | Teljesítmény={power} W, alapérték={base} W, hiszterézis=±{h} W")

					if power >= base + h:
						self.P_last_mode_state = 0
					elif power <= base - h:
						self.P_last_mode_state = 1

					if self.P_last_mode_state == 0:
						self.buffer_1()
					else:
						self.buffer_2()

				# Switching mode (based on 2000 W energy threshold, with hysteresis) | --- Váltó mód (2000W energetika alapján, hiszterézissel) ---
				elif Devices[224].sValue == "100" and not Devices[224].TimedOut:
					Domoticz.Debug(('BUFFER switching mode (2000 W, percentage hysteresis)' + " | " + ("Váltó mód puffer (2000W, % hiszterézis)")))
					power = self.aktual_watt
					base = 2000
					if self.P_last_mode_state == 0:
						power += base
					h = int(base * int(Devices[85].sValue) / 100)
					Domoticz.Debug(f"Power={power} W, base={base} W, hysteresis=±{h} W | Teljesítmény={power} W, alapérték={base} W, hiszterézis=±{h} W")

					if power >= base + h:
						self.P_last_mode_state = 0
					elif power <= base - h:
						self.P_last_mode_state = 1

					if self.P_last_mode_state == 0:
						self.buffer_1()
					else:
						self.buffer_2()

				# Switching mode (based on 3000 W energy threshold, with hysteresis) | --- Váltó mód (3000W energetika alapján, hiszterézissel) ---
				elif Devices[224].sValue == "110" and not Devices[224].TimedOut:
					Domoticz.Debug(('BUFFER switching mode (3000 W, percentage hysteresis)' + " | " + ("Váltó mód puffer (3000W, % hiszterézis)")))
					power = self.aktual_watt
					base = 3000
					if self.P_last_mode_state == 0:
						power += base
					h = int(base * int(Devices[85].sValue) / 100)
					Domoticz.Debug(f"Power={power} W, base={base} W, hysteresis=±{h} W | Teljesítmény={power} W, alapérték={base} W, hiszterézis=±{h} W")

					if power >= base + h:
						self.P_last_mode_state = 0
					elif power <= base - h:
						self.P_last_mode_state = 1

					if self.P_last_mode_state == 0:
						self.buffer_1()
					else:
						self.buffer_2()

				# Switching mode (based on 4000 W energy threshold, with hysteresis) | --- Váltó mód (4000W energetika alapján, hiszterézissel) ---
				elif Devices[224].sValue == "120" and not Devices[224].TimedOut:
					Domoticz.Debug(('BUFFER switching mode (4000 W, percentage hysteresis)' + " | " + ("Váltó mód puffer (4000W, % hiszterézis)")))
					power = self.aktual_watt
					base = 4000
					if self.P_last_mode_state == 0:
						power += base
					h = int(base * int(Devices[85].sValue) / 100)
					Domoticz.Debug(f"Power={power} W, base={base} W, hysteresis=±{h} W | Teljesítmény={power} W, alapérték={base} W, hiszterézis=±{h} W")

					if power >= base + h:
						self.P_last_mode_state = 0
					elif power <= base - h:
						self.P_last_mode_state = 1

					if self.P_last_mode_state == 0:
						self.buffer_1()
					else:
						self.buffer_2()

				# Switching mode (based on 5000 W energy threshold, with hysteresis) | --- Váltó mód (5000W energetika alapján, hiszterézissel) ---
				elif Devices[224].sValue == "130" and not Devices[224].TimedOut:
					Domoticz.Debug(('BUFFER switching mode (5000 W, percentage hysteresis)' + " | " + ("Váltó mód puffer (5000W, % hiszterézis)")))
					power = self.aktual_watt
					base = 5000
					if self.P_last_mode_state == 0:
						power += base
					h = int(base * int(Devices[85].sValue) / 100)
					Domoticz.Debug(f"Power={power} W, base={base} W, hysteresis=±{h} W | Teljesítmény={power} W, alapérték={base} W, hiszterézis=±{h} W")

					if power >= base + h:
						self.P_last_mode_state = 0
					elif power <= base - h:
						self.P_last_mode_state = 1

					if self.P_last_mode_state == 0:
						self.buffer_1()
					else:
						self.buffer_2()

				# Dual mode (based on 500 W energy threshold, with hysteresis) | --- Dual mód (500W energetika alapján, hiszterézissel) ---
				elif Devices[224].sValue == "140" and not Devices[224].TimedOut:
					Domoticz.Debug(('BUFFER dual mode (500 W, percentage hysteresis)' + " | " + ("Dual mód puffer (500W, % hiszterézis)")))
					power = self.aktual_watt
					base = 500
					if self.P_last_mode_state == 0:
						power += base
					h = int(base * int(Devices[85].sValue) / 100)
					Domoticz.Debug(f"Power={power} W, base={base} W, hysteresis=±{h} W | Teljesítmény={power} W, alapérték={base} W, hiszterézis=±{h} W")

					if power >= base + h:
						self.P_last_mode_state = 0
					elif power <= base - h:
						self.P_last_mode_state = 1

					if self.P_last_mode_state == 0:
						self.buffer_1()
						self.buffer_2()
					else:
						self.buffer_2()

				# Dual mode (based on 1000 W energy threshold, with hysteresis) | --- Dual mód (1000W energetika alapján, hiszterézissel) ---
				elif Devices[224].sValue == "150" and not Devices[224].TimedOut:
					Domoticz.Debug(('BUFFER dual mode (1000 W, percentage hysteresis)' + " | " + ("Dual mód puffer (1000W, % hiszterézis)")))
					power = self.aktual_watt
					base = 1000
					if self.P_last_mode_state == 0:
						power += base
					h = int(base * int(Devices[85].sValue) / 100)
					Domoticz.Debug(f"Power={power} W, base={base} W, hysteresis=±{h} W | Teljesítmény={power} W, alapérték={base} W, hiszterézis=±{h} W")

					if power >= base + h:
						self.P_last_mode_state = 0
					elif power <= base - h:
						self.P_last_mode_state = 1

					if self.P_last_mode_state == 0:
						self.buffer_1()
						self.buffer_2()
					else:
						self.buffer_2()

				# Dual mode (based on 1500 W energy threshold, with hysteresis) | --- Dual mód (1500W energetika alapján, hiszterézissel) ---
				elif Devices[224].sValue == "160" and not Devices[224].TimedOut:
					Domoticz.Debug(('BUFFER dual mode (1500 W, percentage hysteresis)' + " | " + ("Dual mód puffer (1500W, % hiszterézis)")))
					power = self.aktual_watt
					base = 1500
					if self.P_last_mode_state == 0:
						power += base
					h = int(base * int(Devices[85].sValue) / 100)
					Domoticz.Debug(f"Power={power} W, base={base} W, hysteresis=±{h} W | Teljesítmény={power} W, alapérték={base} W, hiszterézis=±{h} W")

					if power >= base + h:
						self.P_last_mode_state = 0
					elif power <= base - h:
						self.P_last_mode_state = 1

					if self.P_last_mode_state == 0:
						self.buffer_1()
						self.buffer_2()
					else:
						self.buffer_2()

				# Dual mode (based on 2000 W energy threshold, with hysteresis) | --- Dual mód (2000W energetika alapján, hiszterézissel) ---
				elif Devices[224].sValue == "170" and not Devices[224].TimedOut:
					Domoticz.Debug(('BUFFER dual mode (2000 W, percentage hysteresis)' + " | " + ("Dual mód puffer (2000W, % hiszterézis)")))
					power = self.aktual_watt
					base = 2000
					if self.P_last_mode_state == 0:
						power += base
					h = int(base * int(Devices[85].sValue) / 100)
					Domoticz.Debug(f"Power={power} W, base={base} W, hysteresis=±{h} W | Teljesítmény={power} W, alapérték={base} W, hiszterézis=±{h} W")

					if power >= base + h:
						self.P_last_mode_state = 0
					elif power <= base - h:
						self.P_last_mode_state = 1

					if self.P_last_mode_state == 0:
						self.buffer_1()
						self.buffer_2()
					else:
						self.buffer_2()

				# Dual mode (based on 3000 W energy threshold, with hysteresis) | --- Dual mód (3000W energetika alapján, hiszterézissel) ---
				elif Devices[224].sValue == "180" and not Devices[224].TimedOut:
					Domoticz.Debug(('BUFFER dual mode (3000 W, percentage hysteresis)' + " | " + ("Dual mód puffer (3000W, % hiszterézis)")))
					power = self.aktual_watt
					base = 3000
					if self.P_last_mode_state == 0:
						power += base
					h = int(base * int(Devices[85].sValue) / 100)
					Domoticz.Debug(f"Power={power} W, base={base} W, hysteresis=±{h} W | Teljesítmény={power} W, alapérték={base} W, hiszterézis=±{h} W")

					if power >= base + h:
						self.P_last_mode_state = 0
					elif power <= base - h:
						self.P_last_mode_state = 1

					if self.P_last_mode_state == 0:
						self.buffer_1()
						self.buffer_2()
					else:
						self.buffer_2()

				# Dual mode (based on 4000 W energy threshold, with hysteresis) | --- Dual mód (4000W energetika alapján, hiszterézissel) ---
				elif Devices[224].sValue == "190" and not Devices[224].TimedOut:
					Domoticz.Debug(('BUFFER dual mode (4000 W, percentage hysteresis)' + " | " + ("Dual mód puffer (4000W, % hiszterézis)")))
					power = self.aktual_watt
					base = 4000
					if self.P_last_mode_state == 0:
						power += base
					h = int(base * int(Devices[85].sValue) / 100)
					Domoticz.Debug(f"Power={power} W, base={base} W, hysteresis=±{h} W | Teljesítmény={power} W, alapérték={base} W, hiszterézis=±{h} W")

					if power >= base + h:
						self.P_last_mode_state = 0
					elif power <= base - h:
						self.P_last_mode_state = 1

					if self.P_last_mode_state == 0:
						self.buffer_1()
						self.buffer_2()
					else:
						self.buffer_2()

				# Dual mode (based on 5000 W energy threshold, with hysteresis) | --- Dual mód (5000W energetika alapján, hiszterézissel) ---
				elif Devices[224].sValue == "200" and not Devices[224].TimedOut:
					Domoticz.Debug(('BUFFER dual mode (5000 W, percentage hysteresis)' + " | " + ("Dual mód puffer (5000W, % hiszterézis)")))
					power = self.aktual_watt
					base = 5000
					if self.P_last_mode_state == 0:
						power += base
					h = int(base * int(Devices[85].sValue) / 100)
					Domoticz.Debug(f"Power={power} W, base={base} W, hysteresis=±{h} W | Teljesítmény={power} W, alapérték={base} W, hiszterézis=±{h} W")

					if power >= base + h:
						self.P_last_mode_state = 0
					elif power <= base - h:
						self.P_last_mode_state = 1

					if self.P_last_mode_state == 0:
						self.buffer_1()
						self.buffer_2()
					else:
						self.buffer_2()

			else:
				Domoticz.Debug(('BUFFER heating off → switch everything off' + " | " + ("PUFFER H Off → minden kikapcs")))
				self.switchElsodleges_P_H(False)
				self.switchMasodlagos_P_H(False)


			# Close and restart switchcreated so room circulation follows the current state | A switchcreated lezárása és újraindítása, hogy a szobai keringtetés az aktuális állapotot kövesse

			if Devices[66].sValue == "10" and not (self.f1works or self.h1works or self.f2works or self.h2works):
				
				if self.minszoba + self.diffszoba <= self.maxszoba :
					Domoticz.Debug(('Room circulation is active' + " | " + ("Van szoba keringtetes")))
					self.switch_szoba_on(True)
				else :
					Domoticz.Debug(('Room circulation disabled: difference below limit' + " | " + ("Nincs szoba keringtetes limitnel kissebb a diferencia")))
					self.switch_szoba_on(False)
			else :
				Domoticz.Debug(('Room circulation disabled: heating/cooling active' + " | " + ("Nincs szoba keringtetes hutes-futes van")))
				self.switch_szoba_on(False)

			now = time.time()

			self.switchcommand()
			self.statuscommand()

			self.nextupdate = datetime.now() + timedelta(minutes=self.nextupdatetime)
		else: 
			Domoticz.Debug("No update yet; next scheduled update: {0} | Még nem esedékes a frissítés; következő ütemezett frissítés: {0}".format(self.nextupdate))


		# Mark plugin ready after a successful heartbeat | Plugin készenlétének jelzése sikeres heartbeat után
		if Devices[87].sValue != "READY":
			Devices[87].Update(nValue=0, sValue="READY")


	def readTemps(self):

		Domoticz.Debug(('Starting temperature data collection' + " | " + ("Indul a hőmérséklet adatok gyüjtése")))

		noerror = True
		listintemps = []
		listouttemps = []
		listoutdewpoint = []
		listtartalytemps = []
		listpuffertemps = []
		listdewpoint = []
		list_kevero_1 = []
		list_kevero_2 = []
		listszoba = []
		listfrosttemps = []
		self.FrostTemp = None

		# Zone temperature and dew-point lists in a separate dictionary | Zónák hőmérséklet- és harmatpontlistái külön szótárban
		zone_temps = {z: [] for z in range(1, 13)}
		zone_dewpoints = {z: [] for z in range(1, 13)}

		devicesAPI = DomoticzAPI("type=command&param=getdevices&filter=temp&order=Name")

		self.AktualTemp = devicesAPI

		if devicesAPI:
			Domoticz.Debug(('devicesAPI is available' + " | " + ("Van devicesAPI")))
			for device in devicesAPI["result"]:
				idx = int(device["idx"])

				# Outdoor temperature sensors | Külső hőmérséklet-érzékelők
				if idx in self.KulsoTempSensors:
					if "Temp" in device:
						Domoticz.Debug((f'Outdoor: {device["idx"]}-{device["Name"]} = {device["Temp"]}' + " | " + (f"Külső: {device['idx']}-{device['Name']} = {device['Temp']}")))
						if not self.SensorTimedOut(idx, device["Name"], device["LastUpdate"]):
							listouttemps.append(device["Temp"])
							device["HaveTimeout"] = False
							if device["Type"] == "Temp + Humidity":
								dew_value = float(device["DewPoint"])
								listoutdewpoint.append(dew_value)
						else:
							device["HaveTimeout"] = True
					else:
						Domoticz.Debug((f'{device["Name"]} is not a temperature sensor' + " | " + (f"{device['Name']} nem hőmérséklet szenzor")))

				# Tank sensors | Tartályérzékelők
				if idx in self.TartalyTempSensors:
					if "Temp" in device:
						Domoticz.Debug((f'Tank: {device["idx"]}-{device["Name"]} = {device["Temp"]}' + " | " + (f"Tartály: {device['idx']}-{device['Name']} = {device['Temp']}")))
						if not self.SensorTimedOut(idx, device["Name"], device["LastUpdate"]):
							listtartalytemps.append(device["Temp"])
							device["HaveTimeout"] = False
						else:
							device["HaveTimeout"] = True

				# Buffer sensors | Pufferérzékelők
				if idx in self.PufferTempSensors:
					if "Temp" in device:
						Domoticz.Debug((f'Buffer: {device["idx"]}-{device["Name"]} = {device["Temp"]}' + " | " + (f"Puffer: {device['idx']}-{device['Name']} = {device['Temp']}")))
						if not self.SensorTimedOut(idx, device["Name"], device["LastUpdate"]):
							listpuffertemps.append(device["Temp"])
							device["HaveTimeout"] = False
						else:
							device["HaveTimeout"] = True

				# Mixing valve 1 | 1. keverőszelep
				if idx in self.Kevero_1_TempSensor:
					if "Temp" in device:
						Domoticz.Debug((f'Mixing valve 1: {device["idx"]}-{device["Name"]} = {device["Temp"]}' + " | " + (f"Keverő1: {device['idx']}-{device['Name']} = {device['Temp']}")))
						if not self.SensorTimedOut(idx, device["Name"], device["LastUpdate"]):
							list_kevero_1.append(device["Temp"])
							device["HaveTimeout"] = False
						else:
							device["HaveTimeout"] = True

				# Mixing valve 2 | 2. keverőszelep
				if idx in self.Kevero_2_TempSensor:
					if "Temp" in device:
						Domoticz.Debug((f'Mixing valve 2: {device["idx"]}-{device["Name"]} = {device["Temp"]}' + " | " + (f"Keverő2: {device['idx']}-{device['Name']} = {device['Temp']}")))
						if not self.SensorTimedOut(idx, device["Name"], device["LastUpdate"]):
							list_kevero_2.append(device["Temp"])
							device["HaveTimeout"] = False
						else:
							device["HaveTimeout"] = True

				# Frost protection sensors | Fagyvédelmi hőmérők
				if idx in self.FrostTempSensors:
					if "Temp" in device:
						Domoticz.Debug(f'Frost protection: {device["idx"]}-{device["Name"]} = {device["Temp"]} | Fagyvédelem: {device["idx"]}-{device["Name"]} = {device["Temp"]}')
						if not self.SensorTimedOut(idx, device["Name"], device["LastUpdate"]):
							try:
								temp = float(device["Temp"])
								if math.isfinite(temp):
									listfrosttemps.append(temp)
									device["HaveTimeout"] = False
							except (TypeError, ValueError):
								Domoticz.Error(f'Invalid frost temperature: idx={idx} | Érvénytelen fagyvédelmi hőmérséklet: idx={idx}')
						else:
							device["HaveTimeout"] = True

				# Zone sensors | Zónaérzékelők
				for z in range(1, 13):
					sensor_list = getattr(self, f"Zone_TempSensors_{z}", [])
					window_closed = getattr(self, f"zone_{z}_window_closed", True)

					Domoticz.Debug((f'--- Processing zone {z} ---' + " | " + (f"--- Zóna {z} feldolgozása ---")))
					Domoticz.Debug((f'Zone {z} sensor list: {sensor_list}' + " | " + (f"Zóna {z} szenzorlista: {sensor_list}")))
					Domoticz.Debug((f'Window status: {"closed" if window_closed else "open"}' + " | " + (f"Ablak állapot: {'zárva' if window_closed else 'nyitva'}")))

					if not sensor_list:
						Domoticz.Debug((f'No sensors assigned to zone {z}' + " | " + (f"Zóna {z}-ben nincs hozzárendelt szenzor.")))
						continue

					for idx in sensor_list:
						matched = False
						for device in devicesAPI["result"]:
							if int(device["idx"]) == idx:
								matched = True
								Domoticz.Debug((f'Match for zone {z}: {device["idx"]} - {device["Name"]}' + " | " + (f"Találat zóna {z}-hez: {device['idx']} - {device['Name']}")))
								if "Temp" in device:
									Domoticz.Debug((f'Temperature: {device["Temp"]} °C, last update: {device["LastUpdate"]}' + " | " + (f"Hőmérséklet: {device['Temp']} °C, LastUpdate: {device['LastUpdate']}")))
									timed_out = self.SensorTimedOut(idx, device["Name"], device["LastUpdate"])
									device["HaveTimeout"] = not timed_out

									if not timed_out and window_closed:
										zone_temps[z].append(device["Temp"])
										Domoticz.Debug((f'Valid reading added to zone {z} list; total entries: {len(zone_temps[z])}' + " | " + (f"Érvényes adat, hozzáadva zóna {z} listához. "
											       f"Összes elem: {len(zone_temps[z])}")))
										if device["Type"] == "Temp + Humidity":
											dew_value = float(device["DewPoint"])
											zone_dewpoints[z].append(dew_value)
											listdewpoint.append(dew_value)
											Domoticz.Debug((f'Dew point added: {dew_value} °C (zone {z} dew-point entries: {len(zone_dewpoints[z])})' + " | " + (f"Harmatpont hozzáadva: {dew_value} °C "
												       f"(zóna {z} harmatpont lista mérete: {len(zone_dewpoints[z])})")))
									else:
										reason = "időtúllépés" if timed_out else "ablak nyitva"
										Domoticz.Debug((f'Sensor skipped ({reason}) – {device["Name"]}' + " | " + (f"Szenzor kihagyva ({reason}) – {device['Name']}")))
								else:
									Domoticz.Debug((f'{device["idx"]}-{device["Name"]} is not a temperature sensor!' + " | " + (f"{device['idx']}-{device['Name']} nem hőmérséklet szenzor!")))
								break

						if not matched:
							Domoticz.Debug((f'Zone {z}: no device found for idx {idx} in devicesAPI list' + " | " + (f"Zóna {z}: {idx} idx-hez nem találtam eszközt a devicesAPI listában.")))

				# Room sensors | Szobaérzékelők
				if idx in self.szobaTempSensors:
					if "Temp" in device:
						Domoticz.Debug((f'Room: {device["idx"]}-{device["Name"]} = {device["Temp"]}' + " | " + (f"Szoba: {device['idx']}-{device['Name']} = {device['Temp']}")))
						if not self.SensorTimedOut(idx, device["Name"], device["LastUpdate"]):
							listszoba.append(device["Temp"])
							device["HaveTimeout"] = False
						else:
							device["HaveTimeout"] = True

		# Temperature and dew-point calculation | Hőmérséklet és harmatpont számítása

		# Outdoor temperature | Külső hőmérséklet
		nbtemps = len(listouttemps)

		if nbtemps > 0:
			self.outtemp = round(sum(listouttemps) / nbtemps, 1)
		elif self.nowtemp is not None: 
			self.outtemp = self.nowtemp
		else :
			Domoticz.Error('No Outside Temperature found... | Nem található külső hőmérsékleti adat...')
			self.outtemp = 0.0
		
		Devices[69].Update(nValue=0, sValue=str(self.outtemp), TimedOut=False)
		
		# Outdoor dew point | Külső harmatpont
		nboutdewpoint = len(listoutdewpoint)
		if nboutdewpoint > 0:
			self.outdewpoint = round(sum(listoutdewpoint) / nboutdewpoint, 1)
			Domoticz.Debug((f'Outdoor dew point: {self.outdewpoint}' + " | " + (f"Külső harmatpont: {self.outdewpoint}")))
		else:
			self.find_now_dewpoint()
			Domoticz.Debug(('No measured outdoor dew-point value available' + " | " + ("Nem volt mért külső harmatpont érték")))
		
		Domoticz.Debug("Outdoor dew point (self.outdewpoint): {0} | Külső harmatpont (self.outdewpoint): {0}".format(self.outdewpoint))
		Devices[97].Update(nValue=0, sValue=str(self.outdewpoint), TimedOut=False)


		# Indoor dew point | Belső harmatpont
		nbdewpoint = len(listdewpoint)
		if nbdewpoint > 0:
			self.indewpoint = round(sum(listdewpoint) / nbdewpoint, 1)
			self.minindewpoint = min(listdewpoint)
			self.maxindewpoint = max(listdewpoint)
			Domoticz.Debug((f'Dew point: {self.indewpoint}, minimum={self.minindewpoint}, maximum={self.maxindewpoint}' + " | " + (f"Harmatpont: {self.indewpoint}, min={self.minindewpoint}, max={self.maxindewpoint}")))
		else:
			self.indewpoint = 0.0
			Domoticz.Debug(('No valid indoor dew-point value available' + " | " + ("Nincs érvényes belső harmatpont érték")))

		Devices[157].Update(nValue=0, sValue=str(self.indewpoint), TimedOut=False)

		# Average zone temperatures and dew points | Zónahőmérséklet- és harmatpontátlagok
		for z in range(1, 13):
			if zone_temps[z]:
				avg = round(sum(zone_temps[z]) / len(zone_temps[z]), 1)
				setattr(self, f"zone_{z}_aktual_temp", avg)
				listintemps.append(avg)
				Domoticz.Debug((f'Zone {z} temperature: {avg}°C ({len(zone_temps[z])} sensors)' + " | " + (f"Zóna {z} hőmérséklet: {avg}°C ({len(zone_temps[z])} szenzor)")))
			else:
				Domoticz.Debug((f'Zone {z}: no valid temperature data' + " | " + (f"Zóna {z}: nincs érvényes hőmérséklet adat")))

			if zone_dewpoints[z]:
				avg_dew = round(sum(zone_dewpoints[z]) / len(zone_dewpoints[z]), 1)
				setattr(self, f"zone_{z}_aktual_dewpoint", avg_dew)
				Domoticz.Debug((f'Zone {z} dew point: {avg_dew}°C ({len(zone_dewpoints[z])} sensors)' + " | " + (f"Zóna {z} harmatpont: {avg_dew}°C ({len(zone_dewpoints[z])} szenzor)")))

		# Calculate indoor temperature | Belső hőmérséklet kiszámítása
		nbtemps = len(listintemps)
		if nbtemps > 0:
			self.intemp = round(sum(listintemps) / nbtemps, 1)
			self.minintemp = min(listintemps)
			self.maxintemp = max(listintemps)
				
			Domoticz.Debug('Indoor temperature (self.intemp): {0} | Belső hőmérséklet (self.intemp): {0}'.format(self.intemp))
			Domoticz.Debug('Minimum indoor temperature (self.minintemp): {0} | Minimális belső hőmérséklet (self.minintemp): {0}'.format(self.minintemp))
			Domoticz.Debug('Maximum indoor temperature (self.maxintemp): {0} | Maximális belső hőmérséklet (self.maxintemp): {0}'.format(self.maxintemp))

			# Update the virtual device displaying the current temperature | frissítse az áleszközt, amely az aktuális hőmérsékletet mutatja
			Devices[6].Update(nValue=0, sValue=str(self.intemp), TimedOut=False)
			if self.intemperror:  # Indoor temperature was previously marked invalid... restore normal state | korábban érvénytelen belső hőmérséklet jelzés volt... visszaállítás normálra
				self.intemperror = False
				self.WriteLog("Indoor temperature reading valid again: normal operation resumed | A belső hőmérséklet ismét érvényes: visszaállás normál működésre", "Status")
				# Clear the timeout flag on the thermostat switch | Eltávolítjuk az időtúllépés-jelzést a termosztátkapcsolóról
				Devices[1].Update(nValue=Devices[1].nValue, sValue=Devices[1].sValue, TimedOut=False)
			
			if len(self.intemp_avglist) >= int(self.HF_dif_felements) :
				self.intemp_avglist.pop(0)  # Remove the first (oldest) element | Távolítsa el a legelső (legrégebbi) elemet
			
			self.intemp_avglist.append(self.intemp)  # Add a new value to the list | Új érték hozzáadása a listához
			
			# Calculate the average of all current elements | Az összes jelenlegi elem átlagának kiszámítása
			self.intemp_avg = sum(self.intemp_avglist) / len(self.intemp_avglist)
		else:
			# No valid indoor temperature | Nincs érvényes belső hőmérséklet
			noerror = False
			if not self.intemperror:
				self.intemperror = True
				Domoticz.Error('No Inside Temperature found: Switching Off | Nem található belső hőmérsékleti adat: kikapcsolás')
				self.switchElsodleges_F(False)
				self.switchMasodlagos_F(False)
				self.switchElsodleges_H(False)
				self.switchMasodlagos_H(False)
	
				# Mark the thermostat switch and thermometer devices as timed out | A termosztátkapcsolót és a termosztát-hőmérőket is időtúllépettnek jelöljük
				Devices[1].Update(nValue=Devices[1].nValue, sValue=Devices[1].sValue, TimedOut=True)
				Devices[6].Update(nValue=Devices[6].nValue, sValue=Devices[6].sValue, TimedOut=True)

		# Calculate room temperature | Szobahőmérséklet kiszámítása
		Domoticz.Debug("Room list: {0} | Szobák listája: {0}".format(listszoba))
		nszoba = len(listszoba)
		if nszoba > 0:
			self.minszoba = min(listszoba)
			self.maxszoba = max(listszoba)

		# Calculate mean outdoor temperature | Átlagos külső hőmérséklet kiszámítása
		
		Domoticz.Debug("Read temperature; self.ido: {0} | Hőmérséklet-olvasás; self.ido: {0}".format(self.ido))
		
		Domoticz.Debug("Read temperature; self.met_data_string: {0} | Hőmérséklet-olvasás; self.met_data_string: {0}".format(self.met_data_string))

		if self.met_data_string :
			Domoticz.Debug(('self.met_data_string is available' + " | " + ("A self.met_data_string rendelkezésre áll")))
			self.find_future_temperature()

			if self.closest_temp is not None:
				self.FutureTemp = float(self.closest_temp)
			else:
				self.FutureTemp = self.outtemp
				Domoticz.Error('Error calculating self.closest_temp | Hiba a self.closest_temp kiszámításakor')

			Devices[131].Update(nValue=0, sValue=str(self.FutureTemp), TimedOut=False)

		else:
			Domoticz.Debug(('self.ido and/or self.met_data_string is missing' + " | " + ("Hiányzik a self.ido és/vagy a self.met_data_string")))
			self.FutureTemp = self.outtemp
			Devices[131].Update(nValue=0, sValue=str(0), TimedOut=False)

		
		Domoticz.Debug("Outdoor temperature list: {0} | Külső hőmérsékletek listája: {0}".format(listouttemps))
		Domoticz.Debug("Current temperature (self.nowtemp): {0} | Aktuális hőmérséklet (self.nowtemp): {0}".format(self.nowtemp))

		nbtemps = len(listouttemps)
		
		if nbtemps > 0:
			self.outtemp = round(sum(listouttemps) / nbtemps, 1)
		elif self.nowtemp is not None: 
			self.outtemp = self.nowtemp
		else :
			Domoticz.Error('No Outside Temperature found... | Nem található külső hőmérsékleti adat...')
			self.outtemp = 0.0

		Devices[69].Update(nValue=0, sValue=str(self.outtemp), TimedOut=False)

		# Calculate average frost protection temperature | Fagyvédelmi átlaghőmérséklet meghatározása
		if listfrosttemps:
			self.FrostTemp = round(sum(listfrosttemps) / len(listfrosttemps), 1)
			Domoticz.Debug(f'Frost protection average temperature: {self.FrostTemp}°C | Fagyvédelmi átlaghőmérséklet: {self.FrostTemp}°C')
		else:
			self.FrostTemp = None

		# Calculate mean tank temperature | Átlagos tartályhőmérséklet kiszámítása
		Domoticz.Debug("Tank temperature list: {0} | Tartályhőmérsékletek listája: {0}".format(listtartalytemps))
		nbtemps = len(listtartalytemps)
		if nbtemps > 0:
			self.TartalyAktual = round(sum(listtartalytemps) / nbtemps, 1)
			# Update the virtual device displaying the current temperature | frissítse az áleszközt, amely az aktuális hőmérsékletet mutatja
			Devices[19].Update(nValue=0, sValue=str(self.TartalyAktual), TimedOut=False)
			if self.tartalytemperror:  # Indoor temperature was previously marked invalid... restore normal state | korábban érvénytelen belső hőmérséklet jelzés volt... visszaállítás normálra
				self.tartalytemperror = False
				self.WriteLog("Tank temperature reading valid again: normal operation resumed | A tartályhőmérséklet ismét érvényes: visszaállás normál működésre", "Status")
				# Clear the timeout flag on the thermostat switch | Eltávolítjuk az időtúllépés-jelzést a termosztátkapcsolóról
				Devices[13].Update(nValue=Devices[13].nValue, sValue=Devices[13].sValue, TimedOut=False)

			if len(self.TartalyAktuallist) >= int(self.dhw_dif_felements) :
				self.TartalyAktuallist.pop(0)  # Remove the first (oldest) element | Távolítsa el a legelső (legrégebbi) elemet
			
			self.TartalyAktuallist.append(self.TartalyAktual)  # Add a new value to the list | Új érték hozzáadása a listához
			
			# Calculate the average of all current elements | Az összes jelenlegi elem átlagának kiszámítása
			self.TartalyAktualDiff = sum(self.TartalyAktuallist) / len(self.TartalyAktuallist)
		else:
			# No valid tank temperature | Nincs érvényes tartályhőmérséklet
			noerror = False
			self.tartalytemperror = True
			self.switchElsodleges_M(False)
			self.switchMasodlagos_M(False)
			self.switchElsodleges_E(False)
			self.switchMasodlagos_E(False)
			# Mark the DHW switch and tank thermometers as timed out | A HMV-kapcsolót és a tartály-hőmérőket is időtúllépettnek jelöljük
			Devices[13].Update(nValue=Devices[13].nValue, sValue=Devices[13].sValue, TimedOut=True)
			Devices[19].Update(nValue=Devices[19].nValue, sValue=Devices[19].sValue, TimedOut=True)

		# Calculate mean buffer temperature | Átlagos pufferhőmérséklet kiszámítása
		Domoticz.Debug("Buffer temperature list: {0} | Pufferhőmérsékletek listája: {0}".format(listpuffertemps))
		nbtemps = len(listpuffertemps)
		if nbtemps > 0:
			self.PufferAktual = round(sum(listpuffertemps) / nbtemps, 1)
			# Update the virtual device displaying the current temperature | frissítse az áleszközt, amely az aktuális hőmérsékletet mutatja
			Devices[105].Update(nValue=0, sValue=str(self.PufferAktual), TimedOut=False)
			if self.puffertemperror:  # Indoor temperature was previously marked invalid... restore normal state | korábban érvénytelen belső hőmérséklet jelzés volt... visszaállítás normálra
				self.puffertemperror = False
				self.WriteLog("Buffer temperature reading valid again: normal operation resumed | A pufferhőmérséklet ismét érvényes: visszaállás normál működésre", "Status")
				# Clear the timeout flag on the thermostat switch | Eltávolítjuk az időtúllépés-jelzést a termosztátkapcsolóról
				Devices[104].Update(nValue=Devices[104].nValue, sValue=Devices[104].sValue, TimedOut=False)

			if len(self.PufferAktuallist) >= int(self.P_dif_felements) :
					self.PufferAktuallist.pop(0)  # Remove the first (oldest) element | Távolítsa el a legelső (legrégebbi) elemet
			
			self.PufferAktuallist.append(self.PufferAktual)  # Add a new value to the list | Új érték hozzáadása a listához
			
			# Calculate the average of all current elements | Az összes jelenlegi elem átlagának kiszámítása
			self.PufferAktualDiff = sum(self.PufferAktuallist) / len(self.PufferAktuallist)

		else:
			# No valid buffer temperature | Nincs érvényes pufferhőmérséklet
			noerror = False
			if not self.puffertemperror:
				self.puffertemperror = True
				self.switchElsodleges_P_F(False)
				self.switchMasodlagos_P_F(False)
				self.switchElsodleges_P_H(False)
				self.switchMasodlagos_P_H(False)
				# Mark the buffer switch and buffer thermometers as timed out | A pufferkapcsolót és a puffer-hőmérőket is időtúllépettnek jelöljük
				Devices[104].Update(nValue=Devices[104].nValue, sValue=Devices[104].sValue, TimedOut=True)
				Devices[105].Update(nValue=Devices[105].nValue, sValue=Devices[105].sValue, TimedOut=True)
				Devices[224].Update(nValue=Devices[224].nValue, sValue=Devices[224].sValue, TimedOut=True)
		
		# Calculate supply temperature of mixing valve 1 | Az 1. keverőszelep előremenő hőmérsékletének kiszámítása
		nbtemps = len(list_kevero_1)
		if nbtemps > 0:
			self.Kevero_1_temp_aktual = round(sum(list_kevero_1) / nbtemps, 1)
			Devices[152].Update(nValue=0, sValue=str(self.Kevero_1_temp_aktual), TimedOut=False)
		else:
			Domoticz.Debug(('No temperature reading for mixing valve 1...' + " | " + ("Nincs keverőszelep 1 hőmérséklet...")))
			self.Kevero_1_temp_aktual = 90
			if Devices[58].sValue == "10" :
				self.switch_kevero_1_plusz(False)
				self.switch_kevero_1_minusz(True)
			else :
				self.switch_kevero_1_minusz(False)
				self.switch_kevero_1_plusz(True)

		# Calculate supply temperature of mixing valve 2 | A 2. keverőszelep előremenő hőmérsékletének kiszámítása
		nbtemps = len(list_kevero_2)
		if nbtemps > 0:
			self.Kevero_2_temp_aktual = round(sum(list_kevero_2) / nbtemps, 1)
			Devices[153].Update(nValue=0, sValue=str(self.Kevero_2_temp_aktual), TimedOut=False)
		else:
			Domoticz.Debug(('No temperature reading for mixing valve 2...' + " | " + ("Nincs keverőszelep 2 hőmérséklet...")))
			self.Kevero_2_temp_aktual = 90
			if Devices[58].sValue == "10" :
				self.switch_kevero_2_plusz(False)
				self.switch_kevero_2_minusz(True)
			else :
				self.switch_kevero_2_minusz(False)
				self.switch_kevero_2_plusz(True)

		return noerror

	def update_window_states(self):

		Domoticz.Debug(('update_window_states() called' + " | " + ("update_window_states() hívva")))

		# List of zones | Zónák listája
		zones = [
			self.zone_1_window, self.zone_2_window, self.zone_3_window, self.zone_4_window,
			self.zone_5_window, self.zone_6_window, self.zone_7_window, self.zone_8_window,
			self.zone_9_window, self.zone_10_window, self.zone_11_window, self.zone_12_window
		]

		zone_states = [True] * 12
		Domoticz.Debug((f'Initialized zone_states: {zone_states}' + " | " + (f"Inicializált zone_states: {zone_states}")))

		# API call | API-hívás
		devicesAPI = DomoticzAPI(
			"type=devices&filter=light&order=Name"
			if float(Parameters["DomoticzVersion"]) <= 2023.1
			else "type=command&param=getdevices&filter=light&order=Name"
		)

		if not devicesAPI:
			Domoticz.Error('devicesAPI is empty or None | devicesAPI üres vagy None')
			return

		if "result" not in devicesAPI:
			Domoticz.Error("devicesAPI does not contain the 'result' key | devicesAPI nem tartalmaz 'result' kulcsot")
			return

		Domoticz.Debug((f'devicesAPI result count: {len(devicesAPI["result"])}' + " | " + (f"devicesAPI eredmények száma: {len(devicesAPI['result'])}")))

		# Fetch states | Állapotok lekérdezése
		for device in devicesAPI["result"]:
			try:
				idx = int(device["idx"])
				status = device.get("Status", "N/A")
				Domoticz.Debug((f'Checking: idx={idx}, status={status}' + " | " + (f"Vizsgálat: idx={idx}, Status={status}")))

				for i, zone in enumerate(zones):
					if zone:
						Domoticz.Debug((f'  Zone {i+1} contents: {zone}' + " | " + (f"  Zóna {i+1} tartalom: {zone}")))
						if idx in zone:
							Domoticz.Debug((f'  Match in zone {i+1} for idx {idx}, status: {status}' + " | " + (f"  Találat zóna {i+1}-ben idx {idx}, státusz: {status}")))
							if status in ["Open", "Unlocked", "On"]:
								zone_states[i] = False
							else:
								zone_states[i] = True
			except Exception as e:
				Domoticz.Error((f'Error processing devicesAPI: {str(e)}' + " | " + (f"Hiba a devicesAPI feldolgozásánál: {str(e)}")))

		# Print detailed zone states | Részletes zónaállapotok kiírása
		for i, st in enumerate(zone_states):
			Domoticz.Debug((f'Zone {i+1}: window {"CLOSED" if st else "OPEN"}' + " | " + (f"Zóna {i+1}: ablak {'ZÁRVA' if st else 'NYITVA'}")))

		Domoticz.Debug((f'Updated zone_states: {zone_states}' + " | " + (f"Frissített zone_states: {zone_states}")))

		# Update text devices (IDs 240–251) only if changed | Szöveges eszközök (ID 240–251) frissítése csak változás esetén
		for i, state in enumerate(zone_states):
			unit = 240 + i
			if unit not in Devices:
				Domoticz.Error((f'Device ID {unit} not found in Devices' + " | " + (f"Device ID {unit} nem található a Devices-ben")))
				continue

			current = Devices[unit].sValue.strip()
			new_state = tl.t("Closed") if state else tl.t("Open, cooling-heating off")
			new_nValue = 1 if state else 4

			if current != new_state or Devices[unit].nValue != new_nValue:
				Devices[unit].Update(nValue=new_nValue, sValue=new_state)
				Domoticz.Debug((f'Zone {i+1} (ID {unit}) updated → {new_state} (nValue={new_nValue})' + " | " + (f"Zone {i+1} (ID {unit}) frissítve → {new_state} (nValue={new_nValue})")))
			else:
				Domoticz.Debug((f'Zone {i+1} (ID {unit}) unchanged → {current}' + " | " + (f"Zone {i+1} (ID {unit}) változatlan → {current}")))

		# Update self variables so control logic sees the correct state | A self változók frissítése, hogy a vezérlési logika is a helyes állapotot lássa
		for i, state in enumerate(zone_states):
			setattr(self, f'zone_{i+1}_window_closed', state)
			Domoticz.Debug((f'zone_{i+1}_window_closed set to: {state}' + " | " + (f"zone_{i+1}_window_closed beállítva: {state}")))


	def find_future_temperature(self):

		Domoticz.Debug(('Starting find_future_temperature' + " | " + ("Indul a find_future_temperature")))

		def truncate_to_hour(date_string):
			try:
				return date_string[:13]  # YYYY-MM-DD HH | ÉÉÉÉ-HH-NN ÓÓ
			except Exception as e:
				Domoticz.Error("Date truncation error: date={0}, error={1} | Dátumcsonkolási hiba: dátum={0}, hiba={1}".format(date_string, e))
				return None

		if self.met_data_string is None:
			Domoticz.Error('The value of met_data_string is None. | A met_data_string értéke None.')
			self.closest_temp = 0
			self.nowtemp = 0
			return

		current_time = time.strftime("%Y-%m-%d %H", time.localtime())
		Domoticz.Debug("Current time: {0} | Aktuális idő: {0}".format(current_time))

		if self.ido is None:
			Domoticz.Error('The value of self.ido is None. | A self.ido értéke None.')
			return
		else:
			future_time = time.strftime("%Y-%m-%d %H", time.localtime(time.time() + self.ido * 3600))
			Domoticz.Debug(('Future time: ' + " | " + ("future_time: " + future_time)))

		closest_temp = None
		now_temp = None

		for entry in self.met_data_string:
			try:
				if not isinstance(entry, dict):
					continue

				entry_time = truncate_to_hour(entry.get('time'))

				Domoticz.Debug("Entry: {0} -> {1} | Bejegyzés: {0} -> {1}".format(entry.get("time"), entry_time))

				if entry_time is None:
					continue

				if entry_time == current_time:
					now_temp = entry.get('temp')
					Domoticz.Debug("Matching current time: {0} | Egyező aktuális idő: {0}".format(now_temp))

				if entry_time == future_time:
					closest_temp = entry.get('temp')
					Domoticz.Debug("Matching future time: {0} | Egyező jövőbeli idő: {0}".format(closest_temp))

			except Exception as e:
				Domoticz.Error("Error processing entry: {0}, error: {1} | Hiba a bejegyzés feldolgozásakor: {0}, hiba: {1}".format(entry, e))
				continue

		if closest_temp is None:
			Domoticz.Error("No future data available: {0} | Nem áll rendelkezésre jövőbeli adat: {0}".format(future_time))
			closest_temp = self.outtemp if hasattr(self, 'outtemp') else 0

		if now_temp is None:
			Domoticz.Error("No current data available: {0} | Nem áll rendelkezésre aktuális adat: {0}".format(current_time))
			now_temp = self.outtemp if hasattr(self, 'outtemp') else 0

		try:
			self.closest_temp = float(closest_temp)
		except:
			Domoticz.Error("closest_temp conversion error: {0} | closest_temp átalakítási hiba: {0}".format(closest_temp))
			self.closest_temp = 0

		try:
			self.nowtemp = float(now_temp)
		except:
			Domoticz.Error("now_temp conversion error: {0} | now_temp átalakítási hiba: {0}".format(now_temp))
			self.nowtemp = 0

		Domoticz.Debug("Final result: closest={0}, now={1} | Végső eredmény: legközelebbi={0}, aktuális={1}".format(self.closest_temp, self.nowtemp))

	def find_future_temperature_list(self):

		Domoticz.Debug(('find_future_temperature_list started' + " | " + ("find_future_temperature_list elindult")))

		# Check that met_data_string is not None | Ellenőrizzük, hogy a met_data_string nem None
		if self.met_data_string is None:
			Domoticz.Error('met_data_string is None | A met_data_string értéke None')
			return []

		def to_timestamp(date_string):
			date_format = "%Y-%m-%d %H:%M:%S"
			try:
				return time.mktime(time.strptime(date_string, date_format))
			except ValueError as e:
				Domoticz.Error((f'Invalid date format: {date_string}, error: {e}' + " | " + (f"Érvénytelen dátumformátum: {date_string}, hiba: {e}")))
				return None

		self.future_temperatures = []

		# Iterate through self.met_data_string entries | Végigmegyünk a self.met_data_string lista elemein
		for entry in self.met_data_string:
			try:
				# Check that the entry contains the required keys | Ellenőrizzük, hogy a bejegyzés tartalmazza-e a szükséges kulcsokat
				if 'time' not in entry or 'temp' not in entry:
					Domoticz.Error((f'Missing key in entry: {entry}' + " | " + (f"Hiányzó kulcs a bejegyzésben: {entry}")))
					continue

				# Convert entry time to a timestamp | A bejegyzés idejének átalakítása időbélyeggé
				entry_time = to_timestamp(entry['time'])

				if entry_time is None:
					Domoticz.Error((f'Invalid time format: {entry["time"]}' + " | " + (f"Hibás időformátum: {entry['time']}")))
					continue

				# Consider only future temperatures | Csak a jövőbeli hőmérsékleteket vesszük figyelembe
				if entry_time > time.time():
					self.future_temperatures.append({
						'time': entry['time'],
						'temperature': entry['temp']
					})
					#Domoticz.Debug(f"Added future temperature: {entry['time']}, {entry['temp']} | Hozzáadott jövőbeli hőmérséklet: {entry['time']}, {entry['temp']}")
			except ValueError as e:
				Domoticz.Error((f'Date parsing error for {entry["time"]}: {str(e)}' + " | " + (f"Dátumfeldolgozási hiba a(z) {entry['time']} időpontnál: {str(e)}")))
				continue
			except TypeError as e:
				Domoticz.Error((f'TypeError while processing entry in find_future_temperature_list: {entry}; error: {str(e)}' + " | " + (f"Típushiba a find_future_temperature_list bejegyzésének feldolgozásakor: {entry}; hiba: {str(e)}")))
				continue
			except Exception as e:
				Domoticz.Error((f'Unknown error occurred: {str(e)}' + " | " + (f"Ismeretlen hiba történt: {str(e)}")))
				continue

		# Return the list of future temperatures | A jövőbeli hőmérsékletek listájának visszaadása
		#Domoticz.Debug(f"Future temperatures: {self.future_temperatures} | Jövőbeli hőmérsékletek: {self.future_temperatures}")
		return self.future_temperatures

	def find_now_dewpoint(self):

		if not self.met_data_string:
			Domoticz.Error('self.met_data_string was unavailable; loading it via WeatherForecastAPI() | Nem volt self.met_data_string, betöltés WeatherForecastAPI()-val')
			self.met_data_string = self.WeatherForecastAPI()

		current_hour = time.strftime("%Y-%m-%d %H", time.localtime())

		def extract_current_dew(data):
			for entry in data or []:
				try:
					if (entry.get('time') or '')[:13] == current_hour:
						return entry.get('dewpoint')
				except Exception as e:
					Domoticz.Error((f'Error in entry {entry}: {e}' + " | " + (f"Hiba a bejegyzésnél: {entry}, hiba: {e}")))
			return None

		dew = extract_current_dew(self.met_data_string)

		if dew is None:
			Domoticz.Debug(('No dew point for current hour; refreshing via WeatherForecastAPI()' + " | " + ("Nincs aktuális órára dewpoint, újratöltés WeatherForecastAPI()-val")))
			self.met_data_string = self.WeatherForecastAPI()
			dew = extract_current_dew(self.met_data_string)

		if dew is not None:
			try:
				self.outdewpoint = float(dew)
			except Exception as e:
				Domoticz.Error((f'Invalid dew-point value {dew}: {e}' + " | " + (f"Hibás dewpoint érték: {dew}, hiba: {e}")))
				self.outdewpoint = 0.0
		else:
			self.outdewpoint = 0.0

		Domoticz.Debug(f"Current dew point: {self.outdewpoint} (hour: {current_hour}) | Aktuális harmatpont: {self.outdewpoint} (óra: {current_hour})")
		return self.outdewpoint


	def get_total_watt(self):

		total_watt = 0

		if not self.power_p_1 or int(self.power_p_1) == 0:
			Domoticz.Debug(('get_total_watt: no P1 device configured' + " | " + ("get_total_watt: nincs P1 eszköz beállítva")))
			self.aktual_watt = 0
			return 0
		
		devicesAPI = DomoticzAPI(
			"type=devices&filter=utility&order=Name" 
			if float(Parameters["DomoticzVersion"]) <= 2023.1 
			else "type=command&param=getdevices&filter=utility&order=Name"
		)

		if devicesAPI and "result" in devicesAPI:
			Domoticz.Debug(('devicesAPI is available (utility)' + " | " + ("Van devicesAPI utility")))
			for device in devicesAPI["result"]:
				idx = int(device["idx"])
				if idx == self.power_p_1:
					if "Data" in device:
						Domoticz.Debug("Device: {0}-{1} = {2} | Eszköz: {0}-{1} = {2}".format(device["idx"], device["Name"], device["Data"]))
						watt_value = float(device["Data"].split(";")[-1])
						total_watt += watt_value
					else:
						Domoticz.Debug("Device: {0}-{1} is not a counter | Eszköz: {0}-{1} nem számláló".format(device["idx"], device["Name"]))
		else:
			Domoticz.Error('get_total_watt: no result in the devicesAPI response: {0} | get_total_watt: nincs result a devicesAPI válaszban: {0}'.format(devicesAPI))

		self.aktual_watt = int(total_watt)

		return total_watt


	def zone_temp_read(self):

		# Use the selected mode for the heating/cooling setpoint calculation (10 = normal, 20 = economy) | Fűtési–hűtési célhőmérséklet számításakor az alapjel a kiválasztott módot tükrözze (10 = normál, 20 = takarékos)

		p1_meter_actual = self.aktual_watt + int(self.Internals['power_hc_consumption'])

		Domoticz.Debug("P1 meter actual power = {0} | P1-mérő aktuális teljesítménye = {0}".format(p1_meter_actual))
		
		if Devices[125].sValue == "0" :
			self.solar_hc_limit = 0
		elif Devices[125].sValue == "10" :
			self.solar_hc_limit = 500
		elif Devices[125].sValue == "20" :
			self.solar_hc_limit = 1000
		elif Devices[125].sValue == "30" :
			self.solar_hc_limit = 2000
		elif Devices[125].sValue == "40" :
			self.solar_hc_limit = 3000
		elif Devices[125].sValue == "50" :
			self.solar_hc_limit = 4000
		elif Devices[125].sValue == "60" :
			self.solar_hc_limit = 5000

		if  Devices[58].sValue == "10" :
			self.hc_external_H_limit = None
			self.hc_external_time_H_limit = None

			if Devices[124].sValue == "0" :
				self.hc_external_F_limit = None
				self.hc_external_time_F_limit = None
			elif Devices[124].sValue == "10" :
				self.hc_external_F_limit = float(-5)
				self.hc_external_time_F_limit = None
			elif Devices[124].sValue == "20" :
				self.hc_external_F_limit = 0
				self.hc_external_time_F_limit = None
			elif Devices[124].sValue == "30" :
				self.hc_external_F_limit = float(7)
				self.hc_external_time_F_limit = None
			elif Devices[124].sValue == "40" :
				self.hc_external_F_limit = float(15)
				self.hc_external_time_F_limit = None
			elif Devices[124].sValue == "50" :
				self.hc_external_F_limit = float(20)
				self.hc_external_time_F_limit = None
			elif Devices[124].sValue == "60" :
				self.hc_external_time_F_limit = 6
				self.hc_external_F_limit = None
			elif Devices[124].sValue == "70" :
				self.hc_external_time_F_limit = 8
				self.hc_external_F_limit = None
			elif Devices[124].sValue == "80" :
				self.hc_external_time_F_limit = 12
				self.hc_external_F_limit = None
		else :
			self.hc_external_F_limit = None
			self.hc_external_time_F_limit = None

			if Devices[130].sValue == "0" :
				self.hc_external_H_limit = None
				self.hc_external_time_H_limit = None
			elif Devices[130].sValue == "10" :
				self.hc_external_H_limit = float(20)
				self.hc_external_time_H_limit = None
			elif Devices[130].sValue == "20" :
				self.hc_external_H_limit = float(22)
				self.hc_external_time_H_limit = None
			elif Devices[130].sValue == "30" :
				self.hc_external_H_limit = float(24)
				self.hc_external_time_H_limit = None
			elif Devices[130].sValue == "40" :
				self.hc_external_H_limit = float(26)
				self.hc_external_time_H_limit = None
			elif Devices[130].sValue == "50" :
				self.hc_external_H_limit = float(28)
				self.hc_external_time_H_limit = None
			elif Devices[130].sValue == "60" :
				self.hc_external_time_H_limit = 6
				self.hc_external_H_limit = None
			elif Devices[130].sValue == "70" :
				self.hc_external_time_H_limit = 8
				self.hc_external_H_limit = None
			elif Devices[130].sValue == "80" :
				self.hc_external_time_H_limit = 12
				self.hc_external_H_limit = None
		

		if Devices[2].sValue == "10" :
			fnormaltemp = []
			hnormaltemp =[]
			f_temp = []
			h_temp =[]
			power = [0]
			if self.Zone_TempSensors_1:
				fnormaltemp.append(float(Devices[4].sValue))
				hnormaltemp.append(float(Devices[8].sValue))
			if self.Zone_TempSensors_2:
				fnormaltemp.append(float(Devices[38].sValue))
				hnormaltemp.append(float(Devices[40].sValue))
			if self.Zone_TempSensors_3:
				fnormaltemp.append(float(Devices[42].sValue))
				hnormaltemp.append(float(Devices[44].sValue))
			if self.Zone_TempSensors_4:
				fnormaltemp.append(float(Devices[46].sValue))
				hnormaltemp.append(float(Devices[48].sValue))
			if self.Zone_TempSensors_5:
				fnormaltemp.append(float(Devices[50].sValue))
				hnormaltemp.append(float(Devices[52].sValue))
			if self.Zone_TempSensors_6:
				fnormaltemp.append(float(Devices[54].sValue))
				hnormaltemp.append(float(Devices[56].sValue))
			if self.Zone_TempSensors_7:
				fnormaltemp.append(float(Devices[162].sValue))
				hnormaltemp.append(float(Devices[164].sValue))
			if self.Zone_TempSensors_8:
				fnormaltemp.append(float(Devices[170].sValue))
				hnormaltemp.append(float(Devices[172].sValue))
			if self.Zone_TempSensors_9:
				fnormaltemp.append(float(Devices[178].sValue))
				hnormaltemp.append(float(Devices[180].sValue))
			if self.Zone_TempSensors_10:
				fnormaltemp.append(float(Devices[186].sValue))
				hnormaltemp.append(float(Devices[188].sValue))
			if self.Zone_TempSensors_11:
				fnormaltemp.append(float(Devices[194].sValue))
				hnormaltemp.append(float(Devices[196].sValue))
			if self.Zone_TempSensors_12:
				fnormaltemp.append(float(Devices[202].sValue))
				hnormaltemp.append(float(Devices[204].sValue))

			
			if self.solar_hc_limit != 0 and int(p1_meter_actual) > int(self.solar_hc_limit) :
				f_temp.append(max(fnormaltemp) + float(Devices[126].sValue))
				power.append(self.solar_hc_limit)
			
			if self.current_hour in self.warmest_hours_hc :
				f_temp.append(max(fnormaltemp) + float(Devices[128].sValue))
				power.append(0)
			
			if self.hc_external_F_limit is not None and self.outtemp > self.hc_external_F_limit :
				f_temp.append(max(fnormaltemp) + float(Devices[128].sValue))
				power.append(0)
			
			f_temp.append(max(fnormaltemp))

			if max(f_temp):  # Check that f_temp is not empty | Ellenőrzi, hogy a f_temp lista nem üres
				self.Fsetpoint = max(f_temp)
				self.DualFsetpoint = float(sum(fnormaltemp) / len(fnormaltemp))

			if self.solar_hc_limit != 0 and int(p1_meter_actual) > int(self.solar_hc_limit) :
				h_temp.append(min(hnormaltemp) + float(Devices[127].sValue))
				power.append(self.solar_hc_limit)
			
			if self.current_hour in self.coldest_hours_hc :
				h_temp.append(min(hnormaltemp) + float(Devices[128].sValue))
				power.append(0)
			
			if self.hc_external_H_limit is not None and self.outtemp < self.hc_external_H_limit :
				h_temp.append(min(hnormaltemp) + float(Devices[129].sValue))
				power.append(0)
			
			h_temp.append(min(hnormaltemp))
				
			if min(h_temp):  # Check that h_temp is not empty | Ellenőrzi, hogy a h_temp lista nem üres
				self.Hsetpoint = min(h_temp)
				self.DualHsetpoint = float(sum(hnormaltemp) / len(hnormaltemp))

			self.Internals['power_hc_consumption'] = max(power)

		else:
			
			ftakarektemp = []
			htakarektemp =[]
			f_temp = []
			h_temp =[]
			power = [0]
			if self.Zone_TempSensors_1:
				ftakarektemp.append(float(Devices[5].sValue))
				htakarektemp.append(float(Devices[9].sValue))
			if self.Zone_TempSensors_2:
				ftakarektemp.append(float(Devices[39].sValue))
				htakarektemp.append(float(Devices[41].sValue))
			if self.Zone_TempSensors_3:
				ftakarektemp.append(float(Devices[43].sValue))
				htakarektemp.append(float(Devices[45].sValue))
			if self.Zone_TempSensors_4:
				ftakarektemp.append(float(Devices[47].sValue))
				htakarektemp.append(float(Devices[49].sValue))
			if self.Zone_TempSensors_5:
				ftakarektemp.append(float(Devices[51].sValue))
				htakarektemp.append(float(Devices[53].sValue))
			if self.Zone_TempSensors_6:
				ftakarektemp.append(float(Devices[55].sValue))
				htakarektemp.append(float(Devices[57].sValue))
			if self.Zone_TempSensors_7:
				ftakarektemp.append(float(Devices[163].sValue))
				htakarektemp.append(float(Devices[165].sValue))
			if self.Zone_TempSensors_8:
				ftakarektemp.append(float(Devices[171].sValue))
				htakarektemp.append(float(Devices[173].sValue))
			if self.Zone_TempSensors_9:
				ftakarektemp.append(float(Devices[179].sValue))
				htakarektemp.append(float(Devices[181].sValue))
			if self.Zone_TempSensors_10:
				ftakarektemp.append(float(Devices[187].sValue))
				htakarektemp.append(float(Devices[189].sValue))
			if self.Zone_TempSensors_11:
				ftakarektemp.append(float(Devices[195].sValue))
				htakarektemp.append(float(Devices[197].sValue))
			if self.Zone_TempSensors_12:
				ftakarektemp.append(float(Devices[203].sValue))
				htakarektemp.append(float(Devices[205].sValue))

			
			if self.solar_hc_limit != 0 and int(p1_meter_actual) > int(self.solar_hc_limit) :
				f_temp.append(max(ftakarektemp) + float(Devices[126].sValue))
				power.append(self.solar_hc_limit)
			
			if self.current_hour in self.warmest_hours_hc :
				f_temp.append(max(ftakarektemp) + float(Devices[128].sValue))
				power.append(0)
			
			if self.hc_external_F_limit is not None and self.outtemp > self.hc_external_F_limit :
				f_temp.append(max(ftakarektemp) + float(Devices[128].sValue))
				power.append(0)
			
			f_temp.append(max(ftakarektemp))

			if max(f_temp):  # Check that f_temp is not empty | Ellenőrzi, hogy a f_temp lista nem üres
				self.Fsetpoint = max(f_temp)
				self.DualFsetpoint = float(sum(ftakarektemp) / len(ftakarektemp))

			if self.solar_hc_limit != 0 and int(p1_meter_actual) > int(self.solar_hc_limit) :
				h_temp.append(min(htakarektemp) + float(Devices[127].sValue))
				power.append(self.solar_hc_limit)
			
			if self.current_hour in self.coldest_hours_hc :
				h_temp.append(min(htakarektemp) + float(Devices[129].sValue))
				power.append(0)
			
			if self.hc_external_H_limit is not None and self.outtemp < self.hc_external_H_limit :
				h_temp.append(min(htakarektemp) + float(Devices[129].sValue))
				power.append(0)
			
			h_temp.append(min(htakarektemp))

			if min(h_temp):  # Check that h_temp is not empty | Ellenőrzi, hogy a h_temp lista nem üres
				self.Hsetpoint = min(h_temp)
				self.DualHsetpoint = float(sum(htakarektemp) / len(htakarektemp))


			self.Internals['power_hc_consumption'] = max(power)

		try:
			self.Fsetpoint = float(self.Fsetpoint)
		except (ValueError, TypeError):
			Domoticz.Error(f"Invalid heating setpoint: {self.Fsetpoint} | Érvénytelen fűtési célhőmérséklet: {self.Fsetpoint}")
			self.Fsetpoint = 22.0

		try:
			self.Hsetpoint = float(self.Hsetpoint)
		except (ValueError, TypeError):
			Domoticz.Error(f"Invalid cooling setpoint: {self.Hsetpoint} | Érvénytelen hűtési célhőmérséklet: {self.Hsetpoint}")
			self.Hsetpoint = 24.0


		Devices[10].Update(nValue=0,  sValue=str(round(self.Fsetpoint, 2)), TimedOut=False)

		Devices[20].Update(nValue=0, sValue=str(round(self.Hsetpoint, 2)), TimedOut=False)

		saveUserVar(self)

		if Devices[2].sValue == "10" :
			ft_1 = []
			ft_2 = []
			ft_3 = []
			ft_4 = []
			ft_5 = []
			ft_6 = []
			ft_7 = []
			ft_8 = []
			ft_9 = []
			ft_10 = []
			ft_11 = []
			ft_12 = []
			if self.solar_hc_limit != 0 and int(p1_meter_actual) > int(self.solar_hc_limit) :
				Domoticz.Debug("Solar heating/cooling limit condition: self.solar_hc_limit != 0 and int(p1_meter_actual) > int(self.solar_hc_limit) | Napelemes fűtés/hűtés korlátfeltétele: self.solar_hc_limit != 0 and int(p1_meter_actual) > int(self.solar_hc_limit)")
				ft_1.append(float(Devices[4].sValue) + float(Devices[126].sValue))
				ft_2.append(float(Devices[38].sValue) + float(Devices[132].sValue))
				ft_3.append(float(Devices[42].sValue) + float(Devices[136].sValue))
				ft_4.append(float(Devices[46].sValue) + float(Devices[140].sValue))
				ft_5.append(float(Devices[50].sValue) + float(Devices[144].sValue))
				ft_6.append(float(Devices[54].sValue) + float(Devices[148].sValue))
				ft_7.append(float(Devices[162].sValue) + float(Devices[166].sValue))
				ft_8.append(float(Devices[170].sValue) + float(Devices[174].sValue))
				ft_9.append(float(Devices[178].sValue) + float(Devices[182].sValue))
				ft_10.append(float(Devices[186].sValue) + float(Devices[190].sValue))
				ft_11.append(float(Devices[194].sValue) + float(Devices[198].sValue))
				ft_12.append(float(Devices[202].sValue) + float(Devices[206].sValue))
			
			if self.hc_external_F_limit is not None and self.outtemp > self.hc_external_F_limit or self.current_hour in self.warmest_hours_hc :
				Domoticz.Debug("Cooling external temperature or warmest-hour condition: self.hc_external_F_limit is not None and self.outtemp > self.hc_external_F_limit or self.current_hour in self.warmest_hours_hc | Hűtési külsőhőmérséklet- vagy legmelegebbórás feltétel: self.hc_external_F_limit is not None and self.outtemp > self.hc_external_F_limit or self.current_hour in self.warmest_hours_hc")
				ft_1.append(float(Devices[4].sValue) + float(Devices[128].sValue))
				ft_2.append(float(Devices[38].sValue) + float(Devices[134].sValue))
				ft_3.append(float(Devices[42].sValue) + float(Devices[138].sValue))
				ft_4.append(float(Devices[46].sValue) + float(Devices[142].sValue))
				ft_5.append(float(Devices[50].sValue) + float(Devices[146].sValue))
				ft_6.append(float(Devices[54].sValue) + float(Devices[150].sValue))
				ft_7.append(float(Devices[162].sValue) + float(Devices[168].sValue))
				ft_8.append(float(Devices[170].sValue) + float(Devices[176].sValue))
				ft_9.append(float(Devices[178].sValue) + float(Devices[184].sValue))
				ft_10.append(float(Devices[186].sValue) + float(Devices[192].sValue))
				ft_11.append(float(Devices[194].sValue) + float(Devices[200].sValue))
				ft_12.append(float(Devices[202].sValue) + float(Devices[208].sValue))
			
			if Devices[4].sValue.strip():
				ft_1.append(float(Devices[4].sValue))

			if Devices[38].sValue.strip():
				ft_2.append(float(Devices[38].sValue))

			if Devices[42].sValue.strip():
				ft_3.append(float(Devices[42].sValue))

			if Devices[46].sValue.strip():
				ft_4.append(float(Devices[46].sValue))

			if Devices[50].sValue.strip():
				ft_5.append(float(Devices[50].sValue))

			if Devices[54].sValue.strip():
				ft_6.append(float(Devices[54].sValue))

			if Devices[162].sValue.strip():
				ft_7.append(float(Devices[162].sValue))

			if Devices[170].sValue.strip():
				ft_8.append(float(Devices[170].sValue))

			if Devices[178].sValue.strip():
				ft_9.append(float(Devices[178].sValue))

			if Devices[186].sValue.strip():
				ft_10.append(float(Devices[186].sValue))

			if Devices[194].sValue.strip():
				ft_11.append(float(Devices[194].sValue))

			if Devices[202].sValue.strip():
				ft_12.append(float(Devices[202].sValue))


			ft_list = [ft_1, ft_2, ft_3, ft_4, ft_5, ft_6, ft_7, ft_8, ft_9, ft_10, ft_11, ft_12]

			for i, ft in enumerate(ft_list, start=1):
				if ft and self.F_max >= max(ft):
					setattr(self, f"ftargettemp_{i}", max(ft))
				else:
					setattr(self, f"ftargettemp_{i}", self.F_max)


			ht_1 = []
			ht_2 = []
			ht_3 = []
			ht_4 = []
			ht_5 = []
			ht_6 = []
			ht_7 = []
			ht_8 = []
			ht_9 = []
			ht_10 = []
			ht_11 = []
			ht_12 = []

			if self.solar_hc_limit != 0 and int(p1_meter_actual) > int(self.solar_hc_limit) :
				Domoticz.Debug("Solar heating/cooling limit condition: self.solar_hc_limit != 0 and int(p1_meter_actual) > int(self.solar_hc_limit) | Napelemes fűtés/hűtés korlátfeltétele: self.solar_hc_limit != 0 and int(p1_meter_actual) > int(self.solar_hc_limit)")
				ht_1.append(float(Devices[8].sValue) + float(Devices[127].sValue))
				ht_2.append(float(Devices[40].sValue) + float(Devices[133].sValue))
				ht_3.append(float(Devices[44].sValue) + float(Devices[137].sValue))
				ht_4.append(float(Devices[48].sValue) + float(Devices[141].sValue))
				ht_5.append(float(Devices[52].sValue) + float(Devices[145].sValue))
				ht_6.append(float(Devices[56].sValue) + float(Devices[149].sValue))
				ht_7.append(float(Devices[164].sValue) + float(Devices[167].sValue))
				ht_8.append(float(Devices[172].sValue) + float(Devices[175].sValue))
				ht_9.append(float(Devices[180].sValue) + float(Devices[183].sValue))
				ht_10.append(float(Devices[188].sValue) + float(Devices[191].sValue))
				ht_11.append(float(Devices[196].sValue) + float(Devices[199].sValue))
				ht_12.append(float(Devices[204].sValue) + float(Devices[207].sValue))
			
			if self.hc_external_H_limit is not None and self.outtemp < self.hc_external_H_limit or self.current_hour in self.coldest_hours_hc :
				Domoticz.Debug("Heating external temperature or coldest-hour condition: self.hc_external_H_limit is not None and self.outtemp < self.hc_external_H_limit or self.current_hour in self.coldest_hours_hc | Fűtési külsőhőmérséklet- vagy leghidegebbórás feltétel: self.hc_external_H_limit is not None and self.outtemp < self.hc_external_H_limit or self.current_hour in self.coldest_hours_hc")
				ht_1.append(float(Devices[8].sValue) + float(Devices[129].sValue))
				ht_2.append(float(Devices[40].sValue) + float(Devices[135].sValue))
				ht_3.append(float(Devices[44].sValue) + float(Devices[139].sValue))
				ht_4.append(float(Devices[48].sValue) + float(Devices[143].sValue))
				ht_5.append(float(Devices[52].sValue) + float(Devices[147].sValue))
				ht_6.append(float(Devices[56].sValue) + float(Devices[151].sValue))
				ht_7.append(float(Devices[164].sValue) + float(Devices[169].sValue))
				ht_8.append(float(Devices[172].sValue) + float(Devices[177].sValue))
				ht_9.append(float(Devices[180].sValue) + float(Devices[185].sValue))
				ht_10.append(float(Devices[188].sValue) + float(Devices[193].sValue))
				ht_11.append(float(Devices[196].sValue) + float(Devices[201].sValue))
				ht_12.append(float(Devices[204].sValue) + float(Devices[209].sValue))
			
			if Devices[8].sValue.strip():
				ht_1.append(float(Devices[8].sValue))

			if Devices[40].sValue.strip():
				ht_2.append(float(Devices[40].sValue))

			if Devices[44].sValue.strip():
				ht_3.append(float(Devices[44].sValue))

			if Devices[48].sValue.strip():
				ht_4.append(float(Devices[48].sValue))

			if Devices[52].sValue.strip():
				ht_5.append(float(Devices[52].sValue))

			if Devices[56].sValue.strip():
				ht_6.append(float(Devices[56].sValue))

			if Devices[164].sValue.strip():
				ht_7.append(float(Devices[164].sValue))

			if Devices[172].sValue.strip():
				ht_8.append(float(Devices[172].sValue))

			if Devices[180].sValue.strip():
				ht_9.append(float(Devices[180].sValue))

			if Devices[188].sValue.strip():
				ht_10.append(float(Devices[188].sValue))

			if Devices[196].sValue.strip():
				ht_11.append(float(Devices[196].sValue))

			if Devices[204].sValue.strip():
				ht_12.append(float(Devices[204].sValue))


			ht_list = [ht_1, ht_2, ht_3, ht_4, ht_5, ht_6, ht_7, ht_8, ht_9, ht_10, ht_11, ht_12]

			for i, ht in enumerate(ht_list, start=1):
				if ht and self.H_min <= min(ht):
					setattr(self, f"htargettemp_{i}", min(ht))
				else:
					setattr(self, f"htargettemp_{i}", self.H_min)

		else:
			ft_1 = []
			ft_2 = []
			ft_3 = []
			ft_4 = []
			ft_5 = []
			ft_6 = []
			ft_7 = []
			ft_8 = []
			ft_9 = []
			ft_10 = []
			ft_11 = []
			ft_12 = []

			if self.solar_hc_limit != 0 and int(p1_meter_actual) > int(self.solar_hc_limit) :
				ft_1.append(float(Devices[5].sValue) + float(Devices[126].sValue))
				ft_2.append(float(Devices[39].sValue) + float(Devices[132].sValue))
				ft_3.append(float(Devices[43].sValue) + float(Devices[136].sValue))
				ft_4.append(float(Devices[47].sValue) + float(Devices[140].sValue))
				ft_5.append(float(Devices[51].sValue) + float(Devices[144].sValue))
				ft_6.append(float(Devices[55].sValue) + float(Devices[148].sValue))
				ft_7.append(float(Devices[163].sValue) + float(Devices[166].sValue))
				ft_8.append(float(Devices[171].sValue) + float(Devices[174].sValue))
				ft_9.append(float(Devices[179].sValue) + float(Devices[182].sValue))
				ft_10.append(float(Devices[187].sValue) + float(Devices[190].sValue))
				ft_11.append(float(Devices[195].sValue) + float(Devices[198].sValue))
				ft_12.append(float(Devices[203].sValue) + float(Devices[206].sValue))
			
			if self.hc_external_F_limit is not None and self.outtemp > self.hc_external_F_limit or self.current_hour in self.warmest_hours_hc :
				ft_1.append(float(Devices[5].sValue) + float(Devices[128].sValue))
				ft_2.append(float(Devices[39].sValue) + float(Devices[134].sValue))
				ft_3.append(float(Devices[43].sValue) + float(Devices[138].sValue))
				ft_4.append(float(Devices[47].sValue) + float(Devices[142].sValue))
				ft_5.append(float(Devices[51].sValue) + float(Devices[146].sValue))
				ft_6.append(float(Devices[55].sValue) + float(Devices[150].sValue))
				ft_7.append(float(Devices[163].sValue) + float(Devices[167].sValue))
				ft_8.append(float(Devices[171].sValue) + float(Devices[175].sValue))
				ft_9.append(float(Devices[179].sValue) + float(Devices[183].sValue))
				ft_10.append(float(Devices[187].sValue) + float(Devices[191].sValue))
				ft_11.append(float(Devices[195].sValue) + float(Devices[199].sValue))
				ft_12.append(float(Devices[203].sValue) + float(Devices[207].sValue))
			
			if Devices[5].sValue.strip():
				ft_1.append(float(Devices[5].sValue))

			if Devices[39].sValue.strip():
				ft_2.append(float(Devices[39].sValue))

			if Devices[43].sValue.strip():
				ft_3.append(float(Devices[43].sValue))

			if Devices[47].sValue.strip():
				ft_4.append(float(Devices[47].sValue))

			if Devices[51].sValue.strip():
				ft_5.append(float(Devices[51].sValue))

			if Devices[55].sValue.strip():
				ft_6.append(float(Devices[55].sValue))

			if Devices[163].sValue.strip():
				ft_7.append(float(Devices[163].sValue))

			if Devices[171].sValue.strip():
				ft_8.append(float(Devices[171].sValue))

			if Devices[179].sValue.strip():
				ft_9.append(float(Devices[179].sValue))

			if Devices[187].sValue.strip():
				ft_10.append(float(Devices[187].sValue))
			
			if Devices[195].sValue.strip():
				ft_11.append(float(Devices[195].sValue))

			if Devices[203].sValue.strip():
				ft_12.append(float(Devices[203].sValue))

			
			ft_list = [ft_1, ft_2, ft_3, ft_4, ft_5, ft_6, ft_7, ft_8, ft_9, ft_10, ft_11, ft_12]

			for i, ft in enumerate(ft_list, start=1):
				if ft and self.F_max >= max(ft):
					setattr(self, f"ftargettemp_{i}", max(ft))
				else:
					setattr(self, f"ftargettemp_{i}", self.F_max)

			ht_1 = []
			ht_2 = []
			ht_3 = []
			ht_4 = []
			ht_5 = []
			ht_6 = []
			ht_7 = []
			ht_8 = []
			ht_9 = []
			ht_10 = []
			ht_11 = []
			ht_12 = []
			if self.solar_hc_limit != 0 and int(p1_meter_actual) > int(self.solar_hc_limit) :
				ht_1.append(float(Devices[9].sValue) + float(Devices[127].sValue))
				ht_2.append(float(Devices[41].sValue) + float(Devices[133].sValue))
				ht_3.append(float(Devices[45].sValue) + float(Devices[137].sValue))
				ht_4.append(float(Devices[49].sValue) + float(Devices[141].sValue))
				ht_5.append(float(Devices[53].sValue) + float(Devices[145].sValue))
				ht_6.append(float(Devices[57].sValue) + float(Devices[149].sValue))
				ht_7.append(float(Devices[165].sValue) + float(Devices[167].sValue))
				ht_8.append(float(Devices[173].sValue) + float(Devices[175].sValue))
				ht_9.append(float(Devices[181].sValue) + float(Devices[183].sValue))
				ht_10.append(float(Devices[189].sValue) + float(Devices[191].sValue))
				ht_11.append(float(Devices[197].sValue) + float(Devices[199].sValue))
				ht_12.append(float(Devices[205].sValue) + float(Devices[207].sValue))
			
			if self.hc_external_H_limit is not None and self.outtemp < self.hc_external_H_limit or self.current_hour in self.coldest_hours_hc:
				ht_1.append(float(Devices[9].sValue) + float(Devices[129].sValue))
				ht_2.append(float(Devices[41].sValue) + float(Devices[135].sValue))
				ht_3.append(float(Devices[45].sValue) + float(Devices[139].sValue))
				ht_4.append(float(Devices[49].sValue) + float(Devices[143].sValue))
				ht_5.append(float(Devices[53].sValue) + float(Devices[147].sValue))
				ht_6.append(float(Devices[57].sValue) + float(Devices[151].sValue))
				ht_7.append(float(Devices[165].sValue) + float(Devices[168].sValue))
				ht_8.append(float(Devices[173].sValue) + float(Devices[176].sValue))
				ht_9.append(float(Devices[181].sValue) + float(Devices[184].sValue))
				ht_10.append(float(Devices[189].sValue) + float(Devices[192].sValue))
				ht_11.append(float(Devices[197].sValue) + float(Devices[200].sValue))
				ht_12.append(float(Devices[205].sValue) + float(Devices[208].sValue))

			if Devices[9].sValue.strip():
				ht_1.append(float(Devices[9].sValue))

			if Devices[41].sValue.strip():
				ht_2.append(float(Devices[41].sValue))

			if Devices[45].sValue.strip():
				ht_3.append(float(Devices[45].sValue))

			if Devices[49].sValue.strip():
				ht_4.append(float(Devices[49].sValue))

			if Devices[53].sValue.strip():
				ht_5.append(float(Devices[53].sValue))

			if Devices[57].sValue.strip():
				ht_6.append(float(Devices[57].sValue))

			if Devices[165].sValue.strip():
				ht_7.append(float(Devices[165].sValue))

			if Devices[173].sValue.strip():
				ht_8.append(float(Devices[173].sValue))

			if Devices[181].sValue.strip():
				ht_9.append(float(Devices[181].sValue))

			if Devices[189].sValue.strip():
				ht_10.append(float(Devices[189].sValue))

			if Devices[197].sValue.strip():
				ht_11.append(float(Devices[197].sValue))

			if Devices[205].sValue.strip():
				ht_12.append(float(Devices[205].sValue))

			
			ht_list = [ht_1, ht_2, ht_3, ht_4, ht_5, ht_6, ht_7, ht_8, ht_9, ht_10, ht_11, ht_12]

			for i, ht in enumerate(ht_list, start=1):
				if ht and self.H_min <= min(ht):
					setattr(self, f"htargettemp_{i}", min(ht))
				else:
					setattr(self, f"htargettemp_{i}", self.H_min)


	
	def dhw_temp_read(self) :

		p1_meter_actual = self.aktual_watt + int(self.Internals['power_dhw_consumption'])

		fM = []
		fH = []
		power = []

		if self.solar_dhw_limit != 0 and int(p1_meter_actual) > int(self.solar_dhw_limit):
			Domoticz.Debug(('Surplus energy is available | ' + "Van + energia"))
			power.append(self.solar_dhw_limit)
			fM.append(float(Devices[81].sValue))
			fH.append(float(Devices[80].sValue))
		else:
			Domoticz.Debug(('No surplus energy is available | ' + "Nincs + energia"))

		# Update DHW solar energy-limit status from different messages | A HMV napelemes energiakorlát-állapotának frissítése különböző üzenetek alapján
		if self.solar_dhw_limit == 0:
			power_msg = tl.t("Solar DHW target temperature not set")
		elif int(p1_meter_actual) <= int(self.solar_dhw_limit):
			power_msg = tl.t("Solar panel production below limit")
		elif int(p1_meter_actual) > int(self.solar_dhw_limit):
			power_msg = tl.t("Solar panel production limit reached, DHW target temperature change!")
		else:
			power_msg = tl.t("Unknown status")

		# Set nValue based on power_msg | nValue beállítása a power_msg alapján
		if power_msg.strip() == tl.t("Solar DHW target temperature not set").strip():
			power_nvalue = 0
		elif power_msg.strip() == tl.t("Solar panel production below limit").strip():
			power_nvalue = 2
		elif power_msg.strip() == tl.t("Solar panel production limit reached, DHW target temperature change!").strip():
			power_nvalue = 1
		else:
			power_nvalue = 0  # Default | alapértelmezett

		# Update only when a change has occurred | Csak változás esetén frissít
		if Devices[233].sValue.strip() != power_msg.strip() or Devices[233].nValue != power_nvalue:
			Domoticz.Debug(f"Update: solar limit state changed -> nValue={power_nvalue}, sValue='{power_msg}' | Frissítés: napelemes limit állapot változott -> nValue={power_nvalue}, sValue='{power_msg}'")
			Devices[233].Update(nValue=power_nvalue, sValue=power_msg)
		else:
			Domoticz.Debug(('Solar power limit status has not changed; no update required | ' + "Napelemes limit állapot nem változott, nem frissítünk"))

		
		if self.dhw_external_limit is not None and self.outtemp > self.dhw_external_limit and Devices[83].sValue != "0":
			power.append(0)
			Domoticz.Debug(('It is warmer outdoors | ' + "Kint melegebb van"))
			fM.append(float(Devices[79].sValue))
			fH.append(float(Devices[31].sValue))

			if (
				self.dhw_external_limit is not None
				and self.dhw_external_limit != 0
				and self.outtemp > self.dhw_external_limit
				and Devices[83].sValue != "0"
				and not Devices[79].TimedOut
				and not Devices[31].TimedOut
			):
				power.append(0)
				Domoticz.Debug('POWER OVERRIDE: DHW disabled because outdoor temperature exceeds the external limit | Teljesítmény-felülbírálás: HMV tiltva, mert a külső hőmérséklet meghaladja a megadott határt')

				try:
					fM.append(float(Devices[79].sValue))
					fH.append(float(Devices[31].sValue))
				except Exception as e:
					Domoticz.Error(f"DHW float conversion error (79/31): {e} | HMV float konverziós hiba (79/31): {e}")

			# Status-handling logic | Állapotkezelési logika
			if self.dhw_external_limit in (None, 0):
				out_limit_msg = tl.t("Outdoor temperature dependent DHW target temperature not set")
				out_limit_nvalue = 0
			elif self.outtemp <= self.dhw_external_limit:
				out_limit_msg = tl.t("Outdoor temperature did not reach the DHW setpoint temperature change limit value")
				out_limit_nvalue = 2
			else:
				out_limit_msg = tl.t("Outdoor temperature has reached the limit for DHW target temperature change!")
				out_limit_nvalue = 1

			old_s = Devices[234].sValue or ""

			if old_s.strip() != out_limit_msg.strip() or Devices[234].nValue != out_limit_nvalue:
				Devices[234].Update(
					nValue=out_limit_nvalue,
					sValue=out_limit_msg,
					TimedOut=False
				)

		if self.current_hour in self.warmest_hours_dhw and Devices[83].sValue != "0" :
			power.append(0)
			Domoticz.Debug(('Current period is warm, and it is even warmer now | ' + "Most van meleg ido es ez meg melegebb"))
			fM.append(float(Devices[79].sValue))
			fH.append(float(Devices[31].sValue))
		
		if Devices[32].sValue == "10" :
			power.append(0)
			Domoticz.Debug(('Normal operation | ' + "Normal uzem"))
			fM.append(float(Devices[14].sValue))
			fH.append(float(Devices[17].sValue))
		else:
			power.append(0)
			Domoticz.Debug(('Economy operation | ' + "Takarekos uzem"))
			fM.append(float(Devices[30].sValue))
			fH.append(float(Devices[17].sValue))
			
		if self.tartaly_max >= max(fM) :
			self.M_celhomerseklet = max(fM)
		else :
			self.M_celhomerseklet = self.tartaly_max

		self.M_hiszterezis = min(fH)

		self.disinfection()

		Devices[21].Update(nValue=0, sValue=str(self.M_celhomerseklet), TimedOut=False)
		self.Internals['power_dhw_consumption'] = max(power)
		saveUserVar(self)

	def buffer_temp_read(self) :

		p1_meter_actual = self.aktual_watt + int(self.Internals['power_buffer_consumption'])

		if Devices[58].sValue == "10" :
			pC = []
			pH = []
			power =[]
			if self.solar_puffer_limit != 0 and int(p1_meter_actual) > int(self.solar_puffer_limit) :
				power.append(self.solar_dhw_limit)
				pC.append(float(Devices[94].sValue))
				pH.append(float(Devices[96].sValue))
				
			
			if self.buffer_external_F_limit is not None and self.buffer_external_F_limit and self.outtemp > self.buffer_external_F_limit and self.P_celhomerseklet < float(Devices[82].sValue):
				power.append(0)
				pC.append(float(Devices[82].sValue))
				pH.append(float(Devices[77].sValue))
				Devices[100].Update(nValue=0, sValue=str(self.P_celhomerseklet), TimedOut=False)
			
			if self.current_hour in self.warmest_hours_buffer and self.P_celhomerseklet < float(Devices[96].sValue):
				power.append(0)
				pC.append(float(Devices[82].sValue))
				pH.append(float(Devices[77].sValue))
				Devices[100].Update(nValue=0, sValue=str(self.P_celhomerseklet), TimedOut=False)

			power.append(0)
			pC.append(float(Devices[90].sValue))
			pH.append(float(Devices[92].sValue))

			self.P_celhomerseklet = max(pC)
			self.P_hiszterezis = min(pH)
			Devices[100].Update(nValue=0, sValue=str(self.P_celhomerseklet), TimedOut=False)
			self.Internals['power_dhw_consumption'] = max(power)
			saveUserVar(self)

		else :
			pC = []
			pH = []
			power =[]
			if self.solar_puffer_limit != 0 and int(p1_meter_actual) > int(self.solar_puffer_limit) :
				power.append(self.solar_dhw_limit)
				pC.append(float(Devices[93].sValue))
				pH.append(float(Devices[96].sValue))

			if self.buffer_external_H_limit is not None and self.buffer_external_H_limit and self.outtemp < self.buffer_external_H_limit and self.P_celhomerseklet > float(Devices[95].sValue):
				power.append(0)
				pC.append(float(Devices[95].sValue))
				self.P_hiszterezis = float(Devices[77].sValue)
			
			if self.current_hour in self.coldest_hours_buffer and self.P_celhomerseklet > float(Devices[95].sValue) :
				power.append(0)
				pC.append(float(Devices[95].sValue))
				pH.append(float(Devices[77].sValue))
			
			power.append(0)
			pC.append(float(Devices[91].sValue))
			pH.append(float(Devices[123].sValue))
			
			pC_max = max(pC)

			if pC_max > self.buffer_max :
				self.P_celhomerseklet = self.buffer_max
			elif pC_max < self.buffer_min :
				self.P_celhomerseklet = self.buffer_min
			else :
				self.P_celhomerseklet = pC_max

			self.P_hiszterezis = min(pH)
			Devices[100].Update(nValue=0, sValue=str(self.P_celhomerseklet), TimedOut=False)
			self.Internals['power_dhw_consumption'] = max(power)
			saveUserVar(self)
	
	def dhw_timer (self):
		
		Domoticz.Debug("DHW timer start, self.dhw_time_run: {0} | HMV-időzítő kezdete, self.dhw_time_run: {0}".format(self.dhw_time_run))

		if (self.device_dhw_max_time > 0 and Devices[65].sValue != "0" and Devices[13].sValue != "0") :
			Domoticz.Debug(('Timer is running | ' + "Fut az idozito"))

			# Convert uploaded value to datetime | A feltöltött érték átalakítása datetime típussá
			raw_val = self.Internals['switchTimer_dhw']
			if raw_val != 0 and isinstance(raw_val, str):
				try:
					self.switchTimer_dhw = datetime.fromisoformat(raw_val)
				except:
					self.switchTimer_dhw = 0
			else:
				self.switchTimer_dhw = raw_val

			Domoticz.Debug('DHW switch timer | HMV kapcsolási időzítő: '+ format(self.switchTimer_dhw))
			Domoticz.Debug("Current date and time: {0} | Aktuális dátum és idő: {0}".format(datetime.now()))

			if self.switchTimer_dhw == 0 :
				Domoticz.Debug(('self.switchTimer_dhw == 0 | ' + "A HMV-kapcsolási időzítő értéke nulla"))
				self.Internals['switchTimer_dhw'] = datetime.now() + timedelta(minutes=self.device_dhw_max_time)
				saveUserVar(self)
				self.dhw_time_run = True

			else :
				if self.switchTimer_dhw < datetime.now() :
					Domoticz.Debug(('Timer has elapsed; switching is required | ' + "Lejárt az időzítő; váltás szükséges"))
					self.Internals['switchTimer_dhw'] = datetime.now() + timedelta(minutes=self.device_dhw_max_time)
					saveUserVar(self)
					if self.dhw_time_run :
						self.dhw_time_run = False
						Domoticz.Debug(('self.dhw_time_run = False | ' + "A HMV-időzített üzem kikapcsolva"))
					else :
						self.dhw_time_run = True
						Domoticz.Debug(('self.dhw_time_run = True | ' + "A HMV-időzített üzem bekapcsolva"))
				else :
					Domoticz.Debug(('Timer has not elapsed; no switching yet | ' + "Az időzítő még nem járt le; nincs váltás"))

		else :
			self.dhw_time_run = False
			Domoticz.Debug(('Timer is not running | ' + "Az időzítő nem fut"))
		
		Domoticz.Debug("DHW timer end, self.dhw_time_run: {0} | HMV-időzítő vége, self.dhw_time_run: {0}".format(self.dhw_time_run))



	def disinfection(self):

		now = datetime.now()
		today = now.isoweekday()
		yesterday = 7 if today == 1 else today - 1

		# Disinfection schedule diagnostics | Fertőtlenítési időzítés diagnosztikája
		Domoticz.Debug(f"[DISINFECTION] START: now={now}, today={today}, yesterday={yesterday}, Tank_1_N={self.Tank_1_N}, Tank_1_O={self.Tank_1_O}, Tank_2_N={self.Tank_2_N}, Tank_2_O={self.Tank_2_O}, complete={self.disinfection_complete} | [FERTŐTLENÍTÉS] INDULÁS: idő={now}, nap={today}, előző_nap={yesterday}, 1_napok={self.Tank_1_N}, 1_óra={self.Tank_1_O}, 2_napok={self.Tank_2_N}, 2_óra={self.Tank_2_O}, teljesítve={self.disinfection_complete}")

		# Check primary disinfection schedule | Elsődleges fertőtlenítési időzítés ellenőrzése
		start_1 = now.replace(hour=int(self.Tank_1_O), minute=0, second=0, microsecond=0)
		active_1 = ((today in self.Tank_1_N and start_1 <= now < start_1 + timedelta(hours=6)) or (yesterday in self.Tank_1_N and start_1 - timedelta(days=1) <= now < start_1 - timedelta(days=1) + timedelta(hours=6)))

		# Check secondary disinfection schedule | Másodlagos fertőtlenítési időzítés ellenőrzése
		start_2 = now.replace(hour=int(self.Tank_2_O), minute=0, second=0, microsecond=0)
		active_2 = ((today in self.Tank_2_N and start_2 <= now < start_2 + timedelta(hours=6)) or (yesterday in self.Tank_2_N and start_2 - timedelta(days=1) <= now < start_2 - timedelta(days=1) + timedelta(hours=6)))

		# Log calculated disinfection windows | Számított fertőtlenítési időablakok naplózása
		Domoticz.Debug(f"[DISINFECTION] WINDOWS: active_1={active_1}, start_1={start_1}, active_2={active_2}, start_2={start_2} | [FERTŐTLENÍTÉS] IDŐABLAKOK: aktív_1={active_1}, kezdés_1={start_1}, aktív_2={active_2}, kezdés_2={start_2}")

		# Reset completion outside the scheduled window | Teljesítés törlése az időablakon kívül
		if not active_1 and not active_2:
			self.disinfection_complete = False
			Domoticz.Debug("[DISINFECTION] STOP: outside both time windows, resetting completion | [FERTŐTLENÍTÉS] LEÁLLÁS: mindkét időablakon kívül, teljesítés törölve")
			return

		# Do not repeat completed disinfection | Teljesített fertőtlenítés ismétlésének tiltása
		if self.disinfection_complete:
			Domoticz.Debug("[DISINFECTION] STOP: disinfection already completed | [FERTŐTLENÍTÉS] LEÁLLÁS: fertőtlenítés már teljesítve")
			return

		target = float(Devices[76].sValue)
		tank_temp = float(self.TartalyAktual)

		# Log current tank and target temperatures | Aktuális tartály- és célhőmérséklet naplózása
		Domoticz.Debug(f"[DISINFECTION] TEMPERATURE: tank={tank_temp}, target={target}, reached={tank_temp >= target} | [FERTŐTLENÍTÉS] HŐMÉRSÉKLET: tartály={tank_temp}, cél={target}, elérte={tank_temp >= target}")

		# Mark disinfection complete when target is reached | Fertőtlenítés teljesítése a célhőmérséklet elérésekor
		if tank_temp >= target:
			self.disinfection_complete = True
			Domoticz.Debug("[DISINFECTION] COMPLETE: tank reached target temperature | [FERTŐTLENÍTÉS] TELJESÍTVE: a tartály elérte a célhőmérsékletet")
			return

		# Device 1 disinfection | 1. eszköz fertőtlenítése
		if active_1:
			Domoticz.Debug("[DISINFECTION] DEVICE 1: active, setting target and calling dhw_1() | [FERTŐTLENÍTÉS] 1. ESZKÖZ: aktív, célhőmérséklet beállítása és dhw_1() hívása")
			self.M_celhomerseklet = target
		else:
			Domoticz.Debug("[DISINFECTION] DEVICE 1: no active disinfection period | [FERTŐTLENÍTÉS] 1. ESZKÖZ: nincs aktív fertőtlenítési időszak")

		# Device 2 disinfection | 2. eszköz fertőtlenítése
		if active_2:
			Domoticz.Debug("[DISINFECTION] DEVICE 2: active, setting target and calling dhw_2() | [FERTŐTLENÍTÉS] 2. ESZKÖZ: aktív, célhőmérséklet beállítása és dhw_2() hívása")
			self.M_celhomerseklet = target
		else:
			Domoticz.Debug("[DISINFECTION] DEVICE 2: no active disinfection period | [FERTŐTLENÍTÉS] 2. ESZKÖZ: nincs aktív fertőtlenítési időszak")

		# Disinfection function finished | Fertőtlenítési függvény befejeződött
		Domoticz.Debug(f"[DISINFECTION] END: complete={self.disinfection_complete}, DHW_target={self.M_celhomerseklet} | [FERTŐTLENÍTÉS] VÉGE: teljesítve={self.disinfection_complete}, HMV_cél={self.M_celhomerseklet}")


	def buffer_1(self) :
		
		self.switchMasodlagos_P_F(False)
		self.switchMasodlagos_P_H(False)
		self.switchMasodlagos_PE(False)

		Domoticz.Debug(f"Mode (Devices[2]) = {Devices[2].sValue} | Üzemmód (Devices[2]) = {Devices[2].sValue}")
		Domoticz.Debug(f"Current buffer temperature = {self.PufferAktual:.1f} °C | Aktuális pufferhőmérséklet = {self.PufferAktual:.1f} °C")
		Domoticz.Debug(f"Buffer target temperature = {self.P_celhomerseklet:.1f} °C | Puffer célhőmérséklete = {self.P_celhomerseklet:.1f} °C")
		Domoticz.Debug(f"Buffer hysteresis = {self.P_hiszterezis:.1f} °C | Puffer hiszterézise = {self.P_hiszterezis:.1f} °C")
		Domoticz.Debug("Previous buffer status = {0} | Korábbi pufferállapot = {0}".format(int(self.PufferLast)))

		Domoticz.Debug(f"Outside temperature = {self.outtemp:.1f} °C | Külső hőmérséklet = {self.outtemp:.1f} °C")
		Domoticz.Debug(f"Primary E threshold (Devices[110]) = {float(Devices[110].sValue):.1f} °C | 1 E határ (Devices[110]) = {float(Devices[110].sValue):.1f} °C")
		Domoticz.Debug(f"Primary E switching limit (Devices[117]) = {float(Devices[117].sValue):.1f} °C | 1 E Kapcsolási limit (Devices[117]) = {float(Devices[117].sValue):.1f} °C")

		if Devices[58].sValue == "10" :
			if self.PufferAktual < self.P_celhomerseklet - self.P_hiszterezis :
				Domoticz.Debug(('Buffer below target minus hysteresis: switch on primary source | ' + "Hidegeb mint a cél - hiszterezis a puffer elsődleges bekapcsolás!"))
				if self.outtemp < float(Devices[110].sValue) and self.Elsodleges_PE :
					Domoticz.Debug(('One device required; buffer E available and outside temperature is below E threshold: switch E on | ' + "1 eszkoz kell, van puffer E es kint hidegebb van mint a E hatar E bekapcs"))
					self.switchElsodleges_PE(True)
					self.switchElsodleges_P_F(False)
				elif self.PufferAktual > float(Devices[117].sValue) and self.Elsodleges_PE :
					Domoticz.Debug(('One device required; buffer E available and tank temperature exceeds its limit: switch E on | ' + "1 eszkoz kell, van puffer E es tartaly melegebb mint a limit E bekapcs"))
					self.switchElsodleges_PE(True)
					self.switchElsodleges_P_F(False)
				else :
					self.switchElsodleges_PE(False)
					self.switchElsodleges_P_F(True)
				self.PufferLast = True

			elif self.PufferLast and self.PufferAktual <= self.P_celhomerseklet :
				Domoticz.Debug(('Within hysteresis band and buffer is being heated: switch on primary source | ' + "Hiszterezis belűl de nem hűl azaz puffer felfűtés, elsődleges bekapcsolás!"))
				if self.outtemp < float(Devices[110].sValue) and self.Elsodleges_PE :
					Domoticz.Debug(('One device required; buffer E available and outside temperature is below E threshold: switch E on | ' + "1 eszkoz kell, van puffer E es kint hidegebb van mint a E hatar E bekapcs"))
					self.switchElsodleges_PE(True)
					self.switchElsodleges_P_F(False)
				elif self.PufferAktual > float(Devices[117].sValue) and self.Elsodleges_PE :
					Domoticz.Debug(('One device required; buffer E available and tank temperature exceeds its limit: switch E on | ' + "1 eszkoz kell, van puffer E es tartaly melegebb mint a limit E bekapcs"))
					self.switchElsodleges_PE(True)
					self.switchElsodleges_P_F(False)
				else :
					self.switchElsodleges_PE(False)
					self.switchElsodleges_P_F(True)
			else : 
				Domoticz.Debug(('Buffer is colder: switch off | ' + "Hidegebb a puffer kikapcsolás"))
				self.switchElsodleges_P_F(False)
				self.switchElsodleges_PE(False)
				self.PufferLast = False
		else :
			if self.PufferAktual > self.P_celhomerseklet - self.P_hiszterezis :
				Domoticz.Debug(('Buffer above target minus hysteresis: switch on primary source | ' + "Melegebb mint a cél - hiszterezis a puffer elsődleges bekapcsolás!"))
				self.switchElsodleges_PE(False)
				self.switchElsodleges_P_H(True)
				self.PufferLast = True

			elif self.PufferLast and self.PufferAktual >= self.P_celhomerseklet :
				Domoticz.Debug(('Within hysteresis band during buffer cooling: switch on primary source | ' + "Hiszterezis belűl puffer lehűtés, elsődleges bekapcsolás!"))
				self.switchElsodleges_PE(False)
				self.switchElsodleges_P_H(True)
			else : 
				Domoticz.Debug(('Cooling: buffer is colder, switch off | ' + "Hűtés hidegebb a puffer kikapcsolás"))
				self.switchElsodleges_P_H(False)
				self.switchElsodleges_PE(False)
				self.PufferLast = False

	def buffer_2(self) :
		
		self.switchElsodleges_P_F(False)
		self.switchElsodleges_P_H(False)
		self.switchElsodleges_PE(False)

		if Devices[58].sValue == "10" :
			if self.PufferAktual < self.P_celhomerseklet - self.P_hiszterezis :
				Domoticz.Debug(('Buffer below target minus hysteresis: switch on secondary source | ' + "Hidegeb mint a cél - hiszterezis a puffer másodlagos bekapcsolás!"))
				if self.outtemp < float(Devices[111].sValue) and self.Masodlagos_PE :
					Domoticz.Debug(('Two devices required; buffer E available and outside temperature below E threshold: switch E on | ' + "2 eszköz kell, van puffer E és kint hidegebb van mint az E határ → E bekapcs"))
					self.switchMasodlagos_PE(True)
					self.switchMasodlagos_P_F(False)
				elif self.PufferAktual > float(Devices[118].sValue) and self.Masodlagos_PE :
					Domoticz.Debug(('Two devices required; buffer E available and tank temperature above limit: switch E on | ' + "2 eszköz kell, van puffer E és tartály melegebb mint a limit → E bekapcs"))
					self.switchMasodlagos_PE(True)
					self.switchMasodlagos_P_F(False)
				else :
					self.switchMasodlagos_PE(False)
					self.switchMasodlagos_P_F(True)
				self.PufferLast = True

			elif self.PufferLast and self.PufferAktual <= self.P_celhomerseklet :
				Domoticz.Debug(('Within hysteresis band during buffer heating: switch on secondary source | ' + "Hiszterézisen belül, puffer felfűtés – másodlagos bekapcsolás"))
				if self.outtemp < float(Devices[111].sValue) and self.Masodlagos_PE :
					self.switchMasodlagos_PE(True)
					self.switchMasodlagos_P_F(False)
				elif self.PufferAktual > float(Devices[118].sValue) and self.Masodlagos_PE :
					self.switchMasodlagos_PE(True)
					self.switchMasodlagos_P_F(False)
				else :
					self.switchMasodlagos_PE(False)
					self.switchMasodlagos_P_F(True)
			else :
				Domoticz.Debug(('Buffer cold: switch off secondary source | ' + "Hideg a puffer – másodlagos kikapcsolás"))
				self.switchMasodlagos_P_F(False)
				self.switchMasodlagos_PE(False)
				self.PufferLast = False

		else :
			if self.PufferAktual > self.P_celhomerseklet - self.P_hiszterezis :
				Domoticz.Debug(('Buffer above target with hysteresis: switch on secondary source | ' + "Melegebb mint a cél – hiszterézis, puffer másodlagos bekapcsolás"))
				self.switchMasodlagos_PE(False)
				self.switchMasodlagos_P_H(True)
				self.PufferLast = True

			elif self.PufferLast and self.PufferAktual >= self.P_celhomerseklet :
				Domoticz.Debug(('Within hysteresis band during buffer cooling: switch on secondary source | ' + "Hiszterézisen belül, puffer lehűtés – másodlagos bekapcsolás"))
				self.switchMasodlagos_PE(False)
				self.switchMasodlagos_P_H(True)
			else :
				Domoticz.Debug(('Buffer cold: switch off secondary source | ' + "Hideg a puffer – másodlagos kikapcsolás"))
				self.switchMasodlagos_P_H(False)
				self.switchMasodlagos_PE(False)
				self.PufferLast = False


	def dhw_1(self) :
		Domoticz.Debug(('Starting dhw_1 | ' + "dhw_1 indul"))

		Domoticz.Debug("Current tank temperature = {0} | TartalyAktual = {0}".format(self.TartalyAktual))
		Domoticz.Debug("Previous tank status = {0} | TartalyLast = {0}".format(self.TartalyLast))

		Domoticz.Debug("M target temperature = {0} | M_celhomerseklet = {0}".format(self.M_celhomerseklet))
		Domoticz.Debug("M hysteresis = {0} | M_hiszterezis = {0}".format(self.M_hiszterezis))
		Domoticz.Debug("Target minus hysteresis = {0} | cél - hiszterézis = {0}".format(self.M_celhomerseklet - self.M_hiszterezis))

		hiszt = float(Devices[15].sValue)
		out_set = float(Devices[35].sValue)

		Domoticz.Debug("Hysteresis = {0} | Hiszterézis (hiszt) = {0}".format(hiszt))
		Domoticz.Debug("Outside setpoint = {0} | Külső beállított érték (out_set) = {0}".format(out_set))
		Domoticz.Debug("Outside temperature = {0} | Külső hőmérséklet (outtemp) = {0}".format(self.outtemp))

		Domoticz.Debug("Primary E status = {0} | Elsődleges E = {0}".format(self.Elsodleges_E))
		Domoticz.Debug("Primary M status = {0} | Elsődleges M = {0}".format(self.Elsodleges_M))

		Domoticz.Debug("Tank limit (Dev115) = {0} | Tartályhatár (Dev115) = {0}".format(Devices[115].sValue))


		self.switchMasodlagos_M(False)
		self.switchMasodlagos_E(False)

		hiszt = float(Devices[15].sValue)
		out_set = float(Devices[35].sValue)

		if self.TartalyAktual < self.M_celhomerseklet - self.M_hiszterezis :
			Domoticz.Debug(('Below target minus hysteresis: switch on primary DHW source | ' + "Hidegeb mint a cél - hiszterezis a hmv elsődleges bekapcsolás!"))
			if self.TartalyAktual > float(Devices[115].sValue) and self.Elsodleges_E :
				Domoticz.Debug(('Below target; one device required, DHW E available and tank temperature above limit: switch E on | ' + "Hidegeb mint a cél - 1 eszkoz kell, van hmv E es tartaly melegebb mint a limit E bekapcs"))
				self.switchElsodleges_E(True)
				self.switchElsodleges_M(False)
			elif self.outtemp < out_set - hiszt and self.Elsodleges_E :
				Domoticz.Debug(('Below target; one device required, DHW E available and outside temperature below E threshold minus hysteresis: switch E on | ' + "Hidegeb mint a cél - 1 eszkoz kell, van hmv E és kint hidegebb van mint a E hatar - hiszterézissel, E bekapcs"))
				self.switchElsodleges_E(True)
				self.switchElsodleges_M(False)
			elif self.outtemp > out_set + hiszt and self.Elsodleges_E :
				Domoticz.Debug(('Below target; outside temperature above threshold plus hysteresis: switch E off | ' + "Hidegeb mint a cél - Kint melegebb van mint a határ + hiszterézis, E kikapcs"))
				self.switchElsodleges_E(False)
				self.dhw_timer()
				self.switchElsodleges_M(True)
			else :
				Domoticz.Debug(('Below target; one device required, DHW E unavailable or outside its threshold | ' + "Hidegeb mint a cél - 1 eszkoz kell hatarertek, nincs vagy hataron kivul hmv E"))
				self.switchElsodleges_E(False)
				self.dhw_timer()
				self.switchElsodleges_M(True)
			
			self.TartalyLast = True
		
		elif self.TartalyLast and self.TartalyAktual <= self.M_celhomerseklet :
			Domoticz.Debug(('Within hysteresis band and DHW heating: switch on primary source | ' + "Hiszterezis belül de nem hűl azaz hmv felfűtés, elsődleges bekapcsolás!"))
			if self.TartalyAktual > float(Devices[115].sValue) and self.Elsodleges_E :
				Domoticz.Debug(('Within hysteresis band; one device required, DHW E available and tank temperature above limit: switch E on | ' + "Hiszterezis belül - 1 eszkoz kell, van hmv E es tartaly melegebb mint a limit E bekapcs"))
				self.switchElsodleges_E(True)
				self.switchElsodleges_M(False)
			elif self.outtemp < out_set - hiszt and self.Elsodleges_E :
				Domoticz.Debug(('Within hysteresis band; one device required, DHW E available and outside temperature below E threshold minus hysteresis: switch E on | ' + "Hiszterezis belül - 1 eszkoz kell, van hmv E és kint hidegebb van mint a E hatar - hiszterézissel, E bekapcs"))
				self.switchElsodleges_E(True)
				self.switchElsodleges_M(False)
			elif self.outtemp > out_set + hiszt and self.Elsodleges_E :
				Domoticz.Debug(('Within hysteresis band; outside temperature above threshold plus hysteresis: switch E off | ' + "Hiszterezis belül - Kint melegebb van mint a határ + hiszterézis, E kikapcs"))
				self.switchElsodleges_E(False)
				self.dhw_timer()
				self.switchElsodleges_M(True)
			
			else :
				Domoticz.Debug(('Within hysteresis band; one device required during heating, DHW E unavailable or outside its threshold | ' + "Hiszterezis belül - 1 eszkoz kell, felfutes, nincs vagy hataron kivul hmv E"))
				self.switchElsodleges_E(False)
				self.switchElsodleges_M(True)

		else : 
			Domoticz.Debug(('DHW is hot: switch off | ' + "Meleg a hmv kikapcsolás"))
			self.switchElsodleges_M(False)
			self.switchElsodleges_E(False)
			self.TartalyLast = False


	def dhw_2(self) :
		Domoticz.Debug(('Starting dhw_2 | ' + "dhw_2 indul"))

		Domoticz.Debug("Current tank temperature = {0} | TartalyAktual = {0}".format(self.TartalyAktual))
		Domoticz.Debug("Previous tank status = {0} | TartalyLast = {0}".format(self.TartalyLast))

		Domoticz.Debug("M target temperature = {0} | M_celhomerseklet = {0}".format(self.M_celhomerseklet))
		Domoticz.Debug("M hysteresis = {0} | M_hiszterezis = {0}".format(self.M_hiszterezis))
		Domoticz.Debug("Target minus hysteresis = {0} | cél - hiszterézis = {0}".format(self.M_celhomerseklet - self.M_hiszterezis))

		hiszt = float(Devices[15].sValue)
		out_set = float(Devices[36].sValue)
		Domoticz.Debug("Outside setpoint (Dev36) = {0} | Külső beállított érték (Dev36) = {0}".format(out_set))


		Domoticz.Debug("Hysteresis = {0} | Hiszterézis (hiszt) = {0}".format(hiszt))
		Domoticz.Debug("Outside setpoint = {0} | Külső beállított érték (out_set) = {0}".format(out_set))
		Domoticz.Debug("Outside temperature = {0} | Külső hőmérséklet (outtemp) = {0}".format(self.outtemp))

		Domoticz.Debug("Secondary E status = {0} | Másodlagos E = {0}".format(self.Masodlagos_E))
		Domoticz.Debug("Secondary M status = {0} | Másodlagos M = {0}".format(self.Masodlagos_M))


		Domoticz.Debug("Tank limit (Dev115) = {0} | Tartályhatár (Dev115) = {0}".format(Devices[115].sValue))
		
		self.switchElsodleges_M(False)
		self.switchElsodleges_E(False)

		hiszt = float(Devices[15].sValue)
		out_set = float(Devices[36].sValue)

		self.dhw_timer()

		if self.TartalyAktual < self.M_celhomerseklet - self.M_hiszterezis :
			Domoticz.Debug(('Below target minus hysteresis: switch on secondary DHW source | ' + "Hidegeb mint a cél - hiszterezis a hmv Masodlagos bekapcsolás!"))
			if self.TartalyAktual > float(Devices[116].sValue) and self.Masodlagos_E :
				Domoticz.Debug(('Below target; two devices required, DHW E available and tank temperature above limit: switch E on | ' + "Hidegeb mint a cél - 2 eszkoz kell, van hmv E és tartaly melegebb mint a limit E bekapcs"))
				self.switchMasodlagos_E(True)
				self.switchMasodlagos_M(False)
			if self.outtemp < out_set - hiszt and self.Masodlagos_E :

				Domoticz.Debug(("Before condition: outdoor temperature compared with the setpoint minus hysteresis | " + ("FELTETEL ELOTT: "+str(self.outtemp)+" < "+str(out_set-hiszt)+" = "+str(self.outtemp < out_set - hiszt))))

				Domoticz.Debug(('Below target; two devices required, DHW E available and outside temperature below E threshold minus hysteresis: switch E on | ' + "Hidegeb mint a cél - 2 eszkoz kell, van hmv E és kint hidegebb van mint a E hatar - hiszterézissel, E bekapcs"))
				self.switchMasodlagos_E(True)
				self.switchMasodlagos_M(False)
			elif self.outtemp > out_set + hiszt and self.Masodlagos_E :
				Domoticz.Debug(('Below target; outside temperature above threshold plus hysteresis: switch E off | ' + "Hidegeb mint a cél - Kint melegebb van mint a határ + hiszterézis, E kikapcs"))
				self.switchMasodlagos_E(False)
				self.switchMasodlagos_M(True)
			else :
				Domoticz.Debug(('Below target; two devices required, DHW E unavailable or outside its threshold | ' + "Hidegeb mint a cél - 2 eszkoz kell hatarertek, nincs vagy hataron kivul hmv E"))
				self.switchMasodlagos_E(False)
				self.switchMasodlagos_M(True)
			
			self.TartalyLast = True

		elif self.TartalyLast and self.TartalyAktual <= self.M_celhomerseklet :
			Domoticz.Debug(('Within hysteresis band and DHW heating: switch on secondary source | ' + "Hiszterezis belül de nem hűl azaz hmv felfűtés, masodlagos bekapcsolás!"))
			if self.TartalyAktual > float(Devices[116].sValue) and self.Masodlagos_E :
				Domoticz.Debug(('Within hysteresis band; two devices required, DHW E available and tank temperature above limit: switch E on | ' + "Hiszterezis belül - 2 eszkoz kell, van hmv E és tartaly melegebb mint a limit E bekapcs"))
				self.switchMasodlagos_E(True)
				self.switchMasodlagos_M(False)
			elif self.outtemp < out_set - hiszt and self.Masodlagos_E :
				Domoticz.Debug(('Within hysteresis band; two devices required, DHW E available and outside temperature below E threshold minus hysteresis: switch E on | ' + "Hiszterezis belül - 2 eszkoz kell, van hmv E és kint hidegebb van mint a E hatar - hiszterézissel, E bekapcs"))
				self.switchMasodlagos_E(True)
				self.switchMasodlagos_M(False)
			elif self.outtemp > out_set + hiszt and self.Masodlagos_E :
				Domoticz.Debug(('Within hysteresis band; outside temperature above threshold plus hysteresis: switch E off | ' + "Hiszterezis belül - Kint melegebb van mint a határ + hiszterézis, E kikapcs"))
				self.switchMasodlagos_E(False)
				self.switchMasodlagos_M(True)
			else :
				Domoticz.Debug(('Within hysteresis band; two devices required during heating, DHW E unavailable or outside its threshold | ' + "Hiszterezis belül - 2 eszkoz kell, felfutes, nincs vagy hataron kivul hmv E"))
				self.switchMasodlagos_E(False)
				self.switchMasodlagos_M(True)

		else : 
			Domoticz.Debug(('DHW is hot: switch off | ' + "Meleg a hmv kikapcsolás"))
			self.switchMasodlagos_M(False)
			self.switchMasodlagos_E(False)
			self.TartalyLast = False

	def find_warmest_hours_today_dhw(self):
		try:
			Domoticz.Debug('Entering find_warmest_hours_today_dhw | Belépés a HMV mai legmelegebb óráit kereső függvénybe')

			def to_timestamp(date_string):
				date_format = "%Y-%m-%d %H:%M:%S"
				try:
					return time.mktime(time.strptime(date_string, date_format))
				except ValueError as e:
					Domoticz.Error(f"Invalid date format: {date_string}, error: {e} | Érvénytelen dátumformátum: {date_string}, hiba: {e}")
					return None

			# Today’s date with timestamp | Mai dátum időbélyeggel
			today_start = time.mktime(time.strptime(time.strftime('%Y-%m-%d 00:00:00'), "%Y-%m-%d %H:%M:%S"))
			today_end = time.mktime(time.strptime(time.strftime('%Y-%m-%d 23:59:59'), "%Y-%m-%d %H:%M:%S"))

			# Check that met_data_string exists and is not empty | Ellenőrizzük, hogy a met_data_string létezik és nem üres
			if not self.met_data_string:
				Domoticz.Error('met_data_string is empty or not initialized. | A met_data_string üres vagy nincs inicializálva.')
				self.warmest_hours_dhw = []
				return self.warmest_hours_dhw

			# Filter values for today | Szűrés a mai dátumhoz tartozó értékekre
			today_data = []
			for entry in self.met_data_string:
				try:
					# Check that entry contains all required keys | Ellenőrizzük, hogy minden szükséges kulcs megtalálható-e az entry-ben
					if 'time' not in entry or 'temp' not in entry:
						Domoticz.Error(f"Missing keys in entry: {entry} | Hiányzó kulcsok a bejegyzésben: {entry}")
						continue

					# Check that 'temp' is not None | Ellenőrizzük, hogy a 'temp' értéke nem None
					if entry['temp'] is None:
						Domoticz.Error(f"Invalid 'temp' value in entry: {entry} | Érvénytelen 'temp' érték a bejegyzésben: {entry}")
						continue

					# Validate date and convert to timestamp | Dátum ellenőrzése és átalakítása időbélyeggé
					entry_timestamp = to_timestamp(entry['time'])
					if entry_timestamp is None:
						continue

					# Add only data for today | Csak a mai naphoz tartozó adatok hozzáadása
					if today_start <= entry_timestamp <= today_end:
						today_data.append((float(entry['temp']), entry_timestamp))
				except (ValueError, KeyError) as e:
					Domoticz.Error(f"Error parsing entry: {entry}, error: {e} | Hiba a bejegyzés feldolgozásakor: {entry}, hiba: {e}")

			# Continue if data is available | Ha van adat, folytatjuk
			if today_data:
				if self.dhw_external_time_limit is None or self.dhw_external_time_limit <= 0:
					Domoticz.Error(f"Invalid DHW external time limit: {self.dhw_external_time_limit} | Érvénytelen HMV külső időkorlát: {self.dhw_external_time_limit}")
					self.warmest_hours_dhw = []
				else:
					# Select the warmest hours | A legmelegebb órák kiválasztása
					warmest_hours_full = heapq.nlargest(self.dhw_external_time_limit, today_data)
					self.warmest_hours_dhw = [time.localtime(hour[1]).tm_hour for hour in warmest_hours_full]
			else:
				Domoticz.Debug('No data available for today. | Nem áll rendelkezésre adat a mai napra.')
				self.warmest_hours_dhw = []

			Domoticz.Debug("Warmest hours for DHW: {0} | A HMV legmelegebb órái: {0}".format(self.warmest_hours_dhw))
			Domoticz.Debug('Exiting find_warmest_hours_today_dhw | Kilépés a HMV mai legmelegebb óráit kereső függvényből')
		except Exception as e:
			Domoticz.Error(f"'find_warmest_hours_today_dhw' failed '{e.__class__.__name__}':'{e}' | A mai legmelegebb HMV-órák keresése sikertelen: '{e.__class__.__name__}':'{e}'")

		return self.warmest_hours_dhw


	def find_warmest_hours_today_buffer(self):
		try:
			Domoticz.Debug('Entering find_warmest_hours_today_buffer | Belépés a puffer mai legmelegebb óráit kereső függvénybe')

			def to_timestamp(date_string):
				date_format = "%Y-%m-%d %H:%M:%S"
				try:
					return time.mktime(time.strptime(date_string, date_format))
				except ValueError as e:
					Domoticz.Error(f"Invalid date format: {date_string}, error: {e} | Érvénytelen dátumformátum: {date_string}, hiba: {e}")
					return None

			# Today’s date with timestamp | Mai dátum időbélyeggel
			today_start = time.mktime(time.strptime(time.strftime('%Y-%m-%d 00:00:00'), "%Y-%m-%d %H:%M:%S"))
			today_end = time.mktime(time.strptime(time.strftime('%Y-%m-%d 23:59:59'), "%Y-%m-%d %H:%M:%S"))

			# Check that met_data_string exists and is not empty | Ellenőrizd, hogy a met_data_string létezik és nem üres
			if not self.met_data_string:
				Domoticz.Error('met_data_string is empty or not initialized. | A met_data_string üres vagy nincs inicializálva.')
				self.warmest_hours_buffer = []
				return self.warmest_hours_buffer

			# Filter values for today | Szűrés a mai dátumhoz tartozó értékekre
			today_data = []
			for entry in self.met_data_string:
				try:
					# Check that entry contains the required keys | Ellenőrizd, hogy az entry tartalmazza a szükséges kulcsokat
					if 'time' not in entry or 'temp' not in entry:
						Domoticz.Error(f"Missing keys in entry: {entry} | Hiányzó kulcsok a bejegyzésben: {entry}")
						continue

					# Convert to timestamp | Átalakítás időbélyeggé
					entry_timestamp = to_timestamp(entry['time'])
					if entry_timestamp is None:
						continue

					# Data belonging only to today | Csak a mai naphoz tartozó adatok
					if today_start <= entry_timestamp <= today_end:
						today_data.append((float(entry['temp']), entry['time']))
				except (ValueError, KeyError) as e:
					Domoticz.Error(f"Error parsing entry: {entry}, error: {e} | Hiba a bejegyzés feldolgozásakor: {entry}, hiba: {e}")

			# Continue if data is available | Ha van adat, folytatjuk
			if today_data:
				if self.buffer_external_time_F_limit > 0:
					warmest_hours_full = heapq.nlargest(self.buffer_external_time_F_limit, today_data)
					self.warmest_hours_buffer = [time.localtime(to_timestamp(hour[1])).tm_hour for hour in warmest_hours_full]
				else:
					Domoticz.Error(f"Invalid buffer heating external time limit: {self.buffer_external_time_F_limit} | Érvénytelen puffer fűtési külső időkorlát: {self.buffer_external_time_F_limit}")
					self.warmest_hours_buffer = []
			else:
				Domoticz.Debug('No data available for today. | Nem áll rendelkezésre adat a mai napra.')
				self.warmest_hours_buffer = []

			Domoticz.Debug("Warmest hours for buffer: {0} | A puffer legmelegebb órái: {0}".format(self.warmest_hours_buffer))
			Domoticz.Debug('Exiting find_warmest_hours_today_buffer | Kilépés a puffer mai legmelegebb óráit kereső függvényből')
		except Exception as e:
			Domoticz.Error(f"'find_warmest_hours_today_buffer' failed '{e.__class__.__name__}':'{e}' | A mai legmelegebb pufferórák keresése sikertelen: '{e.__class__.__name__}':'{e}'")

		return self.warmest_hours_buffer

	def find_coldest_hours_today_buffer(self):
		try:
			Domoticz.Debug('Entering find_coldest_hours_today_buffer | Belépés a puffer mai leghidegebb óráit kereső függvénybe')

			def to_timestamp(date_string):
				date_format = "%Y-%m-%d %H:%M:%S"
				try:
					return time.mktime(time.strptime(date_string, date_format))
				except ValueError as e:
					Domoticz.Error(f"Invalid date format: {date_string}, error: {e} | Érvénytelen dátumformátum: {date_string}, hiba: {e}")
					return None

			# Today’s date with timestamp | Mai dátum időbélyeggel
			today_start = time.mktime(time.strptime(time.strftime('%Y-%m-%d 00:00:00'), "%Y-%m-%d %H:%M:%S"))
			today_end = time.mktime(time.strptime(time.strftime('%Y-%m-%d 23:59:59'), "%Y-%m-%d %H:%M:%S"))

			# Check that met_data_string exists and is not empty | Ellenőrizd, hogy a met_data_string létezik és nem üres
			if not self.met_data_string:
				Domoticz.Error('met_data_string is empty or not initialized. | A met_data_string üres vagy nincs inicializálva.')
				self.coldest_hours_buffer = []
				return self.coldest_hours_buffer

			# Filter values for today | Szűrés a mai dátumhoz tartozó értékekre
			today_data = []
			for entry in self.met_data_string:
				try:
					# Check that entry contains the required keys | Ellenőrizd, hogy az entry tartalmazza a szükséges kulcsokat
					if 'time' not in entry or 'temp' not in entry:
						Domoticz.Error(f"Missing keys in entry: {entry} | Hiányzó kulcsok a bejegyzésben: {entry}")
						continue

					# Convert to timestamp | Átalakítás időbélyeggé
					entry_timestamp = to_timestamp(entry['time'])
					if entry_timestamp is None:
						continue

					# Data belonging only to today | Csak a mai naphoz tartozó adatok
					if today_start <= entry_timestamp <= today_end:
						today_data.append((float(entry['temp']), entry['time']))
				except (ValueError, KeyError) as e:
					Domoticz.Error(f"Error parsing entry: {entry}, error: {e} | Hiba a bejegyzés feldolgozásakor: {entry}, hiba: {e}")

			# Continue if data is available | Ha van adat, folytatjuk
			if today_data:
				if self.buffer_external_time_H_limit > 0:
					coldest_hours_full = heapq.nsmallest(self.buffer_external_time_H_limit, today_data)
					self.coldest_hours_buffer = [time.localtime(to_timestamp(hour[1])).tm_hour for hour in coldest_hours_full]
				else:
					Domoticz.Error(f"Invalid buffer cooling external time limit: {self.buffer_external_time_H_limit} | Érvénytelen puffer hűtési külső időkorlát: {self.buffer_external_time_H_limit}")
					self.coldest_hours_buffer = []
			else:
				Domoticz.Debug('No data available for today. | Nem áll rendelkezésre adat a mai napra.')
				self.coldest_hours_buffer = []

			Domoticz.Debug('Coldest hours for buffer: {0} | A puffer leghidegebb órái: {0}'.format(self.coldest_hours_buffer))
			Domoticz.Debug('Exiting find_coldest_hours_today_buffer | Kilépés a puffer mai leghidegebb óráit kereső függvényből')
		except Exception as e:
			Domoticz.Error(f"'find_coldest_hours_today_buffer' failed '{e.__class__.__name__}':'{e}' | A mai leghidegebb pufferórák keresése sikertelen: '{e.__class__.__name__}':'{e}'")

		return self.coldest_hours_buffer

	def find_warmest_hours_today_hc(self):
		try:
			Domoticz.Debug('Entering find_warmest_hours_today_hc | Belépés a fűtés–hűtés mai legmelegebb óráit kereső függvénybe')

			def to_timestamp(date_string):
				date_format = "%Y-%m-%d %H:%M:%S"
				try:
					return time.mktime(time.strptime(date_string, date_format))
				except ValueError as e:
					Domoticz.Error(f"Invalid date format: {date_string}, error: {e} | Érvénytelen dátumformátum: {date_string}, hiba: {e}")
					return None

			# Today as a timestamp | Mai nap időbélyegként
			today_start = time.mktime(time.strptime(time.strftime('%Y-%m-%d 00:00:00'), "%Y-%m-%d %H:%M:%S"))
			today_end = time.mktime(time.strptime(time.strftime('%Y-%m-%d 23:59:59'), "%Y-%m-%d %H:%M:%S"))

			# Check that met_data_string exists and is not empty | Ellenőrizd, hogy a met_data_string létezik és nem üres
			if not self.met_data_string:
				Domoticz.Error('met_data_string is empty or not initialized. | A met_data_string üres vagy nincs inicializálva.')
				self.warmest_hours_hc = []
				return self.warmest_hours_hc

			# Filter values for today | Szűrés a mai dátumhoz tartozó értékekre
			today_data = []
			for entry in self.met_data_string:
				try:
					# Check that entry contains the required keys | Ellenőrizd, hogy az entry tartalmazza a szükséges kulcsokat
					if 'time' not in entry or 'temp' not in entry:
						Domoticz.Error(f"Missing keys in entry: {entry} | Hiányzó kulcsok a bejegyzésben: {entry}")
						continue

					# Convert to timestamp | Átalakítás időbélyeggé
					entry_timestamp = to_timestamp(entry['time'])
					if entry_timestamp is None:
						continue

					# Data belonging only to today | Csak a mai naphoz tartozó adatok
					if today_start <= entry_timestamp <= today_end:
						today_data.append((float(entry['temp']), entry['time']))
				except (ValueError, KeyError) as e:
					Domoticz.Error(f"Error parsing entry: {entry}, error: {e} | Hiba a bejegyzés feldolgozásakor: {entry}, hiba: {e}")

			# Continue if data is available | Ha van adat, folytatjuk
			if today_data:
				if self.hc_external_time_F_limit > 0:
					warmest_hours_full = heapq.nlargest(self.hc_external_time_F_limit, today_data)
					self.warmest_hours_hc = [time.localtime(to_timestamp(hour[1])).tm_hour for hour in warmest_hours_full]
				else:
					Domoticz.Error(f"Invalid heating external time limit: {self.hc_external_time_F_limit} | Érvénytelen fűtési külső időkorlát: {self.hc_external_time_F_limit}")
					self.warmest_hours_hc = []
			else:
				Domoticz.Debug('No data available for today. | Nem áll rendelkezésre adat a mai napra.')
				self.warmest_hours_hc = []

			Domoticz.Debug("Warmest hours for heating/cooling: {0} | A fűtés/hűtés legmelegebb órái: {0}".format(self.warmest_hours_hc))
			Domoticz.Debug('Exiting find_warmest_hours_today_hc | Kilépés a fűtés–hűtés mai legmelegebb óráit kereső függvényből')
		except Exception as e:
			Domoticz.Error(f"'find_warmest_hours_today_hc' failed '{e.__class__.__name__}':'{e}' | A mai legmelegebb fűtés-hűtési órák keresése sikertelen: '{e.__class__.__name__}':'{e}'")

		return self.warmest_hours_hc

	def find_coldest_hours_today_hc(self):
		try:
			Domoticz.Debug('Entering find_coldest_hours_today_hc | Belépés a fűtés–hűtés mai leghidegebb óráit kereső függvénybe')

			def to_timestamp(date_string):
				date_format = "%Y-%m-%d %H:%M:%S"
				try:
					return time.mktime(time.strptime(date_string, date_format))
				except ValueError as e:
					Domoticz.Error(f"Invalid date format: {date_string}, error: {e} | Érvénytelen dátumformátum: {date_string}, hiba: {e}")
					return None

			# Today as a timestamp | Mai nap időbélyegként
			today_start = time.mktime(time.strptime(time.strftime('%Y-%m-%d 00:00:00'), "%Y-%m-%d %H:%M:%S"))
			today_end = time.mktime(time.strptime(time.strftime('%Y-%m-%d 23:59:59'), "%Y-%m-%d %H:%M:%S"))

			# Check that met_data_string exists and is not empty | Ellenőrizd, hogy a met_data_string létezik és nem üres
			if not self.met_data_string:
				Domoticz.Error('met_data_string is empty or not initialized. | A met_data_string üres vagy nincs inicializálva.')
				self.coldest_hours_hc = []
				return self.coldest_hours_hc

			# Filter values for today | Szűrés a mai dátumhoz tartozó értékekre
			today_data = []
			for entry in self.met_data_string:
				try:
					# Check that entry contains the required keys | Ellenőrizd, hogy az entry tartalmazza a szükséges kulcsokat
					if 'time' not in entry or 'temp' not in entry:
						Domoticz.Error(f"Missing keys in entry: {entry} | Hiányzó kulcsok a bejegyzésben: {entry}")
						continue

					# Convert to timestamp | Átalakítás időbélyeggé
					entry_timestamp = to_timestamp(entry['time'])
					if entry_timestamp is None:
						continue

					# Data belonging only to today | Csak a mai naphoz tartozó adatok
					if today_start <= entry_timestamp <= today_end:
						today_data.append((float(entry['temp']), entry['time']))
				except (ValueError, KeyError) as e:
					Domoticz.Error(f"Error parsing entry: {entry}, error: {e} | Hiba a bejegyzés feldolgozásakor: {entry}, hiba: {e}")

			# Continue if data is available | Ha van adat, folytatjuk
			if today_data:
				if self.hc_external_time_H_limit > 0:
					coldest_hours_full = heapq.nsmallest(self.hc_external_time_H_limit, today_data)
					self.coldest_hours_hc = [time.localtime(to_timestamp(hour[1])).tm_hour for hour in coldest_hours_full]
				else:
					Domoticz.Error(f"Invalid cooling external time limit: {self.hc_external_time_H_limit} | Érvénytelen hűtési külső időkorlát: {self.hc_external_time_H_limit}")
					self.coldest_hours_hc = []
			else:
				Domoticz.Debug('No data available for today. | Nem áll rendelkezésre adat a mai napra.')
				self.coldest_hours_hc = []

			Domoticz.Debug('Coldest hours for heating/cooling: {0} | A fűtés/hűtés leghidegebb órái: {0}'.format(self.coldest_hours_hc))
			Domoticz.Debug('Exiting find_coldest_hours_today_hc | Kilépés a fűtés–hűtés mai leghidegebb óráit kereső függvényből')
		except Exception as e:
			Domoticz.Error(f"'find_coldest_hours_today_hc' failed '{e.__class__.__name__}':'{e}' | A mai leghidegebb fűtés-hűtési órák keresése sikertelen: '{e.__class__.__name__}':'{e}'")

		return self.coldest_hours_hc


	def get_device_data_by_idx(self, idx):
		url = f"type=devices&rid={idx}"
		result = DomoticzAPI(url)
		if result and "result" in result:
			try:
				dev = result["result"][0]
				value = float(dev["SetPoint"]) if "SetPoint" in dev else float(dev["Data"])
				last_update = dev["LastUpdate"]
				return (value, last_update)
			except Exception as e:
				Domoticz.Error(f"Failed to process idx {idx}: {e} | Nem sikerült feldolgozni az idx {idx} adatokat: {e}")
		return (None, None)


	def sync_zone_console_and_setpoints(self):

		if Devices[217].sValue != "0" :
		
			id_names = ['normal_futes', 'takarekos_futes', 'normal_hutes', 'takarekos_hutes', 'kulsohomersekletfuggo_futes', 'kulsohomersekletfuggo_hutes', 'energieatermelesfuggo_futes', 'energieatermelesfuggo_hutes']
			console_data = {}
			setpoint_data = {}

			Domoticz.Debug('Starting synchronization of zones between console and setpoint | A zónák összehangolásának kezdete a konzol és az alapjel között')

			# 1. Console averages by idx | 1. Konzolátlagok idx szerint
			for i in range(1, 13):
				zone_key = f"ZoneConsole_{i}"
				consoles = getattr(self, zone_key, [])
				Domoticz.Debug(f"{zone_key} contents: {consoles} | {zone_key} tartalma: {consoles}")

				if not consoles:
					Domoticz.Debug(f"Zone {i}: no console assigned | Zóna {i}: nincs hozzárendelt konzol")
					console_data[i] = (None, None)
					continue

				total = 0
				count = 0
				latest_update = None

				for idx in consoles:
					val, last = self.get_device_data_by_idx(idx)
					if val is not None:
						total += val
						count += 1
						if not latest_update or last > latest_update:
							latest_update = last
						Domoticz.Debug(f"Zone {i}: console idx {idx}, value={val}, updated={last} | Zóna {i}: konzol idx {idx}, érték={val}, frissítés={last}")
					else:
						Domoticz.Debug(f"Zone {i}: console idx {idx} cannot be read | Zóna {i}: konzol idx {idx} nem olvasható")

				avg = round(total / count, 2) if count > 0 else None
				console_data[i] = (avg, latest_update)
				Domoticz.Debug(f"Zone {i}: console average={avg}, latest update={latest_update} | Zóna {i}: konzolátlag={avg}, utolsó frissítés={latest_update}")

			# 2. Setpoints (still based on Devices and unit IDs) | 2. Célhőmérsékletek (továbbra is Devices szerint, egységalapon)
			for zone in range(1, 13):
				id_tuple = self.base_ids[zone]
				target_setpoint_type = None

				if Devices[217].sValue == "10" :

					if Devices[58].sValue == "10":  # Heating | Fűtés
						
						target_setpoint_type = "normal_futes"
						
					else:  # Cooling | Hűtés

						target_setpoint_type = "normal_hutes"

				elif Devices[217].sValue == "20" :
					
					if Devices[58].sValue == "10":  # Heating | Fűtés
						if Devices[124].sValue != "0":
							target_setpoint_type = "kulsohomersekletfuggo_futes"
						elif Devices[130].sValue != "0":
							target_setpoint_type = "kulsohomersekletfuggo_hutes"
						elif Devices[125].sValue != "0":
							target_setpoint_type = "energieatermelesfuggo_futes"
						elif Devices[2].sValue == "10":
							target_setpoint_type = "normal_futes"
						else:
							target_setpoint_type = "takarekos_futes"
					else:  # Cooling | Hűtés
						if Devices[2].sValue == "10":
							target_setpoint_type = "normal_hutes"
						else:
							target_setpoint_type = "takarekos_hutes"


				Domoticz.Debug(f"Zone {zone}: selected setpoint type = {target_setpoint_type} | Zóna {zone}: választott célhőmérséklet-típus = {target_setpoint_type}")

				if target_setpoint_type not in id_names:
					Domoticz.Error(f"Zone {zone}: invalid setpoint type: {target_setpoint_type} | Zóna {zone}: érvénytelen célhőmérséklet-típus: {target_setpoint_type}")
					setpoint_data[zone] = (None, None)
					continue

				index = id_names.index(target_setpoint_type)
				device_id = id_tuple[index]

				if device_id in Devices:
					try:
						value = float(Devices[device_id].sValue)
					except ValueError:
						value = None
					last_update = Devices[device_id].LastUpdate
					Domoticz.Debug(f"Zone {zone}: setpoint {device_id}, value={value}, updated={last_update} | Zóna {zone}: célhőmérséklet {device_id}, érték={value}, frissítés={last_update}")
				else:
					value = None
					last_update = None
					Domoticz.Debug(f"Zone {zone}: missing setpoint device ({device_id}) | Zóna {zone}: hiányzó célhőmérséklet-eszköz ({device_id})")

				setpoint_data[zone] = (value, last_update)

			# 3. Comparison | 3. Összehasonlítás
			id_names = ['normal_futes', 'takarekos_futes', 'normal_hutes', 'takarekos_hutes', 'kulsohomersekletfuggo_futes', 'kulsohomersekletfuggo_hutes', 'energieatermelesfuggo_futes', 'energieatermelesfuggo_hutes']

			for zone in range(1, 13):
				cons_val, _ = console_data.get(zone, (None, None))

				if cons_val is None:
					Domoticz.Debug(f"Zone {zone}: no console, setpoint is not updated | Zóna {zone}: nincs konzol, a célhőmérséklet nem frissül")
					continue

				id_tuple = self.base_ids[zone]

				if target_setpoint_type not in id_names:
					Domoticz.Error(f"Zone {zone}: invalid setpoint type: {target_setpoint_type} | Zóna {zone}: érvénytelen célhőmérséklet-típus: {target_setpoint_type}")
					continue

				index = id_names.index(target_setpoint_type)
				device_id = id_tuple[index]

				if device_id in Devices:
					Domoticz.Log(f"Zone {zone}: setpoint ({device_id}) updated with console average: {cons_val} | Zóna {zone}: célhőmérséklet ({device_id}) frissítve a konzolok átlagával: {cons_val}")
					Devices[device_id].Update(nValue=0, sValue=str(round(cons_val, 1)))
				else:
					Domoticz.Error(f"Zone {zone}: missing setpoint device ({device_id}) | Zóna {zone}: hiányzó célhőmérséklet-eszköz ({device_id})")


	def met_date_load(self) :

		Domoticz.Debug('Starting met_date_load | A met_date_load elindul')
		Domoticz.Debug("Meteorological data string = {0} | Meteorológiai adatsor (self.met_data_string) = {0}".format(self.met_data_string))

		if not self.met_data_string :
			Domoticz.Error('self.met_data_string was unavailable | Nem volt self.met_data_string')

			self.met_data_string = self.WeatherForecastAPI()

			if self.met_data_string is None:
				Domoticz.Error('Unable to retrieve data using WeatherForecastAPI. | Nem sikerült adatot lekérni a WeatherForecastAPI segítségével.')
			else:
				Domoticz.Debug("Data retrieved successfully: {0} | Sikeres adatlekérés: {0}".format(self.met_data_string))

			Devices[3].Update(nValue=0, sValue=str(Devices[3].sValue))
			Devices[4].Update(nValue=0, sValue=str(Devices[4].sValue))
			Devices[5].Update(nValue=0, sValue=str(Devices[5].sValue))
			Devices[7].Update(nValue=0, sValue=str(Devices[7].sValue))
			Devices[8].Update(nValue=0, sValue=str(Devices[8].sValue))
			Devices[9].Update(nValue=0, sValue=str(Devices[9].sValue))
			Devices[14].Update(nValue=0, sValue=str(Devices[14].sValue))
			Devices[16].Update(nValue=0, sValue=str(Devices[16].sValue))
			Devices[17].Update(nValue=0, sValue=str(Devices[17].sValue))
			Devices[18].Update(nValue=0, sValue=str(Devices[18].sValue))
			Devices[30].Update(nValue=0, sValue=str(Devices[30].sValue))
			Devices[31].Update(nValue=0, sValue=str(Devices[31].sValue))
			Devices[35].Update(nValue=0, sValue=str(Devices[35].sValue))
			Devices[36].Update(nValue=0, sValue=str(Devices[36].sValue))
			Devices[37].Update(nValue=0, sValue=str(Devices[37].sValue))
			Devices[38].Update(nValue=0, sValue=str(Devices[38].sValue))
			Devices[39].Update(nValue=0, sValue=str(Devices[39].sValue))
			Devices[40].Update(nValue=0, sValue=str(Devices[40].sValue))
			Devices[41].Update(nValue=0, sValue=str(Devices[41].sValue))
			Devices[42].Update(nValue=0, sValue=str(Devices[42].sValue))
			Devices[43].Update(nValue=0, sValue=str(Devices[43].sValue))
			Devices[44].Update(nValue=0, sValue=str(Devices[44].sValue))
			Devices[45].Update(nValue=0, sValue=str(Devices[45].sValue))
			Devices[46].Update(nValue=0, sValue=str(Devices[46].sValue))
			Devices[47].Update(nValue=0, sValue=str(Devices[47].sValue))
			Devices[48].Update(nValue=0, sValue=str(Devices[48].sValue))
			Devices[49].Update(nValue=0, sValue=str(Devices[49].sValue))
			Devices[50].Update(nValue=0, sValue=str(Devices[50].sValue))
			Devices[51].Update(nValue=0, sValue=str(Devices[51].sValue))
			Devices[52].Update(nValue=0, sValue=str(Devices[52].sValue))
			Devices[53].Update(nValue=0, sValue=str(Devices[53].sValue))
			Devices[54].Update(nValue=0, sValue=str(Devices[54].sValue))
			Devices[55].Update(nValue=0, sValue=str(Devices[55].sValue))
			Devices[56].Update(nValue=0, sValue=str(Devices[56].sValue))
			Devices[57].Update(nValue=0, sValue=str(Devices[57].sValue))
			Devices[59].Update(nValue=0, sValue=str(Devices[59].sValue))
			Devices[60].Update(nValue=0, sValue=str(Devices[60].sValue))
			Devices[61].Update(nValue=0, sValue=str(Devices[61].sValue))
			Devices[62].Update(nValue=0, sValue=str(Devices[62].sValue))
			Devices[63].Update(nValue=0, sValue=str(Devices[63].sValue))
			Devices[64].Update(nValue=0, sValue=str(Devices[64].sValue))
			Devices[67].Update(nValue=0, sValue=str(Devices[67].sValue))
			Devices[70].Update(nValue=0, sValue=str(Devices[70].sValue))
			Devices[71].Update(nValue=0, sValue=str(Devices[71].sValue))
			Devices[75].Update(nValue=0, sValue=str(Devices[75].sValue))
			Devices[76].Update(nValue=0, sValue=str(Devices[76].sValue))
			Devices[77].Update(nValue=0, sValue=str(Devices[77].sValue))
			Devices[79].Update(nValue=0, sValue=str(Devices[79].sValue))
			Devices[80].Update(nValue=0, sValue=str(Devices[80].sValue))
			Devices[81].Update(nValue=0, sValue=str(Devices[81].sValue))
			Devices[82].Update(nValue=0, sValue=str(Devices[82].sValue))
			Devices[90].Update(nValue=0, sValue=str(Devices[90].sValue))
			Devices[91].Update(nValue=0, sValue=str(Devices[91].sValue))
			Devices[92].Update(nValue=0, sValue=str(Devices[92].sValue))
			Devices[93].Update(nValue=0, sValue=str(Devices[93].sValue))
			Devices[94].Update(nValue=0, sValue=str(Devices[94].sValue))
			Devices[95].Update(nValue=0, sValue=str(Devices[95].sValue))
			Devices[96].Update(nValue=0, sValue=str(Devices[96].sValue))
			Devices[108].Update(nValue=0, sValue=str(Devices[108].sValue))
			Devices[109].Update(nValue=0, sValue=str(Devices[109].sValue))
			Devices[110].Update(nValue=0, sValue=str(Devices[110].sValue))
			Devices[111].Update(nValue=0, sValue=str(Devices[111].sValue))
			Devices[115].Update(nValue=0, sValue=str(Devices[115].sValue))
			Devices[116].Update(nValue=0, sValue=str(Devices[116].sValue))
			Devices[117].Update(nValue=0, sValue=str(Devices[117].sValue))
			Devices[118].Update(nValue=0, sValue=str(Devices[118].sValue))
			Devices[119].Update(nValue=0, sValue=str(Devices[119].sValue))
			Devices[120].Update(nValue=0, sValue=str(Devices[120].sValue))
			Devices[121].Update(nValue=0, sValue=str(Devices[121].sValue))
			Devices[122].Update(nValue=0, sValue=str(Devices[122].sValue))
			Devices[123].Update(nValue=0, sValue=str(Devices[123].sValue))
			Devices[126].Update(nValue=0, sValue=str(Devices[126].sValue))
			Devices[127].Update(nValue=0, sValue=str(Devices[127].sValue))
			Devices[128].Update(nValue=0, sValue=str(Devices[128].sValue))
			Devices[129].Update(nValue=0, sValue=str(Devices[129].sValue))
			Devices[132].Update(nValue=0, sValue=str(Devices[132].sValue))
			Devices[133].Update(nValue=0, sValue=str(Devices[133].sValue))
			Devices[134].Update(nValue=0, sValue=str(Devices[134].sValue))
			Devices[135].Update(nValue=0, sValue=str(Devices[135].sValue))
			Devices[136].Update(nValue=0, sValue=str(Devices[136].sValue))
			Devices[137].Update(nValue=0, sValue=str(Devices[137].sValue))
			Devices[138].Update(nValue=0, sValue=str(Devices[138].sValue))
			Devices[139].Update(nValue=0, sValue=str(Devices[139].sValue))
			Devices[140].Update(nValue=0, sValue=str(Devices[140].sValue))
			Devices[141].Update(nValue=0, sValue=str(Devices[141].sValue))
			Devices[142].Update(nValue=0, sValue=str(Devices[142].sValue))
			Devices[143].Update(nValue=0, sValue=str(Devices[143].sValue))
			Devices[144].Update(nValue=0, sValue=str(Devices[144].sValue))
			Devices[145].Update(nValue=0, sValue=str(Devices[145].sValue))
			Devices[146].Update(nValue=0, sValue=str(Devices[146].sValue))
			Devices[147].Update(nValue=0, sValue=str(Devices[147].sValue))
			Devices[148].Update(nValue=0, sValue=str(Devices[148].sValue))
			Devices[149].Update(nValue=0, sValue=str(Devices[149].sValue))
			Devices[150].Update(nValue=0, sValue=str(Devices[150].sValue))
			Devices[151].Update(nValue=0, sValue=str(Devices[151].sValue))
			Devices[216].Update(nValue=0, sValue=str(Devices[216].sValue))
			Devices[252].Update(nValue=0, sValue=str(Devices[252].sValue))
			for device_id in range(162, 210):  # 210 because the upper bound of range is excluded | 210, mert a range felső határa nem része a tartománynak
				Devices[device_id].Update(nValue=0, sValue=str(Devices[device_id].sValue))


		if self.met_data_string :
			Domoticz.Debug("Weather data string available = {0} | A self.met_data_string rendelkezésre áll = {0}".format(self.met_data_string))
			
			max_date = max(time.mktime(time.strptime(entry['time'], '%Y-%m-%d %H:%M:%S')) for entry in self.met_data_string)
			Domoticz.Debug('Latest date | Legkésőbbi dátum: '+format(max_date))

			today_23_hour = time.mktime(time.strptime(time.strftime('%Y-%m-%d 23:00:00', time.localtime()), '%Y-%m-%d %H:%M:%S'))
			Domoticz.Debug('Today at 23:00 | Mai nap 23:00: '+format(today_23_hour))

			if self.ido :
				current_timenergieatermelesfuggo_futes_ido = time.time() + self.ido * 3600
				Domoticz.Debug('Current time for energy-dependent heating | Energiatermelés-függő fűtés aktuális ideje: '+format(current_timenergieatermelesfuggo_futes_ido))

				if max_date < current_timenergieatermelesfuggo_futes_ido :
					self.met_data_string = []
					self.met_data_string = self.WeatherForecastAPI()
					Domoticz.Debug("Weather data in scheduled-time branch: {0} | Meteorológiai adatok az időzített ágban: {0}".format(self.met_data_string))
					Devices[3].Update(nValue=0, sValue=str(Devices[3].sValue))
					Devices[4].Update(nValue=0, sValue=str(Devices[4].sValue))
					Devices[5].Update(nValue=0, sValue=str(Devices[5].sValue))
					Devices[6].Update(nValue=0, sValue=str(Devices[6].sValue))
					Devices[8].Update(nValue=0, sValue=str(Devices[8].sValue))

			
			if max_date > today_23_hour :
				Domoticz.Debug('No update needed: maximum date is later than today at 23:00 | Nem szükséges frissítés: a legkésőbbi dátum a mai 23:00 után van')
			else:
				Domoticz.Debug('Update required: time data is outdated | Frissíteni kell: az időadat elavult')
				self.met_data_string = []
				self.met_data_string = self.WeatherForecastAPI()
				Domoticz.Debug('Weather data string in latest-date branch | Legkésőbbi dátum ág meteorológiai adatsora: '+format(self.met_data_string))

			if self.dhw_external_time_limit and self.met_data_string :
				self.find_warmest_hours_today_dhw()
				Domoticz.Debug("Find today’s warmest hours for DHW | Mai legmelegebb órák keresése HMV-hez")
			
			if self.buffer_external_time_F_limit and self.met_data_string :
				self.find_warmest_hours_today_buffer()
				Domoticz.Debug("Find today’s warmest hours for buffer | Mai legmelegebb órák keresése a pufferhez")
			
			if self.buffer_external_time_H_limit and self.met_data_string :
				self.find_coldest_hours_today_buffer()
				Domoticz.Debug("Find today’s coldest hours for buffer | Mai leghidegebb órák keresése a pufferhez")

			if self.hc_external_time_F_limit and self.met_data_string :
				self.find_warmest_hours_today_hc()
				Domoticz.Debug("Find today’s warmest hours for heating/cooling | Mai legmelegebb órák keresése fűtéshez/hűtéshez")
			
			if self.hc_external_time_H_limit and self.met_data_string :
				self.find_coldest_hours_today_hc()
				Domoticz.Debug("Find today’s coldest hours for heating/cooling | Mai leghidegebb órák keresése fűtéshez/hűtéshez")
		
		Domoticz.Debug('met_date_load finished | A met_date_load befejeződött')


	def AutoCallib(self):
		
		Domoticz.Debug('AutoCallib calculation started | Az AutoCallib számítása elindult')

		if self.nextcalc <= datetime.now():
			
			Domoticz.Debug('AutoCallib calculation is running because it is due | Az AutoCallib számítása fut, mert elérkezett az ideje')

			getPowerVar(self)

			self.LastInT = self.AutoPower['LastInT']
			self.LastOutT = self.AutoPower['LastOutT']
			self.LastPwr = self.AutoPower['LastPwr']
			LastFutureTemps = self.AutoPower['LastFutureTemps']
			
			now = datetime.now()

			# Assign weights (most recent value receives greatest weight) | Súlyok meghatározása (a legutóbbi érték kapja a legnagyobb súlyt)
			weights = [4, 3, 2, 1]
			total_weight = sum(weights)

			# Calculate weighted average of LastFutureTemps | A LastFutureTemps értékeinek súlyozott átlagolása
			weighted_average = sum(LastFutureTemps[i] * weights[i] for i in range(4)) / total_weight

			Domoticz.Debug(f"Weighted average forecast temperature: {weighted_average} | Súlyozott átlagos előrejelzett hőmérséklet: {weighted_average}")

			if Devices[58].sValue == "10":  # Heating logic | Fűtési logika

				# Starting value | Kiindulási érték
				self.power = 0  # Base value | Alapérték

				# Calculate weighted average temperature change | Súlyozott átlagos hőmérséklet-változás kiszámítása
				future_change = weighted_average - self.outtemp

				# Adjust proportionally to weighted change | Módosítás a súlyozott változás arányában
				if future_change > 0:
					# Reduce power when temperatures rise | Melegedés esetén csökkentjük a teljesítményt
					self.power += max(-future_change, -10)
				elif future_change < 0:
					# Increase power when temperatures fall | Hűlés esetén növeljük a teljesítményt
					self.power += min(-future_change, 10)

				# Clamp `power` to the allowed range | A `power` érték megengedett tartományra korlátozása
				self.power = max(-10, min(10, self.power))

				Domoticz.Debug(f"Final weighted power: {self.power} | Végleges súlyozott teljesítmény: {self.power}")


			else:  # Cooling logic | Hűtési logika

				# Starting value | Kiindulási érték
				self.power = 0  # Base value | Alapérték

				# Calculate weighted average temperature change | Súlyozott átlagos hőmérséklet-változás kiszámítása
				future_change = weighted_average - self.outtemp

				# Adjust proportionally to weighted change | Módosítás a súlyozott változás arányában
				if future_change > 0:
					# Increase cooling power when temperatures rise | Melegedés esetén növeljük a hűtési teljesítményt
					self.power += min(future_change, 10)
				elif future_change < 0:
					# Reduce cooling power when temperatures fall | Hűlés esetén csökkentjük a hűtési teljesítményt
					self.power += max(future_change, -10)

				# Clamp `power` to the allowed range | A `power` érték megengedett tartományra korlátozása
				self.power = max(-10, min(10, self.power))

				# Debug information in Hungarian | Hibakeresési információ magyarul
				Domoticz.Debug(f"Future change: {future_change} | Jövőbeli változás: {future_change}")
				Domoticz.Debug(f"Final cooling power: {self.power} | Végleges hűtési teljesítmény (power): {self.power}")

			
			Domoticz.Debug(f"Power: {self.power} | Teljesítmény: {self.power}")
			Devices[11].Update(nValue=0, sValue=str(self.power), TimedOut=False)

			# Debug messages on temperature changes | Hibakeresési üzenetek a hőmérséklet változásairól
			Domoticz.Debug(f"Current temperature: {self.outtemp} | Aktuális hőmérséklet: {self.outtemp}")
			Domoticz.Debug(f"Previous temperature: {self.LastOutT} | Előző hőmérséklet: {self.LastOutT}")
			Domoticz.Debug(f"Forecast temperature: {self.FutureTemp} | Előrejelzett hőmérséklet: {self.FutureTemp}")
			Domoticz.Debug(f"Last forecast temperatures: {LastFutureTemps} | Legutóbbi előrejelzett hőmérsékletek: {LastFutureTemps}")

			# Rotation: add new futuretemp and discard oldest | Rotáció: új futuretemp hozzáadása és a legrégebbi eltávolítása
			LastFutureTemps = [self.FutureTemp] + LastFutureTemps[:3]

			self.AutoPower['LastPwr'] = self.power
			self.AutoPower['LastFutureTemps'] = LastFutureTemps
			self.AutoPower['LastInT'] = self.intemp
			self.AutoPower['LastOutT'] = self.outtemp

			savePowerVar(self)
			
			self.lastcalc = datetime.now()
			self.nextcalc = datetime.now() + timedelta(minutes=self.calculate_period)

		else:
			Domoticz.Debug(f"AutoCallib not due yet; next scheduled time: {self.nextcalc} | Az AutoCallib még nem esedékes; következő időpont: {self.nextcalc}")

	def switchJelenlet(self):

		self.jelenletInfo = JelenletAPI(self.jelenlet)

		if Devices[12].sValue == "20":
			if self.jelenlet :
				Domoticz.Debug("Heating presence is configured = {0} | Fűtés jelenlet van beallitva = {0}".format(self.jelenlet))
				Domoticz.Debug('Device 2 selector value | 2-es eszköz választóértéke: '+format(Devices[2].sValue))
				Domoticz.Debug('Presence information | Jelenléti információ: '+format(self.jelenletInfo))
				
				if self.jelenletInfo :
					if Devices[2].sValue != "10":
						Devices[2].Update(nValue=1, sValue="10")
						self.parameter_change()
				else :
					if Devices[2].sValue != "20":
						self.Internals['fjelenstatus'] = 1
						saveUserVar(self)
						Devices[2].Update(nValue=1, sValue="20")
						self.parameter_change()

		elif Devices[12].sValue == "10" and self.Internals['fjelenstatus']== 1 :
			self.Internals['fjelenstatus'] = 0
			saveUserVar(self)
			if Devices[2].sValue != "10":
				Domoticz.Debug("Update to 10 required | Frissiteni kell 10-re")
				Devices[2].Update(nValue=1, sValue="10")
				self.parameter_change()

		elif Devices[12].sValue == "10":
			Domoticz.Debug("Heating presence is not configured = {0} | Nincs fűtés jelenlet beallitva = {0}".format(self.jelenlet))

		# Update heating/cooling presence status from different messages | A fűtés–hűtés jelenlétérzékelési állapotának frissítése különböző üzenetek alapján
		if Devices[12].sValue == "10":
			presence_msg = tl.t("Not active")
		elif Devices[12].sValue == "20" and self.jelenletInfo :
			presence_msg = tl.t("Presence detected")
		elif Devices[12].sValue == "20" :
			presence_msg = tl.t("Monitoring active, no presence")
		else:
			presence_msg = tl.t("Unknown status")

		# Set nValue based on presence_msg | nValue beállítása a presence_msg alapján
		if presence_msg.strip() == tl.t("Not active").strip():
			presence_nvalue = 0
		elif presence_msg.strip() == tl.t("Monitoring active, no presence").strip():
			presence_nvalue = 2
		elif presence_msg.strip() == tl.t("Presence detected").strip():
			presence_nvalue = 1
		else:
			presence_nvalue = 0  # Default | alapértelmezett

		# Update only when a change has occurred | Csak változás esetén frissít
		if Devices[238].sValue.strip() != presence_msg.strip() or Devices[238].nValue != presence_nvalue:
			Domoticz.Debug(f"Update: heating/cooling presence state changed -> nValue={presence_nvalue}, sValue='{presence_msg}' | Frissítés: fűtés–hűtés jelenlétérzékelés változott -> nValue={presence_nvalue}, sValue='{presence_msg}'")
			Devices[238].Update(nValue=presence_nvalue, sValue=presence_msg)
		else:
			Domoticz.Debug('Heating/cooling presence detection unchanged; no update | A fűtés–hűtés jelenlétérzékelése nem változott, nem frissítünk')

		if Devices[29].sValue == "20":
			if self.jelenlet != None :
				Domoticz.Debug("DHW presence is configured = {0} | HMV jelenlet van beallitva = {0}".format(self.jelenlet))
				Domoticz.Debug('Device 32 selector value | 32-es eszköz választóértéke: '+format(Devices[32].sValue))
				Domoticz.Debug("Presence information: {0} | Jelenléti információ: {0}".format(self.jelenletInfo))
				if self.jelenletInfo :
					if Devices[32].sValue != "10":
						Domoticz.Debug("Update to 10 required | Frissiteni kell 10-re")
						Devices[32].Update(nValue=1, sValue="10")
				else :
					if Devices[32].sValue != "20":
						self.Internals['dhwjelenstatus'] = 1
						saveUserVar(self)
						Domoticz.Debug("Update to 20 required | Frissiteni kell 20-ra")
						Devices[32].Update(nValue=1, sValue="20")
		elif Devices[29].sValue == "10" and self.Internals['dhwjelenstatus']== 1 :
			self.Internals['dhwjelenstatus'] = 0
			saveUserVar(self)
			if Devices[32].sValue != "10":
				Domoticz.Debug("Update to 10 required | Frissiteni kell 10-re")
				Devices[32].Update(nValue=1, sValue="10")

		# Update DHW presence status from different messages | A HMV jelenlétérzékelési állapotának frissítése különböző üzenetek alapján
		if Devices[29].sValue == "10":
			presence_msg = tl.t("Not active")
		elif Devices[29].sValue == "20" and self.jelenletInfo :
			presence_msg = tl.t("Presence detected")
		elif Devices[29].sValue == "20" :
			presence_msg = tl.t("Monitoring active, no presence")
		else:
			presence_msg = tl.t("Unknown status")

		# Set nValue based on presence_msg | nValue beállítása a presence_msg alapján
		if presence_msg.strip() == tl.t("Not active").strip():
			presence_nvalue = 0
		elif presence_msg.strip() == tl.t("Monitoring active, no presence").strip():
			presence_nvalue = 2
		elif presence_msg.strip() == tl.t("Presence detected").strip():
			presence_nvalue = 1
		else:
			presence_nvalue = 0  # Default | alapértelmezett

		# Update only when a change has occurred | Csak változás esetén frissít
		if Devices[239].sValue.strip() != presence_msg.strip() or Devices[239].nValue != presence_nvalue:
			Domoticz.Debug(f"Update: DHW presence state changed -> nValue={presence_nvalue}, sValue='{presence_msg}' | Frissítés: HMV jelenlétérzékelés változott -> nValue={presence_nvalue}, sValue='{presence_msg}'")
			Devices[239].Update(nValue=presence_nvalue, sValue=presence_msg)
		else:
			Domoticz.Debug('DHW presence detection unchanged; no update | A HMV jelenlétérzékelése nem változott, nem frissítünk')


	def HeatMode(self):

		Domoticz.Debug('Heating mode | Fűtési mód')

		cal_hiszterezis = 0

		target_temp_felso = []

		target_temp_also = []

		if Devices[74].sValue != "0":
			cal_hiszterezis = round(self.automatic_range * self.power / 10 + self.F_hiszterezis, 1)
		else :
			cal_hiszterezis = self.F_hiszterezis

		for i in range(1, 13): 
			if getattr(self, f'Zone_TempSensors_{i}') and getattr(self, f'zone_{i}_window_closed'):
				ftargettemp_felso = getattr(self, f'ftargettemp_{i}') + cal_hiszterezis
				target_temp_felso.append(ftargettemp_felso)
				setattr(self, f'ftargettemp_{i}_felso', ftargettemp_felso)
				Domoticz.Debug("Zone {0}: upper heating target (ftargettemp_felso) = {1} | {0}. zóna: felső fűtési célhőmérséklet (ftargettemp_felso) = {1}".format(i, getattr(self, f'ftargettemp_{i}')))

		self.felsohatar = round(max(target_temp_felso), 1)

		for i in range(1, 13):
			if getattr(self, f'Zone_TempSensors_{i}') and getattr(self, f'zone_{i}_window_closed'):
				ftargettemp_also = getattr(self, f'ftargettemp_{i}_felso') - 2 * self.F_hiszterezis
				target_temp_also.append(ftargettemp_also)
				setattr(self, f'ftargettemp_{i}_also', ftargettemp_also)
				Domoticz.Debug("Zone {0}: lower heating target (ftargettemp_also) = {1} | {0}. zóna: alsó fűtési célhőmérséklet (ftargettemp_also) = {1}".format(i, getattr(self, f'ftargettemp_{i}_also')))

		self.alsohatar = round(max(target_temp_also), 1)

		Devices[154].Update(nValue=0, sValue=str(cal_hiszterezis), TimedOut=False)
		Devices[158].Update(nValue=0, sValue=str(self.felsohatar), TimedOut=False)
		Devices[159].Update(nValue=0, sValue=str(self.alsohatar), TimedOut=False)


		self.switchElsodleges_H(False)
		self.switchMasodlagos_H(False)
		for i in range(1, 13):
			self.switchzone_H(i, False)
			self.send_AC_command(i, "H", "Off")

		Domoticz.Debug("Minimum indoor temperature = {0} | Minimális belső hőmérséklet (self.minintemp) = {0}".format(self.minintemp))
		Domoticz.Debug("Maximum indoor temperature = {0} | Maximális belső hőmérséklet (self.maxintemp) = {0}".format(self.maxintemp))
		Domoticz.Debug("Heating active = {0} | Fűtés aktív = {0}".format(self.heating_active))

		if self.heating_active:
			Domoticz.Debug('Heating is active | A fűtés aktív')
			if self.minintemp >= self.felsohatar:
				Domoticz.Debug('Upper limit reached; switching heating off | Elérte a felső határt, a fűtést kikapcsoljuk')
				self.heating_active = False
				self.switchElsodleges_F(False)
				self.switchMasodlagos_F(False)
				for i in range(1, 13): 
					ac_data = self.get_AC_zone_var(i, "F")
					self.switchzone_F(i, False)
					# If OFF is disabled in the AC user variable, send the ON command | Ha a klíma uservariable-ben tiltva van az OFF → akkor ON parancs küldése
					if ac_data.get("target_off", True):
						self.send_AC_command(i, "F", "Off")
					else:
						self.send_AC_command(i, "F", "On")
					self.update_setpoint_minusz(i)
			else:
				Domoticz.Debug('Within the permitted range; heating continues | Határértéken belül, a fűtés működik')
				self.heating_active = True
		else:
			Domoticz.Debug('Heating is inactive | A fűtés inaktív')
			self.switchElsodleges_F(False)
			self.switchMasodlagos_F(False)
			for i in range(1, 13): 
				ac_data = self.get_AC_zone_var(i, "F")
				self.switchzone_F(i, False)
				# If OFF is disabled in the AC user variable, send the ON command | Ha a klíma uservariable-ben tiltva van az OFF → akkor ON parancs küldése
				if ac_data.get("target_off", True):
					self.send_AC_command(i, "F", "Off")
				else:
					self.send_AC_command(i, "F", "On")
				self.update_setpoint_minusz(i)

			for i in range(1, 13):
				if getattr(self, f'Zone_TempSensors_{i}') and getattr(self, f'zone_{i}_window_closed'):
					aktual_temp = getattr(self, f'zone_{i}_aktual_temp')
					also = getattr(self, f'ftargettemp_{i}_also')

					Domoticz.Debug(
						f"Heating demand check: zone={i}, actual={aktual_temp}, lower={also} | Fűtési igény ellenőrzés: zone={i}, aktual={aktual_temp}, also={also}"
					)

					if aktual_temp is not None and aktual_temp <= also:
						Domoticz.Debug(
							f"Zone {i} requests heating: {aktual_temp} <= {also} | Zóna {i} fűtést kér: {aktual_temp} <= {also}"
						)
						self.heating_active = True
						break

		self.HeatDevices()


	def CoolMode(self):

		Domoticz.Debug('Cooling mode | Hűtési mód')

		target_temp_felso = []

		target_temp_also = []

		if Devices[74].sValue != "0":
			target_comp = round(self.automatic_range * self.power / 10, 1)
		else :
			target_comp = 0.0

		Domoticz.Debug(f"Target compensation = {target_comp} | Célhőmérséklet-kompenzáció = {target_comp}")

		for i in range(1, 13):
			if getattr(self, f'Zone_TempSensors_{i}') and getattr(self, f'zone_{i}_window_closed'):

				htargettemp_felso = getattr(self, f'htargettemp_{i}') + self.H_hiszterezis
				if Devices[214].sValue == "10":
					if getattr(self, f'htargettemp_{i}') < self.outtemp - abs(float(Devices[213].sValue)) :
						htargettemp_felso = (self.outtemp - abs(float(Devices[213].sValue))) + self.H_hiszterezis

				htargettemp_felso += target_comp

				target_temp_felso.append(htargettemp_felso)
				setattr(self, f'htargettemp_{i}_felso', htargettemp_felso)
				Domoticz.Debug(f"Zone {i}: upper cooling target (htargettemp_felso) = {htargettemp_felso} | {i}. zóna: felső hűtési célhőmérséklet (htargettemp_felso) = {htargettemp_felso}")

		self.felsohatar = round(max(target_temp_felso), 1)

		for i in range(1, 13):
			if getattr(self, f'Zone_TempSensors_{i}') and getattr(self, f'zone_{i}_window_closed'):
				htargettemp_also = getattr(self, f'htargettemp_{i}_felso') - 2 * self.H_hiszterezis
				target_temp_also.append(htargettemp_also)
				setattr(self, f'htargettemp_{i}_also', htargettemp_also)
				Domoticz.Debug(f"Zone {i}: lower cooling target (htargettemp_also) = {htargettemp_also} | {i}. zóna: alsó hűtési célhőmérséklet (htargettemp_also) = {htargettemp_also}")

		self.alsohatar = round(min(target_temp_also), 1)

		Devices[158].Update(nValue=0, sValue=str(self.felsohatar), TimedOut=False)
		Devices[159].Update(nValue=0, sValue=str(self.alsohatar), TimedOut=False)

		self.switchElsodleges_F(False)
		self.switchMasodlagos_F(False)
		for i in range(1, 13):
			self.switchzone_F(i, False)
			self.send_AC_command(i, "F", "Off")

		Domoticz.Debug('Is cooling required? | Szükséges a hűtés?')

		Domoticz.Debug("Minimum indoor temperature = {0} | Minimális belső hőmérséklet (self.minintemp) = {0}".format(self.minintemp))
		Domoticz.Debug("Maximum indoor temperature = {0} | Maximális belső hőmérséklet (self.maxintemp) = {0}".format(self.maxintemp))
		Domoticz.Debug("Cooling active = {0} | Hűtés aktív (self.cooling_active) = {0}".format(self.cooling_active))


		if self.cooling_active:
			if self.maxintemp <= self.alsohatar:
				Domoticz.Debug('Cooling not required: temperature is too low | Nem kell hűteni, alacsony a hőmérséklet')
				self.switchElsodleges_H(False)
				self.switchMasodlagos_H(False)
				self.cooling_active = False
				for i in range(1, 13):
					ac_data = self.get_AC_zone_var(i, "H")
					self.switchzone_H(i, False)
					# If OFF is disabled in the AC user variable, send the ON command | Ha a klíma uservariable-ben tiltva van az OFF → akkor ON parancs küldése
					if ac_data.get("target_off", True):
						self.send_AC_command(i, "H", "Off")
					else:
						self.send_AC_command(i, "H", "On")
					self.update_setpoint_minusz(i)
			else:
				Domoticz.Debug('Within target range; cooling required | Célértéken belül, hűteni kell')
				self.cooling_active = True
		else:
			Domoticz.Debug('Cooling is inactive | A hűtés inaktív')
			self.switchElsodleges_H(False)
			self.switchMasodlagos_H(False)
			for i in range(1, 13):
				ac_data = self.get_AC_zone_var(i, "H")
				self.switchzone_H(i, False)
				# If OFF is disabled in the AC user variable, send the ON command | Ha a klíma uservariable-ben tiltva van az OFF → akkor ON parancs küldése
				if ac_data.get("target_off", True):
					self.send_AC_command(i, "H", "Off")
				else:
					self.send_AC_command(i, "H", "On")
				self.update_setpoint_minusz(i)

			for i in range(1, 13):
				if getattr(self, f'Zone_TempSensors_{i}') and getattr(self, f'zone_{i}_window_closed'):
					aktual_temp = getattr(self, f'zone_{i}_aktual_temp')
					felso = getattr(self, f'htargettemp_{i}_felso')

					Domoticz.Debug(
						f"Cooling demand check: zone={i}, actual={aktual_temp}, upper={felso} | Hűtési igény ellenőrzés: zone={i}, aktual={aktual_temp}, felso={felso}"
					)

					if aktual_temp is not None and aktual_temp >= felso:
						Domoticz.Debug(
							f"Zone {i} requests cooling: {aktual_temp} >= {felso} | Zóna {i} hűtést kér: {aktual_temp} >= {felso}"
						)
						self.cooling_active = True
						break

		self.CoolDevices()


	def HeatDevices(self):

		self.operation = set()
		self.f1works = False
		self.f2works = False

		if self.heating_active:
		
			Domoticz.Debug('Zone and mixing valve control starting | A zóna- és keverőszelep-szabályozás elindul')

			for i in range(1, 13):
				if getattr(self, f'Zone_TempSensors_{i}') and (Devices[1].sValue != "0" and Devices[1].Used == 1):
					aktual_temp = getattr(self, f'zone_{i}_aktual_temp') or self.intemp
					target_also = getattr(self, f'ftargettemp_{i}_also')
					target_felso = getattr(self, f'ftargettemp_{i}_felso')
					window_closed = getattr(self, f'zone_{i}_window_closed')

					aktual_temp = round(aktual_temp, 2)
					target_felso = round(target_felso, 2)
					target_also = round(target_also, 2)

					Domoticz.Debug(
						f"Current temperature={aktual_temp}, upper target={target_felso}, lower target={target_also} | Aktuális hőmérséklet={aktual_temp}, felső célérték={target_felso}, alsó célérték={target_also}"
					)

					if window_closed:
						if aktual_temp <= target_also:
							Domoticz.Debug(f"Zone_{i} is colder than the minimum target: switch on | Zone_{i} hidegebb a minimális célnál: bekapcsolás")
							self.switchzone_F(i, True)
							if self.switchElsodleges_F and Devices[215].sValue == "10":
								self.send_AC_command(i, "F", "On")
							elif self.Masodlagos_F and Devices[215].sValue == "20":
								self.send_AC_command(i, "F", "On")
							else:
								self.send_AC_command(i, "F", "Off")

							self.update_setpoint_pluss(i)
							self.operation.add(i)
							continue
							
						elif aktual_temp >= target_felso:
							Domoticz.Debug(f"Zone_{i} is warmer than the maximum target: switch off | Zone_{i} melegebb a maximális célnál: kikapcsolás")
							self.switchzone_F(i, False)
							self.send_AC_command(i, "F", "Off")
							self.update_setpoint_minusz(i)
							continue

						else:
							# Keep previous heating state within hysteresis limits | A hiszterézishatárok között megtartjuk az előző fűtési állapotot
							zone_state = getattr(self, f'zone_{i}_heating_state', False)

							Domoticz.Debug(f"Zone_{i} within hysteresis limits, previous state: {zone_state} | Zone_{i} hiszterézishatárok között, előző állapot: {zone_state}")

							self.switchzone_F(i, zone_state)

							if zone_state:
								if self.switchElsodleges_F and Devices[215].sValue == "10":
									self.send_AC_command(i, "F", "On")
								elif self.Masodlagos_F and Devices[215].sValue == "20":
									self.send_AC_command(i, "F", "On")
								else:
									self.send_AC_command(i, "F", "Off")

								self.update_setpoint_pluss(i)
								self.operation.add(i)
							else:
								self.send_AC_command(i, "F", "Off")
								self.update_setpoint_minusz(i)

							continue
					else:
						self.switchzone_F(i, False)
						self.send_AC_command(i, "F", "Off")
						self.update_setpoint_minusz(i)

			Domoticz.Debug(f"Summary: operation = {self.operation} | Összegzés: operation = {self.operation}")

			if self.Kevero_1_TempSensor or self.Kevero_2_TempSensor :
				
				if self.kevero_max >= float(Devices[59].sValue):
					self.Kevero_1_temp_max = float(Devices[59].sValue)
				else:
					self.Kevero_1_temp_max = self.kevero_max 

				if self.Kevero_1_temp_max < float(Devices[70].sValue):
					self.Kevero_1_temp_min = self.Kevero_1_temp_max
				elif self.kevero_min > float(Devices[70].sValue):
					self.Kevero_1_temp_min = self.kevero_min
				else:
					self.Kevero_1_temp_min = float(Devices[70].sValue)

				if self.kevero_max >= float(Devices[60].sValue):
					self.Kevero_2_temp_max = float(Devices[60].sValue)
				else:
					self.Kevero_2_temp_max = self.kevero_max 

				if self.Kevero_2_temp_max < float(Devices[71].sValue):
					self.Kevero_2_temp_min = self.Kevero_2_temp_max
				elif self.kevero_min > float(Devices[71].sValue):
					self.Kevero_2_temp_min = self.kevero_min
				else:
					self.Kevero_2_temp_min = float(Devices[71].sValue)

				kulonbseg = abs(round(self.Fsetpoint - self.minintemp,1))
				
				arany = max(0, min(1, kulonbseg / (self.Kevero_1_szorzo/100)))

				self.Kevero_1_temp_target = round(self.Kevero_1_temp_min + arany * (abs(self.Kevero_1_temp_max - self.Kevero_1_temp_min)),1)
	  
				Domoticz.Debug('Mixing valve 1 target temperature | 1. keverőszelep célhőmérséklete: '+format(self.Kevero_1_temp_target))
				Devices[72].Update(nValue=0, sValue=str(self.Kevero_1_temp_target), TimedOut=False)

				Domoticz.Debug('Operation | Működési mód: '+format(self.operation))

				if self.operation :
					if self.Kevero_1_temp_aktual > self.Kevero_1_temp_target + self.Kevero_1_hiszterezis :
						Domoticz.Debug("Mixing valve 1 is warmer than the set maximum plus hysteresis: reduce supply temperature | Az 1. keverőszelep hőmérséklete a beállított maximum és hiszterézis fölött van: csökkenteni kell az előremenő hőmérsékletet")
						self.switch_kevero_1_plusz(False)
						self.switch_kevero_1_minusz(True)

					elif self.Kevero_1_temp_aktual + self.Kevero_1_hiszterezis < self.Kevero_1_temp_target :
						Domoticz.Debug("Mixing valve 1 is colder than the threshold: increase supply temperature | Az 1. keverőszelep hőmérséklete a küszöb alatt van: növelni kell az előremenő hőmérsékletet")
						self.switch_kevero_1_minusz(False)
						self.switch_kevero_1_plusz(True)
					
					else :
						Domoticz.Debug('Calculated supply temperature requires no adjustment | A számítás szerint nem kell változtatni az előremenő hőmérsékleten')
						self.switch_kevero_1_minusz(False)
						self.switch_kevero_1_plusz(False)

				arany = max(0, min(1, kulonbseg / (self.Kevero_2_szorzo/100)))
				
				self.Kevero_2_temp_target = round(self.Kevero_2_temp_min + arany * (abs(self.Kevero_2_temp_max - self.Kevero_2_temp_min)),1)

				Devices[73].Update(nValue=0, sValue=str(self.Kevero_2_temp_target), TimedOut=False)
				
				Domoticz.Debug('Operation | Működési mód: '+format(self.operation))

				if self.operation :
					
					if self.Kevero_2_temp_aktual > self.Kevero_2_temp_target + self.Kevero_2_hiszterezis :
						Domoticz.Debug("Mixing valve 2 is warmer than the set maximum plus hysteresis: reduce supply temperature | A 2. keverőszelep hőmérséklete a beállított maximum és hiszterézis fölött van: csökkenteni kell az előremenő hőmérsékletet")
						self.switch_kevero_2_plusz(False)
						self.switch_kevero_2_minusz(True)

					elif self.Kevero_2_temp_aktual + self.Kevero_2_hiszterezis < self.Kevero_2_temp_target :
						Domoticz.Debug("Mixing valve 2 is colder than the threshold: increase supply temperature | A 2. keverőszelep hőmérséklete a küszöb alatt van: növelni kell az előremenő hőmérsékletet")
						self.switch_kevero_2_minusz(False)
						self.switch_kevero_2_plusz(True)
					
					else :
						Domoticz.Debug('Calculated supply temperature requires no adjustment | A számítás szerint nem kell változtatni az előremenő hőmérsékleten')
						self.switch_kevero_2_minusz(False)
						self.switch_kevero_2_plusz(False)


		# Initially turn all virtual valves off; turn them on when needed | Minden virtuális szelep kezdetben legyen kikapcsolva; szükség esetén bekapcsoljuk
		for vlist in self.Zone_F_V:
			for idx in vlist:
				self.switchappend(idx, "Off")

		if len(self.operation) == 1:
			main_zone = next(iter(self.operation))

			virtual_list = getattr(self, f'Zone_{main_zone}_F_V', [])

			for idx in virtual_list:
				self.switchappend(idx, "On")

			Domoticz.Debug(f"Heating virtual devices ON: main_zone={main_zone}, idx={virtual_list} | Fűtési virtuális eszközök BE: fő_zóna={main_zone}, idx={virtual_list}")
		else:
			Domoticz.Debug(f"Heating virtual devices OFF | Fűtési virtuális eszközök KI")


		# Virtual hydraulic shifter status | Virtuális hidraulikus váltó állapota
		if len(self.operation) == 1:
			main_zone = next(iter(self.operation))
			virtual_list = getattr(self, f'Zone_{main_zone}_F_V', [])

			if virtual_list:
				new_msg = f"{tl.t('Active– zone')} {main_zone}"
				new_n = 1
			else:
				new_msg = tl.t("Not active")
				new_n = 0
		else:
			new_msg = tl.t("Not active")
			new_n = 0

		old_s = Devices[86].sValue or ""

		if old_s.strip() != new_msg.strip() or Devices[86].nValue != new_n:
			Devices[86].Update(
				nValue=new_n,
				sValue=new_msg,
				TimedOut=False
			)

		if Devices[1].sValue != "0":

			Domoticz.Debug('Heating mode active | Fűtési üzemmód aktív')

			mode = Devices[1].sValue
			outlimit = float(Devices[7].sValue)    # Outdoor temperature threshold | Külső hőmérsékleti határ
			outdewpointkomp = float(Devices[221].sValue)  # Outdoor dew-point compensation | Külső harmatpont-kompenzáció
			dualdiff = float(Devices[3].sValue)    # Difference value (°C) | Különbség értéke (°C)
			outhiszt = float(Devices[18].sValue)      # Outdoor hysteresis value | Külső hiszterézis értéke
			dualhiszt = float(Devices[64].sValue)      # Dual indoor hysteresis value | Dual belső hiszterézis értéke

			Domoticz.Debug('Heating parameters: | Fűtési paraméterek:')
			Domoticz.Debug(f"Mode: {mode} | Üzemmód: {mode}")
			Domoticz.Debug(f"  Outside temperature = {self.outtemp:.1f}°C | Külső hőmérséklet = {self.outtemp:.1f}°C")
			Domoticz.Debug(f"  Outside temperature limit = {outlimit:.1f}°C | Külső hőmérsékleti határ = {outlimit:.1f}°C")
			Domoticz.Debug(f"Outside dew point = {self.outdewpoint} | Külső harmatpont = {self.outdewpoint}")
			Domoticz.Debug(f"  Dew-point compensation = {outdewpointkomp:.1f}°C | Harmatpont-kompenzáció = {outdewpointkomp:.1f}°C")
			Domoticz.Debug(f"  Average indoor temperature = {self.intemp_avg:.1f} | Átlagos belső hőmérséklet = {self.intemp_avg:.1f}")
			Domoticz.Debug(f"  Dual-mode difference = {dualdiff:.1f} | Dual mód eltérése = {dualdiff:.1f}")
			Domoticz.Debug(f"  Dual heating setpoint = {self.DualFsetpoint:.1f} | Dual fűtési célhőmérséklet = {self.DualFsetpoint:.1f}")
			Domoticz.Debug(f"  Dual indoor hysteresis = {dualhiszt:.1f} | Dual belső hiszterézis = {dualhiszt:.1f}")
			Domoticz.Debug(f"  Outdoor hysteresis = {outhiszt:.1f} | Külső hiszterézis = {outhiszt:.1f}")
			Domoticz.Debug(f"Operation = {self.operation} | Működési mód = {self.operation}")

			# 10: Primary mode | 10: Elsődleges mód
			if mode == "10":
				Domoticz.Debug('Primary heating mode | Elsődleges fűtési mód')
				if self.operation:
					self.switchElsodleges_F(True)
				else:
					self.switchElsodleges_F(False)
				self.switchMasodlagos_F(False)

			# 20: Secondary mode | 20: Másodlagos mód
			elif mode == "20":
				Domoticz.Debug("Secondary heating mode! | Másodlagos fűtési mód!")
				self.switchElsodleges_F(False)
				if self.operation:
					self.switchMasodlagos_F(True)
				else:
					self.switchMasodlagos_F(False)

			# 30: Switching mode (based on indoor temperature) | 30: Váltó mód (belső hőmérséklet alapján)
			elif mode == "30":
				Domoticz.Debug("Switching mode (based on indoor temperature)! | Váltó mód (belső hőmérséklet alapján)!")

				# Switching point | Váltási pont
				switch_point = self.DualFsetpoint - dualdiff

				# Hysteresis band | Hiszterézis sáv
				upper_limit = switch_point + dualhiszt   # Switch back to 1 from here | Innen visszaváltás 1-re
				lower_limit = switch_point - dualhiszt   # Switch to 2 from here | Innen váltás 2-re

				Domoticz.Debug(
					("Switching point and hysteresis band | " + (f"Váltási pont = {switch_point:.2f}°C  "
					f"({lower_limit:.2f}–{upper_limit:.2f} hiszterézis sáv)"))
				)
				Domoticz.Debug(f"Average indoor temperature: {self.intemp_avg:.2f}°C | Átlagos belső hőmérséklet: {self.intemp_avg:.2f}°C")

				# Decision logic | Döntési logika
				if self.intemp_avg < lower_limit:
					Domoticz.Debug(
						("Average indoor temperature below lower threshold: secondary mode | " + (f"IntAvgTemp {self.intemp_avg:.2f} < alsó határ {lower_limit:.2f} → Másodlagos"))
					)
					self.F_last_mode_state = 1

				elif self.intemp_avg > upper_limit:
					Domoticz.Debug(
						("Average indoor temperature above upper threshold: primary mode | " + (f"IntAvgTemp {self.intemp_avg:.2f} > felső határ {upper_limit:.2f} → Elsődleges"))
					)
					self.F_last_mode_state = 0

				else:
					Domoticz.Debug(
						f"Average indoor temperature {self.intemp_avg:.2f} within hysteresis band ({lower_limit:.2f}–{upper_limit:.2f}): retain mode {self.F_last_mode_state} | Belső átlaghőmérséklet {self.intemp_avg:.2f} a hiszterézissávban ({lower_limit:.2f}–{upper_limit:.2f}): állapot tartása: {self.F_last_mode_state}"
					)

				# Execution | --- Végrehajtás ---
				if self.F_last_mode_state == 0:
					# Primary | Elsődleges
					if self.operation:
						self.switchElsodleges_F(True)
					else:
						self.switchElsodleges_F(False)
					self.switchMasodlagos_F(False)

				else:
					# Secondary | Másodlagos
					self.switchElsodleges_F(False)
					if self.operation:
						self.switchMasodlagos_F(True)
					else:
						self.switchMasodlagos_F(False)

			# 40: Switching mode (based on outdoor temperature, with hysteresis) | 40: Váltó mód (külső hőmérséklet alapján, hiszterézissel)
			elif mode == "40":
				Domoticz.Debug('Switching mode (based on outdoor temperature, with hysteresis) | Váltó mód (külső hőmérséklet alapján, hiszterézissel)')

				# Hysteresis thresholds | --- Hiszterézis határok ---
				upper_limit = outlimit + outhiszt     # Above: primary | Fölötte: elsődleges
				lower_limit = outlimit - outhiszt     # Below: secondary | Alatta: másodlagos

				# Determine mode (switch only outside hysteresis band) | Üzemmód meghatározása (váltás csak a külső tartományokon túl)
				if self.outtemp > upper_limit:
					Domoticz.Debug(("Outdoor temperature above upper threshold: primary mode | " + (f"Kint melegebb ({self.outtemp:.1f}°C > {upper_limit:.1f}°C) → Elsődleges")))
					self.F_last_mode_state = 0

				elif self.outtemp < lower_limit:
					Domoticz.Debug(("Outdoor temperature below lower threshold: secondary mode | " + (f"Kint hidegebb ({self.outtemp:.1f}°C < {lower_limit:.1f}°C) → Másodlagos")))
					self.F_last_mode_state = 1

				else:
					Domoticz.Debug(
						(f"Outdoor temperature {self.outtemp:.1f} within hysteresis band ({lower_limit:.1f}–{upper_limit:.1f}): retain mode {self.F_last_mode_state} | " + (f"Külső hőmérséklet hiszterézisen belül "
						f"({lower_limit:.1f}–{upper_limit:.1f}) → nincs váltás, tartjuk a(z) {self.F_last_mode_state} módot"))
					)

				# Switch according to stored mode | Kapcsolás a tárolt üzemmód szerint
				if self.F_last_mode_state == 0:
					# Primary | Elsődleges
					if self.operation:
						self.switchElsodleges_F(True)
					else:
						self.switchElsodleges_F(False)
					self.switchMasodlagos_F(False)

				else:
					# Secondary | Másodlagos
					self.switchElsodleges_F(False)
					if self.operation:
						self.switchMasodlagos_F(True)
					else:
						self.switchMasodlagos_F(False)

			# 50: Switching mode (based on outdoor dew point, with hysteresis) | 50: Váltó mód (külső harmatpont alapján, hiszterézissel)
			elif mode == "50":
				Domoticz.Debug('Switching mode (based on outdoor dew point, dew-gap and hysteresis) | Váltó mód (külső harmatpont alapján, dew-gap és hiszterézis)')

				# Calculate dew-point gap | Harmatpont-különbség kiszámítása
				dew_gap = self.outtemp - self.outdewpoint

				SAFE = outdewpointkomp		# May be negative or positive | Lehet negatív vagy pozitív
				HYST = outhiszt			# Hysteresis | Hiszterézis

				Domoticz.Debug(f"Outdoor temperature: {self.outtemp:.1f}°C | Külső hőmérséklet: {self.outtemp:.1f}°C")
				Domoticz.Debug(f"Outdoor dew point: {self.outdewpoint:.1f}°C | Külső harmatpont: {self.outdewpoint:.1f}°C")
				Domoticz.Debug(f"Dew-point gap (temperature minus dew point): {dew_gap:.1f}°C | Harmatpont-különbség (hőmérséklet mínusz harmatpont): {dew_gap:.1f}°C")
				Domoticz.Debug(f"Safety threshold (outdewpointkomp): {SAFE:.1f}°C | Biztonsági határ (outdewpointkomp): {SAFE:.1f}°C")
				Domoticz.Debug(f"Hysteresis (outhiszt): {HYST:.1f}°C | Hiszterézis (outhiszt): {HYST:.1f}°C")

				# MODE SWITCHING | ÜZEMMÓDVÁLTÁS
				# 1 = Primary (heat pump) | 1 = Elsődleges (hőszivattyú)
				# 2 = Secondary (boiler) | 2 = Másodlagos (kazán)

				# Freeze risk: dew-point gap too small, switch to secondary | Fagyveszély: túl kicsi harmatpont-különbség, váltás másodlagosra
				if dew_gap < SAFE:
					Domoticz.Debug(
						("Dew-point gap below safe threshold: secondary mode; heat pump disabled | " + (f"Dew-gap {dew_gap:.1f}°C < SAFE {SAFE:.1f}°C → Másodlagos mód (HP tilt)"))
					)
					self.F_last_mode_state = 2

				# Safe range: enable heat pump again | Biztonságos tartomány: újra engedélyezzük a hőszivattyút
				elif dew_gap > SAFE + HYST:
					Domoticz.Debug(
						("Dew-point gap above safe threshold plus hysteresis: primary mode | " + (f"Dew-gap {dew_gap:.1f}°C > SAFE+HYST {SAFE + HYST:.1f}°C → Elsődleges mód"))
					)
					self.F_last_mode_state = 1

				else:
					Domoticz.Debug(
						("Dew-point gap within hysteresis band: retain current mode | " + (f"Dew-gap {dew_gap:.1f}°C a sávban ({SAFE:.1f}–{SAFE + HYST:.1f}) → "
						f"tartjuk a(z) {self.F_last_mode_state} módot"))
					)

				# SWITCHING | KAPCSOLÁS
				if self.F_last_mode_state == 1:
					# Heat pump | Hőszivattyú
					self.switchMasodlagos_F(False)
					if self.operation:
						self.switchElsodleges_F(True)
					else:
						self.switchElsodleges_F(False)

				else:
					# Boiler | Kazán
					self.switchElsodleges_F(False)
					if self.operation:
						self.switchMasodlagos_F(True)
					else:
						self.switchMasodlagos_F(False)


			# 60: Dual mode (based on indoor temperature) | 60: Dual mód (belső hőmérséklet alapján)
			elif mode == "60":
				Domoticz.Debug('Dual mode (based on indoor temperature) | Dual mód (belső hőmérséklet alapján)')

				# Switching point | Váltási pont
				switch_point = self.DualFsetpoint - dualdiff

				# Hysteresis band | Hiszterézis sáv
				upper_limit = switch_point + dualhiszt   # Switch back to 1 from here | Innen visszaváltás 1-re
				lower_limit = switch_point - dualhiszt   # Switch to 2 from here | Innen váltás 2-re

				Domoticz.Debug(
					("Switching point and hysteresis band | " + (f"Váltási pont = {switch_point:.2f}°C  "
					f"({lower_limit:.2f}–{upper_limit:.2f} hiszterézis sáv)"))
				)
				Domoticz.Debug(f"Average indoor temperature: {self.intemp_avg:.2f}°C | Átlagos belső hőmérséklet: {self.intemp_avg:.2f}°C")

				# Decision logic | Döntési logika
				if self.intemp_avg < lower_limit:
					Domoticz.Debug(
						("Average indoor temperature below lower threshold: dual mode | " + (f"IntAvgTemp {self.intemp_avg:.2f} < alsó határ {lower_limit:.2f} → Dual"))
					)
					self.F_last_mode_state = 1

				elif self.intemp_avg > upper_limit:
					Domoticz.Debug(
						("Average indoor temperature above upper threshold: primary mode | " + (f"IntAvgTemp {self.intemp_avg:.2f} > felső határ {upper_limit:.2f} → Elsődleges"))
					)
					self.F_last_mode_state = 0

				else:
					Domoticz.Debug(
						(f"Average indoor temperature {self.intemp_avg:.2f} within hysteresis band ({lower_limit:.2f}–{upper_limit:.2f}): retain mode {self.F_last_mode_state} | " + (f"IntAvgTemp {self.intemp_avg:.2f} hiszterézis sávban "
						f"({lower_limit:.2f}–{upper_limit:.2f}) → állapot tartása: {self.F_last_mode_state}"))
					)

				# Execution | --- Végrehajtás ---
				if self.F_last_mode_state == 0:
					# Primary | Elsődleges
					if self.operation:
						self.switchElsodleges_F(True)
					else:
						self.switchElsodleges_F(False)
					self.switchMasodlagos_F(False)

				else:
					# Dual mode | Dual mód
					if self.operation:
						self.switchElsodleges_F(True)
						self.switchMasodlagos_F(True)
					else:
						self.switchElsodleges_F(False)
						self.switchMasodlagos_F(False)

			# 70: Dual mode (based on outdoor temperature, with hysteresis) | 70: Dual mód (külső hőmérséklet alapján, hiszterézissel)
			elif mode == "70":
				Domoticz.Debug('Dual mode (based on outdoor temperature, with hysteresis) | Dual mód (külső hőmérséklet alapján, hiszterézissel)')

				# Hysteresis thresholds | --- Hiszterézis határok ---
				upper_limit = outlimit + outhiszt     # Above: primary | Fölötte: elsődleges
				lower_limit = outlimit - outhiszt     # Below: secondary | Alatta: másodlagos

				# Determine mode (switch only outside hysteresis band) | Üzemmód meghatározása (váltás csak a külső tartományokon túl)
				if self.outtemp > upper_limit:
					Domoticz.Debug(("Outdoor temperature above upper threshold: primary mode | " + (f"Kint melegebb ({self.outtemp:.1f}°C > {upper_limit:.1f}°C) → Elsődleges")))
					self.F_last_mode_state = 0

				elif self.outtemp < lower_limit:
					Domoticz.Debug(("Outdoor temperature below lower threshold: dual mode | " + (f"Kint hidegebb ({self.outtemp:.1f}°C < {lower_limit:.1f}°C) → Dual")))
					self.F_last_mode_state = 1

				else:
					Domoticz.Debug(
						(f"Outdoor temperature {self.outtemp:.1f} within hysteresis band ({lower_limit:.1f}–{upper_limit:.1f}): retain mode {self.F_last_mode_state} | " + (f"Külső hőmérséklet hiszterézisen belül "
						f"({lower_limit:.1f}–{upper_limit:.1f}) → nincs váltás, tartjuk a(z) {self.F_last_mode_state} módot"))
					)

				# Switch according to stored mode | Kapcsolás a tárolt üzemmód szerint
				if self.F_last_mode_state == 0:
					# Primary | Elsődleges
					if self.operation:
						self.switchElsodleges_F(True)
						self.switchMasodlagos_F(False)
					else:
						self.switchElsodleges_F(False)
						self.switchMasodlagos_F(False)
				else:
					# Dual mode | Dual mód
					if self.operation:
						self.switchElsodleges_F(True)
						self.switchMasodlagos_F(True)
					else:
						self.switchElsodleges_F(False)
						self.switchMasodlagos_F(False)
					

			# 80: Dual mode (based on outdoor dew point, with hysteresis) | 80: Dual mód (külső harmatpont alapján, hiszterézissel)
			elif mode == "80":
				Domoticz.Debug('Dual mode (based on outdoor dew point, with hysteresis) | Dual mód (külső harmatpont alapján, hiszterézissel)')

				# Calculate dew-point gap | Harmatpont-különbség kiszámítása
				dew_gap = self.outtemp - self.outdewpoint

				SAFE = outdewpointkomp		# May be negative or positive | Lehet negatív vagy pozitív
				HYST = outhiszt			# Hysteresis | Hiszterézis

				Domoticz.Debug(f"Outdoor temperature: {self.outtemp:.1f}°C | Külső hőmérséklet: {self.outtemp:.1f}°C")
				Domoticz.Debug(f"Outdoor dew point: {self.outdewpoint:.1f}°C | Külső harmatpont: {self.outdewpoint:.1f}°C")
				Domoticz.Debug(f"Dew-point gap (temperature minus dew point): {dew_gap:.1f}°C | Harmatpont-különbség (hőmérséklet mínusz harmatpont): {dew_gap:.1f}°C")
				Domoticz.Debug(f"Safety threshold (outdewpointkomp): {SAFE:.1f}°C | Biztonsági határ (outdewpointkomp): {SAFE:.1f}°C")
				Domoticz.Debug(f"Hysteresis (outhiszt): {HYST:.1f}°C | Hiszterézis (outhiszt): {HYST:.1f}°C")

				# MODE SWITCHING | ÜZEMMÓDVÁLTÁS
				# 1 = Primary (heat pump) | 1 = Elsődleges (hőszivattyú)
				# 2 = Secondary (boiler) | 2 = Másodlagos (kazán)

				# Freeze risk: dew-point gap too small, switch to secondary | Fagyveszély: túl kicsi harmatpont-különbség, váltás másodlagosra
				if dew_gap < SAFE:
					Domoticz.Debug(
						("Dew-point gap below safe threshold: secondary mode; heat pump disabled | " + (f"Dew-gap {dew_gap:.1f}°C < SAFE {SAFE:.1f}°C → Másodlagos mód (HP tilt)"))
					)
					self.F_last_mode_state = 2

				# Safe range: enable heat pump again | Biztonságos tartomány: újra engedélyezzük a hőszivattyút
				elif dew_gap > SAFE + HYST:
					Domoticz.Debug(
						("Dew-point gap above safe threshold plus hysteresis: primary mode | " + (f"Dew-gap {dew_gap:.1f}°C > SAFE+HYST {SAFE + HYST:.1f}°C → Elsődleges mód"))
					)
					self.F_last_mode_state = 1

				else:
					Domoticz.Debug(
						("Dew-point gap within hysteresis band: retain current mode | " + (f"Dew-gap {dew_gap:.1f}°C a sávban ({SAFE:.1f}–{SAFE + HYST:.1f}) → "
						f"tartjuk a(z) {self.F_last_mode_state} módot"))
					)

				# SWITCHING | KAPCSOLÁS
				if self.F_last_mode_state == 1:
					# Primary | Elsődleges
					self.switchMasodlagos_F(False)
					if self.operation:
						self.switchElsodleges_F(True)
					else:
						self.switchElsodleges_F(False)

				else:
					# Dual mode | Dual mód
					if self.operation:
						self.switchElsodleges_F(True)
						self.switchMasodlagos_F(True)
					else:
						self.switchElsodleges_F(False)
						self.switchMasodlagos_F(False)

			# 90: Saver mode (indoor + outdoor temperature, with hysteresis) | 90: Saver mód (belső + külső hőmérséklet, hiszterézissel)
			elif mode == "90":
				Domoticz.Debug('Switching mode (combined indoor target and outdoor condition, with hysteresis) | Váltó mód (belső cél és külső feltétel kombinációja, hiszterézissel)')

				# Indoor switching point | Belső váltási pont
				target_switch = self.DualFsetpoint - dualdiff
				upper_int = target_switch + dualhiszt     # Switch back to 1 | Visszaváltás 1-re
				lower_int = target_switch - dualhiszt     # Switch to 2 | Váltás 2-re

				# Outdoor condition | Külső feltétel
				outer_ok_limit = outlimit - outhiszt      # Allow mode 2 only when it is warm enough | Csak akkor engedélyezett a 2-es mód, ha elég meleg van

				Domoticz.Debug(
					("Indoor switching limits and outdoor limit | " + (f"belső váltás: lower={lower_int:.2f}, upper={upper_int:.2f}, "
					f"külső limit={outer_ok_limit:.2f}"))
				)
				Domoticz.Debug(("Average indoor temperature and outdoor temperature | " + (f"IntAvgTemp={self.intemp_avg:.2f}, Outtemp={self.outtemp:.2f}")))

				# 1) If indoor temperature exceeds upper, return to mode 1 | 1) Ha bent melegebb van, mint upper, vissza az 1-es módra
				if self.intemp_avg > upper_int:
					Domoticz.Debug('Indoor temperature high → primary mode | Magas belső hőmérséklet → elsődleges mód')
					self.F_last_mode_state = 0

				# 2) If indoor temperature is below lower and outdoor temperature is warm enough, switch to mode 2 | 2) Ha bent hidegebb van, mint lower, de kint elég meleg, váltás a 2-es módra
				elif self.intemp_avg < lower_int and self.outtemp >= outer_ok_limit:
					Domoticz.Debug('Indoor temperature low and outdoor condition permits → secondary mode | Alacsony belső hőmérséklet és a külső feltétel megengedi → másodlagos mód')
					self.F_last_mode_state = 1

				# 3) If both indoor and outdoor temperatures are low, mode 2 is blocked; stay in mode 1 | 3) Ha bent és kint is hideg van, a 2-es mód tiltott; marad az 1-es
				elif self.intemp_avg < lower_int and self.outtemp < outer_ok_limit:
					Domoticz.Debug('Indoor temperature low, but outdoors too cold → primary mode | Alacsony belső hőmérséklet, de kint túl hideg → elsődleges mód')
					self.F_last_mode_state = 0

				# 4) Hysteresis band | 4) Hiszterézistartomány
				else:
					Domoticz.Debug(
						("Within hysteresis band: retain current mode | " + (f"Hiszterézis tartomány → tartjuk a módot: {self.F_last_mode_state}"))
					)

				# Execution | --- Végrehajtás ---
				if self.F_last_mode_state == 0:
					if self.operation:
						self.switchElsodleges_F(True)
					else:
						self.switchElsodleges_F(False)
					self.switchMasodlagos_F(False)

				else:
					self.switchElsodleges_F(False)
					if self.operation:
						self.switchMasodlagos_F(True)
					else:
						self.switchMasodlagos_F(False)

			# 100: Saver mode (indoor temperature + outdoor dew point, with hysteresis) | 100: Saver mód (belső + külső harmatpont, hiszterézissel)
			elif mode == "100":
				Domoticz.Debug('Switching mode (combined indoor temperature and outdoor dew point, with hysteresis) | Váltó mód (belső hőmérséklet és külső harmatpont kombinációja, hiszterézissel)')

				# Adjusted outdoor temperature | --- Korrigált külső hőmérséklet ---
				Tcorr = self.outtemp + outdewpointkomp

				# Dew point hysteresis thresholds | Harmatpont hiszterézis határok
				safe_low  = Tcorr - outhiszt     # Below: safe, mode 2 is permitted | Alatta: biztonságos, engedélyezett a 2-es mód
				safe_high = Tcorr + outhiszt     # Above: unsafe, mode 2 is blocked | Fölötte: veszélyes, a 2-es mód tiltott

				# Indoor temperature hysteresis | Belső hőmérséklet hiszterézise
				target_switch = self.DualFsetpoint - dualdiff
				upper_int = target_switch + dualhiszt    # Back to 1 | Vissza 1-re
				lower_int = target_switch - dualhiszt    # Switch to 2 | Váltás 2-re

				# Debug | Hibakeresés
				Domoticz.Debug(f"Corrected temperature={Tcorr:.2f}, safe lower bound={safe_low:.2f}, safe upper bound={safe_high:.2f} | Korrigált hőmérséklet={Tcorr:.2f}, biztonságos alsó határ={safe_low:.2f}, biztonságos felső határ={safe_high:.2f}")
				Domoticz.Debug(f"Indoor lower limit={lower_int:.2f}, upper limit={upper_int:.2f} | Belső alsó határ={lower_int:.2f}, felső határ={upper_int:.2f}")
				Domoticz.Debug(f"Dew point={self.outdewpoint:.2f}, average indoor temperature={self.intemp_avg:.2f} | Harmatpont={self.outdewpoint:.2f}, belső átlaghőmérséklet={self.intemp_avg:.2f}")

				# 1) Indoor condition: too warm; return to primary mode | 1) Belső feltétel: túl meleg van; vissza az elsődleges módra
				if self.intemp_avg > upper_int:
					Domoticz.Debug('Indoors too warm → primary mode | Bent túl meleg van → elsődleges mód')
					self.F_last_mode_state = 0

				# 2) Indoors is cold and dew point is safe; use secondary mode | 2) Bent hideg van, és a harmatpont biztonságos; másodlagos mód
				elif self.intemp_avg < lower_int and self.outdewpoint < safe_low:
					Domoticz.Debug('Indoors cold and dew point low → secondary mode | Bent hideg van és alacsony a harmatpont → másodlagos mód')
					self.F_last_mode_state = 1

				# 3) Indoors is cold but dew point is too high; use primary mode | 3) Bent hideg van, de a harmatpont túl magas; elsődleges mód
				elif self.intemp_avg < lower_int and self.outdewpoint > safe_high:
					Domoticz.Debug('Indoors cold but dew point high → primary mode | Bent hideg van, de magas a harmatpont → elsődleges mód')
					self.F_last_mode_state = 0

				# 4) Within hysteresis band: keep current mode | 4) Hiszterézistartomány: megtartjuk az aktuális módot
				else:
					Domoticz.Debug(
						("Within hysteresis band: retain current mode | " + (f"Hiszterézis tartomány → mód tartása: {self.F_last_mode_state}"))
					)

				# Switching | Kapcsolás
				if self.F_last_mode_state == 0:
					# Primary | Elsődleges
					if self.operation:
						self.switchElsodleges_F(True)
					else:
						self.switchElsodleges_F(False)
					self.switchMasodlagos_F(False)

				else:
					# Secondary | Másodlagos
					self.switchElsodleges_F(False)
					if self.operation:
						self.switchMasodlagos_F(True)
					else:
						self.switchMasodlagos_F(False)


			# 110: Switching mode (based on 500 W energy, with hysteresis) | 110: Váltó mód (500W energetika alapján, hiszterézissel)
			elif mode == "110":
				Domoticz.Debug('Switching mode (500 W, percentage hysteresis) | Váltó mód (500 W, százalékos hiszterézis)')
				power = self.aktual_watt
				base = 500
				if self.F_last_mode_state == 0:
					power += base
				h = int(base * int(Devices[85].sValue) / 100)
				Domoticz.Debug(f"Power={power} W, base={base} W, hysteresis=±{h} W | Teljesítmény={power} W, alapérték={base} W, hiszterézis=±{h} W")

				if power >= base + h:
					self.F_last_mode_state = 0
				elif power <= base - h:
					self.F_last_mode_state = 1
				
				if self.F_last_mode_state == 0:
					if self.operation: 
						self.switchElsodleges_F(True)
					else: 
						self.switchElsodleges_F(False)
					self.switchMasodlagos_F(False)
				else:
					self.switchElsodleges_F(False)
					if self.operation: 
						self.switchMasodlagos_F(True)
					else: 
						self.switchMasodlagos_F(False)

			# 120: Switching mode (based on 1000 W energy, with hysteresis) | 120: Váltó mód (1000W energetika alapján, hiszterézissel)
			elif mode == "120":
				Domoticz.Debug('Switching mode (1000 W, percentage hysteresis) | Váltó mód (1000 W, százalékos hiszterézis)')
				power = self.aktual_watt
				base = 1000
				if self.F_last_mode_state == 0:
					power += base
				h = int(base * int(Devices[85].sValue) / 100)
				Domoticz.Debug(f"Power={power} W, base={base} W, hysteresis=±{h} W | Teljesítmény={power} W, alapérték={base} W, hiszterézis=±{h} W")

				if power >= base + h:
					self.F_last_mode_state = 0
				elif power <= base - h:
					self.F_last_mode_state = 1
				
				if self.F_last_mode_state == 0:
					if self.operation: 
						self.switchElsodleges_F(True)
					else: 
						self.switchElsodleges_F(False)
					self.switchMasodlagos_F(False)
				else:
					self.switchElsodleges_F(False)
					if self.operation: 
						self.switchMasodlagos_F(True)
					else: 
						self.switchMasodlagos_F(False)

			# 130: Switching mode (based on 1500 W energy, with hysteresis) | 130: Váltó mód (1500W energetika alapján, hiszterézissel)
			elif mode == "130":
				Domoticz.Debug('Switching mode (1500 W, percentage hysteresis) | Váltó mód (1500 W, százalékos hiszterézis)')
				power = self.aktual_watt
				base = 1500
				if self.F_last_mode_state == 0:
					power += base
				h = int(base * int(Devices[85].sValue) / 100)
				Domoticz.Debug(f"Power={power} W, base={base} W, hysteresis=±{h} W | Teljesítmény={power} W, alapérték={base} W, hiszterézis=±{h} W")

				if power >= base + h:
					self.F_last_mode_state = 0
				elif power <= base - h:
					self.F_last_mode_state = 1

				if self.F_last_mode_state == 0:
					if self.operation: 
						self.switchElsodleges_F(True)
					else: 
						self.switchElsodleges_F(False)
					self.switchMasodlagos_F(False)
				else:
					self.switchElsodleges_F(False)
					if self.operation: 
						self.switchMasodlagos_F(True)
					else: 
						self.switchMasodlagos_F(False)

			# 140: Switching mode (based on 2000 W energy, with hysteresis) | 140: Váltó mód (2000W energetika alapján, hiszterézissel)
			elif mode == "140":
				Domoticz.Debug('Switching mode (2000 W, percentage hysteresis) | Váltó mód (2000 W, százalékos hiszterézis)')
				power = self.aktual_watt
				base = 2000
				if self.F_last_mode_state == 0:
					power += base
				h = int(base * int(Devices[85].sValue) / 100)
				Domoticz.Debug(f"Power={power} W, base={base} W, hysteresis=±{h} W | Teljesítmény={power} W, alapérték={base} W, hiszterézis=±{h} W")

				if power >= base + h:
					self.F_last_mode_state = 0
				elif power <= base - h:
					self.F_last_mode_state = 1

				if self.F_last_mode_state == 0:
					if self.operation: 
						self.switchElsodleges_F(True)
					else: 
						self.switchElsodleges_F(False)
					self.switchMasodlagos_F(False)
				else:
					self.switchElsodleges_F(False)
					if self.operation: 
						self.switchMasodlagos_F(True)
					else: 
						self.switchMasodlagos_F(False)

			# 150: Switching mode (based on 3000 W energy, with hysteresis) | 150: Váltó mód (3000W energetika alapján, hiszterézissel)
			elif mode == "150":
				Domoticz.Debug('Switching mode (3000 W, percentage hysteresis) | Váltó mód (3000 W, százalékos hiszterézis)')
				power = self.aktual_watt
				base = 3000
				if self.F_last_mode_state == 0:
					power += base
				h = int(base * int(Devices[85].sValue) / 100)
				Domoticz.Debug(f"Power={power} W, base={base} W, hysteresis=±{h} W | Teljesítmény={power} W, alapérték={base} W, hiszterézis=±{h} W")

				if power >= base + h:
					self.F_last_mode_state = 0
				elif power <= base - h:
					self.F_last_mode_state = 1

				if self.F_last_mode_state == 0:
					if self.operation: 
						self.switchElsodleges_F(True)
					else: 
						self.switchElsodleges_F(False)
					self.switchMasodlagos_F(False)
				else:
					self.switchElsodleges_F(False)
					if self.operation: 
						self.switchMasodlagos_F(True)
					else: 
						self.switchMasodlagos_F(False)

			# 160: Switching mode (based on 4000 W energy, with hysteresis) | 160: Váltó mód (4000W energetika alapján, hiszterézissel)
			elif mode == "160":
				Domoticz.Debug('Switching mode (4000 W, percentage hysteresis) | Váltó mód (4000 W, százalékos hiszterézis)')
				power = self.aktual_watt
				base = 4000
				if self.F_last_mode_state == 0:
					power += base
				h = int(base * int(Devices[85].sValue) / 100)
				Domoticz.Debug(f"Power={power} W, base={base} W, hysteresis=±{h} W | Teljesítmény={power} W, alapérték={base} W, hiszterézis=±{h} W")

				if power >= base + h:
					self.F_last_mode_state = 0
				elif power <= base - h:
					self.F_last_mode_state = 1

				if self.F_last_mode_state == 0:
					if self.operation: 
						self.switchElsodleges_F(True)
					else: 
						self.switchElsodleges_F(False)
					self.switchMasodlagos_F(False)
				else:
					self.switchElsodleges_F(False)
					if self.operation: 
						self.switchMasodlagos_F(True)
					else: 
						self.switchMasodlagos_F(False)

			# 170: Switching mode (based on 5000 W energy, with hysteresis) | 170: Váltó mód (5000W energetika alapján, hiszterézissel)
			elif mode == "170":
				Domoticz.Debug('Switching mode (5000 W, percentage hysteresis) | Váltó mód (5000 W, százalékos hiszterézis)')
				power = self.aktual_watt
				base = 5000
				if self.F_last_mode_state == 0:
					power += base
				h = int(base * int(Devices[85].sValue) / 100)
				Domoticz.Debug(f"Power={power} W, base={base} W, hysteresis=±{h} W | Teljesítmény={power} W, alapérték={base} W, hiszterézis=±{h} W")

				if power >= base + h:
					self.F_last_mode_state = 0
				elif power <= base - h:
					self.F_last_mode_state = 1

				if self.F_last_mode_state == 0:
					if self.operation: 
						self.switchElsodleges_F(True)
					else: 
						self.switchElsodleges_F(False)
					self.switchMasodlagos_F(False)
				else:
					self.switchElsodleges_F(False)
					if self.operation: 
						self.switchMasodlagos_F(True)
					else: 
						self.switchMasodlagos_F(False)

			# 180: Dual mode (based on 500 W energy, with hysteresis) | 180: Dual mód (500W energetika alapján, hiszterézissel)
			elif mode == "180":
				Domoticz.Debug('Dual mode (500 W, percentage hysteresis) | Dual mód (500 W, százalékos hiszterézis)')
				power = self.aktual_watt
				base = 500
				if self.F_last_mode_state == 0:
					power += base
				h = int(base * int(Devices[85].sValue) / 100)
				Domoticz.Debug(f"Power={power} W, base={base} W, hysteresis=±{h} W | Teljesítmény={power} W, alapérték={base} W, hiszterézis=±{h} W")

				if power >= base + h:
					self.F_last_mode_state = 0
				elif power <= base - h:
					self.F_last_mode_state = 1

				if self.F_last_mode_state == 0:
					if self.operation:
						self.switchElsodleges_F(True)
						self.switchMasodlagos_F(True)
					else:
						self.switchElsodleges_F(False)
						self.switchMasodlagos_F(False)
				else:
					self.switchElsodleges_F(False)
					if self.operation: 
						self.switchMasodlagos_F(True)
					else: 
						self.switchMasodlagos_F(False)

			# 190: Dual mode (based on 1000 W energy, with hysteresis) | 190: Dual mód (1000W energetika alapján, hiszterézissel)
			elif mode == "190":
				Domoticz.Debug('Dual mode (1000 W, percentage hysteresis) | Dual mód (1000 W, százalékos hiszterézis)')
				power = self.aktual_watt
				base = 1000
				if self.F_last_mode_state == 0:
					power += base
				h = int(base * int(Devices[85].sValue) / 100)
				Domoticz.Debug(f"Power={power} W, base={base} W, hysteresis=±{h} W | Teljesítmény={power} W, alapérték={base} W, hiszterézis=±{h} W")

				if power >= base + h:
					self.F_last_mode_state = 0
				elif power <= base - h:
					self.F_last_mode_state = 1

				if self.F_last_mode_state == 0:
					if self.operation:
						self.switchElsodleges_F(True)
						self.switchMasodlagos_F(True)
					else:
						self.switchElsodleges_F(False)
						self.switchMasodlagos_F(False)
				else:
					self.switchElsodleges_F(False)
					if self.operation: 
						self.switchMasodlagos_F(True)
					else: 
						self.switchMasodlagos_F(False)

			# 200: Dual mode (based on 1500 W energy, with hysteresis) | 200: Dual mód (1500W energetika alapján, hiszterézissel)
			elif mode == "200":
				Domoticz.Debug('Dual mode (1500 W, percentage hysteresis) | Dual mód (1500 W, százalékos hiszterézis)')
				power = self.aktual_watt
				base = 1500
				if self.F_last_mode_state == 0:
					power += base
				h = int(base * int(Devices[85].sValue) / 100)
				Domoticz.Debug(f"Power={power} W, base={base} W, hysteresis=±{h} W | Teljesítmény={power} W, alapérték={base} W, hiszterézis=±{h} W")

				if power >= base + h:
					self.F_last_mode_state = 0
				elif power <= base - h:
					self.F_last_mode_state = 1

				if self.F_last_mode_state == 0:
					if self.operation:
						self.switchElsodleges_F(True)
						self.switchMasodlagos_F(True)
					else:
						self.switchElsodleges_F(False)
						self.switchMasodlagos_F(False)
				else:
					self.switchElsodleges_F(False)
					if self.operation: 
						self.switchMasodlagos_F(True)
					else: 
						self.switchMasodlagos_F(False)

			# 210: Dual mode (based on 2000 W energy, with hysteresis) | 210: Dual mód (2000W energetika alapján, hiszterézissel)
			elif mode == "210":
				Domoticz.Debug('Dual mode (2000 W, percentage hysteresis) | Dual mód (2000 W, százalékos hiszterézis)')
				power = self.aktual_watt
				base = 2000
				if self.F_last_mode_state == 0:
					power += base
				h = int(base * int(Devices[85].sValue) / 100)
				Domoticz.Debug(f"Power={power} W, base={base} W, hysteresis=±{h} W | Teljesítmény={power} W, alapérték={base} W, hiszterézis=±{h} W")

				if power >= base + h:
					self.F_last_mode_state = 0
				elif power <= base - h:
					self.F_last_mode_state = 1

				if self.F_last_mode_state == 0:
					if self.operation:
						self.switchElsodleges_F(True)
						self.switchMasodlagos_F(True)
					else:
						self.switchElsodleges_F(False)
						self.switchMasodlagos_F(False)
				else:
					self.switchElsodleges_F(False)
					if self.operation: 
						self.switchMasodlagos_F(True)
					else: 
						self.switchMasodlagos_F(False)

			# 220: Dual mode (based on 3000 W energy, with hysteresis) | 220: Dual mód (3000W energetika alapján, hiszterézissel)
			elif mode == "220":
				Domoticz.Debug('Dual mode (3000 W, percentage hysteresis) | Dual mód (3000 W, százalékos hiszterézis)')
				power = self.aktual_watt
				base = 3000
				if self.F_last_mode_state == 0:
					power += base
				h = int(base * int(Devices[85].sValue) / 100)
				Domoticz.Debug(f"Power={power} W, base={base} W, hysteresis=±{h} W | Teljesítmény={power} W, alapérték={base} W, hiszterézis=±{h} W")

				if power >= base + h:
					self.F_last_mode_state = 0
				elif power <= base - h:
					self.F_last_mode_state = 1

				if self.F_last_mode_state == 0:
					if self.operation:
						self.switchElsodleges_F(True)
						self.switchMasodlagos_F(True)
					else:
						self.switchElsodleges_F(False)
						self.switchMasodlagos_F(False)
				else:
					self.switchElsodleges_F(False)
					if self.operation: 
						self.switchMasodlagos_F(True)
					else: 
						self.switchMasodlagos_F(False)

			# 230: Dual mode (based on 4000 W energy, with hysteresis) | 230: Dual mód (4000W energetika alapján, hiszterézissel)
			elif mode == "230":
				Domoticz.Debug('Dual mode (4000 W, percentage hysteresis) | Dual mód (4000 W, százalékos hiszterézis)')
				power = self.aktual_watt
				base = 4000
				if self.F_last_mode_state == 0:
					power += base
				h = int(base * int(Devices[85].sValue) / 100)
				Domoticz.Debug(f"Power={power} W, base={base} W, hysteresis=±{h} W | Teljesítmény={power} W, alapérték={base} W, hiszterézis=±{h} W")

				if power >= base + h:
					self.F_last_mode_state = 0
				elif power <= base - h:
					self.F_last_mode_state = 1

				if self.F_last_mode_state == 0:
					if self.operation:
						self.switchElsodleges_F(True)
						self.switchMasodlagos_F(True)
					else:
						self.switchElsodleges_F(False)
						self.switchMasodlagos_F(False)
				else:
					self.switchElsodleges_F(False)
					if self.operation: 
						self.switchMasodlagos_F(True)
					else: 
						self.switchMasodlagos_F(False)

			# 240: Dual mode (based on 5000 W energy, with hysteresis) | 240: Dual mód (5000W energetika alapján, hiszterézissel)
			elif mode == "240":
				Domoticz.Debug('Dual mode (5000 W, percentage hysteresis) | Dual mód (5000 W, százalékos hiszterézis)')
				power = self.aktual_watt
				base = 5000
				if self.F_last_mode_state == 0:
					power += base
				h = int(base * int(Devices[85].sValue) / 100)
				Domoticz.Debug(f"Power={power} W, base={base} W, hysteresis=±{h} W | Teljesítmény={power} W, alapérték={base} W, hiszterézis=±{h} W")

				if power >= base + h:
					self.F_last_mode_state = 0
				elif power <= base - h:
					self.F_last_mode_state = 1

				if self.F_last_mode_state == 0:
					if self.operation:
						self.switchElsodleges_F(True)
						self.switchMasodlagos_F(True)
					else:
						self.switchElsodleges_F(False)
						self.switchMasodlagos_F(False)
				else:
					self.switchElsodleges_F(False)
					if self.operation: 
						self.switchMasodlagos_F(True)
					else: 
						self.switchMasodlagos_F(False)


	def CoolDevices(self):

		self.operation = set()
		self.switchElsodleges_H(False)
		self.switchMasodlagos_H(False)

		Domoticz.Debug('Zone cooling devices | Zónahűtési eszközök')
		
		if self.cooling_active:
		
			Domoticz.Debug('Zone cooling mode | Zónahűtési mód')

			for i in range(1, 13):
				if getattr(self, f'Zone_TempSensors_{i}') and (Devices[22].sValue != "0" and Devices[22].Used == 1):
					aktual_temp = getattr(self, f'zone_{i}_aktual_temp') or self.intemp
					target_also = getattr(self, f'htargettemp_{i}_also')
					target_felso = getattr(self, f'htargettemp_{i}_felso')
					window_closed = getattr(self, f'zone_{i}_window_closed')

					aktual_temp = round(aktual_temp, 2)
					target_felso = round(target_felso, 2)
					target_also = round(target_also, 2)

					if getattr(self, f'zone_{i}_window_closed'):
						if aktual_temp >= target_felso:
							Domoticz.Debug(("Temperature exceeds target: open heating valve for zone | " + (f"Melegebb van mint a cél, szelep nyitás zone_{i} H")))
							self.switchzone_H(i, True)
							if self.switchElsodleges_H and Devices[215].sValue == "10":
								self.send_AC_command(i, "H", "On")
							elif self.switchMasodlagos_H and Devices[215].sValue == "20":
								self.send_AC_command(i, "H", "On")
							else: 
								self.send_AC_command(i, "H", "Off")

							self.update_setpoint_pluss(i)
							self.operation.add(i)
							continue

						elif aktual_temp <= target_also:
							Domoticz.Debug(("Temperature below target: close heating valve for zone | " + (f"Hidegebb van mint a cél, szelep zárás zone_{i} H")))
							self.switchzone_H(i, False)
							self.send_AC_command(i, "H", "Off")
							self.update_setpoint_minusz(i)
							continue
						
						else:
							# Keep previous cooling state within hysteresis limits | A hiszterézishatárok között megtartjuk az előző hűtési állapotot
							zone_state = getattr(self, f'zone_{i}_cooling_state', False)

							Domoticz.Debug(f"Zone_{i} within hysteresis limits, previous cooling state: {zone_state} | Zone_{i} hiszterézishatárok között, előző hűtési állapot: {zone_state}")

							self.switchzone_H(i, zone_state)

							if zone_state:
								if self.switchElsodleges_H and Devices[215].sValue == "10":
									self.send_AC_command(i, "H", "On")
								elif self.switchMasodlagos_H and Devices[215].sValue == "20":
									self.send_AC_command(i, "H", "On")
								else:
									self.send_AC_command(i, "H", "Off")

								self.update_setpoint_pluss(i)
								self.operation.add(i)
							else:
								self.send_AC_command(i, "H", "Off")
								self.update_setpoint_minusz(i)

							continue

					else:
						Domoticz.Debug(f"Zone_{i} window | Zone_{i} ablak")
						self.switchzone_H(i, False)
						self.send_AC_command(i, "H", "Off")
						self.update_setpoint_minusz(i)

			Domoticz.Debug(f"Summary: operation = {self.operation} | Összegzés: operation = {self.operation}")

			if self.operation :
				
				if Devices[101].sValue == "10" :

					Domoticz.Debug("Dew-point-based cooling control | Harmatpont hűtésvezérlés")

					self.Kevero_1_temp_target = int(self.maxindewpoint +  self.Kevero_1_harmatkorr)
					Devices[72].Update(nValue=0, sValue=str(self.Kevero_1_temp_target), TimedOut=False)

					if self.Kevero_1_temp_aktual - self.Kevero_1_harmatkorr < self.minindewpoint :
						Domoticz.Debug("Dew point: mixing valve 1 is too cold; increase temperature | Harmatpont, túl hideg 1 keverőszelep növelni kell a hőfokot")
						self.switch_kevero_1_plusz(True)
						self.switch_kevero_1_minusz(False)
						
					elif self.Kevero_1_temp_aktual > self.minindewpoint + self.Kevero_1_harmatkorr + self.Kevero_1_hiszterezis  :
						Domoticz.Debug(("Dew point control: supply temperature is above mixer 1 dew-point-corrected threshold; reduce supply temperature | " + ("Harmatpont, melegebb az előremenő mint a self.Kevero_1_temp_aktual - self.Kevero_1_harmatkorr + self.Kevero_1_hiszterezis, hűteni kell az előre menőt")))
						self.switch_kevero_1_minusz(True)
						self.switch_kevero_1_plusz(False)
						
					else :
						Domoticz.Debug('Dew-point control: mixing valve 1 is within target temperature range; no action required | Harmatpontszabályozás: az 1. keverőszelep a célhőmérséklet-tartományon belül van, nem kell beavatkozni')
						self.switch_kevero_1_plusz(False)
						self.switch_kevero_1_minusz(False)


					self.Kevero_2_temp_target = int(self.maxindewpoint +  self.Kevero_2_harmatkorr)
					Devices[73].Update(nValue=0, sValue=str(self.Kevero_2_temp_target), TimedOut=False)

					if self.Kevero_2_temp_aktual - self.Kevero_2_harmatkorr < self.minindewpoint :
						Domoticz.Debug("Dew point: mixing valve 2 is too cold; increase temperature | Harmatpont, túl hideg 2 keverőszelep növelni kell a hőfokot")
						self.switch_kevero_2_plusz(True)
						self.switch_kevero_2_minusz(False)
						
					elif self.Kevero_2_temp_aktual > self.minindewpoint + self.Kevero_2_harmatkorr + self.Kevero_2_hiszterezis  :
						Domoticz.Debug(("Dew point control: supply temperature is above mixer 2 dew-point-corrected threshold; reduce supply temperature | " + ("Harmatpont, melegebb az előremenő mint a self.Kevero_2_temp_aktual - self.Kevero_2_harmatkorr + self.Kevero_2_hiszterezis, hűteni kell az előre menőt")))
						self.switch_kevero_2_minusz(True)
						self.switch_kevero_2_plusz(False)
						
					else :
						Domoticz.Debug('Dew-point control: mixing valve 1 is within target temperature range; no action required | Harmatpontszabályozás: az 1. keverőszelep a célhőmérséklet-tartományon belül van, nem kell beavatkozni')
						self.switch_kevero_2_plusz(False)
						self.switch_kevero_2_minusz(False)

				else :

					Domoticz.Debug("Normal cooling control | Normál hűtésvezérlés")
					
					self.Kevero_1_temp_max = float(Devices[119].sValue)
					self.Kevero_1_temp_min = float(Devices[121].sValue)

					if self.maxintemp <= self.Hsetpoint:
						arany = 0
					else:
						kulonbseg = abs(round(self.maxintemp - self.Hsetpoint , 1))
						arany = max(0, min(1, kulonbseg / (self.Kevero_1_szorzo / 100)))

					self.Kevero_1_temp_target = round(self.Kevero_1_temp_max - arany * (abs(self.Kevero_1_temp_max - self.Kevero_1_temp_min)), 1)

					Devices[72].Update(nValue=0, sValue=str(self.Kevero_1_temp_target), TimedOut=False)
					
					if self.Kevero_1_temp_aktual > self.Kevero_1_temp_target + self.Kevero_1_hiszterezis :
						Domoticz.Debug("Mixing valve 1 is too cold; increase temperature | Túl hideg 1 keverőszelep növelni kell a hőfokot")
						self.switch_kevero_1_plusz(True)
						self.switch_kevero_1_minusz(False)

					elif self.Kevero_1_temp_aktual + self.Kevero_1_hiszterezis < self.Kevero_1_temp_target :
						Domoticz.Debug(("Supply temperature exceeds mixer 1 dew-point-corrected threshold; reduce supply temperature | " + ("Melegebb az előremenő mint a self.Kevero_1_temp_aktual - self.Kevero_1_harmatkorr + self.Kevero_1_hiszterezis, hűteni kell az előre menőt")))
						self.switch_kevero_1_minusz(True)
						self.switch_kevero_1_plusz(False)
					
					else :
						Domoticz.Debug('Mixing valve 1 temperature is within target range; no action required | Az 1. keverőszelep hőmérséklete a céltartományon belül van, nem kell beavatkozni')
						self.switch_kevero_1_plusz(False)
						self.switch_kevero_1_minusz(False)


					self.Kevero_2_temp_max = float(Devices[120].sValue)
					self.Kevero_2_temp_min = float(Devices[122].sValue)
					
					if self.maxintemp <= self.Hsetpoint:
						arany = 0
					else:
						kulonbseg = abs(round(self.maxintemp - self.Hsetpoint , 1))
						arany = max(0, min(1, kulonbseg / (self.Kevero_2_szorzo / 100)))

					self.Kevero_2_temp_target = round(self.Kevero_2_temp_max - arany * (abs(self.Kevero_2_temp_max - self.Kevero_2_temp_min)), 1)
					
					Devices[73].Update(nValue=0, sValue=str(self.Kevero_2_temp_target), TimedOut=False)
					
					if self.Kevero_2_temp_aktual > self.Kevero_2_temp_target + self.Kevero_2_hiszterezis :
						Domoticz.Debug("Mixing valve 2 is too cold; increase temperature | Túl hideg 2 keverőszelep növelni kell a hőfokot")
						self.switch_kevero_2_plusz(True)
						self.switch_kevero_2_minusz(False)

					elif self.Kevero_2_temp_aktual + self.Kevero_2_hiszterezis < self.Kevero_2_temp_target :
						Domoticz.Debug(("Supply temperature exceeds mixer 2 dew-point-corrected threshold; reduce supply temperature | " + ("Melegebb az előremenő mint a self.Kevero_2_temp_aktual - self.Kevero_2_harmatkorr + self.Kevero_2_hiszterezis, hűteni kell az előre menőt")))
						self.switch_kevero_2_minusz(True)
						self.switch_kevero_2_plusz(False)
					
					else :
						Domoticz.Debug('Mixing valve 2 temperature is within target range; no action required | A 2. keverőszelep hőmérséklete a céltartományon belül van, nem kell beavatkozni')
						self.switch_kevero_2_plusz(False)
						self.switch_kevero_2_minusz(False)
					

			# Initially turn all virtual valves off; turn them on when needed | Minden virtuális szelep kezdetben legyen kikapcsolva; szükség esetén bekapcsoljuk
			for vlist in self.Zone_H_V:
				for idx in vlist:
					self.switchappend(idx, "Off")

			if len(self.operation) == 1:
				main_zone = next(iter(self.operation))

				virtual_list = getattr(self, f'Zone_{main_zone}_H_V', [])

				for idx in virtual_list:
					self.switchappend(idx, "On")

				Domoticz.Debug(f"Cooling virtual devices ON: main_zone={main_zone}, idx={virtual_list} | Hűtési virtuális eszközök BE: fő_zóna={main_zone}, idx={virtual_list}")
			else:
				Domoticz.Debug(f"Cooling virtual devices OFF | Hűtési virtuális eszközök KI")


			# Virtual hydraulic shifter status | Virtuális hidraulikus váltó állapota
			if len(self.operation) == 1:
				main_zone = next(iter(self.operation))
				virtual_list = getattr(self, f'Zone_{main_zone}_H_V', [])

				if virtual_list:
					new_msg = f"{tl.t('Active– zone')} {main_zone}"
					new_n = 1
				else:
					new_msg = tl.t("Not active")
					new_n = 0
			else:
				new_msg = tl.t("Not active")
				new_n = 0

			old_s = Devices[86].sValue or ""

			if old_s.strip() != new_msg.strip() or Devices[86].nValue != new_n:
				Devices[86].Update(
					nValue=new_n,
					sValue=new_msg,
					TimedOut=False
				)

			if Devices[22].sValue != "0":

				Domoticz.Debug('Cooling mode active | Hűtési üzemmód aktív')

				mode = Devices[22].sValue
				outlimit = float(Devices[252].sValue)      # Outdoor temperature threshold (cooling) | Külső hőmérsékleti határ (hűtés)
				dualdiff = float(Devices[3].sValue)       # Difference value (°C) | Különbség értéke (°C)
				hiszt = float(Devices[18].sValue)         # Hysteresis (°C) | Hiszterézis (°C)

				Domoticz.Debug('Cooling parameters | Hűtési paraméterek')
				Domoticz.Debug(f"  Mode = {mode} | Üzemmód = {mode}")
				Domoticz.Debug(f"  Outside temperature = {self.outtemp:.1f}°C | Külső hőmérséklet = {self.outtemp:.1f}°C")
				Domoticz.Debug(f"  Outside temperature limit = {outlimit:.1f}°C | Külső hőmérsékleti határ = {outlimit:.1f}°C")
				Domoticz.Debug(f"  Outside dew point = {self.outdewpoint:.1f}°C | Külső harmatpont = {self.outdewpoint:.1f}°C")
				Domoticz.Debug(f"  Average indoor temperature = {self.intemp_avg:.1f} | Átlagos belső hőmérséklet = {self.intemp_avg:.1f}")
				Domoticz.Debug(f"  Dual cooling setpoint = {self.DualHsetpoint:.1f} | Dual hűtési célhőmérséklet = {self.DualHsetpoint:.1f}")
				Domoticz.Debug(f"  Hysteresis = {hiszt:.1f} | Hiszterézis = {hiszt:.1f}")
				Domoticz.Debug(f"  Operation = {self.operation} | Működési állapot = {self.operation}")

				# 10: Primary cooling mode | 10: Elsődleges hűtés mód
				if mode == "10":
					Domoticz.Debug("Primary cooling mode! | Elsődleges hűtés mód!")
					if self.operation:
						self.switchElsodleges_H(True)
					else:
						self.switchElsodleges_H(False)
					self.switchMasodlagos_H(False)

				# 20: Secondary cooling mode | 20: Másodlagos hűtés mód
				elif mode == "20":
					Domoticz.Debug("Secondary cooling mode! | Másodlagos hűtés mód!")
					self.switchElsodleges_H(False)
					if self.operation:
						self.switchMasodlagos_H(True)
					else:
						self.switchMasodlagos_H(False)

				# 30: Switching mode (based on indoor temperature) | 30: Váltó mód (belső hőmérséklet alapján)
				elif mode == "30":
					Domoticz.Debug('Switching mode (based on indoor temperature, with hysteresis) | Váltó mód (belső hőmérséklet alapján, hiszterézissel)')

					upper = self.DualHsetpoint + (dualdiff + hiszt)
					lower = self.DualHsetpoint + (dualdiff - hiszt)

					# Very warm: secondary cooling (2) | Nagyon meleg van: másodlagos hűtés (2)
					if self.intemp_avg > upper:
						Domoticz.Debug(f"Average indoor temperature {self.intemp_avg:.1f} exceeds upper limit {upper:.1f}: secondary cooling | Belső átlaghőmérséklet {self.intemp_avg:.1f} meghaladja a felső határt ({upper:.1f}): másodlagos hűtés")
						self.H_last_mode_state = 1

					# Cool enough: primary cooling (1) | Elég hűvös van: elsődleges hűtés (1)
					elif self.intemp_avg < lower:
						Domoticz.Debug(("Average indoor temperature difference below lower threshold: primary cooling | " + (f"diff {self.intemp_avg:.1f} < lower {lower:.1f} → Elsődleges hűtés")))
						self.H_last_mode_state = 0

					# Hysteresis band: no switching | Hiszterézistartomány: nincs váltás
					else:
						Domoticz.Debug(
							("Within hysteresis band: retain cooling mode | " + (f"Hiszterézis tartomány ({lower:.1f}–{upper:.1f}) "
							f"→ mód tartása: {self.H_last_mode_state}"))
						)

					# Execution | --- VÉGREHAJTÁS ---
					if self.H_last_mode_state == 0:
						if self.operation:
							self.switchElsodleges_H(True)
						else:
							self.switchElsodleges_H(False)
						self.switchMasodlagos_H(False)

					else:
						self.switchElsodleges_H(False)
						if self.operation:
							self.switchMasodlagos_H(True)
						else:
							self.switchMasodlagos_H(False)


				# 40: Switching mode (based on outdoor temperature, with hysteresis) | 40: Váltó mód (külső hőmérséklet alapján, hiszterézissel)
				elif mode == "40":
					Domoticz.Debug('Switching mode (based on outdoor temperature, with hysteresis) | Váltó mód (külső hőmérséklet alapján, hiszterézissel)')

					# Hysteresis thresholds | Hiszterézishatárok
					lower = outlimit - hiszt	# Below: primary (cool outdoors) | Ez alatt: elsődleges (kint hűvös van)
					upper = outlimit + hiszt	# Above: secondary (warm outdoors) | Ez fölött: másodlagos (kint meleg van)

					Domoticz.Debug(
						f"DEBUG: outside temperature={self.outtemp:.1f}, lower threshold={lower:.1f}, upper threshold={upper:.1f} | DEBUG: külső hőmérséklet={self.outtemp:.1f}, alsó határ={lower:.1f}, felső határ={upper:.1f}"
					)

					# Decision logic with hysteresis | Döntési logika hiszterézissel

					# Too warm: switch to secondary cooling | Túl meleg van: váltás másodlagos hűtésre
					if self.outtemp > upper:
						Domoticz.Debug(
							("Outdoor temperature above upper threshold: secondary cooling | " + (f"{self.outtemp:.1f} > upper {upper:.1f} → Másodlagos hűtés"))
						)
						self.H_last_mode_state = 1

					# Too cool: switch to primary cooling | Túl hűvös van: váltás elsődleges hűtésre
					elif self.outtemp < lower:
						Domoticz.Debug(
							("Outdoor temperature below lower threshold: primary cooling | " + (f"{self.outtemp:.1f} < lower {lower:.1f} → Elsődleges hűtés"))
						)
						self.H_last_mode_state = 0

					# Hysteresis band: no switching | Hiszterézistartomány: nincs váltás
					else:
						Domoticz.Debug(
							("Outdoor temperature within hysteresis band: retain cooling mode | " + (f"Külső hőmérséklet hiszterézisben ({lower:.1f}–{upper:.1f}) → "
							f"tartjuk a módot: {self.H_last_mode_state}"))
						)

					# Execution | --- végrehajtás ---
					if self.H_last_mode_state == 0:
						if self.operation:
							self.switchElsodleges_H(True)
						else:
							self.switchElsodleges_H(False)
						self.switchMasodlagos_H(False)

					else:
						self.switchElsodleges_H(False)
						if self.operation:
							self.switchMasodlagos_H(True)
						else:
							self.switchMasodlagos_H(False)

				# 50: Dual mode (based on indoor temperature) | 50: Dual mód (belső hőmérséklet alapján)
				elif mode == "50":
					Domoticz.Debug('Dual mode (based on indoor temperature, with hysteresis) | Dual mód (belső hőmérséklet alapján, hiszterézissel)')

					# Hysteresis thresholds | Hiszterézishatárok
					upper = self.DualHsetpoint + (dualdiff + hiszt)
					lower = self.DualHsetpoint + (dualdiff - hiszt)

					Domoticz.Debug(
						f"Indoor temperature difference={self.intemp_avg:.1f}, lower threshold={lower:.1f}, upper threshold={upper:.1f} | Belső hőmérséklet-különbség={self.intemp_avg:.1f}, alsó határ={lower:.1f}, felső határ={upper:.1f}"
					)

					# Decision with hysteresis | Döntés hiszterézissel
					# Too warm: 1+2 | Túl meleg van: 1+2
					if self.intemp_avg > upper:
						Domoticz.Debug(
							("Temperature difference above upper threshold: primary and secondary cooling | " + (f"Diff {self.intemp_avg:.1f} > upper {upper:.1f} → Elsődleges + Másodlagos hűtés"))
						)
						self.H_last_mode_state = 1

					# Cool enough: only 1 | Elég hűvös van: csak 1
					elif self.intemp_avg < lower:
						Domoticz.Debug(
							("Temperature difference below lower threshold: primary cooling only | " + (f"Diff {self.intemp_avg:.1f} < lower {lower:.1f} → Csak elsődleges hűtés"))
						)
						self.H_last_mode_state = 0

					# Hysteresis band | Hiszterézistartomány
					else:
						Domoticz.Debug(
							("Within hysteresis band: retain previous mode | " + (f"Hiszterézis tartomány ({lower:.1f}–{upper:.1f}) → "
							f"előző mód tartása: {self.H_last_mode_state}"))
						)

					# Execution | --- végrehajtás ---
					if self.H_last_mode_state == 0:
						if self.operation:
							self.switchElsodleges_H(True)
						else:
							self.switchElsodleges_H(False)
						self.switchMasodlagos_H(False)

					else:
						if self.operation:
							self.switchElsodleges_H(True)
							self.switchMasodlagos_H(True)
						else:
							self.switchElsodleges_H(False)
							self.switchMasodlagos_H(False)

				# 60: Dual mode (based on outdoor temperature, with hysteresis) | 60: Dual mód (külső hőmérséklet alapján, hiszterézissel)
				elif mode == "60":
					Domoticz.Debug('Dual mode (based on outdoor temperature, with hysteresis) | Dual mód (külső hőmérséklet alapján, hiszterézissel)')

					# Hysteresis thresholds | Hiszterézishatárok
					lower = outlimit - hiszt	# Below: cool, only 1 | Ez alatt: hűvös van, csak 1
					upper = outlimit + hiszt	# Above: warm, 1+2 | Ez fölött: meleg van, 1+2

					Domoticz.Debug(
						f"DEBUG: outside temperature={self.outtemp:.1f}, lower threshold={lower:.1f}, upper threshold={upper:.1f} | DEBUG: külső hőmérséklet={self.outtemp:.1f}, alsó határ={lower:.1f}, felső határ={upper:.1f}"
					)

					# State-dependent decision logic with hysteresis | Állapotfüggő döntési logika hiszterézissel

					# If too warm: dual mode (1+2) | Ha túl meleg van: dual mód (1+2)
					if self.outtemp > upper:
						Domoticz.Debug(
							("Outdoor temperature above upper threshold: primary and secondary modes | " + (f"Kint melegebb ({self.outtemp:.1f} > {upper:.1f}) → Elsődleges + Másodlagos"))
						)
						self.H_last_mode_state = 1

					# If cool: primary only | Ha hűvös van: csak az elsődleges
					elif self.outtemp < lower:
						Domoticz.Debug(
							("Outdoor temperature below lower threshold: primary mode only | " + (f"Kint hűvösebb ({self.outtemp:.1f} < {lower:.1f}) → Csak elsődleges"))
						)
						self.H_last_mode_state = 0

					# Hysteresis band: no switching | Hiszterézissáv: nincs váltás
					else:
						Domoticz.Debug(
							("Outdoor temperature within hysteresis band: retain mode | " + (f"Külső hőmérséklet hiszterézisben ({lower:.1f}–{upper:.1f}) → "
							f"mód tartása: {self.H_last_mode_state}"))
						)

					# Execution | --- végrehajtás ---
					if self.H_last_mode_state == 0:
						# Primary only | Csak elsődleges
						if self.operation:
							self.switchElsodleges_H(True)
						else:
							self.switchElsodleges_H(False)
						self.switchMasodlagos_H(False)

					else:
						# Primary and secondary | Elsődleges és másodlagos
						if self.operation:
							self.switchElsodleges_H(True)
							self.switchMasodlagos_H(True)
						else:
							self.switchElsodleges_H(False)
							self.switchMasodlagos_H(False)

				# 70: Switching mode (based on 500 W energy, with hysteresis) | 70: Váltó mód (500W energetika alapján, hiszterézissel)
				elif mode == "70":
					Domoticz.Debug('Switching mode (500 W, percentage hysteresis) | Váltó mód (500 W, százalékos hiszterézis)')
					power = self.aktual_watt
					base = 500
					if self.H_last_mode_state == 0:
						power += base
					h = int(base * int(Devices[85].sValue) / 100)
					Domoticz.Debug(f"Power={power} W, base={base} W, hysteresis=±{h} W | Teljesítmény={power} W, alapérték={base} W, hiszterézis=±{h} W")

					if power >= base + h:
						self.H_last_mode_state = 0
					elif power <= base - h:
						self.H_last_mode_state = 1
					
					if self.H_last_mode_state == 0:
						if self.operation: 
							self.switchElsodleges_H(True)
						else: 
							self.switchElsodleges_H(False)
						self.switchMasodlagos_H(False)
					else:
						self.switchElsodleges_H(False)
						if self.operation: 
							self.switchMasodlagos_H(True)
						else: 
							self.switchMasodlagos_H(False)

				# 80: Switching mode (based on 1000 W energy, with hysteresis) | 80: Váltó mód (1000W energetika alapján, hiszterézissel)
				elif mode == "80":
					Domoticz.Debug('Switching mode (1000 W, percentage hysteresis) | Váltó mód (1000 W, százalékos hiszterézis)')
					power = self.aktual_watt
					base = 1000
					if self.H_last_mode_state == 0:
						power += base
					h = int(base * int(Devices[85].sValue) / 100)
					Domoticz.Debug(f"Power={power} W, base={base} W, hysteresis=±{h} W | Teljesítmény={power} W, alapérték={base} W, hiszterézis=±{h} W")

					if power >= base + h:
						self.H_last_mode_state = 0
					elif power <= base - h:
						self.H_last_mode_state = 1
					
					if self.H_last_mode_state == 0:
						if self.operation: 
							self.switchElsodleges_H(True)
						else: 
							self.switchElsodleges_H(False)
						self.switchMasodlagos_H(False)
					else:
						self.switchElsodleges_H(False)
						if self.operation: 
							self.switchMasodlagos_H(True)
						else: 
							self.switchMasodlagos_H(False)

				# 90: Switching mode (based on 1500 W energy, with hysteresis) | 90: Váltó mód (1500W energetika alapján, hiszterézissel)
				elif mode == "90":
					Domoticz.Debug('Switching mode (1500 W, percentage hysteresis) | Váltó mód (1500 W, százalékos hiszterézis)')
					power = self.aktual_watt
					base = 1500
					if self.H_last_mode_state == 0:
						power += base
					h = int(base * int(Devices[85].sValue) / 100)
					Domoticz.Debug(f"Power={power} W, base={base} W, hysteresis=±{h} W | Teljesítmény={power} W, alapérték={base} W, hiszterézis=±{h} W")

					if power >= base + h:
						self.H_last_mode_state = 0
					elif power <= base - h:
						self.H_last_mode_state = 1

					if self.H_last_mode_state == 0:
						if self.operation: 
							self.switchElsodleges_H(True)
						else: 
							self.switchElsodleges_H(False)
						self.switchMasodlagos_H(False)
					else:
						self.switchElsodleges_H(False)
						if self.operation: 
							self.switchMasodlagos_H(True)
						else: 
							self.switchMasodlagos_H(False)

				# 100: Switching mode (based on 2000 W energy, with hysteresis) | 100: Váltó mód (2000W energetika alapján, hiszterézissel)
				elif mode == "100":
					Domoticz.Debug('Switching mode (2000 W, percentage hysteresis) | Váltó mód (2000 W, százalékos hiszterézis)')
					power = self.aktual_watt
					base = 2000
					if self.H_last_mode_state == 0:
						power += base
					h = int(base * int(Devices[85].sValue) / 100)
					Domoticz.Debug(f"Power={power} W, base={base} W, hysteresis=±{h} W | Teljesítmény={power} W, alapérték={base} W, hiszterézis=±{h} W")

					if power >= base + h:
						self.H_last_mode_state = 0
					elif power <= base - h:
						self.H_last_mode_state = 1

					if self.H_last_mode_state == 0:
						if self.operation: 
							self.switchElsodleges_H(True)
						else: 
							self.switchElsodleges_H(False)
						self.switchMasodlagos_H(False)
					else:
						self.switchElsodleges_H(False)
						if self.operation: 
							self.switchMasodlagos_H(True)
						else: 
							self.switchMasodlagos_H(False)

				# 110: Switching mode (based on 3000 W energy, with hysteresis) | 110: Váltó mód (3000W energetika alapján, hiszterézissel)
				elif mode == "110":
					Domoticz.Debug('Switching mode (3000 W, percentage hysteresis) | Váltó mód (3000 W, százalékos hiszterézis)')
					power = self.aktual_watt
					base = 3000
					if self.H_last_mode_state == 0:
						power += base
					h = int(base * int(Devices[85].sValue) / 100)
					Domoticz.Debug(f"Power={power} W, base={base} W, hysteresis=±{h} W | Teljesítmény={power} W, alapérték={base} W, hiszterézis=±{h} W")

					if power >= base + h:
						self.H_last_mode_state = 0
					elif power <= base - h:
						self.H_last_mode_state = 1

					if self.H_last_mode_state == 0:
						if self.operation: 
							self.switchElsodleges_H(True)
						else: 
							self.switchElsodleges_H(False)
						self.switchMasodlagos_H(False)
					else:
						self.switchElsodleges_H(False)
						if self.operation: 
							self.switchMasodlagos_H(True)
						else: 
							self.switchMasodlagos_H(False)

				# 120: Switching mode (based on 4000 W energy, with hysteresis) | 120: Váltó mód (4000W energetika alapján, hiszterézissel)
				elif mode == "120":
					Domoticz.Debug('Switching mode (4000 W, percentage hysteresis) | Váltó mód (4000 W, százalékos hiszterézis)')
					power = self.aktual_watt
					base = 4000
					if self.H_last_mode_state == 0:
						power += base
					h = int(base * int(Devices[85].sValue) / 100)
					Domoticz.Debug(f"Power={power} W, base={base} W, hysteresis=±{h} W | Teljesítmény={power} W, alapérték={base} W, hiszterézis=±{h} W")

					if power >= base + h:
						self.H_last_mode_state = 0
					elif power <= base - h:
						self.H_last_mode_state = 1

					if self.H_last_mode_state == 0:
						if self.operation: 
							self.switchElsodleges_H(True)
						else: 
							self.switchElsodleges_H(False)
						self.switchMasodlagos_H(False)
					else:
						self.switchElsodleges_H(False)
						if self.operation: 
							self.switchMasodlagos_H(True)
						else: 
							self.switchMasodlagos_H(False)

				# 130: Switching mode (based on 5000 W energy, with hysteresis) | 130: Váltó mód (5000W energetika alapján, hiszterézissel)
				elif mode == "130":
					Domoticz.Debug('Switching mode (5000 W, percentage hysteresis) | Váltó mód (5000 W, százalékos hiszterézis)')
					power = self.aktual_watt
					base = 5000
					if self.H_last_mode_state == 0:
						power += base
					h = int(base * int(Devices[85].sValue) / 100)
					Domoticz.Debug(f"Power={power} W, base={base} W, hysteresis=±{h} W | Teljesítmény={power} W, alapérték={base} W, hiszterézis=±{h} W")

					if power >= base + h:
						self.H_last_mode_state = 0
					elif power <= base - h:
						self.H_last_mode_state = 1

					if self.H_last_mode_state == 0:
						if self.operation: 
							self.switchElsodleges_H(True)
						else: 
							self.switchElsodleges_H(False)
						self.switchMasodlagos_H(False)
					else:
						self.switchElsodleges_H(False)
						if self.operation: 
							self.switchMasodlagos_H(True)
						else: 
							self.switchMasodlagos_H(False)

				# 140: Dual mode (based on 500 W energy, with hysteresis) | 140: Dual mód (500W energetika alapján, hiszterézissel)
				elif mode == "140":
					Domoticz.Debug('Dual mode (500 W, percentage hysteresis) | Dual mód (500 W, százalékos hiszterézis)')
					power = self.aktual_watt
					base = 500
					if self.H_last_mode_state == 0:
						power += base
					h = int(base * int(Devices[85].sValue) / 100)
					Domoticz.Debug(f"Power={power} W, base={base} W, hysteresis=±{h} W | Teljesítmény={power} W, alapérték={base} W, hiszterézis=±{h} W")

					if power >= base + h:
						self.H_last_mode_state = 0
					elif power <= base - h:
						self.H_last_mode_state = 1

					if self.H_last_mode_state == 0:
						if self.operation:
							self.switchElsodleges_H(True)
							self.switchMasodlagos_H(True)
						else:
							self.switchElsodleges_H(False)
							self.switchMasodlagos_H(False)
					else:
						self.switchElsodleges_H(False)
						if self.operation: 
							self.switchMasodlagos_H(True)
						else: 
							self.switchMasodlagos_H(False)

				# 150: Dual mode (based on 1000 W energy, with hysteresis) | 150: Dual mód (1000W energetika alapján, hiszterézissel)
				elif mode == "150":
					Domoticz.Debug('Dual mode (1000 W, percentage hysteresis) | Dual mód (1000 W, százalékos hiszterézis)')
					power = self.aktual_watt
					base = 1000
					if self.H_last_mode_state == 0:
						power += base
					h = int(base * int(Devices[85].sValue) / 100)
					Domoticz.Debug(f"Power={power} W, base={base} W, hysteresis=±{h} W | Teljesítmény={power} W, alapérték={base} W, hiszterézis=±{h} W")

					if power >= base + h:
						self.H_last_mode_state = 0
					elif power <= base - h:
						self.H_last_mode_state = 1

					if self.H_last_mode_state == 0:
						if self.operation:
							self.switchElsodleges_H(True)
							self.switchMasodlagos_H(True)
						else:
							self.switchElsodleges_H(False)
							self.switchMasodlagos_H(False)
					else:
						self.switchElsodleges_H(False)
						if self.operation: 
							self.switchMasodlagos_H(True)
						else: 
							self.switchMasodlagos_H(False)

				# 160: Dual mode (based on 1500 W energy, with hysteresis) | 160: Dual mód (1500W energetika alapján, hiszterézissel)
				elif mode == "160":
					Domoticz.Debug('Dual mode (1500 W, percentage hysteresis) | Dual mód (1500 W, százalékos hiszterézis)')
					power = self.aktual_watt
					base = 1500
					if self.H_last_mode_state == 0:
						power += base
					h = int(base * int(Devices[85].sValue) / 100)
					Domoticz.Debug(f"Power={power} W, base={base} W, hysteresis=±{h} W | Teljesítmény={power} W, alapérték={base} W, hiszterézis=±{h} W")

					if power >= base + h:
						self.H_last_mode_state = 0
					elif power <= base - h:
						self.H_last_mode_state = 1

					if self.H_last_mode_state == 0:
						if self.operation:
							self.switchElsodleges_H(True)
							self.switchMasodlagos_H(True)
						else:
							self.switchElsodleges_H(False)
							self.switchMasodlagos_H(False)
					else:
						self.switchElsodleges_H(False)
						if self.operation: 
							self.switchMasodlagos_H(True)
						else: 
							self.switchMasodlagos_H(False)

				# 170: Dual mode (based on 2000 W energy, with hysteresis) | 170: Dual mód (2000W energetika alapján, hiszterézissel)
				elif mode == "170":
					Domoticz.Debug('Dual mode (2000 W, percentage hysteresis) | Dual mód (2000 W, százalékos hiszterézis)')
					power = self.aktual_watt
					base = 2000
					if self.H_last_mode_state == 0:
						power += base
					h = int(base * int(Devices[85].sValue) / 100)
					Domoticz.Debug(f"Power={power} W, base={base} W, hysteresis=±{h} W | Teljesítmény={power} W, alapérték={base} W, hiszterézis=±{h} W")

					if power >= base + h:
						self.H_last_mode_state = 0
					elif power <= base - h:
						self.H_last_mode_state = 1

					if self.H_last_mode_state == 0:
						if self.operation:
							self.switchElsodleges_H(True)
							self.switchMasodlagos_H(True)
						else:
							self.switchElsodleges_H(False)
							self.switchMasodlagos_H(False)
					else:
						self.switchElsodleges_H(False)
						if self.operation: 
							self.switchMasodlagos_H(True)
						else: 
							self.switchMasodlagos_H(False)

				# 180: Dual mode (based on 3000 W energy, with hysteresis) | 180: Dual mód (3000W energetika alapján, hiszterézissel)
				elif mode == "180":
					Domoticz.Debug('Dual mode (3000 W, percentage hysteresis) | Dual mód (3000 W, százalékos hiszterézis)')
					power = self.aktual_watt
					base = 3000
					if self.H_last_mode_state == 0:
						power += base
					h = int(base * int(Devices[85].sValue) / 100)
					Domoticz.Debug(f"Power={power} W, base={base} W, hysteresis=±{h} W | Teljesítmény={power} W, alapérték={base} W, hiszterézis=±{h} W")

					if power >= base + h:
						self.H_last_mode_state = 0
					elif power <= base - h:
						self.H_last_mode_state = 1

					if self.H_last_mode_state == 0:
						if self.operation:
							self.switchElsodleges_H(True)
							self.switchMasodlagos_H(True)
						else:
							self.switchElsodleges_H(False)
							self.switchMasodlagos_H(False)
					else:
						self.switchElsodleges_H(False)
						if self.operation: 
							self.switchMasodlagos_H(True)
						else: 
							self.switchMasodlagos_H(False)

				# 190: Dual mode (based on 4000 W energy, with hysteresis) | 190: Dual mód (4000W energetika alapján, hiszterézissel)
				elif mode == "190":
					Domoticz.Debug('Dual mode (4000 W, percentage hysteresis) | Dual mód (4000 W, százalékos hiszterézis)')
					power = self.aktual_watt
					base = 4000
					if self.H_last_mode_state == 0:
						power += base
					h = int(base * int(Devices[85].sValue) / 100)
					Domoticz.Debug(f"Power={power} W, base={base} W, hysteresis=±{h} W | Teljesítmény={power} W, alapérték={base} W, hiszterézis=±{h} W")

					if power >= base + h:
						self.H_last_mode_state = 0
					elif power <= base - h:
						self.H_last_mode_state = 1

					if self.H_last_mode_state == 0:
						if self.operation:
							self.switchElsodleges_H(True)
							self.switchMasodlagos_H(True)
						else:
							self.switchElsodleges_H(False)
							self.switchMasodlagos_H(False)
					else:
						self.switchElsodleges_H(False)
						if self.operation: 
							self.switchMasodlagos_H(True)
						else: 
							self.switchMasodlagos_H(False)

				# 200: Dual mode (based on 5000 W energy, with hysteresis) | 200: Dual mód (5000W energetika alapján, hiszterézissel)
				elif mode == "200":
					Domoticz.Debug('Dual mode (5000 W, percentage hysteresis) | Dual mód (5000 W, százalékos hiszterézis)')
					power = self.aktual_watt
					base = 5000
					if self.H_last_mode_state == 0:
						power += base
					h = int(base * int(Devices[85].sValue) / 100)
					Domoticz.Debug(f"Power={power} W, base={base} W, hysteresis=±{h} W | Teljesítmény={power} W, alapérték={base} W, hiszterézis=±{h} W")

					if power >= base + h:
						self.H_last_mode_state = 0
					elif power <= base - h:
						self.H_last_mode_state = 1

					if self.H_last_mode_state == 0:
						if self.operation:
							self.switchElsodleges_H(True)
							self.switchMasodlagos_H(True)
						else:
							self.switchElsodleges_H(False)
							self.switchMasodlagos_H(False)
					else:
						self.switchElsodleges_H(False)
						if self.operation: 
							self.switchMasodlagos_H(True)
						else: 
							self.switchMasodlagos_H(False)

				else:
					Domoticz.Debug('Unknown operating mode; everything switched off | Ismeretlen üzemmód, minden kikapcsolva')
					self.switchElsodleges_H(False)
					self.switchMasodlagos_H(False)

			else:
				Domoticz.Debug('Cooling not running: no CoolDevices configured | Nem működik a hűtés: nincs CoolDevices beállítva')
				self.switchElsodleges_H(False)
				self.switchMasodlagos_H(False)


	def switchElsodleges_M(self, switch):

		command = "On" if switch else "Off"

		level = int(Devices[65].sValue)

		check = False

		if level in [10, 20, 30, 40, 50]:
			check = self.switchElsodleges_F or self.switchElsodleges_H

		elif level in [60, 70, 80, 90, 100]:
			check = self.switchElsodleges_P

		elif level in [110, 120, 130, 140, 150]:
			check = self.switchElsodleges_F or self.switchElsodleges_H or self.switchElsodleges_P


		if command == "On" and not self.dhw_time_run and check:
			Domoticz.Debug('OFF due to DHW priority | HMV-prioritás miatt kikapcsolva')
			command = "Off"

		if command == "On" :
			Domoticz.Debug('Primary mixing valve switch: ON | Elsődleges keverőszelep-kapcsoló: Be')
			self.Elsodleges_M_On = True
		else :
			Domoticz.Debug('Primary mixing valve switch: OFF | Elsődleges keverőszelep-kapcsoló: Ki')
			self.Elsodleges_M_On = False
		
		Domoticz.Debug("Primary M switching: {0} | Elsődleges M kapcsolás: {0}".format(command))

		for idx in self.Elsodleges_M:
			self.switchappend(idx,command)

		self.switchstatus(int(Devices[24].ID),command)


	def switchMasodlagos_M(self, switch):

		command = "On" if switch else "Off"

		level = int(Devices[65].sValue)

		check = False

		if level in [10, 20, 30, 40, 50]:
			# Heating–cooling: F or H | Fűtés–hűtés: F vagy H
			check = self.switchMasodlagos_F or self.switchMasodlagos_H

		elif level in [60, 70, 80, 90, 100]:
			# Buffer: P | Puffer: P
			check = self.switchMasodlagos_P

		elif level in [110, 120, 130, 140, 150]:
			# Heating–cooling plus buffer: F, H or P | Fűtés–hűtés és puffer: F, H vagy P
			check = self.switchMasodlagos_F or self.switchMasodlagos_H or self.switchMasodlagos_P

		if command == "On" and not self.dhw_time_run and check:
			Domoticz.Debug('Secondary switch OFF due to DHW priority | Másodlagos kapcsoló kikapcsolva HMV-prioritás miatt')
			command = "Off"

		if command == "On" :
			self.Masodlagos_M_On = True
		else :
			self.Masodlagos_M_On = False

		Domoticz.Debug("Secondary M switching: {0} | Másodlagos M kapcsolás: {0}".format(command))

		for idx in self.Masodlagos_M:
			self.switchappend(idx,command)
		
		self.switchstatus(int(Devices[27].ID),command)


	def switchElsodleges_F(self, switch):

		command = "On" if switch else "Off"

		if self.dhwprior_F_H and self.Elsodleges_M_On :
			Domoticz.Debug('Primary_F OFF due to DHW priority | Elsodleges_F kikapcsolva HMV-prioritás miatt')
			command = "Off"

		Domoticz.Debug("Primary F switching: {0} | Elsődleges F kapcsolás: {0}".format(command))

		for idx in self.Elsodleges_F:
			self.switchappend(idx,command)

		if command == "On" :
			self.f1works = True
		else :
			self.f1works = False

		self.switchstatus(Devices[23].ID,command)


	def switchMasodlagos_F(self, switch):

		command = "On" if switch else "Off"

		if self.dhwprior_F_H and self.Masodlagos_M_On :
			Domoticz.Debug('Secondary_F OFF due to DHW priority | Masodlagos_F kikapcsolva HMV-prioritás miatt')
			command = "Off"

		
		Domoticz.Debug("Secondary F switching: {0} | Másodlagos F kapcsolás: {0}".format(command))

		for idx in self.Masodlagos_F:
			self.switchappend(idx,command)

		if command == "On" :
			self.f2works = True
		else :
			self.f2works = False

		self.switchstatus(int(Devices[26].ID),command)


	def switchElsodleges_P_F(self, switch):

		command = "On" if switch else "Off"

		if self.dhwprior_P and self.Elsodleges_M_On :
			Domoticz.Debug('Primary_P OFF due to DHW priority | Elsodleges_P kikapcsolva HMV-prioritás miatt')
			command = "Off"
		
		Domoticz.Debug("Primary P_F switching: {0} | Elsődleges P_F kapcsolás: {0}".format(command))

		for idx in self.Elsodleges_P_F:
			self.switchappend(idx,command)

		if command == "On" :
			self.pworks = True
		else :
			self.pworks = False

		self.switchstatus(int(Devices[102].ID),command)

	def switchElsodleges_P_H(self, switch):

		command = "On" if switch else "Off"

		if self.dhwprior_P and self.Elsodleges_M_On :
			Domoticz.Debug('Primary_P_H OFF due to DHW priority | Elsodleges_P_H kikapcsolva HMV-prioritás miatt')
			command = "Off"
		
		Domoticz.Debug("Primary P_H switching: {0} | Elsődleges P_H kapcsolás: {0}".format(command))

		for idx in self.Elsodleges_P_H:
			self.switchappend(idx,command)

		if command == "On" :
			self.pworks = True
		else :
			self.pworks = False

		self.switchstatus(int(Devices[102].ID),command)


	def switchMasodlagos_P_F(self, switch):

		command = "On" if switch else "Off"

		if self.dhwprior_P and self.Masodlagos_M_On :
			Domoticz.Debug('Secondary_P_F OFF due to DHW priority | Masodlagos_P_F kikapcsolva HMV-prioritás miatt')
			command = "Off"
		
		Domoticz.Debug("Secondary P_F switching: {0} | Másodlagos P_F kapcsolás: {0}".format(command))

		for idx in self.Masodlagos_P_F:
			self.switchappend(idx,command)

		if command == "On" :
			self.pworks = True
		else :
			self.pworks = False

		self.switchstatus(int(Devices[103].ID),command)

	def switchMasodlagos_P_H(self, switch):

		command = "On" if switch else "Off"

		if self.dhwprior_P and self.Masodlagos_M_On :
			Domoticz.Debug('Secondary_P_H OFF due to DHW priority | Masodlagos_P_H kikapcsolva HMV-prioritás miatt')
			command = "Off"
		
		Domoticz.Debug("Secondary P_H switching: {0} | Másodlagos P_H kapcsolás: {0}".format(command))

		for idx in self.Masodlagos_P_H:
			self.switchappend(idx,command)

		if command == "On" :
			self.pworks = True
		else :
			self.pworks = False

		self.switchstatus(int(Devices[103].ID),command)


	def switchElsodleges_PE(self, switch):

		command = "On" if switch else "Off"

		Domoticz.Debug("Primary PE switching: {0} | Elsődleges PE kapcsolás: {0}".format(command))

		for idx in self.Elsodleges_PE:
			self.switchappend(idx,command)

		self.switchstatus(int(Devices[160].ID),command)



	def switchMasodlagos_PE(self, switch):

		command = "On" if switch else "Off"

		Domoticz.Debug("Secondary PE switching: {0} | Másodlagos PE kapcsolás: {0}".format(command))

		for idx in self.Masodlagos_PE:
			self.switchappend(idx,command)

		self.switchstatus(int(Devices[27].ID),command)

	def switchElsodleges_E(self, switch):

		command = "On" if switch else "Off"

		Domoticz.Debug("Primary E switching: {0} | Elsődleges E kapcsolás: {0}".format(command))

		for idx in self.Elsodleges_E:
			self.switchappend(idx,command)

		self.switchstatus(int(Devices[33].ID),command)


	def switchMasodlagos_E(self, switch):

		command = "On" if switch else "Off"

		Domoticz.Debug("Secondary E switching: {0} | Másodlagos E kapcsolás: {0}".format(command))

		for idx in self.Masodlagos_E:
			self.switchappend(idx,command)

		self.switchstatus(int(Devices[34].ID),command)


	def switchElsodleges_H(self, switch):

		command = "On" if switch else "Off"

		if self.dhwprior_F_H and self.Elsodleges_M_On :
			Domoticz.Debug('Primary_H OFF due to DHW priority | Elsodleges_H kikapcsolva HMV-prioritás miatt')
			command = "Off"

		Domoticz.Debug("Primary H switching: {0} | Elsődleges H kapcsolás: {0}".format(command))

		for idx in self.Elsodleges_H:
			self.switchappend(idx,command)

		if command == "On" :
			self.h1works = True
		else :
			self.h1works = False

		self.switchstatus(int(Devices[25].ID),command)

	def switchMasodlagos_H(self, switch):

		command = "On" if switch else "Off"

		if self.dhwprior_F_H and self.Masodlagos_M_On :
			Domoticz.Debug('Secondary_H OFF due to DHW priority | Masodlagos_H kikapcsolva HMV-prioritás miatt')
			command = "Off"

		Domoticz.Debug("Secondary H switching: {0} | Másodlagos H kapcsolás: {0}".format(command))

		for idx in self.Masodlagos_H:
			self.switchappend(idx,command)

		self.switchstatus(int(Devices[28].ID),command)


	def switch_kevero_1_plusz(self, switch):

		command = "On" if switch else "Off"

		Domoticz.Debug("Increase mixing valve 1: {0} | Keverőszelep 1 növelése (switch_kevero_1_plusz): {0}".format(command))

		for idx in self.Keveroszelep_1_plusz:
			self.switchappend(idx,command)

	def switch_kevero_1_minusz(self, switch):

		command = "On" if switch else "Off"

		Domoticz.Debug("Decrease mixing valve 1: {0} | Keverőszelep 1 csökkentése (switch_kevero_1_minusz): {0}".format(command))

		for idx in self.Keveroszelep_1_minusz:
			self.switchappend(idx,command)

	def switch_kevero_2_plusz(self, switch):

		command = "On" if switch else "Off"

		Domoticz.Debug("Increase mixing valve 2: {0} | Keverőszelep 2 növelése (switch_kevero_2_plusz): {0}".format(command))

		for idx in self.Keveroszelep_2_plusz:
			self.switchappend(idx,command)

	def switch_kevero_2_minusz(self, switch):

		command = "On" if switch else "Off"

		Domoticz.Debug("Decrease mixing valve 2: {0} | Keverőszelep 2 csökkentése (switch_kevero_2_minusz): {0}".format(command))

		for idx in self.Keveroszelep_2_minusz:
			self.switchappend(idx,command)

	def switch_szoba_on(self, switch):

		command = "On" if switch else "Off"

		self.switchstatus(int(Devices[68].ID),command)

		Domoticz.Debug("Switch room on: {0} | Szoba bekapcsolása (switch_szoba_on): {0}".format(command))

		for idx in self.szoba_on:
			self.switchappend(idx,command)

	def switchzone_F(self, zone: int, switch: bool):

		if getattr(self, f'Zone_TempSensors_{zone}'):
			command = "On" if switch else "Off"
			Domoticz.Debug(f"Heating zone switch: switchzone_{zone}_F '{command}' | Fűtési zóna kapcsolása: switchzone_{zone}_F '{command}'")

			# Store the heating zone state | Fűtési zóna állapotának eltárolása
			setattr(self, f'zone_{zone}_heating_state', switch)

			for idx in getattr(self, f'Zone_{zone}_F'):
				self.switchappend(idx, command)



	def switchzone_H(self, zone: int, switch: bool):

		if getattr(self, f'Zone_TempSensors_{zone}'):
			command = "On" if switch else "Off"
			Domoticz.Debug(f"Cooling zone switch: switchzone_{zone}_H '{command}' | Hűtési zóna kapcsolása: switchzone_{zone}_H '{command}'")

			# Store the cooling zone state | Hűtési zóna állapotának eltárolása
			setattr(self, f'zone_{zone}_cooling_state', switch)

			for idx in getattr(self, f'Zone_{zone}_H'):
				self.switchappend(idx, command)

	def frost_protection(self):

		# Frost protection | Fagyvédelem
		if not self.FrostTempSensors or not self.FrostSwitches:
			return

		# No valid temperature | Nincs érvényes hőmérséklet
		if self.FrostTemp is None:
			return

		limit = self.FrostLimit
		hysteresis = max(0.0, self.FrostHysteresis)

		# Hysteresis control | Hiszterézises szabályozás
		if self.FrostTemp <= limit:
			self.FrostActive = True
		elif self.FrostTemp >= limit + hysteresis:
			self.FrostActive = False

		# Add switch requests | Kapcsolási igények hozzáadása
		command = "On" if self.FrostActive else "Off"

		for idx in self.FrostSwitches:
			self.switchappend(idx, command)

		Domoticz.Debug(
			f"Frost protection: temp={self.FrostTemp:.1f}°C, "
			f"limit={limit:.1f}°C, hysteresis={hysteresis:.1f}°C, "
			f"command={command} | "
			f"Fagyvédelem: hőmérséklet={self.FrostTemp:.1f}°C, "
			f"határ={limit:.1f}°C, hiszterézis={hysteresis:.1f}°C, "
			f"parancs={command}"
		)

	def pump_protection(self):

		# Periodic pump protection | Időszakos szivattyúvédelem
		if not self.PumpProtectionSwitches:
			return

		if self.PumpProtectionDay is None or self.PumpProtectionHour is None or self.PumpProtectionMinutes is None:
			return

		now = datetime.now()
		now_ts = now.timestamp()

		# Calculate scheduled start for the current week | Az aktuális heti tervezett indítás kiszámítása
		start_date = (now - timedelta(days=now.weekday())).date() + timedelta(days=self.PumpProtectionDay)
		start = datetime.combine(start_date, datetime.min.time()).replace(hour=self.PumpProtectionHour).timestamp()

		# Read saved run expiry timestamp | Mentett járatási lejárat beolvasása
		run = float(self.Internals.get("pump_protection_run", 0) or 0)

		# Start once within the one-hour window | Egyszeri indítás az egyórás időablakban
		if start <= now_ts < start + 3600 and run < start:

			run = now_ts + self.PumpProtectionMinutes * 60

			self.Internals["pump_protection_run"] = run
			saveUserVar(self)

			Domoticz.Log(
				f"Pump protection started: duration={self.PumpProtectionMinutes} min | "
				f"Szivattyúvédelem elindult: időtartam={self.PumpProtectionMinutes} perc"
			)

		# Determine switch command | Kapcsolási parancs meghatározása
		command = "On" if start <= run and now_ts < run else "Off"

		# Append switch commands with ON priority | Kapcsolási parancsok hozzáadása ON prioritással
		for idx in self.PumpProtectionSwitches:
			self.switchappend(idx, command)

		#Domoticz.Debug(f"Pump protection: command={command}, run={run}, now={now_ts} | " f"Szivattyúvédelem: parancs={command}, lejárat={run}, most={now_ts}")

	def switchappend(self,idx,command):

		notInList = True
		for switch in self.switchcreated:
			if switch.idx == idx:
				Domoticz.Debug("Switch already in list: idx={0}, command={1} | Kapcsoló már szerepel a listában: idx={0}, parancs={1}".format(idx, command))
				if command == "On":
					Domoticz.Debug(("Override current switch command %s with requested command %s | Jelenlegi kapcsolási parancs %s felülírása a kért %s paranccsal" % (switch.command, command, switch.command, command)))
					switch.command = command

				notInList = False
				break
		if notInList:
			Domoticz.Debug("Switch not in list, adding: idx={0}, command={1} | Kapcsoló még nincs a listában, hozzáadás: idx={0}, parancs={1}".format(idx, command))
			self.switchcreated.append(switchparam(idx, command))

	def get_delay_for_idx(self, idx, command):
		# Command: "On" or "Off" | Parancs: "On" vagy "Off"
		delay = 0

		Domoticz.Debug(
			f"Delayed switch started: idx={idx}, command={command} | Késleltetett kapcsolás indítása: idx={idx}, parancs={command}"
		)

		# -------------------------
		# ON: BEFORE delay | BEKAPCSOLÁS: BEFORE késleltetés
		# -------------------------
		if command == "On":
			Domoticz.Debug('Delay mode → before (On) | Késleltetett mód → előtte (bekapcsolt állapot)')

			if idx in self.before_switch_1:
				Domoticz.Debug(
					f"Device idx {idx}: first pre-switch delay, time={self.before_switch_1_time} | Eszköz idx {idx}: első kapcsolás előtti késleltetés, idő={self.before_switch_1_time}"
				)
				delay = self.before_switch_1_time

			if idx in self.before_switch_2:
				Domoticz.Debug(
					f"Device idx {idx}: second pre-switch delay, time={self.before_switch_2_time} | Eszköz idx {idx}: második kapcsolás előtti késleltetés, idő={self.before_switch_2_time}"
				)
				delay = self.before_switch_2_time

		# -------------------------
		# OFF: AFTER delay | KIKAPCSOLÁS: AFTER késleltetés
		# -------------------------
		elif command == "Off":
			Domoticz.Debug('Delay mode: AFTER (Off) | Késleltetési mód: utókapcsolás (Ki)')

			if idx in self.after_switch_1:
				Domoticz.Debug(
					f"Device idx {idx}: first post-switch delay, time={self.after_switch_1_time} | Eszköz idx {idx}: első kapcsolás utáni késleltetés, idő={self.after_switch_1_time}"
				)
				delay = self.after_switch_1_time

			if idx in self.after_switch_2:
				Domoticz.Debug(
					f"Device idx {idx}: second post-switch delay, time={self.after_switch_2_time} | Eszköz idx {idx}: második kapcsolás utáni késleltetés, idő={self.after_switch_2_time}"
				)
				delay = self.after_switch_2_time

		Domoticz.Debug(
			f"Delayed switch result: idx={idx}, command={command}, delay={delay} | Késleltetett kapcsolás eredménye: idx={idx}, parancs={command}, késleltetés={delay}"
		)

		return delay


	def delayed_switch(self, idx, command, delay):
		now = time.time()
		execute_time = now + delay

		# Overwrite existing delay (the new command takes precedence) | Ha volt korábbi késleltetés, felülírjuk (az új parancs az érvényes)
		self.delayedActions[idx] = {
			"command": command,
			"time": execute_time
		}

		Domoticz.Debug(f"Delayed switching scheduled: idx={idx}, command={command}, delay={delay}s, execute_time={execute_time} | Késleltetett kapcsolás beállítva: idx={idx}, parancs={command}, késleltetés={delay}s, végrehajtás={execute_time}")


	def switchcommand(self):

		devicesAPI = DomoticzAPI(
			"type=devices&filter=light&order=Name"
			if float(Parameters["DomoticzVersion"]) <= 2023.1
			else "type=command&param=getdevices&filter=light&order=Name"
		)

		for switch in self.switchcreated:
			for device in devicesAPI["result"]:

				deviceidx = int(device["idx"])
				if deviceidx != switch.idx:
					continue

				current_state = device["Status"]      # Domoticz state | Domoticz állapota
				desired_state = switch.command         # State requested by plugin | A plugin által kért állapot

				Domoticz.Debug("Switch {0} current state: {1} → requested state: {2} | Kapcsoló {0} jelen állapota: {1} → kívánt állapot: {2}".format(
					switch.idx, current_state, desired_state))

				# ------------------------------------------------------------------
				# 1) Do not touch a switch while its delay is pending | 1) Ha a kapcsoló késleltetés alatt áll, nem szabad módosítani
				# ------------------------------------------------------------------
				if switch.idx in self.delayedActions:
					Domoticz.Debug(f"Switch {switch.idx} is in delay period: no switching now | Kapcsoló {switch.idx} késleltetési időszakban van: most nincs kapcsolás")
					# But if the requested command equals current state, cancel the delay | Ha azonban a parancs már egyezik a jelenlegi állapottal, töröljük a késleltetést
					if current_state == desired_state:
						Domoticz.Debug(f"Switch {switch.idx}: current state matches requested state, cancelling delay | Kapcsoló {switch.idx}: a jelenlegi állapot megegyezik a kérttel, késleltetés törlése")
						del self.delayedActions[switch.idx]
					continue

				# ------------------------------------------------------------------
				# 2) If already in the desired state, no switching is needed | 2) Ha már a kívánt állapotban van, nincs szükség kapcsolásra
				# ------------------------------------------------------------------
				if current_state == desired_state:
					Domoticz.Debug("No switching required | Nincs szükség kapcsolásra")

					# Cancel any pending delay if one still exists | Ha mégis maradt függőben lévő késleltetés, törölni kell
					if switch.idx in self.delayedActions:
						Domoticz.Debug(f"Switch {switch.idx}: pending delay cancelled (state already correct) | Kapcsoló {switch.idx}: függőben lévő késleltetés törölve (az állapot már megfelelő)")
						del self.delayedActions[switch.idx]

					continue

				# ------------------------------------------------------------------
				# 3) A real ON/OFF action is required at this point | 3) Ezen a ponton tényleges ON/OFF műveletre van szükség
				# First calculate the delay | Előbb ki kell számítani a késleltetést
				# ------------------------------------------------------------------

				Domoticz.Debug(
					f"SWITCH ACTION: idx={switch.idx}, desired_state={desired_state}, before1_time={self.before_switch_1_time}, before2_time={self.before_switch_2_time}, after1_time={self.after_switch_1_time}, after2_time={self.after_switch_2_time} | KAPCSOLÁSI MŰVELET: idx={switch.idx}, kívánt állapot={desired_state}, első előzetes késleltetés={self.before_switch_1_time}, második előzetes késleltetés={self.before_switch_2_time}, első utólagos késleltetés={self.after_switch_1_time}, második utólagos késleltetés={self.after_switch_2_time}"
				)

				delay = self.get_delay_for_idx(switch.idx, desired_state)

				Domoticz.Debug(
					f"Switch delay result: idx={switch.idx}, state={desired_state}, delay={delay}s | Kapcsolási késleltetés eredménye: idx={switch.idx}, állapot={desired_state}, késleltetés={delay}s"
				)


				# If a delay is configured, switch after the delay | Ha van késleltetés, késleltetett kapcsolás történik
				if delay > 0:
					Domoticz.Debug(f"Delayed switching required: idx={switch.idx}, delay={delay}s | Késleltetett kapcsolás szükséges: idx={switch.idx}, késleltetés={delay}s")
					self.delayed_switch(switch.idx, desired_state, delay)
					continue

				# ------------------------------------------------------------------
				# 4) If there is no delay, switch IMMEDIATELY | 4) Ha nincs késleltetés, AZONNALI kapcsolás történik
				# ------------------------------------------------------------------
				Domoticz.Debug(f"Immediate switch: idx={switch.idx} → {desired_state} | Azonnali kapcsolás: idx={switch.idx} → {desired_state}")
				DomoticzAPI("type=command&param=switchlight&idx={}&switchcmd={}".format(
					switch.idx, desired_state))


	def switchstatus(self,idx,command):
		notInList = True
		for statusflag in self.statuscreated:
			if statusflag.idx == idx:
				Domoticz.Debug("Status already in list: idx={0}, command={1} | Az állapot már szerepel a listában: idx={0}, parancs={1}".format(idx, command))
				if command == "On":
					Domoticz.Debug(("Override the current status-flag command with the requested command | " + ("%s az érték felül kell írni a %s értékkel" % (statusflag.command, command))))
					statusflag.command = command
				else:
					Domoticz.Debug(("Keep the existing value | " + ("Marad a %s érték" % command)))
				notInList = False
				break
		if notInList:
			Domoticz.Debug("Status not in list, adding: idx={0}, command={1} | Az állapot még nem szerepel a listában, hozzáadás: idx={0}, parancs={1}".format(idx, command))
			self.statuscreated.append(switchparam(idx, command))

	def switchzone(self, zoneidx):

		devicesAPI = DomoticzAPI(
			"type=devices&filter=light&order=Name" 
			if float(Parameters["DomoticzVersion"]) <= 2023.1 
			else "type=command&param=getdevices&filter=light&order=Name"
		)
		if devicesAPI:
			for device in devicesAPI["result"]:  # Inspect switch devices | A kapcsolóeszközök elemzése
				idx = int(device["idx"])
				if idx == zoneidx :  # This is the switch | Ez a kapcsoló
					DomoticzAPI("type=command&param=switchlight&idx={}&switchcmd=On".format(idx))
					Domoticz.Debug('Zone switching time: {0} | Zónakapcsolás időpontja: {0}'.format(datetime.now()))


	def statuscommand(self):
		devicesAPI = DomoticzAPI(
			"type=devices&filter=light&order=Name" 
			if float(Parameters["DomoticzVersion"]) <= 2023.1 
			else "type=command&param=getdevices&filter=light&order=Name"
		)
		if devicesAPI:
			for statusflag in self.statuscreated:
				# Read the current status and compare it with the desired state | A status aktuális állapotának megállapítása és összevetése a kívánt állapottal
				for device in devicesAPI["result"]:  # Inspect the switch device | A kapcsolóeszköz elemzése
					deviceidx = int(device["idx"])
					if deviceidx == statusflag.idx:  # This is the target switch | Ez a keresett kapcsoló
						Domoticz.Debug("Status: idx={0}, value={1} | Állapot: idx={0}, érték={1}".format(statusflag.idx, device["Status"]))
						if device["Status"] != format(statusflag.command) :
							Domoticz.Debug('Status change required | Állapotváltás szükséges')
							if format(statusflag.command) == "On":
								nValue = 1
							else :
								nValue = 0

							self.UpdateDevice(device["Unit"],nValue,statusflag.command)
						else: 
							Domoticz.Debug('No status change required | Nincs szükség állapotváltásra')

	def update_setpoint_pluss(self, zone: int):
		
		if not self.AktualThermostat or "result" not in self.AktualThermostat:
			return

		# Run only if the zone has a thermometer | Csak akkor fut, ha az adott zónához tartozik hőmérő
		zone_sensors = getattr(self, f"Zone_TempSensors_{zone}", None)
		if not zone_sensors:
			Domoticz.Debug(f"[Z{zone}] No temperature sensor ( | Nincs hőmérő (Zone_TempSensors_{zone}), kihagyva update_setpoint_pluss.")
			return

		zone_list = getattr(self, f"ZoneTRV_{zone}")
		ftargettemp_felso = getattr(self, f"ftargettemp_{zone}_felso")
		ftargettemp_also = getattr(self, f"ftargettemp_{zone}_also")
		ftargettemp = getattr(self, f"ftargettemp_{zone}")
		htargettemp_felso = getattr(self, f"htargettemp_{zone}_felso")
		htargettemp_also = getattr(self, f"htargettemp_{zone}_also")
		htargettemp = getattr(self, f"htargettemp_{zone}")
		aktual_temp = getattr(self, f"zone_{zone}_aktual_temp") or self.intemp

		for setpoint in self.AktualThermostat["result"]:
			setpointidx = int(setpoint["idx"])
			setpointID = str(setpoint["ID"])
			setpoint_value = setpoint["Data"]

			if setpointidx not in zone_list:
				continue

			try:
				setpoint_value_num = float(setpoint_value)
			except ValueError:
				if setpoint_value == 'On':
					setpoint_value_num = 1.0
				elif setpoint_value == 'Off':
					setpoint_value_num = 0.0
				else:
					Domoticz.Debug(("Cannot convert setpoint_value | " + (f"Nem konvertálható setpoint_value: {setpoint_value}")))
					setpoint_value_num = 0.0

			# Default: leave unchanged | Alapértelmezés: ne változzon
			setpoint_pluss = setpoint_value_num

			# If heating mode and dynamic control are active | Ha a fűtési mód és a dinamikus szabályozás aktív

			if Devices[58].sValue == "10" :

				trv_temp = self.get_trv_temp(setpointID)

				komp = round((ftargettemp_felso - aktual_temp) *2)

				if Devices[211].sValue == "20":

					if isinstance(trv_temp, (int, float)):
						if aktual_temp < trv_temp:
							diff = trv_temp - aktual_temp
							setpoint_pluss = ftargettemp_felso + diff + komp
						else:
							setpoint_pluss = ftargettemp_felso + komp
					else:
						setpoint_pluss = ftargettemp_felso + komp
				else:
					setpoint_pluss = ftargettemp_felso + komp

				setpoint_pluss = round(setpoint_pluss * 2) / 2
				setpoint_pluss = max(ftargettemp_felso - 5, min(setpoint_pluss, ftargettemp_felso + 5))
			
			elif Devices[58].sValue == "20" :

				trv_temp = self.get_trv_temp(setpointID)

				komp = round((aktual_temp - htargettemp_also) * 2)

				if Devices[211].sValue == "30":

					if isinstance(trv_temp, (int, float)):
						if aktual_temp < trv_temp:
							diff = trv_temp - aktual_temp
							setpoint_pluss = htargettemp_felso + diff + komp
						else:
							setpoint_pluss = htargettemp_felso + komp
					else:
						setpoint_pluss = htargettemp_felso + komp
				else:
					komp = round((ftargettemp_felso - aktual_temp) *2)

					setpoint_pluss = ftargettemp_felso + komp

			setpoint_pluss = max(setpoint_pluss, 30.0)
			setpoint_pluss = round(setpoint_pluss, 1)

			if setpoint_pluss != setpoint_value_num :
				update_url = f"type=command&param=udevice&idx={setpointidx}&nvalue=0&svalue={setpoint_pluss}"
				DomoticzAPI(update_url)
				Domoticz.Debug(f"Setpoint increase URL: {update_url} | Célhőmérséklet-növelés URL-je ={update_url}")
				Domoticz.Debug(f"Increase setpoint: idx={setpointidx}, setpoint={setpoint_pluss} | Célhőmérséklet növelése: idx={setpointidx}, célérték={setpoint_pluss}")


	def update_setpoint_minusz(self, zone: int):

		if not self.AktualThermostat or "result" not in self.AktualThermostat:
			return

		# Run only if the zone has a thermometer | Csak akkor fut, ha az adott zónához tartozik hőmérő
		zone_sensors = getattr(self, f"Zone_TempSensors_{zone}", None)
		if not zone_sensors:
			Domoticz.Debug(f"[Z{zone}] No temperature sensor ( | Nincs hőmérő (Zone_TempSensors_{zone}), kihagyva update_setpoint_minusz.")
			return

		zone_list = getattr(self, f"ZoneTRV_{zone}")
		ftargettemp_felso = getattr(self, f"ftargettemp_{zone}_felso")
		ftargettemp_also = getattr(self, f"ftargettemp_{zone}_also")
		ftargettemp = getattr(self, f"ftargettemp_{zone}")
		htargettemp_felso = getattr(self, f"htargettemp_{zone}_felso")
		htargettemp_also = getattr(self, f"htargettemp_{zone}_also")
		htargettemp = getattr(self, f"htargettemp_{zone}")
		aktual_temp = getattr(self, f"zone_{zone}_aktual_temp") or self.intemp

		for setpoint in self.AktualThermostat["result"]:
			setpointidx = int(setpoint["idx"])
			setpointID = str(setpoint["ID"])
			setpoint_value = setpoint["Data"]

			if setpointidx not in zone_list:
				continue

			try:
				setpoint_value_num = float(setpoint_value)
			except ValueError:
				if setpoint_value == 'On':
					setpoint_value_num = 1.0
				elif setpoint_value == 'Off':
					setpoint_value_num = 0.0
				else:
					Domoticz.Debug(("Cannot convert setpoint_value | " + (f"Nem konvertálható setpoint_value: {setpoint_value}")))
					setpoint_value_num = 0.0

			# Default: retain the previous value | Alapértelmezésként a korábbi érték marad
			setpoint_minusz = setpoint_value_num

			if Devices[58].sValue == "10":

				komp = round((aktual_temp - ftargettemp_also) * 2)

				if Devices[211].sValue == "20":

					trv_temp = self.get_trv_temp(setpointID)

					if isinstance(trv_temp, (int, float)):
						if trv_temp > aktual_temp:
							diff = trv_temp - aktual_temp 
							setpoint_minusz = (ftargettemp_also - diff) - komp
						else:
							setpoint_minusz = ftargettemp_also - komp
					else:
						setpoint_minusz = ftargettemp_also - komp
				else:
					setpoint_minusz = ftargettemp_also - komp
				
				setpoint_minusz = round(setpoint_minusz * 2) / 2
				setpoint_minusz = max(ftargettemp_also - 5, min(setpoint_minusz, ftargettemp_also))
				
			elif Devices[58].sValue == "20" :

				if Devices[211].sValue == "30":

					trv_temp = self.get_trv_temp(setpointID)

					komp = round((aktual_temp - htargettemp_also) * 6)

					if isinstance(trv_temp, (int, float)):
						if aktual_temp > trv_temp:
							diff = aktual_temp - trv_temp
							setpoint_minusz = htargettemp_also + diff + komp
							Domoticz.Debug(f"Lower heating target + difference + compensation | Alsó fűtési célérték + különbség + kompenzáció: ")
						else:
							setpoint_minusz = htargettemp_also + komp
							Domoticz.Debug(f"Lower heating target + compensation | Alsó fűtési célérték + kompenzáció: ")
					else:
						setpoint_minusz = htargettemp_also + komp
						Domoticz.Debug(f"Lower cooling target + compensation | Alsó hűtési célérték + kompenzáció: {setpoint_minusz}")
				else: 
					setpoint_minusz = round(setpoint_minusz * 2) / 2
					setpoint_minusz = max(htargettemp_also - 5, min(setpoint_minusz, htargettemp_also))

			setpoint_minusz = min(setpoint_minusz, 30.0)
			setpoint_minusz = round(setpoint_minusz, 1)

			if setpoint_minusz != setpoint_value_num :
				update_url = f"type=command&param=udevice&idx={setpointidx}&nvalue=0&svalue={setpoint_minusz}"
				DomoticzAPI(update_url)
				Domoticz.Debug(f"Setpoint decrease URL: {update_url} | Célhőmérséklet-csökkentés URL-je ={update_url}")
				Domoticz.Debug(f"Decrease setpoint: idx={setpointidx}, setpoint={setpoint_minusz} | Célhőmérséklet csökkentése: idx={setpointidx}, célérték={setpoint_minusz}")


	def get_trv_temp(self, trv_id):

		trv_id = str(trv_id)

		if not isinstance(self.AktualTemp, dict) or not isinstance(self.AktualTemp.get("result"), list):
			return None

		for dev in self.AktualTemp["result"]:

			dev_id = str(dev.get("ID", ""))

			# Match by ID | ID szerinti egyezés
			if dev_id == trv_id:
				try:
					temp_val = float(dev.get("Temp"))
					if math.isfinite(temp_val):
						return temp_val
					return None
				except (TypeError, ValueError) as e:
					Domoticz.Debug(f"[TRV] Temperature parsing error (ID={dev_id}): {e} | [TRV] Hőmérséklet-feldolgozási hiba (ID={dev_id}): {e}")
					return None

		return None


	def get_AC_zone_var(self, zone: int, fh_mode: str = "F"):

		varname = Parameters["Name"] + f"_Z_{zone}_AC_{fh_mode}"
		default_attr = f"AC_{zone}_{fh_mode}"
		target_attr = f"Z_{zone}_AC_{fh_mode}"

		# Reuse cached variables for 5 seconds | Gyorsítótárazott változók használata 5 másodpercig
		now = time.monotonic()

		if now >= self._ac_variables_cache_until:
			variables = DomoticzAPI("type=command&param=getuservariables")

			if variables is not None and isinstance(variables.get("result"), list):
				self._ac_variables_cache = {
					variable["Name"]: variable.get("Value", "")
					for variable in variables["result"]
					if isinstance(variable, dict) and "Name" in variable
				}
			else:
				# API failure does not mean the variable is missing | Az API-hiba nem jelenti a változó hiányát
				self._ac_variables_cache = None
				Domoticz.Error(
					f"Cannot read AC variables for {varname} | "
					f"Nem olvashatók a(z) {varname} klímaváltozói"
				)

			self._ac_variables_cache_until = time.monotonic() + 5.0

		# Preserve current settings on API failure | API-hiba esetén a jelenlegi beállítások megőrzése
		if self._ac_variables_cache is None:
			return getattr(self, target_attr)

		if varname not in self._ac_variables_cache:
			# Create missing variable only after successful reading | Hiányzó változó létrehozása csak sikeres lekérdezés után
			default_value = getattr(self, default_attr).copy()

			result = DomoticzAPI(
				f"type=command&param=adduservariable&vname={varname}&vtype=2&vvalue={json.dumps(default_value)}"
			)

			if result is not None:
				self._ac_variables_cache[varname] = json.dumps(default_value)
			else:
				self._ac_variables_cache = None
				self._ac_variables_cache_until = time.monotonic() + 5.0
				Domoticz.Error(
					f"Cannot create AC variable {varname} | "
					f"Nem hozható létre a(z) {varname} klímaváltozó"
				)
				return getattr(self, target_attr)

			setattr(self, target_attr, default_value)
			return getattr(self, target_attr)

		try:
			stored = json.loads(self._ac_variables_cache[varname])
			if not isinstance(stored, dict):
				raise ValueError("AC variable must contain a JSON object")

			base = getattr(self, default_attr).copy()
			base.update(stored)
			setattr(self, target_attr, base)

		except (ValueError, TypeError) as e:
			Domoticz.Debug(
				f"Invalid JSON in user variable {varname}: {e} | "
				f"Hibás JSON a(z) {varname} felhasználói változóban: {e}"
			)
			setattr(self, target_attr, getattr(self, default_attr).copy())

		return getattr(self, target_attr)


	def send_AC_command(self, zone, fh_mode, power):
		
		# Initial debug check: inspect received parameters | Első hibakeresési ellenőrzés: milyen paramétereket kaptunk
		Domoticz.Debug(f"Send AC command parameters (zone, mode, power): {zone}, {fh_mode}, {power} | Klímavezérlési parancs paraméterei (zóna, üzemmód, teljesítmény): {zone}, {fh_mode}, {power}")

		# Convert mode to text | Az üzemmód átalakítása szöveggé
		mode = "Heat" if fh_mode == "F" else "Cool"
		power_cmd = "On" if power == "On" else "Off"

		# Retrieve AC settings | Klímabeállítások lekérdezése
		ac_data = self.get_AC_zone_var(zone, fh_mode)
		if str(ac_data["type"]) in ("0", "", "-"):
			Domoticz.Debug(f"Zone {zone} [{fh_mode}]: no air conditioner configured | Zóna {zone} [{fh_mode}]: nincs klíma beállítva")
			return

		# Retrieve target temperature (F: heating, H: cooling) | Célhőmérséklet lekérdezése (F: fűtés, H: hűtés)
		if fh_mode == "F":
			target = getattr(self, f"ftargettemp_{zone}")
		else:
			target = getattr(self, f"htargettemp_{zone}")
		
		Domoticz.Debug(f"Zone {zone}: target temperature = {target} | Zóna {zone}: célhőmérséklet = {target}")

		Domoticz.Debug(
			"AC presence: self.jelenletInfo={0} ({1}), AC_jelenlet={2} ({3}) | Klímajelenlét: self.jelenletInfo={0} ({1}), AC_jelenlet={2} ({3})".format(self.jelenletInfo, type(self.jelenletInfo), ac_data.get('AC_jelenlet'), type(ac_data.get('AC_jelenlet')))
		)

		if self.jelenletInfo and ac_data["AC_jelenlet"] == "On" :
			power_cmd = "On"
		elif self.jelenletInfo and ac_data["AC_jelenlet"] == "Off" :
			power_cmd = "Off"

		# Assemble command | Parancs összeállítása
		cmd = (
			f'IRHVAC {{"Vendor":"{ac_data["type"]}","Power":"{power_cmd}","Mode":"{mode}",'
			f'"Temp":{target},"FanSpeed":{ac_data["fanspeed"]},'
			f'"SwingV":{ac_data["swingv"]},"SwingH":{ac_data["swingh"]},"Beep":0}}'
		)
		url = f'http://{ac_data["IP"]}/cm?cmnd={parse.quote(cmd)}'

		key = f"{zone}_{fh_mode}"  # Key for zone and mode | Kulcs a zónához és az üzemmódhoz

		# Storage for previous commands and counters | Korábbi parancsok és számlálók tárolói
		if not hasattr(self, 'last_ac_commands'):
			self.last_ac_commands = {}

		if not hasattr(self, 'ir_resend_counters'):
			self.ir_resend_counters = {}

		# 1. If command changes, send immediately and reset | 1. Ha a parancs megváltozott: azonnali küldés és visszaállítás
		if self.last_ac_commands.get(key) != cmd:
			Domoticz.Debug(f"Zone {zone} [{fh_mode}]: new command, sending immediately to {url} | Zóna {zone} [{fh_mode}]: új parancs, azonnali küldés ide: {url}")
			try:
				response = request.urlopen(url)
				Domoticz.Debug((lambda reply: f"Zone {zone} [{fh_mode}] response: {reply} | Zóna {zone} [{fh_mode}] válasz: {reply}")(response.read().decode()))
				time.sleep(0.5)
				self.last_ac_commands[key] = cmd
				self.ir_resend_counters[key] = 0
			except Exception as e:
				Domoticz.Debug(f"Zone {zone} [{fh_mode}] send error: {e} | Zóna {zone} [{fh_mode}] küldési hiba: {e}")
			return

		# 2. If unchanged and repeats are disabled, do not send | 2. Ha nincs változás és ismétlés sincs engedélyezve, nem küldünk
		if getattr(self, 'ir_resend', 0) == 0:
			Domoticz.Debug(f"Zone {zone} [{fh_mode}]: command unchanged and resend disabled, not sending | Zóna {zone} [{fh_mode}]: parancs változatlan, újraküldés letiltva, nincs küldés")
			return

		# 3. If unchanged and repeats enabled, resend on the x-th cycle | 3. Ha nincs változás, de ismétlés van beállítva, újraküldés az x-edik ciklusban
		counter = self.ir_resend_counters.get(key, 0) + 1

		if counter >= self.ir_resend:
			try:
				Domoticz.Debug(f"Zone {zone} [{fh_mode}]: resend attempt {counter} to {url} | Zóna {zone} [{fh_mode}]: {counter}. újraküldési kísérlet ide: {url}")
				response = request.urlopen(url)
				Domoticz.Debug((lambda reply: f"Zone {zone} [{fh_mode}] response: {reply} | Zóna {zone} [{fh_mode}] válasz: {reply}")(response.read().decode()))
				time.sleep(0.5)
				self.ir_resend_counters[key] = 0
			except Exception as e:
				Domoticz.Debug(f"Zone {zone} [{fh_mode}] resend error: {e} | Zóna {zone} [{fh_mode}] újraküldési hiba: {e}")
		else:
			self.ir_resend_counters[key] = counter
			Domoticz.Debug(f"Zone {zone} [{fh_mode}]: resend counter {counter}/{self.ir_resend} | Zóna {zone} [{fh_mode}]: újraküldési számláló {counter}/{self.ir_resend}")

	
	def UpdateDevice(self, Unit, nValue, sValue):
		Domoticz.Debug("Update Unit: "+format(Unit)+" | nValue: "+str(nValue)+" | sValue: "+str(sValue)+" ("+Devices[Unit].Name+")")
		Devices[Unit].Update(nValue=nValue, sValue=str(sValue))

	def WriteLog(self, message, level="Normal"):

		if (self.loglevel == "Verbose" and level == "Verbose") or level == "Status":
			if self.statussupported:
				Domoticz.Status(message)
			else:
				Domoticz.Log(message)
		elif level == "Normal":
			Domoticz.Log(message)


	def SensorTimedOut(self, idx, name, datestring):
		Domoticz.Debug("Device index = {0} | Eszközindex (idx) = {0}".format(idx))
		Domoticz.Debug("Name = {0} | Név = {0}".format(name))
		Domoticz.Debug("Date string = {0} | Dátumszöveg = {0}".format(datestring))

		def LastUpdate(datestring):
			dateformat = "%Y-%m-%d %H:%M:%S"
			try:
				result = time.mktime(time.strptime(datestring, dateformat))
			except ValueError as e:
				Domoticz.Error(f"Invalid date format: {datestring}, error: {e} | Érvénytelen dátumformátum: {datestring}, hiba: {e}")
				result = None
			return result

		last_update_timestamp = LastUpdate(datestring)
		if last_update_timestamp is None:
			Domoticz.Error('Unable to parse datestring; assuming sensor has timed out. | Nem sikerült feldolgozni a dátumszöveget; feltételezzük, hogy az érzékelő időtúllépés miatt nem válaszol.')
			return True

		# Current timestamp | Aktuális időbélyeg
		now_timestamp = time.time()

		# Check timeout (70 minutes after the last update) | Időtúllépés ellenőrzése (70 perccel az utolsó frissítés után)
		timedout = (last_update_timestamp + 70 * 60) < now_timestamp

		Domoticz.Debug("Timed out = {0} | Időtúllépés = {0}".format(timedout))

		return timedout

	def addfavorite(self, deviceidx):
		self._fav_actions[deviceidx] = "add"

	def removefavorite(self, deviceidx):
		# Only if ADD has not yet occurred for this idx | Csak akkor, ha ehhez az idx-hez még nem volt ADD
		if self._fav_actions.get(deviceidx) != "add":
			self._fav_actions[deviceidx] = "remove"

	def applyfavorites(self):

		Domoticz.Debug(
			"applyfavorites(): favorite actions = {0} | applyfavorites(): kedvencműveletek = {0}".format(self._fav_actions)
		)

		for idx, action in self._fav_actions.items():
			if action == "add":
				DomoticzAPI(
					"idx={}&isfavorite=1&param=makefavorite&type=command".format(idx)
				)
			elif action == "remove":
				DomoticzAPI(
					"idx={}&isfavorite=0&param=makefavorite&type=command".format(idx)
				)

		# Reset for the next cycle | Visszaállítás a következő ciklusra
		self._fav_actions.clear()


	def WeatherForecastAPI(self):

		WeatherForecast = self.met_data_string if self.met_data_string else None
		url = "None"

		try:
			url = (
				"https://api.open-meteo.com/v1/forecast"
				f"?latitude={self.location[0]}"
				f"&longitude={self.location[1]}"
				"&hourly=temperature_2m,relative_humidity_2m,dew_point_2m,rain,precipitation,wind_speed_10m,wind_gusts_10m,wind_direction_10m,shortwave_radiation,cloud_cover,pressure_msl"
				"&timezone=auto"
				"&forecast_days=1"
			)

			Domoticz.Debug(f"Calling WeatherForecastAPI via Open-Meteo: {url} | WeatherForecastAPI Open-Meteo hívása: {url}")

			req = request.Request(url)
			response = request.urlopen(req, timeout=10)

			if response.status == 200:

				raw_data = json.loads(response.read().decode("utf-8"))
				hourly = raw_data.get("hourly", {})

				times = hourly.get("time", [])
				temperatures = hourly.get("temperature_2m", [])
				humidities = hourly.get("relative_humidity_2m", [])
				dewpoints = hourly.get("dew_point_2m", [])
				rains = hourly.get("rain", [])
				precipitations = hourly.get("precipitation", [])
				winds = hourly.get("wind_speed_10m", [])
				windgusts = hourly.get("wind_gusts_10m", [])
				winddirections = hourly.get("wind_direction_10m", [])
				radiations = hourly.get("shortwave_radiation", [])
				cloudcovers = hourly.get("cloud_cover", [])
				pressures = hourly.get("pressure_msl", [])

				WeatherForecast = []

				for i in range(len(times)):

					datum = times[i].replace("T", " ")

					if len(datum) == 16:
						datum += ":00"

					temp = temperatures[i] if i < len(temperatures) else None
					humidity = humidities[i] if i < len(humidities) else None
					dewpoint = dewpoints[i] if i < len(dewpoints) else None
					rain = rains[i] if i < len(rains) else None
					precipitation = precipitations[i] if i < len(precipitations) else None
					wind = winds[i] if i < len(winds) else None
					windgust = windgusts[i] if i < len(windgusts) else None
					winddirection = winddirections[i] if i < len(winddirections) else None
					radiation = radiations[i] if i < len(radiations) else None
					cloudcover = cloudcovers[i] if i < len(cloudcovers) else None
					pressure = pressures[i] if i < len(pressures) else None

					lux = round(radiation * 120) if radiation is not None else None

					WeatherForecast.append({"time": datum, "temp": str(temp) if temp is not None else None, "humidity": str(humidity) if humidity is not None else None, "dewpoint": str(dewpoint) if dewpoint is not None else None, "rain": str(rain) if rain is not None else None, "precipitation": str(precipitation) if precipitation is not None else None, "wind": str(wind) if wind is not None else None, "windgust": str(windgust) if windgust is not None else None, "winddirection": str(winddirection) if winddirection is not None else None, "radiation": str(radiation) if radiation is not None else None, "lux": str(lux) if lux is not None else None, "cloudcover": str(cloudcover) if cloudcover is not None else None, "pressure": str(pressure) if pressure is not None else None})

				Domoticz.Debug(f"Open-Meteo data converted: {len(WeatherForecast)} records | Open-Meteo adatok átalakítva: {len(WeatherForecast)} rekord")

			else:
				Domoticz.Error(f"WeatherForecastAPI Open-Meteo: HTTP error = {response.status} | WeatherForecastAPI Open-Meteo: HTTP-hiba = {response.status}")

			response.close()

		except Exception as e:
			Domoticz.Error("API request failed for '{0}': {1} | Hiba történt a következő API hívásakor: '{0}'. Hiba: {1}".format(url, str(e)))

		return WeatherForecast

global _plugin
_plugin = BasePlugin()

def onStart():
	global _plugin
	_plugin.onStart()


def onStop():
	# Mark plugin as stopping | Plugin leállításának jelzése
	if 87 in Devices and Devices[87].sValue != "STOPPING":
		Devices[87].Update(nValue=0, sValue="STOPPING")
	
	global _plugin
	_plugin.onStop()


def onCommand(Unit, Command, Level, Color):
	global _plugin
	_plugin.onCommand(Unit, Command, Level, Color)


def onHeartbeat():
	global _plugin
	_plugin.onHeartbeat()


# Plugin utility functions | Plugin segédfüggvényei

def parseCSV(strCSV):

	listvals = []
	for value in strCSV.split(","):
		try:
			val = int(value)
		except:
			pass
		else:
			listvals.append(val)
	return listvals

def parseCSVparams(strCSV):
	listvalsparams = []
	for i, value in enumerate(strCSV.split(",")):
		try:
			# Elements 5 and 6 always remain strings | Az 5. és 6. elem mindig karakterlánc marad
			if i >= 3:
				val = str(value)
			else:
				val = int(value)
		except ValueError:
			val = None  # On error, store None instead | Hiba esetén inkább None értéket állítunk be
		listvalsparams.append(val)
	return listvalsparams


def parse_K(strCSV):

	s = strCSV

	pattern = r'K:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_T(strCSV):

	s = strCSV

	pattern = r'T:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_P(strCSV):

	s = strCSV

	pattern = r'P:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_P_F(strCSV):

	s = strCSV

	pattern = r'P_F:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_P_H(strCSV):

	s = strCSV

	pattern = r'P_H:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_PE(strCSV):

	s = strCSV

	pattern = r'PE:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_BK(strCSV):

	s = strCSV

	pattern = r'BK:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_UK(strCSV):

	s = strCSV

	pattern = r'UK:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_F(strCSV):

	s = strCSV

	pattern = r'F:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_M(strCSV):

	s = strCSV

	pattern = r'M:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_E(strCSV):

	s = strCSV

	pattern = r'E:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_H(strCSV):

	s = strCSV

	pattern = r'H:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_Z_1(strCSV):

	s = strCSV

	pattern = r'Z_1:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_Z_2(strCSV):

	s = strCSV

	pattern = r'Z_2:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_Z_3(strCSV):

	s = strCSV

	pattern = r'Z_3:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_Z_4(strCSV):

	s = strCSV

	pattern = r'Z_4:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_Z_5(strCSV):

	s = strCSV

	pattern = r'Z_5:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_Z_6(strCSV):

	s = strCSV

	pattern = r'Z_6:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_Z_7(strCSV):

	s = strCSV

	pattern = r'Z_7:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_Z_8(strCSV):

	s = strCSV

	pattern = r'Z_8:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_Z_9(strCSV):

	s = strCSV

	pattern = r'Z_9:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_Z_10(strCSV):

	s = strCSV

	pattern = r'Z_10:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_Z_11(strCSV):

	s = strCSV

	pattern = r'Z_11:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_Z_12(strCSV):

	s = strCSV

	pattern = r'Z_12:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_Z_1_F(strCSV):

	s = strCSV

	pattern = r'Z_1_F:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_Z_2_F(strCSV):

	s = strCSV

	pattern = r'Z_2_F:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_Z_3_F(strCSV):

	s = strCSV

	pattern = r'Z_3_F:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_Z_4_F(strCSV):

	s = strCSV

	pattern = r'Z_4_F:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_Z_5_F(strCSV):

	s = strCSV

	pattern = r'Z_5_F:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_Z_6_F(strCSV):

	s = strCSV

	pattern = r'Z_6_F:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_Z_7_F(strCSV):

	s = strCSV

	pattern = r'Z_7_F:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_Z_8_F(strCSV):

	s = strCSV

	pattern = r'Z_8_F:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_Z_9_F(strCSV):

	s = strCSV

	pattern = r'Z_9_F:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_Z_10_F(strCSV):

	s = strCSV

	pattern = r'Z_10_F:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_Z_11_F(strCSV):

	s = strCSV

	pattern = r'Z_11_F:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_Z_12_F(strCSV):

	s = strCSV

	pattern = r'Z_12_F:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_Z_1_F_V(strCSV):

	s = strCSV

	pattern = r'Z_1_F_V:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_Z_2_F_V(strCSV):

	s = strCSV

	pattern = r'Z_2_F_V:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_Z_3_F_V(strCSV):

	s = strCSV

	pattern = r'Z_3_F_V:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_Z_4_F_V(strCSV):

	s = strCSV

	pattern = r'Z_4_F_V:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_Z_5_F_V(strCSV):

	s = strCSV

	pattern = r'Z_5_F_V:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_Z_6_F_V(strCSV):

	s = strCSV

	pattern = r'Z_6_F_V:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_Z_7_F_V(strCSV):

	s = strCSV

	pattern = r'Z_7_F_V:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_Z_8_F_V(strCSV):

	s = strCSV

	pattern = r'Z_8_F_V:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_Z_9_F_V(strCSV):

	s = strCSV

	pattern = r'Z_9_F_V:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_Z_10_F_V(strCSV):

	s = strCSV

	pattern = r'Z_10_F_V:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_Z_11_F_V(strCSV):

	s = strCSV

	pattern = r'Z_11_F_V:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_Z_12_F_V(strCSV):

	s = strCSV

	pattern = r'Z_12_F_V:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_Z_1_H(strCSV):

	s = strCSV

	pattern = r'Z_1_H:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_Z_2_H(strCSV):

	s = strCSV

	pattern = r'Z_2_H:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_Z_3_H(strCSV):

	s = strCSV

	pattern = r'Z_3_H:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_Z_4_H(strCSV):

	s = strCSV

	pattern = r'Z_4_H:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_Z_5_H(strCSV):

	s = strCSV

	pattern = r'Z_5_H:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_Z_6_H(strCSV):

	s = strCSV

	pattern = r'Z_6_H:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_Z_7_H(strCSV):

	s = strCSV

	pattern = r'Z_7_H:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_Z_8_H(strCSV):

	s = strCSV

	pattern = r'Z_8_H:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_Z_9_H(strCSV):

	s = strCSV

	pattern = r'Z_9_H:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_Z_10_H(strCSV):

	s = strCSV

	pattern = r'Z_10_H:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_Z_11_H(strCSV):

	s = strCSV

	pattern = r'Z_11_H:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_Z_12_H(strCSV):

	s = strCSV

	pattern = r'Z_12_H:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_Z_1_H_V(strCSV):

	s = strCSV

	pattern = r'Z_1_H_V::(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_Z_2_H_V(strCSV):

	s = strCSV

	pattern = r'Z_2_H_V::(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_Z_3_H_V(strCSV):

	s = strCSV

	pattern = r'Z_3_H_V::(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_Z_4_H_V(strCSV):

	s = strCSV

	pattern = r'Z_4_H_V::(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_Z_5_H_V(strCSV):

	s = strCSV

	pattern = r'Z_5_H_V::(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_Z_6_H_V(strCSV):

	s = strCSV

	pattern = r'Z_6_H_V::(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_Z_7_H_V(strCSV):

	s = strCSV

	pattern = r'Z_7_H_V::(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_Z_8_H_V(strCSV):

	s = strCSV

	pattern = r'Z_8_H_V::(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_Z_9_H_V(strCSV):

	s = strCSV

	pattern = r'Z_9_H_V::(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_Z_10_H_V(strCSV):

	s = strCSV

	pattern = r'Z_10_H_V::(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_Z_11_H_V(strCSV):

	s = strCSV

	pattern = r'Z_11_H_V::(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_Z_12_H_V(strCSV):

	s = strCSV

	pattern = r'Z_12_H_V::(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_A_1(strCSV):

	s = strCSV

	pattern = r'A_1:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_A_2(strCSV):

	s = strCSV

	pattern = r'A_2:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_A_3(strCSV):

	s = strCSV

	pattern = r'A_3:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_A_4(strCSV):

	s = strCSV

	pattern = r'A_4:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_A_5(strCSV):

	s = strCSV

	pattern = r'A_5:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_A_6(strCSV):

	s = strCSV

	pattern = r'A_6:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_A_7(strCSV):

	s = strCSV

	pattern = r'A_7:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_A_8(strCSV):

	s = strCSV

	pattern = r'A_8:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_A_9(strCSV):

	s = strCSV

	pattern = r'A_9:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_A_10(strCSV):

	s = strCSV

	pattern = r'A_10:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_A_11(strCSV):

	s = strCSV

	pattern = r'A_11:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_A_12(strCSV):

	s = strCSV

	pattern = r'A_12:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams



def parse_S_1(strCSV):

	s = strCSV

	pattern = r'S_1:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_S_2(strCSV):

	s = strCSV

	pattern = r'S_2:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_S_1M(strCSV):
	s = strCSV
	pattern = r'S_1M:(\d+)'  # The \d+ pattern matches digits only | A \d+ minta csak számjegyeket illeszt
	match = re.search(pattern, s)
	if match:
		return int(match.group(1))  # The first group contains the matched number | Az első csoport tartalmazza az illesztett számot
	else:
		return 100

def parse_S_2M(strCSV):
	s = strCSV
	pattern = r'S_2M:(\d+)'  # The \d+ pattern matches digits only | A \d+ minta csak számjegyeket illeszt
	match = re.search(pattern, s)
	if match:
		return int(match.group(1))  # The first group contains the matched number | Az első csoport tartalmazza az illesztett számot
	else:
		return 100

def parse_L(strCSV):

	s = strCSV

	pattern = r'L:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_N(strCSV):
	
	s = strCSV

	pattern = r'N:(\w+)'
	
	values = re.findall(pattern, s)
	
	listvalsparams = [1 if int(val) < 1 or int(val) > 7 else int(val) for val in values]
	
	return listvalsparams

def parse_O(strCSV):
	pattern = r'O:(\w+)'
	match = re.search(pattern, strCSV)
	if match:
		value = int(match.group(1))
		if 0 <= value <= 23:
			return value
		else:
			return 0  # Return 0 if the value is outside the specified range | Ha az érték kívül esik a megadott tartományon, 0-t adunk vissza
	else:
		return 0  # Also return 0 if no value was found | Ha nincs találat, szintén 0-t adunk vissza

def parse_V_1(strCSV):

	s = strCSV

	pattern = r'V_1:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_V_2(strCSV):

	s = strCSV

	pattern = r'V_2:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_V_3(strCSV):

	s = strCSV

	pattern = r'V_3:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_V_4(strCSV):

	s = strCSV

	pattern = r'V_4:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_V_5(strCSV):

	s = strCSV

	pattern = r'V_5:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_V_6(strCSV):

	s = strCSV

	pattern = r'V_6:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_V_7(strCSV):

	s = strCSV

	pattern = r'V_7:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_V_8(strCSV):

	s = strCSV

	pattern = r'V_8:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_V_9(strCSV):

	s = strCSV

	pattern = r'V_9:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_V_10(strCSV):

	s = strCSV

	pattern = r'V_10:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_V_11(strCSV):

	s = strCSV

	pattern = r'V_11:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_V_12(strCSV):

	s = strCSV

	pattern = r'V_12:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_C_1(strCSV):

	s = strCSV

	pattern = r'C_1:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_C_2(strCSV):

	s = strCSV

	pattern = r'C_2:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_C_3(strCSV):

	s = strCSV

	pattern = r'C_3:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_C_4(strCSV):

	s = strCSV

	pattern = r'C_4:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_C_5(strCSV):

	s = strCSV

	pattern = r'C_5:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_C_6(strCSV):

	s = strCSV

	pattern = r'C_6:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_C_7(strCSV):

	s = strCSV

	pattern = r'C_7:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_C_8(strCSV):

	s = strCSV

	pattern = r'C_8:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_C_9(strCSV):

	s = strCSV

	pattern = r'C_9:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_C_10(strCSV):

	s = strCSV

	pattern = r'C_10:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_C_11(strCSV):

	s = strCSV

	pattern = r'C_11:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_C_12(strCSV):

	s = strCSV

	pattern = r'C_12:(\w+)'

	listvalsparams = list(map(int, re.findall(pattern,s)))

	return listvalsparams

def parse_FG_T(strCSV):

	pattern = r'(?:^|,)FG_T:(\d+)(?=,|$)'

	return list(map(int, re.findall(pattern, strCSV)))


def parse_FG_S(strCSV):

	pattern = r'(?:^|,)FG_S:(\d+)(?=,|$)'

	return list(map(int, re.findall(pattern, strCSV)))


def parse_SV_P(strCSV):

	pattern = r'(?:^|,)SV_P:(\d+)(?=,|$)'

	return list(map(int, re.findall(pattern, strCSV)))


def parse_SV_D(strCSV):

	pattern = r'(?:^|,)SV_D:(\d+)(?=,|$)'
	values = re.findall(pattern, strCSV)

	return int(values[0]) if values and 0 <= int(values[0]) <= 6 else None


def parse_SV_H(strCSV):

	pattern = r'(?:^|,)SV_H:(\d+)(?=,|$)'
	values = re.findall(pattern, strCSV)

	return int(values[0]) if values and 0 <= int(values[0]) <= 23 else None


def parse_SV_M(strCSV):

	pattern = r'(?:^|,)SV_M:(\d+)(?=,|$)'
	values = re.findall(pattern, strCSV)

	return int(values[0]) if values and 1 <= int(values[0]) <= 20 else None

def DomoticzAPI(APICall):

	resultJson = None
	url = "http://{}:{}/json.htm?{}".format(Parameters["Address"], Parameters["Port"], parse.quote(APICall, safe="&="))
	Domoticz.Debug("Calling Domoticz API: {0} | Domoticz API hívása: {0}".format(url))
	try:
		req = request.Request(url)
		if Parameters["Username"] != "":
			Domoticz.Debug("Add authentication for user {0} | Hitelesítés hozzáadása a(z) {0} felhasználóhoz".format(Parameters["Username"]))
			credentials = ('%s:%s' % (Parameters["Username"], Parameters["Password"]))
			encoded_credentials = base64.b64encode(credentials.encode('ascii'))
			req.add_header('Authorization', 'Basic %s' % encoded_credentials.decode("ascii"))
		
		response = request.urlopen(req, timeout=5)
		if response.status == 200:
			resultJson = json.loads(response.read().decode('utf-8'))
			if resultJson["status"] != "OK":
				Domoticz.Error('Calling domoticz API: {0} | Domoticz API hívása: {0}'.format(url))
				Domoticz.Error('Domoticz API returned an error: status = {0} | A Domoticz API hibát jelzett: állapot = {0}'.format(resultJson["status"]))
				resultJson = None
		else:
			Domoticz.Error('Domoticz API: http error = {0} | Domoticz API: HTTP-hiba = {0}'.format(response.status))
		response.close()
	except Exception as e:
		# Log the actual API error | A tényleges API-hiba naplózása
		Domoticz.Error(
			f"Error calling '{url}': {type(e).__name__}: {e} | "
			f"Hiba a következő cím hívásakor: '{url}': {type(e).__name__}: {e}"
		)
	return resultJson

# Generic helper functions | Általános segédfüggvények
def DumpConfigToLog():
	for x in Parameters:
		if Parameters[x] != "":
			Domoticz.Debug("Parameter: '{0}':'{1}' | Paraméter: '{0}':'{1}'".format(x, Parameters[x]))
	Domoticz.Debug("Number of devices: {0} | Eszközök száma: {0}".format(len(Devices)))
	for x in Devices:
		Domoticz.Debug("Device: {0} - {1} | Eszköz: {0} - {1}".format(x, Devices[x]))
		Domoticz.Debug("Device ID: {0} | Eszközazonosító: {0}".format(Devices[x].ID))
		Domoticz.Debug("Device name: {0} | Eszköz neve: {0}".format(Devices[x].Name))
		Domoticz.Debug("Device numeric value: {0} | Eszköz nValue értéke: {0}".format(Devices[x].nValue))
		Domoticz.Debug("Device string value: {0} | Eszköz sValue értéke: {0}".format(Devices[x].sValue))
		Domoticz.Debug("Device last level: {0} | Eszköz utolsó szintje: {0}".format(Devices[x].LastLevel))
	return
	
def JelenletAPI(jelennev):
	resultJelen = False  # Default value | Alapértelmezett érték
	
	try:
		wifiurl = "http://{}/cgi-bin/luci/wifi-presence/{}".format(Parameters["Address"], jelennev)
		Domoticz.Debug("Calling presence API (Wi-Fi branch): {0} | Jelenlét-API hívása (Wi-Fi ág): {0}".format(wifiurl))
		reqwifi = request.Request(wifiurl)
		response = request.urlopen(reqwifi)
		
		if response.status == 404:
			Domoticz.Error('Presence API (Wi-Fi branch): HTTP 404 – URL not found | Jelenlét-API (Wi-Fi ág): HTTP 404 – a kért URL nem található')
			resultJelen = "404"
		elif response.status == 200:
			response_text = response.read().decode('utf-8').strip()
			Domoticz.Debug("Presence API (Wi-Fi branch) response: {0} | Jelenlét-API (Wi-Fi ág) válasza: {0}".format(response_text))  # Log response contents | A válasz tartalmának naplózása
			
			# Distinguish JSON response from other string responses | Megkülönböztetjük a JSON-választ a többi karakterlánc-választól
			if response_text == "nogroup":
				resultJelen = "nogroup"
				Domoticz.Debug("Presence API (Wi-Fi branch): received nogroup response | Jelenlét-API (Wi-Fi ág): nogroup válasz érkezett")
			elif response_text:  # If the response is nonempty, try parsing it as JSON | Ha a válasz nem üres, megpróbáljuk JSON-ként feldolgozni
				try:
					resultJelen = json.loads(response_text)
				except json.JSONDecodeError:
					Domoticz.Error('Presence API (Wi-Fi branch): invalid JSON response | Jelenlét-API (Wi-Fi ág): nem érvényes JSON válasz')
					resultJelen = False
				
				# Check whether response is a boolean | Ellenőrizzük, hogy a válasz logikai (bool) típusú-e
				if isinstance(resultJelen, bool):
					Domoticz.Debug(("Presence API (Wi-Fi branch): boolean response received | " + ("Jelenlét-API (Wi-Fi ág): bool típusú válasz érkezett")))
				elif isinstance(resultJelen, str):
					if resultJelen.strip() == "true":
						resultJelen = True
					elif resultJelen.strip() == "false":
						resultJelen = False
				else:
					Domoticz.Error('Presence API (Wi-Fi branch): unexpected response type | Jelenlét-API (Wi-Fi ág): nem várt típusú válasz')
			else:
				Domoticz.Error('Presence API (Wi-Fi branch): received an empty response | Jelenlét-API (Wi-Fi ág): üres válasz érkezett')
		else:
			Domoticz.Error('Presence API (Wi-Fi branch): HTTP error = {0} | Jelenlét-API (Wi-Fi ág): HTTP-hiba = {0}'.format(response.status))
		response.close()

	except request.HTTPError as e:
		if e.code == 404:
			Domoticz.Error('Presence API (Wi-Fi branch): HTTP 404 – URL not found | Jelenlét-API (Wi-Fi ág): HTTP 404 – a kért URL nem található')
			resultJelen = "404"
		else:
			Domoticz.Error('Presence API (Wi-Fi branch): HTTP error = {0} | Jelenlét-API (Wi-Fi ág): HTTP-hiba = {0}'.format(e.code))
	except Exception as e:
		Domoticz.Error("Presence API (Wi-Fi branch): error calling '{0}': {1} | Jelenlét-API (Wi-Fi ág): Hiba a hívás során '{0}': {1}".format(wifiurl, str(e)))

	# Delay to prevent Wi-Fi and LAN branches running at the same time | Késleltetés, hogy a Wi-Fi és LAN ágak ne fussanak egyszerre
	time.sleep(0.2)

	# If the first attempt did not return 'True', try the second URL | Ha az első próbálkozás nem adott 'True' értéket, megpróbáljuk a második URL-t
	if resultJelen != True:
		try:
			lanurl = "http://{}/cgi-bin/luci/presence/{}".format(Parameters["Address"], jelennev)
			Domoticz.Debug("Calling presence API (LAN branch): {0} | Jelenlét-API hívása (LAN ág): {0}".format(lanurl))
			reqlan = request.Request(lanurl)
			response = request.urlopen(reqlan)

			if response.status == 404:
				Domoticz.Error('Presence API (LAN branch): HTTP 404 – URL not found | Jelenlét-API (LAN ág): HTTP 404 – a kért URL nem található')
				resultJelen = "404"
			elif response.status == 200:
				response_text = response.read().decode('utf-8').strip()
				Domoticz.Debug("Presence API (LAN branch) response: {0} | Jelenlét-API (LAN ág) válasza: {0}".format(response_text))  # Log response contents | A válasz tartalmának naplózása
				
				# Distinguish JSON response from other string responses | Megkülönböztetjük a JSON-választ a többi karakterlánc-választól
				if response_text == "nogroup":
					resultJelen = "nogroup"
					Domoticz.Debug(("Presence API (LAN branch): nogroup response received | " + ("Jelenlét-API (LAN ág): nogroup válasz érkezett")))
				elif response_text:  # If the response is nonempty, try parsing it as JSON | Ha a válasz nem üres, megpróbáljuk JSON-ként feldolgozni
					try:
						resultJelen = json.loads(response_text)
					except json.JSONDecodeError:
						Domoticz.Error('Presence API (LAN branch): invalid JSON response | Jelenlét-API (LAN ág): nem érvényes JSON válasz')
						resultJelen = False
					
					# Check whether response is a boolean | Ellenőrizzük, hogy a válasz logikai (bool) típusú-e
					if isinstance(resultJelen, bool):
						Domoticz.Debug(("Presence API (LAN branch): boolean response received | " + ("Jelenlét-API (LAN ág): bool típusú válasz érkezett")))
					elif isinstance(resultJelen, str):
						if resultJelen.strip() == "true":
							resultJelen = True
						elif resultJelen.strip() == "false":
							resultJelen = False
					else:
						Domoticz.Error('Presence API (LAN branch): unexpected response type | Jelenlét-API (LAN ág): nem várt típusú válasz')
				else:
					Domoticz.Error('Presence API (LAN branch): received an empty response | Jelenlét-API (LAN ág): üres válasz érkezett')
			else:
				Domoticz.Error('Presence API (LAN branch): HTTP error = {0} | Jelenlét-API (LAN ág): HTTP-hiba = {0}'.format(response.status))
			response.close()

		except request.HTTPError as e:
			if e.code == 404:
				Domoticz.Error('Presence API (LAN branch): HTTP 404 – URL not found | Jelenlét-API (LAN ág): HTTP 404 – a kért URL nem található')
				resultJelen = "404"
			else:
				Domoticz.Error('Presence API (LAN branch): HTTP error = {0} | Jelenlét-API (LAN ág): HTTP-hiba = {0}'.format(e.code))
		except Exception as e:
			Domoticz.Error("Presence API (LAN branch): error calling '{0}': {1} | Jelenlét-API (LAN ág): Hiba a hívás során '{0}': {1}".format(lanurl, str(e)))

	return resultJelen



def getUserVar(self):

	variables = DomoticzAPI("type=command&param=getuservariables")
	if variables:
		# there is a valid response from the API but we do not know if our variable exists yet | Érvényes API-válasz érkezett, de még nem tudjuk, hogy létezik-e a változónk
		novar = True
		varname = Parameters["Name"] + "status"
		valuestring = ""
		if "result" in variables:
			for variable in variables["result"]:
				if variable["Name"] == varname :
					valuestring = variable["Value"]
					novar = False
					Domoticz.Debug('Variable novar | novar változó: '+format(novar))
					break

		if novar:
			parameter = "adduservariable"

			DomoticzAPI("type=command&param={}&vname={}&vtype=2&vvalue={}".format(parameter, varname, str(self.InternalsDefaults)))
			self.Internals = self.InternalsDefaults.copy()  # Reinitialize internal variables | Újrainicializáljuk a belső változókat
			
		else:
			try:
				self.Internals.update(eval(valuestring))
			except:
				self.Internals = self.InternalsDefaults.copy()
			return


def saveUserVar(self):

	varname = Parameters["Name"] + "status"
	
	DomoticzAPI("type=command&param=updateuservariable&vname={}&vtype=2&vvalue={}".format(varname, str(self.Internals)))

def getPowerVar(self):

	variables = DomoticzAPI("type=command&param=getuservariables")
	if variables:
		# there is a valid response from the API but we do not know if our variable exists yet | Érvényes API-válasz érkezett, de még nem tudjuk, hogy létezik-e a változónk
		novar = True
		varname = Parameters["Name"] + "power"
		valuestring = ""
		if "result" in variables:
			for variable in variables["result"]:
				if variable["Name"] == varname :
					valuestring = variable["Value"]
					novar = False
					Domoticz.Debug('Variable novar | novar változó: '+format(novar))
					break

		if novar:
			parameter = "adduservariable"

			DomoticzAPI("type=command&param={}&vname={}&vtype=2&vvalue={}".format(parameter, varname, str(self.AutocallibDefaults)))
			self.AutoPower = self.AutocallibDefaults.copy()  # Reinitialize power variables | Újrainicializáljuk a teljesítményváltozókat
			
		else:
			try:
				self.AutoPower.update(eval(valuestring))
			except:
				self.AutoPower = self.InternalsDefaults.copy()
			return


def savePowerVar(self):

	varname = Parameters["Name"] + "power"
	
	DomoticzAPI("type=command&param=updateuservariable&vname={}&vtype=2&vvalue={}".format(varname, str(self.AutoPower)))


def current_day_of_week(first_day=0):
	
	# first_day: 0 = Monday, 1 = Tuesday, ..., 6 = Sunday | first_day: 0 = hétfő, 1 = kedd, ..., 6 = vasárnap
	today = datetime.now()
	
	week_day = today.weekday()
	
	days_to_first_day = (week_day - first_day) % 7
	
	return days_to_first_day + 1  # Days of the week numbered with Monday first (Monday = 1) | A hét napjainak száma, hétfő az első nap (hétfőtől 1-gyel számozva)
	
	getUserVar(self)

