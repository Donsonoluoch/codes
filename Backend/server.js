// backend/server.js
const express = require('express');
const http = require('http');
const { Server } = require('socket.io');
const { createClient } = require('redis');
const { InfluxDB, Point } = require('@influxdata/influxdb-client');
const cors = require('cors');

const app = express();
app.use(cors());
app.use(express.json());

const server = http.createServer(app);
const io = new Server(server, { cors: { origin: "*" } });

// --- Configuration ---
const INFLUX_URL = 'http://localhost:8086';
const INFLUX_TOKEN = 'my-super-secret-token';
const INFLUX_ORG = 'my-org';
const INFLUX_BUCKET = 'market-data';

// --- Database Connections ---
// 1. InfluxDB Setup
const influxClient = new InfluxDB({ url: INFLUX_URL, token: INFLUX_TOKEN });
const writeApi = influxClient.getWriteApi(INFLUX_ORG, INFLUX_BUCKET);

// 2. Redis Setup
const redisPublisher = createClient();
const redisSubscriber = createClient();

async function startServer() {
    await redisPublisher.connect();
    await redisSubscriber.connect();

    // --- Redis Pub/Sub Logic ---
    // When Redis receives a message on 'stock-updates', send it to frontend via Socket.io
    await redisSubscriber.subscribe('stock-updates', (message) => {
        const data = JSON.parse(message);
        io.emit('new-data', data); // Broadcast to all connected React clients
    });

    // --- Ingestion Endpoint (Simulates receiving data from distributed sources) ---
    app.post('/ingest', async (req, res) => {
        const { value, time } = req.body; // Expecting { value: 105.2, time: 167... }

        // A. Save to InfluxDB (Cold Storage)
        const point = new Point('stock_price')
            .floatField('value', value)
            .timestamp(new Date(time * 1000)); // Influx expects ms or Date object
        writeApi.writePoint(point);
        await writeApi.flush();

        // B. Publish to Redis (Hot Path)
        // We only send minimal data needed for the UI
        await redisPublisher.publish('stock-updates', JSON.stringify({
            time: time,
            value: value
        }));

        res.sendStatus(200);
    });

    server.listen(4000, () => {
        console.log('Server running on port 4000');
    });
}

startServer();