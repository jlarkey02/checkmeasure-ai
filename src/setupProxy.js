const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
  // Proxy all /api requests to the backend
  app.use(
    '/api',
    createProxyMiddleware({
      target: 'http://localhost:8000',
      changeOrigin: true,
      timeout: 0,  // No timeout for requests
      proxyTimeout: 0,  // No timeout for proxy connection
      ws: false,  // We don't use WebSockets for API
      onError: (err, req, res) => {
        console.error('Proxy error:', err);
        res.status(502).json({ error: 'Backend connection failed' });
      },
      onProxyReq: (proxyReq, req, res) => {
        // Log proxied requests for debugging
        console.log(`Proxying ${req.method} ${req.url} -> ${proxyReq.path}`);
      }
    })
  );

  // Also proxy /health endpoint directly
  app.use(
    '/health',
    createProxyMiddleware({
      target: 'http://localhost:8000',
      changeOrigin: true,
      timeout: 0,
      proxyTimeout: 0,
      ws: false
    })
  );
};