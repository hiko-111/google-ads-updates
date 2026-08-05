"""
fetch_updates.py
- 读取 archive/entries.json（用户手动上传的条目）
- 抓取官方 RSS 博客（自动补充背景内容）
- 合并排序后生成 index.html 和 updates.json
"""
import feedparser
import json
import datetime
import html
import re
import sys
from pathlib import Path

FEEDS = [
    {
        "name": "Google Ads Dev Blog",
        "url": "https://ads-developers.googleblog.com/feeds/posts/default",
        "color": "#4285F4",
        "label": "开发者",
        "source_type": "scrape",
    },
    {
        "name": "Google Ads & Commerce",
        "url": "https://blog.google/products/ads-commerce/rss/",
        "color": "#34A853",
        "label": "产品",
        "source_type": "scrape",
    },
]

CATEGORY_COLORS = {
    "产品功能":  "#34A853",
    "开发者API": "#4285F4",
    "政策变更":  "#EA4335",
    "出价策略":  "#FBBC05",
    "受众定向":  "#9C27B0",
    "其他":      "#757575",
}


def clean_html(text):
    text = re.sub(r'<[^>]+>', '', text or '')
    text = html.unescape(text)
    return ' '.join(text.split())


def parse_date(entry):
    for field in ('published_parsed', 'updated_parsed'):
        t = entry.get(field)
        if t:
            try:
                return datetime.datetime(*t[:6])
            except Exception:
                pass
    return datetime.datetime.min


def load_archive():
    path = Path(__file__).parent / "archive" / "entries.json"
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    result = []
    for e in raw:
        dt_str = e.get("date", "")
        try:
            dt = datetime.datetime.strptime(dt_str, "%Y-%m-%d")
        except Exception:
            dt = datetime.datetime.min
        cat = e.get("category", "其他")
        result.append({
            "title":        e.get("title", ""),
            "link":         e.get("link", ""),
            "summary":      e.get("summary", ""),
            "detail":       e.get("detail", ""),
            "published":    dt,
            "published_str": dt_str,
            "source":       e.get("source_label", "用户上传"),
            "source_type":  "upload",
            "color":        CATEGORY_COLORS.get(cat, "#757575"),
            "label":        cat,
            "tags":         e.get("tags", []),
        })
    return result


def fetch_rss():
    entries = []
    for cfg in FEEDS:
        try:
            feed = feedparser.parse(cfg["url"])
            for e in feed.entries[:20]:
                dt = parse_date(e)
                entries.append({
                    "title":        clean_html(e.get("title", "")),
                    "link":         e.get("link", ""),
                    "summary":      clean_html(e.get("summary", e.get("description", "")))[:400],
                    "detail":       "",
                    "published":    dt,
                    "published_str": dt.strftime("%Y-%m-%d") if dt != datetime.datetime.min else "",
                    "source":       cfg["name"],
                    "source_type":  "scrape",
                    "color":        cfg["color"],
                    "label":        cfg["label"],
                    "tags":         [],
                })
        except Exception as ex:
            print(f"[WARN] {cfg['name']}: {ex}", file=sys.stderr)
    return entries


def generate_html(entries, updated_at):
    cards = ""
    for e in entries:
        is_upload = e["source_type"] == "upload"
        upload_badge = '<span class="badge upload-badge">✎ 手动</span>' if is_upload else ''
        body_text = e["detail"] if e["detail"] else e["summary"]
        body_text = body_text[:280] + ("…" if len(body_text) > 280 else "")
        tags_html = "".join(
            f'<span class="tag">{t}</span>' for t in e.get("tags", [])
        )
        link_html = f'<a class="read-more" href="{e["link"]}" target="_blank" rel="noopener">原文 →</a>' if e["link"] else ""
        cards += f"""
    <article class="card{'  upload' if is_upload else ''}">
      <div class="card-meta">
        <span class="badge" style="background:{e['color']}">{e['label']}</span>
        {upload_badge}
        <span class="source">{e['source']}</span>
        <span class="date">{e['published_str']}</span>
      </div>
      <h2>{e['title']}</h2>
      <p>{body_text}</p>
      <div class="card-footer">
        <div class="tags">{tags_html}</div>
        {link_html}
      </div>
    </article>"""

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Google Ads 产品更新</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
           background: #f5f7fa; color: #1a1a2e; line-height: 1.6; }}
    header {{ background: #1a73e8; color: #fff; padding: 24px 32px;
              display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px; }}
    header h1 {{ font-size: 1.4rem; font-weight: 600; }}
    .updated {{ font-size: 0.8rem; opacity: 0.8; }}
    .container {{ max-width: 860px; margin: 32px auto; padding: 0 16px; }}
    .card {{ background: #fff; border-radius: 12px; padding: 20px 24px;
             margin-bottom: 16px; box-shadow: 0 1px 4px rgba(0,0,0,.08);
             transition: box-shadow .2s; border-left: 3px solid transparent; }}
    .card.upload {{ border-left-color: #1a73e8; }}
    .card:hover {{ box-shadow: 0 4px 16px rgba(0,0,0,.12); }}
    .card-meta {{ display: flex; align-items: center; gap: 8px; margin-bottom: 8px; flex-wrap: wrap; }}
    .badge {{ color: #fff; font-size: 0.7rem; font-weight: 700; padding: 2px 8px;
              border-radius: 12px; letter-spacing: .5px; }}
    .upload-badge {{ background: #1a73e8 !important; }}
    .source {{ font-size: 0.8rem; color: #666; }}
    .date {{ font-size: 0.8rem; color: #999; margin-left: auto; }}
    h2 {{ font-size: 1rem; font-weight: 600; margin-bottom: 6px; color: #1a1a2e; }}
    p {{ font-size: 0.875rem; color: #555; margin-bottom: 10px; }}
    .card-footer {{ display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px; }}
    .tags {{ display: flex; gap: 6px; flex-wrap: wrap; }}
    .tag {{ background: #f0f4ff; color: #1a73e8; font-size: 0.72rem; padding: 2px 8px;
             border-radius: 8px; }}
    .read-more {{ font-size: 0.8rem; color: #1a73e8; text-decoration: none; }}
    .read-more:hover {{ text-decoration: underline; }}
    footer {{ text-align: center; padding: 24px; font-size: 0.8rem; color: #999; }}
    @media (max-width: 600px) {{
      header {{ padding: 16px; }}
      .container {{ margin: 16px auto; }}
      .card {{ padding: 16px; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>&#128276; Google Ads 产品更新</h1>
    <span class="updated">更新于 {updated_at}</span>
  </header>
  <div class="container">
    {cards if cards else '<p style="text-align:center;padding:40px;color:#999">暂无数据</p>'}
  </div>
  <footer>手动整理 + Google 官方博客自动抓取 · ✎ 标记为手动录入</footer>
</body>
</html>"""


if __name__ == "__main__":
    print("Loading archive entries...")
    archive = load_archive()
    print(f"  Archive: {len(archive)} entries")

    print("Fetching RSS feeds...")
    scraped = fetch_rss()
    print(f"  Scraped: {len(scraped)} entries")

    # Merge: archive takes priority; deduplicate scraped by link
    archive_links = {e["link"] for e in archive if e["link"]}
    merged = archive + [e for e in scraped if e["link"] not in archive_links]
    merged.sort(key=lambda x: x["published"], reverse=True)
    merged = merged[:60]
    print(f"  Total after merge: {len(merged)}")

    updated_at = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(generate_html(merged, updated_at))
    print("index.html written")

    json_entries = [
        {k: v for k, v in e.items() if k != "published"}
        for e in merged
    ]
    with open("updates.json", "w", encoding="utf-8") as f:
        json.dump({"updated_at": updated_at, "entries": json_entries}, f, ensure_ascii=False, indent=2)
    print("updates.json written")
