# Production Deployment Checklist

## Pre-Deployment

- [ ] Review and update `.env` file with production credentials
- [ ] Set `FLASK_ENV=production` in environment
- [ ] Generate a strong `SECRET_KEY`
- [ ] Test application in development mode first
- [ ] Verify all dependencies are listed in `requirements.txt`

## Security

- [ ] Enable SSL/HTTPS in production
- [ ] Set `SESSION_COOKIE_SECURE=True` for HTTPS
- [ ] Configure firewall rules for port access
- [ ] Restrict database/session file permissions
- [ ] Review and secure log file access

## Infrastructure

- [ ] Configure reverse proxy (nginx/Apache)
- [ ] Set up process manager (systemd/supervisor)
- [ ] Configure log rotation
- [ ] Set up monitoring and alerting
- [ ] Configure backup strategy for session data

## Performance

- [ ] Tune Gunicorn worker count based on CPU cores
- [ ] Configure connection timeouts
- [ ] Set up static file serving via reverse proxy
- [ ] Enable gzip compression
- [ ] Configure caching headers

## Monitoring

- [ ] Set up application monitoring
- [ ] Configure log aggregation
- [ ] Set up health checks
- [ ] Configure error alerting
- [ ] Monitor SSE API rate limits

## Testing

- [ ] Test authentication flow
- [ ] Test tenant CRUD operations
- [ ] Test bulk operations
- [ ] Test error handling
- [ ] Test session persistence
- [ ] Load test the application

## Documentation

- [ ] Update README with production-specific instructions
- [ ] Document deployment procedures
- [ ] Document backup/restore procedures
- [ ] Document troubleshooting steps
