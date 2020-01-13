var sqlite3 = require('sqlite3').verbose();
var express = require('express');
var restapi = express();

restapi.use(function(req, res, next) {
  res.header("Access-Control-Allow-Origin", "*");
  res.header("Access-Control-Allow-Headers", "Origin, X-Requested-With, Content-Type, Accept");
  res.header('Cache-Control', 'private, no-cache, no-store, must-revalidate');
  res.header('Expires', '-1');
  res.header('Pragma', 'no-cache');
  next();
});
restapi.use(express.json());


restapi.get('/vehicles', function(request, res) {
  var resultv = {
    "rows": []
  };
  var keys = [];
  var select = "SELECT * " +
    "FROM vehicles";
  var where_filter = "";

  var vehicle_id = request.query.vehicle_id;
  if (vehicle_id)
  {
    if (where_filter.length == 0)
    {
      where_filter += "WHERE ";
    }
    where_filter += " internal_id = ?"
    keys.push(vehicle_id);
  }

  var id = request.query.id;
  if (id)
  {
    if (where_filter.length == 0)
    {
      where_filter += "WHERE ";
    }
    where_filter += " id = ?"
    keys.push(id);
  }

  var query = select + " " + where_filter + "";

  var db = new sqlite3.Database("data.db");
  db.all(query, keys, function(err, rows) {
    if (err) {
      return console.error(err.message);
    }
    if (rows) {
      rows.forEach((row) => {
        resultv['rows'].push(row);
      });
    }

    res.contentType('application/json');
    res.send(JSON.stringify(resultv));
  });
});


restapi.get('/current', function(request, res) {
  var resultv = {
    "rows": []
  };
  var keys = [];
  var select = "SELECT * FROM vehicles " +
    "LEFT JOIN log ON log.internal_id = vehicles.internal_id AND log.timestamp >= vehicles.lastLocationUpdate ";

  var group = " GROUP BY vehicles.internal_id ORDER BY timestamp DESC";
  var where_filter = "";

  var vehicle_id = request.query.vehicle_id;
  if (vehicle_id)
  {
    if (where_filter.length == 0)
    {
      where_filter += "WHERE ";
    }
    where_filter += " internal_id = ?"
    keys.push(vehicle_id);
  }

  var id = request.query.id;
  if (id)
  {
    if (where_filter.length == 0)
    {
      where_filter += "WHERE ";
    }
    where_filter += " id = ?"
    keys.push(id);
  }

  var query = select + " " + where_filter + group;

  var db = new sqlite3.Database("data.db");
  db.all(query, keys, function(err, rows) {
    if (err) {
      return console.error(err.message);
    }
    if (rows) {
      rows.forEach((row) => {
        resultv['rows'].push(row);
      });
    }

    res.contentType('application/json');
    res.send(JSON.stringify(resultv));
  });
});




restapi.get('/log', function(request, res) {
  result = {
    "rows": []
  };
  var keys = [];
  var select = "SELECT * " +
    "FROM log";

  var where_filter = "";

  var vehicle_id = request.query.vehicle_id;
  if (vehicle_id)
  {
    if (where_filter.length == 0)
    {
      where_filter += "WHERE ";
    }
    where_filter += " internal_id = ?"
    keys.push(vehicle_id);
  }
  var timespan = request.query.timespan;
  if (timespan)
  {
    if (where_filter.length == 0)
    {
      where_filter += "WHERE ";
    }
    else {
      where_filter += " AND ";
    }
    where_filter += " timestamp >= ?"

    if (timespan == "today")
    {
        keys.push(new Date(new Date().setHours(0,0,0,0)).toISOString());
    }
  }

  var query = select + " " + where_filter + " ORDER BY timestamp ASC";

  var db = new sqlite3.Database("data.db");
  db.all(query, keys, function(err, rows) {
    if (err) {
      return console.error(err.message);
    }
    if (rows) {
      rows.forEach((row) => {
        result['rows'].push(row);
      });
    }

    res.contentType('application/json');
    res.send(JSON.stringify(result));
  });
});


const port = 3000;
restapi.listen(port);
console.log("Running on port " + port);
