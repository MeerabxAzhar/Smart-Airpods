// server.js (Node.js - Optional Proxy)
const express = require('express');
const cors = require('cors');
const { createProxyMiddleware } = require('http-proxy-middleware');

const app = express();
app.use(cors());

app.use('/api', createProxyMiddleware({
  target: 'http://localhost:5000',
  changeOrigin: true,
}));

app.listen(3001, () => {
  console.log('Proxy server running on port 3001');
});