const fs = require("fs");
const https = require("https");
const express = require("express");

const app = express();

const options = {
  key: fs.readFileSync("server.key"),
  cert: fs.readFileSync("server.cert"),
};

app.get("/", (req, res) => {
  res.send("Hello, HTTPS!");
});

https.createServer(options, app).listen(3000, () => {
  console.log("Server running on https://127.0.0.1:3000");
});

