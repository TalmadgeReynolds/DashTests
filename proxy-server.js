const express = require('express');
const { createProxyMiddleware } = require('http-proxy-middleware');
const cors = require('cors');

const app = express();
const port = 3001;

// Enable CORS
app.use(cors());

// Proxy middleware for /jobs requests
app.use('/jobs', createProxyMiddleware({
  target: 'http://localhost:8000',
  pathRewrite: {
    '^/jobs': '/api/v1/jobs'
  },
  changeOrigin: true
}));

// Start the server
app.listen(port, () => {
  console.log(`Proxy server running at http://localhost:${port}`);
});