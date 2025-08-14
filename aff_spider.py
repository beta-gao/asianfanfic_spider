#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random
import re
import time
from urllib.parse import urljoin

import pandas as pd
from bs4 import BeautifulSoup, Tag, NavigableString
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# -----------------------
# 工具函数：数字解析（支持 1,234 / 1.2k / 3.4M / 56）
# -----------------------
def _extract_num_compact(text):
    """把紧凑数字转成整数；返回 None 表示解析失败"""
    if text is None:
        return None
    t = str(text).strip().lower()
    m = re.search(r"(\d[\d,]*)(\.\d+)?\s*([km])?", t)
    if not m:
        return None
    whole = m.group(1).replace(",", "")
    frac = m.group(2) or ""
    unit = (m.group(3) or "").lower()
    try:
        num = float(whole + frac) if frac else float(whole)
    except Exception:
        return None
    if unit == "k":
        num *= 1000.0
    elif unit == "m":
        num *= 1000000.0
    try:
        return int(num)
    except Exception:
        return None


# -----------------------
# 解析逻辑（严格邻接 + 内置订阅比）
# -----------------------
def parse_story_info(section, base_url):
    """
    按 DOM “紧邻右侧”规则解析 chapters/subscribers/views，
    并在本函数内直接计算 subscriber/view 比值（避免除零）。
    """
    info = {
        "title": "",
        "url": "",
        "chapters": None,
        "subscribers": None,
        "views": None
    }

    # 标题与链接
    h1 = section.find("h1", class_="excerpt__title")
    if h1 is not None:
        a = h1.find("a")
        if a is not None:
            info["title"] = a.get_text(strip=True)
            href = a.get("href") or ""
            if href:
                info["url"] = urljoin(base_url, href)

    # 元信息容器
    meta = section.find("div", class_="excerpt__meta__views")
    if meta is None:
        for k in ("chapters", "subscribers", "views"):
            if info.get(k) is None:
                info[k] = 0
        # 方案A：安全除法计算订阅比
        def _safe_div(n, d):
            try:
                d = float(d)
                if d == 0.0:
                    return 0.0
                return float(n) / d
            except Exception:
                return 0.0
        info["sub_view_ratio"] = _safe_div(info["subscribers"], info["views"])
        info["sub_view_pct"] = "{:.2f}%".format(info["sub_view_ratio"] * 100.0)
        return info

    # 允许 </strong> 与关键词之间出现空白（你的页面为 "<strong>600</strong> views"）
    ALLOW_SPACE_AFTER_STRONG = True
    INLINE_TAGS = ("span", "small", "em", "i", "b")

    def _next_right_token_text(strong):
        """
        只看 <strong> 的紧邻右兄弟：
        - 文本节点：直接返回（不 strip，保留前导空白）
        - 内联标签：返回其 text（不 strip）
        - 其它：视为不紧邻
        """
        sib = strong.next_sibling
        if sib is None:
            return ""
        if isinstance(sib, NavigableString):
            return str(sib)
        if isinstance(sib, Tag) and sib.name in INLINE_TAGS:
            return sib.get_text("", strip=False)
        return ""

    def _label_from_right_text(raw, allow_space):
        """
        从紧邻右侧文本里抽取第一个“纯字母单词”作为标签。
        - allow_space=True：允许前导空白
        - allow_space=False：前导必须非空白
        """
        if raw is None:
            return None
        s = raw
        if allow_space:
            s = s.lstrip()
            if not s:
                return None
        else:
            if len(s) == 0 or s[0].isspace():
                return None
        m = re.match(r'^([A-Za-z]+)\b', s)
        return m.group(1).lower() if m else None

    def _extract_right_value(strong):
        return _extract_num_compact(strong.get_text("", strip=True))

    def bind_if_right_label(strong, key, keywords, info_dict):
        """
        仅当：<strong>数字</strong> 的紧邻右兄弟（文本或内联标签）起始就是目标关键词（可带前导空白）时，才绑定。
        """
        right_raw = _next_right_token_text(strong)
        if not right_raw:
            return False
        label = _label_from_right_text(right_raw, allow_space=ALLOW_SPACE_AFTER_STRONG)
        if label in keywords:
            val = _extract_right_value(strong)
            if val is not None and info_dict.get(key) is None:
                info_dict[key] = val
                return True
        return False

    # 严格邻接扫描所有 <strong>
    strongs = meta.find_all("strong")
    for s in strongs:
        if info["chapters"] is None and bind_if_right_label(s, "chapters", ("chapter", "chapters"), info):
            continue
        if info["subscribers"] is None and bind_if_right_label(s, "subscribers", ("subscriber", "subscribers"), info):
            continue
        if info["views"] is None and bind_if_right_label(s, "views", ("view", "views"), info):
            continue

    # 兜底：用原始 HTML 严格正则，顺序为 </strong> + 可空白 + 可选内联 + 关键词
    if info["chapters"] is None or info["subscribers"] is None or info["views"] is None:
        html_small = meta.decode_contents()

        def strict_pick(html_text, key, word):
            if info[key] is not None:
                return
            pattern = (
                r'(?is)'
                r'<strong[^>]*>\s*([0-9][0-9,\.]*\s*[km]?)\s*</strong>'
                r'\s*'                                      # 允许若干空白
                r'(?:<(?:span|small|em|i|b)[^>]*>\s*)?'     # 可选内联标签
                r'(' + word + r's?)\b'
            )
            m = re.search(pattern, html_text)
            if m:
                val = _extract_num_compact(m.group(1))
                if val is not None:
                    info[key] = val

        strict_pick(html_small, "chapters", "chapter")
        strict_pick(html_small, "subscribers", "subscriber")
        strict_pick(html_small, "views", "view")

    # 兜底填 0
    for k in ("chapters", "subscribers", "views"):
        if info[k] is None:
            info[k] = 0

    # 方案A：在本函数内直接计算订阅比（避免除零）
    def _safe_div(n, d):
        try:
            d = float(d)
            if d == 0.0:
                return 0.0
            return float(n) / d
        except Exception:
            return 0.0

    info["sub_view_ratio"] = _safe_div(info["subscribers"], info["views"])
    info["sub_view_pct"] = "{:.2f}%".format(info["sub_view_ratio"] * 100.0)

    return info


def parse_html(html, base_url):
    soup = BeautifulSoup(html, "html.parser")
    sections = soup.find_all("section", class_="excerpt")
    out = []
    for sec in sections:
        d = parse_story_info(sec, base_url)
        if d.get("title") and d.get("url"):
            out.append(d)
    return out


# -----------------------
# Playwright 抓取 + 翻页
# -----------------------
def run_with_playwright(turn_pages, start_url, pages, out_file, min_delay, max_delay, ua):
    base_url = "https://www.asianfanfics.com"
    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(user_agent=ua)
        page = context.new_page()

        def wait_human_if_challenge():
            try:
                page.wait_for_selector("text=Verify you are human", timeout=2000)
                print("检测到 Cloudflare 人机验证，请在浏览器里完成验证，然后回到终端按回车。")
                raw_input = input
                raw_input("完成后按回车继续...")
                return True
            except PlaywrightTimeoutError:
                return False

        for i in range(int(pages)):
            if i == 0:
                url = start_url
            else:
                # 根据站点翻页规则调整；此处示例为偏移 60 的分页
                url = "{}/{}".format(start_url.rstrip("/"), i * turn_pages)

            print("==== 抓取第 {} 页: {} ====".format(i + 1, url))
            page.goto(url, wait_until="domcontentloaded")

            just_challenged = wait_human_if_challenge()

            try:
                page.wait_for_selector("section.excerpt", timeout=10000)
            except PlaywrightTimeoutError:
                if just_challenged:
                    time.sleep(3.0)
                    try:
                        page.wait_for_selector("section.excerpt", timeout=7000)
                    except PlaywrightTimeoutError:
                        pass

            html = page.content()
            items = parse_html(html, base_url)
            print("本页提取 {} 条".format(len(items)))
            results.extend(items)

            if len(items) == 0:
                print("未提取到数据，提前结束翻页。")
                break

            if i < int(pages) - 1:
                delay = random.uniform(min_delay, max_delay)
                print("等待 {:.1f} 秒以避免频率过高...".format(delay))
                time.sleep(delay)

        browser.close()

    if results:
        df = pd.DataFrame(results)

        # 类型与列顺序统一，并把订阅比两列写入 Excel
        for c in ["chapters", "subscribers", "views"]:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(int)
        df["sub_view_ratio"] = pd.to_numeric(df.get("sub_view_ratio", 0.0), errors="coerce").fillna(0.0)
        if "sub_view_pct" not in df.columns:
            df["sub_view_pct"] = (df["sub_view_ratio"] * 100.0).round(2).astype(str) + "%"

        cols = ["title", "url", "chapters", "subscribers", "views", "sub_view_ratio", "sub_view_pct"]
        df = df.reindex(columns=[c for c in cols if c in df.columns])

        df.to_excel(out_file, index=False, engine="openpyxl")
        print("已保存 {} 条到 {}".format(len(df), out_file))

        print("\n示例：")
        for idx, row in enumerate(results[:5]):
            print("{}: {} / ch:{} sub:{} view:{} ratio:{:.4f} ({})".format(
                idx + 1,
                row.get("title", "")[:50],
                row.get("chapters", 0),
                row.get("subscribers", 0),
                row.get("views", 0),
                float(row.get("sub_view_ratio", 0.0)),
                row.get("sub_view_pct", "")
            ))
    else:
        print("没有提取到数据。")


# -----------------------
# 可修改的参数
# -----------------------
if __name__ == "__main__":

    turn_pages1 = 60
    tag="nomin"
    start_url1 = "https://www.asianfanfics.com/browse/tag/{}/L/".format(tag)    # 起始链接

    
    turn_pages2 = 20
    start_url2 = "https://www.asianfanfics.com/browse/search/eyJ0YWdzIjpbIm5vbWluIl0sImV4VGFncyI6WyJqYWVubyJdLCJyYXRpbmciOiJhbGxfcmF0aW5ncyIsImlzQ29tcGxldGUiOjAsImlzT25lU2hvdCI6MCwiaGFzQ292ZXIiOjAsImlzVW5kaXNjb3ZlcmVkIjowLCJtaW5DaGFwdGVycyI6IjAiLCJtYXhDaGFwdGVycyI6MCwibWluV29yZHMiOiIwIiwibWF4V29yZHMiOjAsIm1pbkNvbW1lbnRzIjoiMCIsIm1heENvbW1lbnRzIjowLCJudW1TdWJzY3JpYmVycyI6IjAiLCJudW1Wb3RlcyI6IjAiLCJudW1WaWV3cyI6IjAiLCJtaW5VcGRhdGVkTW9udGgiOm51bGwsIm1pblVwZGF0ZWRZZWFyIjpudWxsLCJtYXhVcGRhdGVkTW9udGgiOm51bGwsIm1heFVwZGF0ZWRZZWFyIjpudWxsfQ%3D%3D"


    pages = 400                                                         # 要翻的页数
    out_file = "test.xlsx"                                              # 输出 Excel 名
    min_delay = 1.0                                                     # 翻页最小等待秒数
    max_delay = 3.0                                                     # 翻页最大等待秒数
    ua = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
          "AppleWebKit/537.36 (KHTML, like Gecko) "
          "Chrome/119.0.0.0 Safari/537.36")                             # User-Agent

    run_with_playwright(turn_pages1,start_url1, pages, out_file, min_delay, max_delay, ua)
