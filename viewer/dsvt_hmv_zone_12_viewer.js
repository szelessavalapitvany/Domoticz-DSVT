var hardwareReq   = "/json.htm?type=command&param=gethardware";
var tempReq       = "/json.htm?type=command&param=graph&sensor=temp&range=day&idx=";
var tempName      = "/json.htm?type=command&param=getdevices&filter=temp&order=Name";
var switchReq = "/json.htm?type=command&param=getlightlog&range=day&idx=";
var switchName    = "/json.htm?type=command&param=getdevices&filter=lightlog&order=Name";
var devicesReq    = "/json.htm?type=command&param=getdevices";
var PercentageReq = "/json.htm?type=command&param=graph&sensor=Percentage&range=day&idx=";
var utilityReq    = "/json.htm?type=command&param=graph&sensor=counter&range=day&idx=";
var windReq       = "/json.htm?type=command&param=graph&sensor=wind&range=day&idx=";
var setpointReq   = "/json.htm?type=command&param=getdevices&rid=";
var settingsReg   = "/json.htm?type=command&param=getsettings";
var userVarReq    = "/json.htm?type=command&param=getuservariables";

class DSVT_HMV_ZONE_12_Thermostat {
	constructor() {
		this.name = "";
		this.tempIn = undefined;
		this.tempOut = undefined;
		this.tempTartaly = undefined;
	}
}
class Elsodleges_F {
	constructor() {
		this.historic=undefined;
		this.isDimmer=false;
	}
}
class Elsodleges_M {
	constructor() {
		this.historic=undefined;
		this.isDimmer=false;
	}
}
class Elsodleges_P {
	constructor() {
		this.historic=undefined;
		this.isDimmer=false;
	}
}
class Elsodleges_E {
	constructor() {
		this.historic=undefined;
		this.isDimmer=false;
	}
}
class Elsodleges_H {
	constructor() {
		this.historic=undefined;
		this.isDimmer=false;
	}
}
class Masodlagos_F {
	constructor() {
		this.historic=undefined;
		this.isDimmer=false;
	}
}
class Masodlagos_M {
	constructor() {
		this.historic=undefined;
		this.isDimmer=false;
	}
}
class Masodlagos_P {
	constructor() {
		this.historic=undefined;
		this.isDimmer=false;
	}
}
class Masodlagos_E {
	constructor() {
		this.historic=undefined;
		this.isDimmer=false;
	}
}
class Masodlagos_H {
	constructor() {
		this.historic=undefined;
		this.isDimmer=false;
	}
}
Date.prototype.yyyymmdd_hhmm = function() {
	var month = this.getMonth() + 1;
	var day = this.getDate();
	var hour = this.getHours();
	var minute = this.getMinutes();

	return [this.getFullYear(),
		(month > 9 ? '' : '0') + month,
		(day > 9 ? '' : '0') + day,
		'_',
		(hour > 9 ? '' : '0') + hour,
		(minute > 9 ? '' : '0') + minute
	].join('');
	};

function Elsodleges_PE() {
	this.historic = [];
}

function Masodlagos_PE() {
	this.historic = [];
}

function getRequestPelsodleges(name){
	var req = location.search;
	if(req.length == 0) {
		req = location.href;
	}
	var match = (new RegExp('[?&]' + encodeURIComponent(name) + '=([^&]*)')).exec(req);
	if (match) {
		return decodeURIComponent(match[1]);
	}
	return undefined;
}

function getThermostats() {
	nodata = true;
	var request=proto+address + ":" + port.toString() + hardwareReq;
	var thermostats = [];
	$.ajax({url: request,
		async: false,
		success: function(result){
			for(i=0;i<result.result.length;i++) {
				if(result.result[i].Extra == "DSVT_HMV_ZONE_12" && result.result[i].Enabled == "true") {
					nodata = false;
					var regExpF = /(F:|,|^)(\d+)/g;
					var regExpM = /(M:)(\d+)/g;
					var regExpH = /(H:)(\d+)/g;
					var thermostat = new DSVT_HMV_ZONE_12_Thermostat();
					var name = result.result[i].Name;
					thermostat.name = name;
					thermostat.id = result.result[i].idx;
					var minDate = 0;
					var innerRequest = proto + address + ":" + port.toString() + devicesReq;
					$.ajax({
						url: innerRequest,
						async: false,
						success: function (resultMode) {
							thermostat.host = result.result[i].Address
							thermostat.uname = result.result[i].Username
							thermostat.pass = result.result[i].Password
							thermostat.port = result.result[i].Port
							thermostat.Mode1 = result.result[i].Mode1;
							thermostat.Mode2 = result.result[i].Mode2;
							thermostat.Mode3 = result.result[i].Mode3;
							thermostat.Mode4 = result.result[i].Mode4;
							thermostat.Mode5 = result.result[i].Mode5;
							thermostat.Mode6 = result.result[i].Mode6;
							//console.log(thermostat.Mode1);
							//console.log(thermostat.Mode2);
							//console.log(thermostat.Mode3);
							//console.log(thermostat.Mode4);
							//console.log(thermostat.Mode5);
							//console.log(thermostat.Mode6);
						}
					});
					thermostat.dayname = [
						"Monday:0",
						"Tuesday:1",
						"Wednesday:2",
						"Thursday:3",
						"Friday:4",
						"Saturday:5",
						"Sunday:6"
					];

					const elemek = (thermostat.Mode1 || "").split(",");

					for (let i = 0; i < elemek.length; i++) {
						const [kulcs, ertek] = (elemek[i] || "").split(":");
						if (kulcs.startsWith("Z_")) {
							const infoUrl = proto + address + ":" + port.toString() + "type=command&param=getdevices&rid=" + ertek;

							$.ajax({
								url: infoUrl,
								async: false,
								success: function(info) {
									if (!info || !info.result || !info.result[0]) return;

									// Eszköznév normalizálása (ékezetek nélkül, kisbetűvel, szóköz helyett _)
									const nev = info.result[0].Name
										.normalize("NFD")
										.replace(/[\u0300-\u036f]/g, "")
										.replace(/\s+/g, "_")
										.toLowerCase();

									const tempUrl = proto + address + ":" + port.toString() + tempReq + ertek;

									$.ajax({
										url: tempUrl,
										async: false,
										success: function(resultZoneTemp) {
											if (!resultZoneTemp || !Array.isArray(resultZoneTemp.result)) return;

											const prop = "zonetemp_" + kulcs + "_" + nev;
											thermostat[prop] = resultZoneTemp.result; // közvetlenül a thermostat-hoz

											// mint a többi listaelem
											if (!Array.isArray(thermostat.zonetemp)) thermostat.zonetemp = [];
											thermostat.zonetemp.push(ertek + ":" + nev);

											//console.log(kulcs, "→ idx:", ertek, "→ nev:", nev);
										}
									});
								}
							});
						}
					}


					request = proto + address + ":" + port.toString() + devicesReq;
					$.ajax({
						url: request,
						async: false,
						success: function (resultAktName) {
							thermostat.aktname = []; 
							resultAktName.result.forEach(function (item) {
								thermostat.aktname.push(item.Unit + ':' + item.Name + ':' + item.idx);
							});
							//console.log(resultAktName);
							//console.log(thermostat.aktname);
						}
					});
					request = proto + address + ":" + port.toString() + tempName;
					$.ajax({
						url: request,
						async: false,
						success: function (resultTempName) {
							thermostat.tempnameakt = []; 
							resultTempName.result.forEach(function (item) {
								if (
									item.Type.toLowerCase().includes('temp') &&
									item.Used === 1 &&
									(
										item.HardwareName.toLowerCase().includes('dummy') ||
										item.HardwareName.toLowerCase().includes('zigbee')
									)
								) {
									thermostat.tempnameakt.push(item.Unit + ':' + item.Name + ':' + item.idx);
								}
							});
							//console.log(resultTempName);
							//console.log(thermostat.tempnameakt);
						}
					});
					request = proto + address + ":" + port.toString() + switchName;
					$.ajax({
						url: request,
						async: false,
						success: function (resultswitchName) {
							thermostat.switchnameakt = [];
							resultswitchName.result.forEach(function (item) {
								if (
										item.SwitchType &&
										item.SwitchType.toLowerCase().includes('on/off') &&
										item.Used == 1
								) {
									thermostat.switchnameakt.push(item.Unit + ':' + item.Name + ':' + item.idx);
								}
							});
							//console.log(resultswitchName);
							//console.log(thermostat.switchnameakt);
						}
					});
					request = proto + address + ":" + port.toString() + devicesReq;
					$.ajax({
						url: request,
						async: false,
						success: function (resultSetPointhName) {
							thermostat.setpointnameakt = [];
							resultSetPointhName.result.forEach(function (item) {
								if (
									item.SubType.toLowerCase().includes('setpoint') &&
									thermostat.id == item.HardwareID
								) {
									thermostat.setpointnameakt.push(item.Unit + ':' + item.Name + ':' + item.idx + ':' + item.SetPoint);
								}
							});
							//console.log(resultSetPointhName);
							//console.log(thermostat.setpointnameakt);
						}
					});
					request = proto + address + ":" + port.toString() + devicesReq;
					$.ajax({
						url: request,
						async: false,
						success: function (resultConsoleName) {
							thermostat.consolenameakt = [];
							resultConsoleName.result.forEach(function (item) {
								if (
									item.Type.toLowerCase().includes('Thermostat') &&
									thermostat.id != item.HardwareID
								) {
									thermostat.consolenameakt.push(item.Unit + ':' + item.Name + ':' + item.idx + ':' + item.SetPoint);
								}
							});
							//console.log(resultConsoleName);
							//console.log(thermostat.consolenameakt);
						}
					});
					request = proto + address + ":" + port.toString() + devicesReq;
					$.ajax({
						url: request,
						async: false,
						success: function (resultTRVName) {
							thermostat.trvnameakt = [];
							resultTRVName.result.forEach(function (item) {
								if (
									item.SubType &&
										item.SubType.toLowerCase().includes('setpoint') &&
										item.HardwareName &&
										item.HardwareName.toLowerCase().includes('zigbee')
								) {
									thermostat.trvnameakt.push(item.Unit + ':' + item.Name + ':' + item.idx);
								}
							});
							//console.log(resultTRVName);
							//console.log(thermostat.trvnameakt);
						}
					});
					request = proto + address + ":" + port.toString() + devicesReq;
					$.ajax({
						url: request,
						async: false, // (tudom: blokkol, de ha így kell maradjon)
						success: function (res) {
							thermostat.doornameakt = [];
							if (!res || !res.result) return;

							res.result.forEach(function (item) {
								const type = (item.SwitchType || "").toLowerCase();

								// Fogja: "door", "door lock", "contact", "door sensor", stb.
								if (type.includes("door") || type.includes("contact") || type.includes("lock")) {
									thermostat.doornameakt.push(`${item.Unit}:${item.Name}:${item.idx}`);
								}
							});
							// console.log(thermostat.doornameakt);
						}
					});
					request=proto+address + ":" + port.toString() + devicesReq;
					$.ajax({url: request,
						async: false,
						success: function(resultDevice){
							for(var j=0;j<resultDevice.result.length;j++) {
								if(thermostat.id == resultDevice.result[j].HardwareID && resultDevice.result[j].Unit == 6 && resultDevice.result[j].Used == 1) {
									var request=proto+address + ":" + port.toString() + tempReq + resultDevice.result[j].idx;
									$.ajax({url: request,
										async: false,
										success: function(resultTempIn){
											if (!resultTempIn.result || !Array.isArray(resultTempIn.result)) {
												//console.error("Hibás vagy üres válasz:", resultTempIn);
												return;
											}
											//console.log(resultTempIn);
											thermostat.TempIn = resultTempIn.result;
											minDate = Math.min.apply(null,
												resultTempIn.result.map(function (item) {
													return new Date(item.d);
												})
											);
										}
									});
								}
							}
							for(var j=0;j<resultDevice.result.length;j++) {
								if(thermostat.id == resultDevice.result[j].HardwareID && resultDevice.result[j].Unit == 69 && resultDevice.result[j].Used == 1) {
									var request=proto+address + ":" + port.toString() + tempReq + resultDevice.result[j].idx;
									$.ajax({url: request,
										async: false,
										success: function(resultTempOut){
											if (!resultTempOut.result || !Array.isArray(resultTempOut.result)) {
												//console.error("Hibás vagy üres válasz:", resultTempOut);
												return;
											}
											//console.log(resultTempOut);
											thermostat.tempOut = resultTempOut.result;
											minDate = Math.min.apply(null,
												resultTempOut.result.map(function (item) {
													return new Date(item.d);
												})
											);
										}
									});
								}
							}
							for(var j=0;j<resultDevice.result.length;j++) {
								if(thermostat.id == resultDevice.result[j].HardwareID && resultDevice.result[j].Unit == 72 && resultDevice.result[j].Used == 1) {
									var request=proto+address + ":" + port.toString() + tempReq + resultDevice.result[j].idx;
									$.ajax({url: request,
										async: false,
										success: function(resultKevero_1_temp){
											if (!resultKevero_1_temp || !Array.isArray(resultKevero_1_temp.result)) {
												//console.error("Hibás vagy üres válasz:", resultKevero_1_temp);
												return;
											}
											//console.log(resultKevero_1_temp);
											thermostat.Kevero_1_temp = resultKevero_1_temp.result;
											minDate = Math.min.apply(null,
												resultKevero_1_temp.result.map(function (item) {
													return new Date(item.d);
												})
											);
										}
									});
								}
							}
							for(var j=0;j<resultDevice.result.length;j++) {
								if(thermostat.id == resultDevice.result[j].HardwareID && resultDevice.result[j].Unit == 73 && resultDevice.result[j].Used == 1) {
									var request=proto+address + ":" + port.toString() + tempReq + resultDevice.result[j].idx;
									$.ajax({url: request,
										async: false,
										success: function(resultKevero_2_temp){
											if (!resultKevero_2_temp || !Array.isArray(resultKevero_2_temp.result)) {
												//console.error("Hibás vagy üres válasz:", resultKevero_2_temp);
												return;
											}
											//console.log(resultKevero_2_temp);
											thermostat.Kevero_2_temp = resultKevero_2_temp.result;
											minDate = Math.min.apply(null,
												resultKevero_2_temp.result.map(function (item) {
													return new Date(item.d);
												})
											);
										}
									});
								}
							}
							for(var j=0;j<resultDevice.result.length;j++) {
								if(thermostat.id == resultDevice.result[j].HardwareID && resultDevice.result[j].Unit == 19 && resultDevice.result[j].Used == 1) {
									var request=proto+address + ":" + port.toString() + tempReq + resultDevice.result[j].idx;
									$.ajax({url: request,
										async: false,
										success: function(resulttempTartaly){
											if (!resulttempTartaly || !Array.isArray(resulttempTartaly.result)) {
												//console.error("Hibás vagy üres válasz:", resulttempTartaly);
												return;
											}
											//console.log(resulttempTartaly);
											thermostat.tempTartaly = resulttempTartaly.result;
											minDate = Math.min.apply(null,
												resulttempTartaly.result.map(function (item) {
													return new Date(item.d);
												})
											);
										}
									});
								}
							}
							for(var j=0;j<resultDevice.result.length;j++) {
								if(thermostat.id == resultDevice.result[j].HardwareID && resultDevice.result[j].Unit == 97) {
									var request=proto+address + ":" + port.toString() + tempReq + resultDevice.result[j].idx;
									$.ajax({url: request,
										async: false,
										success: function(resulttempOutdew){
											if (!resulttempOutdew || !Array.isArray(resulttempOutdew.result)) {
												//console.error("Hibás vagy üres válasz:", resulttempOutdew);
												return;
											}
											//console.log(resulttempOutdew);
											thermostat.tempOutdew = resulttempOutdew.result;
											minDate = Math.min.apply(null,
												resulttempOutdew.result.map(function (item) {
													return new Date(item.d);
												})
											);
										}
									});
								}
							}
							for(var j=0;j<resultDevice.result.length;j++) {
								if(thermostat.id == resultDevice.result[j].HardwareID && resultDevice.result[j].Unit == 157) {
									var request=proto+address + ":" + port.toString() + tempReq + resultDevice.result[j].idx;
									$.ajax({url: request,
										async: false,
										success: function(resulttempIntdew){
											if (!resulttempIntdew || !Array.isArray(resulttempIntdew.result)) {
												//console.error("Hibás vagy üres válasz:", resulttempIntdew);
												return;
											}
											//console.log(resulttempIntdew);
											thermostat.tempIntdew = resulttempIntdew.result;
											minDate = Math.min.apply(null,
												resulttempIntdew.result.map(function (item) {
													return new Date(item.d);
												})
											);
										}
									});
								}
							}




							for(var j=0;j<resultDevice.result.length;j++) {
								if(thermostat.id == resultDevice.result[j].HardwareID && resultDevice.result[j].Unit == 23) {
									request=proto+address + ":" + port.toString() + switchReq + resultDevice.result[j].idx;
									$.ajax({url: request,
										async: false,
										success: function(resultElsodleges_F){
											if (!resultElsodleges_F || !Array.isArray(resultElsodleges_F.result)) {
												//console.error("Hibás vagy üres válasz:", resultElsodleges_F);
												return;
											}
											//console.log(resultElsodleges_F);
											thermostat.Elsodleges_F = new Elsodleges_F();
											if (typeof(resultElsodleges_F.result) != "undefined") {
												thermostat.Elsodleges_F.historic = resultElsodleges_F.result.filter(item => new Date(item.Date).getTime() >= minDate).sort((a,b)=>new Date(a.Date).getTime()>new Date(b.Date).getTime());
												
												lastState = resultElsodleges_F.result.sort((a, b) => new Date(a.Date).getTime() - new Date(b.Date).getTime()).slice(-1)[0]; 
												lastStateDate = new Date(lastState.Date).getTime();
												
												if (lastStateDate < minDate && lastState.Status === "On") {
													minDateState = { ...lastState, Date: new Date(minDate).toISOString() };
													thermostat.Elsodleges_F.historic.unshift(minDateState);
													currentTime = Date.now();
													currentState = { ...lastState, Date: new Date(currentTime).toISOString() };
													thermostat.Elsodleges_F.historic.push(currentState);
												}

											} else {
												thermostat.Elsodleges_F.historic = "";
											}
										}
									});
								}
							}
							for(var j=0;j<resultDevice.result.length;j++) {
								if(thermostat.id == resultDevice.result[j].HardwareID && resultDevice.result[j].Unit == 26) {
									request=proto+address + ":" + port.toString() + switchReq + resultDevice.result[j].idx;
									$.ajax({url: request,
										async: false,
										success: function(resultMasodlagos_F){
											if (!resultMasodlagos_F || !Array.isArray(resultMasodlagos_F.result)) {
												//console.error("Hibás vagy üres válasz:", resultMasodlagos_F);
												return;
											}
											//console.log(resultMasodlagos_F);
											thermostat.Masodlagos_F = new Masodlagos_F();
											if (typeof(resultMasodlagos_F.result) != "undefined") {
												thermostat.Masodlagos_F.historic = resultMasodlagos_F.result.filter(item => new Date(item.Date).getTime() >= minDate).sort((a,b)=>new Date(a.Date).getTime()>new Date(b.Date).getTime());
												
												lastState = resultMasodlagos_F.result.sort((a, b) => new Date(a.Date).getTime() - new Date(b.Date).getTime()).slice(-1)[0]; 
												lastStateDate = new Date(lastState.Date).getTime();
												
												if (lastStateDate < minDate && lastState.Status === "On") {
													minDateState = { ...lastState, Date: new Date(minDate).toISOString() };
													thermostat.Masodlagos_F.historic.unshift(minDateState);
													currentTime = Date.now();
													currentState = { ...lastState, Date: new Date(currentTime).toISOString() };
													thermostat.Masodlagos_F.historic.push(currentState);
												}

											} else {
												thermostat.Masodlagos_F.historic = "";
											}
										}
									});
								}
							}
							for(var j=0;j<resultDevice.result.length;j++) {
								if(thermostat.id == resultDevice.result[j].HardwareID && resultDevice.result[j].Unit == 25) {
									request=proto+address + ":" + port.toString() + switchReq + resultDevice.result[j].idx;
									$.ajax({url: request,
										async: false,
										success: function(resultElsodleges_H){
											if (!resultElsodleges_H || !Array.isArray(resultElsodleges_H.result)) {
												//console.error("Hibás vagy üres válasz:", resultElsodleges_H);
												return;
											}
											//console.log(resultElsodleges_H);
											thermostat.Elsodleges_H = new Elsodleges_H();
											if (typeof(resultElsodleges_H.result) != "undefined") {
												thermostat.Elsodleges_H.historic = resultElsodleges_H.result.filter(item => new Date(item.Date).getTime() >= minDate).sort((a,b)=>new Date(a.Date).getTime()>new Date(b.Date).getTime());
												
												lastState = resultElsodleges_H.result.sort((a, b) => new Date(a.Date).getTime() - new Date(b.Date).getTime()).slice(-1)[0]; 
												lastStateDate = new Date(lastState.Date).getTime();
												
												if (lastStateDate < minDate && lastState.Status === "On") {
													minDateState = { ...lastState, Date: new Date(minDate).toISOString() };
													thermostat.Elsodleges_H.historic.unshift(minDateState);
													currentTime = Date.now();
													currentState = { ...lastState, Date: new Date(currentTime).toISOString() };
													thermostat.Elsodleges_H.historic.push(currentState);
												}
											
											} else {
												thermostat.Elsodleges_H.historic = "";
											}
										}
									});
								}
							}
							for(var j=0;j<resultDevice.result.length;j++) {
								if(thermostat.id == resultDevice.result[j].HardwareID && resultDevice.result[j].Unit == 28) {
									request=proto+address + ":" + port.toString() + switchReq + resultDevice.result[j].idx;
									$.ajax({url: request,
										async: false,
										success: function(resultMasodlagos_H){
											if (!resultMasodlagos_H || !Array.isArray(resultMasodlagos_H.result)) {
												//console.error("Hibás vagy üres válasz:", resultMasodlagos_H);
												return;
											}
											//console.log(resultMasodlagos_H);
											thermostat.Masodlagos_H = new Masodlagos_H();
											if (typeof(resultMasodlagos_H.result) != "undefined") {
												thermostat.Masodlagos_H.historic = resultMasodlagos_H.result.filter(item => new Date(item.Date).getTime() >= minDate).sort((a,b)=>new Date(a.Date).getTime()>new Date(b.Date).getTime());
											
												lastState = resultMasodlagos_H.result.sort((a, b) => new Date(a.Date).getTime() - new Date(b.Date).getTime()).slice(-1)[0]; 
												lastStateDate = new Date(lastState.Date).getTime();
												
												if (lastStateDate < minDate && lastState.Status === "On") {
													minDateState = { ...lastState, Date: new Date(minDate).toISOString() };
													thermostat.Masodlagos_H.historic.unshift(minDateState);
													currentTime = Date.now();
													currentState = { ...lastState, Date: new Date(currentTime).toISOString() };
													thermostat.Masodlagos_H.historic.push(currentState);
												}
											
											} else {
												thermostat.Masodlagos_H.historic = "";
											}
										}
									});
								}
							}
							for(var j=0;j<resultDevice.result.length;j++) {
								if(thermostat.id == resultDevice.result[j].HardwareID && resultDevice.result[j].Unit == 24) {
									request=proto+address + ":" + port.toString() + switchReq + resultDevice.result[j].idx;
									$.ajax({url: request,
										async: false,
										success: function(resultElsodleges_M){
											if (!resultElsodleges_M || !Array.isArray(resultElsodleges_M.result)) {
												//console.error("Hibás vagy üres válasz:", resultElsodleges_M);
												return;
											}
											//console.log(resultElsodleges_M);
											thermostat.Elsodleges_M = new Elsodleges_M();
											if (typeof(resultElsodleges_M.result) != "undefined") {
												thermostat.Elsodleges_M.historic = resultElsodleges_M.result.filter(item => new Date(item.Date).getTime() >= minDate).sort((a,b)=>new Date(a.Date).getTime()>new Date(b.Date).getTime());
											
												lastState = resultElsodleges_M.result.sort((a, b) => new Date(a.Date).getTime() - new Date(b.Date).getTime()).slice(-1)[0]; 
												lastStateDate = new Date(lastState.Date).getTime();
												
												if (lastStateDate < minDate && lastState.Status === "On") {
													minDateState = { ...lastState, Date: new Date(minDate).toISOString() };
													thermostat.Elsodleges_M.historic.unshift(minDateState);
													currentTime = Date.now();
													currentState = { ...lastState, Date: new Date(currentTime).toISOString() };
													thermostat.Elsodleges_M.historic.push(currentState);
												}
											
											} else {
												thermostat.Elsodleges_M.historic = "";
											}
										}
									});
								}
							}
							for(var j=0;j<resultDevice.result.length;j++) {
								if(thermostat.id == resultDevice.result[j].HardwareID && resultDevice.result[j].Unit == 27) {
									request=proto+address + ":" + port.toString() + switchReq + resultDevice.result[j].idx;
									$.ajax({url: request,
										async: false,
										success: function(resultMasodlagos_M){
											if (!resultMasodlagos_M || !Array.isArray(resultMasodlagos_M.result)) {
												//console.error("Hibás vagy üres válasz:", resultMasodlagos_M);
												return;
											}
											//console.log(resultMasodlagos_M);
											thermostat.Masodlagos_M = new Masodlagos_M();
											if (typeof(resultMasodlagos_M.result) != "undefined") {
												thermostat.Masodlagos_M.historic = resultMasodlagos_M.result.filter(item => new Date(item.Date).getTime() >= minDate).sort((a,b)=>new Date(a.Date).getTime()>new Date(b.Date).getTime());
											
												lastState = resultMasodlagos_M.result.sort((a, b) => new Date(a.Date).getTime() - new Date(b.Date).getTime()).slice(-1)[0]; 
												lastStateDate = new Date(lastState.Date).getTime();
												
												if (lastStateDate < minDate && lastState.Status === "On") {
													minDateState = { ...lastState, Date: new Date(minDate).toISOString() };
													thermostat.Masodlagos_M.historic.unshift(minDateState);
													currentTime = Date.now();
													currentState = { ...lastState, Date: new Date(currentTime).toISOString() };
													thermostat.Masodlagos_M.historic.push(currentState);
												}
											
											} else {
												thermostat.Masodlagos_M.historic = "";
											}
										}
									});
								}
							}

							for(var j=0;j<resultDevice.result.length;j++) {
								if(thermostat.id == resultDevice.result[j].HardwareID && resultDevice.result[j].Unit == 102) {
									request=proto+address + ":" + port.toString() + switchReq + resultDevice.result[j].idx;
									$.ajax({url: request,
										async: false,
										success: function(resultElsodleges_P){
											if (!resultElsodleges_P || !Array.isArray(resultElsodleges_P.result)) {
												//console.error("Hibás vagy üres válasz:", resultElsodleges_P);
												return;
											}
											//console.log(resultElsodleges_P);
											thermostat.Elsodleges_P = new Elsodleges_P();
											if (typeof(resultElsodleges_P.result) != "undefined") {
												thermostat.Elsodleges_P.historic = resultElsodleges_P.result.filter(item => new Date(item.Date).getTime() >= minDate).sort((a,b)=>new Date(a.Date).getTime()>new Date(b.Date).getTime());
											
												lastState = resultElsodleges_P.result.sort((a, b) => new Date(a.Date).getTime() - new Date(b.Date).getTime()).slice(-1)[0]; 
												lastStateDate = new Date(lastState.Date).getTime();
												
												if (lastStateDate < minDate && lastState.Status === "On") {
													minDateState = { ...lastState, Date: new Date(minDate).toISOString() };
													thermostat.Elsodleges_P.historic.unshift(minDateState);
													currentTime = Date.now();
													currentState = { ...lastState, Date: new Date(currentTime).toISOString() };
													thermostat.Elsodleges_P.historic.push(currentState);
												}
											
											} else {
												thermostat.Elsodleges_P.historic = "";
											}
										}
									});
								}
							}
							for(var j=0;j<resultDevice.result.length;j++) {
								if(thermostat.id == resultDevice.result[j].HardwareID && resultDevice.result[j].Unit == 103) {
									request=proto+address + ":" + port.toString() + switchReq + resultDevice.result[j].idx;
									$.ajax({url: request,
										async: false,
										success: function(resultMasodlagos_P){
											if (!resultMasodlagos_P || !Array.isArray(resultMasodlagos_P.result)) {
												//console.error("Hibás vagy üres válasz:", resultMasodlagos_P);
												return;
											}
											//console.log(resultMasodlagos_P);
											thermostat.Masodlagos_P = new Masodlagos_P();
											if (typeof(resultMasodlagos_P.result) != "undefined") {
												thermostat.Masodlagos_P.historic = resultMasodlagos_P.result.filter(item => new Date(item.Date).getTime() >= minDate).sort((a,b)=>new Date(a.Date).getTime()>new Date(b.Date).getTime());
											
												lastState = resultMasodlagos_P.result.sort((a, b) => new Date(a.Date).getTime() - new Date(b.Date).getTime()).slice(-1)[0]; 
												lastStateDate = new Date(lastState.Date).getTime();
												
												if (lastStateDate < minDate && lastState.Status === "On") {
													minDateState = { ...lastState, Date: new Date(minDate).toISOString() };
													thermostat.Masodlagos_P.historic.unshift(minDateState);
													currentTime = Date.now();
													currentState = { ...lastState, Date: new Date(currentTime).toISOString() };
													thermostat.Masodlagos_P.historic.push(currentState);
												}
											
											} else {
												thermostat.Masodlagos_P.historic = "";
											}
										}
									});
								}
							}
							for(var j=0;j<resultDevice.result.length;j++) {
								if(thermostat.id == resultDevice.result[j].HardwareID && resultDevice.result[j].Unit == 33) {
									request=proto+address + ":" + port.toString() + switchReq + resultDevice.result[j].idx;
									$.ajax({url: request,
										async: false,
										success: function(resultElsodleges_E){
											if (!resultElsodleges_E || !Array.isArray(resultElsodleges_E.result)) {
												//console.error("Hibás vagy üres válasz:", resultElsodleges_E);
												return;
											}
											//console.log(resultElsodleges_E);
											thermostat.Elsodleges_E = new Elsodleges_E();
											if (typeof(resultElsodleges_E.result) != "undefined") {
												thermostat.Elsodleges_E.historic = resultElsodleges_E.result.filter(item => new Date(item.Date).getTime() >= minDate).sort((a,b)=>new Date(a.Date).getTime()>new Date(b.Date).getTime());
											
												lastState = resultElsodleges_E.result.sort((a, b) => new Date(a.Date).getTime() - new Date(b.Date).getTime()).slice(-1)[0]; 
												lastStateDate = new Date(lastState.Date).getTime();
												
												if (lastStateDate < minDate && lastState.Status === "On") {
													minDateState = { ...lastState, Date: new Date(minDate).toISOString() };
													thermostat.Elsodleges_E.historic.unshift(minDateState);
													currentTime = Date.now();
													currentState = { ...lastState, Date: new Date(currentTime).toISOString() };
													thermostat.Elsodleges_E.historic.push(currentState);
												}
											
											} else {
												thermostat.Elsodleges_E.historic = "";
											}
										}
									});
								}
							}
							for(var j=0;j<resultDevice.result.length;j++) {
								if(thermostat.id == resultDevice.result[j].HardwareID && resultDevice.result[j].Unit == 34) {
									request=proto+address + ":" + port.toString() + switchReq + resultDevice.result[j].idx;
									$.ajax({url: request,
										async: false,
										success: function(resultMasodlagos_E){
											if (!resultMasodlagos_E || !Array.isArray(resultMasodlagos_E.result)) {
												//console.error("Hibás vagy üres válasz:", resultMasodlagos_E);
												return;
											}
											//console.log(resultMasodlagos_E);
											thermostat.Masodlagos_E = new Masodlagos_E();
											if (typeof(resultMasodlagos_E.result) != "undefined") {
												thermostat.Masodlagos_E.historic = resultMasodlagos_E.result.filter(item => new Date(item.Date).getTime() >= minDate).sort((a,b)=>new Date(a.Date).getTime()>new Date(b.Date).getTime());
											
												lastState = resultMasodlagos_E.result.sort((a, b) => new Date(a.Date).getTime() - new Date(b.Date).getTime()).slice(-1)[0]; 
												lastStateDate = new Date(lastState.Date).getTime();
												
												if (lastStateDate < minDate && lastState.Status === "On") {
													minDateState = { ...lastState, Date: new Date(minDate).toISOString() };
													thermostat.Masodlagos_E.historic.unshift(minDateState);
													currentTime = Date.now();
													currentState = { ...lastState, Date: new Date(currentTime).toISOString() };
													thermostat.Masodlagos_E.historic.push(currentState);
												}
											
											} else {
												thermostat.Masodlagos_E.historic = "";
											}
										}
									});
								}
							}
							for(var j=0;j<resultDevice.result.length;j++) {
								if(thermostat.id == resultDevice.result[j].HardwareID && resultDevice.result[j].Unit == 160) {
									request=proto+address + ":" + port.toString() + switchReq + resultDevice.result[j].idx;
									$.ajax({url: request,
										async: false,
										success: function(resultElsodleges_PE){
											if (!resultElsodleges_PE || !Array.isArray(resultElsodleges_PE.result)) {
												//console.error("Hibás vagy üres válasz:", resultElsodleges_PE);
												return;
											}
											//console.log(resultElsodleges_PE);
											thermostat.Elsodleges_PE = new Elsodleges_PE();
											if (typeof(resultElsodleges_PE.result) != "undefined") {
												thermostat.Elsodleges_PE.historic = resultElsodleges_PE.result.filter(item => new Date(item.Date).getTime() >= minDate).sort((a,b)=>new Date(a.Date).getTime()>new Date(b.Date).getTime());
											
												lastState = resultElsodleges_PE.result.sort((a, b) => new Date(a.Date).getTime() - new Date(b.Date).getTime()).slice(-1)[0]; 
												lastStateDate = new Date(lastState.Date).getTime();
												
												if (lastStateDate < minDate && lastState.Status === "On") {
													minDateState = { ...lastState, Date: new Date(minDate).toISOString() };
													thermostat.Elsodleges_PE.historic.unshift(minDateState);
													currentTime = Date.now();
													currentState = { ...lastState, Date: new Date(currentTime).toISOString() };
													thermostat.Elsodleges_PE.historic.push(currentState);
												}
											
											} else {
												thermostat.Elsodleges_PE.historic = "";
											}
										}
									});
								}
							}
							for(var j=0;j<resultDevice.result.length;j++) {
								if(thermostat.id == resultDevice.result[j].HardwareID && resultDevice.result[j].Unit == 161) {
									request=proto+address + ":" + port.toString() + switchReq + resultDevice.result[j].idx;
									$.ajax({url: request,
										async: false,
										success: function(resultMasodlagos_PE){
											if (!resultMasodlagos_PE || !Array.isArray(resultMasodlagos_PE.result)) {
												//console.error("Hibás vagy üres válasz:", resultMasodlagos_PE);
												return;
											}
											//console.log(resultMasodlagos_PE);
											thermostat.Masodlagos_PE = new Masodlagos_PE();
											if (typeof(resultMasodlagos_PE.result) != "undefined") {
												thermostat.Masodlagos_PE.historic = resultMasodlagos_PE.result.filter(item => new Date(item.Date).getTime() >= minDate).sort((a,b)=>new Date(a.Date).getTime()>new Date(b.Date).getTime());
											
												lastState = resultMasodlagos_PE.result.sort((a, b) => new Date(a.Date).getTime() - new Date(b.Date).getTime()).slice(-1)[0]; 
												lastStateDate = new Date(lastState.Date).getTime();
												
												if (lastStateDate < minDate && lastState.Status === "On") {
													minDateState = { ...lastState, Date: new Date(minDate).toISOString() };
													thermostat.Masodlagos_PE.historic.unshift(minDateState);
													currentTime = Date.now();
													currentState = { ...lastState, Date: new Date(currentTime).toISOString() };
													thermostat.Masodlagos_PE.historic.push(currentState);
												}
											
											} else {
												thermostat.Masodlagos_PE.historic = "";
											}
										}
									});
								}
							}
						}
					});
					request = proto + address + ":" + port.toString() + userVarReq;
					$.ajax({
						url: request,
						async: false,
						success: function (resultVars) {
							thermostat.acValues = {};
							resultVars.result.forEach(function (item) {
								if (
									item.Name.startsWith(`${name}`) &&
									item.Name.includes("_AC_")
								) {
									try {
										const regex = /_Z_(\d+)_AC_(F|H)$/;
										const match = item.Name.match(regex);
										if (!match) return;
										const zoneId = parseInt(match[1], 10); // "1"
										const acType = match[2]; // "F" vagy "H"
										var fixed = item.Value
											.replace(/'/g, '"')
											.replace(/\bNone\b/g, 'null')
											.replace(/\bTrue\b/g, 'true')
											.replace(/\bFalse\b/g, 'false');
										var parsed = JSON.parse(fixed);
										if (!thermostat.acValues[zoneId]) {
											thermostat.acValues[zoneId] = {};
										}
										thermostat.acValues[zoneId][acType] = parsed;
									} catch (e) {
										console.warn("Hibás JSON user variable: " + item.Name + " = " + item.Value);
									}
								}
							});
						}
					});
					// Kilistázzuk a klíma adatokat a táblázathoz
					let klimaTabla = [];
					for (let z = 1; z <= 12; z++) {
						["F", "H"].forEach(function (tipus) {
							let adat = thermostat.acValues[z]?.[tipus]; // mivel zoneId szám volt, itt is szám a kulcs

							klimaTabla.push({
								zona: z,
								tipus: tipus,
								type: adat?.type && adat.type !== "" && adat.type !== "-" ? adat.type : "nincs",
								IP: adat?.IP && adat.IP !== "" && adat.IP !== "nincs" ? adat.IP : "nincs",
								fanspeed: (adat?.fanspeed ?? "nincs"),
								swingv: (adat?.swingv ?? "nincs"),
								swingh: (adat?.swingh ?? "nincs"),
								komp: (adat?.komp ?? 0),
								hatar_low: (adat?.hatar_low ?? 0),
								hatar_top: (adat?.hatar_top ?? 0),
								target_off: (adat?.target_off ?? false),
								AC_jelenlet: adat?.AC_jelenlet ?? "None"
							});
						});
					}
					thermostat.klimatabla = klimaTabla;
					//console.table(klimaTabla);
					request=proto+address + ":" + port.toString() + devicesReq;
					$.ajax({url: request,
						async: false,
						success: function(resultTemp){
							for(var j=0;j<resultTemp.result.length;j++) {
								if(thermostat.id == resultTemp.result[j].HardwareID && resultTemp.result[j].Unit == 10 && resultTemp.result[j].Used == 1) {
									request=proto+address + ":" + port.toString() + tempReq + resultTemp.result[j].idx;
									$.ajax({url: request,
										async: false,
										success: function(resultTemp){
											//console.log(resultTemp);
											thermostat.Fsetpoint = resultTemp.result;
										}
									});
								}
								if(thermostat.id == resultTemp.result[j].HardwareID && resultTemp.result[j].Unit == 20 && resultTemp.result[j].Used == 1) {
									request=proto+address + ":" + port.toString() + tempReq + resultTemp.result[j].idx;
									$.ajax({url: request,
										async: false,
										success: function(resultTemp){
											//console.log(resultTemp);
											thermostat.Hsetpoint = resultTemp.result;
										}
									});
								}
								if(thermostat.id == resultTemp.result[j].HardwareID && resultTemp.result[j].Unit == 21 && resultTemp.result[j].Used == 1) {
									request=proto+address + ":" + port.toString() + tempReq + resultTemp.result[j].idx;
									$.ajax({url: request,
										async: false,
										success: function(resultTemp){
											//console.log(resultTemp);
											thermostat.Msetpoint = resultTemp.result;
										}
									});
								}
								if(thermostat.id == resultTemp.result[j].HardwareID && resultTemp.result[j].Unit == 100 && resultTemp.result[j].Used == 1) {
									request=proto+address + ":" + port.toString() + tempReq + resultTemp.result[j].idx;
									$.ajax({url: request,
										async: false,
										success: function(resultTemp){
											//console.log(resultTemp);
											thermostat.Psetpoint = resultTemp.result;
										}
									});
								}
								if(thermostat.id == resultTemp.result[j].HardwareID && resultTemp.result[j].Unit == 154 && resultTemp.result[j].Used == 1) {
									request=proto+address + ":" + port.toString() + tempReq + resultTemp.result[j].idx;
									$.ajax({url: request,
										async: false,
										success: function(resultTemp){
											//console.log(resultTemp);
											thermostat.hiszterezis = resultTemp.result;
										}
									});
								}
								if(thermostat.id == resultTemp.result[j].HardwareID && resultTemp.result[j].Unit == 158 && resultTemp.result[j].Used == 1) {
									request=proto+address + ":" + port.toString() + tempReq + resultTemp.result[j].idx;
									$.ajax({url: request,
										async: false,
										success: function(resultTemp){
											//console.log(resultTemp);
											thermostat.aktcelmax = resultTemp.result;
										}
									});
								}
								if(thermostat.id == resultTemp.result[j].HardwareID && resultTemp.result[j].Unit == 159 && resultTemp.result[j].Used == 1) {
									request=proto+address + ":" + port.toString() + tempReq + resultTemp.result[j].idx;
									$.ajax({url: request,
										async: false,
										success: function(resultTemp){
											//console.log(resultTemp);
											thermostat.aktcelmin = resultTemp.result;
										}
									});
								}
							}
						}
					});
					thermostats.push(thermostat);
				}
			}
			//console.log(thermostats);
		}
	});
	return thermostats;
}



