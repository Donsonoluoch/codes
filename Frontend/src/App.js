// frontend/src/App.js
import React, { useEffect, useRef } from 'react';
import { createChart } from 'lightweight-charts';
import io from 'socket.io-client';

const socket = io('http://localhost:4000');

function App() {
  const chartContainerRef = useRef();
  const seriesRef = useRef();

  useEffect(() => {
    // 1. Create the Chart
    const chart = createChart(chartContainerRef.current, {
      width: 800,
      height: 400,
      layout: {
        backgroundColor: '#253248',
        textColor: 'rgba(255, 255, 255, 0.9)',
      },
      grid: {
        vertLines: { color: '#334158' },
        horzLines: { color: '#334158' },
      },
      timeScale: {
        timeVisible: true,
        secondsVisible: true,
      },
    });

    // 2. Add an Area Series (Line chart with fill)
    const areaSeries = chart.addAreaSeries({
      topColor: 'rgba(33, 150, 243, 0.56)',
      bottomColor: 'rgba(33, 150, 243, 0.04)',
      lineColor: 'rgba(33, 150, 243, 1)',
      lineWidth: 2,
    });
    
    seriesRef.current = areaSeries;

    // 3. Listen for Real-Time Updates via Socket.io
    socket.on('new-data', (data) => {
      // data format: { time: 1234567890, value: 105.20 }
      areaSeries.update(data);
    });

    return () => {
      chart.remove();
      socket.off('new-data');
    };
  }, []);

  return (
    <div style={{ display: 'flex', justifyContent: 'center', marginTop: '50px' }}>
      <div>
        <h2>Distributed Real-Time Chart</h2>
        <div ref={chartContainerRef} />
      </div>
    </div>
  );
}

export default App;