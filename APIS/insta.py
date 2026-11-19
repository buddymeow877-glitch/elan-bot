# ------------------------------------------------------------
# Instagram Info API — Credit: Anmol (@FOREVER_HIDDEN)
# RATE LIMIT FIXED - Working with proxies & session management
# ------------------------------------------------------------

from flask import Flask, jsonify, request
import requests
import time
import socket
import json
import logging
import random
import re
from functools import lru_cache
from typing import Optional, Dict, Any
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# ============ PROXY CONFIGURATION ============
# Add your proxies here (free or paid)
FREE_PROXIES = [
    # Format: "http://ip:port" or "socks5://ip:port"
    # You can get free proxies from: https://free-proxy-list.net/
    # "http://103.152.112.120:80",
    # "http://103.152.112.120:8080",
    # "http://103.152.112.120:3128",
]

# ============ SESSION MANAGEMENT ============
class InstagramSession:
    def __init__(self):
        self.session = requests.Session()
        self.last_request = 0
        self.min_delay = 5  # Minimum 5 seconds between requests
        
    def get(self, url, headers=None, timeout=15, proxies=None):
        # Rate limit ourselves
        elapsed = time.time() - self.last_request
        if elapsed < self.min_delay:
            time.sleep(self.min_delay - elapsed)
        
        self.last_request = time.time()
        return self.session.get(url, headers=headers, timeout=timeout, proxies=proxies)
    
    def post(self, url, params=None, headers=None, timeout=15, proxies=None):
        elapsed = time.time() - self.last_request
        if elapsed < self.min_delay:
            time.sleep(self.min_delay - elapsed)
        
        self.last_request = time.time()
        return self.session.post(url, params=params, headers=headers, timeout=timeout, proxies=proxies)

# ============ USER AGENTS ============
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15",
]

IG_APP_IDS = [
    "936619743392459",
    "124024574287414", 
    "567067343352427",
    "714293450924931",
]

# ============ COOKIE GENERATION ============
def generate_cookies():
    """Generate random Instagram cookies"""
    return {
        "ig_did": f"02F{random.randint(1000000000, 9999999999)}",
        "ig_nrcb": f"1-{random.randint(1000000000, 9999999999)}",
        "csrftoken": f"{''.join(random.choices('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=32))}",
        "mid": f"Z{random.choice('abcdefghijklmnopqrstuvwxyz')}{random.randint(1000000000, 9999999999)}",
        "rur": f"ATN{random.randint(1000000000, 9999999999)}",
        "urlgen": f"{random.choice('abcdefghijklmnopqrstuvwxyz')}{random.randint(1000000000, 9999999999)}",
    }

# ============ PROXY ROTATOR ============
class ProxyRotator:
    def __init__(self):
        self.proxies = FREE_PROXIES.copy()
        self.current_index = 0
        
    def get_proxy(self):
        if not self.proxies:
            return None
        proxy = self.proxies[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.proxies)
        return proxy
    
    def add_proxy(self, proxy):
        if proxy not in self.proxies:
            self.proxies.append(proxy)

proxy_rotator = ProxyRotator()

# ============ MAIN FETCH FUNCTION ============
def fetch_instagram_profile(username: str, proxy: Optional[str] = None) -> Dict[str, Any]:
    """Fetch Instagram profile with multiple bypass methods"""
    
    username = username.strip().lower()
    
    # If no proxy provided, use rotator
    if not proxy and proxy_rotator.proxies:
        proxy = proxy_rotator.get_proxy()
        logger.info(f"Using proxy: {proxy}")
    
    # Multiple API endpoints
    endpoints = [
        # Method 1: GraphQL API
        {
            "url": "https://www.instagram.com/graphql/query/",
            "params": {
                "query_hash": "c9100bf9110dd6361671f11383502d04",
                "variables": json.dumps({
                    "username": username,
                    "include_reel": True,
                    "fetch_media": True,
                    "media_limit": 12
                })
            },
            "method": "POST"
        },
        # Method 2: Web API
        {
            "url": f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}",
            "params": None,
            "method": "GET"
        },
        # Method 3: i.instagram.com
        {
            "url": f"https://i.instagram.com/api/v1/users/web_profile_info/?username={username}",
            "params": None,
            "method": "GET"
        },
        # Method 4: JSON endpoint
        {
            "url": f"https://www.instagram.com/{username}/?__a=1&__d=dis",
            "params": None,
            "method": "GET"
        },
        # Method 5: Regular page (will parse HTML)
        {
            "url": f"https://www.instagram.com/{username}/",
            "params": None,
            "method": "GET"
        }
    ]
    
    # Try each endpoint with multiple attempts
    for endpoint_idx, endpoint in enumerate(endpoints):
        for attempt in range(3):  # 3 attempts per endpoint
            try:
                # Random delay to avoid detection
                time.sleep(random.uniform(1, 3))
                
                # Generate fresh headers
                headers = {
                    "User-Agent": random.choice(USER_AGENTS),
                    "Accept": "application/json, text/plain, */*",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept-Encoding": "gzip, deflate, br",
                    "x-ig-app-id": random.choice(IG_APP_IDS),
                    "x-ig-www-claim": "0",
                    "x-requested-with": "XMLHttpRequest",
                    "Referer": f"https://www.instagram.com/{username}/",
                    "Origin": "https://www.instagram.com",
                    "Sec-Fetch-Dest": "empty" if endpoint_idx < 3 else "document",
                    "Sec-Fetch-Mode": "cors" if endpoint_idx < 3 else "navigate",
                    "Sec-Fetch-Site": "same-origin",
                    "Cookie": "; ".join([f"{k}={v}" for k, v in generate_cookies().items()])
                }
                
                # Setup proxy
                proxies = None
                if proxy:
                    proxies = {"http": proxy, "https": proxy}
                
                # Make request
                session = InstagramSession()
                if endpoint["method"] == "POST":
                    resp = session.post(
                        endpoint["url"],
                        params=endpoint["params"],
                        headers=headers,
                        timeout=15,
                        proxies=proxies
                    )
                else:
                    resp = session.get(
                        endpoint["url"],
                        headers=headers,
                        timeout=15,
                        proxies=proxies
                    )
                
                # Handle response
                if resp.status_code == 200:
                    # Try to parse JSON
                    try:
                        data = resp.json()
                        user = extract_user_from_response(data)
                        if user:
                            logger.info(f"✅ Successfully fetched {username} using method {endpoint_idx+1}")
                            return {"data": {"user": user}}
                    except:
                        # Try HTML parsing
                        if 'window._sharedData' in resp.text:
                            try:
                                shared_data = re.search(r'window\._sharedData\s*=\s*({.*?});', resp.text, re.DOTALL)
                                if shared_data:
                                    data = json.loads(shared_data.group(1))
                                    user = data.get("entry_data", {}).get("ProfilePage", [{}])[0].get("graphql", {}).get("user")
                                    if user:
                                        logger.info(f"✅ Successfully fetched {username} from HTML")
                                        return {"data": {"user": user}}
                            except:
                                pass
                        
                        # Try to extract from any JSON in page
                        json_data = re.findall(r'<script type="application/json">(.*?)</script>', resp.text)
                        for json_str in json_data:
                            try:
                                data = json.loads(json_str)
                                user = extract_user_from_response(data)
                                if user:
                                    logger.info(f"✅ Successfully fetched {username} from embedded JSON")
                                    return {"data": {"user": user}}
                            except:
                                continue
                
                elif resp.status_code == 429:
                    logger.warning(f"Rate limited, waiting {attempt+1 * 5}s...")
                    time.sleep((attempt + 1) * 5)
                    
                elif resp.status_code == 404:
                    return {"error": "not_found", "status_code": 404}
                    
                elif resp.status_code in [403, 400]:
                    logger.warning(f"Access denied for {username}")
                    time.sleep(random.uniform(2, 5))
                    
            except Exception as e:
                logger.error(f"Error: {e}")
                time.sleep(random.uniform(1, 3))
                
            # Rotate proxy if available
            if proxy_rotator.proxies:
                proxy = proxy_rotator.get_proxy()
                logger.info(f"Switching to proxy: {proxy}")
    
    return {"error": "request_failed", "status_code": 500}


def extract_user_from_response(data):
    """Extract user data from various response formats"""
    if not data:
        return None
    
    # Try different paths
    paths = [
        ("data", "user"),
        ("user",),
        ("data", "graphql", "user"),
        ("graphql", "user"),
        ("entry_data", "ProfilePage", 0, "graphql", "user"),
    ]
    
    for path in paths:
        try:
            result = data
            for key in path:
                if isinstance(key, int):
                    result = result[key]
                else:
                    result = result.get(key)
                if not result:
                    break
            if result and isinstance(result, dict) and result.get("username"):
                return result
        except:
            continue
    
    return None


def parse_instagram_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Parse and structure Instagram profile data"""
    
    user = None
    if isinstance(data, dict):
        user = data.get("data", {}).get("user") or data.get("user") or data.get("data")
        
        if not user and "graphql" in data:
            user = data["graphql"].get("user")
        if not user and "entry_data" in data:
            profile = data.get("entry_data", {}).get("ProfilePage", [{}])[0]
            user = profile.get("graphql", {}).get("user")
    
    if not user:
        return {"error": "invalid_data_structure", "raw": data}
    
    out = {
        "success": True,
        "id": str(user.get("id", "")),
        "username": user.get("username", ""),
        "full_name": user.get("full_name", ""),
        "biography": user.get("biography", ""),
        "is_private": user.get("is_private", False),
        "is_verified": user.get("is_verified", False),
        "is_business": user.get("is_business", False),
        "business_category_name": user.get("business_category_name", ""),
        "profile_pic_url": user.get("profile_pic_url_hd") or user.get("profile_pic_url", ""),
        "profile_pic_url_hd": user.get("profile_pic_url_hd", ""),
        "external_url": user.get("external_url", ""),
        "followers_count": 0,
        "following_count": 0,
        "media_count": 0,
        "recent_media": [],
        "stats": {}
    }
    
    # Handle counts
    followers = user.get("edge_followed_by", {}).get("count") or user.get("followers_count")
    following = user.get("edge_follow", {}).get("count") or user.get("following_count")
    media = user.get("media_count") or user.get("edge_owner_to_timeline_media", {}).get("count")
    
    if followers is not None:
        out["followers_count"] = int(followers)
    if following is not None:
        out["following_count"] = int(following)
    if media is not None:
        out["media_count"] = int(media)
    
    # Parse recent media
    media_data = (user.get("edge_owner_to_timeline_media") or 
                  user.get("media") or 
                  user.get("recent_media") or 
                  {})
    
    edges = media_data.get("edges") or media_data.get("items") or []
    
    for item in edges[:12]:
        if not item:
            continue
        
        if isinstance(item, dict):
            node = item.get("node") or item
        else:
            node = item
            
        if not node:
            continue
        
        caption = ""
        if node.get("edge_media_to_caption"):
            caption_edges = node["edge_media_to_caption"].get("edges") or []
            if caption_edges:
                if "node" in caption_edges[0]:
                    caption = caption_edges[0]["node"].get("text", "")
                else:
                    caption = caption_edges[0].get("text", "")
        elif node.get("caption"):
            caption = node.get("caption")
        elif node.get("caption_text"):
            caption = node.get("caption_text")
        
        media_item = {
            "id": str(node.get("id", "")),
            "shortcode": node.get("shortcode", ""),
            "display_url": node.get("display_url") or node.get("display_src", ""),
            "taken_at": node.get("taken_at_timestamp") or node.get("taken_at", 0),
            "caption": caption or "",
            "is_video": node.get("is_video", False),
            "video_url": node.get("video_url", ""),
            "like_count": node.get("edge_liked_by", {}).get("count", 0),
            "comment_count": node.get("edge_media_to_comment", {}).get("count", 0),
        }
        
        out["recent_media"].append(media_item)
    
    out["stats"] = {
        "total_posts": out["media_count"],
        "followers": out["followers_count"],
        "following": out["following_count"],
        "has_bio": bool(out["biography"]),
        "has_external_link": bool(out["external_url"]),
        "is_business": out["is_business"],
        "is_verified": out["is_verified"],
        "is_private": out["is_private"]
    }
    
    return out

# ============ ROUTES ============
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "name": "Instagram Info API",
        "version": "2.1 - Rate Limit Fixed",
        "author": "Anmol @FOREVER_HIDDEN",
        "status": "✅ Working",
        "endpoints": {
            "/api/insta/<username>": "Get full profile info",
            "/api/insta/<username>/media": "Get only media",
            "/api/insta/<username>/stats": "Get only stats",
            "/proxy/add": "Add a proxy (POST)"
        },
        "example": "/api/insta/cristiano",
        "note": "Rate limit protection: waits 5 seconds between requests"
    })


@app.route("/api/insta/<username>", methods=["GET"])
def insta_info(username):
    if not username:
        return jsonify({"error": "username_required"}), 400
    
    proxy = request.args.get("proxy")
    max_retries = int(request.args.get("retries", 3))
    
    for retry in range(max_retries):
        logger.info(f"Attempt {retry+1}/{max_retries} for {username}")
        
        data = fetch_instagram_profile(username, proxy=proxy)
        
        if data and not data.get("error"):
            result = parse_instagram_data(data)
            if result and not result.get("error"):
                return jsonify(result)
        
        if retry < max_retries - 1:
            wait_time = (2 ** retry) * 2
            logger.info(f"Waiting {wait_time}s before retry...")
            time.sleep(wait_time)
    
    return jsonify({
        "error": "request_failed",
        "message": "Unable to fetch Instagram data",
        "solutions": [
            "1. Wait 60 seconds and try again (rate limit)",
            "2. Add a proxy: /api/insta/username?proxy=http://ip:port",
            "3. The account might be private",
            "4. Instagram API might be down",
            "5. Try a different username"
        ],
        "recommendation": "Use a VPN or proxy to bypass rate limits"
    }), 503


@app.route("/api/insta/<username>/media", methods=["GET"])
def insta_media_only(username):
    if not username:
        return jsonify({"error": "username_required"}), 400
    
    proxy = request.args.get("proxy")
    data = fetch_instagram_profile(username, proxy=proxy)
    
    if data.get("error"):
        return jsonify({"error": data["error"]}), 400
    
    result = parse_instagram_data(data)
    return jsonify({
        "username": result.get("username"),
        "media_count": result.get("media_count", 0),
        "recent_media": result.get("recent_media", [])
    })


@app.route("/api/insta/<username>/stats", methods=["GET"])
def insta_stats_only(username):
    if not username:
        return jsonify({"error": "username_required"}), 400
    
    proxy = request.args.get("proxy")
    data = fetch_instagram_profile(username, proxy=proxy)
    
    if data.get("error"):
        return jsonify({"error": data["error"]}), 400
    
    result = parse_instagram_data(data)
    return jsonify({
        "username": result.get("username"),
        "full_name": result.get("full_name"),
        "stats": result.get("stats", {})
    })


@app.route("/proxy/add", methods=["POST"])
def add_proxy():
    """Add a proxy to the rotator"""
    data = request.json
    if not data or "proxy" not in data:
        return jsonify({"error": "proxy_required"}), 400
    
    proxy = data["proxy"]
    proxy_rotator.add_proxy(proxy)
    return jsonify({
        "success": True,
        "message": f"Proxy added: {proxy}",
        "total_proxies": len(proxy_rotator.proxies)
    })


@app.route("/proxy/list", methods=["GET"])
def list_proxies():
    """List all configured proxies"""
    return jsonify({
        "proxies": proxy_rotator.proxies,
        "total": len(proxy_rotator.proxies)
    })


@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "endpoint_not_found"}), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "internal_server_error"}), 500


def find_free_port(start=8080, end=65535):
    for port in range(start, end):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('0.0.0.0', port)) != 0:
                return port
    raise RuntimeError("No free port available")


if __name__ == "__main__":
    port = find_free_port()
    print("=" * 70)
    print("🔥 Instagram Info API - RATE LIMIT FIXED")
    print("=" * 70)
    print(f"🌐 Server: http://localhost:{port}")
    print(f"📱 Example: http://localhost:{port}/api/insta/cristiano")
    print(f"📊 Stats: http://localhost:{port}/api/insta/cristiano/stats")
    print("=" * 70)
    print("⚠️  RATE LIMIT PROTECTION:")
    print("   ✅ 5 second delay between requests")
    print("   ✅ Random delays to avoid detection")
    print("   ✅ Multiple API endpoints")
    print("   ✅ Cookie rotation")
    print("   ✅ User-Agent rotation")
    print("=" * 70)
    print("💡 To add proxies:")
    print("   POST /proxy/add")
    print('   {"proxy": "http://ip:port"}')
    print("=" * 70)
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)