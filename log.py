import requests
import json
import sqlite3
from datetime import datetime, timezone, timedelta
import configparser
import os.path

URL = "https://platform.tier-services.io/vehicle?zoneId="
CONFIG_FILE_NAME = 'config.ini'



if (not os.path.exists(CONFIG_FILE_NAME)):
    print("Config file '%s' not found. You can copy the example file if you want." % CONFIG_FILE_NAME)
    exit(1)

# Read config:
config = configparser.ConfigParser()
config.read(CONFIG_FILE_NAME)

try:
    CITY = config['API']['CITY']
except KeyError:
    print("Please set the entry for API->CITY inside the config file '%s'." % CONFIG_FILE_NAME)
    exit(1)

try:
    API_KEY = config['API']['KEY']
except KeyError:
    print("Please set the entry for API->KEY inside the config file '%s'." % CONFIG_FILE_NAME)
    exit(1)

try:
    DB_FILENAME = config['DB']['FILENAME']
except KeyError:
    print("Please set the entry for DB->FILENAME inside the config file '%s'." % CONFIG_FILE_NAME)
    exit(1)

headers = {'X-Api-Key': API_KEY}
r = requests.get(URL + CITY, headers=headers)
j = r.json()
data = j['data']

db = sqlite3.connect(DB_FILENAME)
c = db.cursor()

def isTableExisting(table):
    query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?;"
    c.execute(query, (table,))
    r = c.fetchone()
    if (not r is None):
        return True
    return False

def createLogTable():
    query = """CREATE TABLE if not exists log (
    timestamp TEXT,
    internal_id INTEGER,
    state TEXT,
    batteryLevel INTEGER,
    lat REAL,
    lng REAL,
    isRentable TEXT
    );"""
    c.execute(query)
    db.commit()

def createVehicleTable():
    query = """CREATE TABLE if not exists vehicles (
        	internal_id INTEGER PRIMARY KEY,
        	id TEXT NOT NULL,
        	lastLocationUpdate TEXT,
        	lastStateChange TEXT,
        	maxSpeed INTEGER,
        	licencePlate TEXT,
        	vin TEXT,
        	code TEXT,
        	iotVendor TEXT,
		    logCounter INTEGER DEFAULT 0
        );"""
    c.execute(query)

    query = 'CREATE INDEX log_timestamp_IDX ON log ("timestamp",internal_id);'
    c.execute(query)

    db.commit()

def getVehicleId(scooterData):
    c.execute(
        "SELECT internal_id FROM vehicles WHERE id = ?", (scooterData['id'],))
    r = c.fetchone()
    if (r is None):
        query = "insert into vehicles (id,lastLocationUpdate,lastStateChange,maxSpeed,licencePlate,vin,code,iotVendor) values (?,?,?,?,?,?,?,?)"
        keys = (scooterData['id'], scooterData['lastLocationUpdate'], scooterData['lastStateChange'],
        scooterData['maxSpeed'], scooterData['licencePlate'], scooterData['vin'], scooterData['code'], scooterData['iotVendor'])
        c.execute(query, keys)
        c.execute("SELECT internal_id FROM vehicles WHERE id = ?", (scooterData['id'],))
        r = c.fetchone()
        print("Created new vehicle from id=%s with internal_id=%s" % (str(scooterData['id']), str(r[0])))
    return r[0]

def updateVehicle(vid, scooterData):
    query = "UPDATE vehicles SET lastLocationUpdate = ?, lastStateChange = ?, maxSpeed = ?, licencePlate = ?, vin = ?, code = ? WHERE internal_id = ?"
    keys = (scooterData['lastLocationUpdate'], scooterData['lastStateChange'], scooterData['maxSpeed'], scooterData['licencePlate'], scooterData['vin'], scooterData['code'], vid)
    c.execute(query, keys)

def increaseVehicleLogCounter(vid):
    query = "UPDATE vehicles SET logCounter = logCounter + 1 WHERE internal_id = ?"
    keys = (vid, )
    c.execute(query, keys)

def insertLog(scooterData):

    vid = getVehicleId(scooterData)
    if (not vid is None):

        updateVehicle(vid, scooterData)

        columns = list(scooterData.keys())
        query = "insert into log (timestamp,internal_id,state,batteryLevel,lat,lng,isRentable) values (?,?,?,?,?,?,?) "
        timestamp = datetime.now(timezone.utc).isoformat()
        keys = (timestamp, vid, scooterData['state'], scooterData['batteryLevel'], scooterData['lat'], scooterData['lng'], scooterData['isRentable'])
        c.execute(query, keys)

        print("Inserting log entry for vehicle with ID=%s from %s" % (str(vid), scooterData['lastLocationUpdate']))

        increaseVehicleLogCounter(vid)
    else:
        print("Error: vehicle with %s not found in DB!" % str(scooterData['id']))


def doWeNeedToSaveLocationForVehicle(scooterData):
    vid = getVehicleId(scooterData)

    # look if an entry with same position, batteryLevel and state is already existing in the last 30 minutes
    timestamp = datetime.now(timezone.utc) - timedelta(hours=0, minutes=30) # now minus 30 minutes
    query = "SELECT internal_id FROM log WHERE internal_id = ? AND timestamp > ? AND lat = ? AND lng = ? AND batteryLevel = ? AND state = ? ORDER BY timestamp DESC LIMIT 1"
    keys = (vid, timestamp.isoformat(), scooterData['lat'], scooterData['lng'], scooterData['batteryLevel'], scooterData['state'] )

    c.execute(query, keys)
    r = c.fetchone()
    if (r is None):
        return True
    return False

# ------

if not isTableExisting("log"):
    createLogTable()
if not isTableExisting("vehicles"):
    createVehicleTable()

for scooterData in data:
    if (doWeNeedToSaveLocationForVehicle(scooterData)):
        insertLog(scooterData)

db.commit()
c.close()
