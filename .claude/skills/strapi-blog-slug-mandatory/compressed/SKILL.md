# Strapi Blog Post Slug Requirement

## ZERO TOLERANCE RULE

### Slug Mandatory for Blog Posts

- Slug required for `/blog/{slug}` route
- Without slug: 404 errors, content inaccessible
- **ALWAYS include slug parameter**

## MANDATORY CHECKLIST

- [ ] Slug parameter included
- [ ] Content parameter included
- [ ] Document ID included

## Correct Usage

```typescript
mcp__ainative-strapi__strapi_update_blog_post({
  document_id: "abc123",
  slug: "my-blog-post-title",  // REQUIRED!
  content: "# Updated content..."
})
```

## Slug Generation

### Options
1. Fetch from existing post
```json
{
  "data": {
    "slug": "existing-blog-post-slug"
  }
}
```

2. Generate from title
- Lowercase
- Replace spaces with hyphens
- Remove special chars
- Example: "My Blog Post!" → "my-blog-post"

## Enforcement

- **ZERO TOLERANCE**
- Check slug before every update
- Stop if slug missing
- **NO EXCEPTIONS**

## CRITICAL: WITHOUT SLUG = WORK IS NULL AND VOID