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

// Load API resources concurrently with a bounded request count | API-adatok párhuzamos betöltése korlátozott kérésszámmal
function dsvtApi(url) {
	return new Promise((resolve, reject) => {
		$.ajax({url: url, dataType: "json", timeout: 15000, cache: false})
			.done(resolve)
			.fail((xhr, status, error) => reject(new Error(url + ": " + (error || status))));
	});
}

async function dsvtRunLimited(tasks, limit) {
	let next = 0;
	const workers = Array.from({length: Math.min(limit, tasks.length)}, async () => {
		while (next < tasks.length) {
			const index = next++;
			try {
				await tasks[index]();
			} catch (error) {
				console.warn("DSVT data request failed | DSVT adatlekérés sikertelen:", error);
			}
		}
	});
	await Promise.all(workers);
}

function dsvtNormalizeName(name) {
	return String(name || "").normalize("NFD")
		.replace(/[\u0300-\u036f]/g, "")
		.replace(/\s+/g, "_").toLowerCase();
}

// Returns Promise<Array>; the HTML caller must await this function | Tömböt tartalmazó Promise; a HTML-hívónak await szükséges
async function getThermostats() {
	nodata = true;
	const prefix = proto + address + ":" + port.toString();
	const [hardwareResponse, devicesResponse, variablesResponse] = await Promise.all([
		dsvtApi(prefix + hardwareReq),
		dsvtApi(prefix + devicesReq),
		dsvtApi(prefix + userVarReq).catch(error => {
			console.warn("Cannot load AC settings | A klímabeállítások nem tölthetők be:", error);
			return {result: []};
		})
	]);

	const hardware = Array.isArray(hardwareResponse.result) ? hardwareResponse.result : [];
	const devices = Array.isArray(devicesResponse.result) ? devicesResponse.result : [];
	const variables = Array.isArray(variablesResponse.result) ? variablesResponse.result : [];
	const byIdx = new Map(devices.map(item => [String(item.idx), item]));
	const thermostats = [];
	const temperatureTasks = [];
	const historyTasks = [];

	for (const hw of hardware) {
		if (hw.Extra !== "DSVT_HMV_ZONE_12" || String(hw.Enabled).toLowerCase() !== "true") continue;
		nodata = false;
		const thermostat = new DSVT_HMV_ZONE_12_Thermostat();
		thermostat.name = hw.Name;
		thermostat.id = hw.idx;
		thermostat.host = hw.Address;
		thermostat.uname = hw.Username;
		thermostat.pass = hw.Password;
		thermostat.port = hw.Port;
		for (let n = 1; n <= 6; n++) thermostat["Mode" + n] = hw["Mode" + n];
		thermostat.dayname = ["Monday:0", "Tuesday:1", "Wednesday:2", "Thursday:3", "Friday:4", "Saturday:5", "Sunday:6"];

		// All selection lists come from the single getdevices response | Minden választólista az egyetlen getdevices válaszból készül
		thermostat.aktname = devices.map(item => item.Unit + ":" + item.Name + ":" + item.idx);
		thermostat.tempnameakt = devices.filter(item => {
			const kind = String(item.Type || "").toLowerCase();
			const source = String(item.HardwareName || "").toLowerCase();
			return kind.includes("temp") && Number(item.Used) === 1 && (source.includes("dummy") || source.includes("zigbee"));
		}).map(item => item.Unit + ":" + item.Name + ":" + item.idx);
		thermostat.switchnameakt = devices.filter(item => String(item.SwitchType || "").toLowerCase().includes("on/off") && Number(item.Used) === 1)
			.map(item => item.Unit + ":" + item.Name + ":" + item.idx);
		thermostat.setpointnameakt = devices.filter(item => String(item.SubType || "").toLowerCase().includes("setpoint") && String(item.HardwareID) === String(hw.idx))
			.map(item => item.Unit + ":" + item.Name + ":" + item.idx + ":" + item.SetPoint);
		thermostat.consolenameakt = devices.filter(item => String(item.Type || "").toLowerCase().includes("thermostat") && String(item.HardwareID) !== String(hw.idx))
			.map(item => item.Unit + ":" + item.Name + ":" + item.idx + ":" + item.SetPoint);
		thermostat.trvnameakt = devices.filter(item => String(item.SubType || "").toLowerCase().includes("setpoint") && String(item.HardwareName || "").toLowerCase().includes("zigbee"))
			.map(item => item.Unit + ":" + item.Name + ":" + item.idx);
		thermostat.doornameakt = devices.filter(item => /door|contact|lock/.test(String(item.SwitchType || "").toLowerCase()))
			.map(item => item.Unit + ":" + item.Name + ":" + item.idx);

		thermostat.acValues = {};
		for (const item of variables) {
			if (!String(item.Name || "").startsWith(thermostat.name) || !String(item.Name || "").includes("_AC_")) continue;
			const match = String(item.Name).match(/_Z_(\d+)_AC_(F|H)$/);
			if (!match) continue;
			try {
				const fixed = String(item.Value).replace(/'/g, '"').replace(/\bNone\b/g, "null")
					.replace(/\bTrue\b/g, "true").replace(/\bFalse\b/g, "false");
				const zone = Number(match[1]);
				if (!thermostat.acValues[zone]) thermostat.acValues[zone] = {};
				thermostat.acValues[zone][match[2]] = JSON.parse(fixed);
			} catch (error) {
				console.warn("Invalid AC variable | Hibás klímaváltozó:", item.Name, error);
			}
		}
		thermostat.klimatabla = [];
		for (let zone = 1; zone <= 12; zone++) {
			for (const mode of ["F", "H"]) {
				const value = (thermostat.acValues[zone] || {})[mode] || {};
				thermostat.klimatabla.push({
					zona: zone, tipus: mode,
					type: value.type && value.type !== "-" ? value.type : "nincs",
					IP: value.IP && value.IP !== "nincs" ? value.IP : "nincs",
					fanspeed: value.fanspeed ?? "nincs", swingv: value.swingv ?? "nincs", swingh: value.swingh ?? "nincs",
					komp: value.komp ?? 0, hatar_low: value.hatar_low ?? 0, hatar_top: value.hatar_top ?? 0,
					target_off: value.target_off ?? false, AC_jelenlet: value.AC_jelenlet ?? "None"
				});
			}
		}

		const unitFields = {
			6: "TempIn", 69: "tempOut", 72: "Kevero_1_temp", 73: "Kevero_2_temp", 19: "tempTartaly",
			97: "tempOutdew", 157: "tempIntdew", 10: "Fsetpoint", 20: "Hsetpoint", 21: "Msetpoint",
			100: "Psetpoint", 154: "hiszterezis", 158: "aktcelmax", 159: "aktcelmin"
		};
		const historyFields = {
			23: "Elsodleges_F", 26: "Masodlagos_F", 25: "Elsodleges_H", 28: "Masodlagos_H",
			24: "Elsodleges_M", 27: "Masodlagos_M", 102: "Elsodleges_P", 103: "Masodlagos_P",
			33: "Elsodleges_E", 34: "Masodlagos_E", 160: "Elsodleges_PE", 161: "Masodlagos_PE"
		};
		const own = devices.filter(item => String(item.HardwareID) === String(hw.idx));
		const minDates = [];
		const graphRequests = new Map();
		function queueGraph(idx, assign, isBase) {
			const key = String(idx);
			if (!graphRequests.has(key)) graphRequests.set(key, {callbacks: [], isBase: false});
			const entry = graphRequests.get(key);
			entry.callbacks.push(assign);
			if (isBase) entry.isBase = true;
		}

		// Zone names use the already fetched device list | Zónanevek a már lekért eszközlistából
		thermostat.zonetemp = [];
		for (const entry of String(hw.Mode1 || "").split(",")) {
			const [key, idx] = entry.split(":");
			if (!key || !key.startsWith("Z_") || !idx) continue;
			const device = byIdx.get(String(idx));
			if (!device) continue;
			const normalized = dsvtNormalizeName(device.Name);
			const field = "zonetemp_" + key + "_" + normalized;
			queueGraph(idx, result => {
				thermostat[field] = result;
				thermostat.zonetemp.push(idx + ":" + normalized);
			}, false);
		}

		for (const item of own) {
			const unit = Number(item.Unit);
			const field = unitFields[unit];
			if (field && (unit === 97 || unit === 157 || Number(item.Used) === 1)) {
				queueGraph(item.idx, result => { thermostat[field] = result; }, true);
			}
			const history = historyFields[unit];
			if (history) {
				// History is processed after temperature graphs establish the timeline | Kapcsolási előzmények feldolgozása a grafikonok időtengelyének meghatározása után
				historyTasks.push({thermostat, name: history, idx: item.idx, minDates});
			}
		}
		for (const [idx, entry] of graphRequests) {
			temperatureTasks.push(async () => {
				const data = await dsvtApi(prefix + tempReq + idx);
				if (!Array.isArray(data.result)) return;
				for (const callback of entry.callbacks) callback(data.result);
				if (entry.isBase) {
					for (const point of data.result) {
						const date = new Date(point.d).getTime();
						if (Number.isFinite(date)) minDates.push(date);
					}
				}
			});
		}
		thermostats.push(thermostat);
	}

	// Up to six requests at a time; no synchronous browser blocking | Legfeljebb hat párhuzamos kérés; nincs szinkron böngészőblokkolás
	await dsvtRunLimited(temperatureTasks, 6);
	const logTasks = historyTasks.map(job => async () => {
		const data = await dsvtApi(prefix + switchReq + job.idx);
		if (!Array.isArray(data.result)) return;
		const sorted = data.result.slice().sort((a, b) => new Date(a.Date).getTime() - new Date(b.Date).getTime());
		const minDate = job.minDates.length ? Math.min(...job.minDates) : 0;
		const historic = sorted.filter(item => new Date(item.Date).getTime() >= minDate);
		const last = sorted[sorted.length - 1];
		if (last && new Date(last.Date).getTime() < minDate && last.Status === "On") {
			historic.unshift({...last, Date: new Date(minDate).toISOString()});
			historic.push({...last, Date: new Date().toISOString()});
		}
		job.thermostat[job.name] = {historic};
	});
	await dsvtRunLimited(logTasks, 6);
	return thermostats;
}
