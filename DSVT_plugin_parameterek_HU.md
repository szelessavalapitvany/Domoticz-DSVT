# DSVT – Pluginparaméterek beállítása

> **Alap:** `plugin.py`, 2026. október 20-i állapot (a fájlban jelzett verzió: 1.2.1).  
> A dokumentáció a **Domoticz → Beállítások → Hardver → DSVT + HMV (DHW) + 12 ZONE** felület mezőinek sorrendjét követi.
>
> **Fontos!** A beállításokat lehetőség szerint **ne közvetlenül a Domoticz hardverbeállításainak paramétermezőiben szerkeszd**, hanem a plugin `templates` könyvtárába telepített **HTML konfigurációs felületen** végezd el. Az alábbi mezőnkénti leírás a paraméterek jelentését és helyét ismerteti, elsősorban ellenőrzéshez vagy kézi beállításhoz.

## Általános szabályok

A plugin hat konfigurációs mezőt használ (`Mode1`–`Mode6`). **Mindegyik paramétert kizárólag a lent megjelölt mezőbe kell beírni.** Más mezőben azonos nevű kulcs más szerepet is jelenthet, vagy a program egyszerűen nem dolgozza fel.

Az `idx` a **meglévő Domoticz-eszköz azonosítója**, nem a DSVT által létrehozott eszköz `Unit` értéke. A kulcsokat és az idx értékeket kettőspont választja el, az egyes bejegyzéseket vesszővel kell elválasztani: `Z_1:101,Z_2:102,K:110`. Az idx számokat a saját Domoticz rendszerből kell kiolvasni. A példákban szereplő számok kitalált minták.

A szükségtelen eszközcsoportok elhagyhatók. Ugyanabból a kulcsból a listát visszaadó paramétereknél több bejegyzés is megadható, például `Z_1:101,Z_1:102` vagy `SV_P:301,SV_P:302`. A speciális `FG_`/`SV_` paramétereknél **ne tegyünk szóközt** a vesszők után: a parser teljes, közvetlenül vesszővel elválasztott kulcsokat vár.

## Domoticz IP Address

**Ide kizárólag IP-címet vagy elérhető kiszolgálócímet írjunk**, nem eszköz-idx listát.

- Alapérték: `127.0.0.1` – ha a plugin és a Domoticz ugyanazon a gépen fut.
- Másik szerver esetén annak a Domoticz API-n keresztül elérhető címét adjuk meg, például `192.168.1.20`.

## Port

A Domoticz HTTP API portja. Alapérték: `8080`. Csak a portszámot kell beírni, nem teljes URL-t.

## Username és Password

A Domoticz API hitelesítéséhez szükséges felhasználónév és jelszó. Ha a konkrét helyi API-hozzáféréshez nincs szükség hitelesítésre, a mezők üresen maradhatnak. A helyi hozzáférés és a jogosultságok beállításait külön ellenőrizni kell.

---

## 1. mező – List of thermometers (`Mode1`)

**Itt kizárólag a bemeneti érzékelőket, TRV-ket, zónakonzolokat és a keverőszelep-szorzókat konfiguráljuk.** Fűtési/hűtési relék és hőtermelőkapcsolók nem ebbe a mezőbe tartoznak.

| Kulcs | Mit kell utána írni? | Mire szolgál? |
|---|---|---|
| `Z_1` … `Z_12` | Hőmérő **idx** | Az 1–12. zóna hőmérséklet-érzékelői. |
| `A_1` … `A_12` | Nyitásérzékelő **idx** | Az adott zóna ajtó- és ablakállapota. |
| `K` | Külső hőmérő **idx** | Külső hőmérséklet alapján működő szabályozás. |
| `T` | HMV-tartály hőmérő **idx** | Használati melegvíz hőmérséklete. |
| `P` | Puffertartály hőmérő **idx** | Puffertartály hőmérséklete. |
| `S_1`, `S_2` | 1. és 2. keverőkör hőmérőjének **idx** értéke | A kevert körök mért hőmérséklete. **Itt érzékelőt jelent**, nem szelepkapcsolót! |
| `S_1M`, `S_2M` | Egész szám, alapérték `100` | Az 1. és 2. keverőszelephez tartozó belső szorzó. Nem idx; csak tudatos beállítás esetén módosítandó. |
| `L` | Szobahőmérő **idx** | Szobahőmérséklet-kompenzációhoz rendelt érzékelő. |
| `V_1` … `V_12` | TRV **idx** | Az adott zónához rendelt termosztatikus radiátorszelep / beállítási pont. |
| `C_1` … `C_12` | Konzol **idx** | Az adott zóna kezelőkonzoljának kapcsolata. |
| **`FG_T`** | Fagyvédelmi hőmérő **idx** | **Új:** külön fagyvédelmi érzékelő(k). |

**Példa a teljes mezőre:**

```text
Z_1:101,Z_1:102,Z_2:103,A_1:201,K:110,T:111,P:112,S_1:113,L:114,V_1:115,C_1:116,FG_T:117
```

A fagyvédelemhez a `FG_T` önmagában nem elegendő: a vezérelt kapcsolókat a **2. mező `FG_S`** kulcsával kell megadni. A fagyvédelmi hőmérsékleti határ és hiszterézis a plugin saját Domoticz-eszközein állítható (Unit `89`, `156`; alapértékek 5 °C és 1 °C). Érvényes hőmérséklet hiányában a fagyvédelmi függvény nem küld új kapcsolási igényt; nem helyettesít önálló berendezésvédelmet.

---

## 2. mező – Heating devices (`Mode2`)

**Itt a fűtési zónakapcsolók, a keverőszelepek `+` irányú reléi, valamint a fagy- és szivattyúvédelmi kapcsolók szerepelnek.**

| Kulcs | Mit kell utána írni? | Mire szolgál? |
|---|---|---|
| `Z_1_F` … `Z_12_F` | Kapcsoló **idx** | Adott zóna fűtési szelepe vagy szivattyúja. |
| `Z_1_F_V` … `Z_12_F_V` | Kapcsoló **idx** | Virtuális hidraulikus váltó fűtési kapcsolói. |
| `S_1`, `S_2` | Kapcsoló **idx** | 1. és 2. keverőszelep **`+` (növelő)** iránya. |
| **`FG_S`** | Kapcsoló **idx** | **Új:** fagyvédelem által vezérelt kapcsoló(k). |
| **`SV_P`** | Kapcsoló **idx** | **Új:** időszakos szivattyú-/szelepjáratásra kijelölt kapcsoló(k). |
| **`SV_D`** | `0`–`6` | **Új:** heti járatási nap: `0` hétfő, …, `6` vasárnap. |
| **`SV_H`** | `0`–`23` | **Új:** a járatás kezdőórája. |
| **`SV_M`** | `1`–`20` | **Új:** járatási idő **percben**. |

**Példa a teljes mezőre:**

```text
Z_1_F:301,Z_2_F:302,Z_1_F_V:303,S_1:304,FG_S:305,FG_S:306,SV_P:307,SV_P:308,SV_D:0,SV_H:12,SV_M:5
```

**Szivattyúvédelem:** a példában a 307-es és 308-as kapcsoló hétfőn 12:00-tól tervezetten 5 percig kap bekapcsolási igényt. A jelenlegi megvalósítás a megadott óra kezdetétől **egyórás indítási ablakban** egyszer indít; a befejezési időpontot menti, és a lejárat után kikapcsolási igényt ad. Más funkció egyidejű bekapcsolási igénye elsőbbséget élvez az `Off` igénnyel szemben. A `SV_M` időt célszerű **legalább a frissítési ciklus hosszára** állítani.

**Figyelem: eltérő napszámozás!** `SV_D:0` = hétfő; a HMV-fertőtlenítés `N:1` = hétfő.

---

## 3. mező – Cooling devices (`Mode3`)

**Itt csak a hűtési kapcsolókat és a keverőszelepek `−` irányú reléit adjuk meg.**

| Kulcs | Mit kell utána írni? | Mire szolgál? |
|---|---|---|
| `Z_1_H` … `Z_12_H` | Kapcsoló **idx** | Adott zóna hűtési szelepe vagy szivattyúja. |
| `Z_1_H_V` … `Z_12_H_V` | Kapcsoló **idx** | Virtuális hidraulikus váltó hűtési kapcsolói. |
| `S_1`, `S_2` | Kapcsoló **idx** | 1. és 2. keverőszelep **`−` (csökkentő)** iránya. |

**Példa:**

```text
Z_1_H:401,Z_2_H:402,Z_1_H_V:403,S_1:404,S_2:405
```

**Ugyanaz az `S_1` kulcs három különböző mezőben:** `Mode1` = hőmérő, `Mode2` = `+` relé, `Mode3` = `−` relé. A relék felcserélése téves szelepszabályozást okoz.

---

## 4. mező – 1. device control (`Mode4`)

**Kizárólag az első hőtermelő funkcióihoz rendelt eszközök és annak fertőtlenítési ütemezése tartozik ide.** Lehet például az első hőtermelő hőszivattyú.

| Kulcs | Mit kell utána írni? | Mire szolgál? |
|---|---|---|
| `F` | Kapcsoló **idx** | Az első eszköz fűtési vezérlése. |
| `M` | Kapcsoló **idx** | Az első eszköz HMV-vezérlése. |
| `E` | Kapcsoló **idx** | Az első eszköz HMV elektromos fűtőpatronja. |
| `H` | Kapcsoló **idx** | Az első eszköz hűtési vezérlése. |
| `P_F` | Kapcsoló **idx** | Az első eszköz pufferfűtése. |
| `P_H` | Kapcsoló **idx** | Az első eszköz pufferhűtése. |
| `PE` | Kapcsoló **idx** | Az első eszköz puffer-fűtőpatronja. |
| `BK` | Kapcsoló **idx** | Az első eszköz **bekapcsolásakor késleltetendő** kapcsoló. Nem időtartam! |
| `UK` | Kapcsoló **idx** | Az első eszköz **kikapcsolásakor késleltetendő** kapcsoló. Nem időtartam! |
| `N` | Nap száma `1`–`7` | Az első eszköz HMV-fertőtlenítési napja: `1` hétfő, …, `7` vasárnap. |
| `O` | Óra `0`–`23` | Az első eszköz HMV-fertőtlenítésének kezdőórája. |

**Példa:**

```text
F:501,M:502,E:503,H:504,P_F:505,P_H:506,PE:507,BK:508,UK:509,N:1,O:2
```

A fertőtlenítés kezdete a példában hétfő **02:00**. A kód a kezdéstől hatórás aktív időablakot vizsgál; ez nem jelenti azt, hogy a fűtőberendezés szükségképpen hat órán át folyamatosan működik. `N` többször is megadható több fertőtlenítési naphoz. A `0` **nem kikapcsolást jelent** az `N` mezőben: a parser az érvénytelen értéket `1`-re alakítja. Ha nincs ütemezett fertőtlenítés, az `N` paramétert el kell hagyni.

A `BK`/`UK` kulcsok után **kapcsoló idx** kerül; a tényleges késleltetési idő a plugin választóeszközein állítható: **218** (1. eszköz bekapcsolási késleltetés), **219** (1. eszköz kikapcsolási késleltetés). Az időértékeket tehát nem a `BK:` és `UK:` után kell beírni.

---

## 5. mező – 2. device control (`Mode5`)

**Ugyanaz a kulcskészlet, mint a 4. mezőben, de minden érték a második hőtermelőre vonatkozik** (például gázkazán). Az első és második eszköz funkciói egymástól függetlenül konfigurálhatók.

| Kulcsok | Elfogadott tartalom |
|---|---|
| `F`, `M`, `E`, `H`, `P_F`, `P_H`, `PE` | A második eszköz funkcióihoz tartozó **kapcsoló idx**. |
| `BK`, `UK` | A második eszköz be-/kikapcsolásakor késleltetendő **kapcsoló idx**. |
| `N` | HMV-fertőtlenítés napja: `1`–`7`, hétfőtől vasárnapig. |
| `O` | HMV-fertőtlenítés kezdőórája: `0`–`23`. |

**Példa:**

```text
F:601,M:602,P_F:603,BK:604,UK:605,N:7,O:3
```

Ebben a példában a második eszköz fertőtlenítési napja vasárnap, kezdete 03:00. A második eszköz késleltetéseit a **220** (bekapcsolás) és **232** (kikapcsolás) Unit számú DSVT-választóeszköz szabályozza.

---

## 6. mező – Operating parameters (`Mode6`)

**Ez a mező kivétel: nem `KULCS:idx` formátumú, hanem kötött sorrendű, vesszővel elválasztott értéksor.** A sorrendet megváltoztatni nem szabad.

| Pozíció | Mit jelent? | Milyen érték? | Alapérték |
|---|---|---|---|
| 1. | Debug/naplózási szint | Domoticz Python debug bitmaszk: `0` (nincs debug), `1` (összes debug), `2` (Python debug), `62` (a korábbi alap naplózási mód megnevezése). | `0` |
| 2. | Frissítési ciklus | Egész szám, percben. | `5` |
| 3. | Kalkulációs ciklus | Egész szám, percben. | `15` |
| 4. | P1 mérő | A fogyasztásmérő Domoticz **idx** száma; `0` = nincs megadva. | `0` |
| 5. | Jelenlétfigyelés | A jelenlétfigyelő **csoport neve**, vagy `None`; nem idx. | `None` |

**Alapértelmezett érték (teljes mező):**

```text
0,5,15,0,None
```

**Példa bekötött P1 mérővel és `csalad` jelenlétcsoporttal:**

```text
0,5,15,245,csalad
```

A kód első három pozíciót egész számmá alakítja, a negyedik pozíciót karakterláncként beolvassa, majd induláskor egész számmá alakítja. Az ötödik pozíció szöveg marad. **Ne hagyjuk ki a köztes elemeket**, mert a pozíciójuk határozza meg a jelentésüket.

---

## Gyors ellenőrzés: melyik kulcs melyik mezőbe kerül?

| Mező | Ide tartozó kulcsok |
|---|---|
| **Mode1 – érzékelők** | `Z_1…Z_12`, `A_1…A_12`, `K`, `T`, `P`, `S_1`, `S_2`, `S_1M`, `S_2M`, `L`, `V_1…V_12`, `C_1…C_12`, `FG_T` |
| **Mode2 – fűtési kapcsolók** | `Z_1_F…Z_12_F`, `Z_1_F_V…Z_12_F_V`, `S_1`, `S_2`, `FG_S`, `SV_P`, `SV_D`, `SV_H`, `SV_M` |
| **Mode3 – hűtési kapcsolók** | `Z_1_H…Z_12_H`, `Z_1_H_V…Z_12_H_V`, `S_1`, `S_2` |
| **Mode4 – első hőtermelő** | `F`, `M`, `E`, `H`, `P_F`, `P_H`, `PE`, `BK`, `UK`, `N`, `O` |
| **Mode5 – második hőtermelő** | `F`, `M`, `E`, `H`, `P_F`, `P_H`, `PE`, `BK`, `UK`, `N`, `O` |
| **Mode6 – működési értékek** | Öt pozicionális érték: `debug,frissítés,kalkuláció,P1_idx,jelenlét_csoport` |

### Fontos üzemeltetési megjegyzések

- A `Mode2` és `Mode3` keverőszelep-reléinek bekötését éles üzem előtt külön ellenőrizzük, mert a `+` és `−` irány felcserélése hibás szabályozást eredményezhet.
- A fagyvédelem és a szivattyúvédelem a normál kapcsolási igényekkel közös kapcsolási listát használ. Azonos kapcsolónál a **bekapcsolási igény elsőbbséget élvez**.
- A szivattyúvédelmi `SV_D` napja **0–6**, a HMV-fertőtlenítési `N` napja **1–7**.
- A két hőtermelő `BK` és `UK` paramétere **nem perceket, hanem kapcsoló-idx értékeket** tartalmaz.
- A fűtési, hűtési és HMV-célhőmérsékleteket, hiszteréziseket és egyéb szabályozási küszöböket jellemzően **a plugin által létrehozott Domoticz-eszközökön** kell beállítani, nem ezekben a hardverparaméter-mezőkben.
- A módosítás után ellenőrizzük a plugin naplóját és az érintett kimenetek tényleges kapcsolását.
