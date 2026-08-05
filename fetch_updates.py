"""
fetch_updates.py
- 读取 archive/entries.json（手动录入的条目）
- 生成 index.html 和 updates.json
"""
import json
import datetime
from pathlib import Path

CATEGORY_COLORS = {
    "产品功能":  "#34A853",
    "开发者API": "#4285F4",
    "政策变更":  "#EA4335",
    "出价策略":  "#FBBC05",
    "受众定向":  "#9C27B0",
    "其他":      "#757575",
}


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
            "source":       e.get("source_label", "手动录入"),
            "color":        CATEGORY_COLORS.get(cat, "#757575"),
            "label":        cat,
            "tags":         e.get("tags", []),
            "images":       e.get("images", []),
        })
    result.sort(key=lambda x: x["published"], reverse=True)
    return result


def generate_html(entries, updated_at):
    cards = ""
    for e in entries:
        body_text = e["detail"] if e["detail"] else e["summary"]
        tags_html = "".join(
            f'<span class="tag">{t}</span>' for t in e.get("tags", [])
        )
        link_html = (
            f'<a class="read-more" href="{e["link"]}" target="_blank" rel="noopener">原文 →</a>'
            if e["link"] else ""
        )
        images_html = ""
        if e.get("images"):
            imgs = "".join(
                f'<a href="{img}" target="_blank" rel="noopener"><img src="{img}" alt="" loading="lazy"></a>'
                for img in e["images"]
            )
            images_html = f'<div class="img-gallery">{imgs}</div>'
        cards += f"""
    <article class="card">
      <div class="card-meta">
        <span class="badge" style="background:{e['color']}">{e['label']}</span>
        <span class="source">{e['source']}</span>
        <span class="date">{e['published_str']}</span>
      </div>
      <h2>{e['title']}</h2>
      <p>{body_text}</p>
      {images_html}
      <div class="card-footer">
        <div class="tags">{tags_html}</div>
        {link_html}
      </div>
    </article>"""

    empty = '<p style="text-align:center;padding:60px;color:#999">暂无内容，等待录入</p>'

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
             transition: box-shadow .2s; border-left: 3px solid #1a73e8; }}
    .card:hover {{ box-shadow: 0 4px 16px rgba(0,0,0,.12); }}
    .card-meta {{ display: flex; align-items: center; gap: 8px; margin-bottom: 8px; flex-wrap: wrap; }}
    .badge {{ color: #fff; font-size: 0.7rem; font-weight: 700; padding: 2px 8px;
              border-radius: 12px; letter-spacing: .5px; }}
    .source {{ font-size: 0.8rem; color: #666; }}
    .date {{ font-size: 0.8rem; color: #999; margin-left: auto; }}
    h2 {{ font-size: 1rem; font-weight: 600; margin-bottom: 6px; color: #1a1a2e; }}
    p {{ font-size: 0.875rem; color: #555; margin-bottom: 10px; }}
    .card-footer {{ display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px; }}
    .tags {{ display: flex; gap: 6px; flex-wrap: wrap; }}
    .tag {{ background: #f0f4ff; color: #1a73e8; font-size: 0.72rem; padding: 2px 8px; border-radius: 8px; }}
    .read-more {{ font-size: 0.8rem; color: #1a73e8; text-decoration: none; }}
    .read-more:hover {{ text-decoration: underline; }}
    .img-gallery {{ display: flex; gap: 10px; overflow-x: auto; padding: 8px 0 12px;
                    scrollbar-width: thin; }}
    .img-gallery a {{ flex: 0 0 auto; }}
    .img-gallery img {{ height: 180px; width: auto; border-radius: 6px;
                        border: 1px solid #e0e0e0; cursor: zoom-in;
                        transition: opacity .2s; }}
    .img-gallery img:hover {{ opacity: 0.85; }}
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
    {cards if cards else empty}
  </div>
  <footer>内容由 UA 团队整理录入</footer>
</body>
</html>"""


if __name__ == "__main__":
    entries = load_archive()
    print(f"Loaded {len(entries)} entries from archive")

    updated_at = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(generate_html(entries, updated_at))
    print("index.html written")

    json_out = [
        {k: v for k, v in e.items() if k != "published"}
        for e in entries
    ]
    with open("updates.json", "w", encoding="utf-8") as f:
        json.dump({"updated_at": updated_at, "entries": json_out}, f, ensure_ascii=False, indent=2)
    print("updates.json written")
