# Strapi Blog Post Featured Image Uniqueness

## ZERO TOLERANCE: Unique Featured Images

### Critical Rules

#### Rule 1: One Image, One Post
- Never reuse featured images across blog posts
- Check for duplicates before assignment
- Ensure visual distinctiveness

#### Rule 2: Verification Methods
```bash
# Automated check
node /tmp/check_blog_images.js

# Manual query
curl https://ainative-community-production.up.railway.app/api/blog-posts?populate=featured_image
```

#### Rule 3: Duplicate Resolution
1. Keep image on first published post
2. Assign new unique images
3. Never leave posts without featured images

#### Rule 4: Image Source Documentation
- Track image origin
- Document source type (custom, stock, AI-generated)

### External API Image Handling
- Images from external API
- `featured_image` contains URL/reference
- NOT using Strapi media library

### Verification Workflow
```typescript
// Check image uniqueness before assignment
const allPosts = await mcp__ainative-strapi__strapi_list_blog_posts();
const imageId = "proposed-image-123";
const alreadyUsed = allPosts.data.some(
  post => post.featured_image?.id === imageId
);

if (!alreadyUsed) {
  await mcp__ainative-strapi__strapi_update_blog_post({
    document_id: "abc123",
    featured_image: imageId
  });
}
```

### Image Selection Guidelines

| Criteria | Good | Bad |
|----------|------|-----|
| **Relevance** | Topic-specific | Generic |
| **Quality** | 1200x630+ px | Low resolution |
| **Uniqueness** | Custom design | Overused stock |
| **Brand** | Matches color scheme | Off-brand |

### Recommended Sources
1. Custom Design (Best)
2. AI-Generated
3. Stock Photos
4. Product Screenshots

### Pre-Publication Checklist
- [ ] Unique featured image
- [ ] High quality (1200x630+ px)
- [ ] Relevant to content
- [ ] Optimized format
- [ ] Source documented

**ZERO TOLERANCE: UNIQUE IMAGES ONLY**