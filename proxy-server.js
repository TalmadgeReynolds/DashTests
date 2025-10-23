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

// Proxy middleware for /prompts requests
app.use('/prompts', createProxyMiddleware({
  target: 'http://localhost:8000',
  pathRewrite: {
    '^/prompts': '/api/v1/prompts'
  },
  changeOrigin: true,
  logLevel: 'debug',
  onProxyReq: (proxyReq, req) => {
    console.log(`Proxying request: ${req.method} ${req.path} -> ${proxyReq.path}`);
  },
  onProxyRes: (proxyRes, req) => {
    console.log(`Received response: ${proxyRes.statusCode} for ${req.method} ${req.path}`);
  }
}));

// Proxy middleware for /screenplays requests
app.use('/screenplays', createProxyMiddleware({
  target: 'http://localhost:8000',
  pathRewrite: {
    '^/screenplays': '/api/v1/screenplays'
  },
  changeOrigin: true
}));

// Start the server
app.listen(port, () => {
  console.log(`Proxy server running at http://localhost:${port}`);
});