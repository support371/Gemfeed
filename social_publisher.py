import re
import hashlib
import logging
import os
import requests
from urllib.parse import urlparse, urlencode, urlunparse, parse_qsl

BANNED_NEXTDOOR_TERMS = {
    "hodl", "bullish", "moon", "to the moon", "pump", "dump", "ape in", "lambo"
}

MAX_NEXTDOOR_CHARS = 900
MAX_HASHTAGS = 0

def add_utm(url: str, source: str, medium: str = "social", campaign: str = "gem_intel") -> str:
    if not url:
        return url
    parts = urlparse(url)
    q = dict(parse_qsl(parts.query))
    q.update({
        "utm_source": source,
        "utm_medium": medium,
        "utm_campaign": campaign,
    })
    new_query = urlencode(q)
    return urlunparse((parts.scheme, parts.netloc, parts.path, parts.params, new_query, parts.fragment))

def sanitize_nextdoor_text(text: str) -> str:
    if not text:
        return ""
    t = text.strip()
    t = re.sub(r"#\w+", "", t)
    t = re.sub(r"[!]{2,}", "!", t)
    t = re.sub(r"[\U0001F300-\U0001FAFF]+", "", t)
    t = re.sub(r"\s+", " ", t).strip()
    lowered = t.lower()
    for term in BANNED_NEXTDOOR_TERMS:
        if term in lowered:
            pattern = re.compile(re.escape(term), re.IGNORECASE)
            t = pattern.sub("", t)
            lowered = t.lower()
    if len(t) > MAX_NEXTDOOR_CHARS:
        t = t[:MAX_NEXTDOOR_CHARS].rsplit(" ", 1)[0].strip() + "…"
    return t

def render_x(article):
    """Version A: Short, punchy, market-focused"""
    url = add_utm(article['link'], source="twitter")
    text = f"🚨 {article['title']}\n\n{article['summary'][:150]}...\n\nRead: {url} #CyberSecurity #Tech"
    return text[:280]

def render_facebook(article):
    """Version B: Casual, shareable, family budgeting tone"""
    url = add_utm(article['link'], source="facebook")
    text = f"Stay safe online! 🛡️ {article['title']}\n\nA quick update on how to protect your digital life and save on unnecessary fees. Check it out: {url}"
    return text

def render_nextdoor(article):
    """Version C: Neighbor-friendly, local utility"""
    url = add_utm(article['link'], source="nextdoor")
    lines = [
        "Hello neighbors — quick security & savings tip:",
        f"{article['title']}".strip(),
        f"Thought this might be helpful for our community's digital safety.",
        f"Simple tip: {article['summary'][:100]}",
        f"More info: {url}"
    ]
    caption = "\n".join([ln for ln in lines if ln])
    return sanitize_nextdoor_text(caption)

def render_tiktok(article):
    """Version D: Short hook + 1 clear benefit + CTA"""
    text = f"🛡️ SECURITY TIP: {article['title']}\n\nProtect your family's budget from online threats! 💸\n\nFollow for daily security tips! #GEMSecurity #Safety"
    return text

def render_instagram(article):
    """Version D: Short hook + 1 clear benefit + CTA"""
    text = f"✨ {article['title']}\n\nStay one step ahead of scammers. One simple check could save your budget! 🛡️\n\nFollow @GEMSecurity for more. #CyberSafety #Secure"
    return text

def publish_to_ayrshare(post_text, platforms, media_urls=None, options=None):
    api_key = os.environ.get("AYRSHARE_API_KEY")
    if not api_key:
        logging.error("AYRSHARE_API_KEY not set")
        return {"success": False, "message": "API Key missing"}

    url = "https://app.ayrshare.com/api/post"
    payload = {
        "post": post_text,
        "platforms": platforms
    }
    if media_urls:
        payload["mediaUrls"] = media_urls
    
    # Platform-specific defaults
    if "facebook" in platforms:
        payload["faceBookOptions"] = {"isReel": True}
    if "nextdoor" in platforms:
        payload["nextdoorOptions"] = {"scope": "public"}
        
    if options:
        payload.update(options)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        return response.json()
    except Exception as e:
        logging.error(f"Ayrshare publish error: {e}")
        return {"success": False, "message": str(e)}

def stable_post_key(platform: str, article_id: str, url: str) -> str:
    base = f"{platform}:{article_id or url}"
    return hashlib.sha256(base.encode("utf-8")).hexdigest()
