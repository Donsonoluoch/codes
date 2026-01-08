// backend/producer.js
const axios = require('axios');

let price = 100;

// Function to generate a random walk price (simulating stock movement)
function generateData() {
    const change = (Math.random() - 0.5) * 2; // Random value between -1 and 1
    price += change;
    
    // Lightweight-charts expects seconds for timestamp
    const payload = {
        time: Math.floor(Date.now() / 1000), 
        value: parseFloat(price.toFixed(2))
    };

    // Send to our Main Server
    axios.post('http://localhost:4000/ingest', payload)
        .then(() => console.log(`Sent: $${payload.value}`))
        .catch(err => console.error("Server offline?"));
}

// Generate data every 500ms
setInterval(generateData, 500);