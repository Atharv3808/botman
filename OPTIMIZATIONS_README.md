# Botman Performance & AI Resilience Optimizations

This document summarizes the recent performance audits, optimizations, and AI resilience features implemented in the Botman platform.

## 🚀 Performance Optimizations

### Backend Improvements
- **Payload Compression**: Enabled `GZipMiddleware` to compress JSON responses, significantly reducing network transfer time for data-heavy endpoints.
- **Global Pagination**: Implemented `PageNumberPagination` across all REST framework views with a default `PAGE_SIZE` of 20. This prevents UI "white screen" crashes and reduces initial data load times.
- **Database Query Optimization**: 
    - Integrated `select_related` and `prefetch_related` in `ChatbotViewSet` and `ConversationHistoryViewSet` to eliminate N+1 query problems.
    - Added database-level annotations for message counts in list views.
- **Smart Caching**: 
    - Implemented a 5-minute cache for historical analytics data.
    - Added a 30-second cache for live bot statistics to reduce database pressure during high-traffic sessions.
- **Async Logging**: Migrated request and system logging to background Celery tasks, ensuring that monitoring does not block user requests.

### AI Resilience & SDK Migration
- **Gemini SDK Migration**: Successfully migrated from the deprecated `google-generativeai` to the modern `google-genai` SDK, using the `gemini-2.0-flash` and `text-embedding-004` models.
- **Exponential Backoff**: Implemented automatic retries using the `backoff` library for all Gemini API calls (LLM and Embeddings). This gracefully handles `429 RESOURCE_EXHAUSTED` errors by retrying with exponential delays.
- **Fallback Mechanism**: If the primary model (`gemini-2.0-flash`) hits a persistent quota limit, the system automatically attempts a fallback to `gemini-1.5-flash` to ensure service continuity.

### Frontend Improvements
- **Code Splitting & Lazy Loading**: Converted all major routes in `App.jsx` to use `React.lazy` and `Suspense`, resulting in a significantly smaller initial JS bundle.
- **Vite Build Optimization**: Configured manual chunking for heavy dependencies (Firebase, Lucide-React, React core) to improve browser caching and parallel loading.
- **Hydration Fixes**: Resolved invalid HTML nesting in `ChatPreview.jsx` (replacing `<p>` with `<div>` for markdown content containing code blocks) to prevent React hydration errors.

---

## 🛠 Widget Fixes & Deployment

### Dynamic Configuration
The `widget.js` script has been overhauled to support live deployments:
- **Auto-Origin Detection**: The widget now automatically detects the API base URL from its own script `src` attribute. No more hardcoded `localhost:8000`.
- **Flexible Bot Lookup**: The backend now supports looking up bots via both numeric `id` and UUID `widget_token`.
- **CORS & Security**: Configured `ALLOWED_HOSTS=*` and `CORS_ALLOW_ALL_ORIGINS` to ensure the widget can be embedded on external domains.

### Embedding the Widget
To embed the Botman widget on your site, use the following snippet:

```html
<script 
  src="http://15.206.28.131/static/widgets/widget.js" 
  data-bot-id="YOUR_BOT_ID" 
  async>
</script>
```

---

## 📈 Performance Targets
- **API Response Time**: < 200ms (Average)
- **Initial Page Load**: < 3s (4G connection)
- **AI Reliability**: 99.9% success rate on API calls through retry logic.

## 📋 Maintenance
- Ensure Redis is running for caching and Celery tasks.
- Static files should be collected using `python manage.py collectstatic` after any changes to `widget.js`.
