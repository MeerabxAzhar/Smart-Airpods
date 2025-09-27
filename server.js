const express = require('express');
const cors = require('cors');
const { createProxyMiddleware } = require('http-proxy-middleware');

const app = express();
const PORT = process.env.PORT || 3001;

// Enable CORS for all routes
app.use(cors());

// Proxy requests starting with /api to the Flask backend
app.use('/api', createProxyMiddleware({
  target: 'http://localhost:5000', // Your Flask backend
  changeOrigin: true,
}));

// Simple test endpoint
app.get('/api/hello', (req, res) => {
  res.send({ message: 'Hello from backend!' });
});

// Start the server with error handling
app.listen(PORT, () => {
  console.log(`Proxy server running on port ${PORT}`);
}).on('error', (err) => {
  if (err.code === 'EADDRINUSE') {
    console.error(`❌ Port ${PORT} is already in use. Please try a different one.`);
  } else {
    console.error(err);
  }
});
