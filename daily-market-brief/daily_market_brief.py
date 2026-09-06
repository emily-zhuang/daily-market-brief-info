from __future__ import annotations

import base64
import email.mime.multipart
import email.mime.text
import os
import re
import smtplib
from datetime import datetime, timedelta, timezone
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from zoneinfo import ZoneInfo

import feedparser
import requests
from docx import Document
from docx.shared import Inches, Pt
from docx.oxml.ns import qn
from bilingual import bilingual_block, translate_to_chinese
from cmc_market import extract_snapshot
from mail_config import smtp_config_from_env

BEIJING = ZoneInfo("Asia/Shanghai")
UTC = timezone.utc
ROOT = Path(__file__).resolve().parent
OUT = ROOT / "outputs"
OUT.mkdir(parents=True, exist_ok=True)

FEEDS = {
    "美国经济与股市": [
        ("Reuters Business", "https://feeds.reuters.com/reuters/businessNews"),
        ("CNBC Finance", "https://www.cnbc.com/id/100003114/device/rss/rss.html"),
        ("Yahoo Finance", "https://finance.yahoo.com/news/rssindex"),
    ],
    "中国经济与股市": [
        ("SCMP Business", "https://www.scmp.com/rss/91/feed"),
        ("China Daily Business", "https://www.chinadaily.com.cn/rss/business_rss.xml"),
        ("Google News China Finance", "https://news.google.com/rss/search?q=China+economy+stock+market&hl=en-US&gl=US&ceid=US:en"),
    ],
    "加密货币": [
        ("CoinDesk", "https://www.coindesk.com/arc/outboundfeeds/rss/"),
        ("Cointelegraph", "https://cointelegraph.com/rss"),
        ("Google News Crypto", "https://news.google.com/rss/search?q=cryptocurrency+bitcoin+ethereum+market&hl=en-US&gl=US&ceid=US:en"),
    ],
}


def clean(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", value or "")).strip()


def collect_news(since: datetime) -> dict[str, list[dict[str, str]]]:
    result: dict[str, list[dict[str, str]]] = {}
    for section, feeds in FEEDS.items():
        items: list[dict[str, str]] = []
        for source, url in feeds:
            try:
                parsed = feedparser.parse(url)
                for entry in parsed.entries[:20]:
                    published = entry.get("published_parsed") or entry.get("updated_parsed")
                    if published:
                        ts = datetime(*published[:6], tzinfo=UTC)
                        if ts < since:
                            continue
                    items.append({
                        "title": clean(entry.get("title", "")),
                        "summary": clean(entry.get("summary", ""))[:400],
                        "source": source,
                        "url": entry.get("link", ""),
                    })
            except Exception as exc:
                items.append({"title": f"采集失败：{source}", "summary": str(exc), "source": source, "url": url})
        result[section] = items[:10]
    return result


def market_data() -> dict[str, str]:
    key = os.getenv("COINMARKETCAP_API_KEY")
    if not key:
        return {"error": "未配置 COINMARKET_API_KEY / COINMARKETCAP_API_KEY；未填充 CoinMarketCap 行情数值。"}
    try:
        headers = {"X-CMC_PRO_API_KEY": key}
        listings = requests.get(
            "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest",
            params={"start": 1, "limit": 10, "convert": "USD"},
            headers=headers, timeout=20)
        listings.raise_for_status()
        global_metrics = requests.get(
            "https://pro-api.coinmarketcap.com/v1/global-metrics/quotes/latest",
            params={"convert": "USD"}, headers=headers, timeout=20)
        global_metrics.raise_for_status()
        return {"snapshot": extract_snapshot(listings.json(), global_metrics.json()),
                "captured_at": f"{datetime.now(UTC).astimezone(BEIJING):%Y-%m-%d %H:%M} 北京时间 / Beijing time"}
    except Exception as exc:
        return {"error": f"CoinMarketCap 读取失败 / CoinMarketCap request failed：{exc}"}


def add_link(paragraph, text: str, url: str) -> None:
    paragraph.add_run(f"{text}：{url}")


def build_doc(news: dict[str, list[dict[str, str]]], markets: dict[str, str], now: datetime) -> Path:
    doc = Document()
    section = doc.sections[0]
    section.top_margin = section.bottom_margin = section.left_margin = section.right_margin = Inches(0.7)
    for style_name in ("Normal", "Title", "Heading 1", "Heading 2"):
        style = doc.styles[style_name]
        style.font.name = "Noto Sans CJK SC"
        style.font.color.rgb = None
        style._element.get_or_add_rPr().rFonts.set(qn("w:ascii"), "Arial")
        style._element.get_or_add_rPr().rFonts.set(qn("w:hAnsi"), "Arial")
        style._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), "Noto Sans CJK SC")
    doc.styles["Normal"].font.name = "Noto Sans CJK SC"
    doc.styles["Normal"].font.size = Pt(10)
    doc.add_heading(f"美国、中国经济股市及加密货币每日汇总 | Daily US-China-Crypto Market Brief｜{now:%Y-%m-%d}", 0)
    doc.add_paragraph(f"报告时间 / Report time：北京时间 / Beijing time {now:%Y-%m-%d %H:%M}｜新闻窗口 / News window：前24小时 / Previous 24 hours｜来源 / Sources：主流媒体与公开市场数据 / Mainstream media and public market data。")
    doc.add_paragraph("说明 / Note：本文为新闻与数据摘要，不构成投资建议 / This is a news and data summary, not investment advice。主流媒体报道未逐条交叉验证 / Mainstream-media reports are not independently cross-checked。")

    doc.add_heading("一、加密货币市场数据 / Crypto Market Data", 1)
    snapshot = markets.get("snapshot")
    if snapshot:
        global_metrics = snapshot["global"]
        doc.add_paragraph("Global metrics / 全球市场指标", style="Heading 2")
        for label, value in (
            ("Total market cap / 全球总市值", global_metrics["total_market_cap"]),
            ("Volume 24h / 24小时成交量", global_metrics["total_volume_24h"]),
            ("BTC dominance / BTC 主导率", global_metrics["btc_dominance"]),
            ("ETH dominance / ETH 主导率", global_metrics["eth_dominance"]),
            ("Active cryptocurrencies / 活跃加密货币数量", global_metrics["active_cryptocurrencies"]),
        ):
            doc.add_paragraph(f"{label}：{value}", style="List Bullet")
        doc.add_paragraph("Top 10 cryptocurrencies / 市值前十加密货币", style="Heading 2")
        table = doc.add_table(rows=1, cols=10)
        table.style = "Table Grid"
        headers = ["Rank\n排名", "Asset\n币种", "Price\n价格", "1h", "24h", "7d", "Market cap\n市值", "Volume 24h\n24小时量", "Circulating supply\n流通供应", "Source\n来源"]
        for cell, value in zip(table.rows[0].cells, headers):
            cell.text = value
        for asset in snapshot["assets"]:
            cells = table.add_row().cells
            values = [asset["rank"], f"{asset['name']} ({asset['symbol']})", asset["price"], asset["change_1h"], asset["change_24h"], asset["change_7d"], asset["market_cap"], asset["volume_24h"], asset["supply"], "CoinMarketCap.com"]
            for cell, value in zip(cells, values):
                cell.text = str(value)
        doc.add_paragraph(f"数据抓取时间 / Captured：{markets['captured_at']}；报价货币 / Quote currency：USD。")
    else:
        doc.add_paragraph(markets.get("error", "CoinMarketCap 数据不可用 / Data unavailable"))
    doc.add_heading("二、新闻摘要 / News Summary", 1)
    for section_name, items in news.items():
        english_section = {
            "美国经济与股市": "US Economy and Equity Markets",
            "中国经济与股市": "China Economy and Equity Markets",
            "加密货币": "Cryptocurrency",
        }.get(section_name, section_name)
        doc.add_heading(f"{section_name} / {english_section}", 2)
        if not items:
            doc.add_paragraph("前24小时未取得可用条目 / No usable items were retrieved in the previous 24 hours.")
        for item in items:
            p = doc.add_paragraph(style="List Bullet")
            title_en = item["title"] or "Untitled"
            summary_en = item["summary"] or "No summary available."
            p.add_run(bilingual_block(
                translate_to_chinese(title_en), title_en,
                translate_to_chinese(summary_en), summary_en,
            )).bold = True
            p.add_run(f"\n来源 / Source：{item['source']}")
            add_link(p, "原文", item["url"])

    doc.add_heading("三、数据与运行记录 / Data and Run Log", 1)
    doc.add_paragraph(f"执行时间 / Execution time：{now:%Y-%m-%d %H:%M:%S} 北京时间 / Beijing time")
    doc.add_paragraph("采集方式 / Collection：RSS/公开网页摘要 / RSS and public web summaries；市场行情优先使用 CoinMarketCap API / CoinMarketCap API is preferred for market data。")
    for paragraph in doc.paragraphs:
        for run in paragraph.runs:
            run.font.name = "Noto Sans CJK SC"
            run._element.get_or_add_rPr().rFonts.set(qn("w:ascii"), "Arial")
            run._element.get_or_add_rPr().rFonts.set(qn("w:hAnsi"), "Arial")
            run._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), "Noto Sans CJK SC")
    path = OUT / f"美国与中国经济股市及加密货币每日新闻汇总_{now:%Y-%m-%d}.docx"
    doc.save(path)
    return path


def gmail_send(path: Path, now: datetime) -> None:
    sender, app_password = smtp_config_from_env()
    message = email.mime.multipart.MIMEMultipart()
    message["from"] = sender
    message["to"] = os.getenv("REPORT_RECIPIENT", "975471498@qq.com")
    message["subject"] = f"美国与中国经济股市及加密货币每日新闻汇总｜{now:%Y-%m-%d}"
    message.attach(email.mime.text.MIMEText(
        f"报告已生成，时间为北京时间 {now:%Y-%m-%d %H:%M}。附件：{path.name}\n\n本文不构成投资建议。", "plain", "utf-8"))
    with path.open("rb") as handle:
        part = MIMEBase("application", "vnd.openxmlformats-officedocument.wordprocessingml.document")
        part.set_payload(handle.read())
    encoders.encode_base64(part)
    part.add_header("Content-Disposition", "attachment", filename=path.name)
    message.attach(part)
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as smtp:
        smtp.login(sender, app_password)
        smtp.send_message(message)


def main() -> None:
    now = datetime.now(BEIJING)
    news = collect_news((now - timedelta(hours=24)).astimezone(UTC))
    path = build_doc(news, market_data(), now)
    gmail_send(path, now)
    print(f"sent: {path}")


if __name__ == "__main__":
    main()
