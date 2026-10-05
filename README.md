# DSVT – Smart Heating, Cooling and DHW Control for Domoticz

DSVT is an advanced multi-zone heating, cooling and domestic hot water control system for Domoticz, designed primarily for the automation of existing residential buildings.

It is not simply a thermostat controller. The system can coordinate multiple heating and cooling zones, multiple heat sources, domestic hot water production, buffer tanks, mixing valves, energy consumption and production, weather data, presence information, and door/window states.

The goal is not only to provide a control algorithm, but to deliver a ready-to-use automation system. DSVT therefore automatically creates a significant part of the required Domoticz devices and control elements and makes them available on the Domoticz dashboard.

The system is designed to operate locally in an open environment without requiring the user to build the complete control logic from scratch.

## Main Features

### Multi-zone heating and cooling

- Up to 12 independent heating/cooling zones
- Individual room temperature control
- Manual selection between heating and cooling mode
- TRV thermostatic radiator valve control
- Support for underfloor heating, radiators, wall heating/cooling and ceiling heating/cooling
- Automatically calculated target temperatures
- Door and window opening detection per zone
- Heating or cooling demand of a zone can be ignored while a window or door is open

### Multiple heat sources

DSVT can coordinate multiple heat sources, for example:

- Heat pumps
- Gas boilers
- Electric heating
- Other auxiliary heat sources

The system can coordinate the heat sources according to heat demand and system configuration.

It is especially suitable for hybrid systems, for example when a heat pump is added to an existing gas boiler.

### Outdoor-temperature-based target temperature

To improve heat pump efficiency, DSVT can adjust target temperatures according to the outdoor temperature.

This can be used for:

- Heating supply target temperature
- DHW target temperature

Lower target temperatures can be used during milder weather and higher target temperatures during colder conditions, helping the heat pump operate under more favorable conditions.

### Domestic Hot Water control

DHW control is an integral part of the system.

Main features include:

- DHW temperature control
- Multiple heat source support
- Heat pump DHW production
- Boiler-based DHW production
- Electric immersion heater control
- Scheduled operation
- Coordinated use of heat sources
- Outdoor-temperature-dependent DHW target temperature
- Scheduled thermal disinfection heating using the electric immersion heater

The scheduled disinfection cycle can periodically raise the DHW tank to a higher temperature.

### Buffer tank control

The system can use buffer tank temperature data as part of the heating and cooling control strategy.

The buffer state can be used to coordinate heat source operation and reduce unnecessary switching.

### Mixing valve control

DSVT can control two independent mixing valves.

This allows different supply temperatures to be used for different heat distribution systems, for example:

- Underfloor heating
- Radiators
- Wall heating
- Ceiling heating
- Ceiling cooling
- Wall cooling

Mixing valve target temperatures can be adjusted according to current system demand.

### Dew point monitoring in cooling mode

During cooling operation, the system can take the dew point into account.

The purpose is to reduce the risk of condensation when surface cooling is used and to prevent the cooling water temperature from falling below a safe level.

### Health-related cooling limit

In cooling mode, DSVT can automatically apply a configurable health-related cooling limit.

The purpose is to avoid an unnecessarily large temperature difference between outdoor and indoor temperatures and therefore prevent excessively aggressive cooling.

### Integration of conventional air conditioners

Traditional split air-conditioning systems can be integrated into the central cooling strategy using infrared control.

This allows conventional air conditioners to operate as part of the overall cooling system instead of as isolated devices.

### Look-ahead control

DSVT does not automatically calculate the thermal inertia of the building.

Instead, the user can configure how far ahead the controller should take expected temperature changes into account.

This makes it possible to adapt the control strategy to systems such as:

- Slow-response underfloor heating
- Faster-response radiator heating
- Buildings with different thermal characteristics

### Weather data

DSVT can use weather forecast information as part of its control strategy.

Forecast data can be used for look-ahead control and for estimating future heating or cooling demand.

The project aims to use an international weather data source that provides at least temperature forecasts worldwide.

### Presence-based control

The system can use presence information to automatically switch between comfort and energy-saving operation.

When nobody is at home, unnecessary heating or cooling can be reduced.

When occupants return, normal comfort settings can automatically be restored.

Presence detection is being made available as a separately installable component so that this functionality will not depend on the Szélessáv SmartHome firmware.

### Door and window opening detection

DSVT can monitor door and window sensors individually for each zone.

When a window or door is open, the heating or cooling demand of the affected room can be ignored.

This helps prevent heating or cooling a room while a window is open.

### Energy consumption and production monitoring

The system can use energy consumption and production data.

This makes it possible to coordinate flexible electrical loads according to factors such as:

- Current photovoltaic production
- Grid power consumption
- Available surplus energy
- Configured power limits

For example, DHW production or other controllable loads can be shifted to more favorable periods.

## Dedicated HTML configuration interface

Because of the large number of functions and configuration options, managing all parameters through standard Domoticz hardware fields would be difficult.

DSVT therefore provides a dedicated HTML administration interface.

The interface can be used to configure, among other things:

- Zones
- Temperature targets
- Heat sources
- Mixing valves
- DHW operation
- Presence logic
- Door and window sensors
- Cooling limits
- Look-ahead time
- Other operating and optimization parameters

The goal is to keep configuration understandable even though the underlying control logic is complex.

## Graphical event log

The administration interface provides a graphical log of the last 24 hours of system events.

This can help with:

- Checking system operation
- Fine-tuning configuration
- Identifying problems
- Optimizing energy use
- Understanding control decisions

## Automatic user interface creation

For easier everyday use, DSVT automatically creates and places a significant part of the required control elements on the Domoticz dashboard.

These may include:

- Operating mode selectors
- Target temperature controls
- Zone controls
- Heat source status indicators
- DHW controls
- Mixing valve settings
- Presence status
- System status
- Operating and optimization parameters

The goal is that after installation the user is not presented with an empty automation platform, but with a usable and preconfigured control interface.

## Local operation

DSVT is designed to operate locally within Domoticz.

Heating, cooling and DHW control do not require a permanent cloud connection.

The main control logic runs locally.

## Typical system configuration

A typical DSVT installation may include:

- Heat pump
- Gas boiler
- Electric immersion heater
- Multiple heating/cooling zones
- TRVs
- Underfloor heating
- Radiators
- Wall or ceiling heating/cooling
- Conventional split air conditioners
- Buffer tank
- DHW tank
- Two mixing valves
- Indoor temperature sensors
- Outdoor temperature sensor
- Humidity sensors
- Door and window sensors
- Presence detection
- Energy consumption measurement
- Photovoltaic production monitoring
- Weather forecast data

DSVT handles these components as parts of one coordinated control system.

## Intended use

DSVT is primarily designed for automation of existing residential buildings.

It is especially useful where:

- Different heat distribution systems are used
- Multiple heat sources must be coordinated
- A heat pump is added to an existing boiler
- Independent control of multiple rooms is required
- DHW production must also be automated
- Surface cooling and air conditioning are used together
- Photovoltaic generation is available
- Local, cloud-independent operation is important
- The user does not want to build the complete automation logic manually

## Multi-language support

The system interface and Domoticz devices support multiple languages.

Currently supported languages include:

- Chinese
- Czech
- Danish
- Dutch
- English
- Finnish
- French
- German
- Hungarian
- Italian
- Japanese
- Norwegian
- Polish
- Portuguese
- Spanish
- Swedish

The system can create devices and interface elements according to the language configured in Domoticz.

## Requirements

- Domoticz 2023.2 or newer
- Python plugin support
- Compatible temperature, humidity and other sensors
- Switching and control devices suitable for the HVAC system

The system has so far been primarily tested and used in an OpenWrt environment.

Testing on other Linux-based Domoticz systems is welcome.

## Installation

Clone the repository into the Domoticz plugin directory:

```sh
cd /etc/domoticz/plugins
git clone https://github.com/szelessavalapitvany/Domoticz-DSVT.git DSVT_HMV_ZONE_12
