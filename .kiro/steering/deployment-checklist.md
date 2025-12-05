# Deployment Checklist

## Pre-Deployment

- [ ] All tests passing
- [ ] Database migrations created and tested
- [ ] Environment variables documented
- [ ] API keys secured
- [ ] CORS configured for production domains
- [ ] Rate limiting enabled
- [ ] Logging configured

## Database

- [ ] Run `alembic upgrade head` on production
- [ ] Verify all tables created
- [ ] Check indexes are in place
- [ ] Backup strategy configured
- [ ] Connection pooling configured

## Backend Deployment

- [ ] Build Docker image
- [ ] Deploy to Cloud Run
- [ ] Set environment variables
- [ ] Configure Cloud SQL connection
- [ ] Enable Cloud KMS for API keys
- [ ] Setup Redis/Memorystore
- [ ] Configure auto-scaling (min=1, max=20)
- [ ] Test health endpoint
- [ ] Verify authentication works
- [ ] Test agent execution

## Frontend Deployment

- [ ] Build production bundle (`npm run build`)
- [ ] Set VITE_API_URL to production backend
- [ ] Upload to Cloud Storage
- [ ] Configure CDN (optional)
- [ ] Test all pages load
- [ ] Verify API calls work
- [ ] Check authentication flow
- [ ] Test agent creation and execution

## Post-Deployment

- [ ] Monitor logs for errors
- [ ] Check credit system working
- [ ] Verify email sending (password reset)
- [ ] Test OAuth flows
- [ ] Monitor performance metrics
- [ ] Setup alerts for errors
- [ ] Document rollback procedure

## Security

- [ ] JWT_SECRET_KEY is strong
- [ ] Database has no public IP
- [ ] API keys encrypted with KMS
- [ ] HTTPS enforced
- [ ] Rate limiting active
- [ ] CORS properly configured
- [ ] Secrets in Secret Manager

## Monitoring

- [ ] Cloud Logging enabled
- [ ] Error tracking configured
- [ ] Performance monitoring active
- [ ] Budget alerts set
- [ ] Uptime checks configured
