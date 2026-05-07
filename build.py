#!/usr/bin/env python3
"""
Netlify 构建脚本：把 _posts/*.md 转成 posts/*.html
并更新 blogs.html 和 index.html
"""
import os, re, html as htmllib
from pathlib import Path

PROJECT = Path(__file__).parent

MONTHS_LONG = ['January','February','March','April','May','June',
               'July','August','September','October','November','December']
MONTHS_SHORT = ['Jan','Feb','Mar','Apr','May','Jun',
                'Jul','Aug','Sep','Oct','Nov','Dec']

def fmt_long(d):
    y, m, day = d.split('-')
    return f'{MONTHS_LONG[int(m)-1]} {int(day)}, {y}'

def fmt_short(d):
    y, m, day = d.split('-')
    return f'{MONTHS_SHORT[int(m)-1]} {int(day)}, {y}'

def slugify(text):
    text = text.strip()
    text = re.sub(r'[^\w\u4e00-\u9fff-]', '-', text)
    text = re.sub(r'-+', '-', text).strip('-')
    return text[:60] or 'untitled'

def parse_frontmatter(content):
    """解析 YAML frontmatter，返回 (meta_dict, body_str)"""
    meta = {}
    if not content.startswith('---'):
        return meta, content
    end = content.find('\n---', 3)
    if end == -1:
        return meta, content
    fm = content[3:end].strip()
    body = content[end+4:].strip()
    for line in fm.splitlines():
        if ':' in line:
            k, _, v = line.partition(':')
            meta[k.strip()] = v.strip().strip('"\'')
    return meta, body

def md_to_html(text):
    """Markdown → HTML（支持段落/标题/粗体/引用/列表/链接/图片）"""
    lines = text.split('\n')
    blocks, buf = [], []

    def flush():
        if buf:
            blocks.append(('p', '\n'.join(buf)))
            buf.clear()

    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith('### '):
            flush(); blocks.append(('h3', line[4:]))
        elif line.startswith('## '):
            flush(); blocks.append(('h2', line[3:]))
        elif line.startswith('# '):
            flush(); blocks.append(('h1', line[2:]))
        elif line.startswith('> '):
            flush(); blocks.append(('bq', line[2:]))
        elif line.startswith('- ') or line.startswith('* '):
            flush()
            items = []
            while i < len(lines) and (lines[i].startswith('- ') or lines[i].startswith('* ')):
                items.append(lines[i][2:])
                i += 1
            blocks.append(('ul', items))
            continue
        elif line.strip() == '':
            flush()
        else:
            buf.append(line)
        i += 1
    flush()

    def inline(text):
        # images before links
        text = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', r'<img src="\2" alt="\1">', text)
        text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
        text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
        return text

    parts = []
    for kind, val in blocks:
        if kind == 'h1':
            parts.append(f'<h1>{inline(val)}</h1>')
        elif kind == 'h2':
            parts.append(f'<h2>{inline(val)}</h2>')
        elif kind == 'h3':
            parts.append(f'<h3>{inline(val)}</h3>')
        elif kind == 'bq':
            parts.append(f'<blockquote><p>{inline(val)}</p></blockquote>')
        elif kind == 'ul':
            lis = ''.join(f'<li>{inline(v)}</li>' for v in val)
            parts.append(f'<ul>{lis}</ul>')
        elif kind == 'p':
            joined = ' '.join(val.splitlines())
            if joined.strip():
                parts.append(f'<p>{inline(joined)}</p>')
    return '\n      '.join(parts)

def get_excerpt(body_md, max_chars=90):
    for line in body_md.splitlines():
        line = line.strip()
        if line and not line.startswith('#') and not line.startswith('>') and not line.startswith('!'):
            text = re.sub(r'\*\*(.+?)\*\*', r'\1', line)
            text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
            return text[:max_chars].rstrip() + ('…' if len(text) > max_chars else '')
    return ''

POST_STYLE = """
  <style>
    .post-header { padding: 80px 0 48px; border-bottom: 1px solid var(--border); margin-bottom: 56px; }
    .post-date { font-size: 11px; letter-spacing: 3px; text-transform: uppercase; color: var(--muted); margin-bottom: 20px; }
    .post-header h1 { font-size: clamp(1.8rem, 4vw, 3rem); font-weight: 300; letter-spacing: -1px; line-height: 1.2; color: var(--text); }
    .post-content { max-width: 660px; padding-bottom: 120px; }
    .post-content p { font-size: 16.5px; line-height: 1.9; color: var(--prose); margin-bottom: 1.6em; }
    .post-content p:empty { display: none; }
    .post-content h2, .post-content h3 { font-weight: 400; margin: 2.4em 0 0.8em; letter-spacing: -0.3px; color: var(--text); }
    .post-content h2 { font-size: 1.35rem; }
    .post-content h3 { font-size: 1.05rem; color: var(--accent); }
    .post-content img { width: 100%; border-radius: 10px; margin: 2.4em 0; border: 1px solid var(--border); box-shadow: 0 2px 12px rgba(0,0,0,0.07); }
    .post-content a { color: var(--accent); text-decoration: underline; text-underline-offset: 3px; }
    .post-content blockquote { border-left: 2px solid var(--border); padding-left: 24px; margin: 2.4em 0; color: var(--muted); font-style: italic; }
    .post-content ul, .post-content ol { padding-left: 24px; margin-bottom: 1.6em; color: var(--prose); }
    .post-content li { margin-bottom: 0.5em; line-height: 1.85; font-size: 16.5px; }
    .post-content strong { color: var(--text); font-weight: 500; }
    .back-link { display: inline-flex; align-items: center; gap: 6px; font-size: 13px; color: var(--muted); text-decoration: none; margin-bottom: 48px; letter-spacing: 0.3px; transition: color 0.2s; }
    .back-link:hover { color: var(--accent); }
  </style>"""

NAV = """\
  <header>
    <nav>
      <a class="nav-brand" href="../index.html">Lumiere Feng</a>
      <button class="nav-toggle" aria-label="Toggle menu" aria-expanded="false">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
          <path d="M4 7h16M4 12h16M4 17h16"/>
        </svg>
      </button>
      <ul class="nav-links">
        <li><a href="../index.html">Home</a></li>
        <li class="nav-dropdown">
          <button class="active">Writings <span class="dropdown-arrow">&#9662;</span></button>
          <ul class="dropdown-menu">
            <li><a href="../blogs.html">Blogs</a></li>
            <li><button type="button" data-qr-src="../images/writings-wechat.jpg" data-qr-title="微信公众号">微信公众号</button></li>
            <li><button type="button" data-qr-src="../images/writings-rednote.jpg" data-qr-title="小红书">小红书</button></li>
          </ul>
        </li>
        <li class="nav-dropdown">
          <button>Podcast <span class="dropdown-arrow">&#9662;</span></button>
          <ul class="dropdown-menu">
            <li><a href="https://podcasts.apple.com/hk/podcast/the-good-place%E5%A5%BD%E5%9C%B0%E6%96%B9/id1711323222" target="_blank">Apple Podcast</a></li>
            <li><a href="https://www.instagram.com/the.good.place_podcast" target="_blank">Instagram</a></li>
            <li><a href="https://www.xiaoyuzhoufm.com/podcast/652570afb292e77709a3cefe" target="_blank">小宇宙</a></li>
            <li><a href="https://mp.weixin.qq.com/mp/appmsgalbum?__biz=Mzg3NDAyNzYxNw==&amp;action=getalbum&amp;album_id=4346635139062349828#wechat_redirect" target="_blank">微信公众号</a></li>
          </ul>
        </li>
        <li><a href="../photography.html">Album</a></li>
        <li><a href="../videography.html">Videography</a></li>
        <li><a href="../resources.html">Resources</a></li>
      </ul>
    </nav>
  </header>"""

FOOTER = """\
  <footer>
    <div class="footer-inner">
      <div>
        <a class="footer-brand" href="../index.html">Lumiere Feng</a>
        <p class="footer-quote">"In a relatively good place"</p>
      </div>
      <div>
        <p class="footer-col-label">Email</p>
        <a class="footer-email" href="mailto:lumierefpx@gmail.com">lumierefpx@gmail.com</a>
      </div>
    </div>
    <div class="footer-bottom">
      <span class="footer-copy">&#169; Lumiere Feng</span>
      <span class="footer-copy">lumierefeng.com</span>
    </div>
  </footer>"""

# ── 读取所有 _posts/*.md ──────────────────────────────────
posts_dir = PROJECT / '_posts'
posts_dir.mkdir(exist_ok=True)
posts = []

for md_file in sorted(posts_dir.glob('*.md'), reverse=False):
    content = md_file.read_text(encoding='utf-8')
    meta, body = parse_frontmatter(content)

    title = meta.get('title', md_file.stem)
    post_date = meta.get('date', '2025-01-01')[:10]
    category = meta.get('category', 'Writing')
    excerpt = meta.get('excerpt', '') or get_excerpt(body)

    posts.append({
        'title': title,
        'date': post_date,
        'category': category,
        'excerpt': excerpt,
        'body': body,
        'slug': slugify(title),
        'md_file': md_file.name,
    })

# 按日期降序
posts.sort(key=lambda x: x['date'], reverse=True)

if not posts:
    print('No markdown posts found in _posts/, skipping build.')
    exit(0)

# ── 生成 posts/*.html ─────────────────────────────────────
(PROJECT / 'posts').mkdir(exist_ok=True)

post_records = []
for p in posts:
    fname = f"posts/{p['slug']}.html"
    content_html = md_to_html(p['body'])

    html = f"""<!DOCTYPE html>
<html lang="zh">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{htmllib.escape(p['title'])} — Lumiere Feng</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="../css/style.css">{POST_STYLE}
</head>
<body>
{NAV}
  <main class="page">
    <div class="post-header">
      <p class="post-date">{p['date']}</p>
      <h1>{htmllib.escape(p['title'])}</h1>
    </div>
    <div class="post-content">
      <a class="back-link" href="../blogs.html">← Blogs</a>
      {content_html}
    </div>
  </main>
{FOOTER}
  <script src="../js/main.js"></script>
</body>
</html>"""

    (PROJECT / fname).write_text(html, encoding='utf-8')
    post_records.append({'title': p['title'], 'date': p['date'],
                         'category': p['category'], 'excerpt': p['excerpt'],
                         'href': fname})
    print(f'  post: {fname}')

# ── 更新 blogs.html ───────────────────────────────────────
blogs_path = PROJECT / 'blogs.html'
blogs_html = blogs_path.read_text(encoding='utf-8')

feed_items = []
years_seen = []
for pr in post_records:
    year = pr['date'][:4]
    if year not in years_seen:
        years_seen.append(year)
        feed_items.append(
            f'          <div class="year-group" data-year="{year}">\n'
            f'            <div class="year-divider">{year}</div>'
        )
    exc = htmllib.escape(pr['excerpt'])
    feed_items.append(
        f'            <a class="feed-item" href="{pr["href"]}">\n'
        f'              <div class="feed-item-inner">\n'
        f'                <div class="feed-body">\n'
        f'                  <span class="feed-title">{htmllib.escape(pr["title"])}</span>\n'
        f'                  <p class="feed-excerpt">{exc}</p>\n'
        f'                  <div class="feed-meta"><span>{fmt_long(pr["date"])}</span>'
        f'<span class="feed-meta-dot"></span><span>{pr["category"]}</span></div>\n'
        f'                </div>\n'
        f'                <span class="feed-arrow">→</span>\n'
        f'              </div>\n'
        f'            </a>'
    )
feed_items.append('          </div>')

feed_html = '\n'.join(feed_items)
blogs_html = re.sub(
    r'<!-- FEED_START -->.*?<!-- FEED_END -->',
    f'<!-- FEED_START -->\n{feed_html}\n          <!-- FEED_END -->',
    blogs_html, flags=re.DOTALL
)

# 更新文章数量（含现有的手写文章 + 新文章）
total = len(post_records)
blogs_html = re.sub(r'\d+ posts', f'{total} posts', blogs_html, count=1)

# 更新 featured post（最新一篇）
latest = post_records[0]
new_featured = (
    f'        <a id="featured-post" class="feed-featured"\n'
    f'           href="{latest["href"]}"\n'
    f'           data-search-title="{htmllib.escape(latest["title"])}"\n'
    f'           data-search-excerpt="{htmllib.escape(latest["excerpt"])}">\n'
    f'          <div class="feed-featured-header">\n'
    f'            <span class="feed-featured-tag">Latest</span>\n'
    f'            <span class="feed-featured-date">{fmt_long(latest["date"])}</span>\n'
    f'          </div>\n'
    f'          <span class="feed-featured-title">{htmllib.escape(latest["title"])}</span>\n'
    f'          <p class="feed-featured-excerpt">{htmllib.escape(latest["excerpt"])}</p>\n'
    f'          <div class="feed-featured-footer">\n'
    f'            <div class="feed-featured-meta"><span>{latest["category"]}</span></div>\n'
    f'            <span class="feed-featured-cta">Read post →</span>\n'
    f'          </div>\n'
    f'        </a>'
)
blogs_html = re.sub(
    r'<a id="featured-post".*?</a>',
    new_featured, blogs_html, flags=re.DOTALL
)

blogs_path.write_text(blogs_html, encoding='utf-8')
print(f'  blogs.html updated ({total} posts)')

# ── 更新 index.html ───────────────────────────────────────
index_path = PROJECT / 'index.html'
index_html = index_path.read_text(encoding='utf-8')

new_card = (
    f'        <!-- Latest blog — text card -->\n'
    f'        <a class="home-card home-card-sm" href="{latest["href"]}">\n'
    f'          <div>\n'
    f'            <div class="home-card-badge">Latest Blog</div>\n'
    f'            <h3 class="home-card-title">{htmllib.escape(latest["title"])}</h3>\n'
    f'            <p class="home-card-excerpt">{htmllib.escape(latest["excerpt"])}</p>\n'
    f'          </div>\n'
    f'          <div class="home-card-footer">\n'
    f'            <span class="home-card-date">{fmt_short(latest["date"])}</span>\n'
    f'            <span class="home-card-arrow">→</span>\n'
    f'          </div>\n'
    f'        </a>'
)
index_html = re.sub(
    r'<!-- LATEST_BLOG_START -->.*?<!-- LATEST_BLOG_END -->',
    f'<!-- LATEST_BLOG_START -->\n{new_card}\n        <!-- LATEST_BLOG_END -->',
    index_html, flags=re.DOTALL
)
index_path.write_text(index_html, encoding='utf-8')
print(f'  index.html updated → {latest["title"]}')

print('\n构建完成！')
