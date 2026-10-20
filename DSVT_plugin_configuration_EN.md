# DSVT – Plugin Parameter Configuration

> **Source:** `plugin.py`, as of October 20, 2026 (version indicated in the file: 1.2.1).  
> This guide follows the field order in **Domoticz → Setup → Hardware → DSVT + HMV (DHW) + 12 ZONE**.
>
> **Important!** Whenever possible, **do not edit these parameters directly in the Domoticz hardware configuration fields**. Instead, configure them through the **HTML configuration interface installed in the plugin’s `templates` directory**. The field-by-field reference below explains where the parameters belong and is mainly intended for verification or manual configuration.


## General rules

The plugin uses six configuration fields (`Mode1`–`Mode6`). **Enter each parameter only in the field specified below.** The same key may have a different meaning in another field, or the plugin may simply ignore it.

An `idx` is the **identifier of an existing Domoticz device**, not the `Unit` number of a device created by DSVT. Separate keys and idx values with a colon, and separate entries with commas: `Z_1:101,Z_2:102,K:110`. Obtain the idx values from your own Domoticz installation. The numbers in the examples are illustrative only.

Unused device groups may be omitted. Parameters that return lists can be specified more than once, for example `Z_1:101,Z_1:102` or `SV_P:301,SV_P:302`. For the special `FG_`/`SV_` parameters, **do not add spaces** after commas: the parser expects complete keys separated directly by commas.

## Domoticz IP Address

**Enter only an IP address or reachable server hostname here**, not a device idx list.

- Default: `127.0.0.1` – when the plugin and Domoticz run on the same host.
- If Domoticz runs on another server, use an address reachable through the Domoticz API, such as `192.168.1.20`.

## Port

The Domoticz HTTP API port. Default: `8080`. Enter the port number only, not a complete URL.

## Username and Password

Username and password for Domoticz API authentication. If authentication is not required for the particular local API connection, these fields may be left blank. Verify local access and permission settings separately.

---

## Field 1 – List of thermometers (`Mode1`)

**Configure input sensors, TRVs, zone consoles, and mixing-valve multipliers here only.** Heating/cooling relays and heat-generator switches belong in other fields.

| Key | Value to enter | Purpose |
|---|---|---|
| `Z_1` … `Z_12` | Temperature sensor **idx** | Temperature sensors for zones 1–12. |
| `A_1` … `A_12` | Opening sensor **idx** | Door/window state for the corresponding zone. |
| `K` | Outdoor temperature sensor **idx** | Outdoor-temperature-based control. |
| `T` | DHW tank temperature sensor **idx** | Domestic hot water temperature. |
| `P` | Buffer tank temperature sensor **idx** | Buffer tank temperature. |
| `S_1`, `S_2` | Temperature sensor **idx** for mixing circuits 1 and 2 | Measured temperature of each mixed circuit. **These keys identify sensors here**, not valve switches! |
| `S_1M`, `S_2M` | Integer; default `100` | Internal multiplier for mixing valves 1 and 2. Not an idx; change only when deliberately adjusting this setting. |
| `L` | Room temperature sensor **idx** | Sensor used for room-temperature compensation. |
| `V_1` … `V_12` | TRV **idx** | Thermostatic radiator valve / setpoint assigned to the zone. |
| `C_1` … `C_12` | Console **idx** | Control console assigned to the zone. |
| **`FG_T`** | Frost-protection temperature sensor **idx** | **New:** dedicated frost-protection sensor(s). |

**Example of the complete field:**

```text
Z_1:101,Z_1:102,Z_2:103,A_1:201,K:110,T:111,P:112,S_1:113,L:114,V_1:115,C_1:116,FG_T:117
```

For frost protection, `FG_T` alone is not sufficient: specify the controlled switches using **`FG_S` in Field 2**. The frost-protection temperature threshold and hysteresis are adjustable through the plugin's own Domoticz devices (Units `89` and `156`; defaults 5 °C and 1 °C). If no valid temperature reading is available, the frost-protection function does not submit a new switching request. It is not a substitute for independent equipment protection.

---

## Field 2 – Heating devices (`Mode2`)

**This field contains heating zone switches, the `+` direction relays of mixing valves, and frost-/pump-protection switches.**

| Key | Value to enter | Purpose |
|---|---|---|
| `Z_1_F` … `Z_12_F` | Switch **idx** | Heating valve or pump for the corresponding zone. |
| `Z_1_F_V` … `Z_12_F_V` | Switch **idx** | Heating switches for the virtual hydraulic separator. |
| `S_1`, `S_2` | Switch **idx** | **`+` (increase)** direction of mixing valves 1 and 2. |
| **`FG_S`** | Switch **idx** | **New:** switch(es) controlled by frost protection. |
| **`SV_P`** | Switch **idx** | **New:** switch(es) included in periodic pump/valve exercise. |
| **`SV_D`** | `0`–`6` | **New:** weekly exercise day: `0` Monday, …, `6` Sunday. |
| **`SV_H`** | `0`–`23` | **New:** exercise start hour. |
| **`SV_M`** | `1`–`20` | **New:** exercise duration **in minutes**. |

**Example of the complete field:**

```text
Z_1_F:301,Z_2_F:302,Z_1_F_V:303,S_1:304,FG_S:305,FG_S:306,SV_P:307,SV_P:308,SV_D:0,SV_H:12,SV_M:5
```

**Pump protection:** In this example, switches 307 and 308 are scheduled to receive an On request for five minutes starting at 12:00 on Monday. The current implementation starts once within a **one-hour start window** beginning at the configured hour. It saves the end time and submits an Off request after the interval expires. If another function simultaneously requests On, that request takes priority over Off. It is advisable to set `SV_M` to **at least the length of the update cycle**.

**Important: the day numbering differs!** `SV_D:0` = Monday, whereas `N:1` = Monday for DHW disinfection.

---

## Field 3 – Cooling devices (`Mode3`)

**Enter only cooling switches and the `−` direction relays of mixing valves here.**

| Key | Value to enter | Purpose |
|---|---|---|
| `Z_1_H` … `Z_12_H` | Switch **idx** | Cooling valve or pump for the corresponding zone. |
| `Z_1_H_V` … `Z_12_H_V` | Switch **idx** | Cooling switches for the virtual hydraulic separator. |
| `S_1`, `S_2` | Switch **idx** | **`−` (decrease)** direction of mixing valves 1 and 2. |

**Example:**

```text
Z_1_H:401,Z_2_H:402,Z_1_H_V:403,S_1:404,S_2:405
```

**The same `S_1` key has three different meanings:** `Mode1` = temperature sensor, `Mode2` = `+` relay, `Mode3` = `−` relay. Swapping the relays may cause incorrect mixing-valve operation.

---

## Field 4 – 1st device control (`Mode4`)

**This field is reserved for functions assigned to the first heat generator and its DHW disinfection schedule.** For example, the first heat generator may be a heat pump.

| Key | Value to enter | Purpose |
|---|---|---|
| `F` | Switch **idx** | Heating control for the first device. |
| `M` | Switch **idx** | DHW control for the first device. |
| `E` | Switch **idx** | Electric DHW heating element for the first device. |
| `H` | Switch **idx** | Cooling control for the first device. |
| `P_F` | Switch **idx** | Buffer heating for the first device. |
| `P_H` | Switch **idx** | Buffer cooling for the first device. |
| `PE` | Switch **idx** | Electric buffer heating element for the first device. |
| `BK` | Switch **idx** | Switch to be **delayed when the first device turns on**. Not a duration! |
| `UK` | Switch **idx** | Switch to be **delayed when the first device turns off**. Not a duration! |
| `N` | Day number `1`–`7` | DHW disinfection day for the first device: `1` Monday, …, `7` Sunday. |
| `O` | Hour `0`–`23` | DHW disinfection start hour for the first device. |

**Example:**

```text
F:501,M:502,E:503,H:504,P_F:505,P_H:506,PE:507,BK:508,UK:509,N:1,O:2
```

In this example, disinfection begins on Monday at **02:00**. The code checks a six-hour active window from the start time; this does not mean that the heater necessarily runs continuously for six hours. Specify `N` more than once to schedule multiple disinfection days. **`N:0` does not disable the schedule:** the parser converts an invalid value to `1`. To omit scheduled disinfection, leave out the `N` parameter.

The `BK`/`UK` values are **switch idx numbers**. The actual delay durations are configured through the plugin's selector devices: **Unit 218** (first device switch-on delay) and **Unit 219** (first device switch-off delay). Do not enter the delay duration after `BK:` or `UK:`.

---

## Field 5 – 2nd device control (`Mode5`)

**This field uses the same set of keys as Field 4, but all values refer to the second heat generator** (for example, a gas boiler). The functions of the first and second devices can be configured independently.

| Keys | Accepted values |
|---|---|
| `F`, `M`, `E`, `H`, `P_F`, `P_H`, `PE` | **Switch idx** for the corresponding function of the second device. |
| `BK`, `UK` | **Switch idx** to be delayed when the second device turns on/off. |
| `N` | DHW disinfection day: `1`–`7`, Monday through Sunday. |
| `O` | DHW disinfection start hour: `0`–`23`. |

**Example:**

```text
F:601,M:602,P_F:603,BK:604,UK:605,N:7,O:3
```

In this example, the second device's disinfection day is Sunday, starting at 03:00. Delay durations for the second device are controlled by DSVT selector devices **Unit 220** (switch-on) and **Unit 232** (switch-off).

---

## Field 6 – Operating parameters (`Mode6`)

**This field is different: instead of `KEY:idx` entries, it uses a fixed-order, comma-separated list of values.** Do not rearrange the values.

| Position | Meaning | Value | Default |
|---|---|---|---|
| 1 | Debug/logging level | Domoticz Python debug bitmask: `0` (no debug), `1` (all debug), `2` (Python debug), `62` (previously named basic logging mode). | `0` |
| 2 | Update cycle | Integer, in minutes. | `5` |
| 3 | Calculation cycle | Integer, in minutes. | `15` |
| 4 | P1 meter | Domoticz **idx** of the electricity meter; `0` = not configured. | `0` |
| 5 | Presence detection | Presence-detection **group name**, or `None`; not an idx. | `None` |

**Default value (entire field):**

```text
0,5,15,0,None
```

**Example with a configured P1 meter and a `family` presence group:**

```text
0,5,15,245,family
```

The code converts the first three values to integers. The fourth is initially read as a string and converted to an integer during startup. The fifth remains text. **Do not omit intermediate values**, because each position determines its meaning.

---

## Quick reference: which field accepts which key?

| Field | Accepted keys |
|---|---|
| **Mode1 – sensors** | `Z_1…Z_12`, `A_1…A_12`, `K`, `T`, `P`, `S_1`, `S_2`, `S_1M`, `S_2M`, `L`, `V_1…V_12`, `C_1…C_12`, `FG_T` |
| **Mode2 – heating switches** | `Z_1_F…Z_12_F`, `Z_1_F_V…Z_12_F_V`, `S_1`, `S_2`, `FG_S`, `SV_P`, `SV_D`, `SV_H`, `SV_M` |
| **Mode3 – cooling switches** | `Z_1_H…Z_12_H`, `Z_1_H_V…Z_12_H_V`, `S_1`, `S_2` |
| **Mode4 – first heat generator** | `F`, `M`, `E`, `H`, `P_F`, `P_H`, `PE`, `BK`, `UK`, `N`, `O` |
| **Mode5 – second heat generator** | `F`, `M`, `E`, `H`, `P_F`, `P_H`, `PE`, `BK`, `UK`, `N`, `O` |
| **Mode6 – operating values** | Five positional values: `debug,update_cycle,calculation_cycle,P1_idx,presence_group` |

### Important operational notes

- Verify the wiring of the `Mode2` and `Mode3` mixing-valve relays before commissioning. Reversing the `+` and `−` directions may cause incorrect valve control.
- Frost protection and pump protection share the switching-request list with normal control functions. **On requests take priority** when multiple functions address the same switch.
- Pump-protection `SV_D` uses days **0–6**, whereas DHW disinfection `N` uses **1–7**.
- For both heat generators, `BK` and `UK` take **switch idx values, not minutes**.
- Heating, cooling, and DHW target temperatures, hysteresis settings, and other control thresholds are generally configured **through the Domoticz devices created by the plugin**, not in these hardware parameter fields.
- After editing the configuration, check the plugin log and verify that the affected outputs switch correctly.
