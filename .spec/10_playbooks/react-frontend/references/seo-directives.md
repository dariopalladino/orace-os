---
title: SEO Indexability for React + Python Blog
type: engineering-spec
scope:
  - public blog pages
  - crawlability
  - search indexing
  - metadata
  - sitemap
  - robots
  - redirects
  - structured data
stack:
  frontend: React
  backend: Python
load_when:
  - implementing blog routing
  - implementing SSR or prerendering
  - adding SEO metadata
  - generating sitemap or robots.txt
  - debugging indexing issues
  - changing canonical URLs or redirects
do_not_load_when:
  - working only on authenticated dashboard features
  - changing internal APIs unrelated to public content
  - making visual-only UI changes with no routing or metadata impact
success_criteria:
  - public article content is present in initial HTML
  - every published article has a stable crawlable URL
  - sitemap contains all indexable canonical pages
  - robots.txt permits crawling of public content
  - nonexistent pages return 404
  - moved pages return 301
  - indexable pages do not contain noindex
---

# Objective

Make all public blog content reliably discoverable, crawlable, renderable, and indexable by Google, Bing, and standards-compliant search crawlers.

Do not rely on client-side JavaScript execution as the only way to obtain article content.

# Requirements

## 1. Render public content into initial HTML

Public blog routes MUST return meaningful HTML containing the article content.

Preferred approaches, in order:

1. Static generation / prerendering for published articles.
2. Server-side rendering for dynamically generated pages.
3. Client-side rendering only for non-SEO-critical application areas.

A request such as:

```bash
curl -L https://example.com/blog/article-slug
```

MUST return the article title and body in the HTML response.

The implementation SHOULD NOT require the crawler to:

```text
load empty React shell
→ execute JavaScript
→ fetch API
→ render article
```

The existing Python backend MAY remain the source of content.

## 2. Use canonical, crawlable routes

Each published article MUST have one stable URL:

```text
/blog/{slug}
```

Prefer:

```text
/blog/react-seo
```

Avoid:

```text
/#/blog/react-seo
```

Query parameters MUST NOT be required to identify the canonical article.

## 3. Add page-specific metadata

Every indexable page MUST provide server-rendered or prerendered:

```html
<title>...</title>
<meta name="description" content="...">
<link rel="canonical" href="...">
```

Article pages SHOULD also include:

```html
<meta property="og:title" content="...">
<meta property="og:description" content="...">
<meta property="og:image" content="...">
<meta property="og:url" content="...">
```

Metadata MUST reflect the current article and MUST NOT be identical across all posts.

## 4. Add structured data

Published article pages SHOULD expose JSON-LD using `BlogPosting` or `Article`.

Include when available:

```text
headline
description
datePublished
dateModified
author
canonical URL
image
```

Structured data MUST describe visible page content accurately.

## 5. Generate an XML sitemap

Expose:

```text
/sitemap.xml
```

The sitemap MUST include all canonical, published, indexable URLs.

It MUST exclude:

```text
drafts
private pages
admin pages
API endpoints
non-canonical duplicates
```

Include accurate `lastmod` values when reliable modification timestamps exist.

Generate the sitemap from the application's source of truth rather than maintaining URLs manually.

For large sites, support sitemap indexes and multiple sitemap files.

## 6. Provide robots.txt

Expose:

```text
/robots.txt
```

Default behavior:

```text
User-agent: *
Allow: /

Sitemap: https://example.com/sitemap.xml
```

Private or irrelevant application areas MAY be disallowed.

Do not block assets required for rendering public pages.

Public blog pages MUST NOT be blocked.

## 7. Keep API endpoints out of search results

Python API endpoints SHOULD NOT be treated as search landing pages.

Where appropriate:

```text
Disallow: /api/
```

Public HTML pages remain indexable independently of API routes.

## 8. Use crawlable internal links

Navigation to articles MUST use normal crawlable links.

Preferred:

```html
<a href="/blog/article-slug">...</a>
```

React Router links are acceptable when they resolve to real URLs.

Do not make essential content discoverable only through:

```text
onClick handlers
JavaScript-only state
client-side search
infinite-scroll events
```

## 9. Make pagination crawlable

If article listings are paginated or infinite-scrolling, expose stable paginated URLs such as:

```text
/blog/page/1
/blog/page/2
/blog/page/3
```

or an equivalent crawlable scheme.

Each page MUST contain normal links to other relevant pages.

Infinite scroll MAY exist as a UX enhancement but MUST NOT be the only discovery mechanism.

## 10. Return correct HTTP status codes

For existing canonical pages:

```text
200
```

For nonexistent pages:

```text
404
```

Do not return `200` with an "article not found" UI.

For permanently moved pages:

```text
301
```

redirecting to the new canonical URL.

Temporary redirects MUST use the appropriate temporary status instead.

## 11. Prevent accidental de-indexing

Indexable pages MUST NOT emit:

```html
<meta name="robots" content="noindex">
```

unless explicitly required by product rules.

Check both HTML metadata and response headers for indexing directives.

## 12. Keep public articles unauthenticated

Search crawlers MUST be able to request published blog URLs without:

```text
login
session cookie
Authorization header
client-side authentication bootstrap
```

Authentication MAY remain mandatory for private application routes.

# Recommended Architecture

Preferred public-content flow:

```text
Crawler / Browser
      ↓
React framework with SSR or static generation
      ↓
Python API / service layer
      ↓
Database
```

The Python backend SHOULD remain responsible for domain data.

The frontend rendering layer SHOULD transform that data into crawlable HTML.

For mostly static blog content, prefer build-time or publish-time static generation.

# Acceptance Tests

An implementation is complete only when all applicable tests pass.

## HTML rendering

For a published article:

```bash
curl -L https://example.com/blog/test-post
```

Expected:

- HTTP 200
- article `<title>` exists
- article `<h1>` exists
- meaningful article body exists
- canonical URL exists
- description exists

Failure condition:

```html
<div id="root"></div>
```

with no article content in the initial response.

## Sitemap

Request:

```text
GET /sitemap.xml
```

Verify:

- returns valid XML
- returns HTTP 200
- contains published canonical posts
- excludes drafts
- excludes deleted posts
- excludes `/api/`
- excludes admin/private routes

## Robots

Request:

```text
GET /robots.txt
```

Verify:

- returns HTTP 200
- public blog routes are crawlable
- sitemap URL is declared
- no accidental `Disallow: /`

## Routing

Verify:

```text
existing article      → 200
missing article       → 404
renamed article       → 301 → canonical article
canonical article     → no redirect loop
```

## Metadata

For at least two different posts, verify:

```text
title differs
description differs
canonical differs
structured data matches page
```

# Implementation Order

Execute in this order unless repository constraints require otherwise:

1. Inspect current rendering behavior with raw HTTP requests.
2. Ensure public article routes render complete HTML.
3. Establish canonical `/blog/{slug}` routing.
4. Implement dynamic page metadata.
5. Implement canonical tags.
6. Implement structured data.
7. Implement sitemap generation.
8. Implement robots.txt.
9. Fix internal linking and pagination.
10. Correct 404 and redirect behavior.
11. Add automated SEO/indexability tests.
12. Verify production URLs with search-engine webmaster tools.

# Guardrails

Do not:

```text
rewrite the Python backend solely for SEO
duplicate article data in the frontend
maintain article URLs manually
depend solely on JavaScript rendering
index authenticated pages
index API responses as article pages
return HTTP 200 for missing resources
use hash-based routing for public content
```

Prefer standards-based HTML and HTTP behavior over crawler-specific workarounds.

# Definition of Done

The feature is complete when:

```text
a crawler can discover an article via internal links or sitemap
→ request its canonical URL
→ receive HTTP 200
→ read its title, metadata, structured data, and article body from initial HTML
→ follow additional crawlable links
```

without requiring authenticated access or client-side JavaScript execution.