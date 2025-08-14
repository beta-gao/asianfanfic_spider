# Asianfanfics Tag/Search Scraper (Playwright + BeautifulSoup)

[中文readme](中文版)

Scrape **Asianfanfics** tag pages or search result pages in bulk and export to Excel.  
For each story the script extracts:

- `title`
- `url`
- `chapters`
- `subscribers`
- `views`
- `sub_view_ratio` (subscribers / views, e.g., `0.12`)
- `sub_view_pct` (percentage text, e.g., `12.00%`)

> Use responsibly. Check the website’s Terms of Service and robots rules. This tool is for learning/research, not high-frequency or large-scale scraping.

---

## Requirements

- Python 3.8+
- The packages listed in `requirements.txt`
- Playwright Chromium runtime (installed once via a command below)

---

## Quick Start

```bash
# 1) Enter your project folder
cd your-project-folder

# 2) (Optional) Create a virtual environment
python -m venv .venv           # Windows
# python3 -m venv .venv        # macOS / Linux
.venv\Scripts\activate         # Windows
# source .venv/bin/activate    # macOS / Linux

# 3) Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 4) Install Playwright browser runtime
python -m playwright install chromium

# 5) Run (replace the filename with your actual script file)
python aff_scraper.py          # Windows
# python3 aff_scraper.py       # macOS / Linux
If a Cloudflare challenge appears, complete it in the opened browser window. Return to the terminal and press Enter to resume.

Configuration
Edit the “Configurable Parameters” block at the bottom of the script and re-run:

python
Copy
Edit
# -----------------------
# Configurable Parameters
# -----------------------
if __name__ == "__main__":

    # Option A: Tag browsing (page offset step = 60)
    turn_pages1 = 60
    tag = "nomin"
    start_url1 = "https://www.asianfanfics.com/browse/tag/{}/L/".format(tag)

    # Option B: Search results (page offset step = 20)
    turn_pages2 = 20
    start_url2 = "https://www.asianfanfics.com/browse/search/..."  # full example provided in code

    pages = 400                 # how many pages to iterate (start small, e.g., 2–3)
    out_file = "test.xlsx"      # output Excel filename
    min_delay = 1.0             # min delay (seconds) between pages
    max_delay = 3.0             # max delay (seconds) between pages
    ua = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
          "AppleWebKit/537.36 (KHTML, like Gecko) "
          "Chrome/119.0.0.0 Safari/537.36")  # User-Agent

    # Choose ONE of the following calls:
    run_with_playwright(turn_pages1, start_url1, pages, out_file, min_delay, max_delay, ua)
    # run_with_playwright(turn_pages2, start_url2, pages, out_file, min_delay, max_delay, ua)
```
### Which one should I use?

Tag pages (start_url1): URLs like .../browse/tag/<tag>/L/ typically use an offset step of 60 per page.

Search results (start_url2): Encoded search URLs often use an offset step of 20.

If the site changes, the offset step might shift. Click “Next page” manually in your browser, observe how the URL changes, and update turn_pages accordingly.

##Output
An Excel file (default test.xlsx) with the columns:

title, url, chapters, subscribers, views, sub_view_ratio, sub_view_pct

Numbers like 1,234, 1.2k, 3.4M, and 56 are parsed correctly.

Safe division avoids errors when views are 0 (ratio becomes 0).

## How It Works (Parser Strategy)
Uses a strict adjacency rule: matches <strong>NUMBER</strong> whose immediate right sibling (text or inline tag) starts with the target keyword (chapter(s), subscriber(s), view(s)).

If adjacency fails, a tight HTML snippet regex fallback is applied.

Types are normalized and column order is fixed.

The subscribers/views ratio is computed inside the parser to avoid divide-by-zero issues later.

## Project Structure (example)
bash
Copy
Edit
.
├─ aff_scraper.py     # the script described in this README
├─ README.md          # main README (this file can be README_EN.md if you keep a Chinese README)
└─ test.xlsx          # generated output (example)
Legal & Compliance
Review and respect the target site’s ToS and robots rules.

Use for learning/research; avoid high-frequency or large-scale scraping.

Do not collect, publish, or share private or sensitive data.

Stop scraping if the site owner requests it.

## License
Recommended: MIT License. Add a LICENSE file with the standard MIT text.

# 中文版

用来批量抓取 Asianfanfics 某个标签或搜索结果列表中的作品信息，并导出为 Excel。脚本会解析每条作品的 标题、链接、章节数、订阅数、浏览数，并计算 订阅/浏览比。

# Asianfanfics 标签/搜索抓取器（Playwright + BeautifulSoup）

批量抓取 **Asianfanfics** 某个标签或搜索结果列表中的作品信息，并导出为 Excel。解析字段包括：
- `title`（标题）
- `url`（链接）
- `chapters`（章节数）
- `subscribers`（订阅数）
- `views`（浏览数）
- `sub_view_ratio`（订阅/浏览 比值，如 0.12）
- `sub_view_pct`（订阅/浏览 百分比，如 12.00%）

> ⚠️ 请遵守目标网站的使用条款，仅用于学习研究；避免高频与大规模抓取。

---

## 环境要求

- Python 3.8+
- 可访问公网下载依赖
- （首次运行）需要安装 Playwright 浏览器内核

---

## 快速开始

```bash
# 1) 克隆或下载仓库后，进入项目目录
cd your-project-folder

# 2) 安装依赖
pip install --upgrade pip
pip install -r requirements.txt

# 3) 安装 Chromium 内核（Playwright）
python -m playwright install chromium

# 4) 运行（把文件名替换成你的脚本名）
python aff_spider.py         # Windows
# python3 aff_spider.py      # macOS / Linux
```

如何配置抓取参数
在脚本底部的「可修改的参数」区域直接改即可（无需命令行参数）：
```bash
# -----------------------
# 可修改的参数
# -----------------------
if __name__ == "__main__":

    # 方案一：抓“标签浏览”页（每翻一页偏移 60）
    turn_pages1 = 60
    tag = "nomin"
    start_url1 = "https://www.asianfanfics.com/browse/tag/{}/L/".format(tag)

    # 方案二：抓“搜索结果”页（每翻一页偏移 20）
    turn_pages2 = 20
    start_url2 = "https://www.asianfanfics.com/browse/search/..."  # 已给出完整示例

    pages = 400                 # 要翻多少页（建议先用 2~3 测试）
    out_file = "test.xlsx"      # 输出 Excel 文件名
    min_delay = 1.0             # 每页抓取后的最小等待秒数
    max_delay = 3.0             # 每页抓取后的最大等待秒数
    ua = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
          "AppleWebKit/537.36 (KHTML, like Gecko) "
          "Chrome/119.0.0.0 Safari/537.36")  # User-Agent

    # 任选其一运行（取消注释你需要的那行）：
    run_with_playwright(turn_pages1, start_url1, pages, out_file, min_delay, max_delay, ua)
    # run_with_playwright(turn_pages2, start_url2, pages, out_file, min_delay, max_delay, ua)
```
### 何时用哪一个？

turn_pages1/start_url1用于标签浏览（start_url1）：形如 .../browse/tag/<tag>/L/，分页步长通常 60。

turn_pages2/start_url2用于advanced search搜索结果（start_url2）：复杂编码的搜索 URL，分页步长通常 20。需要手动点击next页面后得到，编辑进代码时请删掉结尾的“/20”。

若网站改版，分页步长可能变化。可手动点击“下一页”观察 URL 的偏移量，然后更新 turn_pages

## 输出文件
运行成功后生成一个 Excel（默认 test.xlsx），包含列：
title, url, chapters, subscribers, views, sub_view_ratio, sub_view_pct

数字解析支持 1,234 / 1.2k / 3.4M / 56 等格式。

已内置“安全除法”，当浏览数为 0 时比值记为 0。

## 法律与合规
抓取前请阅读目标网站 ToS / Robots；

仅用于学习研究，避免高频与大规模抓取；

不收集、传播任何隐私或敏感数据；

如网站方要求停止抓取，应立即停止。

## 许可证
MIT License
