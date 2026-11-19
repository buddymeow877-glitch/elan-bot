

import sys
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

import asyncio, random, json, os, time, re, traceback, pickle, unicodedata
from datetime import datetime
import aiohttp
import requests
from concurrent.futures import ThreadPoolExecutor
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

from xC4 import *
from xP import JoinSq, OpenCh, MsqSq, ExitSq
from byte import Encrypt_ID, encrypt_api
from Pb2 import DEcwHisPErMsG_pb2, sQ_pb2

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ═══════════════════════════════════════════════════════════════
# PATHS
# ═══════════════════════════════════════════════════════════════
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EMOTES_PATH       = os.path.join(BASE_DIR, "emotes.json")
SPAM_TARGETS_FILE = os.path.join(BASE_DIR, "spam_targets.json")
ADMINS_FILE = os.path.join(BASE_DIR, "admins.json")
AUTO_REPLIES_FILE = os.path.join(BASE_DIR, "auto_replies.json")
BANS_FILE = os.path.join(BASE_DIR, "bans.json")
EXPIRE_FILE = os.path.join(BASE_DIR, "expire.json")

# ═══════════════════════════════════════════════════════════════
# GLOBALS
# ═══════════════════════════════════════════════════════════════
online_writer = None
whisper_writer = None
spam_running = False
bot_uid = None
ToKen = None
region = None
BOT_OWNER_UID = "490381600"
clan_id = 0
clan_data = ""
login_data = None

pending_ghost_future = None
ghost_team_id = None
ghost_squad_code = None

spm_tasks = {}
ban_task = None
ban_running = False
ban_targets = set()
evo_cycle_running = False
evo_cycle_task = None
freeze_running = False
freeze_task = None
fast_spam_running = False
fast_spam_task = None
custom_spam_running = False
custom_spam_task = None
msg_spam_running = False
msg_spam_task = None
mg_spam_task = None
reject_spam_running = False
reject_spam_task = None
emote_hijack = False
bot_enabled = True
last_chat_seen = {}
admin_mode = False
auto_accept_enabled = True

expire_timestamp = 0
spam_request_running = False
spam_request_task = None
evo_fast_spam_running = False
evo_fast_spam_task = None
evo_custom_spam_running = False
evo_custom_spam_task = None

EVO_IDS = [
    909000063, 909000075, 909040010, 909000081, 909039011,
    909045001, 909038012, 909042008, 909051003, 909035012,
    909000098, 909033002, 909037011, 909049010, 909041005,
    909038010, 909033001, 909035007, 909000090, 909000085,
    909000068, 909054004, 909055007
]

# ═══════════════════════════════════════════════════════════════
# LOAD JSON FILES
# ════════════════════════════════════
GENERAL_EMOTES_MAP = {}
EMOTE_MAP = {}
NAME_EMOTES = {}

try:
    with open(EMOTES_PATH, "r", encoding="utf-8") as _f:
        _emote_data = json.load(_f)["EMOTES"]
    GENERAL_EMOTES_MAP = {
        str(number).lower(): int(emote_id)
        for number, emote_id in _emote_data["numbers"].items()
    }
    NAME_EMOTES = {
        str(name).lower(): int(emote_id)
        for name, emote_id in _emote_data["names"].items()
    }
    EMOTE_MAP = {
        int(number): emote_id
        for number, emote_id in GENERAL_EMOTES_MAP.items()
        if number.isdigit()
    }
    print(
        f"✅ Loaded {len(GENERAL_EMOTES_MAP)} numbered and "
        f"{len(NAME_EMOTES)} named emotes from emotes.json"
    )
except Exception as _e:
    print(f"❌ emotes.json load error: {_e}")

NUMBER_EMOTES = GENERAL_EMOTES_MAP

# Badge values for s1 to s8 commands
BADGE_VALUES = {
    "s1": 1048576,
    "s2": 32768,
    "s3": 2048,
    "s4": 64,
    "s5": 262144,
    "s6": 131072,
    "s7": 524288,
    "s8": 16384,
}

# ═══════════════════════════════════════════════════════════════
# EVO EMOTE ID MAP (1-21)
# ═══════════════════════════════════════════════════════════════
evo_emotes = {
    1:  909000063,   # AK47
    2:  909000068,   # SCAR
    3:  909000075,   # MP40
    4:  909000085,   # XM8
    5:  909000098,   # UMP
    6:  909000081,   # M1014
    7:  909033001,   # M4A1
    8:  909033002,   # MP5
    9:  909035007,   # M1887
    10: 909035012,   # AN94
    11: 909000090,   # FAMAS
    12: 909037011,   # EVO FIST
    13: 909038010,   # THOMPSON
    14: 909038012,   # G18
    15: 909039011,   # M1014 2.0
    16: 909040010,   # MP40 2.0
    17: 909041005,   # GROZA
    18: 909042008,   # WOODPECKER
    19: 909045001,   # PARAFAL
    20: 909049010,   # P90
    21: 909051003,   # M60
    22: 909054004,    # AUG
    23: 909055007    # AWM
}

evo_names = {
    1: "AK47",  2: "SCAR",  3: "MP40",  4: "XM8",  5: "UMP",
    6: "M1014", 7: "M4A1",  8: "MP5",   9: "M1887", 10: "AN94",
    11: "FAMAS", 12: "EVO FIST", 13: "THOMPSON", 14: "G18",
    15: "M1014 2.0", 16: "MP40 2.0", 17: "GROZA",
    18: "WOODPECKER", 19: "PARAFAL", 20: "P90", 21: "M60", 22: "AUG", 23: "AWM"
}

EVO_EMOTE_MAP = evo_emotes
for _k, _v in evo_emotes.items():
    EMOTE_MAP[_k] = _v

BLOCKED_NAMES = ["buddy", "meow", "buddymeow", "monir", "mh", "rizz", "riz", "rizzfez", "rizzdez zitu", "boss", "admin"]

GUILD_RULES_MSG = """[FFD700][b][c]╔═『 ☘︎ GUILD RULES ☘︎ 』═╗
[00FFFF]
1. Respect everyone
2. Messenger GC te join thako
3. Invite ignore koro na
4. Admin der respect koro
5. Guild Event e join koro
6. Gala Gali kora jabena
7. Spam not allowed
8. Problem hole admin ke bolo

[FF69B4]Let’s keep the guild happy & friendly

[FFD700]⊱.˚── ⋅ .✧˚❀˚✧. ⋅ ──˚.⊰
"""

# Cloudflare AI API
API_BASE_URL = "https://api.cloudflare.com/client/v4/accounts/dbc8362beb0b17323c1b92dfda03d9be/ai/run/"
API_HEADERS = {
    "Authorization": "Bearer cfut_SdWUdtosCqaPoRqodGBtRJwnxFtS328VzpJlzGs7c5b15f8e",
    "Content-Type": "application/json"
}
AI_MODEL = "@cf/moonshotai/kimi-k2.7-code"

# ═══════════════════════════════════════════════════════════════
# HELPERS

# NEW GLOBALS (auto‑accept state)
insquad = None  # True when currently in a squad
joining_team = False  # True while join sequence is in progress
TEAM_WELCOME_SENT = set()  # Tracks chat_codes that already received a welcome
last_status_packet = None
status_response_cache = {}
senthi = False

# ═══════════════════════════════════════════════════════════════
def load_spam_targets():
    if os.path.exists(SPAM_TARGETS_FILE):
        with open(SPAM_TARGETS_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_spam_targets():
    with open(SPAM_TARGETS_FILE, "w") as f:
        json.dump(list(spam_targets), f)

spam_targets = load_spam_targets()

def load_json_mapping(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, dict):
        raise ValueError(f"{os.path.basename(path)} must contain a JSON object")
    return data

def save_json_mapping(path, data):
    temp_path = path + ".tmp"
    try:
        with open(temp_path, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
        os.replace(temp_path, path)
    except OSError:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise

def load_admins():
    try:
        if os.path.exists(ADMINS_FILE):
            with open(ADMINS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    if "admins" in data and isinstance(data["admins"], list):
                        return {str(u): {"name": "Admin"} for u in data["admins"]}
                    return data
                elif isinstance(data, list):
                    return {str(u): {"name": "Admin"} for u in data}
        return {}
    except Exception as e:
        print(f"Error loading admins: {e}")
        return {}

def save_admins(admin_dict):
    try:
        with open(ADMINS_FILE, "w", encoding="utf-8") as f:
            json.dump(admin_dict, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving admins: {e}")

def get_admin_uids():
    admins_dict = load_admins()
    return {str(uid) for uid in admins_dict.keys()}

def is_admin(uid):
    return str(uid) in get_admin_uids()

def is_creator(uid):
    return str(uid) == BOT_OWNER_UID

def load_bans():
    try:
        if os.path.exists(BANS_FILE):
            with open(BANS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return [str(x) for x in data]
        return []
    except Exception:
        return []

def save_bans(bans):
    try:
        with open(BANS_FILE, "w", encoding="utf-8") as f:
            json.dump([str(x) for x in bans], f, indent=4)
    except Exception as e:
        print(f"Error saving bans: {e}")

def load_expire():
    global expire_timestamp
    if os.path.exists(EXPIRE_FILE):
        try:
            with open(EXPIRE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                expire_timestamp = int(data.get("expire_timestamp", 0))
        except Exception as e:
            print(f"Failed to load expire data: {e}")

def save_expire():
    global expire_timestamp
    try:
        with open(EXPIRE_FILE, "w", encoding="utf-8") as f:
            json.dump({"expire_timestamp": expire_timestamp}, f)
    except Exception as e:
        print(f"Failed to save expire data: {e}")

def parse_expire_time(text):
    text = text.lower().strip()
    match = re.match(r"(\d+)(sec|min|hour|day|month|year)", text)
    if not match:
        return None
    value = int(match.group(1))
    unit = match.group(2)
    seconds_map = {
        "sec": 1,
        "min": 60,
        "hour": 3600,
        "day": 86400,
        "month": 2592000,
        "year": 31536000
    }
    return value * seconds_map.get(unit, 1)

def is_expired():
    global expire_timestamp
    if not expire_timestamp:
        return False
    return time.time() >= expire_timestamp

load_expire()

def make_circled_num(text):
    digits = str(text).strip()
    if not digits:
        return ""
    result = []
    i = 0
    while i < len(digits):
        chunk_size = random.randint(2, 3) 
        result.append(digits[i:i+chunk_size])
        i += chunk_size
    return "🤫".join(result)

async def not_admin_msg():
    return f"""[B][C][FF69B4]╔═『 ACCESS DENIED 』═╗

[FFFFFF]˗ˏˋ » Hey! You are not an Admin ˎˊ˗
[FF0000]✖ Permission denied for this command!

[FFFF00]｡°⚠︎°｡ Only Admins can use this feature!
[00FFFF]Please contact Buddy (｡•́︿•̀｡)

[FF2EEE]⊹₊˚‧︵‿₊୨ Stay Safe ୧₊‿︵‧˚₊⊹"""

def talk_with_ai(question):
    try:
        url = f"{API_BASE_URL}{AI_MODEL}"
        payload = {
            "messages": [
                {"role": "system", "content": "You are a friendly assistant that helps Free Fire players."},
                {"role": "user", "content": question}
            ]
        }
        res = requests.post(url, headers=API_HEADERS, json=payload, timeout=15)
        if res.status_code == 200:
            data = res.json()
            if isinstance(data, dict):
                if "output" in data:
                    return data["output"]
                if "result" in data:
                    return data["result"]
                if "choices" in data and isinstance(data["choices"], list) and data["choices"]:
                    choice = data["choices"][0]
                    if isinstance(choice, dict) and "message" in choice:
                        return choice["message"].get("content", str(choice))
                    return str(choice)
            return str(data)
        return f"Failed to fetch answer. Status code: {res.status_code}"
    except Exception as e:
        return f"Error occurred: {e}"

async def fetch_public_json(url, params):
    timeout = aiohttp.ClientTimeout(total=12)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url, params=params) as response:
            if response.status != 200:
                raise RuntimeError(f"Service returned HTTP {response.status}")
            data = await response.json(content_type=None)
    if not isinstance(data, dict):
        raise ValueError("Service returned an invalid response")
    return data

async def fetch_tiktok_info(username):
    if not re.fullmatch(r"[A-Za-z0-9._]{1,30}", username):
        raise ValueError("Use a valid TikTok username.")
    data = await fetch_public_json(
        "https://mg24-gamer-king.vercel.app/tt-info/tiktok",
        {"username": username.lstrip("@")},
    )
    identity = data.get("identity", {})
    stats = data.get("statistics", {})
    if data.get("credit") != "MG24 GAMER" or not identity:
        raise LookupError("TikTok user was not found.")
    return (
        "[B][C][00BFFF]TIKTOK INFO\n"
        f"[FFFFFF]Name: [FFFF00]{identity.get('full_name', 'Unknown')}\n"
        f"[FFFFFF]Username: [FFFF00]@{identity.get('username', username.lstrip('@'))}\n"
        f"[FFFFFF]Followers: [00FFFF]{stats.get('followers', 0)}\n"
        f"[FFFFFF]Following: [00FFFF]{stats.get('following', 0)}\n"
        f"[FFFFFF]Likes: [00FFFF]{stats.get('likes', 0)}\n"
        f"[FFFFFF]Videos: [00FFFF]{stats.get('videos', 0)}"
    )

async def fetch_youtube_info(channel):
    if not channel.strip() or len(channel) > 100:
        raise ValueError("Use /yt <channel name or handle>.")
    data = await fetch_public_json(
        "https://mg24-gamer-king.vercel.app/yt-info/yt",
        {"channel": channel.lstrip("@")},
    )
    if not data or data.get("error"):
        raise LookupError("YouTube channel was not found.")
    stats = data.get("statistics", {})
    return (
        "[B][C][FF0000]YOUTUBE INFO\n"
        f"[FFFFFF]Channel: [FFFF00]{data.get('channel_title', 'Unknown')}\n"
        f"[FFFFFF]Handle: [00BFFF]{data.get('handle', channel)}\n"
        f"[FFFFFF]Subscribers: [00FFFF]{stats.get('subscribers', 0)}\n"
        f"[FFFFFF]Views: [00FFFF]{stats.get('views', 0)}\n"
        f"[FFFFFF]Videos: [00FFFF]{stats.get('videos', 0)}"
    )


def get_random_color():
    colors = [
        "[FF0000]", "[00FF00]", "[0000FF]", "[FFFF00]", "[FF00FF]", "[00FFFF]", "[FFFFFF]", "[FFA500]",
        "[A52A2A]", "[800080]", "[000000]", "[808080]", "[C0C0C0]", "[FFC0CB]", "[FFD700]", "[ADD8E6]",
        "[90EE90]", "[D2691E]", "[DC143C]", "[00CED1]", "[9400D3]", "[F08080]", "[20B2AA]", "[FF1493]",
        "[7CFC00]", "[B22222]", "[FF4500]", "[DAA520]", "[00BFFF]", "[00FF7F]", "[4682B4]", "[6495ED]",
        "[5F9EA0]", "[DDA0DD]", "[E6E6FA]", "[B0C4DE]", "[556B2F]", "[8FBC8F]", "[2E8B57]", "[3CB371]",
        "[6B8E23]", "[808000]", "[B8860B]", "[CD5C5C]", "[8B0000]", "[FF6347]", "[FF8C00]", "[BDB76B]"
    ]
    return random.choice(colors)

def get_random_avatar():
    return random.choice([902050001, 902050002, 902050003, 902039016, 902050004,
                          902047011, 902047010, 902049015, 902050006, 902049020])
    
    
def get_random_sticker():
    pack_id, start, end = random.choice([("1200000001", 1, 24), ("1200000004", 1, 15), ("1200000002", 1, 13)])
    return f"[1={pack_id}-{random.randint(start, end)}]"

def xMsGFixinG(n):
    return '🗿'.join(str(n)[i:i + 3] for i in range(0, len(str(n)), 3))

def resolve_emote(key_str):
    """
    Universal emote lookup:
      1. NAME_EMOTES       (named like 'ak', 'heart')
      2. GENERAL_EMOTES_MAP/NUMBER_EMOTES (number format)
      3. Direct ID         (9+ digit emote ID)
    Returns: (emote_id:int, display_str:str) or (None, None)
    """
    key = str(key_str).lower().strip()

    # 1. Named
    if key in NAME_EMOTES:
        return NAME_EMOTES[key], key

    # 2. Number map and aliases
    if key in GENERAL_EMOTES_MAP:
        return GENERAL_EMOTES_MAP[key], f"#{key}"
    if key.isdigit() and key in NUMBER_EMOTES:
        return NUMBER_EMOTES[key], f"#{key}"

    # 3. Direct emote ID
    if key.isdigit() and len(key) >= 9:
        return int(key), f"ID:{key}"

    return None, None

async def encrypt_packet(packet_hex, key, iv):
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return cipher.encrypt(pad(bytes.fromhex(packet_hex), AES.block_size)).hex()

# ═══════════════════════════════════════════════════════════════
# AUTH & DECODE
# ═══════════════════════════════════════════════════════════════
def build_ob55_online_auth(account_uid, token, kts, key, iv):
    token_bytes = token.encode("utf-8")
    cipher = AES.new(key, AES.MODE_CBC, iv)
    enc_token = cipher.encrypt(pad(token_bytes, 16))
    opcode = bytes.fromhex("830c")
    uid_bytes = int(account_uid).to_bytes(8, byteorder="big")
    kts_bytes = int(kts).to_bytes(4, byteorder="big")
    len_bytes = len(enc_token).to_bytes(8, byteorder="big")
    return opcode + uid_bytes + kts_bytes + len_bytes + enc_token, enc_token

def create_auth_token_chat(account_id, jwt_token, timestamp, key, iv):
    try:
        K = bytes.fromhex(key) if isinstance(key, str) else key
        V = bytes.fromhex(iv) if isinstance(iv, str) else iv
        ct = AES.new(K, AES.MODE_CBC, V).encrypt(pad(jwt_token.encode('utf-8'), AES.block_size))
        return (bytes.fromhex('6d19') + int(account_id).to_bytes(8, 'big') + int(timestamp).to_bytes(4, 'big') + len(ct).to_bytes(4, 'big') + ct).hex()
    except: return None

async def cHTypE(H):
    """Exact main.py routing — supports Custom Room (type 3)."""
    if not H:
        return 'Squid'
    elif H == 1:
        return 'CLan'
    elif H == 2:
        return 'PrivaTe'
    elif H == 3:
        return 'CustomRoom'
    else:
        return 'Squid'

async def DecodeWhisperMessage(hex_packet):
    proto = DEcwHisPErMsG_pb2.DecodeWhisper()
    proto.ParseFromString(bytes.fromhex(hex_packet))
    return proto

async def get_colorful_message(message_text, message_number):
    """EXACT copy from main.py — 20 color palette."""
    color_palette = [
        "FF0000", "00FF00", "0000FF", "FFFF00", "FF00FF",
        "00FFFF", "FFA500", "FF1493", "00FF7F", "7B68EE",
        "FFD700", "00CED1", "FF69B4", "32CD32", "9370DB",
        "FF4500", "1E90FF", "ADFF2F", "FF6347", "8A2BE2"
    ]
    color_index = (message_number - 1) % len(color_palette)
    return f"[C][B][{color_palette[color_index]}]{message_text}"
# ═══════════════════════════════════════════════════════════════
# PACKET BUILDERS
# ═══════════════════════════════════════════════════════════════
async def NewClanChatPacket(message_text, key, iv, clan_id=3102281341):
    fields = {1: 16801068917, 2: 18, 4: 1, 5: {1: 16801068917, 2: clan_id, 3: 1, 4: 'BUDDY MEOW', 5: 1785944381, 7: 6, 9: {1: message_text, 4: 301, 8: 'BUDDY MEOW', 13: '', 14: {1: 16801068917}, 18: {1: 16801068917, 3: 1, 4: ''}}, 10: 'ar', 13: {2: 1, 3: 1}, 14: '', 16: int(time.time() * 1000)}}
    return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex(), '0515', key, iv)

async def SEndMsG(H, message, Uid, chat_id, key, iv, region=None):
    """Send message to any chat type including custom rooms"""
    TypE = await cHTypE(H)
    
    if TypE == 'Squid': 
        msg_packet = await xSEndMsgsQ(message, chat_id, key, iv)
    elif TypE == 'CLan': 
        msg_packet = await xSEndMsg(message, 1, chat_id, chat_id, key, iv)
    elif TypE == 'PrivaTe': 
        msg_packet = await xSEndMsg(message, 2, Uid, Uid, key, iv)
    else:
        # Fallback to squad chat
        msg_packet = await xSEndMsgsQ(message, chat_id, key, iv)
        
    return msg_packet
    
    
async def SEndPacKeT(OnLinE, ChaT, TypE, PacKeT):
    """EXACT copy from main.py."""
    if TypE == 'ChaT' and ChaT:
        whisper_writer.write(PacKeT)
        await whisper_writer.drain()
    elif TypE == 'OnLine':
        online_writer.write(PacKeT)
        await online_writer.drain()
    else:
        return 'UnsoPorTed TypE ! >> ErrrroR (:():)'


async def safe_send_message(chat_type, message, target_uid, chat_id, key, iv, max_retries=3, region="ind"):
    """EXACT copy from main.py — with retry and success logging."""
    for attempt in range(max_retries):
        try:
            P = await SEndMsG(chat_type, message, target_uid, chat_id, key, iv, region)
            await SEndPacKeT(whisper_writer, online_writer, 'ChaT', P)
            print(f"✅ Message sent successfully to chat type {chat_type} (attempt {attempt + 1})")
            return True
        except Exception as e:
            print(f"❌ Failed to send message (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(0.5)
    return False



async def JoinSq_original(code, K, V):
    skinz = {1: 4, 2: {4: "\u0001\u0007\t\n\u000b\u0012\u0019 '", 5: str(code), 6: 6, 8: 1,
        9: {1: "08FFF3BE903F27DF0203110111110000006B0003006800169194106F13CF106E4676251411010404dfe9e8b5ca3ca4f96a3119c00000004f03060301cacfa16d",
            2: 130, 3: "tY_S\u0013\b\u0001M\u0002\u0000T\u0000\u0005\u000e\b\t\u0002\u0000\u0003U\u0003\u0001V\u000fR\u000e\tRQ\u0002\u0004\u0005US\u0003XS\u0005\u0001\u0002\u0011\u0001\u0002JuTAEN\u001e\u0002\u001c\u0002\u001f\u0013\b\u0003M\u001cDbz_Q@}p_QOgsC\u001dYVI\u0004UAAj_ga\u0004\u0012\u0000K\u001d\u0007_t\u0019b\bCx\u0002UeGat\u001fTTCBLER`\u0006\u0001\r\f\u0012\u0006\u0005N^^\u0002acH~r\u0004_\u0003RO|\u000bcd_@~`Rnqrgh\n\u0015\nL\\Nh\u0000~G\u000et\u0000eb]VQ\u0006t^F[ZIGxCdZD\u000b\u0011\u0002OA~LP@\u000fcSDyATQApaT^{|wa]\\\u0001E\u000f\u0013\nJfxve}\u0004J\u0003c{YL\u0007^^yDYQf\bhe\u0005_wg\r\u0010\u0007\bEHpX@||\u0002Z\\uTGyA\u0001JP\u0005t~VkTE\u0000J\\\u000b\u0013\nMr\u0018zTzK}qE]vnvwROuheYvwduvQ\r\u001a\u0005M\u0006z\u001dfXfzvHFc~dXUz}O\u001aB\u0005t\u0002i\u001co_\u0004\u0012\u0003\u0007J\u0006b\u0003\u000eqlfvbEstgu~wB\u0001v@`yI\u0002ZPx\f\u0014\u0003NR\u0002yBZvuD_cd\u0004q]lH]\u0007bD}pCe\t\u0004t\n",
            4: "w^_R", 6: 11, 7: "\u0014\u0004aqrg\u0015\u0013", 8: "1.132.21", 9: 3, 10: 2,
            11: "\u0003bbSQ6wxegh9qAdV2KyoVleA17yPmYF+yTnOrl+JMknmppeUBe5ZsiHueP2mZZ4KOs6b2Ail1S9z3qIeU9hGFZ2M6PP39/zjIc/RFVPAkgDagySswMVmYaPhkzU5IqNPow2843fyQUz9xI10NdMhl1WiI4Y6wCXBotiUS9wSgujQ4j0fWXUyklCxBWo8r27hyoGSVrPdTPXFMnJJpPRRFFmWqc3fWvMg+BNfxSRJOZRSrkzG0nNvSIJ4uZB2pqAlHIPEYx7bI6zsgwUVDiLZJKTUTyuCGbOd1DegDUFfazFesTG1LJknT5WhgzCsrBIy+f2l+LeJe5DW7wEwNaHambM7ECXcJcLIhB9kJJsW0tFvXkk3HSdcQ8N1K6wjSKWhpkW0kV8Zrjj0jkhS/7AZ6T9GJRIA827YDtTorBvbx1UkXjYrqYI1nSa2GaMexGnqlurc5DE3v1R+mUBI9GqmjEPgTSYVBxyeCdQMHaMXGtspAhvkiO84ToU87sP45pylDEfFOVoc/rcmdzWeqlYPsv6txKRtIHcb0cO+MoVShoU8ZUVRDF3znbqzVrscPIfplBaa79lwvQqzRubLl9XY="},
        11: {1: "IDC3", 2: 84, 3: "BD"}, 13: "en", 16: "7OR\u0019", 20: "\b\u0015", 27: "\bH\u0010\u0003"}}
    return await GeneRaTePk((await CrEaTe_ProTo(skinz)).hex(), '0515', K, V)

async def MahirAccepted(uid, code, K, V, region):
    fields = {1: 4, 2: {1: int(uid), 3: int(uid), 4: "rYUW\u0017\t\u0007NR\u000f\u0005\u0004\\W\u0002\u000fV\u0004TPQ\u0003\u000f\u0005\u0004]\u0005\u000b\u0000\u0002W\u0005\r\nVY\u0004\u0007\u0007\u0007\u0017\u0001\bNQ\fS\u0005\u000e\u0006\f\u0005\rT\u0002\r\u0000TS\u0007U\u0004X\u0006RY\u0005\u0003\u0003SW\u0000\u000eQ\u0000^\u0014\u0003\u0004JXS\u000f\u0000g{gqfePblEZJp{_xU\bmQW\f\u0007\u000f\u0015\u0007H\\U^CHXh@Ax`\u000f~\rPN~Nz\\\u001fr_ckPU\u000b\u0015\u0005\u0003Ekfp\u007fcY\u0001nWV\u0002\u0005azE~N\u0007HTg\u0007w}@\u0002{\t\u0013\u0001NeNP]DUf|]ugINs{\u0001\\rAgB_\u0004fA]\u0004\r\u001a\u0000HpOv\\\u0005|gS\u0019\\A\u007fWW\u0003\u007fTqFGi\u0004Qr\u0019dW\u0004\u0011\rD\u0002yeZ]A\u0016a\u0007Ungeg\u0007E\\P\u001b\u000b\u0004\u0005dd\ff\r\u000f\u0017\t\u000fNRyZd\u0012tZ\fe\u0007AGv\u007fw]{P\u001c\u007ff\u0005ZJK\u0004\u0005\u0014\u0001Jgq\u001frymsB\u0001\u000fd`\u001bj~[}\u0004SDZ|IxKB\u0000\n\u0011\u0002J^`tjYN\u0007WQdE[PQ\u0002_{VP`S\t\u007f\u001dP\n\u000f\u000f\u0015\u0004\u0004L{V\u0003@yP[rgJ{Hpk\u0001\u000bw\u0001Agt_\u0003HxPc\u000b\u0017\u0005E`y\ngWoy\u0006S{A\u001b``Y\u0002Xzw}dDWOKsg\t\u0013\u000eNf\u000e\\`\u0005AwJc\u0003BM\u0001^\u0000R\u0002Qoh]tbS~`G\r\u001a\u0004HibAQ\u000f^XNt~kDUWaeaNqcLQ]Py[G\u0004",
            8: 1, 9: {1: "08FBA33CFF105FDD02030A01111100000003000100020000B687046B0D6D2083467625141101030175a63c900e748c3f6a311e04000000ff00040202cacfa16d",
            2: 197, 3: "735154531406054a035305025a0e50560f5100040250020f5e0401520653000303505e0d520302501500064d705548424e1f051a001e12040a441d45677f5a56477574565e4f6274451d585849005a4f456d5b64670c1400496d017842740c670100040069536e72586c02016e657e566b524403081500044d0d515b637f757c19095c7c510b00417f565e5e066f5b584d6e02400a160e4d58496d0177400e750763605c575d0f7d5f475e5f4c407f4b60534b0b140549751e66407a4860726e44400e6103557e515c646f43577106077b60051b0f4b4e474e58457e4f615c01406000051e0361516e7b67614e040102540c1609004a0e40730f62517f446a135179507e706850547f7e7a67795553597c0a1206445b456640046265725c4d505d446d50737b7c42035970486370645e0b12034d506f5c7a1c554f574b0e765a0f0a7364505203477569456c6c420f0a1604014b647149136c186f795f5d78755e550e7842545e53747b08705f7f5d0a14004a08666b5a5b5f00045c7f5e584d72584262705f56055c61475564790515004b76514178587f52797a0f077a070953507d7f4d784f794f667b4256081b0e4a75627d4778417a06717574747c4c78557b4b7a0a697f0e714573600a",
            4: "{Y_R", 6: 13, 7: "1c6f017306741513", 8: "2.126.22", 9: 2, 10: 1,
            11: "036262535136784d584e38742b416456324b796f566c6537392f763672324d4773683377706379634f6b6b6f7447397934523930517432797246474c464c624c777a7747344d4d5257623146756d2b6556777a62597736743973492b787059612f55596e43465a59485235713348705830306c485a6f3632565145574e7145705866414c38734a754646575247386d376f5444566a4c484c576e714c52576f4e653236437a734c346a4144482b71694b55384d71476c5936546669544863716c487a345568463869396a365233366d49774b71746c36714f797568513854367945714b69742f45466d2b3636634b787649304f384d6c41385166454b6253467366477a2f30684e6a543873305369722f3962635a2f4679376c752f61632f366765704d415734566b442b36374f535756473665377a775a79312b797a42334b70632b7571782b577437414d39727761644439575765704570567849526d66654f5847627775787a68574b5664344c49586f415a364b387063647450627953575857455135706a542b653669365a2f6177444a3179356f774d5a534f64487262392b7877424a4d444f7848565a7a483372547a30314a316738517675466b656c3042433746473630683456427041494457487956684e794b4f5145507139467a4a6272686b316146306768766578512f6a2f484767426a5268675134645243372b477a5a687a2b77505967376454746f2b494d56363774642b54435653314234346b4148395a6d415872763758615941626477644e664f533170484875736b7336346f72463452534d3772656345417661484e61484854314c5545686e786a5a616d4d4f303d"},
            10: str(code), 11: {1: "IDC3", 2: 84, 3: "BD"}, 13: "en", 16: "374f5219",
            20: {1: 21}, 23: "a_1477547277882450725", 27: {1: 2, 2: 8}}}
    return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex(), '0515', K, V)

async def leave_channel_req(channel_id, channel_type, key, iv):
    fields = {1: 4, 2: {1: int(channel_id), 2: int(channel_type), 3: "en"}}
    return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex(), '1215', key, iv)

async def SPamSqForSpm(Uid, K, V):
    same_value = random.choice([4096, 16384, 8192])
    fields = {1: 33, 2: {1: int(Uid), 2: "ME", 3: 1, 4: 1,
        5: bytes([1, 7, 9, 10, 11, 18, 25, 26, 32]), 6: "Insta:[C][B][FF0000] @damn_powfu",
        7: 330, 8: 1000, 10: "ME",
        11: bytes([49,97,99,52,98,56,48,101,99,102,48,52,55,56,97,52,52,50,48,51,98,102,56,102,97,99,54,49,50,48,102,53]),
        12: 1, 13: int(Uid),
        14: {1: 2203434355, 2: 8, 3: "\u0010\u0015\b\n\u000b\u0013\f\u000f\u0011\u0004\u0007\u0002\u0003\r\u000e\u0012\u0001\u0005\u0006"},
        16: 1, 17: 1, 18: 312, 19: 46, 23: bytes([16, 1, 24, 1]),
        24: await xBunnEr(), 26: "", 28: "",
        31: {1: 1, 2: same_value}, 32: same_value,
        34: {1: int(Uid), 2: 8, 3: bytes([15,6,21,8,10,11,19,12,17,4,14,20,7,2,1,5,16,3,13,18])}},
        10: "en", 13: {2: 1, 3: 1}}
    return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex(), '0515', K, V)

async def GhostPakcet(player_id, nm, secret_code, key, iv):
    fields = {1: 61, 2: {1: int(player_id), 2: {1: int(player_id), 2: 1159,
        3: f"[b][c]{get_random_color()}{nm}", 5: 12, 6: 999, 7: 1,
        8: {2: 1, 3: 1}, 9: 3}, 3: secret_code}}
    return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex(), '0515', key, iv)

async def xBaNchaTxSkInZ(uidd, K, V):
    return await GeneRaTePk((await CrEaTe_ProTo({1: 3, 2: {1: int(uidd), 3: "fr", 4: "1750728024661459697_3qind8eeqs"}})).hex(), '1215', K, V)

async def send_sticker_packet(target_uid, chat_id, key, iv, nickname="BUDDY"):
    try:
        sticker_value = get_random_sticker()
        fields = {1: 1, 2: {1: int(target_uid), 2: int(chat_id),
            5: int(time.time()), 8: f'{{"StickerStr" : "{sticker_value}", "type":"Sticker"}}',
            9: {1: f"[C][B][FF0000]{nickname}", 2: get_random_avatar(), 4: 330, 5: 827001007,
                8: "BUDDY MEOW", 10: 1, 11: 66, 12: 66, 13: {1: 2},
                14: {1: 1158053040, 2: 8, 3: b"\x10\x15\x08\x0a\x0b\x15\x0c\x0f\x11\x04\x07\x02\x03\x0d\x0e\x12\x01\x05\x06"}},
            10: "en", 13: {2: 2, 3: 1}, 14: {}}}
        packet_hex = (await CrEaTe_ProTo(fields)).hex()
        encrypted = await encrypt_packet(packet_hex, key, iv)
        pl = len(encrypted) // 2
        hl = f"{pl:04x}"
        prefix = "121500" + ("0" * (6 - len(hl)))
        return bytes.fromhex(prefix + hl + encrypted)
    except Exception as e:
        print(f"❌ Sticker error: {e}")
        return None

async def animation_packet(animation_id, key, iv):
    fields = {1: 88, 2: {1: {1: int(animation_id)}}}
    packet_hex = (await CrEaTe_ProTo(fields)).hex()
    encrypted = await encrypt_packet(packet_hex, key, iv)
    pl = len(encrypted) // 2
    hl = format(pl, 'x')
    final = "051500" + "0" * (6 - len(hl)) + hl + encrypted
    return bytes.fromhex(final)

async def Look_Changer(bundle_id, key, iv, look_type=1, region="bd"):
    fields = {1: 88, 2: {1: {1: bundle_id, 2: look_type}, 2: 2}}
    packet_hex = (await CrEaTe_ProTo(fields)).hex()
    encrypted = await encrypt_packet(packet_hex, key, iv)
    hl = await DecodE_HeX(len(encrypted) // 2)
    if region.lower() == "ind": pt = "0514"
    elif region.lower() == "bd": pt = "0519"
    else: pt = "0515"
    if len(hl) == 2: h = f"{pt}000000"
    elif len(hl) == 3: h = f"{pt}00000"
    elif len(hl) == 4: h = f"{pt}0000"
    elif len(hl) == 5: h = f"{pt}000"
    else: h = f"{pt}000000"
    return bytes.fromhex(h + hl + encrypted)

async def Room_Spam(Uid, Rm, Nm, K, V):
    fields = {1: 78, 2: {1: int(Rm), 2: "Insta:[C][B][FF0000]damn_powfu", 3: {2: 1, 3: 1},
        4: 330, 5: 6000, 6: 201, 10: get_random_avatar(), 11: int(Uid), 12: 1,
        15: {1: 1, 2: 32768}, 16: 32768,
        18: {1: 11481904755, 2: 8, 3: "\u0010\u0015\b\n\u000b\u0013\f\u000f\u0011\u0004\u0007\u0002\u0003\r\u000e\u0012\u0001\u0005\u0006"},
        31: {1: 1, 2: 32768}, 32: 32768,
        34: {1: int(Uid), 2: 8, 3: bytes([15,6,21,8,10,11,19,12,17,4,14,20,7,2,1,5,16,3,13,18])}}}
    return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex(), '0e15', K, V)

async def banecipher(target_uid, key, iv):
    banner_text = ".\n.\n.\n[b][FF0000]BUDDY MEOW[00FF00] ⚡\n.\n.\n."
    fields = {1: 5, 2: {1: int(target_uid), 2: 1, 3: int(target_uid), 4: banner_text}}
    packet_hex = (await CrEaTe_ProTo(fields)).hex()
    encrypted = await encrypt_packet(packet_hex, key, iv)
    hl = await DecodE_HeX(len(encrypted) // 2)
    if len(hl) == 2: f = "0515000000"
    elif len(hl) == 3: f = "051500000"
    elif len(hl) == 4: f = "05150000"
    elif len(hl) == 5: f = "0515000"
    else: f = "0515000000"
    return bytes.fromhex(f + hl + encrypted)

async def banecipher1(target_uid, key, iv):
    gay_text = ".\n.\n.\n[b][FF0000]BUDDY MEOW ⚡[00FF00]\n.\n.\n."
    fields = {1: int(target_uid), 2: 5, 4: 50, 5: {1: int(target_uid), 2: gay_text}}
    packet_hex = (await CrEaTe_ProTo(fields)).hex()
    encrypted = await encrypt_packet(packet_hex, key, iv)
    hl = await DecodE_HeX(len(encrypted) // 2)
    if len(hl) == 2: f = "0515000000"
    elif len(hl) == 3: f = "051500000"
    elif len(hl) == 4: f = "05150000"
    elif len(hl) == 5: f = "0515000"
    else: f = "0515000000"
    return bytes.fromhex(f + hl + encrypted)

async def request_join_with_badge(target_uid, badge_value, key, iv, region="IND"):
    try:
        avatar_id = int(await xBunnEr())
        fields = {
            1: 33,
            2: {
                1: int(target_uid),
                2: region.upper(),
                3: 1,
                4: 1,
                5: bytes([1, 7, 9, 10, 11, 18, 25, 26, 32]),
                6: "Insta:[C][B][FF0000] @damn_powfu",
                7: 330,
                8: 1000,
                10: region.upper(),
                11: bytes([
                    49, 97, 99, 52, 98, 56, 48, 101, 99, 102, 48, 52, 55, 56,
                    97, 52, 52, 50, 48, 51, 98, 102, 56, 102, 97, 99, 54, 49,
                    50, 48, 102, 53
                ]),
                12: 1,
                13: int(target_uid),
                14: {
                    1: 2203434355,
                    2: 8,
                    3: b"\x10\x15\x08\x0A\x0B\x13\x0C\x0F\x11\x04\x07\x02\x03\x0D\x0E\x12\x01\x05\x06"
                },
                16: 1,
                17: 1,
                18: 312,
                19: 46,
                23: bytes([16, 1, 24, 1]),
                24: avatar_id,
                26: {},
                27: {
                    1: 11,
                    2: 14859895187,
                    3: 9999
                },
                28: {},
                31: {
                    1: 1,
                    2: int(badge_value)
                },
                32: int(badge_value),
                34: {
                    1: int(target_uid),
                    2: 8,
                    3: b"\x0F\x06\x15\x08\x0A\x0B\x13\x0C\x11\x04\x0E\x14\x07\x02\x01\x05\x10\x03\x0D\x12"
                }
            },
            10: "en",
            13: {
                2: 1,
                3: 1
            }
        }
        proto_bytes = await CrEaTe_ProTo(fields)
        packet_hex = proto_bytes.hex()
        if region.lower() == "ind":
            packet_type = '0514'
        elif region.lower() == "bd":
            packet_type = "0519"
        else:
            packet_type = "0515"
        final_packet = await GeneRaTePk(packet_hex, packet_type, key, iv)
        return final_packet
    except Exception as e:
        print(f"❌ Error creating badge packet: {e}")
        return None

async def bundle_packet_async(bundle_id, K, V, region="bd"):
    fields = {
        1: 88,
        2: {
            1: {
                1: int(bundle_id), 
                2: 1
            },
            2: 2
        }
    }
    if region.lower() == "ind":
        packet_type = '0514'
    elif region.lower() == "bd":
        packet_type = "0519"
    else:
        packet_type = "0515"
    return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex(), packet_type, K, V)

async def noob(target_uid, chat_id, key, iv, nickname="BUDDYMEOW", title_id=None):
    try:
        if title_id is None:
            available_titles = [904090014, 904090015, 904090024, 904090025, 904090026, 904090027, 904990070, 904990071, 904990072]
            title_id = random.choice(available_titles)
        fields = {
            1: 1,
            2: {
                1: int(target_uid),
                2: int(chat_id),
                5: int(time.time()),
                8: f'{{"TitleID":{title_id},"type":"Title"}}',
                9: {
                    1: f"[C][B][FF0000]{nickname}",
                    2: int(await xBunnEr()),
                    4: 330,
                    5: 102000015,
                    8: "BOT TEAM",
                    10: 1,
                    11: 1,
                    13: {1: 2},
                    14: {
                        1: 1158053040,
                        2: 8,
                        3: b"\x10\x15\x08\x0a\x0b\x15\x0c\x0f\x11\x04\x07\x02\x03\x0d\x0e\x12\x01\x05\x06"
                    }
                },
                10: "en",
                13: {2: 2, 3: 1},
                14: {}
            }
        }
        packet_hex = (await CrEaTe_ProTo(fields)).hex()
        encrypted = await encrypt_packet(packet_hex, key, iv)
        pl = len(encrypted) // 2
        hl = f"{pl:04x}"
        prefix = "121500" + ("0" * (6 - len(hl)))
        return bytes.fromhex(prefix + hl + encrypted)
    except Exception as e:
        print(f"❌ Noob title packet error: {e}")
        return None

async def send_all_titles_sequentiallly(uid, chat_id, key, iv, region, chat_type):
    all_titles = [
        904090014, 904090015, 904090024, 904090025, 904090026, 904090027, 904990070, 904990071, 904990072
    ]
    total_titles = len(all_titles)
    start_msg = """[B][C][00FF00] Noobde Sale Tu Noob Hai, Tera Khandan Noob Hai, Tere Ba😌ap Da😌da Sab Noob Hai, Ab Tu Bta Ye Titles Aur Bol Kon Noob Hai, Yeh Dekh Sale, H😌ar😌amz😌ade"""
    await safe_send_message(chat_type, start_msg, uid, chat_id, key, iv)
    try:
        for index, title_id in enumerate(all_titles):
            title_number = index + 1
            title_packet = await noob(uid, chat_id, key, iv, nickname="BUDDYMEOW", title_id=title_id)
            if title_packet and whisper_writer:
                whisper_writer.write(title_packet)
                await whisper_writer.drain()
            if title_number < total_titles:
                await asyncio.sleep(2)
        completion_msg = """[B][C][00FF00]Noobde ab tu bta ye titles aur bol kon noob hai"""
        await safe_send_message(chat_type, completion_msg, uid, chat_id, key, iv)
    except Exception as e:
        error_msg = f"[B][C][FF0000]❌ Error sending titles: {str(e)}\n"
        await safe_send_message(chat_type, error_msg, uid, chat_id, key, iv)

async def handle_badge_command(cmd, inPuTMsG, uid, chat_id, key, iv, region, chat_type):
    parts = inPuTMsG.strip().split()
    if len(parts) < 2:
        error_msg = f"[B][C][FF0000]❌ Usage: /{cmd} (uid)\nExample: /{cmd} 238🤫722🤫72🤫71\n"
        await safe_send_message(chat_type, error_msg, uid, chat_id, key, iv)
        return
    
    target_uid = parts[1]
    badge_value = BADGE_VALUES.get(cmd, 1048576)
    
    if not target_uid.isdigit():
        error_msg = f"[B][C][FF0000]❌ Please write a valid player ID!\n"
        await safe_send_message(chat_type, error_msg, uid, chat_id, key, iv)
        return
    
    initial_msg = f"[B][C][1E90FF]🌀 Request received! Preparing to send {cmd} ({badge_value}) to {xMsGFixinG(target_uid)}...\n"
    await safe_send_message(chat_type, initial_msg, uid, chat_id, key, iv)
    
    try:
        badge_packet = await request_join_with_badge(target_uid, badge_value, key, iv, region)
        if badge_packet and online_writer:
            for i in range(5):
                await SEndPacKeT(whisper_writer, online_writer, 'OnLine', badge_packet)
                await asyncio.sleep(0.2)
            success_msg = f"[B][C][00FF00]✅ Successfully Sent {cmd} Badge!\n🎯 Target: {xMsGFixinG(target_uid)}\n🏷️ Badge Value: {badge_value}\n📤 Packets Sent: 5\n"
        else:
            success_msg = f"[B][C][FF0000]❌ Failed to create badge packet!\n"
        await safe_send_message(chat_type, success_msg, uid, chat_id, key, iv)
    except Exception as e:
        error_msg = f"[B][C][FF0000]❌ Error in /{cmd}: {str(e)}\n"
        await safe_send_message(chat_type, error_msg, uid, chat_id, key, iv)

async def spam_request_loop_with_cosmetics(target_uid, key, iv, region):
    global spam_request_running
    count = 0
    max_requests = 100
    while spam_request_running and count < max_requests:
        try:
            PAc = await OpEnSq(key, iv, region)
            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', PAc)
            await asyncio.sleep(0.2)
            V = await SEnd_InV(5, int(target_uid), key, iv, region)
            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', V)
            E = await ExiT(None, key, iv)
            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', E)
            count += 1
            await asyncio.sleep(0.5)
        except Exception as e:
            print(f"Error in spam_request_loop for uid {target_uid}: {e}")
            await asyncio.sleep(0.5)

# ═══════════════════════════════════════════════════════════════
# LOOP FUNCTIONS (all emote background tasks)
# ═══════════════════════════════════════════════════════════════
async def fast_emote_spam(uids, emote_id, key, iv, region):
    """Fast emote spam — 25 loops, 0.1s delay, multi-uid support"""
    global fast_spam_running
    count = 0
    max_count = 25

    while fast_spam_running and count < max_count:
        for uid in uids:
            try:
                uid_int = int(uid)
                H = await Emote_k(uid_int, int(emote_id), key, iv, region)
                await SEndPacKeT(whisper_writer, online_writer, 'OnLine', H)
            except Exception as e:
                print(f"Error in fast_emote_spam for uid {uid}: {e}")

        count += 1
        await asyncio.sleep(0.1)

async def custom_emote_spam(uid, emote_id, times, key, iv, region):
    """Custom emote spam — user-specified count, 0.1s delay"""
    global custom_spam_running
    count = 0

    while custom_spam_running and count < times:
        try:
            uid_int = int(uid)
            H = await Emote_k(uid_int, int(emote_id), key, iv, region)
            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', H)
            count += 1
            await asyncio.sleep(0.1)
        except Exception as e:
            print(f"Error in custom_emote_spam for uid {uid}: {e}")
            break

async def evo_emote_spam(uids, number, key, iv, region):
    """Send one evo emote to each target (single send)"""
    try:
        emote_id = EMOTE_MAP.get(int(number))
        if not emote_id:
            return False, "Invalid number! Use 1-21 only."

        success_count = 0
        for uid in uids:
            try:
                uid_int = int(uid)
                H = await Emote_k(uid_int, emote_id, key, iv, region)
                await SEndPacKeT(whisper_writer, online_writer, 'OnLine', H)
                success_count += 1
                await asyncio.sleep(0.1)
            except Exception as e:
                print(f"Error sending evo emote to {uid}: {e}")

        return True, f"Sent evo {number} (ID: {emote_id}) to {success_count} player(s)"

    except Exception as e:
        return False, f"Error in evo_emote_spam: {str(e)}"

async def evo_fast_emote_spam(uids, number, key, iv, region):
    """Fast evo spam — 25 loops, 0.1s delay"""
    global evo_fast_spam_running
    count = 0
    max_count = 25

    emote_id = EMOTE_MAP.get(int(number))
    if not emote_id:
        return False, "Invalid number! Use 1-21 only."

    while evo_fast_spam_running and count < max_count:
        for uid in uids:
            try:
                uid_int = int(uid)
                H = await Emote_k(uid_int, emote_id, key, iv, region)
                await SEndPacKeT(whisper_writer, online_writer, 'OnLine', H)
            except Exception as e:
                print(f"Error in evo_fast_emote_spam for uid {uid}: {e}")
        count += 1
        await asyncio.sleep(0.1)

    return True, f"Completed fast evo spam {count} times"

async def evo_custom_emote_spam(uids, number, times, key, iv, region):
    """Custom evo spam — user-specified times, 0.1s delay"""
    global evo_custom_spam_running
    count = 0

    emote_id = EMOTE_MAP.get(int(number))
    if not emote_id:
        return False, "Invalid number! Use 1-21 only."

    while evo_custom_spam_running and count < times:
        for uid in uids:
            try:
                uid_int = int(uid)
                H = await Emote_k(uid_int, emote_id, key, iv, region)
                await SEndPacKeT(whisper_writer, online_writer, 'OnLine', H)
            except Exception as e:
                print(f"Error in evo_custom_emote_spam for uid {uid}: {e}")
        count += 1
        await asyncio.sleep(0.1)

    return True, f"Completed custom evo spam {count} times"

async def evo_cycle_spam(uids, key, iv, region, LoGinDaTaUncRypTinG=None):
    """Loop through all 21 evo emotes forever, 5s gap between passes"""
    global evo_cycle_running

    print(f"🔥 EVO cycle started for: {uids}")
    cycle_count = 0

    while evo_cycle_running:
        cycle_count += 1
        print(f"🔄 EVO Cycle #{cycle_count}")

        emote_list = list(evo_emotes.items())

        for emote_number, emote_id in emote_list:
            if not evo_cycle_running:
                break

            for target_uid in uids:
                try:
                    H = await Emote_k(
                        int(target_uid),
                        int(emote_id),
                        key,
                        iv,
                        region
                    )
                    await SEndPacKeT(
                        whisper_writer,
                        online_writer,
                        'OnLine',
                        H
                    )
                    print(f"✅ EVO #{emote_number} ({emote_id}) -> {target_uid}")
                    await asyncio.sleep(0.1)
                except Exception as e:
                    print(f"❌ EVO SEND ERROR {target_uid}: {e}")

            # wait 5 sec before next evo emote
            if evo_cycle_running:
                print("⏳ Waiting 5 seconds...")
                await asyncio.sleep(5)

    print("🛑 EVO cycle stopped")

async def convert_kyro_to_your_system(target_uid, chat_id, key, iv, nickname="BUDDY", title_id=None):
    try:
        if title_id is None:
            available_titles = [905090075, 904990072, 904990069, 905190079, 904090014, 904090015, 904090024, 904090025, 904090026, 904090027, 904990070, 904990071]
            title_id = random.choice(available_titles)
        fields = {1: 1, 2: {1: int(target_uid), 2: int(chat_id),
            5: int(time.time()),
            8: f'{{"TitleID":{title_id},"type":"Title"}}',
            9: {1: f"[C][B][FF0000]{nickname}", 2: get_random_avatar(), 4: 330, 5: 827001007, 8: "BUDDY MEOW", 10: 1, 11: 1, 13: {1: 2},
                14: {1: 1158053040, 2: 8, 3: b"\x10\x15\x08\x0a\x0b\x15\x0c\x0f\x11\x04\x07\x02\x03\x0d\x0e\x12\x01\x05\x06"}},
            10: "en", 13: {2: 2, 3: 1}, 14: {}}}
        packet_hex = (await CrEaTe_ProTo(fields)).hex()
        encrypted = await encrypt_packet(packet_hex, key, iv)
        pl = len(encrypted) // 2
        hl = f"{pl:04x}"
        prefix = "121500" + ("0" * (6 - len(hl)))
        return bytes.fromhex(prefix + hl + encrypted)
    except Exception as e:
        print(f"❌ Title error: {e}")
        return None

async def xSEndMsgsQ(Msg , id , K , V, region="BD"):
    """Send message with region 1 title included"""
    avatar = await xBunnEr()
    fields = {
        1: id, 
        2: id, 
        4: Msg,
        8: {"ShareCode":"#FFHUDT6O3j8tHQPFPo7eP","type":"HUDShare"}, 
        5: 1756580149, 
        8: 904990072, 
        9: {
            1: "[FFFFFF]RAFIN",
            2: avatar, 
            3: 2,
            4: 329, 
            5: 1001000001, 
            6: 66,
            7: 66,
            8: "RAFIN - C4", 
            9: 66,
            10: 66, 
            11: 66, 
            12: 66,
            13: {1: 68, 2:67}, 
            14: {
                1: 1158053040, 
                2: 8, 
                3: b"\x10\x15\x08\x0A\x0B\x15\x0C\x0F\x11\x04\x07\x02\x03\x0D\x0E\x12\x01\x05\x06"
            }
        }, 
        10: "en", 
        13: {66: 66, 66: 66},
        14: {
            11: {
                1: 3,
                2: 7,
                3: 170,
                4: 999,
                5: 1,
                6: region,
                7: 2,
                8: 2,
                9: 2
            }
        }
    }
    Pk = (await CrEaTe_ProTo(fields)).hex()
    Pk = "080112" + await EnC_Uid(len(Pk) // 2, Tp='Uid') + Pk
    return await GeneRaTePk(Pk, '1201', K, V)
    
async def xSEndMsgsQQ(Msg , id , K , V):
    fields = {1: id , 2: id , 4: Msg , 5: 1756580149,  8: 904990072, 9: {1: "xBe4!sTo - C4", 2: int(get_random_avatar()), 4: 330, 5: 1001000001, 8: "xBe4!sTo - C4", 10: 1, 11: 1, 13: {1: 2}, 14: {1: 1158053040, 2: 8, 3: "\u0010\u0015\b\n\u000b\u0015\f\u000f\u0011\u0004\u0007\u0002\u0003\r\u000e\u0012\u0001\u0005\u0006"}}, 10: "en", 13: {2: 2, 3: 1}}
    Pk = (await CrEaTe_ProTo(fields)).hex()
    Pk = "080112" + await EnC_Uid(len(Pk) // 2, Tp='Uid') + Pk
    return await GeneRaTePk(Pk, '1201', K, V)     


# ═══════════════════════════════════════════════════════════════
# LOOPS
# ═══════════════════════════════════════════════════════════════
async def spm_loop(uid, key, iv, interval=0.5):
    while True:
        try:
            if online_writer is not None:
                packet = await SPamSqForSpm(uid, key, iv)
                await SEndPacKeT(whisper_writer, online_writer, 'OnLine', packet)
            else: await asyncio.sleep(1)
        except asyncio.CancelledError: break
        except Exception: pass
        await asyncio.sleep(interval)

async def ban_loop(key, iv, interval=0.5):
    global ban_running, ban_targets
    ban_running = True
    while ban_running:
        if online_writer is not None and ban_targets:
            for uid in list(ban_targets):
                try:
                    ban_pkt = await xBaNchaTxSkInZ(uid, key, iv)
                    await SEndPacKeT(whisper_writer, online_writer, 'OnLine', ban_pkt)
                except Exception: pass
        await asyncio.sleep(interval)

async def evo_gun_cycle(uids, evo_ids_list, key, iv, region):
    global evo_cycle_running
    cc = 0
    while evo_cycle_running:
        cc += 1
        for emote_id in evo_ids_list:
            if not evo_cycle_running: break
            for uid_str in uids:
                try:
                    H = await Emote_k(int(uid_str), int(emote_id), key, iv, region)
                    await SEndPacKeT(whisper_writer, online_writer, 'OnLine', H)
                except Exception: pass
            if evo_cycle_running:
                for i in range(5):
                    if not evo_cycle_running: break
                    await asyncio.sleep(1)
        if evo_cycle_running: await asyncio.sleep(2)

# (fast_emote_spam & custom_emote_spam defined above)

async def reject_spam_loop(target_uid, key, iv):
    global reject_spam_running
    count = 0
    while reject_spam_running and count < 150:
        try:
            p1 = await banecipher1(target_uid, key, iv)
            p2 = await banecipher(target_uid, key, iv)
            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', p1)
            await asyncio.sleep(0.1)
            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', p2)
            count += 1
            await asyncio.sleep(0.2)
        except Exception: break
    return count

async def msg_spam_loop(message_text, times, chat_id, key, iv, region):
    global msg_spam_running
    count = 0
    while msg_spam_running and count < times:
        try:
            colorful = await get_colorful_message(message_text, count + 1)
            msg_packet = await xSEndMsgsQQ(colorful, int(chat_id), key, iv)
            if msg_packet and whisper_writer:
                await SEndPacKeT(whisper_writer, online_writer, 'ChaT', msg_packet)
                count += 1
                await asyncio.sleep(0.1)
        except Exception: break
    return count

async def send_wave_messages(message_text, repeats, chat_id, key, iv, region):
    global msg_spam_running
    count = 0
    total_cycles = 0
    while msg_spam_running and total_cycles < repeats:
        try:
            for i in range(1, len(message_text) + 1):
                if not msg_spam_running: break
                partial = message_text[:i]
                colorful = await get_colorful_message(partial, i)
                msg_packet = await xSEndMsgsQ(colorful, int(chat_id), key, iv)
                if msg_packet and whisper_writer:
                    await SEndPacKeT(whisper_writer, online_writer, 'ChaT', msg_packet)
                    count += 1
                    await asyncio.sleep(0.1)
            for i in range(len(message_text) - 1, 0, -1):
                if not msg_spam_running: break
                partial = message_text[:i]
                colorful = await get_colorful_message(partial, i)
                msg_packet = await xSEndMsgsQQ(colorful, int(chat_id), key, iv)
                if msg_packet and whisper_writer:
                    await SEndPacKeT(whisper_writer, online_writer, 'ChaT', msg_packet)
                    count += 1
                    await asyncio.sleep(0.1)
            total_cycles += 1
        except Exception: break
    return count, total_cycles

async def freeze_emote_spam(uid, key, iv, region, chat_type, chat_id, sender_uid):
    global freeze_running
    FREEZE_EMOTES = [909052010, 909052010, 909052010]
    cycles = 0
    while freeze_running and cycles < 10:
        for emote_id in FREEZE_EMOTES:
            if not freeze_running: break
            try:
                emote_packet = await Emote_k(int(uid), emote_id, key, iv, region)
                await SEndPacKeT(whisper_writer, online_writer, 'OnLine', emote_packet)
                await asyncio.sleep(0.1)
            except Exception: pass
        cycles += 1
        await asyncio.sleep(1)
    return cycles


# ═══════════════════════════════════════════════════════════════
# API CALLS (SMT INFO API FIXED)
# ═══════════════════════════════════════════════════════════════
async def send_friend_request(target_uid, token, region):
    try:
        encrypted_id = Encrypt_ID(target_uid)
        payload = f"08a7c4839f1e10{encrypted_id}1801"
        kb = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
        ib = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])
        cipher = AES.new(kb, AES.MODE_CBC, ib)
        ep = cipher.encrypt(pad(bytes.fromhex(payload), AES.block_size)).hex()
        url = "https://clientbp.ggpolarbear.com/RequestAddingFriend"
        headers = {"Authorization": f"Bearer {token}", "X-Unity-Version": "2018.4.11f1", "X-GA": "v1 1", "ReleaseVersion": "OB55", "Content-Type": "application/x-www-form-urlencoded", "User-Agent": "Dalvik/2.1.0 (Linux; Android 9)"}
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=bytes.fromhex(ep), ssl=False) as r:
                return (True, "✅ Friend request sent") if r.status == 200 else (False, f"❌ Status: {r.status}")
    except Exception as e:
        return False, f"❌ Error: {str(e)}"

async def remove_friend(target_uid, token, region):
    try:
        import RemoveFriend_Req_pb2
        msg = RemoveFriend_Req_pb2.RemoveFriend()
        msg.AuthorUid = int(BOT_OWNER_UID); msg.TargetUid = int(target_uid)
        kb = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
        ib = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])
        cipher = AES.new(kb, AES.MODE_CBC, ib)
        eb = cipher.encrypt(pad(msg.SerializeToString(), AES.block_size))
        url = "https://clientbp.ggpolarbear.com/RemoveFriend"
        headers = {'Authorization': f"Bearer {token}", 'User-Agent': "Dalvik/2.1.0 (Linux; Android 9)", 'Content-Type': "application/x-www-form-urlencoded", 'X-Unity-Version': "2018.4.11f1", 'X-GA': "v1 1", 'ReleaseVersion': "OB55"}
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=eb, headers=headers, ssl=False) as r:
                return (True, "✅ Friend removed") if r.status == 200 else (False, f"❌ Status: {r.status}")
    except Exception as e:
        return False, f"❌ Error: {str(e)}"

async def check_banned(player_id):
    try:
        url = f"https://ff.garena.com/api/antihack/check_banned?lang=en&uid={player_id}"
        headers = {"User-Agent": "Mozilla/5.0 (Linux; Android 10)", "Accept": "application/json", "referer": "https://ff.garena.com/en/support/", "x-requested-with": "B6FksShzIgjfrYImLpTsadjS86sddhFH"}
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, ssl=False) as r:
                if r.status == 200: return True, await r.json()
                return False, f"Failed: {r.status}"
    except Exception as e: return False, f"Error: {str(e)}"

def get_player_info(uid):
    try:
        url = f"https://buddy-real-info.vercel.app/info?uid={uid}&region=BD"
        res = requests.get(url, timeout=30)
        print("API RAW RESPONSE:", res.text)
        data = res.json()
        return data
    except Exception as e:
        print(f"Error: {e}")
        return {}

def make_circle_num(number):
    """Return a circled Unicode number for player-info list entries."""
    number = int(number)
    if 1 <= number <= 20:
        return chr(0x245F + number)
    if 21 <= number <= 35:
        return chr(0x3251 + number - 21)
    if 36 <= number <= 50:
        return chr(0x32B1 + number - 36)
    return f"({number})"


def _player_info_lines(value, prefix=""):
    """Flatten the new info API response without dropping nested keys."""
    if isinstance(value, dict):
        lines = []
        for key, item in value.items():
            child_prefix = f"{prefix}.{key}" if prefix else str(key)
            lines.extend(_player_info_lines(item, child_prefix))
        return lines or [(prefix, "{}")]
    if isinstance(value, list):
        if not value:
            return [(prefix, "[]")]
        lines = []
        for index, item in enumerate(value):
            lines.extend(_player_info_lines(item, f"{prefix}[{index}]"))
        return lines
    if value is None or value == "":
        value = "N/A"
    return [(prefix, str(value))]


def build_new_player_info_messages(data, title="PLAYER INFO"):
    """Keep the old info-panel order while reading the new API schema."""
    basic = data.get("basic_info") if isinstance(data.get("basic_info"), dict) else {}
    captain = data.get("captain_basic_info") if isinstance(data.get("captain_basic_info"), dict) else {}
    clan = data.get("clan_basic_info") if isinstance(data.get("clan_basic_info"), dict) else {}
    credit = data.get("credit_score_info") if isinstance(data.get("credit_score_info"), dict) else {}
    pet = data.get("pet_info") if isinstance(data.get("pet_info"), dict) else {}
    profile = data.get("profile_info") if isinstance(data.get("profile_info"), dict) else {}
    social = data.get("social_info") if isinstance(data.get("social_info"), dict) else {}

    def value(section, key, default="N/A"):
        result = section.get(key, default)
        if result is None or result == "":
            return default
        if isinstance(result, (dict, list)):
            return json.dumps(result, ensure_ascii=False, separators=(",", ":"))
        return result

    def format_date(value_to_format):
        try:
            timestamp = int(value_to_format)
            formatted = datetime.fromtimestamp(timestamp).strftime("%d %b %Y, %I:%M%p")
            return formatted.lstrip("0").replace("AM", "am").replace("PM", "pm")
        except (TypeError, ValueError, OverflowError, OSError):
            return "N/A"

    if title == "LEADER INFO":
        def leader_value(section, key, default="N/A"):
            result = section.get(key, default)
            return default if result is None or result == "" else result

        return [f"""[C][B][00FFCC]✿▰▰▰▰▰▰▰▰▰▰✿
[C][B][FFD700]  LEADER INFO
[C][B][00FFCC]✿▰▰▰▰▰▰▰▰▰▰✿

[C][FFD700]Name        : [00FF00]{leader_value(basic, 'nickname')}
[C][FFD700]UID         : [00FFAA]{xMsGFixinG(basic.get('account_id'))}
[C][FFD700]Level       : [FF00FF]{xMsGFixinG(basic.get('level'))}
[C][FFD700]Region      : [FFFFFF]{leader_value(basic, 'region')}
[C][FFD700]Likes       : [FF4444]{xMsGFixinG(basic.get('liked'))}
[C][FFFFFF]Bio :
[66FF00]{leader_value(social, 'social_highlight')}

[C][00FFFF]Guild Name  : [00FF00]{leader_value(clan, 'clan_name', 'No Guild')}
[C][00FFFF]Guild ID    : [FF00FF]{xMsGFixinG(clan.get('clan_id'))}
[C][00FFFF]Guild Level : [FF4444]{xMsGFixinG(clan.get('clan_level'))}
[C][00FFFF]Guild Owner : [FF69B4]{leader_value(captain, 'nickname')}

[C][B][00FFCC]✿▰▰▰▰▰▰▰▰▰▰✿"""]

    def panel(header, color, rows):
        body_lines = []
        for label, section, key in rows:
            item = value(section, key)
            if key in ("create_at", "last_login_at"):
                item = format_date(item)
            else:
                item = make_circle_num(item)
            body_lines.append(f"[C][{color}]{label:<18}: [FFFFFF]{item}")
        body = "\n".join(body_lines)
        return (
            f"[C][B][{color}]✿▰▰▰▰▰▰▰▰▰▰✿\n"
            f"[C][B][FFFFFF]  {header}\n"
            f"[C][B][{color}]✿▰▰▰▰▰▰▰▰▰▰✿\n"
            f"{body}\n\n[C][B][{color}]✿▰▰▰▰▰▰▰▰▰▰✿"
        )

    messages = [
        panel("ACCOUNT INFO", "FF1493", [
            ("Name", basic, "nickname"),
            ("UID", basic, "account_id"),
            ("Level", basic, "level"),
            ("Likes", basic, "liked"),
            ("Bio", social, "social_highlight"),
        ]),
        panel("ACTIVITY INFO", "BF00FF", [
            ("EXP", basic, "exp"),
            ("Account Type", basic, "account_type"),
            ("Badge Count", basic, "badge_cnt"),
            ("Region", basic, "region"),
            ("Title", basic, "title"),
        ]),
        panel("ACTIVITY INFO", "BF00FF", [
            ("Create Date", basic, "create_at"),
            ("Last Login", basic, "last_login_at"),
            ("Honor Score", credit, "score"),
            ("Credit Status", credit, "status"),
            ("Elite Pass", basic, "has_elite_pass"),
            ("Release Version", basic, "release_version"),
        ]),
        panel("BATTLE ROYALE", "FF3131", [
            ("BR Max Rank", basic, "max_rank"),
            ("BR Rank", basic, "rank"),
            ("BR Points", basic, "ranking_points"),
            ("CS Max Rank", basic, "cs_max_rank"),
            ("CS Rank", basic, "cs_rank"),
            ("CS Points", basic, "cs_ranking_points"),
            ("CS Rank Display", basic, "show_cs_rank"),
            ("BR Rank Display", basic, "show_br_rank"),
        ]),
        panel("GUILD DETAILS", "39FF14", [
            ("Guild Name", clan, "clan_name"),
            ("Guild ID", clan, "clan_id"),
            ("Guild Level", clan, "clan_level"),
            ("Members", clan, "current_members"),
            ("Max Members", clan, "max_members"),
            ("Captain UID", clan, "captain_id"),
        ]),
        panel("GUILD LEADER", "FFD700", [
            ("Leader Name", captain, "nickname"),
            ("Leader UID", captain, "account_id"),
            ("Leader Level", captain, "level"),
            ("Leader Region", captain, "region"),
        ]),
        panel("GUILD LEADER", "FFD700", [
            ("Leader Title", captain, "title"),
            ("Leader BR Rank", captain, "rank"),
            ("Leader BR Points", captain, "ranking_points"),
            ("Leader Created", captain, "create_at"),
            ("Leader Last Login", captain, "last_login_at"),
        ]),
        panel("PET DETAILS", "FF00FF", [
            ("Equipped", pet, "is_selected"),
            ("Pet Name", pet, "pet_name"),
            ("Pet Level", pet, "level"),
            ("Pet EXP", pet, "exp"),
            ("Pet Type ID", pet, "pet_id"),
            ("Pet Skin ID", pet, "skin_id"),
            ("Pet Skill ID", pet, "selected_skill_id"),
        ]),
    ]

    # Keep every remaining new-API section available after the original panels.
    shown_sections = {
        "basic_info", "clan_basic_info", "credit_score_info",
        "pet_info", "profile_info", "social_info",
    }
    extra_lines = []
    for section, section_value in data.items():
        if section not in shown_sections:
            extra_lines.extend(_player_info_lines(section_value, section))
    for section, section_value in (("profile_info", profile), ("social_info", social)):
        extra_lines.extend(_player_info_lines(section_value, section))
    for start in range(0, len(extra_lines), 18):
        chunk = extra_lines[start:start + 18]
        body = "\n".join(
            f"[C][00FFFF]{key:<34}: [FFFFFF]{make_circled_num(item)}"
            for key, item in chunk
        )
        messages.append(
            f"[C][B][00FFFF✿▰▰▰▰▰▰▰▰▰▰✿\n"
            f"[C][B][FFFFFF]  ADDITIONAL INFO\n"
            f"[C][B][00FFFF]✿▰▰▰▰▰▰▰▰▰▰✿\n\n{body}\n"
            f"[C][B][00FFFF]✿▰▰▰▰▰▰▰▰▰▰✿"
        )
    return messages


def human_time(unix_timestamp):
    try:
        return datetime.fromtimestamp(int(unix_timestamp)).strftime("%d-%m-%Y %H:%M:%S")
    except:
        return "N/A"


async def send_full_player_info(data, chat_type, uid, chat_id, key, iv):

    # API à¦¥à§‡à¦•à§‡ à¦¡à¦¾à¦Ÿà¦¾ à¦«à§‡à¦š à¦•à¦°à¦¾à¦° à¦œà¦¨à§à¦¯ à¦¸à¦ à¦¿à¦• Key à¦®à§à¦¯à¦¾à¦ªà¦¿à¦‚ (à¦¨à¦¤à§à¦¨ à¦¸à§à¦Ÿà§à¦°à¦¾à¦•à¦šà¦¾à¦° à¦…à¦¨à§à¦¯à¦¾à¦¯à¦¼à§€)
    basic_info = data.get("basic_info", {})
    clan_basic_info = data.get("clan_basic_info", {})
    social_info = data.get("social_info", {})
    profile_info = data.get("profile_info", {})
    captain_basic_info = data.get("captain_basic_info", {})
    credit_score_info = data.get("credit_score_info", {})
    pet_info = data.get("pet_info", {})
    
    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ LANGUAGE HANDLING â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    lang = social_info.get("language", "N/A")
    if lang != "N/A" and isinstance(lang, int):
        # à¦­à¦¾à¦·à¦¾ à¦•à§‹à¦¡ à¦¨à¦¾à¦®à§à¦¬à¦¾à¦°à§‡ à¦†à¦›à§‡, à¦à¦Ÿà¦¾à¦•à§‡ à¦¸à§à¦Ÿà§à¦°à¦¿à¦‚ à¦ à¦•à¦¨à¦­à¦¾à¦°à§à¦Ÿ à¦•à¦°à¦¤à§‡ à¦¹à¦¬à§‡
        lang_map = {
            17: "EN",
            # à¦…à¦¨à§à¦¯à¦¾à¦¨à§à¦¯ à¦­à¦¾à¦·à¦¾ à¦•à§‹à¦¡ à¦à¦–à¦¾à¦¨à§‡ à¦®à§à¦¯à¦¾à¦ª à¦•à¦°à¦¤à§‡ à¦ªà¦¾à¦°à§‡à¦¨
        }
        lang = lang_map.get(lang, str(lang))
    elif lang != "N/A":
        if "_" in str(lang):
            lang = str(lang).split("_")[-1]

    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ MESSAGE 1 : COMMON ACCOUNT INFO â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    msg1 = f"""
[C][B][FF1493]✿▰▰▰▰▰▰▰▰▰▰✿
[C][B][00FFFF]  ACCOUNT INFO
[C][FF1493]✿▰▰▰▰▰▰▰▰▰▰✿

[C][FFD700]Name        : [00FF00]{basic_info.get('nickname', 'N/A')}
[C][FFD700]UID         : [00FFAA]{xMsGFixinG(basic_info.get('account_id'))}
[C][FFD700]Level       : [FF00FF]{xMsGFixinG(basic_info.get('level'))}
[C][FFD700]EXP         : [00FFFF]{xMsGFixinG(basic_info.get('exp'))}
[C][FFD700]Region      : [FFFFFF]{basic_info.get('region', 'N/A')}
[C][FFD700]Likes       : [FF4444]{xMsGFixinG(basic_info.get('liked'))}
[C][FFD700]Honor       : [FFA500]{xMsGFixinG(credit_score_info.get('score'))}
[C][FFD700]BP Badge    : [FFA500]{xMsGFixinG(basic_info.get('badge_cnt'))}
[C][FFD700]Version     : [AAAAFF]{basic_info.get('release_version', 'N/A')}
[C][FFD700]Language    : [66FF00]{lang}
[C][FFD700]Bio         : 
[66FF00]{social_info.get('social_highlight', 'N/A')}

[C][FF1493]✿▰▰▰▰▰▰▰▰▰▰✿
"""
    await safe_send_message(chat_type, msg1, uid, chat_id, key, iv)
    await asyncio.sleep(0.5)

    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ MESSAGE 2 : ACCOUNT DETAILS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    msg2 = f"""
[C][B][00AAFF]✿▰▰▰▰▰▰▰▰▰▰✿
[C][B][FFFFFF]  ACCOUNT DETAILS
[C][00AAFF]✿▰▰▰▰▰▰▰▰▰▰✿

[C][FFAA00]Create Date : [00FF00]{xMsGFixinG(human_time(basic_info.get('create_at', '0'))[:16])}
[C][FFAA00]Last Login  : [00FF00]{xMsGFixinG(human_time(basic_info.get('last_login_at', '0'))[:16])}
[C][FF00FF]BR Max Rank : [FFD700]{xMsGFixinG(basic_info.get('max_rank'))}
[C][FF00FF]BR Points   : [FFD700]{xMsGFixinG(basic_info.get('ranking_points'))}
[C][00FFFF]CS Max Rank : [AA00FF]{xMsGFixinG(basic_info.get('cs_max_rank'))}
[C][FF00FF]CS Points   : [FFD700]{xMsGFixinG(basic_info.get('cs_ranking_points'))}
[C][FF00FF]Hippo Rank  : [FFD700]{xMsGFixinG(basic_info.get('hippo_rank'))}
[C][FF00FF]Hippo Points: [FFD700]{xMsGFixinG(basic_info.get('hippo_ranking_points'))}

[C][00AAFF]✿▰▰▰▰▰▰▰▰▰▰✿
"""
    await safe_send_message(chat_type, msg2, uid, chat_id, key, iv)
    await asyncio.sleep(0.5)

    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ MESSAGE 3 : EQUIPPED DETAILS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    msg5 = f"""
[C][B][00AAFF]✿▰▰▰▰▰▰▰▰▰▰✿
[C][B][FFFFFF]  EQUIPPED DETAILS
[C][00AAFF]✿▰▰▰▰▰▰▰▰
[C][FFD700]Avatar      : [ff0000]{xMsGFixinG(profile_info.get('avatar_id'))}
[C][FFD700]Banner      : [87ceeb]{xMsGFixinG(basic_info.get('banner_id'))}
[C][FFD700]Title       : [800080]{xMsGFixinG(basic_info.get('title'))}
[C][FFD700]Badge       : [FFA500]{xMsGFixinG(basic_info.get('badge_id'))}
[C][FFD700]Head Pic    : [FF69B4]{xMsGFixinG(basic_info.get('head_pic'))}

[C][00AAFF]✿▰▰▰▰▰▰▰▰▰▰✿
"""
    await safe_send_message(chat_type, msg5, uid, chat_id, key, iv)
    await asyncio.sleep(0.5)

    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ MESSAGE 4 : SKILLS DETAILS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    equipped_skills = profile_info.get('equipped_skills', [])
    skill_slots = profile_info.get('skill_slots', [])
    
    skills_text = "N/A"
    if skill_slots:
        skill_list = [str(slot.get('skill_id', 'N/A')) for slot in skill_slots if slot.get('skill_id')]
        skills_text = ", ".join(skill_list) if skill_list else "N/A"
    elif equipped_skills:
        skills_text = ", ".join([str(s) for s in equipped_skills[:5]])

    msg_skills = f"""
[C][B][00AAFF]✿▰▰▰▰▰▰▰▰▰▰✿
[C][B][FFFFFF]  SKILL DETAILS
[C][00AAFF]✿▰▰▰▰▰▰▰▰▰▰✿

[C][FFD700]Equipped Skills: [00FF00]{skills_text}
[C][FFD700]PVE Primary   : [87ceeb]{xMsGFixinG(profile_info.get('pve_primary_weapon'))}
[C][FFD700]Cosmetic Items: [FF69B4]{xMsGFixinG(profile_info.get('cosmetic_items', []))}

[C][00AAFF]✿▰▰▰▰▰▰▰▰▰▰✿
"""
    await asyncio.sleep(0.5)

    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ MESSAGE 5 : PET DETAILS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    msg4 = f"""
[C][B][00AAFF]✿▰▰▰▰▰▰▰▰▰▰✿
[C][B][FFFFFF]  PET DETAILS
[C][00AAFF]✿▰▰▰▰▰▰▰▰▰▰✿

[C][FFAA00]Equipped?   : [00FF00]{pet_info.get('is_selected', False)}
[C][FFAA00]Pet Name    : [00FF00]{pet_info.get('pet_name', 'N/A')}
[C][FF00FF]Pet Level   : [FFD700]{xMsGFixinG(pet_info.get('level'))}
[C][FF00FF]Pet Exp     : [FFD700]{xMsGFixinG(pet_info.get('exp'))}
[C][FF00FF]Pet ID      : [FFD700]{xMsGFixinG(pet_info.get('pet_id'))}
[C][FF00FF]Skin ID     : [FFD700]{xMsGFixinG(pet_info.get('skin_id'))}

[C][00AAFF]✿▰▰▰▰▰▰▰▰▰▰✿
"""
    await safe_send_message(chat_type, msg4, uid, chat_id, key, iv)
    await asyncio.sleep(0.5)

    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ MESSAGE 6 : GUILD DETAILS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    msg3 = f"""
[C][B][FF8800]✿▰▰▰▰▰▰▰▰▰▰✿
[C][B][FFFFFF]  GUILD DETAILS
[C][FF8800]✿▰▰▰▰▰▰▰▰▰▰✿

[C][00FFFF]Guild Name    : [00FF00]{clan_basic_info.get('clan_name', 'No Guild')}
[C][00FFFF]Guild ID      : [FF00FF]{xMsGFixinG(clan_basic_info.get('clan_id'))}
[C][00FFFF]Owner Name    : [FF69B4]{captain_basic_info.get('nickname', 'N/A')}
[C][00FFFF]Owner UID     : [FFD700]{xMsGFixinG(clan_basic_info.get('captain_id'))}
[C][00FFFF]Guild Level   : [FF4444]{xMsGFixinG(clan_basic_info.get('clan_level'))}
[C][00FFFF]Members       : [66FFAA]{xMsGFixinG(clan_basic_info.get('current_members'))}/{xMsGFixinG(clan_basic_info.get('max_members'))}

[C][FF8800]✿▰▰▰▰▰▰▰▰▰▰✿
"""
    await safe_send_message(chat_type, msg3, uid, chat_id, key, iv)
    await asyncio.sleep(0.5)

    # â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ MESSAGE 7 : CREDIT SCORE INFO â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    msg_credit = f"""
[C][B][FF8800]✿▰▰▰▰▰▰▰▰▰▰✿
[C][B][FFFFFF]  CREDIT SCORE INFO
[C][FF8800]✿▰▰▰▰▰▰▰▰▰▰✿

[C][00FFFF]Credit Score : [00FF00]{xMsGFixinG(credit_score_info.get('score'))}
[C][00FFFF]Status       : [FF69B4]{xMsGFixinG(credit_score_info.get('status'))}
[C][00FFFF]Reason       : [FFD700]{xMsGFixinG(credit_score_info.get('reason'))}
[C][00FFFF]Start Time   : [87ceeb]{xMsGFixinG(human_time(credit_score_info.get('start', '0'))[:16])}
[C][00FFFF]End Time     : [FF4444]{xMsGFixinG(human_time(credit_score_info.get('end', '0'))[:16])}

[C][FF8800]✿▰▰▰▰▰▰▰▰▰▰✿
"""
    await safe_send_message(chat_type, msg_credit, uid, chat_id, key, iv)

async def format_player_info(data, chat_type, uid, chat_id, key, iv):
    if isinstance(data, dict) and "basic_info" in data:
        for message in build_new_player_info_messages(data, "PLAYER INFO"):
            sent = await safe_send_message(chat_type, message, uid, chat_id, key, iv)
            if not sent:
                print("Player info panel delivery failed; stopping remaining panels.")
                return
            await asyncio.sleep(0.5)
        return

    if not isinstance(data, dict) or "basic_info" not in data:
        error_message = (
            data.get("message", "Invalid API response")
            if isinstance(data, dict)
            else "Invalid API response"
        )
        await safe_send_message(
            chat_type,
            f"[B][C][FF0000]❌ {error_message}",
            uid, chat_id, key, iv,
        )
        return

    basic = data.get("basic_info")
    activity = data.get("basic_info")
    guild = data.get("clan_basic_info")
    leader = data.get("captain_basic_info")
    pet = data.get("pet_info")
    basic = basic if isinstance(basic, dict) else {}
    activity = activity if isinstance(activity, dict) else {}
    guild = guild if isinstance(guild, dict) else {}
    leader = leader if isinstance(leader, dict) else {}
    pet = pet if isinstance(pet, dict) else {}

    def value(section, name, default="N/A"):
        result = section.get(name, default)
        return default if result is None or result == "" else result

    messages = [
    f"""
[C][B][FF1493]✿▰▰▰▰▰▰▰▰▰▰✿
[C][B][00FFFF]  ACCOUNT INFO
[C][B][FF1493]✿▰▰▰▰▰▰▰▰▰▰✿

[C][FF1493]Name            : [00FFFF]{xMsGFixinG(value(basic, 'Name'))}
[C][FF1493]UID             : [00FFFF]{xMsGFixinG(value(basic, 'UID'))}
[C][FF1493]Level           : [00FFFF]{xMsGFixinG(value(basic, 'Level'))}
[C][FF1493]Likes           : [00FFFF]{xMsGFixinG(value(basic, 'Likes'))}
[C][FF1493]Prime Level     : [00FFFF]{xMsGFixinG(value(basic, 'PrimeLevel'))}
[C][FF1493]Celebrity       : [00FFFF]{xMsGFixinG(value(basic, 'CelebrityStatus'))}

[C][FF1493]Bio             :
[00FFFF]{(value(basic, 'Signature'))}

[C][FF1493]✿▰▰▰▰▰▰▰▰▰▰✿
""",

    f"""
[C][B][BF00FF]✿▰▰▰▰▰▰▰▰▰▰✿
[C][B][FFFFFF]  ACTIVITY INFO
[C][BF00FF]✿▰▰▰▰▰▰▰▰▰▰✿

[C][BF00FF]EXP             : [00FFFF]{xMsGFixinG(value(basic, 'Exp'))}
[C][BF00FF]Region          : [00FFFF]{xMsGFixinG(value(basic, 'Region'))}
[C][BF00FF]Title           : [00FFFF]{xMsGFixinG(value(basic, 'Title'))}
[C][BF00FF]Create Date     : [00BFFF]{xMsGFixinG(value(activity, 'CreatedAt'))}
[C][BF00FF]Last Login      : [00BFFF]{xMsGFixinG(value(activity, 'LastLogin'))}
[C][BF00FF]Honor Score     : [00BFFF]{xMsGFixinG(value(basic, 'HonorScore'))}
[C][BF00FF]BP Badges       : [00BFFF]{xMsGFixinG(value(activity, 'CurrentBpBadges'))}
[C][BF00FF]Booyah Pass     : [00BFFF]{xMsGFixinG(value(activity, 'BooyahPass'))}
[C][BF00FF]Latest OBB      : [00BFFF]{xMsGFixinG(value(activity, 'MostRecentOB'))}
[C][BF00FF]Ban Status      : [00BFFF]{xMsGFixinG(value(data, 'BanStatus'))}

[C][BF00FF]✿▰▰▰▰▰▰▰▰▰▰✿
""",

    f"""
[C][B][FF3131]✿▰▰▰▰▰▰▰▰▰▰✿
[C][B][FFFFFF]  BATTLE ROYALE
[C][FF3131]✿▰▰▰▰▰▰▰▰▰▰✿

[C][FF3131]BR Max Rank     : [FFFFFF]{xMsGFixinG(value(activity, 'BRRank'))}
[C][FF3131]BR Points       : [FFFFFF]{xMsGFixinG(value(activity, 'BRPoints'))}
[C][FF3131]CS Rank Display : [FFFFFF]{xMsGFixinG(value(activity, 'ShowCSRank'))}
[C][FF3131]BR Rank Display : [FFFFFF]{xMsGFixinG(value(activity, 'ShowBRRank'))}

[C][FF3131]✿▰▰▰▰▰▰▰▰▰▰✿
""",

    f"""
[C][B][39FF14]✿▰▰▰▰▰▰▰▰▰▰✿
[C][B][FFFFFF]  GUILD DETAILS
[C][39FF14]✿▰▰▰▰▰▰▰▰▰▰✿

[C][39FF14]Guild Name      : [FFFFFF]{xMsGFixinG(value(guild, 'GuildName', 'No Guild'))}
[C][39FF14]Guild ID        : [FFFFFF]{xMsGFixinG(value(guild, 'GuildID'))}
[C][39FF14]Guild Level     : [FFFFFF]{xMsGFixinG(value(guild, 'GuildLevel'))}
[C][39FF14]Members         : [FFFFFF]{xMsGFixinG(value(guild, 'LiveMembers'))}
[C][39FF14]Max Members     : [FFFFFF]{xMsGFixinG(value(guild, 'MaxMembers'))}

[C][39FF14]✿▰▰▰▰▰▰▰▰▰▰✿
""",

    f"""
[C][B][FFD700]✿▰▰▰▰▰▰▰▰▰▰✿
[C][B][FFFFFF]  GUILD LEADER
[C][FFD700]✿▰▰▰▰▰▰▰▰▰▰✿

[C][FFD700]Leader Name     : [FF8C00]{xMsGFixinG(value(leader, 'Name'))}
[C][FFD700]Leader UID      : [FF8C00]{xMsGFixinG(value(leader, 'UID'))}
[C][FFD700]Leader Level    : [FF8C00]{xMsGFixinG(value(leader, 'Level'))}
[C][FFD700]Leader Region   : [FF8C00]{xMsGFixinG(value(leader, 'Region'))}
[C][FFD700]Leader Title    : [FF8C00]{xMsGFixinG(value(leader, 'Title'))}

[C][FFD700]Leader BR Rank  : [FF8C00]{xMsGFixinG(value(leader, 'BRRank'))}
[C][FFD700]Leader BR Points: [FF8C00]{xMsGFixinG(value(leader, 'BRPoints'))}

[C][FFD700]Leader BP       : [FF8C00]{xMsGFixinG(value(leader, 'BooyahPass'))}
[C][FFD700]Leader BP Badges: [FF8C00]{xMsGFixinG(value(leader, 'BpBadges'))}

[C][FFD700]Leader Created  : [FF8C00]{xMsGFixinG(value(leader, 'CreatedAt'))}
[C][FFD700]Leader Last Login: [FF8C00]{xMsGFixinG(value(leader, 'LastLogin'))}

[C][FFD700]✿▰▰▰▰▰▰▰▰▰▰✿
""",

    f"""
[C][B][FF00FF]✿▰▰▰▰▰▰▰▰▰▰✿
[C][B][FFFFFF]  PET DETAILS
[C][FF00FF]✿▰▰▰▰▰▰▰▰▰▰✿

[C][FF00FF]Equipped        : [FFFFFF]{xMsGFixinG(value(pet, 'Equipped'))}
[C][FF00FF]Pet Name        : [FFFFFF]{xMsGFixinG(value(pet, 'PetNick'))}
[C][FF00FF]Pet Level       : [FFFFFF]{xMsGFixinG(value(pet, 'PetLevel'))}
[C][FF00FF]Pet EXP         : [FFFFFF]{xMsGFixinG(value(pet, 'PetExp'))}
[C][FF00FF]Pet Type ID     : [FFFFFF]{xMsGFixinG(value(pet, 'PetType'))}
[C][FF00FF]Pet Skin ID     : [FFFFFF]{xMsGFixinG(value(pet, 'PetSkin'))}
[C][FF00FF]Pet Skill ID    : [FFFFFF]{xMsGFixinG(value(pet, 'PetSkill'))}

[C][FF00FF]✿▰▰▰▰▰▰▰▰▰▰✿
"""
    ]

    for message in messages:
        sent = await safe_send_message(chat_type, message, uid, chat_id, key, iv)
        if not sent:
            print("❌ Player info panel delivery failed; stopping remaining panels.")
            return
        await asyncio.sleep(0.5)


def format_check_result(data):
    try: return f"[b][c]{get_random_color()} 🔍 BAN CHECK\n[b][c][FFFFFF]Type: {data.get('ban_type', 'Unknown')}\n[b][c][FFFFFF]Duration: {data.get('ban_duration', 'Unknown')}"
    except Exception as e: return f"[b][c]Error: {str(e)}"

# ═══════════════════════════════════════════════════════════════
# STATUS, CACHE & PROTOBUF HELPERS (FROM MAIN.PY)
# ═══════════════════════════════════════════════════════════════
CACHE_FILE = 'status_cache.pkl'
CACHE_TIMEOUT = 30  # seconds

def save_to_cache(player_id, data):
    """Save status to file cache with timestamp"""
    try:
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, 'rb') as f:
                    cache = pickle.load(f)
            except Exception:
                cache = {}
        else:
            cache = {}
        data['saved_at'] = time.time()
        cache[str(player_id)] = data
        with open(CACHE_FILE, 'wb') as f:
            pickle.dump(cache, f)
        print(f"💾 Saved to file cache: {player_id}")
        return True
    except Exception as e:
        print(f"❌ Cache save error: {e}")
        return False

def load_from_cache(player_id):
    """Load status from file cache, check expiration"""
    try:
        if not os.path.exists(CACHE_FILE):
            return None
        with open(CACHE_FILE, 'rb') as f:
            cache = pickle.load(f)
        player_key = str(player_id)
        if player_key in cache:
            data = cache[player_key]
            if 'saved_at' in data:
                if time.time() - data['saved_at'] > CACHE_TIMEOUT:
                    print(f"⏰ Cache expired for {player_id}")
                    del cache[player_key]
                    with open(CACHE_FILE, 'wb') as f:
                        pickle.dump(cache, f)
                    return None
            print(f"📥 Loaded from cache: {player_id}")
            return data
        return None
    except Exception as e:
        print(f"❌ Cache load error: {e}")
        return None

def clear_cache_entry(player_id):
    """Clear specific cache entry"""
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'rb') as f:
                cache = pickle.load(f)
            player_key = str(player_id)
            if player_key in cache:
                del cache[player_key]
            with open(CACHE_FILE, 'wb') as f:
                pickle.dump(cache, f)
            print(f"🗑️ Cleared cache for {player_id}")
    except Exception as e:
        print(f"❌ Clear cache error: {e}")

def debug_file_cache():
    """Debug the file cache"""
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'rb') as f:
                cache = pickle.load(f)
            print(f"\n📁 FILE CACHE DEBUG: {len(cache)} entries")
            for uid_k, data in cache.items():
                age = time.time() - data.get('saved_at', 0)
                status = data.get('status', 'NO STATUS')
                print(f"  {uid_k}: {status} (age: {age:.1f}s)")
            return cache
        return {}
    except Exception as e:
        print(f"❌ Cache debug error: {e}")
        return {}

def Encrypt(number):
    """Varint byte encoder for Free Fire proto"""
    number = int(number)
    encoded_bytes = []
    while True:
      byte = number & 0x7F
      number >>= 7
      if number:
        byte |= 0x80
      encoded_bytes.append(byte)
      if not number:
        break
    return bytes(encoded_bytes).hex()

async def createpacketinfo(idddd, key, iv):
    """Create player status request packet"""
    try:
        ida = Encrypt(idddd)
        packet = f"080112090A05{ida}1005"
        enc = await encrypt_packet(packet, key, iv)
        header_length = len(enc) // 2
        header_length_hex = hex(header_length).replace("0x", "").upper()
        if len(header_length_hex) == 2:
            final_packet = "0F15000000" + header_length_hex + enc
        elif len(header_length_hex) == 3:
            final_packet = "0F1500000" + header_length_hex + enc
        elif len(header_length_hex) == 4:
            final_packet = "0F150000" + header_length_hex + enc
        elif len(header_length_hex) == 5:
            final_packet = "0F15000" + header_length_hex + enc
        else:
            final_packet = "0F1500000" + header_length_hex + enc
        return bytes.fromhex(final_packet)
    except Exception as e:
        print(f"Error creating packet info: {e}")
        return None

def fix_num(number):
    """Format numbers with breaks"""
    fixed = ""
    count = 0
    num_str = str(number)
    for char in num_str:
        if char.isdigit():
            count += 1
        fixed += char
        if count == 3:
            fixed += "[c]"
            count = 0
    return fixed

def parse_results(parsed_results):
    result_dict = {}
    for result in parsed_results:
        field_data = {}
        field_data["wire_type"] = result.wire_type
        if result.wire_type == "varint":
            field_data["data"] = result.data
        if result.wire_type == "string":
            field_data["data"] = result.data
        if result.wire_type == "bytes":
            field_data["data"] = result.data
        elif result.wire_type == "length_delimited":
            field_data["data"] = parse_results(result.data.results)
        result_dict[result.field] = field_data
    return result_dict

def get_available_room(input_text):
    try:
        from protobuf_decoder.protobuf_decoder import Parser
        parsed_results = Parser().parse(input_text)
        parsed_results_dict = parse_results(parsed_results)
        return json.dumps(parsed_results_dict)
    except Exception as e:
        print(f"get_available_room error: {e}")
        return None

def get_player_status(packet):
    json_result = get_available_room(packet)
    if not json_result:
        return "OFFLINE"
    try:
        parsed_data = json.loads(json_result)
        if "5" not in parsed_data or "data" not in parsed_data["5"]:
            return "OFFLINE"
        json_data = parsed_data["5"]["data"]
        if "1" not in json_data or "data" not in json_data["1"]:
            return "OFFLINE"
        data = json_data["1"]["data"]
        if "3" not in data or "data" not in data["3"]:
            return "OFFLINE"
        status = data["3"]["data"]
        if status == 1:
            return "SOLO"
        if status == 2:
            if "9" in data and "data" in data["9"]:
                group_count = data["9"]["data"]
                countmax = data.get("10", {}).get("data", 3) + 1
                return f"INSQUAD ({group_count}/{countmax})"
            return "INSQUAD"
        if status in [3, 5]:
            return "INGAME"
        if status == 4:
            return "IN ROOM"
        if status in [6, 7]:
            return "IN SOCIAL ISLAND MODE"
        return "NOTFOUND"
    except Exception:
        return "OFFLINE"

def get_idroom_by_idplayer(packet):
    try:
        json_result = get_available_room(packet)
        parsed_data = json.loads(json_result)
        if "5" in parsed_data and "data" in parsed_data["5"]:
            json_data = parsed_data["5"]["data"]
            if "1" in json_data and "data" in json_data["1"]:
                data = json_data["1"]["data"]
                if "6" in data and "data" in data["6"]:
                    return data["6"]["data"]
        return None
    except Exception:
        return None

def get_leader(packet):
    try:
        json_result = get_available_room(packet)
        parsed_data = json.loads(json_result)
        if "5" in parsed_data and "data" in parsed_data["5"]:
            json_data = parsed_data["5"]["data"]
            if "1" in json_data and "data" in json_data["1"]:
                data = json_data["1"]["data"]
                if "8" in data and "data" in data["8"]:
                    return data["8"]["data"]
        return None
    except Exception:
        return None

# ═══════════════════════════════════════════════════════════════
# SOCIAL MEDIA & UTILITY HELPERS (FROM MAIN.PY)
# ═══════════════════════════════════════════════════════════════
def normalize_bio(text):
    if not text:
        return "No Bio"

    # Fancy Unicode -> Normal
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))

    # Keep printable ASCII + newline
    text = "".join(
        c for c in text
        if c == "\n" or (32 <= ord(c) <= 126)
    )

    text = text.replace("\r", "")
    text = text.replace("\n\n", "\n")
    text = text.strip()

    # Limit length
    if len(text) > 120:
        text = text[:120] + "..."

    return text if text else "No Bio"


def get_dynamic_duo_info(uid):
    try:
        response = requests.get(
            "https://buddy-dynamic-duo.vercel.app/api/duo",
            params={"uid": uid},
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, (dict, list)):
            return {"error": "Unexpected response from Duo API"}
        return data
    except requests.RequestException as e:
        print(f"Duo API request error: {e}")
        return {"error": f"Could not reach Duo API: {e}"}
    except ValueError as e:
        print(f"Duo API returned invalid JSON: {e}")
        return {"error": "Duo API returned invalid JSON"}

async def send_dynamic_duo_info(data, chat_type, uid, chat_id, key, iv):
    if isinstance(data, dict) and data.get("error"):
        await safe_send_message(
            chat_type,
            f"[B][C][FF0000]❌ Duo lookup failed:\n{data['error']}",
            uid, chat_id, key, iv,
        )
        return

    fields = []

    def collect_fields(value, prefix=""):
        if len(fields) >= 12:
            return
        if isinstance(value, dict):
            for field_name, field_value in value.items():
                if str(field_name).lower() == "error":
                    continue
                label = f"{prefix} {str(field_name).replace('_', ' ').title()}".strip()
                collect_fields(field_value, label)
                if len(fields) >= 12:
                    break
        elif isinstance(value, list):
            if value and all(not isinstance(item, (dict, list)) for item in value):
                fields.append((prefix or "Result", ", ".join(map(str, value))[:160]))
            else:
                for index, item in enumerate(value[:5], start=1):
                    collect_fields(item, f"{prefix} {index}".strip())
                    if len(fields) >= 12:
                        break
        elif value is not None:
            fields.append((prefix or "Result", str(value)[:160]))

    collect_fields(data)
    if not fields:
        result_message = "[B][C][FFFF00]No duo information found for this UID."
    else:
        result_message = "[B][C][FF69B4]💞 DUO INFORMATION\n[FFFFFF]────────────────\n"
        result_message += "\n".join(f"[00FFFF]{label}: [FFFFFF]{value}" for label, value in fields)
    await safe_send_message(chat_type, result_message, uid, chat_id, key, iv)

def send_tiktok_info(username):
    try:
        response = requests.get(
            f"https://mg24-gamer-king.vercel.app/tt-info/tiktok?username={username}",
            timeout=15
        )
        if response.status_code != 200:
            return f"[B][C][FF0000]❌ TikTok API Error! Status Code: {response.status_code}"

        user = response.json()
        if user.get("credit") != "MG24 GAMER":
            return "[B][C][FF0000]❌ User Not Found!"

        identity = user.get("identity", {})
        statistics = user.get("statistics", {})
        status = user.get("status", {})
        timeline = user.get("timeline", {})

        full_name = identity.get("full_name", "Unknown")
        username_ = identity.get("username", "Unknown")
        user_id = str(identity.get("user_id", "Unknown"))
        language = identity.get("language", "Unknown")
        region = identity.get("region") or "Unknown"

        followers = statistics.get("followers", 0)
        following = statistics.get("following", 0)
        friends = statistics.get("friends", 0)
        likes = statistics.get("likes", 0)
        videos = statistics.get("videos", 0)

        private_status = "Yes" if status.get("private_account", False) else "No"
        verified = "Yes" if status.get("verified", False) else "No"
        business = "Yes" if status.get("business_account", False) else "No"
        downloads = "Yes" if status.get("downloads_open", False) else "No"
        live = "Yes" if status.get("live", False) else "No"
        created = timeline.get("create_time", "Unknown")
        bio = normalize_bio(user.get("bio", "No Bio"))

        msg1 = f"""[B][C][FFD700]╭[FFFF00]─[FFFF00]╮[FFFFFF]
[C][B][00BFFF]│[00BFFF]ꚠ[00BFFF] │[FFFFFF]║[00BFFF]TIKTOK INFO[FFFFFF]║
[C][B][FF00FF]╰[FFFF00]─[FFFF00]╯[FFFFFF]
[C][B][00FFFF]━━━━━━━━━━━━━━━━

[C][B][FFFFFF]Name       : [FFFF00]{make_circled_num(full_name)}
[C][B][FFFFFF]Username   : [FFFF00]{make_circled_num(username_)}
[C][B][FFFFFF]Followers  : [00BFFF]{make_circled_num(followers)}
[C][B][FFFFFF]Following  : [00BFFF]{make_circled_num(following)}
[C][B][FFFFFF]Friends    : [00BFFF]{make_circled_num(friends)}
[C][B][FFFFFF]Likes      : [00BFFF]{make_circled_num(likes)}
[C][B][FFFFFF]Videos     : [00BFFF]{make_circled_num(videos)}
[C][B][FFFFFF]Bio        : 
[00BFFF]{make_circled_num(bio)}
""".strip()

        msg2 = f"""[B][C][FFD700]╭[FFFF00]─[FFFF00]╮[FFFFFF]
[C][B][32CD32]│[32CD32]★[32CD32]│[FFFFFF]║[32CD32]TIKTOK STATUS[FFFFFF]║
[C][B][FF00FF]╰[FFFF00]─[FFFF00]╯[FFFFFF]
[C][B][00FFFF]━━━━━━━━━━━━━━━━

[C][B][FFFFFF]User ID    : [00BFFF]{make_circled_num(user_id)}
[C][B][FFFFFF]Private    : [FFFF00]{private_status}
[C][B][FFFFFF]Verified   : [FFFF00]{verified}
[C][B][FFFFFF]Business   : [FFFF00]{business}
[C][B][FFFFFF]Downloads  : [FFFF00]{downloads}
[C][B][FFFFFF]Live       : [FFFF00]{live}

[C][B][FFFFFF]Language   : [00BFFF]{make_circled_num(language)}
[C][B][FFFFFF]Created    : [00BFFF]{make_circled_num(created)}

[C][B][FF2EEE]⊹₊˚‧︵‿₊୨ᰔ୧₊‿︵‧˚₊⊹

[C][B][FF69B4]Dev: —͟͞͞ </> Buddy Meow""".strip()

        return msg1, msg2
    except requests.exceptions.RequestException:
        return "[B][C][FF0000]❌ TikTok API Connection Failed!"
    except Exception as e:
        return f"[B][C][FF0000]❌ Unexpected Error: {str(e)}"

def get_youtube_info(channel_name):
    try:
        response_json = requests.get(
            f"https://mg24-gamer-king.vercel.app/yt-info/yt?channel={channel_name.lstrip('@')}",
            timeout=15
        ).json()
        return response_json
    except Exception:
        return {}

async def send_youtube_info(channel_name, chat_type, uid, chat_id, key, iv):
    response_json = get_youtube_info(channel_name)
    stats = response_json.get("statistics", {})
    subscribers = xMsGFixinG(stats.get("subscribers", "0"))
    views = xMsGFixinG(stats.get("views", "0"))
    videos = xMsGFixinG(stats.get("videos", "0"))
    description = response_json.get("description", "")

    main_info = f"""
[B][C][FF0000]╭[FF0000]─[FF0000]╮[FFFFFF]
[C][B][FF0000]│[FFFFFF]▶[FF0000] │[FFFFFF]║[00BFFF]YOUTUBE INFO[FFFFFF]║
[C][B][FF0000]╰[FF0000]─[FF0000]╯[FFFFFF]
[C][B][FF00FF]━━━━━━━━━━━
[C][B][FFFFFF]Channel Name : [FFFF00]{response_json.get('channel_title', 'Unknown')}
[C][B][FFFFFF]Channel ID    : [FFFF00]{response_json.get('channel_id', 'Unknown')}
[C][B][FFFFFF]Handle        : [00BFFF]{response_json.get('handle', 'Unknown')}
[C][B][FFFFFF]Subscribers   : [00BFFF]{subscribers}
[C][B][FFFFFF]Views         : [00BFFF]{views}
[C][B][FFFFFF]Videos        : [00BFFF]{videos}
[C][B][FFFFFF]Published At  : [00BFFF]{xMsGFixinG(response_json.get('published_at', ''))}
[C][B][FF2EEE]⊹₊˚‧︵‿₊୨ᰔ୧₊‿︵‧˚₊⊹
[C][B][FFFFFF]Dev: —͟͞͞ </> Buddy Meow
"""
    await safe_send_message(chat_type, main_info, uid, chat_id, key, iv)
    await asyncio.sleep(0.2)
    if description:
        await safe_send_message(chat_type, f"[B][C][00BFFF]Description: {description}", uid, chat_id, key, iv)

def send_insta_info(username):
    username = username.strip().lstrip("@").lower()
    if not re.fullmatch(r"[a-z0-9._]{1,30}", username):
        return "[B][C][FF0000]Invalid Instagram username."
    try:
        from APIS import insta
        raw_data = insta.fetch_instagram_profile(username)
    except Exception:
        try:
            res = requests.get(f"https://mg24-gamer-king.vercel.app/ig-info/ig?username={username}", timeout=15)
            raw_data = res.json()
        except Exception:
            return "[B][C][FF0000]Instagram connection failed. Please try again later."
    if not raw_data:
        return "[B][C][FF0000]Instagram did not return a response."
    user = raw_data.get("data", {}).get("user") or raw_data.get("user") or raw_data.get("data") or raw_data
    if not isinstance(user, dict):
        return "[B][C][FF0000]Instagram returned an unexpected response."

    full_name = user.get("full_name") or user.get("name") or user.get("username") or "Unknown"
    followers = user.get("edge_followed_by", {}).get("count") or user.get("followers_count") or user.get("followers") or 0
    following = user.get("edge_follow", {}).get("count") or user.get("following_count") or user.get("following") or 0
    posts = user.get("media_count") or user.get("edge_owner_to_timeline_media", {}).get("count") or user.get("posts") or 0
    private_status = "Yes" if user.get("is_private") else "No"
    verified_status = "Yes" if user.get("is_verified") else "No"

    return f"""
[B][C][FB0364]╭[D21A92]─[BC26AB]╮[FFFF00]╔═══════╗
[C][B][FF7244]│[FE4250]◯[C81F9C]֯│[FFFF00]║[FFFFFF]INSTAGRAM INFO[FFFF00]║
[C][B][FDC92B]╰[FF7640]─[F5066B]╯[FFFF00]╚═══════╝
[C][B][FFFF00]━━━━━━━━━━━━
[C][B][FFFFFF]Name: [66FF00]{full_name}
[C][B][FFFFFF]Username: [66FF00]@{username}
[C][B][FFFFFF]Followers: [66FF00]{followers}
[C][B][FFFFFF]Following: [66FF00]{following}
[C][B][FFFFFF]Posts: [66FF00]{posts}
[C][B][FFFFFF]Private: [66FF00]{private_status}
[C][B][FFFFFF]Verified: [66FF00]{verified_status}
[C][B][FF2EEE]⊹₊˚‧︵‿₊୨ᰔ୧₊‿︵‧˚₊⊹
[B][C][FF00FF]Dev: —͟͞͞ </> Buddy Meow
"""

async def handle_badge_command(cmd, inPuTMsG, uid, chat_id, key, iv, region, chat_type):
    parts = inPuTMsG.strip().split()
    if len(parts) < 2:
        error_msg = f"[B][C][FF0000]❌ Usage: /{cmd} (uid)\nExample: /{cmd} 238🤫722🤫72🤫71\n"
        await safe_send_message(chat_type, error_msg, uid, chat_id, key, iv)
        return
    target_uid = parts[1]
    badge_value = BADGE_VALUES.get(cmd, 1048576)
    if not target_uid.isdigit():
        error_msg = f"[B][C][FF0000]❌ Please write a valid player ID!\n"
        await safe_send_message(chat_type, error_msg, uid, chat_id, key, iv)
        return
    initial_msg = f"[B][C][1E90FF]🌀 Request received! Preparing to send {cmd} ({badge_value}) to {xMsGFixinG(target_uid)}...\n"
    await safe_send_message(chat_type, initial_msg, uid, chat_id, key, iv)
    try:
        badge_packet = await request_join_with_badge(target_uid, badge_value, key, iv, region)
        if badge_packet:
            for i in range(5):
                await SEndPacKeT(whisper_writer, online_writer, 'OnLine', badge_packet)
                await asyncio.sleep(0.2)
            success_msg = f"[B][C][00FF00]✅ Successfully Sent {cmd} Badge!\n🎯 Target: {xMsGFixinG(target_uid)}\n🏷️ Badge Value: {badge_value}\n📤 Packets Sent: 5\n"
        else:
            success_msg = f"[B][C][FF0000]❌ Failed to create badge packet!\n"
        await safe_send_message(chat_type, success_msg, uid, chat_id, key, iv)
    except Exception as e:
        await safe_send_message(chat_type, f"[B][C][FF0000]❌ Error in /{cmd}: {str(e)}\n", uid, chat_id, key, iv)

async def spam_request_loop_with_cosmetics(target_uid, key, iv, region):
    global spam_request_running
    count = 0
    max_requests = 30
    while spam_request_running and count < max_requests:
        try:
            PAc = await OpEnSq(key, iv, region)
            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', PAc)
            await asyncio.sleep(0.2)
            V = await SEnd_InV(5, int(target_uid), key, iv, region)
            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', V)
            E = await ExiT(None, key, iv)
            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', E)
            count += 1
            print(f"Sent request #{count} to {target_uid}")
            await asyncio.sleep(0.5)
        except Exception as e:
            print(f"Error in spam_request_loop for uid {target_uid}: {e}")
            await asyncio.sleep(0.5)

# (evo loop functions defined above)

async def send_all_titles_sequentiallly(uid, chat_id, key, iv, region, chat_type):
    all_titles = [904090014, 904090015, 904090024, 904090025, 904090026, 904090027, 904990070, 904990071, 904990072]
    total_titles = len(all_titles)
    start_msg = """[B][C][00FF00] Noobde Sale Tu Noob Hai, Tera Khandan Noob Hai, Tere Ba😌ap Da😌da Sab Noob Hai, Ab Tu Bta Ye Titles Aur Bol Kon Noob Hai, Yeh Dekh Sale, H😌ar😌amz😌ade\n\n"""
    await safe_send_message(chat_type, start_msg, uid, chat_id, key, iv)
    try:
        for index, title_id in enumerate(all_titles):
            title_number = index + 1
            title_packet = await noob(uid, chat_id, key, iv, nickname="BUDDYMEOW", title_id=title_id)
            if title_packet and whisper_writer:
                whisper_writer.write(title_packet)
                await whisper_writer.drain()
                print(f"✅ Sent title {title_number}/{total_titles}: {title_id}")
            if title_number < total_titles:
                await asyncio.sleep(2)
        completion_msg = """[B][C][00FF00]Noobde ab tu bta ye titles aur bol kon noob hai\n"""
        await safe_send_message(chat_type, completion_msg, uid, chat_id, key, iv)
    except Exception as e:
        await safe_send_message(chat_type, f"[B][C][FF0000]❌ Error sending titles: {str(e)}\n", uid, chat_id, key, iv)

async def handle_alll_titles_command(inPuTMsG, uid, chat_id, key, iv, region, chat_type=0):
    parts = inPuTMsG.strip().split()
    if len(parts) == 1:
        target_uid = uid
    elif len(parts) == 2 and parts[1].isdigit():
        target_uid = parts[1]
    else:
        error_msg = """[B][C][FF0000]❌ Usage: /noob [uid]\n\n📝 Examples:\n/noob - Send all titles to yourself\n/noob 238🤫722🤫72🤫71 - Send all titles to player\n"""
        await safe_send_message(chat_type, error_msg, uid, chat_id, key, iv)
        return
    asyncio.create_task(send_all_titles_sequentiallly(target_uid, chat_id, key, iv, region, chat_type))

boy_names = [
    "KAI","ZENO","RYO","VEX","ZERO","RAZE","FURY","AKIRA","NOVA","ONYX",
    "SORA","REX","LIO","NERO","AXEL","JIN","KIRA","DARKO","FENIX","LEO",
    "ARON","MAX","ELIO","KAGE","YAMI","SHIRO","HERO","ZEROX","NEXO","CYBER",
    "ULTRA","PRIME","FROST","EMBER","BLAZE","VENOM","RAGE","BLOOD","VOID","CHAOS",
    "STORM","LIGHT","SHADOW","PHOENIX","DRAGON","DEMON","GHOST","WOLF","BEAST","KING",
    "HUNTER","SNIPER","ASSASSIN","LEGEND","MYTH","TITAN","WARRIOR","SLAYER","KILLER","REAPER",
    "GOJO","SUKUNA","ITACHI","MADARA","OBITO","NARUTO","SASUKE","KAKASHI","GOKU","VEGETA",
    "ZENITSU","TANJIRO","INOSUKE","ZEN","RYUKO","AKIO","HARU","REN","RIN","KAZE",
    "TAIGA","DAIKI","SHIN","YORI","KAIJI","RUI","HIKARU","KENTO","SATORU","YUJI",
    "ARATA","KOJI","REO","SHO","TAKU","YUTO","HARUTO","MINATO","SHINJI","KAITO", "ALPHA","OMEGA","SIGMA","DELTA","ECHO","NOVA","ZERO","RAZE","FURY","LEGEND",
    "MYTH","KING","QUEEN","PHOENIX","DRAGON","SHADOW","GHOST","VOID","CHAOS"
]
girl_names = [
    "LUNA","MIRA","YUNA","ARIA","SORA","NOA","MOMO","NANA","EMI","RINA",
    "AYU","HANA","MIKA","SAYA","AIRI","YUKI","REINA","NORA","ELLA","ZARA",
    "DIOSA","NOVA","SHIRO","CYRA","LUX","MIZU","AKI","HINA","KANA","RUKA",
    "SAKI","MEI","RUI","YUME","AIKO","HARU","NAMI","YORI","RISA","KIRA",
    "AYAKA","NAO","YURI","RINO","MIO","SENA","KOKO","FUKA","REI","TSUKI",
    "AMI","MIYU","RUKO","AYA","SAORI","YUKA","HARUKA","NATSUKI","KOHANA","MINA",
    "ELENA","SORAIA","LINA","ARIAH","MIRAI","NOZOMI","SHIHO","MAYU","KAEDE","RUKI",
    "YUNAIA","HIKARI","SATSUKI","RENKA","MOKA","NENE","RINAO","AYANE","YUKINA","KIRARI",
    "SUZU","MARI","RUKIYA","HANAO","MIYU","SAKURA","AOI","KANAO","YUA","MIHO",
    "RAN","NICO","LIA","ARIAE","ELLAH","MIRAEL","LUNARA","ZARINA","NOVIA","CYRIA"
]
all_names = boy_names + girl_names
symbols = ["❤︎","♡","❥","ღ","⚡","✦","✧","✿","❀","☯","☮","᭄","࿐","〆","ϟ","ツ","あ","愛","夜","影","鬼","神","夢","月","桜","炎"]
PREFIX = "—͞"

def clean_name(name: str) -> str:
    name = re.sub(r'[^a-zA-Z0-9 ]', '', name)
    return name.strip().upper()[:12]

def build_name(base, mode="random"):
    base = clean_name(base)
    end = random.choice(symbols)
    apple = random.choice([""])
    return f"{PREFIX}{base}ㅤ{end}{apple}"

# ═══════════════════════════════════════════════════════════════
# TCP ONLINE HANDLER
# ═══════════════════════════════════════════════════════════════
async def TcPOnLine(ip, port, key, iv, AutHToKen, reconnect_delay=0.5):
    global online_writer, last_status_packet, status_response_cache, senthi
    global insquad, joining_team, whisper_writer, region
 
    bot_uid = 18846744624
 
    if insquad is not None:
        insquad = None
    if joining_team is True:
        joining_team = False
    
    online_writer = None
    
    while True:
        try:
            print(f"Attempting to connect to {ip}:{port}...")
            reader, writer = await asyncio.open_connection(ip, int(port))
            online_writer = writer
            
            # --- AUTHENTICATION ---
            bytes_payload = (
                bytes.fromhex(AutHToKen)
                if isinstance(AutHToKen, str)
                else bytes(AutHToKen)
            )
            online_writer.write(bytes_payload)
            await online_writer.drain()
            print("Authentication token sent. Listening for emotes...")
            
            # --- READING LOOP ---
            while True:
                data2 = await reader.read(9999)
                    
                if not data2: 
                    print("Connection closed by the server.")
                    break
                    
                data_hex = data2.hex()
      
                # Your existing code...
  
                
                
              # =================== EMOTE DETECTION ONLY ===================
                if data_hex.startswith("0500") and emote_hijack == True:
                    try:
                        # Try to detect emote
                        emote_info = await extract_emote_info(data_hex, key, iv)
                        
                        in_squad = insquad is not None
            

                

                        
                        if emote_info and emote_info.get('sender_uid'):
                            sender_uid = emote_info['sender_uid']
                            emote_id = emote_info['emote_id']
                            
                            
                            
                            print(f"\n🎯 EMOTE DETECTED!")
                            print(f"   👤 Sender UID: {sender_uid}")
                            print(f"   🎭 Emote ID: {emote_id}")
                            
                            # Don't respond to bot's own emotes
                            if int(sender_uid) != bot_uid:
                                print("🤖 Bot responding with dual emotes...")
                                
                                # STEP 1: Send fixed emote 909035003 to the sender
                                print(f"  1️⃣ Sending emote 909035003 to {sender_uid}")
                                fixed_emote_packet = await Emote_k(
                                    int(sender_uid), 
                                    909035003,  # Fixed emote ID
                                    key, iv, region
                                )
                                if fixed_emote_packet and online_writer:
                                    online_writer.write(fixed_emote_packet)
                                    await online_writer.drain()
                                    await asyncio.sleep(0.5)
                                
                                # STEP 2: Bot does the SAME emote that user did (to itself)
                                print(f"  2️⃣ Bot doing same emote {emote_id} to itself")
                                bot_self_emote = await Emote_k(
                                    bot_uid,  # Bot's own UID
                                    int(emote_id),  # Same emote user did
                                    key, iv, region
                                )
                                if bot_self_emote and online_writer:
                                    online_writer.write(bot_self_emote)
                                    await online_writer.drain()
                                    await asyncio.sleep(0.5)
                                
                                # STEP 3: Bot also sends the emote back to sender
                                print(f"  3️⃣ Mirroring emote {emote_id} back to {sender_uid}")
                                mirror_emote = await Emote_k(
                                    int(sender_uid),
                                    int(emote_id),  # Same emote back
                                    key, iv, region
                                )
                                if mirror_emote and online_writer:
                                    online_writer.write(mirror_emote)
                                    await online_writer.drain()
                                
                                print("✅ Dual emote response complete!")
                            
                            else:
                                print("⚠️ Skipping - bot's own emote")
                                
                    except Exception as e:
                        print(f"❌ Emote response error: {e}")
                        continue 
            
                    


               # =================== AUTO ACCEPT HANDLING ===================

                banned_users = load_bans()
                admin_data = load_admins()


                # =================== CASE 1: SQUAD CANCEL ===================
                if data_hex.startswith('0500') and insquad is not None and joining_team == False:
                    try:
                        packet = await DeCode_PackEt(data_hex[10:])
                        packet_json = json.loads(packet)

                        if packet_json.get('1') in [6, 7]:
                            insquad = None
                            joining_team = False
                            print("Squad cancelled or exited (code 6/7).")
                            continue

                    except Exception as e:
                        print(f"Case 1 error: {e}")


                # =================== CASE 2: AUTO ACCEPT ===================
                # =================== AUTO ACCEPT ===================
                # =================== AUTO ACCEPT ===================
                if data_hex.startswith("0500") and insquad is None and joining_team == False:
                    try:
                        packet = await DeCode_PackEt(data_hex[10:])
                        packet_json = json.loads(packet)

                        field5 = packet_json.get('5', {}).get('data', {})

                        uid = field5.get('1', {}).get('data')
                        code = field5.get('8', {}).get('data')

                        invite_section = field5.get('2', {}).get('data', {})
                        invite_uid = invite_section.get('1', {}).get('data') if isinstance(invite_section, dict) else None

                        squad_owner = uid

                        if not uid or not code:
                            continue

                        # =================== 🚫 BAN CHECK ===================
                        if str(squad_owner) in banned_users or str(invite_uid) in banned_users:
                            print("🚫 Banned user detected → IGNORING invite")
                            continue

                        # =================== 🔐 ADMIN MODE ===================
                        if admin_mode and not is_admin(squad_owner):
                            print("🔐 Admin mode ON → non-admin ignored")
                            continue

                        # =================== 🛑 AUTO-ACCEPT CHECK ===================
                        # ✅ অ্যাডমিনদের জন্য বাইপাস: অ্যাডমিন হলে auto_accept_enabled চেক করবে না
                        if not auto_accept_enabled and not is_admin(squad_owner):
                            print("🚫 Auto-Accept is OFF → REJECTING invite")
                            continue

                        # =================== SAFETY LOCK ===================
                        if insquad or joining_team:
                            continue

                        print(f"📨 Invite UID: {invite_uid}")
                        print(f"👤 Squad Owner: {squad_owner}")
                        print(f"🎯 Squad Code: {code}")

                        emote_id = 909050009
                        bot_uid = 18846744624

                        print(f"✅ Accepting invite from {squad_owner}")

                        # Send invite back (optional)
                        if invite_uid:
                            SendInv = await RedZed_SendInv(bot_uid, invite_uid, key, iv)
                            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', SendInv)

                        # Accept packet
                        inv_packet = await RejectMSGtaxt(squad_owner, uid, key, iv)
                        await SEndPacKeT(whisper_writer, online_writer, 'OnLine', inv_packet)

                        Join = await MahirAccepted(squad_owner, code, key, iv, region)
                        await SEndPacKeT(whisper_writer, online_writer, 'OnLine', Join)

                        await asyncio.sleep(2)

                        # Emotes
                        emote_to_sender = await Emote_k(int(uid), emote_id, key, iv, region)
                        await SEndPacKeT(whisper_writer, online_writer, 'OnLine', emote_to_sender)

                        bot_emote = await Emote_k(int(bot_uid), emote_id, key, iv, region)
                        await SEndPacKeT(whisper_writer, online_writer, 'OnLine', bot_emote)

                        insquad = True
                        joining_team = True

                        print(f"🤖 Bot joined squad of {squad_owner}")

                    except Exception as e:
                        print(f"Auto accept error: {e}")
                        traceback.print_exc()
                        insquad = None
                        joining_team = False
                        continue
                
                # =================== HANDLE KICK/RECONNECT ===================
                # Case 3: Bot was kicked and needs to re-join chat
                if data_hex.startswith('0500') and len(data_hex) > 1000:
                    try:
                        packet = await DeCode_PackEt(data_hex[10:])
                        packet_json = json.loads(packet)
                    
                        packet_type = packet_json.get('1')
        
                        # Detect ALL kick/leave packets
                        if packet_type in [6, 7, 8, 9, 10, 11, 12]:
                            print(f"🚪 Kick/Leave packet detected (Type: {packet_type})")
            
                            # RESET SQUAD STATUS
                            insquad = None
                            joining_team = False
            
                            print(f"✅ Bot reset after kick. Ready for new invites.")
                            
                            # Try to extract squad info for possible reconnection
                            try:
                                if '5' in packet_json and 'data' in packet_json['5']:
                                    OwNer_UiD, CHaT_CoDe, SQuAD_CoDe = await GeTSQDaTa(packet_json)
                                    if any(value is None for value in (OwNer_UiD, CHaT_CoDe, SQuAD_CoDe)):
                                        print("⚠️ Kick/leave packet has incomplete squad data")
                                        continue
                                    print(f"🔄 Attempting reconnection to squad {SQuAD_CoDe}...")
                    
                                    # Re-authenticate chat
                                    JoinCHaT = await AutH_Chat(3, OwNer_UiD, CHaT_CoDe, key, iv)
                                    await SEndPacKeT(whisper_writer, online_writer, 'ChaT', JoinCHaT)
                    
                                    print(f"✅ Chat re-authenticated for reconnection")
                            except:
                                print("⚠️ Could not extract squad info")
                                
                            continue  # Skip other handlers
        
                        # Also check for general squad data packets (for reconnection)
                        elif '5' in packet_json and 'data' in packet_json['5']:
                            try:
                                OwNer_UiD, CHaT_CoDe, SQuAD_CoDe = await GeTSQDaTa(packet_json)
                                if any(value is None for value in (OwNer_UiD, CHaT_CoDe, SQuAD_CoDe)):
                                    print("⚠️ Ignoring incomplete squad data packet")
                                    continue
                
                                # If we have squad data but insquad is None, try to reconnect
                                if insquad is None:
                                    print(f"🤖 Received squad data while not in squad. Attempting chat auth...")
                                    
                                    JoinCHaT = await AutH_Chat(3, OwNer_UiD, CHaT_CoDe, key, iv)
                                    await SEndPacKeT(whisper_writer, online_writer, 'ChaT', JoinCHaT)
                    
                                    # Optional welcome back message
                                    welcome_msg = """[B][C][00FF00]🤖 Bot reconnected!"""
                                    P = await SEndMsG(0, welcome_msg, OwNer_UiD, OwNer_UiD, key, iv)
                                    await SEndPacKeT(whisper_writer, online_writer, 'ChaT', P)
                    
                            except:
                                pass  # Not a squad data packet
                
                    except Exception as e:
                        print(f"❌ Kick/reconnect handler error: {e}")
                        pass
                
                # case 5
                if insquad == True:
                    try:
                        packet = await DeCode_PackEt(data_hex[10:])
                        packet_json = json.loads(packet)

                        if not isinstance(packet_json, dict):
                            continue

                        if '5' not in packet_json:
                            continue

                        if not isinstance(packet_json['5'], dict):
                            continue

                        if 'data' not in packet_json['5']:
                            continue

                        try:
                            OwNer_UiD, CHaT_CoDe, SQuAD_CoDe = await GeTSQDaTa(packet_json)
                        except Exception as e:
                            print(f"⚠️ Not a valid squad packet: {e}")
                            continue
                        if any(value is None for value in (OwNer_UiD, CHaT_CoDe, SQuAD_CoDe)):
                            print("⚠️ Ignoring incomplete squad data packet")
                            continue

                        print(f"Received squad data for joining team, attempting chat auth for {OwNer_UiD}...")

                        JoinCHaT = await AutH_Chat(3, OwNer_UiD, CHaT_CoDe, key, iv)
                        
                        await SEndPacKeT(whisper_writer, online_writer, 'ChaT', JoinCHaT)

                        def get_random_color():
                            return "_"

                        message = """[B][C][FF69B4]૮ ˶ᵔ ᵕ ᵔ˶ ა ITS BUDDY MEOW ˎˊ˗

[00FFFF]»»————-　♡　————-««
[FFFFFF]Creator: [FF69B4]Buddy Meow
[FFFFFF]Facebook: [FFFF00]Rizzfez Zitt
[FFFFFF]TikTok: [FFFF00]@buddy_meow

[FFFFFF]Status: [00FF00]ACTIVE 24/7
[FFFFFF]Enjoy, have fun & stay cute!
[00FFFF]»»————-　♡　————-««

[FF69B4]ฅ^•ﻌ•^ฅ THANK YOU BBE!"""
                        P = await SEndMsG(0, message, OwNer_UiD, OwNer_UiD, key, iv)
                        await SEndPacKeT(whisper_writer, online_writer, 'ChaT', P)

                        joining_team = False
                        insquad = None

                    except Exception as e:
                        print(f"Error in joining_team chat auth: {e}")
                        traceback.print_exc()
                        joining_team = False
                        insquad = None
                
                if "0600" in data2.hex()[0:4] and len(data2.hex()) > 700:
                    accept_packet = f'08{data2.hex().split("08", 1)[1]}'
                    kk = get_available_room(accept_packet)
                    parsed_data = json.loads(kk)
                    #logging.info(parsed_data)

                    senthi = True

                if senthi == True:
                    
                    def get_random_color(): return "_" 
                    message = """[B][C][FF69B4]૮ ˶ᵔ ᵕ ᵔ˶ ა ITS BUDDY MEOW ˎˊ˗

[00FFFF]»»————-　♡　————-««
[FFFFFF]Creator: [FF69B4]Buddy Meow
[FFFFFF]Facebook: [FFFF00]Rizzfez Zitt
[FFFFFF]TikTok: [FFFF00]@buddy_meow

[FFFFFF]Status: [00FF00]ACTIVE 24/7
[FFFFFF]Enjoy, have fun & stay cute!
[00FFFF]»»————-　♡　————-««

[FF69B4]ฅ^•ﻌ•^ฅ THANK YOU BBE!"""
                        # In your auto-join (Old Handler) code, find this line:

                    P = await SEndMsG(0, message, OwNer_UiD, OwNer_UiD, key, iv)
                    await SEndPacKeT(whisper_writer, online_writer, 'ChaT', P)
                    senthi = False


                # =================== STATUS HANDLER ===================
                if data_hex.startswith('0f00') and len(data_hex) > 100:
                    print(f"📡 Received status response packet")
    
                    try:
                        # Assuming the protocol structure: 0f00 + length bytes + 08 + actual proto data
                        # The split logic might need refinement based on the exact protocol
                        if '08' in data_hex:
                            proto_part = f'08{data_hex.split("08", 1)[1]}'
                        else:
                            print("⚠️ Status packet structure missing '08' marker.")
                            continue
        
                        # Assuming get_available_room is available
                        parsed_data = get_available_room(proto_part)
                        if parsed_data:
                            parsed_json = json.loads(parsed_data)
            
                            # Check if it's field 15 (player info)
                            if "2" in parsed_json and parsed_json["2"]["data"] == 15:
                                # Get player ID
                                player_id = parsed_json["5"]["data"]["1"]["data"]["1"]["data"]
                
                                # Assuming get_player_status is available
                                player_status = get_player_status(proto_part) 
                                print(f"✅ Parsed status for {player_id}: {player_status}")
                
                                # Create cache entry
                                cache_entry = {
                                    'status': player_status, 
                                    'packet': proto_part,
                                    'timestamp': time.time(),
                                    'full_packet': data_hex,
                                    'parsed_json': parsed_json
                                }
                
                                # --- SPECIAL CONDITION CHECK ---
                                try:
                                    StatusData = parsed_json
                                    if ("5" in StatusData and "data" in StatusData["5"] and 
                                        "1" in StatusData["5"]["data"] and "data" in StatusData["5"]["data"]["1"] and 
                                        "3" in StatusData["5"]["data"]["1"]["data"] and "data" in StatusData["5"]["data"]["1"]["data"]["3"] and 
                                        StatusData["5"]["data"]["1"]["data"]["3"]["data"] == 1 and 
                                        "11" in StatusData["5"]["data"]["1"]["data"] and "data" in StatusData["5"]["data"]["1"]["data"]["11"] and 
                                        StatusData["5"]["data"]["1"]["data"]["11"]["data"] == 1):
                
                                        print(f"🎯 SPECIAL CONDITION MET: Player {player_id} is in SOLO mode with special flag 11=1")
                                        cache_entry['special_state'] = 'SOLO_WITH_FLAG_1'
                
                                except Exception as cond_error:
                                    print(f"⚠️ Error checking special condition: {cond_error}")
                                # ------------------------------

                                # If in room, extract room ID
                                if "IN ROOM" in player_status:
                                    try:
                                        # Assuming get_idroom_by_idplayer is available
                                        room_id = get_idroom_by_idplayer(proto_part)
                                        if room_id:
                                            cache_entry['room_id'] = room_id
                                            print(f"🏠 Room ID extracted: {room_id}")
                                    except Exception as room_error:
                                        print(f"Failed to extract room ID: {room_error}")
                
                                # If in squad, extract leader
                                elif "INSQUAD" in player_status:
                                    try:
                                        # Assuming get_leader is available
                                        leader_id = get_leader(proto_part)
                                        if leader_id:
                                            cache_entry['leader_id'] = leader_id
                                            print(f"👑 Leader ID: {leader_id}")
                                    except Exception as leader_error:
                                        print(f"Failed to extract leader: {leader_error}")
                
                                # Save to FILE cache (Assuming save_to_cache is available)
                                save_to_cache(player_id, cache_entry)
                                print(f"✅ Saved to cache: {player_id} = {player_status}")
                
                    except Exception as e:
                        print(f"❌ Error parsing status: {e}")
                        traceback.print_exc()
                
                # =================== END STATUS HANDLER ===================

            # --- CLEANUP AFTER INNER LOOP (Connection closed) ---
            if online_writer is not None:
                online_writer.close()
                await online_writer.wait_closed()
                online_writer = None
            
            if whisper_writer is not None:
                try:
                    whisper_writer.close()
                    await whisper_writer.wait_closed()
                except:
                    pass
                whisper_writer = None
                
            insquad = None
            joining_team = False
            
            print(f"Connection closed. Reconnecting in {reconnect_delay} seconds...")

        except ConnectionRefusedError:
            print(f"Connection refused by server at {ip}:{port}.")
        except asyncio.TimeoutError:
            print(f"Connection attempt to {ip}:{port} timed out.")
        except Exception as e:
            print(f"- ErroR With {ip}:{port} - {e}")
            traceback.print_exc() 
            
            # --- CLEANUP AFTER EXCEPTION ---
            if online_writer is not None:
                try:
                    online_writer.close()
                    await online_writer.wait_closed()
                except:
                    pass
                online_writer = None
            if whisper_writer is not None:
                try:
                    whisper_writer.close()
                    await whisper_writer.wait_closed()
                except:
                    pass
                whisper_writer = None
                
            insquad = None
            joining_team = False
            
        await asyncio.sleep(reconnect_delay)


# ═══════════════════════════════════════════════════════════════
# HELP MENU
# ═══════════════════════════════════════════════════════════════
def get_help_pages():
    border = "[BF00FF]✿▰▰▰▰▰▰▰▰▰▰✿"
    pages = (
        f"""{border}

[00FFFF]✿ [FFFFFF]Create 3-Player Group
[FF66CC]  ╰─▷ /3

[00FFFF]✿ [FFFFFF]Create 5-Player Group
[FF66CC]  ╰─▷ /5

[00FFFF]✿ [FFFFFF]Create 6-Player Group
[FF66CC]  ╰─▷ /6

[00FFFF]✿ [FFFFFF]Invite Player
[FF66CC]  ╰─▷ /inv [uid]

[00FFFF]✿ [FFFFFF]Send 5-Player Group
[FF66CC]  ╰─▷ /snd [uid]

[00FFFF]✿ [FFFFFF]Join Team
[FF66CC]  ╰─▷ /join [TeamCode]

[00FFFF]✿ [FFFFFF]Leave Group
[FF66CC]  ╰─▷ /exit

{border}""",
        f"""{border}

[00FFFF]✿ [FFFFFF]Check Player Info
[FF66CC]  ╰─▷ /info [uid]

[00FFFF]✿ [FFFFFF]Check Duo Info
[FF66CC]  ╰─▷ /duo [uid]

[00FFFF]✿ [FFFFFF]Check Ban Status
[FF66CC]  ╰─▷ /check [uid]

[00FFFF]✿ [FFFFFF]Check Cached Chat Activity
[FF66CC]  ╰─▷ /status [uid]

{border}""",
        f"""{border}

[00FFFF]✿ [FFFFFF]Stop Badge Spam
[FF66CC]  ╰─▷ /stop_badge

[00FFFF]✿ [FFFFFF]Spam Invite
[FF66CC]  ╰─▷ /spm_inv [uid]

[00FFFF]✿ [FFFFFF]Stop Spam Invite
[FF66CC]  ╰─▷ /sspm

[FFFFFF]All Badge Spam
[FF66CC]  ╰─▷ /spm_badge [uid] 

[00FFFF]✿ [FFFFFF]Kick Player
[FF66CC]  ╰─▷ /kick [uid]

{border}""",
        f"""{border}

[00FFFF]✿ [FFFFFF]Play Normal Emotes
[FF66CC]  ╰─▷ /e [uid] [1-410]

[00FFFF]✿ [FFFFFF]Play Normal Emotes
[FF66CC]  ╰─▷ /e [uid] [EmoteName]

[00FFFF]✿ [FFFFFF]Play Emote With ID
[FF66CC]  ╰─▷ !e [UID1] [EmoteID]

[00FFFF]✿ [FFFFFF]Fast Emote
[FF66CC]  ╰─▷ /fast [UID1] [EmoteID]

[00FFFF]✿ [FFFFFF]Times Emote
[FF66CC]  ╰─▷ /p [uid] [emote] [count]

[00FFFF]✿ [FFFFFF]Play Emote Self
[FF66CC]  ╰─▷ /play [emote]

[00FFFF]✿ [FFFFFF]Play Emote Player
[FF66CC]  ╰─▷ /play [uid] [emote]

[00FFFF]✿ [FFFFFF]Play Emote Without Bot
[FF66CC]  ╰─▷ /me [TeamCode] [emote]

[00FFFF]✿ [FFFFFF]Player Emote Without Bot
[FF66CC]  ╰─▷ /me [TmCd] [uid] [emote]

{border}""",
        f"""{border}

[00FFFF]✿ [FFFFFF]Evo Emote With Friend
[FF66CC]  ╰─▷ /evo [uid1] [uid2] [emtnum]

[00FFFF]✿ [FFFFFF]Fast Evo Emote
[FF66CC]  ╰─▷ /evo_fast [uid1] [emtnum]

[00FFFF]✿ [FFFFFF]Stop Fast Evo Emote
[FF66CC]  ╰─▷ /stop evo_fast

[00FFFF]✿ [FFFFFF]Evo Emote With Timer
[FF66CC]  ╰─▷ /evo_c [uid1] [emt] [cnt]

[00FFFF]✿ [FFFFFF]Stop Evo With Timer
[FF66CC]  ╰─▷ /stop evo_c

[00FFFF]✿ [FFFFFF]Evo Cycle Self
[FF66CC]  ╰─▷ @evos

[00FFFF]✿ [FFFFFF]Evo Cycle Player
[FF66CC]  ╰─▷ @evos [uid]

[00FFFF]✿ [FFFFFF]List Evo Emotes
[FF66CC]  ╰─▷ /evolist

[00FFFF]✿ [FFFFFF]Stop Evo Cycle
[FF66CC]  ╰─▷ @sevos

{border}""",
        f"""{border}

[00FFFF]✿ [FFFFFF]Chat With AI
[FF66CC]  ╰─▷ /ai [question]

[00FFFF]✿ [FFFFFF]Send Sticker Emoji
[FF66CC]  ╰─▷ /sticker

[00FFFF]✿ [FFFFFF]Send Titles
[FF66CC]  ╰─▷ /title

[00FFFF]✿ [FFFFFF]Important Announcement
[FF66CC]  ╰─▷ /bc [msg]

[00FFFF]✿ [FFFFFF]Freeze Player
[FF66CC]  ╰─▷ /ice [uid]

[00FFFF]✿ [FFFFFF]Fetch Youtuber Info
[FF66CC]  ╰─▷ /yt [username]

[00FFFF]✿ [FFFFFF]Fetch Instagram Info
[FF66CC]  ╰─▷ /ig [username]

[00FFFF]✿ [FFFFFF]Fetch TikTok Info
[FF66CC]  ╰─▷ /tt [username]

[00FFFF]✿ [FFFFFF]Bot Creator Info
[FF66CC]  ╰─▷ /creator

{border}""",
        f"""{border}

[00FFFF]✿ [FFFFFF]Send Spam Message
[FF66CC]  ╰─▷ /ms [msg]

[00FFFF]✿ [FFFFFF]Send Custom Spam Message
[FF66CC]  ╰─▷ /msg [msg] [count]

[00FFFF]✿ [FFFFFF]Stop Custom Spam Message
[FF66CC]  ╰─▷ /stop msg

[00FFFF]✿ [FFFFFF]Send Shrinking Spam Message
[FF66CC]  ╰─▷ /mg [msg]

[00FFFF]✿ [FFFFFF]Send Gali To Haters
[FF66CC]  ╰─▷ /gali [name]

[00FFFF]✿ [FFFFFF]Troll With Haters
[FF66CC]  ╰─▷ /lol [name]

[00FFFF]✿ [FFFFFF]Send Pickup Line
[FF66CC]  ╰─▷ /pick [name]

[00FFFF]✿ [FFFFFF]Send Praise Message
[FF66CC]  ╰─▷ /gd [name]

[00FFFF]✿ [FFFFFF]Random Fun Message
[FF66CC]  ╰─▷ /fun

[00FFFF]✿ [FFFFFF]Noob Title
[FF66CC]  ╰─▷ /noob

[00FFFF]✿ [FFFFFF]Cat ASCII Art
[FF66CC]  ╰─▷ /meow

{border}""",
        f"""{border}

[00FFFF]✿ [FFFFFF]Send Love Message
[FF66CC]  ╰─▷ /love [name]

[00FFFF]✿ [FFFFFF]Send Crush Message
[FF66CC]  ╰─▷ /crush [name]

[00FFFF]✿ [FFFFFF]Generate Stylish Name
[FF66CC]  ╰─▷ /name [name]

[00FFFF]✿ [FFFFFF]Check Your Luck
[FF66CC]  ╰─▷ /luck

[00FFFF]✿ [FFFFFF]Translate Any Language
[FF66CC]  ╰─▷ /translate [text]

[00FFFF]✿ [FFFFFF]See Guild Rules
[FF66CC]  ╰─▷ /guildrules

{border}""",
        f"""{border}

[00FFFF]✿ [FFFFFF]Bundle List
[FF66CC]  ╰─▷ /bundle

[00FFFF]✿ [FFFFFF]Equip Bundle
[FF66CC]  ╰─▷ /bundle [name]

[00FFFF]✿ [FFFFFF]Bundle Spam
[FF66CC]  ╰─▷ /bb_lag [TeamCode]

{border}""",
        f"""{border}

[00FFFF]✿ [FFFFFF]Join Req Craftland Badge
[FF66CC]  ╰─▷ /s1 [uid]

[00FFFF]✿ [FFFFFF]Join Req New V-Badge
[FF66CC]  ╰─▷ /s2 [uid]

[00FFFF]✿ [FFFFFF]Join Req Moderator Badge
[FF66CC]  ╰─▷ /s3 [uid]

[00FFFF]✿ [FFFFFF]Join Req Old V-Badge
[FF66CC]  ╰─▷ /s4 [uid]

[00FFFF]✿ [FFFFFF]Join Req Pro Badge
[FF66CC]  ╰─▷ /s5 [uid]

{border}""",
        f"""{border}

[00FFFF]✿ [FFFFFF]Admin Mode On
[FF66CC]  ╰─▷ /adon

[00FFFF]✿ [FFFFFF]Admin Mode Off
[FF66CC]  ╰─▷ /adoff

[00FFFF]✿ [FFFFFF]On Bot
[FF66CC]  ╰─▷ /on

[00FFFF]✿ [FFFFFF]Off Bot
[FF66CC]  ╰─▷ /off

{border}""",
        f"""{border}

[00FFFF]✿ [FFFFFF]Add New Admin
[FF66CC]  ╰─▷ /addadmin [uid]

[00FFFF]✿ [FFFFFF]Remove Admin
[FF66CC]  ╰─▷ /removeadmin [uid]

[00FFFF]✿ [FFFFFF]Check Your Role
[FF66CC]  ╰─▷ /whoami

[00FFFF]✿ [FFFFFF]Admin List
[FF66CC]  ╰─▷ /admins

[00FFFF]✿ [FFFFFF]Clear Admin List
[FF66CC]  ╰─▷ /clear

[00FFFF]✿ [FFFFFF]Auto Accept Invite
[FF66CC]  ╰─▷ /accept

[00FFFF]✿ [FFFFFF]Reject Spam Invite
[FF66CC]  ╰─▷ /reject

{border}""",
        f"""{border}

[00FFFF]✿ [FFFFFF]Ban User
[FF66CC]  ╰─▷ /ban [uid]

[00FFFF]✿ [FFFFFF]Unban User
[FF66CC]  ╰─▷ /unban [uid]

[00FFFF]✿ [FFFFFF]Ban List
[FF66CC]  ╰─▷ /bans

[00FFFF]✿ [FFFFFF]Clear Ban List
[FF66CC]  ╰─▷ /cb

{border}""",
        f"""{border}

[00FFFF]✿ [FFFFFF]Add Bot Friend
[FF66CC]  ╰─▷ /fadd [uid]

[00FFFF]✿ [FFFFFF]Remove Bot Friend
[FF66CC]  ╰─▷ /fremove [uid]

{border}""",
        f"""{border}

[00FFFF]✿ [FFFFFF]Set Auto Reply
[FF66CC]  ╰─▷ /set [trigger] [reply]

[00FFFF]✿ [FFFFFF]Auto Reply List
[FF66CC]  ╰─▷ /replies

[00FFFF]✿ [FFFFFF]Delete Auto Reply
[FF66CC]  ╰─▷ /del [trigger]

{border}""",
        f"""{border}

[00FFFF]✿ [FFFFFF]Free Guild Bot?
[FF66CC]  ╰─▷ /free

[00FFFF]✿ [FFFFFF]BUDDY'S STORE
[FF66CC]  ╰─▷ /store

{border}""",
        f"""{border}

[00FFFF]✿ [FFFFFF]Owner Name
[FF66CC]  ╰─▷ Buddy Meow

[00FFFF]✿ [FFFFFF]Owner UID
[FF66CC]  ╰─▷ 238🤔722🤔72🤔71

[00FFFF]✿ [FFFFFF]Facebook
[FF66CC]  ╰─▷ Rizzfez Zitt

[00FFFF]✿ [FFFFFF]TikTok
[FF66CC]  ╰─▷ @buddy_meow

{border}""",
        """[C][B][00FFFA]╭┈ • ┈୨ BOT INFO ୧┈ • ┈╮[B]

ㅤㅤㅤ[FFFF00]Dev : [FF1493]Buddy Meow
ㅤㅤㅤ  [32CD32]Status : [00FF00]Online
ㅤㅤ  [1E90FF]Version : [1E90FF]Buddy V5.0

[00FFFA]╰┈ • ┈୨ STAY SAFE ୧┈ • ┈╯""",
    )
    return pages

# ═══════════════════════════════════════════════════════════════
# TCP CHAT HANDLER
# ═══════════════════════════════════════════════════════════════
async def TcPChaT(ip, port, AutHToKen, *args, reconnect_delay=0.5, **kwargs):
    global whisper_writer, online_writer, spm_tasks, ToKen, bot_uid, bot_enabled, emote_hijack
    global admin_mode, auto_accept_enabled, expire_timestamp
    global spam_targets, evo_cycle_running, evo_cycle_task, ban_task, ban_running, ban_targets
    global fast_spam_running, fast_spam_task, custom_spam_running, custom_spam_task
    global evo_fast_spam_running, evo_fast_spam_task, evo_custom_spam_running, evo_custom_spam_task
    global msg_spam_running, msg_spam_task, mg_spam_task
    global reject_spam_running, reject_spam_task, freeze_running, freeze_task
    global clan_id, clan_data, login_data

    # Resolve arguments flexibly
    key = kwargs.get('key')
    iv = kwargs.get('iv')
    ready_event = kwargs.get('ready_event')
    chat_region = kwargs.get('region') or region or "ind"
    c_data = kwargs.get('clan_data') or clan_data
    c_id = kwargs.get('clan_id') or clan_id
    l_data = kwargs.get('login_data') or kwargs.get('LoGinDaTaUncRypTinG') or login_data

    unassigned = []
    for arg in args:
        if isinstance(arg, asyncio.Event):
            ready_event = arg
        elif isinstance(arg, (bytes, bytearray)):
            if key is None:
                key = arg
            elif iv is None:
                iv = arg
            else:
                unassigned.append(arg)
        elif hasattr(arg, 'Clan_ID') or hasattr(arg, 'Clan_Compiled_Data') or (isinstance(arg, dict) and ('clan_id' in arg or 'Clan_ID' in arg)):
            l_data = arg
        elif isinstance(arg, str) and (len(arg) <= 4 or arg.upper() in ['IND', 'BD', 'ME', 'SG', 'BR', 'US', 'PK', 'NA', 'SAC', 'ID', 'TH', 'VN', 'TW', 'RU']):
            chat_region = arg
        else:
            unassigned.append(arg)

    for item in unassigned:
        if key is None and isinstance(item, (bytes, bytearray, str)):
            key = item
        elif iv is None and isinstance(item, (bytes, bytearray, str)):
            iv = item
        elif l_data is None:
            l_data = item
        elif ready_event is None and isinstance(item, asyncio.Event):
            ready_event = item
        elif chat_region is None and isinstance(item, str):
            chat_region = item

    if ready_event is None:
        ready_event = asyncio.Event()

    # Extract clan details if login_data provided
    if l_data is not None:
        login_data = l_data
        if not c_id:
            c_id = getattr(l_data, 'Clan_ID', None) if not isinstance(l_data, dict) else (l_data.get('Clan_ID') or l_data.get('clan_id'))
        if not c_data:
            c_data = getattr(l_data, 'Clan_Compiled_Data', None) if not isinstance(l_data, dict) else (l_data.get('Clan_Compiled_Data') or l_data.get('clan_data'))

    if c_id:
        try: clan_id = int(str(c_id).strip())
        except Exception: clan_id = c_id
    if c_data:
        clan_data = str(c_data)

    print(f"📡 {chat_region} → TCP CHAT connecting...")
    while True:
        try:
            reader, writer = await asyncio.open_connection(ip, int(port))
            whisper_writer = writer
            bytes_payload = (
                bytes.fromhex(AutHToKen)
                if isinstance(AutHToKen, str)
                else bytes(AutHToKen)
            ) if isinstance(AutHToKen, str) else AutHToKen
            whisper_writer.write(bytes_payload); await whisper_writer.drain()
            ready_event.set()
            print(f"✅ CHAT connected to {ip}:{port}")

            # Guild / Clan chat authentication
            active_clan_id = clan_id or (getattr(login_data, 'Clan_ID', 0) if login_data else 0)
            active_clan_data = clan_data or (getattr(login_data, 'Clan_Compiled_Data', '') if login_data else '')
            if isinstance(active_clan_id, str) and active_clan_id.isdigit():
                active_clan_id = int(active_clan_id)
            if active_clan_id and int(active_clan_id) > 0 and active_clan_data:
                try:
                    print('\n - TarGeT BoT in CLan ! ')
                    print(f' - Clan Uid > {active_clan_id}')
                    pK = await AuthClan(int(active_clan_id), str(active_clan_data), key, iv)
                    if whisper_writer:
                        whisper_writer.write(pK)
                        await whisper_writer.drain()
                    print(' - BoT ConnEcTed WiTh CLan ChaT SuccEssFuLy ! \n')
                except Exception as e:
                    print(f' - ❌ Error in Clan Chat Auth: {e}')

            for tgt in spam_targets:
                if tgt not in spm_tasks or spm_tasks[tgt].done():
                    spm_tasks[tgt] = asyncio.create_task(spm_loop(tgt, key, iv))

            while True:
                data = await reader.read(9999)
                if not data: break
                if not data.hex().startswith("120000"): continue
                try:
                    response = await DecodeWhisperMessage(data.hex()[10:])
                    uid = response.Data.uid
                    chat_id = response.Data.Chat_ID
                    XX = response.Data.chat_type
                    inPuTMsG = response.Data.msg.lower()
                except Exception: continue

                seen_now = time.time()
                for seen_uid, seen_time in list(last_chat_seen.items()):
                    if seen_now - seen_time > 600:
                        del last_chat_seen[seen_uid]
                if len(last_chat_seen) >= 2000 and str(uid) not in last_chat_seen:
                    oldest_uid = min(last_chat_seen, key=last_chat_seen.get)
                    del last_chat_seen[oldest_uid]
                last_chat_seen[str(uid)] = seen_now
                command_text = inPuTMsG.strip()
                command = command_text.split()[0].split("@")[0].lower() if command_text else ""

                # =================== CENTRAL SECURITY GATE ===================
                banned_users = load_bans()
                is_user_admin = is_admin(uid)
                is_cmd = inPuTMsG.startswith("/") or inPuTMsG.startswith("@")

                # 1. Ban Check
                if str(uid) in banned_users and not is_user_admin:
                    if is_cmd:
                        banned_name = getattr(getattr(response.Data, "Details", None), "Nickname", "") or "User"
                        banned_msg = f"""[B][C][FF0000]╔═『 ACCESS DENIED 』═╗

[FFFFFF]Sorry {banned_name}, you are banned from using this bot.

[FF69B4]Your access has been permanently restricted

[FFFF00]Please contact Buddy for support

[00FFFF]If this is a mistake, request unban

[FF2EEE]─── ⋆⋅ RESTRICTED ⋅⋆ ───"""
                        await safe_send_message(XX, banned_msg, uid, chat_id, key, iv)
                    continue

                # 2. Admin Mode Check
                if admin_mode and is_cmd and not is_user_admin:
                    requester_name = getattr(getattr(response.Data, "Details", None), "Nickname", "") or "User"
                    requester_msg = f"""[B][C][FF0000]╔═『 ACCESS BLOCKED 』═╗

[FFFFFF]Hey {requester_name}, Admin Mode is currently enabled

[FF0000]You cannot use commands right now
[FFFF00]Only Admins have access

[00FFFF]Command blocked untill Admin Mode is disabled

[FF2EEE]─── ⋆⋅ RESTRICTED ⋅⋆ ───"""
                    await safe_send_message(XX, requester_msg, uid, chat_id, key, iv)
                    continue

                # 3. Expiry Check
                if is_expired() and is_cmd and not is_user_admin:
                    expire_msg = """[C][B][FF4D6D]╭┈ • ┈୨ BOT EXPIRED ୧┈ • ┈╮

[FFFFFF]This bot subscription has expired!
[FFFF00]Please contact Admin to renew.

[00FFFF]Thank you for using our service ♡

[FF2EEE]╰┈ • ┈୨ EXPIRED ୧┈ • ┈╯"""
                    await safe_send_message(XX, expire_msg, uid, chat_id, key, iv)
                    continue

                if not bot_enabled and command not in (
                    "/on", "/off", "/adon", "/adoff", "/adminmode",
                    "/accept", "/reject", "/admin", "/help", "/BUDDY", "help",
                ):
                    continue

                # ═══════════════════════════════════════════════
                # /help & /BUDDY (FIXED TIMING)
                # ═══════════════════════════════════════════════
                if command in ("/help", "help", "/buddy", "buddy") or command_text == "bot help":
                    sender_name = getattr(getattr(response.Data, "Details", None), "Nickname", "") or "User"
                    header = f"[b][c]{get_random_color()}Hey {sender_name} Welcome To BUDDY MEOW's BOT"
                    await safe_send_message(XX, header, uid, chat_id, key, iv)
                    await asyncio.sleep(0.2)
                    pages = get_help_pages()
                    for page_text in pages:
                        try: await safe_send_message(XX, page_text, uid, chat_id, key, iv)
                        except Exception as e: print(f"Help err: {e}")
                        await asyncio.sleep(0.2)

                # =================== /STATUS (CACHE-BASED WITH LEADER INFO) ===================
                elif inPuTMsG.strip().startswith('/status'):
                    parts = inPuTMsG.strip().split()
                    if len(parts) < 2:
                        error_msg = f"[B][C][FF0000]❌ Usage: /status (player_uid)\nExample: /status 238🤫722🤫72🤫71\n"
                        await safe_send_message(XX, error_msg, uid, chat_id, key, iv)
                    else:
                        target_uid = parts[1].strip()
                        clear_cache_entry(target_uid)
                        requester_name = getattr(getattr(response.Data, "Details", None), "Nickname", "") or "User"
                        initial_msg = f"[B][C][FFFF00]🔍 Checking status of {fix_num(target_uid)}...\n [87ceeb]Requested by: {requester_name}"
                        await safe_send_message(XX, initial_msg, uid, chat_id, key, iv)
                        try:
                            status_packet = await createpacketinfo(target_uid, key, iv)
                            if not status_packet:
                                await safe_send_message(XX, "[B][C][FF0000]❌ Failed to create status packet!\n", uid, chat_id, key, iv)
                            else:
                                await SEndPacKeT(whisper_writer, online_writer, 'OnLine', status_packet)
                                max_retries = 12
                                response_received = False
                                status_sent = False
                                for attempt in range(max_retries):
                                    cache_data = load_from_cache(target_uid)
                                    if cache_data:
                                        response_received = True
                                        if not status_sent:
                                            status_sent = True
                                            status_str = cache_data.get('status', 'OFFLINE')
                                            status_msg = f"[B][C][FFFF00]📊 PLAYER STATUS\n────────────────\n👤 UID: {fix_num(target_uid)}\n📊 Status: {status_str}\n"
                                            if "IN ROOM" in status_str:
                                                if 'room_id' in cache_data:
                                                    status_msg += f"🏠 Room ID: {fix_num(cache_data['room_id'])}\n💡 Use: /room {target_uid}\n"
                                                    await safe_send_message(XX, status_msg, uid, chat_id, key, iv)
                                                    await safe_send_message(XX, f"{fix_num(cache_data['room_id'])}", uid, chat_id, key, iv)
                                                else:
                                                    status_msg += "🏠 Room ID: Not available\n"
                                                    await safe_send_message(XX, status_msg, uid, chat_id, key, iv)
                                            elif "INSQUAD" in status_str:
                                                leader_id_val = cache_data.get('leader_id', target_uid)
                                                status_msg = f"[B][C][FFFF00]📊 PLAYER STATUS\n────────────────\n👤 UID: {fix_num(target_uid)}\n📊 Status: {status_str}\n👑 Leader: {fix_num(leader_id_val)}\n"
                                                await safe_send_message(XX, status_msg, uid, chat_id, key, iv)
                                                await safe_send_message(XX, f"{fix_num(leader_id_val)}", uid, chat_id, key, iv)
                                                try:
                                                    leader_uid = str(leader_id_val)
                                                    info_result = get_player_info(leader_uid)
                                                    info_ok = isinstance(info_result, dict) and "basic_info" in info_result
                                                    if info_ok and isinstance(info_result, dict) and "basic_info" in info_result:
                                                        for leader_info_msg in build_new_player_info_messages(
                                                            info_result, "LEADER INFO"
                                                        ):
                                                            await safe_send_message(
                                                                XX, leader_info_msg, uid, chat_id, key, iv
                                                            )
                                                    elif False:
                                                        basic_info = info_result.get("basic_info", {})
                                                        activity_info = info_result.get("basic_info", {})
                                                        guild_info = info_result.get("clan_basic_info", {})
                                                        leader_info = info_result.get("captain_basic_info", {})
                                                        if not isinstance(basic_info, dict):
                                                            basic_info = {}
                                                        if not isinstance(activity_info, dict):
                                                            activity_info = {}
                                                        if not isinstance(guild_info, dict):
                                                            guild_info = {}
                                                        if not isinstance(leader_info, dict):
                                                            leader_info = {}

                                                        def leader_value(section, key, default="N/A"):
                                                            value = section.get(key, default)
                                                            return default if value is None or value == "" else value

                                                        leader_info_msg = f"""[B][C][00FFCC]╔═『 LEADER INFO 』═╗

[C][00BFFF]Name        : [FFFFFF]{xMsGFixinG(leader_value(basic_info, 'Name'))}
[C][00BFFF]UID         : [FFFFFF]{xMsGFixinG(leader_value(basic_info, 'UID'))}
[C][00BFFF]Level       : [FFFFFF]{xMsGFixinG(leader_value(basic_info, 'Level'))}
[C][00BFFF]Likes       : [FFFFFF]{xMsGFixinG(leader_value(basic_info, 'Likes'))}
[C][00BFFF]Bio :
[FFFFFF]{(leader_value(basic_info, 'Signature'))}

[C][00BFFF]Guild Name  : [FFFFFF]{xMsGFixinG(leader_value(guild_info, 'GuildName', 'No Guild'))}
[C][00BFFF]Guild ID    : [FFFFFF]{xMsGFixinG(leader_value(guild_info, 'GuildID'))}
[C][00BFFF]Guild Level : [FFFFFF]{xMsGFixinG(leader_value(guild_info, 'GuildLevel'))}
[C][00BFFF]Guild Owner : [FFFFFF]{xMsGFixinG(leader_value(leader_info, 'Name'))}
[C][00BFFF]Guild Members: [FFFFFF]{xMsGFixinG(leader_value(guild_info, 'LiveMembers'))}/{xMsGFixinG(leader_value(guild_info, 'MaxMembers'))}

[00FFCC]╚══════════════╝"""

                                                        await safe_send_message(XX, leader_info_msg, uid, chat_id, key, iv)
                                                    else:
                                                        detail = (
                                                            info_result
                                                            if not info_ok
                                                            else info_result.get("message", "Invalid API response")
                                                        )
                                                        print(f"❌ Leader info lookup failed for {leader_uid}: {detail}")
                                                        await safe_send_message(
                                                            XX,
                                                            "[B][C][FF0000]❌ Could not fetch leader information from the player-info API.",
                                                            uid, chat_id, key, iv,
                                                        )
                                                except Exception as info_err:
                                                    print(f"❌ Leader info error: {info_err}")
                                            elif "OFFLINE" in status_str:
                                                status_msg += "🔴 Player is offline\n"
                                                await safe_send_message(XX, status_msg, uid, chat_id, key, iv)
                                            elif "INGAME" in status_str:
                                                status_msg += "🎮 Player is in a match\n"
                                                await safe_send_message(XX, status_msg, uid, chat_id, key, iv)
                                            elif "SOLO" in status_str:
                                                status_msg += "👤 Player is solo\n"
                                                await safe_send_message(XX, status_msg, uid, chat_id, key, iv)
                                            else:
                                                await safe_send_message(XX, status_msg, uid, chat_id, key, iv)
                                        break
                                    await asyncio.sleep(0.5)
                                if not response_received:
                                    error_msg = f"""[B][C][FF0000]❌ STATUS CHECK FAILED
────────────────
👤 UID: {fix_num(target_uid)}
📛 No response from server
────────────────
💡 Possible issues:
• Player is offline
• Server is busy
• Try again in 10 seconds
"""
                                    await safe_send_message(XX, error_msg, uid, chat_id, key, iv)
                        except Exception as e:
                            await safe_send_message(XX, f"[B][C][FF0000]❌ Error: {str(e)[:50]}\n", uid, chat_id, key, iv)

                # =================== 2️⃣ SOCIAL MEDIA INFO ===================
                elif inPuTMsG.strip().startswith('/tt'):
                    parts = inPuTMsG.strip().split()
                    if len(parts) != 2:
                        error_msg = f"[B][C][FF0000]❌ ERROR! Usage: /tt <username>\nExample: /tt buddy_meow\n"
                        await safe_send_message(XX, error_msg, uid, chat_id, key, iv)
                    else:
                        target_username = parts[1]
                        initial_message = f"[B][C]{get_random_color()}Fetching TikTok info for {target_username}..."
                        await safe_send_message(XX, initial_message, uid, chat_id, key, iv)
                        result = send_tiktok_info(target_username)
                        if isinstance(result, tuple):
                            msg1, msg2 = result
                            await safe_send_message(XX, msg1, uid, chat_id, key, iv)
                            await asyncio.sleep(0.4)
                            await safe_send_message(XX, msg2, uid, chat_id, key, iv)
                        else:
                            await safe_send_message(XX, result, uid, chat_id, key, iv)

                elif inPuTMsG.strip().startswith('/yt'):
                    target_channel = inPuTMsG.strip()[4:].strip()
                    if not target_channel:
                        error_msg = f"[B][C][FF0000]❌ ERROR! Usage: /yt <channel>\nExample: /yt BUDDY MEOW\n"
                        await safe_send_message(XX, error_msg, uid, chat_id, key, iv)
                    else:
                        initial_message = f"[B][C]{get_random_color()}\nFetching YouTube info for {target_channel}...\n"
                        await safe_send_message(XX, initial_message, uid, chat_id, key, iv)
                        await send_youtube_info(target_channel, XX, uid, chat_id, key, iv)

                elif inPuTMsG.strip().startswith('/ig') or command_text.startswith('/ig'):
                    parts = inPuTMsG.strip().split()
                    if len(parts) != 2:
                        error_msg = f"[B][C][FF0000]❌ ERROR! Usage: /ig <username>\nExample: /ig hey._.buddyyy\n"
                        await safe_send_message(XX, error_msg, uid, chat_id, key, iv)
                    else:
                        target_username = parts[1]
                        initial_message = f"[B][C]{get_random_color()}\nFetching Instagram info for {target_username}...\n"
                        await safe_send_message(XX, initial_message, uid, chat_id, key, iv)
                        loop = asyncio.get_event_loop()
                        with ThreadPoolExecutor() as executor:
                            insta_result = await loop.run_in_executor(executor, send_insta_info, target_username)
                        await safe_send_message(XX, insta_result, uid, chat_id, key, iv)

                # =================== 3️⃣ BADGE COMMANDS ===================
                elif inPuTMsG.strip().startswith(('/s1', '/s2', '/s3', '/s4', '/s5', '/s6', '/s7', '/s8')):# /s1 /s2 /s3 /s4 /s5 /s6 /s7 /s8
                    cmd = inPuTMsG.strip().split()[0][1:].lower()
                    for _ in range(10):
                        await handle_badge_command(cmd, inPuTMsG, uid, chat_id, key, iv, region, XX)
                        await asyncio.sleep(0.2)

                elif inPuTMsG.strip().startswith('/spm_badge'):
                    parts = inPuTMsG.strip().split()
                    if len(parts) < 2:
                        error_msg = f"[B][C][FF0000]❌ Usage: /spm_badge (uid)\nExample: /spm_badge 238🤫722🤫72🤫71\n"
                        await safe_send_message(XX, error_msg, uid, chat_id, key, iv)
                    else:
                        target_uid = parts[1].strip()
                        if spam_request_task and not spam_request_task.done():
                            spam_request_running = False
                            spam_request_task.cancel()
                            await asyncio.sleep(0.3)
                        spam_request_running = True
                        start_msg = f"""[B][C][00FF00]⚡ ALL BADGES SPAM STARTED!
🎯 Target: {xMsGFixinG(target_uid)}
🏷️ Badges: s1, s2, s3, s4, s5, s6, s7, s8
🔄 Mode: 5 loops sequence
🛑 Stop: /stop_badge
"""
                        await safe_send_message(XX, start_msg, uid, chat_id, key, iv)
                        count = 0
                        try:
                            badge_commands = ['s1', 's2', 's3', 's4', 's5', 's6', 's7', 's8']
                            for loop_i in range(5):
                                if not spam_request_running: break
                                for b_cmd in badge_commands:
                                    if not spam_request_running: break
                                    fake_cmd = f"/{b_cmd} {target_uid}"
                                    await handle_badge_command(b_cmd, fake_cmd, uid, chat_id, key, iv, region, XX)
                                    count += 1
                                    await asyncio.sleep(0.3)
                            success_msg = f"""[B][C][00FF00]✅ SPAM COMPLETED!

🎯 Target: {xMsGFixinG(target_uid)}
✅ Total Requests: {count}
⚡ Status: Done!
"""
                            await safe_send_message(XX, success_msg, uid, chat_id, key, iv)
                        except Exception as e:
                            await safe_send_message(XX, f"[B][C][FF0000]❌ SPAM ERROR!\n[FFFFFF]{str(e)[:100]}", uid, chat_id, key, iv)
                        finally:
                            spam_request_running = False

                elif inPuTMsG.strip() == "/stop_badge":
                    spam_request_running = False
                    if spam_request_task and not spam_request_task.done():
                        spam_request_task.cancel()
                    stop_msg = "[B][C][00FF00]✅ Spam request stopped successfully!"
                    await safe_send_message(XX, stop_msg, uid, chat_id, key, iv)

                # =================== 4️⃣ SPAM INVITE ===================
                elif inPuTMsG.strip().startswith('/spm_inv'):
                    parts = inPuTMsG.strip().split()
                    if len(parts) < 2:
                        error_msg = f"[B][C][FF0000]❌ Usage: /spm_inv (uid)\nExample: /spm_inv 238🤫722🤫72🤫71\n"
                        await safe_send_message(XX, error_msg, uid, chat_id, key, iv)
                    else:
                        target_uid = parts[1].strip()
                        if spam_request_task and not spam_request_task.done():
                            spam_request_running = False
                            spam_request_task.cancel()
                            await asyncio.sleep(0.5)
                        spam_request_running = True
                        spam_request_task = asyncio.create_task(spam_request_loop_with_cosmetics(target_uid, key, iv, region))
                        success_msg = f"""[B][C][00FF00]✅ COSMETIC SPAM STARTED!
🎯 Target: {xMsGFixinG(target_uid)}
📦 Requests: 30
🎭 Features: V-Badges + Cosmetics
⚡ Each invite has different cosmetics!
"""
                        await safe_send_message(XX, success_msg, uid, chat_id, key, iv)

                elif inPuTMsG.strip() == '/sspm':
                    if spam_request_task and not spam_request_task.done():
                        spam_request_running = False
                        spam_request_task.cancel()
                        success_msg = "[B][C][00FF00]✅ SUCCESS! Spam request stopped successfully!\n"
                        await safe_send_message(XX, success_msg, uid, chat_id, key, iv)
                    else:
                        error_msg = "[B][C][FF0000]❌ ERROR! No active spam request to stop!\n"
                        await safe_send_message(XX, error_msg, uid, chat_id, key, iv)

                # ═══════════════════════════════════════════════════════════════
                # 🎭 EMOTE COMMANDS (MERGED & CONFLICT-FREE)
                # ═══════════════════════════════════════════════════════════════

                # ─── /e & /play (Merged main.py /play + bot_core /e) ───
                elif inPuTMsG.strip().startswith('/e ') or inPuTMsG.strip().startswith('/play') or inPuTMsG.strip() == '/e':
                    parts = inPuTMsG.strip().split()
                    try:
                        # Emote system list / help
                        if len(parts) == 1 or (len(parts) == 2 and parts[1].lower() == 'list'):
                            emote_list_msg = f"[B][C][00FF00]🎭 EMOTE SYSTEM\n"
                            emote_list_msg += f"[FFFFFF]────────────────\n"
                            emote_list_msg += f"[00FF00]📊 STATS:\n"
                            emote_list_msg += f"[FFFFFF]• Number emotes: {len(GENERAL_EMOTES_MAP)}\n"
                            emote_list_msg += f"[FFFFFF]• Named emotes: {len(NAME_EMOTES)} names\n"
                            emote_list_msg += f"[FFFFFF]────────────────\n"
                            emote_list_msg += f"[00FF00]🎯 USAGE:\n"
                            emote_list_msg += f"[FFFFFF]/e [number/name] → Send to yourself\n"
                            emote_list_msg += f"[FFFFFF]/e [uid] [number/name] → Send to UID\n"
                            emote_list_msg += f"[FFFFFF]/e [uid1] [uid2] [number/name] → Multi-target\n"
                            emote_list_msg += f"[FFFFFF]────────────────\n"
                            emote_list_msg += f"[00FF00]🔥 POPULAR NAMES:\n"
                            popular_names = ["ak", "m60", "p90", "scar", "famas", "heart", "love", "dance", "hello", "money", "ring"]
                            line = ""
                            for name in popular_names:
                                if name.lower() in NAME_EMOTES:
                                    line += f"[00FF00]{name}[FFFFFF], "
                            if line:
                                emote_list_msg += line.rstrip(", ") + "\n"
                            emote_list_msg += f"[FFFFFF]────────────────\n"
                            emote_list_msg += f"[00FF00]📖 EXAMPLES:\n"
                            emote_list_msg += f"[FFFFFF]/e ak → Send AK emote to yourself\n"
                            emote_list_msg += f"[FFFFFF]/e {uid} heart → Send ❤️ to UID\n"
                            emote_list_msg += f"[FFFFFF]/e {uid} 1 → Send emote #1 to UID\n"
                            emote_list_msg += f"[FFFFFF]/e ring → Send ring emote to yourself\n"
                            emote_list_msg += f"[FFFFFF]/e list names → Show all named emotes\n"
                            await safe_send_message(XX, emote_list_msg, uid, chat_id, key, iv)
                            continue

                        # Detailed named emote list
                        if len(parts) == 2 and parts[1].lower() == 'names':
                            all_names = sorted(NAME_EMOTES.keys())
                            names_msg = f"[B][C][00FF00]📝 ALL NAMED EMOTES ({len(all_names)}):\n[FFFFFF]────────────────\n"
                            for i in range(0, min(len(all_names), 30), 5):
                                group = all_names[i:i+5]
                                names_msg += f"[FFFFFF]{' | '.join(group)}\n"
                            if len(all_names) > 30:
                                names_msg += f"[FFFFFF]... and {len(all_names) - 30} more\n"
                            await safe_send_message(XX, names_msg, uid, chat_id, key, iv)
                            continue

                        if len(parts) < 2:
                            continue

                        last = parts[-1].lower()

                        # Resolve via unified lookup
                        emote_id, display = resolve_emote(last)
                        if not emote_id:
                            await safe_send_message(
                                XX,
                                f"[B][C][FF0000]❌ Emote '{last}' not found\n"
                                f"[FFFFFF]Use name (ak, heart) or number or 9-digit ID\n"
                                f"Use /e list to view popular emotes",
                                uid, chat_id, key, iv,
                            )
                            continue

                        # Determine targets
                        target_uids = []
                        if len(parts) == 2:
                            target_uids.append(int(uid))         # /e ak       → self
                        else:
                            for p in parts[1:-1]:                # /e uid1 uid2 ak
                                if p.isdigit():
                                    target_uids.append(int(p))

                        if not target_uids:
                            target_uids = [int(uid)]

                        # Send
                        ok = 0
                        for t in target_uids:
                            try:
                                H = await Emote_k(t, int(emote_id), key, iv, region)
                                await SEndPacKeT(whisper_writer, online_writer, 'OnLine', H)
                                ok += 1
                                await asyncio.sleep(0.1)
                            except Exception as e:
                                print(f"[{display}] send error → {t}: {e}")

                        await safe_send_message(
                            XX,
                            f"[B][C][00FF00]✅ Emote '{display}' → {ok}/{len(target_uids)} sent",
                            uid, chat_id, key, iv,
                        )

                    except Exception as e:
                        print(f"/e cmd error: {e}")
                        await safe_send_message(
                            XX,
                            f"[B][C][FF0000]❌ Error: {str(e)[:60]}",
                            uid, chat_id, key, iv,
                        )

                # ─── !e (Direct/UID Emote - Renamed from main.py's /emote) ───
                elif inPuTMsG.strip().startswith('!e ') or inPuTMsG.strip().startswith('/emote'):
                    parts = inPuTMsG.strip().split()
                    try:
                        if len(parts) < 3:
                            await safe_send_message(
                                XX,
                                "[B][C][FF0000]Usage:\n"
                                "!e <uid> <emoteID>\n"
                                "!e <uid1> <uid2> <emoteID>\n"
                                "[FFFFFF]Example: !e 123🤔456🤔78🤔9 90🤔900🤔00🤔63",
                                uid, chat_id, key, iv,
                            )
                            continue

                        # Parse target UIDs
                        target_uids = []
                        for p in parts[1:-1]:
                            if p.isdigit():
                                target_uids.append(int(p))
                        if not target_uids:
                            target_uids = [int(uid)]

                        # Parse emote — accepts name, number, or direct ID
                        last = parts[-1].lower()
                        emote_id, display = resolve_emote(last)
                        if not emote_id:
                            await safe_send_message(
                                XX,
                                f"[B][C][FF0000]❌ Invalid emote '{last}'",
                                uid, chat_id, key, iv,
                            )
                            continue

                        # Send
                        ok = 0
                        for t in target_uids:
                            try:
                                H = await Emote_k(t, int(emote_id), key, iv, region)
                                await SEndPacKeT(whisper_writer, online_writer, 'OnLine', H)
                                ok += 1
                                await asyncio.sleep(0.05)
                            except Exception as e:
                                print(f"!e send error → {t}: {e}")

                        await safe_send_message(
                            XX,
                            f"[B][C][00FF00]✅ !e → '{display}' sent to {ok}/{len(target_uids)}",
                            uid, chat_id, key, iv,
                        )

                    except Exception as e:
                        await safe_send_message(
                            XX,
                            f"[B][C][FF0000]❌ !e error: {str(e)[:60]}",
                            uid, chat_id, key, iv,
                        )

                # ─── /me (Join squad -> Emote -> Leave) ───
                elif inPuTMsG.strip().startswith('/me '):
                    parts = inPuTMsG.strip().split()

                    if len(parts) < 3:
                        await safe_send_message(
                            XX,
                            "[B][C][FF0000]Usage:\n"
                            "/me <team_code> <emote>\n"
                            "/me <team_code> <uid> <emote>\n"
                            "[FFFFFF]Example: /me ABC123 ak\n"
                            f"/me ABC123 {uid} heart",
                            uid, chat_id, key, iv,
                        )
                        continue

                    team_code = parts[1]
                    emote_key = parts[-1].lower()

                    # Targets
                    target_uids = []
                    if len(parts) == 3:
                        target_uids.append(int(uid))                 # /me CODE ak → self
                    else:
                        for p in parts[2:-1]:                        # /me CODE uid emote
                            if p.isdigit():
                                target_uids.append(int(p))

                    if not target_uids:
                        target_uids = [int(uid)]

                    # Resolve emote
                    emote_id, display = resolve_emote(emote_key)
                    if not emote_id:
                        await safe_send_message(
                            XX,
                            f"[B][C][FF0000]❌ Invalid emote '{emote_key}'",
                            uid, chat_id, key, iv,
                        )
                        continue

                    await safe_send_message(
                        XX,
                        f"[B][C]{get_random_color()}\n⏳ Joining {team_code} for '{display}'...",
                        uid, chat_id, key, iv,
                    )

                    try:
                        # Step 1 — Join
                        join_packet = await JoinSq_original(team_code, key, iv)
                        await SEndPacKeT(whisper_writer, online_writer, 'OnLine', join_packet)
                        await asyncio.sleep(0.2)

                        # Step 2 — Emote to all targets
                        for t_uid in target_uids:
                            try:
                                H = await Emote_k(int(t_uid), int(emote_id), key, iv, region)
                                await SEndPacKeT(whisper_writer, online_writer, 'OnLine', H)
                                await asyncio.sleep(0.1)
                            except Exception as e:
                                print(f"/me emote error → {t_uid}: {e}")

                        # Step 3 — Leave
                        leave_packet = await ExiT(None, key, iv)
                        await SEndPacKeT(whisper_writer, online_writer, 'OnLine', leave_packet)

                        await safe_send_message(
                            XX,
                            f"[B][C][00FF00]✅ Joined {team_code}, sent '{display}', left!",
                            uid, chat_id, key, iv,
                        )

                    except Exception as e:
                        print(f"/me failed: {e}")
                        await safe_send_message(
                            XX,
                            f"[B][C][FF0000]❌ /me failed: {str(e)[:60]}",
                            uid, chat_id, key, iv,
                        )

                # ─── /fast (Fast Emote Spam - 25x) ───
                elif inPuTMsG.strip().startswith('/fast'):
                    print('Processing fast emote spam in any chat type')
                    parts = inPuTMsG.strip().split()

                    try:
                        uids_fast = []
                        emote_key = None

                        if len(parts) == 2:
                            uids_fast = [int(uid)]
                            emote_key = parts[1].lower()
                        elif len(parts) >= 3:
                            emote_key = parts[-1].lower()
                            for part in parts[1:-1]:
                                if part.isdigit():
                                    if len(uids_fast) < 5:
                                        uids_fast.append(int(part))
                            if len(parts) == 3 and parts[1].isdigit() and len(parts[1]) > 5:
                                uids_fast = [int(parts[1])]
                                emote_key = parts[2].lower()
                        else:
                            raise ValueError("Invalid format")

                        if not uids_fast:
                            uids_fast = [int(uid)]

                        # Emote resolve
                        emote_id, display = resolve_emote(emote_key)
                        if not emote_id:
                            error_msg = f"""[B][C][FF0000]❌ INVALID EMOTE!
[FFFFFF]Use number / name / direct ID"""
                            await safe_send_message(XX, error_msg, uid, chat_id, key, iv)
                            continue

                        # Stop old task
                        if fast_spam_task and not fast_spam_task.done():
                            fast_spam_running = False
                            fast_spam_task.cancel()

                        fast_spam_running = True
                        fast_spam_task = asyncio.create_task(
                            fast_emote_spam(uids_fast, emote_id, key, iv, region)
                        )

                        success_msg = f"""[B][C][00FF00]✅ FAST EMOTE STARTED!

[FFFFFF]────────────────
Targets: {make_circled_num(len(uids_fast))} / 5 max
Emote: {display} ({make_circled_num(emote_id)})
Mode: Multi Target Fast
Spam Count: 25x each
[FFFFFF]────────────────"""

                        await safe_send_message(XX, success_msg, uid, chat_id, key, iv)

                    except Exception as e:
                        print("FAST ERROR:", e)
                        await safe_send_message(
                            XX,
                            f"[B][C][FF0000]❌ ERROR: {str(e)[:60]}",
                            uid, chat_id, key, iv
                        )

                # ─── /p (Custom Times Emote Spam) ───
                elif inPuTMsG.strip().startswith('/p ') and not inPuTMsG.strip().startswith('/pick'):
                    print('Processing custom emote spam in any chat type')
                    parts = inPuTMsG.strip().split()

                    if len(parts) < 4:
                        error_msg = f"[B][C][FF0000]❌ ERROR! Usage: /p (uid) (emote) (times)\nExample: /p {uid} 909000001 10\n"
                        await safe_send_message(XX, error_msg, uid, chat_id, key, iv)
                    else:
                        try:
                            target_uid = parts[1]
                            emote_input = parts[2]
                            times = int(parts[3])

                            emote_id, display = resolve_emote(emote_input)
                            if not emote_id:
                                if emote_input.isdigit():
                                    emote_id = int(emote_input)
                                    display = emote_input
                                else:
                                    await safe_send_message(XX, f"[B][C][FF0000]❌ Invalid emote: '{emote_input}'", uid, chat_id, key, iv)
                                    continue

                            if times <= 0:
                                error_msg = f"[B][C][FF0000]❌ ERROR! Times must be greater than 0!\n"
                                await safe_send_message(XX, error_msg, uid, chat_id, key, iv)
                            elif times > 1000:
                                error_msg = f"[B][C][FF0000]❌ ERROR! Maximum 1000 times allowed for safety!\n"
                                await safe_send_message(XX, error_msg, uid, chat_id, key, iv)
                            else:
                                # Stop old task
                                if custom_spam_task and not custom_spam_task.done():
                                    custom_spam_running = False
                                    custom_spam_task.cancel()

                                custom_spam_running = True
                                custom_spam_task = asyncio.create_task(
                                    custom_emote_spam(target_uid, emote_id, times, key, iv, region)
                                )

                                success_msg = (
                                    f"[B][C][00FF00]✅ SUCCESS! Custom emote spam started!\n"
                                    f"Target: {xMsGFixinG(target_uid)}\n"
                                    f"Emote: {display}\n"
                                    f"Times: {times}\n"
                                )
                                await safe_send_message(XX, success_msg, uid, chat_id, key, iv)

                        except ValueError:
                            error_msg = f"[B][C][FF0000]❌ ERROR! Invalid number format! Usage: /p (uid) (emote) (times)\n"
                            await safe_send_message(XX, error_msg, uid, chat_id, key, iv)
                        except Exception as e:
                            error_msg = f"[B][C][FF0000]❌ ERROR! {str(e)}\n"
                            await safe_send_message(XX, error_msg, uid, chat_id, key, iv)

                # ═══════════════════════════════════════════════════════════════
                # ⚡ EVO COMMANDS
                # ═══════════════════════════════════════════════════════════════

                elif inPuTMsG.strip().lower() == "/evolist":
                    print(f"⚡ EVO LIST Command: {inPuTMsG}")

                    evo_list = f"""[B][C][00FFCC]╔══⚡ EVO LIST ══╗

[FFFFFF]1  • AK47
[FFFFFF]2  • SCAR
[FFFFFF]3  • MP40
[FFFFFF]4  • XM8
[FFFFFF]5  • UMP
[FFFFFF]6  • M1014
[FFFFFF]7  • M4A1
[FFFFFF]8  • MP5
[FFFFFF]9  • M1887
[FFFFFF]10 • AN94
[FFFFFF]11 • FAMAS
[FFFFFF]12 • EVO FIST
[FFFFFF]13 • THOMPSON
[FFFFFF]14 • G18
[FFFFFF]15 • M1014 2.0
[FFFFFF]16 • MP40 2.0
[FFFFFF]17 • GROZA
[FFFFFF]18 • WOODPECKER
[FFFFFF]19 • PARAFAL
[FFFFFF]20 • P90
[FFFFFF]21 • M60
[FFFFFF]22 • AUG
[FFFFFF]23 • AWM

[00FFCC]╠═══════════════╣

[FFD700]🎯 Target UID:
[FFFFFF]/evo <uid> <number>

[FFD700]⚡ Fast UID:
[FFFFFF]/evo_fast <uid> <number>

[FFD700]👑 Owner:
[FFFFFF]Buddy Meow

[00FFCC]╚═══════════════╝"""
                    await safe_send_message(XX, evo_list, uid, chat_id, key, iv)
                    continue

                elif inPuTMsG.strip().startswith('/evo ') and not (inPuTMsG.strip().startswith('/evo_fast') or inPuTMsG.strip().startswith('/evo_c') or inPuTMsG.strip().startswith('/evos')):
                    print('Processing evo command')
                    parts = inPuTMsG.strip().split()

                    uids_evo = []
                    evo_number = None

                    for part in parts[1:]:
                        if part.isdigit():
                            num = int(part)
                            if 1 <= num <= 23 and evo_number is None:
                                evo_number = num
                            else:
                                uids_evo.append(num)
                        else:
                            lower_part = part.lower().replace(" ", "").replace("_", "")
                            for evo_num, evo_name in evo_names.items():
                                clean_name_e = evo_name.lower().replace(" ", "").replace("_", "")
                                if lower_part == clean_name_e:
                                    evo_number = evo_num
                                    break

                    if evo_number is None:
                        await safe_send_message(XX, "[B][C][FF0000]Usage: /evo [uid] <1-22>\nUse /evolist to see all evo weapons", uid, chat_id, key, iv)
                        continue

                    if not uids_evo:
                        uids_evo.append(int(uid))

                    success, result_msg = await evo_emote_spam(uids_evo, evo_number, key, iv, region)

                    evo_id = evo_emotes[evo_number]
                    evo_name = evo_names.get(evo_number, "Unknown Evo")

                    success_msg = f"""[B][C][00FF00]╔═『 EVO SENT 』═╗

[FF69B4]Evolution sent successfully 💖

[FFFFFF]Targets:
[00FF00]{make_circled_num(len(uids_evo))}

[FFFFFF]Evo Name:
[FFFF00]{evo_name}

[FFFFFF]Evo ID:
[00FFFF]{make_circled_num(evo_id)}

[FF69B4]Target boosted with evo power ⚡

[FF2EEE]⊹₊˚‧︵‿︵‧˚₊⊹"""

                    await safe_send_message(XX, success_msg, uid, chat_id, key, iv)

                elif inPuTMsG.strip().startswith('/evo_fast'):
                    print('Processing evo_fast command')
                    parts = inPuTMsG.strip().split()

                    uids_evo = []
                    evo_number = None

                    for part in parts[1:]:
                        if part.isdigit():
                            num = int(part)
                            if 1 <= num <= 23 and evo_number is None:
                                evo_number = num
                            else:
                                uids_evo.append(num)
                        else:
                            lower_part = part.lower().replace(" ", "").replace("_", "")
                            for evo_num, evo_name in evo_names.items():
                                clean_name_e = evo_name.lower().replace(" ", "").replace("_", "")
                                if lower_part == clean_name_e:
                                    evo_number = evo_num
                                    break

                    if evo_number is None:
                        await safe_send_message(XX, "[B][C][FF0000]Usage: /evo_fast [uid] <1-21>\nUse /evolist to see numbers", uid, chat_id, key, iv)
                        continue

                    if not uids_evo:
                        uids_evo.append(int(uid))

                    if evo_fast_spam_task and not evo_fast_spam_task.done():
                        evo_fast_spam_running = False
                        evo_fast_spam_task.cancel()
                        await asyncio.sleep(0.3)

                    evo_fast_spam_running = True
                    evo_fast_spam_task = asyncio.create_task(
                        evo_fast_emote_spam(uids_evo, evo_number, key, iv, region)
                    )

                    evo_id = EMOTE_MAP[evo_number]
                    evo_name = evo_names.get(evo_number, "Unknown Evo")

                    evofast_msg = f"""[B][C][00FF00]╔═『 EVO FAST STARTED 』═╗

[FF69B4]Fast Evolution Activated ⚡

[FFFFFF]Targets:
[00FF00]{make_circled_num(len(uids_evo))}

[FFFFFF]Evo Name:
[FFFF00]{evo_name}

[FFFFFF]Evo ID:
[00FFFF]{make_circled_num(evo_id)}

[00FFFF]Ultra Speed Mode Enabled 🚀

[FF2EEE]⊹₊˚‧︵‿︵‧˚₊⊹"""

                    await safe_send_message(XX, evofast_msg, uid, chat_id, key, iv)

                elif inPuTMsG.strip().lower() == '/stop evo_fast':
                    print("Stopping evo_fast spam...")

                    if evo_fast_spam_task and not evo_fast_spam_task.done():
                        evo_fast_spam_running = False
                        evo_fast_spam_task.cancel()

                        success_msg = f"""[B][C][00FF00]╔═『 STOP SUCCESS 』═╗

[FF69B4]Evo Fast Spam Stopped Successfully!

[FFFFFF]Status:
[00FF00]• Task Cancelled ✔
[00FFFF]• System Idle ✔

[FF2EEE]⊹₊˚‧︵‿︵‧˚₊⊹"""
                        await safe_send_message(XX, success_msg, uid, chat_id, key, iv)
                    else:
                        error_msg = f"""[B][C][FF0000]╔═『 NO ACTIVE TASK 』═╗

[FFFFFF]❌ No evo_fast spam is running

[FF69B4]Use:
[00FF00]/evo_fast to start

[FF2EEE]⊹₊˚‧︵‿︵‧˚₊⊹"""
                        await safe_send_message(XX, error_msg, uid, chat_id, key, iv)

                elif inPuTMsG.strip().startswith('/evo_c'):
                    print('Processing evo_c command in any chat type')
                    parts = inPuTMsG.strip().split()

                    if len(parts) < 4:
                        error_msg = f"""[B][C][FF0000]╔═『 EVO CUSTOM ERROR 』═╗

[FFFFFF]˗ˏˋ » Wrong format

[FF0000]Usage:
[FFFFFF]/evo_c [uid] [EmoteNum] [time]

[FFFF00]Example:
[00FF00]/evo_c {uid} 5 10

[FF69B4]Range:
[00FFFF]{make_circled_num(1)} - {make_circled_num(21)}
[00FFFF]Time: {make_circled_num(1)} - {make_circled_num(100)}

[FF2EEE]⊹₊˚‧︵‿︵‧˚₊⊹"""
                        await safe_send_message(XX, error_msg, uid, chat_id, key, iv)
                        continue

                    uids_c = []
                    number = None
                    time_val = None

                    for part in parts[1:]:
                        if part.isdigit():
                            val = int(part)
                            if 1 <= val <= 21 and number is None:
                                number = val
                            elif 1 <= val <= 100 and time_val is None:
                                time_val = val
                            else:
                                uids_c.append(val)
                        else:
                            number = None
                            time_val = None
                            break

                    if not uids_c or number is None or time_val is None:
                        error_msg = f"""[B][C][FF0000]╔═『 INVALID INPUT 』═╗

[FFFFFF]⚠ Missing UID / EVO / TIME

[00FF00]Correct format:
[FFFFFF]/evo_c uid number time

[FFFF00]Example:
[FFFFFF]/evo_c {uid} 7 10

[FF69B4]Range:
[00FFFF]Evo {make_circled_num(1)}-{make_circled_num(21)}
[00FFFF]Time {make_circled_num(1)}-{make_circled_num(100)}

[FF2EEE]⊹₊˚‧︵‿︵‧˚₊⊹"""
                        await safe_send_message(XX, error_msg, uid, chat_id, key, iv)
                        continue

                    uids_c = uids_c[:5]

                    if number not in EMOTE_MAP:
                        error_msg = f"""[B][C][FF0000]╔═『 EVO NOT FOUND 』═╗

[FFFFFF]Invalid evo number

[FFFF00]Allowed:
[00FF00]{make_circled_num(1)} → {make_circled_num(21)}

[FF2EEE]⊹₊˚‧︵‿︵‧˚₊⊹"""
                        await safe_send_message(XX, error_msg, uid, chat_id, key, iv)
                        continue

                    if evo_custom_spam_task and not evo_custom_spam_task.done():
                        evo_custom_spam_running = False
                        evo_custom_spam_task.cancel()
                        await asyncio.sleep(0.3)

                    evo_custom_spam_running = True
                    evo_custom_spam_task = asyncio.create_task(
                        evo_custom_emote_spam(uids_c, number, time_val, key, iv, region)
                    )

                    evo_id = EMOTE_MAP[number]
                    evo_name = evo_names.get(number, "Unknown Evo")

                    success_msg = f"""[B][C][00FF00]╔═『 EVO CUSTOM ACTIVE 』═╗

[FF69B4]⚡ Custom Evolution Started!

[FFFFFF]Targets:
[00FF00]{make_circled_num(len(uids_c))}

[FFFFFF]Evo Name:
[FFFF00]{evo_name}

[FFFFFF]Repeat:
[00FFFF]{make_circled_num(time_val)} times

[FFFFFF]Evo ID:
[FF69B4]{make_circled_num(evo_id)}

[FF69B4]Mode: Custom Cycle 💫

[FF2EEE]⊹₊˚‧︵‿︵‧˚₊⊹"""

                    await safe_send_message(XX, success_msg, uid, chat_id, key, iv)

                elif inPuTMsG.strip().lower() == '/stop evo_c':
                    print("Stopping evo_custom spam...")

                    if evo_custom_spam_task and not evo_custom_spam_task.done():
                        evo_custom_spam_running = False
                        evo_custom_spam_task.cancel()

                        success_msg = f"""[B][C][00FF00]╔═『 STOP SUCCESS 』═╗

[FF69B4]💫 Evo Custom Spam Stopped Successfully!

[FFFFFF]Status:
[00FF00]• Task Cancelled ✔
[00FFFF]• System Idle ✔

[FF2EEE]⊹₊˚‧︵‿︵‧˚₊⊹"""
                        await safe_send_message(XX, success_msg, uid, chat_id, key, iv)
                    else:
                        error_msg = f"""[B][C][FF0000]╔═『 NO ACTIVE TASK 』═╗

[FFFFFF]❌ No evo_custom spam is running

[FF69B4]Use:
[00FF00]/evo_c to start

[FF2EEE]⊹₊˚‧︵‿︵‧˚₊⊹"""
                        await safe_send_message(XX, error_msg, uid, chat_id, key, iv)

                elif inPuTMsG.strip().startswith('@evos') or inPuTMsG.strip().startswith('/evos'):
                    print('Processing evo cycle start command')
                    parts = inPuTMsG.strip().split()

                    uids_cycle = []

                    if len(parts) == 1:
                        uids_cycle.append(int(uid))
                        print(f"🎯 Self target only: {uid}")
                    else:
                        for part in parts[1:]:
                            if part.isdigit():
                                t_uid = int(part)
                                if t_uid not in uids_cycle:
                                    uids_cycle.append(t_uid)
                        print(f"🎯 Custom targets: {uids_cycle}")

                    if not uids_cycle:
                        await safe_send_message(
                            XX,
                            "[B][C][FF0000]❌ No valid target UID found!",
                            uid, chat_id, key, iv
                        )
                        continue

                    uids_cycle = uids_cycle[:5]

                    try:
                        if evo_cycle_task and not evo_cycle_task.done():
                            evo_cycle_running = False
                            evo_cycle_task.cancel()
                            await asyncio.sleep(0.5)
                    except Exception as e:
                        print("EVO STOP ERROR:", e)

                    evo_cycle_running = True
                    evo_cycle_task = asyncio.create_task(
                        evo_cycle_spam(uids_cycle, key, iv, region)
                    )

                    if len(parts) == 1:
                        success_msg = f"""[B][C][00FF00]✅ EVO CYCLE STARTED!

[FFFFFF]────────────────
🎯 Target: Yourself
🎭 Mode: EVO Cycle
📦 Emotes: {make_circled_num(len(evo_emotes))}
⏰ Delay: 5 seconds
🔄 Loop: Infinite
[FFFFFF]────────────────"""
                    else:
                        success_msg = f"""[B][C][00FF00]✅ EVO CYCLE STARTED!

[FFFFFF]────────────────
🎯 Targets: {make_circled_num(len(uids_cycle))}
🎭 Mode: EVO Cycle
📦 Emotes: {make_circled_num(len(evo_emotes))}
⏰ Delay: 5 seconds
🔄 Loop: Infinite
[FFFFFF]────────────────"""

                    await safe_send_message(XX, success_msg, uid, chat_id, key, iv)
                    print(f"✅ EVO cycle started for: {uids_cycle}")

                elif inPuTMsG.strip() in ('@sevos', '/sevos'):
                    try:
                        evo_cycle_running = False
                        if evo_cycle_task and not evo_cycle_task.done():
                            evo_cycle_task.cancel()

                        await safe_send_message(
                            XX,
                            """[B][C][FF0000]🛑 EVO CYCLE STOPPED!
[FF0000]────────────────
Evolution loop disabled
All evo spam stopped
[FF0000]────────────────""",
                            uid, chat_id, key, iv
                        )
                        print("🛑 EVO cycle stopped")
                    except Exception as e:
                        print("SEVOS ERROR:", e)

                # =================== 7️⃣ ADMIN COMMANDS ===================
                elif inPuTMsG.strip() == "/adon":
                    if is_user_admin:
                        admin_mode = True
                        msg = """[B][C][00FF00]╔═『 ADMIN MODE 』═╗

[FFFFFF]˗ˏˋ » Admin Protection Enabled

[00FF00]Admin Mode Activated Successfully
[FF69B4]Only Admins can use commands now

[FFFF00]｡°⚠︎°｡ Normal users are restricted

[00FFFF]System secured successfully (｡•̀ᴗ-)✧

[FF2EEE]─── ⋆⋅ SAFE MODE ⋅⋆ ───"""
                        await safe_send_message(XX, msg, uid, chat_id, key, iv)
                    else:
                        await safe_send_message(XX, await not_admin_msg(), uid, chat_id, key, iv)

                elif inPuTMsG.strip() == "/adoff":
                    if is_user_admin:
                        admin_mode = False
                        msg = """[B][C][FFFF00]╔═『 ADMIN MODE 』═╗

[FFFFFF]˗ˏˋ » Protection Disabled

[FFFF00]⚠️ Admin Mode Deactivated Successfully
[00FF00]Everyone can use commands now

[FF69B4]Restrictions have been removed

[00FFFF]Enjoy the freedom (｡•̀ᴗ-)✧

[FF2EEE]─── ⋆⋅ PUBLIC MODE ⋅⋆ ───"""
                        await safe_send_message(XX, msg, uid, chat_id, key, iv)
                    else:
                        await safe_send_message(XX, await not_admin_msg(), uid, chat_id, key, iv)

                elif inPuTMsG.strip() == "/accept":
                    if is_user_admin:
                        auto_accept_enabled = True
                        msg = """[B][C][00FF00]╔═『 AUTO-ACCEPT 』═╗

[FFFFFF]˗ˏˋ » Auto-Accept Enabled

[00FF00]✅ Bot will now accept invites from everyone
[FFFF00]｡°⚠︎°｡ All invites will be auto-accepted

[00FFFF]System ready (｡•̀ᴗ-)✧

[FF2EEE]─── ⋆⋅ ACCEPT MODE ⋅⋆ ───"""
                        await safe_send_message(XX, msg, uid, chat_id, key, iv)
                    else:
                        await safe_send_message(XX, await not_admin_msg(), uid, chat_id, key, iv)

                elif inPuTMsG.strip() == "/reject":
                    if is_user_admin:
                        auto_accept_enabled = False
                        msg = """[B][C][FF0000]╔═『 AUTO-ACCEPT 』═╗

[FFFFFF]˗ˏˋ » Auto-Accept Disabled

[FF0000]❌ Bot will REJECT all invites
[FFFF00]｡°⚠︎°｡ Only admins can change this

[FF69B4]System locked (｡•́︿•̀｡)

[FF2EEE]─── ⋆⋅ REJECT MODE ⋅⋆ ───"""
                        await safe_send_message(XX, msg, uid, chat_id, key, iv)
                    else:
                        await safe_send_message(XX, await not_admin_msg(), uid, chat_id, key, iv)

                elif inPuTMsG.strip() == '/admins':
                    if is_user_admin:
                        try:
                            admin_data = load_admins()
                            if not admin_data:
                                msg = "📭 No admins found"
                            else:
                                msg = "[C][B][FF4500]══⚡ ADMIN LIST ⚡══\n\n"
                                for a_uid, info in admin_data.items():
                                    name = info.get("name", "Unknown").title()
                                    msg += f"[FF69B4]{name}\n"
                                    msg += f"[FFFFFF]{make_circled_num(a_uid)}\n"
                                    msg += "━━━━━━━━━━━━━━\n"
                            await safe_send_message(XX, msg, uid, chat_id, key, iv)
                        except Exception as e:
                            await safe_send_message(XX, f"[FF0000]Error: {e}", uid, chat_id, key, iv)
                    else:
                        await safe_send_message(XX, await not_admin_msg(), uid, chat_id, key, iv)

                elif inPuTMsG.strip() in ('/clear', '/clearadmin', '/clearadmins'):
                    if is_creator(uid):
                        save_admins({})
                        await safe_send_message(XX, "[B][C][00FF00]Additional admins cleared. Creator access is unchanged.", uid, chat_id, key, iv)
                    else:
                        await safe_send_message(XX, "[B][C][FF0000]Only the creator can clear admins.", uid, chat_id, key, iv)

                elif inPuTMsG.startswith('/add ') or inPuTMsG.startswith('/addadmin '):
                    if is_user_admin:
                        try:
                            parts = inPuTMsG.split()
                            if len(parts) < 3:
                                msg = "[B][C][FF0000]❌ Format: /add <uid> <name>"
                                await safe_send_message(XX, msg, uid, chat_id, key, iv)
                            else:
                                target_uid = str(parts[1]).strip()
                                name = " ".join(parts[2:]).strip().title()
                                admin_data = load_admins()
                                if target_uid not in admin_data:
                                    admin_data[target_uid] = {"name": name}
                                    save_admins(admin_data)
                                    msg = f"""[B][C][00FF00]╔══『 SUCCESS 』══╗

[FF69B4]˗ˏˋ » Name: {name} ! ˎˊ˗
[FFFFFF]˗ˏˋ » UID: {make_circled_num(target_uid)} ! ˎˊ˗

[00FF00]✔ Added to Admin List!
[00FFFF]Welcome aboard, {name} ♡

[FF2EEE]⊹₊˚‧︵‿₊୨ᰔ୧₊‿︵‧˚₊⊹"""
                                else:
                                    msg = f"""[B][C][FFFF00]╔═══『 NOTICE 』═══╗

[FF69B4]˗ˏˋ » Name: {name} ! ˎˊ˗
[FFFFFF]˗ˏˋ » UID: {make_circled_num(target_uid)} ! ˎˊ˗

[FFFF00]｡°⚠︎°｡ {name} is already an Admin!
[00FFFF]No need to add again (˶>⩊<˶)

[FF2EEE]⊹₊˚‧︵‿₊୨ᰔ୧₊‿︵‧˚₊⊹"""
                                await safe_send_message(XX, msg, uid, chat_id, key, iv)
                        except Exception as e:
                            await safe_send_message(XX, f"[FF0000]Error: {e}", uid, chat_id, key, iv)
                    else:
                        await safe_send_message(XX, await not_admin_msg(), uid, chat_id, key, iv)

                elif inPuTMsG.startswith('/remove ') or inPuTMsG.startswith('/removeadmin '):
                    if is_user_admin:
                        try:
                            parts = inPuTMsG.split()
                            if len(parts) < 2:
                                msg = "[B][C][FF0000]❌ Format: /remove <uid>"
                                await safe_send_message(XX, msg, uid, chat_id, key, iv)
                            else:
                                target_uid = str(parts[1]).strip()
                                admin_data = load_admins()
                                if target_uid == BOT_OWNER_UID:
                                    msg = f"""[B][C][FF4500]╔═══『 PROTECTED 』═══╗

[FFFFFF]˗ˏˋ » UID: {make_circled_num(target_uid)} ! ˎˊ˗

[FF0000]</> This user is the OWNER!
[00FFFF]｡°⚠︎°｡ You cannot remove the boss 

[FF2EEE]⊹₊˚‧︵‿₊୨ᰔ୧₊‿︵‧˚₊⊹"""
                                elif target_uid in admin_data:
                                    removed_name = admin_data[target_uid].get("name", "Unknown").title()
                                    del admin_data[target_uid]
                                    save_admins(admin_data)
                                    msg = f"""[B][C][FF0000]╔═══『 REMOVED 』═══╗

[FF69B4]˗ˏˋ » Name: {removed_name} ! ˎˊ˗
[FFFFFF]˗ˏˋ » UID: {make_circled_num(target_uid)} ! ˎˊ˗

[FF0000]｡°⚠︎°｡ Removed from Admin List!
[00FFFF]Goodbye {removed_name} (╥﹏╥)

[FF2EEE]⊹₊˚‧︵‿₊୨ᰔ୧₊‿︵‧˚₊⊹"""
                                else:
                                    msg = f"""[B][C][FF69B4]╔═══『 NOT FOUND 』═══╗

[FFFFFF]˗ˏˋ » UID: {make_circled_num(target_uid)} ! ˎˊ˗

[FF0000]｡°⚠︎°｡ This UID is not in Admin List!
[00FFFF]Maybe already gone (╥﹏╥)

[FF2EEE]⊹₊˚‧︵‿₊୨ᰔ୧₊‿︵‧˚₊⊹"""
                                await safe_send_message(XX, msg, uid, chat_id, key, iv)
                        except Exception as e:
                            await safe_send_message(XX, f"[FF0000]Error: {e}", uid, chat_id, key, iv)
                    else:
                        await safe_send_message(XX, await not_admin_msg(), uid, chat_id, key, iv)

                elif inPuTMsG.startswith('/ban '):
                    if is_user_admin:
                        try:
                            banned_users = load_bans()
                            target_to_ban = inPuTMsG.split()[1].strip()
                            if target_to_ban not in banned_users:
                                banned_users.append(target_to_ban)
                                save_bans(banned_users)
                                msg = f"""[B][C][FF4D6D]╔═『 BAN NOTICE 』═╗

[FFFFFF]˗ˏˋ » UID: {make_circled_num(target_to_ban)}

[FF69B4]💔 Oops... You got banned!
[FF0000]🚫 Access removed from system

[FFFF00]｡°⚠︎°｡ Behavior was not acceptable

[00FFFF]Goodbye... (╥﹏╥)

[FF2EEE]─── ⋆⋅ SYSTEM ⋅⋆ ───"""
                            else:
                                msg = f"""[B][C][FFA500]╔═『 NOTICE 』═╗

[FFFFFF]˗ˏˋ » UID: {make_circled_num(target_to_ban)}

[FFFF00]✨ This user is already in jail list!
[FF69B4]💔 No need to ban again

[00FFFF]｡°⚠︎°｡ System already handled this user

[FF2EEE]─── ⋆⋅ Stay Safe ⋅⋆ ───"""
                            await safe_send_message(XX, msg, uid, chat_id, key, iv)
                        except Exception as e:
                            print("BAN ERROR:", e)
                    else:
                        await safe_send_message(XX, await not_admin_msg(), uid, chat_id, key, iv)

                elif inPuTMsG.startswith('/unban '):
                    if is_user_admin:
                        try:
                            banned_users = load_bans()
                            target_to_unban = inPuTMsG.split()[1].strip()
                            if target_to_unban in banned_users:
                                banned_users.remove(target_to_unban)
                                save_bans(banned_users)
                                msg = f"""[B][C][00FF00]╔═『 UNBAN NOTICE 』═╗

[FFFFFF]˗ˏˋ » UID: {make_circled_num(target_to_unban)}

[00FF00]💚 Welcome back!
[FF69B4]✨ You are unbanned successfully

[FFFF00]｡°⚠︎°｡ Restrictions removed

[00FFFF]Enjoy your freedom again (｡•́‿•̀｡)

[FF2EEE]─── ⋆⋅ SYSTEM ⋅⋆ ───"""
                            else:
                                msg = f"""[B][C][FFA500]╔═『 NOTICE 』═╗

[FFFFFF]˗ˏˋ » UID: {make_circled_num(target_to_unban)}

[FF69B4]💖 This user was never banned!
[FFFF00]✨ Everything is already clean

[00FFFF]｡°⚠︎°｡ No action needed

[FF2EEE]─── ⋆⋅ System Is Happy ⋅⋆ ───"""
                            await safe_send_message(XX, msg, uid, chat_id, key, iv)
                        except Exception as e:
                            print("UNBAN ERROR:", e)
                    else:
                        await safe_send_message(XX, await not_admin_msg(), uid, chat_id, key, iv)

                elif inPuTMsG.strip() in ('/bans', '/banlist'):
                    if is_user_admin:
                        try:
                            banned_users = load_bans()
                            if len(banned_users) == 0:
                                msg = "[B][C][00FF00]╔═══『 BAN LIST 』═══╗\n\n[FF69B4]💖 Yay! Everything is clean\n[00FF00]✨ No banned users found\n\n[FFFF00]｡°⚠︎°｡ System is peaceful\n\n[FF2EEE]⊹₊˚‧︵‿₊୨ SAFE ZONE ୧₊‿︵‧˚₊⊹"
                            else:
                                msg = f"""[B][C][FF4D6D]╔═『 BAN LIST 』═╗

[FF0000]🚫 TOTAL BANNED USERS: {len(banned_users)}

[FFFF00]⚠︎ Restricted Access List

[00FFFF]─── ⋆⋅☼⋅⋆ ───
"""
                                for i, b_uid in enumerate(banned_users, 1):
                                    msg += f"[FFFFFF]{i}. {make_circled_num(b_uid)}\n"
                            await safe_send_message(XX, msg, uid, chat_id, key, iv)
                        except Exception as e:
                            print("BANLIST ERROR:", e)
                    else:
                        await safe_send_message(XX, await not_admin_msg(), uid, chat_id, key, iv)

                elif inPuTMsG.strip() == '/cb':
                    if is_user_admin:
                        try:
                            save_bans([])
                            msg = """[B][C][00FF00]╔═『 SYSTEM RESET 』═╗

[FFFFFF]˗ˏˋ » All bans cleared successfully

[00FF00]✨ Database is now clean & fresh
[FF69B4]💖 Everyone is free again

[FFFF00]｡°⚠︎°｡ No restrictions remaining

[00FFFF]Have a nice day (｡•̀ᴗ-)✧

[FF2EEE]─── ⋆⋅ CLEAN SYSTEM ⋅⋆ ───"""
                            await safe_send_message(XX, msg, uid, chat_id, key, iv)
                        except Exception as e:
                            print("CLEAR ERROR:", e)
                    else:
                        await safe_send_message(XX, await not_admin_msg(), uid, chat_id, key, iv)

                elif inPuTMsG.strip().lower().startswith("/expire"):
                    if is_user_admin:
                        try:
                            parts = inPuTMsG.strip().split()
                            if len(parts) < 2:
                                await safe_send_message(XX, "[B][C][FF0000]Usage: /expire <time>\nExamples: /expire 10min, /expire 1hour, /expire 2day", uid, chat_id, key, iv)
                            else:
                                seconds = parse_expire_time(parts[1])
                                if not seconds:
                                    await safe_send_message(XX, "[B][C][FF0000]Invalid time format. Use: 10sec/10min/1hour/1day/1month/1year", uid, chat_id, key, iv)
                                else:
                                    expire_timestamp = int(time.time() + seconds)
                                    save_expire()
                                    msg = f"""[C][B][00FFCC]╭┈ • ┈୨ EXPIRE SET ୧┈ • ┈╮

[FFFFFF]Bot will expire after:
[FFD166]{parts[1]}

[FF69B4]Only admins can renew it.

[00FFCC]╰┈ • ┈୨ DONE ୧┈ • ┈╯"""
                                    await safe_send_message(XX, msg, uid, chat_id, key, iv)
                        except Exception as e:
                            print(f"Expire error: {e}")
                    else:
                        await safe_send_message(XX, await not_admin_msg(), uid, chat_id, key, iv)

                elif inPuTMsG.startswith('/set '):
                    if is_user_admin:
                        try:
                            parts = inPuTMsG.split(' ', 2)
                            if len(parts) < 3:
                                msg = "[B][C][FF0000]❌ Format: /set <keyword> <msg>"
                            else:
                                keyword = parts[1].lower()
                                response_text = parts[2]
                                replies = load_json_mapping(AUTO_REPLIES_FILE)
                                replies[keyword] = response_text
                                save_json_mapping(AUTO_REPLIES_FILE, replies)
                                msg = f"[B][C][00FF00]✅ Auto-Reply Set!\n[FFFFFF]Keyword: {keyword}\nReply: {response_text}"
                            await safe_send_message(XX, msg, uid, chat_id, key, iv)
                        except Exception as e:
                            await safe_send_message(XX, f"[FF0000]Error: {e}", uid, chat_id, key, iv)
                    else:
                        await safe_send_message(XX, await not_admin_msg(), uid, chat_id, key, iv)

                elif inPuTMsG.startswith('/del '):
                    if is_user_admin:
                        try:
                            keyword = inPuTMsG.split(' ', 1)[1].lower().strip()
                            replies = load_json_mapping(AUTO_REPLIES_FILE)
                            if keyword in replies:
                                del replies[keyword]
                                save_json_mapping(AUTO_REPLIES_FILE, replies)
                                msg = f"[B][C][00FF00]✅ Reply for '{keyword}' deleted!"
                            else:
                                msg = "[B][C][FF0000]❌ Keyword not found!"
                            await safe_send_message(XX, msg, uid, chat_id, key, iv)
                        except Exception as e:
                            await safe_send_message(XX, f"[FF0000]Error: {e}", uid, chat_id, key, iv)
                    else:
                        await safe_send_message(XX, await not_admin_msg(), uid, chat_id, key, iv)

                elif inPuTMsG.strip() == '/replies':
                    if is_user_admin:
                        replies = load_json_mapping(AUTO_REPLIES_FILE)
                        if replies:
                            list_msg = "[B][C][FFFF00]📋 Current Auto-Replies:\n"
                            for k, v in replies.items():
                                list_msg += f"[FFFFFF]• {k} ➜ {v}\n"
                            msg = list_msg
                        else:
                            msg = "[B][C]📭 No auto-replies set yet."
                        await safe_send_message(XX, msg, uid, chat_id, key, iv)
                    else:
                        await safe_send_message(XX, await not_admin_msg(), uid, chat_id, key, iv)

                elif inPuTMsG.startswith('/bc '):
                    if is_user_admin:
                        raw_announcement = inPuTMsG[4:].strip()
                        if raw_announcement:
                            announcement = re.sub(r'\d+', '', raw_announcement).strip().title()
                            if announcement:
                                design_msg = f"""
[B][C][FF1493]✨ OFFICIAL ANNOUNCEMENT ✨
[B][C][FFFF00]╔•═•══════•═•╗

[B][C][FFFFFF] {announcement}

[B][C][FFFF00]╚•═•══════•═•╝

[B][C][00FF00]Dev: —͟͞͞ </> Buddy Meow ❄️⚡"""
                                await safe_send_message(XX, design_msg, uid, chat_id, key, iv)
                            else:
                                await safe_send_message(XX, "[B][C][FF0000]❌ Numbers are not allowed in /bc!", uid, chat_id, key, iv)
                        else:
                            await safe_send_message(XX, "[B][C][FF0000]❌ Please write something after /bc", uid, chat_id, key, iv)
                    else:
                        await safe_send_message(XX, await not_admin_msg(), uid, chat_id, key, iv)

                # =================== UTILITY & FUN COMMANDS ===================
                elif inPuTMsG.strip().startswith('/noob') or inPuTMsG.strip().startswith('noob'):
                    await handle_alll_titles_command(inPuTMsG, uid, chat_id, key, iv, region, XX)

                elif inPuTMsG.strip() == "/fun" or inPuTMsG.strip().startswith("/fun "):
                    if "__fun_pool__" not in globals():
                        globals()["__fun_pool__"] = [
                            "ভালোবাসা, কান ধরছি আর না, কষ্ট আমি পাইসি, তুমি না!!",
                            "মানে ishq, প্রেম, ভালোবাসা!!",
                            "What is love?",
                            "কি বললি, এই এই কু'ত্তার বাচ্চা, এই তুই কি বললি, তুই কি বললি, এই তুই কি বললি, এই এই, এই কু'ত্তার বাচ্চা, কু'ত্তাররররর বাচ্চা, এই এই এই এইইইইইই.......",
                            "I love you 2, ummmmmmmmmmmmah",
                            "ভাই English তো আমি ভালো বুঝি, কিন্তু আমি তো চোখে দেখিনা....!!!",
                            "তেঁতুলের আচার টক, তোমার নানীরে পক পক....!!!",
                            "প্রেমের জালে ফেলে ধোকা দিতে চাও, পারবে না, কারণ আমি ক্রাইম পেট্রল দেখে বড়  হয়েছি...!!",
                            "এই শুয়োরের বাচ্চা, এই Bᴀꜱᴛᴀʀᴅ, কু'ত্তার বা'চ্চা  টেলিফোন রাখ !!!",
                            "সবার অংক মিলে, কিন্তু আমার অংক মilenা!!",
                            "খান'কির পোলা তোরে আমি খুইজা বেড়াইতাসি.....!!!",
                            "Ishhh আবার ইংরেজি চু'দাও, ইংরেজি ঢুকাই দিবো আইতাছে তোর বা'পে",
                            "আজ প্রত্থম বার কইসোস তাই মাফ কইরা দিলাম, কিন্তু দ্বিতীয় বার যেদিন কবি সেইদিন তোর কইলজা টারে টাইনা বাইর কইরা আমি ওজন করুম !!!",
                            "ওই আমার বা'পে রাজা, আমার দাদায় রাজা, আমি নিজে রাজা, তুই চিনস না আমা'রে, তোর বা'পে চিনে, জিগাইস !!!",
                            "আমার হো'গা মারা শেষ, আপনার নাম যদি হয় বাদশা, তাইলে আমার কি নাম হওয়া উচিত, আপনাগোর মতো ফকিন্নি পোলাগোর নাম বাদশা দেইখাই তো, দেশটার এই অবস্থা !!"
                        ]
                    pool = globals()["__fun_pool__"]
                    if not pool:
                        pool.extend([
                            "ভালোবাসা, কান ধরছি আর না, কষ্ট আমি পাইসি, তুমি না!!",
                            "মানে ishq, প্রেম, ভালোবাসা!!",
                            "What is love?",
                            "কি বললি, এই এই কু'ত্তার বাচ্চা, এই তুই কি বললি, তুই কি বললি, এই তুই কি বললি, এই এই, এই কু'ত্তার বাচ্চা, কু'ত্তাররররর বাচ্চা, এই এই এই এইইইইইই.......",
                            "I love you 2, ummmmmmmmmmmmah",
                            "ভাই English তো আমি ভালো বুঝি, কিন্তু আমি তো চোখে দেখিনা....!!!",
                            "তেঁতুলের আচার টক, তোমার নানীরে পক পক....!!!",
                            "প্রেমের জালে ফেলে ধোকা দিতে চাও, পারবে না, কারণ আমি ক্রাইম পেট্রল দেখে বড়  হয়েছি...!!",
                            "এই শুয়োরের বাচ্চা, এই Bᴀꜱᴛᴀʀᴅ, কু'ত্তার বা'চ্চা  টেলিফোন রাখ !!!",
                            "সবার অংক মিলে, কিন্তু আমার অংক মilenা!!",
                            "খান'কির পোলা তোরে আমি খুইজা বেড়াইতাসি.....!!!",
                            "Ishhh আবার ইংরেজি চু'দাও, ইংরেজি ঢুকাই দিবো আইতাছে তোর বা'পে",
                            "আজ প্রত্থম বার কইসোস তাই মাফ কইরা দিলাম, কিন্তু দ্বিতীয় বার যেদিন কবি সেইদিন তোর কইলজা টারে টাইনা বাইর কইরা আমি ওজন করুম !!!",
                            "ওই আমার বা'পে রাজা, আমার দাদায় রাজা, আমি নিজে রাজা, তুই চিনস না আমা'রে, তোর বা'পে চিনে, জিগাইস !!!",
                            "আমার হো'গা মারা শেষ, আপনার নাম যদি হয় বাদশা, তাইলে আমার কি নাম হওয়া উচিত, আপনাগোর মতো ফকিন্নি পোলাগোর নাম বাদশা দেইখাই তো, দেশটার এই অবস্থা !!"
                        ])
                    selected_msg = random.choice(pool)
                    pool.remove(selected_msg)
                    final_msg = f"[B][C]{get_random_color()}{selected_msg}"
                    await safe_send_message(XX, final_msg, uid, chat_id, key, iv)

                elif inPuTMsG.strip().startswith('/pick'):
                    parts = inPuTMsG.strip().split(maxsplit=1)
                    if len(parts) < 2:
                        error_msg = "[B][C][FF0000]❌ Usage: /pick <name>\nExample: /pick Sneha"
                        await safe_send_message(XX, error_msg, uid, chat_id, key, iv)
                    else:
                        name = parts[1].strip().title()
                        pickup_lines = [
                            "{Name} Agar main ek keyboard hota toh 'U' aur 'I' ko hamesha paas rakhta!",
                            "{Name} Kya aapke paas map hai? Kyunki main aapki aankhon mein kho gaya hoon!",
                            "{Name} Agar main camera hota toh har pal aapko dekh ke smile karta!",
                            "{Name} Kya aap Google ho? Kyunki aap mein woh sab hai jo main dhoondh raha tha!",
                            "{Name} Kya aap bijli ho? Kyunki aapke aane se mera dil light up ho jata hai!",
                            "{Name} Tumhare bina toh main ek incomplete WhatsApp forward ki tarah hoon.",
                            "{Name} Tumhare chehre pe woh smile dekh kar mere dimaag ka antivirus crash ho gaya.",
                            "{Name} Tumhare saath bitaya hua har second mere liye unlimited data pack ki tarah hai.",
                            "{Name} Tumhari aankhon mein aisa jadoo hai ki main unmein kho jana chahta hoon.",
                            "{Name} Tumhari aankhen sitaron se bhari raat ki tarah hain jinmein main doobna chahta hoon."
                        ]
                        for msg in pickup_lines:
                            colored_msg = f"[B][C]{get_random_color()} {msg.replace('{Name}', name)}"
                            await safe_send_message(XX, colored_msg, uid, chat_id, key, iv)
                            await asyncio.sleep(0.5)

                elif inPuTMsG.strip().startswith('/gd'):
                    parts = inPuTMsG.strip().split(maxsplit=1)
                    if len(parts) < 2:
                        await safe_send_message(XX, "[B][C][FF0000]❌ Usage: /gd <name>\nExample: /gd Maruf", uid, chat_id, key, iv)
                    else:
                        words = parts[1].strip().split()
                        name = " ".join(word for word in words if not word.isdigit()).strip().title()
                        if not name:
                            await safe_send_message(XX, "[B][C][FF0000]❌ Please provide a valid name.", uid, chat_id, key, iv)
                        elif name.lower() in [n.lower() for n in BLOCKED_NAMES]:
                            await safe_send_message(XX, f"[B][C][FF0000]⚠️ WARNING! You cannot target '{name}'! Bot owner protected! ⛔", uid, chat_id, key, iv)
                        else:
                            praise_messages = [
                                f"{name} tumhara nature sach me bohot accha hai ✨",
                                f"{name} you are genuinely one of the sweetest people around 🌸",
                                f"{name} tumhari presence hi team ko strong bana deti hai 💪",
                                f"{name} always stay humble and shine bright like a star ⭐",
                                f"{name} your positive vibes make everyone happy around you 😊",
                                f"{name} keep smiling, your smile is truly precious 💖"
                            ]
                            for p_msg in praise_messages:
                                await safe_send_message(XX, f"[B][C]{get_random_color()}{p_msg}", uid, chat_id, key, iv)
                                await asyncio.sleep(0.5)

                elif inPuTMsG.strip().startswith('/lol'):
                    parts = inPuTMsG.strip().split(maxsplit=1)
                    if len(parts) < 2:
                        await safe_send_message(XX, "[B][C][FF0000]❌ Usage: /lol <name>\nExample: /lol hater", uid, chat_id, key, iv)
                    else:
                        words = parts[1].strip().split()
                        name = " ".join(word for word in words if not word.isdigit()).strip().upper()
                        if not name: name = "HATER"
                        roast_messages = [
                            f"{name} er confidence dekhe WiFi o insecure hoy 🤡",
                            f"{name} এত faltu যে background noise হিসেবেও reject",
                            f"{name} নিজেকে legend ভাবে, কিন্তু tutorial skip করে",
                            f"{name} er brain Google Lite version",
                            f"{name} কথা বলে এমনভাবে—নিজেই confused, অন্যরা bonus",
                            f"{name} কে দেখলে lag kore system hang",
                            f"{name} er logic calculator ছুঁলে error দেয়",
                            f"{name} এত expert যে ভুলটাও confidently করে",
                            f"{name} নিজেই নিজের biggest fan 🤣",
                            f"{name} er attitude flagship, skills trial version",
                            f"{name} er presence মানেই lag spike",
                            f"{name} কথা শুরু করে, point হারিয়ে ফেলে",
                            f"{name} এত slow যে loading circle mock করে",
                            f"{name} argument এ হেরে বলে: ‘network issue’",
                            f"{name} er IQ auto-update off",
                            f"{name} dekhe মনে হয় life tutorial miss করেছে",
                            f"{name} er brain.exe stopped unexpectedly ⚠️",
                            f"{name} এত random যে RNG jealous",
                            f"{name} vibe এমন—mute করলে শান্তি",
                            f"{name} নিজেকে pro ভাবে, কিন্তু controls জানে না"
                        ]
                        for r_msg in roast_messages:
                            await safe_send_message(XX, f"[B][C]{get_random_color()}{r_msg}", uid, chat_id, key, iv)
                            await asyncio.sleep(0.5)

                elif inPuTMsG.strip() in ("/whoami", "whoami"):
                    sender_uid_s = str(uid).strip()
                    creator = is_creator(sender_uid_s)
                    whoami_player = getattr(getattr(response.Data, "Details", None), "Nickname", "") or "User"
                    if creator:
                        whoami_msg = f"""[B][C][FFD700]╔═══『 CREATOR 』═══╗
[87ceeb]ㅤㅤYou are {whoami_player}
[FF69B4]ㅤㅤㅤYou are the Creator
[00FFFF]✨ Highest authority unlocked
[00FF00]ㅤEveryone respects your power
[FFFFFF]ㅤ━━━━━━━━━━━━━━
[FFFF00]Dev: —͟͞͞ </> Buddy Meow"""
                    elif is_user_admin:
                        whoami_msg = f"""[B][C][00FFFF]╔════『 ADMIN 』════╗
[87ceeb]ㅤㅤYou are {whoami_player}
[FF69B4]ㅤㅤㅤYou are an Admin
[00FF00]✔ Elevated permissions active
[FFFF00]ㅤHelp protect the system
[FFFFFF]ㅤ━━━━━━━━━━━━━━
[FFFF00]Dev: —͟͞͞ </> Buddy Meow"""
                    else:
                        whoami_msg = f"""[B][C][FF69B4]╔════『 USER 』════╗
[87ceeb]ㅤㅤYou are {whoami_player}
[FFFFFF]ㅤㅤㅤYou are a User
[00FFFF]Enjoy the features & commands
[FF00FF]ㅤStay safe and have fun
[FFFFFF]ㅤ━━━━━━━━━━━━━━
[FFFF00]Dev: —͟͞͞ </> Buddy Meow"""
                    await safe_send_message(XX, whoami_msg, uid, chat_id, key, iv)

                elif inPuTMsG.strip() in ("/meow", "meow"):
                    meow_msg = """[B][C][FF69B4] ╱|、
[FFFFFF](˚ˎ 。7  [FF69B4]Meow❤
[FFFFFF] |、˜〵
[FFFFFF]じしˍ,)ノ"""
                    await safe_send_message(XX, meow_msg, uid, chat_id, key, iv)

                elif command_text == "/duo" or command_text.startswith("/duo "):
                    parts = command_text.split()
                    if len(parts) != 2 or not parts[1].isdigit():
                        await safe_send_message(
                            XX,
                            "[B][C][FF0000]❌ Usage: /duo <uid>\n"
                            "[FFFFFF]Example: /duo 360927069",
                            uid, chat_id, key, iv,
                        )
                    else:
                        target_uid = parts[1]
                        requester_name = (
                            getattr(getattr(response.Data, "Details", None), "Nickname", "")
                            or "User"
                        )
                        loading_msg = (
                            "[B][C][FF69B4]💞 Checking Duo Status...\n\n"
                            f"[00FFFF]UID: {xMsGFixinG(target_uid)}\n"
                            f"[FFFF00]Requested by: {requester_name}\n"
                            "[FFFFFF]Please wait..."
                        )
                        await safe_send_message(XX, loading_msg, uid, chat_id, key, iv)
                        try:
                            loop = asyncio.get_running_loop()
                            duo_data = await loop.run_in_executor(
                                None, get_dynamic_duo_info, target_uid
                            )
                            await send_dynamic_duo_info(
                                duo_data, XX, uid, chat_id, key, iv
                            )
                        except Exception as e:
                            print(f"Duo command error: {e}")
                            await safe_send_message(
                                XX,
                                f"[B][C][FF0000]❌ Duo lookup error:\n{str(e)[:200]}",
                                uid, chat_id, key, iv,
                            )

                elif inPuTMsG.strip().lower() in ("duo", "need duo", "bot duo daw", "/bot need duo", "duo khuje daw", "duo dao", "duo please", "duo pabo?", "duo pabo", "duo khuje dao", "duo khuje den", "duo lagbe"):
                    duo_msg = """[C][B][FF4D6D]╭┈ • ┈୨ WARNING ୧┈ • ┈╮

[FFFFFF]ভাই এইসব Duo Duo Spam  করে লাভ নাই, কারণ তোমার কপালে Duo নাই.

কোনো মেয়েই তোমাকে পাত্তা দিবেনা, অন্তত এই গেমিং লাইফে তো একদমই না.
তাই এইসব Duo স্প্যাম বন্ধ করো.

হয় গিয়ে গেম খেলো নাহলে গিয়ে পড়াশুনা করো,
নিজের Skill ইম্প্রোভ করো
Unnecessary এইসব স্প্যাম অফ করো

ভালোমতো বলে দিলাম, তারপরেও যদি আরেকবার Duo Spam করো তাহলে একদম Ban করে দিবো !! 

─── ⋆⋅☆⋅⋆ ───"""
                    await safe_send_message(XX, duo_msg, uid, chat_id, key, iv)

                elif inPuTMsG.strip().startswith('/ai'):
                    question = inPuTMsG[4:].strip()
                    if question:
                        await safe_send_message(XX, f"[B][C]{get_random_color()}\n🤖 AI is thinking...\n", uid, chat_id, key, iv)
                        ai_response = talk_with_ai(question)
                        ai_message = f"""[B][C][00FF00]🤖 AI Response:

[FFFFFF]{ai_response}

[C][B][FFB300]Question: [FFFFFF]{question}"""
                        await safe_send_message(XX, ai_message, uid, chat_id, key, iv)
                    else:
                        await safe_send_message(XX, "[B][C][FF0000]❌ ERROR! Please provide a question after /ai\nExample: /ai What is Free Fire?\n", uid, chat_id, key, iv)

                elif inPuTMsG.strip().startswith("/translate "):
                    try:
                        from deep_translator import GoogleTranslator

                        text = inPuTMsG.strip().split(" ", 1)[1].strip()
                        if not text:
                            await safe_send_message(
                                XX,
                                "[FF0000]❌ Please provide text to translate!",
                                uid, chat_id, key, iv,
                            )
                            continue

                        is_bangla = any("\u0980" <= ch <= "\u09FF" for ch in text)
                        target_lang = "en" if is_bangla else "bn"
                        translated = GoogleTranslator(
                            source="auto",
                            target=target_lang,
                        ).translate(text)
                        lang_name = "English" if is_bangla else "Bangla"
                        msg = f"""[C][B][00FFCC]╭┈ • ┈୨ TRANSLATOR ୧┈ • ┈╮

[FFFFFF]Input : {text}
[FFD166]{lang_name} : {translated}

[00FFCC]╰┈ • ┈୨ DONE ୧┈ • ┈╯"""

                        await safe_send_message(XX, msg, uid, chat_id, key, iv)
                        await safe_send_message(
                            XX, translated, uid, chat_id, key, iv
                        )
                    except Exception as e:
                        print(f"/translate error: {e}")
                        await safe_send_message(
                            XX,
                            "[FF0000]❌ Translation failed!",
                            uid, chat_id, key, iv,
                        )

                elif inPuTMsG.strip().startswith("/name"):
                    try:
                        parts = inPuTMsG.strip().split(" ", 1)
                        mode = "random"
                        if len(parts) == 1:
                            base = random.choice(all_names)
                        else:
                            arg = parts[1].strip().lower()
                            if arg == "boy":
                                mode = "boy"; base = random.choice(boy_names)
                            elif arg == "girl":
                                mode = "girl"; base = random.choice(girl_names)
                            elif arg == "random":
                                mode = "random"; base = random.choice(all_names)
                            else:
                                mode = "custom"; base = parts[1].strip()
                        final_name = build_name(base, mode)
                        msg1 = f"""[B][C][00FFFF]╔═『 NAME SYSTEM 』═╗
          
[FFFFFF]˗ˏˋ » IGN: {final_name}

[00FF00]✔ Successfully Generated
[FFFF00]Mode: {mode.title()}
[FF69B4]Enjoy your new stylish name ♡

[FF2EEE]─── ⋆⋅ STYLISH IGN ⋅⋆ ───"""
                        await safe_send_message(XX, msg1, uid, chat_id, key, iv)
                        await asyncio.sleep(0.3)
                        await safe_send_message(XX, final_name, uid, chat_id, key, iv)
                    except Exception as e:
                        await safe_send_message(XX, f"[B][C][FF0000]❌ Name error: {e}", uid, chat_id, key, iv)

                elif inPuTMsG.strip() == "/creator":
                    creator_message = """[C][B][00FFCC]╭┈ • ┈୨ Creator ୧┈ • ┈╮

[FFFFFF]  You found me
[FFFFFF]  Thanks for using this bot
[FFFFFF]  Your support means a lot

[00FFCC]  ──────────────
[FFD700]  Owner   : Buddy Meow
[87CEEB]  Facebook: Rizzfez Zitt
[FF69B4]  TikTok  : @buddy_meow

[FFFFFF]  You are really sweet
[FFFFFF]  Keep smiling always

[00FFCC]  ──────────────
[00FFCC]╰┈ • ┈୨ STAY HAPPY ୧┈ • ┈╯
[FFD700]  Dev: —͟͞͞ </> Buddy Meow ⚡"""
                    await safe_send_message(XX, creator_message, uid, chat_id, key, iv)

                elif inPuTMsG.strip().lower() == '/store':
                    store_msg = f"""
[C][B][00E5FF]❖ Buddy Meow Premium Store ❖

[B][C][FFFFFF]Unlock exclusive services fast & premium!

[B][00FF00]SERVICES & PRICES:[00FF00]
├─ [B][C][FF69B4]Video Editing: 
│  └─ Overlay Video 100 Tk
│  └─ Jod 150 Tk
│  └─ CC 100 Tk
├─ [B][C][FFD700]Premium Guild Bot:
│  └─ 7d 500 Tk
│  └─ 30d 1000 Tk
│  └─ 60d 2000 Tk
│  └─ Permanent 5000 Tk
└─ [B][C][ff0000]Guild Glory Bot:
     └─ 4ta bot → 180Tk
     └─ 12ta bot → 540Tk

[B][87ceeb]CONTACT:
➥ Owner: BUDDY MEOW
➥ UID: {make_circled_num("490381600")}
➥ FB: Rizzfez Zitt
➥ TikTok: buddy_meow

[C][B][FF69B4]Thanks for supporting"""
                    await safe_send_message(XX, store_msg, uid, chat_id, key, iv)

                elif inPuTMsG.strip() == "/free":
                    promo_message = """[C][B][00E5FF]╭┈ • ┈୨ FREE ୧┈ • ┈╮[FF00FF][B]

[FFFFFF]Hey Gareeb ☁️
[7C4DFF]Tumi jodi guild bot free te chao,
[FFFFFF]just ekta GF / DUO khuje dao 😌

[2196F3]Ami tomake setup kore dibo full free te ✨
[FF4081]Chinta koro na, sab easy kore dibo 💕

[FFFF00]Contact:
[FFFFFF]» Facebook: Rizzfez Zitt
[FFFFFF]» TikTok: @buddy_meow

[00E5FF]╰┈ • ┈୨ STAY HAPPY ୧┈ • ┈╯
[FF00FF]Dev: —͟͞͞ </> Buddy Meow"""
                    await safe_send_message(XX, promo_message, uid, chat_id, key, iv)

                elif inPuTMsG.strip().startswith('/bundle'):
                    parts = inPuTMsG.strip().split()
                    if len(parts) < 2:
                        bundle_list = """[B][C][00FFCC]╔══🎁 BUNDLE LIST ══╗

[FFFFFF]• Rampage
[FFFFFF]• Cannibal
[FFFFFF]• Devil
[FFFFFF]• Scorpio
[FFFFFF]• Frostfire
[FFFFFF]• Paradox
[FFFFFF]• Naruto
[FFFFFF]• Aurora
[FFFFFF]• Midnight
[FFFFFF]• Itachi
[FFFFFF]• Dreamspace

[00FFCC]╠═══════════════╣
[FFD700]📌 Usage:
[FFFFFF]/bundle <name>

[FFD700]Example:
[FFFFFF]/bundle naruto

[FFD700]👑 Owner: [FFFFFF]Buddy Meow
[00FFCC]╚═══════════════╝"""
                        await safe_send_message(XX, bundle_list, uid, chat_id, key, iv)
                    else:
                        bundle_name = parts[1].lower()
                        bundle_ids_named = {
                            "rampage": "914000002", "cannibal": "914000003",
                            "devil": "914038001", "scorpio": "914039001",
                            "frostfire": "914042001", "paradox": "914044001",
                            "naruto": "914047001", "aurora": "914047002",
                            "midnight": "914048001", "itachi": "914050001",
                            "dreamspace": "914051001"
                        }
                        if bundle_name not in bundle_ids_named:
                            await safe_send_message(XX, "❌ Invalid Name", uid, chat_id, key, iv)
                        else:
                            bid = bundle_ids_named[bundle_name]
                            try:
                                bundle_pkt = await bundle_packet_async(bid, key, iv, region)
                                if bundle_pkt and online_writer:
                                    online_writer.write(bundle_pkt)
                                    await online_writer.drain()
                                    await safe_send_message(XX, f"[B][C][00FF00]✅ Done: {bundle_name}", uid, chat_id, key, iv)
                                else:
                                    await safe_send_message(XX, "[B][C][FF0000]❌ Connection Lost", uid, chat_id, key, iv)
                            except Exception as e:
                                print(f"Bundle error: {e}")

                elif inPuTMsG.strip() in ("/guildrules", "guildrules") or command_text == "guild rules":
                    await safe_send_message(XX, GUILD_RULES_MSG, uid, chat_id, key, iv)

                elif inPuTMsG.strip() in ("/admin", "admin"):
                    msg = f"""[b][c]{get_random_color()} ═══ BUDDY MEOW BOT ═══

[b][c][00FFFF]👤 Name: BUDDY MEOW
[b][c][FFFFFF]👑 Owner UID: {make_circled_num("490381600")}
[b][c][FFFFFF]✈ FB: Rizzfez Zitt | TikTok: @buddy_meow

[b][c][FFFF00]🎮 Free Fire TCP Automation Bot
[b][c][FFFFFF]⚡ Version: Buddy V5.0

[b][c]{get_random_color()} Powered by BUDDY MEOW"""
                    await safe_send_message(XX, msg, uid, chat_id, key, iv)

                elif inPuTMsG.strip() == '/on':
                    if not is_admin(uid):
                        await safe_send_message(XX, await not_admin_msg(), uid, chat_id, key, iv)
                    else:
                        bot_enabled = True
                        await safe_send_message(XX, "[B][C][00FF00]✅ Bot is now ON. Admin mode is unchanged.", uid, chat_id, key, iv)

                elif inPuTMsG.strip() == '/off':
                    if not is_admin(uid):
                        await safe_send_message(XX, await not_admin_msg(), uid, chat_id, key, iv)
                    else:
                        bot_enabled = False
                        await safe_send_message(XX, "[B][C][FF0000]⛔ Bot is now OFF. Only admins can use commands; /on will re-enable it.", uid, chat_id, key, iv)

                # (old /e and /evo merged into main emote block above)

                # ═══════════════════════════════════════════════
# INFO (buddy-real-info API)
                # ═══════════════════════════════════════════════
                elif inPuTMsG.strip().startswith('/info '):
                    parts = inPuTMsG.strip().split()
                    if len(parts) >= 2 and parts[1].isdigit():
                        target_uid = parts[1]
                        requester_name = getattr(getattr(response.Data, "Details", None), "Nickname", "") or "User"
                        initial_msg = (
                            f"[B][C][FFFF00]Fetching info of {fix_num(target_uid)}...\n"
                            f"[87ceeb]Requested by: {requester_name}"
                        )
                        await safe_send_message(XX, initial_msg, uid, chat_id, key, iv)
                        data = get_player_info(target_uid)
                        ok = isinstance(data, dict) and "basic_info" in data
                        if ok:
                            await send_full_player_info(data, XX, uid, chat_id, key, iv)
                        else:
                            await safe_send_message(XX, f"[B][C][FF0000]❌ {data}", uid, chat_id, key, iv)
                    else:
                        await safe_send_message(XX, f"[B][C][FF0000]Usage: /info <uid>", uid, chat_id, key, iv)

                # ═══════════════════════════════════════════════
                # OTHER COMMANDS
                # ═══════════════════════════════════════════════
                elif inPuTMsG.strip().startswith('/check '):
                    parts = inPuTMsG.strip().split()
                    if len(parts) >= 2 and parts[1].isdigit():
                        ok, result = await check_banned(parts[1])
                        reply = format_check_result(result) if ok else f"[B][C][FF0000]❌ {result}"
                        P = await SEndMsG(XX, reply, uid, chat_id, key, iv)
                        await SEndPacKeT(whisper_writer, online_writer, 'ChaT', P)
                    else: await safe_send_message(XX, f"[B][C][FF0000]Usage: /check <uid>", uid, chat_id, key, iv)

                elif inPuTMsG.strip().startswith('/mth'):
                    parts = inPuTMsG.strip().split(maxsplit=1)
                    if len(parts) < 2: await safe_send_message(XX, f"[B][C][FFFF00]Usage: /mth 2+2", uid, chat_id, key, iv)
                    else:
                        expr = parts[1].strip().replace("×", "*").replace("÷", "/").replace("x", "*")
                        try:
                            import re as _re
                            if not _re.match(r'^[\d\s\+\-\*\/\.\(\)\%]+$', expr): raise ValueError("Invalid expression")
                            result = eval(expr)
                            if isinstance(result, float) and result == int(result): result = int(result)
                            P = await SEndMsG(XX, f"[B][C][00FFFF]🧮 Calculator\n\n[FFFF00]Expression: [FFFFFF]{expr}\n[00FF00]Result: [FFFFFF]{result}", uid, chat_id, key, iv)
                            await SEndPacKeT(whisper_writer, online_writer, 'ChaT', P)
                        except ZeroDivisionError: await safe_send_message(XX, f"[B][C][FF0000]❌ Division by zero", uid, chat_id, key, iv)
                        except Exception: await safe_send_message(XX, f"[B][C][FF0000]❌ Invalid expression", uid, chat_id, key, iv)

                elif inPuTMsG.strip().startswith("/fadd ") and is_user_admin:
                    parts = inPuTMsG.strip().split()
                    if len(parts) >= 2 and parts[1].isdigit():
                        try:
                            ok, msg = await send_friend_request(parts[1], ToKen, region)
                            reply = f"[B][C]{get_random_color()} {msg}"
                        except Exception as e: reply = f"[B][C][FF0000]Error: {e}"
                    else: reply = f"[B][C][FF0000]Usage: /fadd <uid>"
                    P = await SEndMsG(XX, reply, uid, chat_id, key, iv)
                    await SEndPacKeT(whisper_writer, online_writer, 'ChaT', P)

                elif inPuTMsG.strip().startswith("/fremove ") and is_user_admin:
                    parts = inPuTMsG.strip().split()
                    if len(parts) >= 2 and parts[1].isdigit():
                        try:
                            ok, msg = await remove_friend(parts[1], ToKen, region)
                            reply = f"[B][C]{get_random_color()} {msg}"
                        except Exception as e: reply = f"[B][C][FF0000]Error: {e}"
                    else: reply = f"[B][C][FF0000]Usage: /fremove <uid>"
                    P = await SEndMsG(XX, reply, uid, chat_id, key, iv)
                    await SEndPacKeT(whisper_writer, online_writer, 'ChaT', P)

                elif inPuTMsG.strip().startswith('/join '):
                    try:
                        code = inPuTMsG.split('/join ')[1].strip()
                        EM = await JoinSq_original(code, key, iv)
                        await SEndPacKeT(whisper_writer, online_writer, 'OnLine', EM)
                        await safe_send_message(XX, f"[B][C]{get_random_color()}\n✅ Joined squad: {code}", uid, chat_id, key, iv)
                    except Exception as e: print(f"Join error: {e}")

                elif inPuTMsG.startswith('/exit') or inPuTMsG.startswith('/leave'):
                    await SEndPacKeT(whisper_writer, online_writer, 'OnLine', await ExiT(uid, key, iv))
                    await safe_send_message(XX, f"[B][C]{get_random_color()}\n✅ Left squad", uid, chat_id, key, iv)

                elif inPuTMsG.strip() == '/5':
                    try:
                        await safe_send_message(XX, f"[B][C]{get_random_color()}\n\nCreating 5-man team...\n", uid, chat_id, key, iv)
                        await SEndPacKeT(whisper_writer, online_writer, 'OnLine', await OpEnSq(key, iv, region))
                        await asyncio.sleep(0.3)
                        await SEndPacKeT(whisper_writer, online_writer, 'OnLine', await cHSq(5, uid, key, iv, region))
                        await asyncio.sleep(0.3)
                        await SEndPacKeT(whisper_writer, online_writer, 'OnLine', await SEnd_InV(5, uid, key, iv, region))
                        await asyncio.sleep(3.5)
                        await SEndPacKeT(whisper_writer, online_writer, 'OnLine', await ExiT(None, key, iv))
                        await safe_send_message(
                            XX,
                            f"[B][C][00FF00]Yay! 5-man group invite sent successfully!\n[FFFFFF]Invite your friends and have fun together!",
                            uid, chat_id, key, iv,
                        )
                    except Exception as e:
                        print(f"Team5 error: {e}")
                        await safe_send_message(
                            XX,
                            f"[B][C][FF0000]❌ Could not create 5-man group: {e}",
                            uid, chat_id, key, iv,
                        )

                elif inPuTMsG.startswith('/6'):
                    try:
                        await safe_send_message(XX, f"[B][C]{get_random_color()}\n\nCreating 6-man team...\n", uid, chat_id, key, iv)
                        await SEndPacKeT(whisper_writer, online_writer, 'OnLine', await ExiT(uid, key, iv))
                        await asyncio.sleep(0.3)
                        await SEndPacKeT(whisper_writer, online_writer, 'OnLine', await OpEnSq(key, iv, region))
                        await asyncio.sleep(0.3)
                        await SEndPacKeT(whisper_writer, online_writer, 'OnLine', await cHSq(6, uid, key, iv, region))
                        await asyncio.sleep(0.3)
                        await SEndPacKeT(whisper_writer, online_writer, 'OnLine', await SEnd_InV(6, uid, key, iv, region))
                        await asyncio.sleep(3.5)
                        await SEndPacKeT(whisper_writer, online_writer, 'OnLine', await ExiT(None, key, iv))
                        await safe_send_message(XX, f"[B][C][00FF00]✅ 6-man team invitation sent!", uid, chat_id, key, iv)
                    except Exception as e: print(f"Team6 error: {e}")

                elif inPuTMsG.startswith('/3') and not inPuTMsG.startswith('/30'):
                    try:
                        await safe_send_message(XX, f"[B][C]{get_random_color()}\n\nCreating 3-man team...\n", uid, chat_id, key, iv)
                        await SEndPacKeT(whisper_writer, online_writer, 'OnLine', await OpEnSq(key, iv, region))
                        await asyncio.sleep(0.3)
                        await SEndPacKeT(whisper_writer, online_writer, 'OnLine', await cHSq(3, uid, key, iv, region))
                        await asyncio.sleep(0.3)
                        await SEndPacKeT(whisper_writer, online_writer, 'OnLine', await SEnd_InV(3, uid, key, iv, region))
                        await asyncio.sleep(3.5)
                        await SEndPacKeT(whisper_writer, online_writer, 'OnLine', await ExiT(None, key, iv))
                        await safe_send_message(XX, f"[B][C][00FF00]✅ 3-man team invitation sent!", uid, chat_id, key, iv)
                    except Exception as e: print(f"Team3 error: {e}")

                elif inPuTMsG.startswith('/4'):
                    try:
                        await safe_send_message(XX, f"[B][C]{get_random_color()}\n\nCreating 4-man team...\n", uid, chat_id, key, iv)
                        await SEndPacKeT(whisper_writer, online_writer, 'OnLine', await OpEnSq(key, iv, region))
                        await asyncio.sleep(0.3)
                        await SEndPacKeT(whisper_writer, online_writer, 'OnLine', await cHSq(4, uid, key, iv, region))
                        await asyncio.sleep(0.3)
                        await SEndPacKeT(whisper_writer, online_writer, 'OnLine', await SEnd_InV(4, uid, key, iv, region))
                        await asyncio.sleep(3.5)
                        await SEndPacKeT(whisper_writer, online_writer, 'OnLine', await ExiT(None, key, iv))
                        await safe_send_message(XX, f"[B][C][00FF00]✅ 4-man team invitation sent!", uid, chat_id, key, iv)
                    except Exception as e: print(f"Team4 error: {e}")
                    
                elif inPuTMsG.strip().startswith('/snd '):
                    try:
                        parts = inPuTMsG.strip().split()
                        if len(parts) < 2 or not parts[1].isdigit():
                            await safe_send_message(
                                XX,
                                f"[B][C][FF0000]❌ Usage: /snd [target_uid]\n[FFFFFF]Example: /snd 49😪03😪816😪00",
                                uid, chat_id, key, iv,
                            )
                        else:
                            target_uid = int(parts[1])
                            await safe_send_message(
                                XX,
                                f"[B][C]{get_random_color()}\n\nSending 5-man team invite to {target_uid}...\n",
                                uid, chat_id, key, iv,
                            )
                            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', await OpEnSq(key, iv, region))
                            await asyncio.sleep(0.3)
                            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', await cHSq(5, target_uid, key, iv, region))
                            await asyncio.sleep(0.3)
                            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', await SEnd_InV(5, target_uid, key, iv, region))
                            await asyncio.sleep(3.5)
                            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', await ExiT(None, key, iv))
                            await safe_send_message(
                                XX,
                                f"[B][C][00FF00]Yay! 5-man group invite sent to {target_uid} successfully!\n"
                                f"[FFFFFF]Invite your friends and have fun together!",
                                uid, chat_id, key, iv,
                            )
                    except Exception as e:
                        print(f"Snd error: {e}")
                        await safe_send_message(
                            XX,
                            f"[B][C][FF0000]❌ Could not send 5-man group invite: {e}",
                            uid, chat_id, key, iv,
                        )
                elif inPuTMsG.strip().startswith('/inv '):
                    try:
                        parts = inPuTMsG.strip().split()
                        if len(parts) < 2 or not parts[1].isdigit():
                            await safe_send_message(
                                XX,
                                f"[B][C][FF0000]❌ Usage: /inv [target_uid]\n[FFFFFF]Example: /inv 490😪381😪60😪0",
                                uid, chat_id, key, iv,
                            )
                        else:
                            target_uid = int(parts[1])
                            await safe_send_message(
                                XX,
                                f"[B][C]{get_random_color()}\n\nCreating 5-man team...\n"
                                f"[FFFFFF]Inviting {target_uid} + commander ({uid})...\n",
                                uid, chat_id, key, iv,
                            )
                            # squad owner = commander
                            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', await OpEnSq(key, iv, region))
                            await asyncio.sleep(0.3)
                            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', await cHSq(5, uid, key, iv, region))
                            await asyncio.sleep(0.3)

                            # invite #1 → target
                            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', await SEnd_InV(5, target_uid, key, iv, region))
                            await asyncio.sleep(0.3)

                            # invite #2 → commander নিজে
                            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', await SEnd_InV(5, uid, key, iv, region))
                            await asyncio.sleep(3.5)

                            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', await ExiT(None, key, iv))
                            await safe_send_message(
                                XX,
                                f"[B][C][00FF00]Yay! 5-man group invite sent to {target_uid} and commander ({uid})!\n"
                                f"[FFFFFF]Both players check your invites!",
                                uid, chat_id, key, iv,
                            )
                    except Exception as e:
                        print(f"Inv error: {e}")
                        await safe_send_message(
                            XX,
                            f"[B][C][FF0000]❌ Could not send group invites: {e}",
                            uid, chat_id, key, iv,
                        )


                elif inPuTMsG.startswith('/spm '):
                    parts = inPuTMsG.strip().split()
                    if len(parts) >= 2 and parts[1].isdigit():
                        tgt = parts[1]
                        if tgt in spm_tasks: spm_tasks[tgt].cancel()
                        spam_targets.add(tgt); save_spam_targets()
                        spm_tasks[tgt] = asyncio.create_task(spm_loop(tgt, key, iv))
                        await safe_send_message(XX, f"[B][C][00FF00]✅ Spam started for {tgt}", uid, chat_id, key, iv)
                    else: await safe_send_message(XX, f"[B][C][FF0000]Usage: /spm <uid>", uid, chat_id, key, iv)

                elif inPuTMsG.startswith('/stp '):
                    parts = inPuTMsG.strip().split()
                    if len(parts) >= 2 and parts[1] in spm_tasks:
                        spm_tasks[parts[1]].cancel(); del spm_tasks[parts[1]]
                        if parts[1] in spam_targets: spam_targets.remove(parts[1]); save_spam_targets()
                        await safe_send_message(XX, f"[B][C][00FF00]✅ Spam stopped", uid, chat_id, key, iv)
                    else: await safe_send_message(XX, f"[B][C][FF0000]❌ No active spam", uid, chat_id, key, iv)

                elif inPuTMsG.startswith('/gh '):
                    parts = inPuTMsG.split(' ', 2)
                    if len(parts) >= 3 and bot_uid is not None:
                        teamcode = parts[1].strip(); name = parts[2].strip()
                        try:
                            pending_ghost_future = asyncio.Future()
                            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', await JoinSq_original(teamcode, key, iv))
                            try: await asyncio.wait_for(pending_ghost_future, timeout=8.0)
                            except asyncio.TimeoutError:
                                await safe_send_message(XX, f"[B][C][FF0000]❌ No response", uid, chat_id, key, iv)
                                pending_ghost_future = None; continue
                            await SEndPacKeT(whisper_writer, online_writer, 'OnLine', await ExiT(None, key, iv))
                            await asyncio.sleep(0.2)
                            for _ in range(4):
                                await SEndPacKeT(whisper_writer, online_writer, 'OnLine', await GhostPakcet(ghost_team_id, name, ghost_squad_code, key, iv))
                                await asyncio.sleep(0.1)
                            await safe_send_message(XX, f"[B][C][00FF00]✅ Ghost joined as {name}", uid, chat_id, key, iv)
                            pending_ghost_future = None
                        except Exception as e:
                            await safe_send_message(XX, f"[B][C][FF0000]❌ {e}", uid, chat_id, key, iv)
                            pending_ghost_future = None

                elif inPuTMsG.strip().startswith('/msg'):
                            print('Processing message spam command')
                            global msg_spam_task
                            parts = inPuTMsG.strip().split()
    
                            if len(parts) < 3:
                                error_msg = f"[B][C][FF0000]❌ ERROR! Usage: /msg (message) (times)\n"
                                error_msg += f"[FFFFFF]Example: /msg Hello Team! 5\n"
                                error_msg += f"[FFFFFF]Will send 'Hello Team!' 5 times in team chat\n"
                                await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                            else:
                                try:
                                    # Extract message and times
                                    times = int(parts[-1]) # Last part is the number
            
                                    # Reconstruct the message (everything except first part and last part)
                                    message_text = ' '.join(parts[1:-1])
            
                                    if times <= 0:
                                        error_msg = f"[B][C][FF0000]❌ ERROR! Times must be greater than 0!\n"
                                        await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                                    
                                    elif not message_text.strip():
                                        error_msg = f"[B][C][FF0000]❌ ERROR! Message cannot be empty!\n"
                                        await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                                    else:
                                        # Stop any existing message spam
                                      
                                        if msg_spam_task and not msg_spam_task.done():
                                            
                                            msg_spam_running = False
                                            msg_spam_task.cancel()
                                            await asyncio.sleep(0.1)
                
                                        # Check if we have the chat_id from the message
                                        # If not, use the bot's UID from login data
                                        chat_id = chat_id
                
                                        # Send initial message
                                        initial_msg = f"[B][C][00FF00]📢 MESSAGE SPAM STARTING!\n"
                                        initial_msg += f"[FFFFFF]Message: {message_text}\n"
                                        initial_msg += f"[FFFFFF]Times: {times}\n"
                                        initial_msg += f"[FFFFFF]Chat: Team/Squad Chat\n"
                                        initial_msg += f"[00FF00]Sending messages...\n"
                                        await safe_send_message(response.Data.chat_type, initial_msg, uid, chat_id, key, iv)
                
                                        # Start message spam
                                        msg_spam_running = True
                                        msg_spam_task = asyncio.create_task(
                                            msg_spam_loop(message_text, times, chat_id, key, iv, region)
                                        )
                
                                        # Wait for completion and send result
                                        asyncio.create_task(
                                            handle_msg_spam_completion(msg_spam_task, message_text, times, uid, chat_id, response.Data.chat_type, key, iv)
                                        )
                                        
                                except ValueError:
                                    error_msg = f"[B][C][FF0000]❌ ERROR! Invalid format!\n"
                                    error_msg += f"[FFFFFF]Usage: /msg (message) (times)\n"
                                    error_msg += f"[FFFFFF]Example: /msg Hello World! 10\n"
                                    await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                                except Exception as e:
                                    error_msg = f"[B][C][FF0000]❌ ERROR: {str(e)}\n"
                                    await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)

                        # Add stop command
                elif inPuTMsG.strip() == '/stop msg':
                            if msg_spam_task and not msg_spam_task.done():
                                msg_spam_running = False
                                msg_spam_task.cancel()
                                success_msg = f"[B][C][00FF00]✅ MESSAGE SPAM STOPPED!\n[FFFFFF]All message sending has been stopped.\n"
                                await safe_send_message(response.Data.chat_type, success_msg, uid, chat_id, key, iv)
                            else:
                                error_msg = f"[B][C][FF0000]❌ No active message spam to stop!\n"
                                await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                        
                        #TEAM SPAM MESSAGE COMMAND
                elif inPuTMsG.strip().startswith('/ms '):
                            print('Processing /ms command')

                            try:
                                parts = inPuTMsG.strip().split(maxsplit=1)

                                if len(parts) < 2:
                                    error_msg = (
                                        "[B][C][FF0000]❌ ERROR! Usage:\n"
                                        "/ms <message>\n"
                                        "Example: /ms Buddy"
                                    )
                                    await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                                else:
                                    user_message = parts[1].strip()

                                    for _ in range(30):
                                        color = get_random_color()  # random color from your list
                                        colored_message = f"[B][C]{color} {user_message}"  # correct format
                                        await safe_send_message(response.Data.chat_type, colored_message, uid, chat_id, key, iv)
                                        await asyncio.sleep(0.5)

                            except Exception as e:
                                error_msg = f"[B][C][FF0000]❌ ERROR! Something went wrong:\n{str(e)}"
                                await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                                

        

                elif inPuTMsG.strip().startswith('/mg'):
                            print('Processing wave message command')
                          
                            parts = inPuTMsG.strip().split()
    
                            if len(parts) < 2:
                                error_msg = f"[B][C][FF0000]❌ Usage: /mg (message) [repeats=5]\n"
                                error_msg += f"[FFFFFF]Example: /mg hello 3\n"
                                error_msg += f"[FFFFFF]Will send: h, he, hel, hell, hello, hell, hel, he, h\n"
                                await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                            else:
                                try:
                                    # Get message and optional repeats
                                    message_text = parts[1]
                                    repeats = 5  # Default
            
                                    if len(parts) > 2:
                                        repeats = int(parts[2])
            
                                    if repeats <= 0:
                                        error_msg = f"[B][C][FF0000]❌ Repeats must be > 0!\n"
                                        await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                                    elif repeats > 10:
                                        error_msg = f"[B][C][FF0000]❌ Max 10 repeats!\n"
                                        await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                                    elif len(message_text) < 2:
                                        error_msg = f"[B][C][FF0000]❌ Message must be at least 2 characters!\n"
                                        await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                                    else:
                                        if mg_spam_task and not mg_spam_task.done():
                                            msg_spam_running = False
                                            mg_spam_task.cancel()
                                            await asyncio.sleep(0.5)
                
                                        # Calculate total messages
                                        total_messages_per_cycle = (len(message_text) * 2) - 2
                                        total_messages = total_messages_per_cycle * repeats
                
                                        initial_msg = f"[B][C][00FF00]🌊 WAVE MESSAGE STARTING!\n"
                                        initial_msg += f"[FFFFFF]Message: {message_text}\n"
                                        initial_msg += f"[FFFFFF]Repeats: {repeats} cycles\n"
                                        initial_msg += f"[FFFFFF]Pattern: h → he → hel → hell → hello → hell → hel → he → h\n"
                                        initial_msg += f"[00FF00]Total messages: {total_messages}\n"
                                        await safe_send_message(response.Data.chat_type, initial_msg, uid, chat_id, key, iv)
                                        
                                        # Start wave messages
                                        msg_spam_running = True
                                        mg_spam_task = asyncio.create_task(
                                            send_wave_messages(message_text, repeats, chat_id, key, iv, region)
                                        )
                
                                        # Handle completion
                                        asyncio.create_task(
                                            handle_wave_completion(mg_spam_task, message_text, repeats, uid, chat_id, response.Data.chat_type, key, iv)
                                        )
                
                                except ValueError:
                                    error_msg = f"[B][C][FF0000]❌ Invalid format!\n"
                                    await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                        
                elif inPuTMsG.startswith('/bpkt '):
                    parts = inPuTMsG.strip().split()
                    if len(parts) >= 2 and parts[1].isdigit():
                        if ban_task and not ban_task.done():
                            ban_running = False; ban_task.cancel(); ban_targets.clear(); await asyncio.sleep(0.3)
                        ban_targets.add(parts[1]); ban_task = asyncio.create_task(ban_loop(key, iv))
                        await safe_send_message(XX, f"[B][C][00FF00]✅ Ban packet spam started on {parts[1]}", uid, chat_id, key, iv)
                    else: await safe_send_message(XX, f"[B][C][FF0000]Usage: /bpkt <uid>", uid, chat_id, key, iv)

                elif inPuTMsG.startswith('/reject '):
                    parts = inPuTMsG.strip().split()
                    if len(parts) >= 2 and parts[1].isdigit():
                        if reject_spam_task and not reject_spam_task.done():
                            reject_spam_running = False; reject_spam_task.cancel(); await asyncio.sleep(0.3)
                        await safe_send_message(XX, f"[B][C][FFFF00]🌀 Reject spam started on {parts[1]}", uid, chat_id, key, iv)
                        reject_spam_running = True
                        reject_spam_task = asyncio.create_task(reject_spam_loop(parts[1], key, iv))
                    else: await safe_send_message(XX, f"[B][C][FF0000]Usage: /reject <uid>", uid, chat_id, key, iv)

                elif inPuTMsG.strip() == '/reject_stop':
                    if reject_spam_task and not reject_spam_task.done():
                        reject_spam_running = False; reject_spam_task.cancel()
                        await safe_send_message(XX, f"[B][C][00FF00]✅ Reject spam stopped", uid, chat_id, key, iv)

                # (old /fast and /p moved into main emote block above)

                elif inPuTMsG.strip().startswith('/title') or inPuTMsG.strip().startswith('/alltitles'):
                    titles_list = [905090075, 904990072, 904990069, 905190079, 904090014, 904090015, 904090024, 904090025, 904090026, 904090027, 904990070, 904990071]
                    await safe_send_message(XX, f"[B][C][FFFF00]🎖️ Sending {len(titles_list)} titles...", uid, chat_id, key, iv)
                    for tid in titles_list:
                        try:
                            pkt = await convert_kyro_to_your_system(int(uid), chat_id, key, iv, nickname="BUDDy", title_id=tid)
                            if pkt and whisper_writer:
                                whisper_writer.write(pkt); await whisper_writer.drain()
                            await asyncio.sleep(2)
                        except Exception as e: print(f"Title error: {e}")
                    await safe_send_message(XX, f"[B][C][00FF00]✅ All titles sent!", uid, chat_id, key, iv)

                elif inPuTMsG.strip().startswith('/animation'):
                    parts = inPuTMsG.strip().split()
                    anim_ids = {"1": 914000002, "2": 914000003, "3": 914038001, "4": 914039001, "5": 914042001, "6": 914044001, "7": 914047001, "8": 914047002, "9": 914048001, "10": 914050001, "11": 914051001, "12": 914053001}
                    if len(parts) < 2:
                        lst = "1-rampage\n2-cannibal\n3-devil\n4-scorpio\n5-frostfire\n6-paradox\n7-naruto\n8-aurora\n9-midnight\n10-itachi\n11-dreamspace\n12-eclipse"
                        await safe_send_message(XX, f"[B][C][FFFF00]Animations:\n{lst}", uid, chat_id, key, iv)
                    elif parts[1] in anim_ids:
                        try:
                            pkt = await animation_packet(anim_ids[parts[1]], key, iv)
                            if pkt and online_writer:
                                online_writer.write(pkt); await online_writer.drain()
                            await safe_send_message(XX, f"[B][C][00FF00]✅ Animation {parts[1]} sent!", uid, chat_id, key, iv)
                        except Exception as e: print(f"Anim error: {e}")
                    else: await safe_send_message(XX, f"[B][C][FF0000]❌ Animation not found", uid, chat_id, key, iv)

                elif inPuTMsG.strip().startswith('/b '):
                    parts = inPuTMsG.strip().split()
                    bundle_ids = {"1": 914000002, "2": 914000003, "3": 914038001, "4": 914039001, "5": 914042001, "6": 914044001, "7": 914047001, "8": 914047002, "9": 914048001, "10": 914050001, "11": 914051001, "12": 914053001}
                    if len(parts) < 2: await safe_send_message(XX, f"[B][C][FFFF00]Usage: /b <1-12>", uid, chat_id, key, iv)
                    elif parts[1] in bundle_ids:
                        bid = bundle_ids[parts[1]]
                        try:
                            anim_pkt = await animation_packet(bid, key, iv)
                            if anim_pkt and online_writer:
                                online_writer.write(anim_pkt); await online_writer.drain()
                            await asyncio.sleep(3)
                            b_pkt = await Look_Changer(bid, key, iv, look_type=1, region=region)
                            if b_pkt and online_writer:
                                online_writer.write(b_pkt); await online_writer.drain()
                            await safe_send_message(XX, f"[B][C][00FF00]✅ Bundle {parts[1]} sent!", uid, chat_id, key, iv)
                        except Exception as e: print(f"Bundle error: {e}")
                    else: await safe_send_message(XX, f"[B][C][FF0000]❌ Bundle not found", uid, chat_id, key, iv)

                elif inPuTMsG.strip().startswith('/sticker'):
                    try:
                        pkt = await send_sticker_packet(uid, chat_id, key, iv)
                        if pkt and whisper_writer:
                            whisper_writer.write(pkt); await whisper_writer.drain()
                    except Exception as e: print(f"Sticker error: {e}")


                elif inPuTMsG.strip().startswith('/propose '):
                    name = inPuTMsG.strip()[9:].strip()
                    msg = f"[B][C][FF1493]💍 {name} 💍\n\nতুই আমার জীবন, তুই আমার সব।\nআমার হয়ে যাবি? 💕\n\n[FF69B4]❤️ প্রেমের প্রস্তাব ❤️"
                    P = await SEndMsG(XX, msg, uid, chat_id, key, iv)
                    await SEndPacKeT(whisper_writer, online_writer, 'ChaT', P)

                elif inPuTMsG.strip().startswith('/flirt '):
                    name = inPuTMsG.strip()[7:].strip()
                    flirts = [
                        f"[B][C][FF69B4]{name} তোর চোখে ডুবে গেলাম! 😍",
                        f"[B][C][FF1493]{name} তুই কি চাঁদ থেকে এসেছিস? 🌙",
                        f"[B][C][FF66CC]{name} তোর হাসি আমার হার্টবিট বাড়ায়! 💓",
                        f"[B][C][FF00FF]{name} তুই আমার স্বপ্নের রাজকুমারী! 👑",
                    ]
                    for m in flirts:
                        P = await SEndMsG(XX, m, uid, chat_id, key, iv)
                        await SEndPacKeT(whisper_writer, online_writer, 'ChaT', P)
                        await asyncio.sleep(1.2)

                elif inPuTMsG.strip().startswith('/kiss '):
                    name = inPuTMsG.strip()[6:].strip()
                    msg = f"[B][C][FF1493]💋 {name} কে চুমু দিলাম! 😘\n[FF69B4]❤️❤️❤️"
                    P = await SEndMsG(XX, msg, uid, chat_id, key, iv)
                    await SEndPacKeT(whisper_writer, online_writer, 'ChaT', P)

                elif inPuTMsG.strip().startswith('/hug '):
                    name = inPuTMsG.strip()[5:].strip()
                    msg = f"[B][C][FF69B4]🤗 {name} কে জড়িয়ে ধরলাম! 💕"
                    P = await SEndMsG(XX, msg, uid, chat_id, key, iv)
                    await SEndPacKeT(whisper_writer, online_writer, 'ChaT', P)

                elif inPuTMsG.strip().startswith('/marry '):
                    name = inPuTMsG.strip()[7:].strip()
                    msg = f"[B][C][FF1493]💍 {name} তুই আমার হয়ে যাবি? 💍\n[FF69B4]❤️ বিয়ে করবো ❤️"
                    P = await SEndMsG(XX, msg, uid, chat_id, key, iv)
                    await SEndPacKeT(whisper_writer, online_writer, 'ChaT', P)

                elif inPuTMsG.strip().startswith('/bf '):
                    name = inPuTMsG.strip()[4:].strip()
                    msg = f"[B][C][FF69B4]💕 {name} তুই আমার বয়ফ্রেন্ড! 💕"
                    P = await SEndMsG(XX, msg, uid, chat_id, key, iv)
                    await SEndPacKeT(whisper_writer, online_writer, 'ChaT', P)

                elif inPuTMsG.strip().startswith('/gf '):
                    name = inPuTMsG.strip()[4:].strip()
                    msg = f"[B][C][FF69B4]💕 {name} তুই আমার গার্লফ্রেন্ড! 💕"
                    P = await SEndMsG(XX, msg, uid, chat_id, key, iv)
                    await SEndPacKeT(whisper_writer, online_writer, 'ChaT', P)

                elif inPuTMsG.strip().startswith('/ship '):
                    parts = inPuTMsG.strip()[6:].split()
                    if len(parts) >= 2:
                        pct = random.randint(1, 100)
                        msg = f"[B][C][FF1493]💘 {parts[0]} + {parts[1]} = {pct}% 💘"
                    else: msg = f"[B][C][FF0000]Usage: /ship <name1> <name2>"
                    P = await SEndMsG(XX, msg, uid, chat_id, key, iv)
                    await SEndPacKeT(whisper_writer, online_writer, 'ChaT', P)

                elif inPuTMsG.strip().startswith('/crush '):
                    name = inPuTMsG.strip()[7:].strip()
                    pct = random.randint(50, 100)
                    msg = f"[B][C][FF69B4]💗 {name} তোর প্রতি আমার ক্রাশ {pct}% 💗"
                    P = await SEndMsG(XX, msg, uid, chat_id, key, iv)
                    await SEndPacKeT(whisper_writer, online_writer, 'ChaT', P)

                elif inPuTMsG.strip().startswith('/breakup '):
                    name = inPuTMsG.strip()[9:].strip()
                    msg = f"[B][C][FF0000]💔 {name} আমাদের সম্পর্ক শেষ! 😭"
                    P = await SEndMsG(XX, msg, uid, chat_id, key, iv)
                    await SEndPacKeT(whisper_writer, online_writer, 'ChaT', P)

                elif inPuTMsG.strip().startswith('/later '):
                    try:
                        name = inPuTMsG.strip()[7:].strip()
                        msg = f"[B][C][FF1493]💌 প্রিয় {name} 💌\n\nতোর یادেতে দিন কাটে,\nতোর ছাড়া মন কাঁদে,\nতুই ছাড়া এই দুনিয়ায়,\nকিছুই যেন ভালো লাগে না।\n\n💕 তোর সবসময় 💕"
                        P = await SEndMsG(XX, msg, uid, chat_id, key, iv)
                        await SEndPacKeT(whisper_writer, online_writer, 'ChaT', P)
                    except Exception as e: print(f"Later error: {e}")

                elif inPuTMsG.strip().startswith('/sadlater '):
                    try:
                        name = inPuTMsG.strip()[10:].strip()
                        msg = f"[B][C][808080]💔 {name} 💔\n\nভাঙা মনের কথা শোনো,\nপ্রতি রাতে তোর কথা আসে,\nতুই দূরে তবুও,\nতোর স্মৃতি প্রতি পলে কাঁদায়।\n\n💔 একা 💔"
                        P = await SEndMsG(XX, msg, uid, chat_id, key, iv)
                        await SEndPacKeT(whisper_writer, online_writer, 'ChaT', P)
                    except Exception as e: print(f"Sad error: {e}")

                elif inPuTMsG.strip() == '/joke':
                    jokes = [
                        "শিক্ষক: বাড়ির কাজ করেছ?\nছাত্র: স্যার, লোডশেডিং ছিল।\nশিক্ষক: দিনে করলে না কেন?\nছাত্র: দিনে তো ঘুম পায়!\n😂😂",
                        "স্ত্রী: জানু, আমি সুন্দর নাকি তোমার মা?\nস্বামী: দুজনেই সুন্দর।\nস্ত্রী: সত্যি বলো!\nস্বামী: সত্যি সবসময় তিতা হয়!\n🤣",
                    ]
                    P = await SEndMsG(XX, f"[B][C][FFFF00]😂 JOKE 😂\n\n{random.choice(jokes)}", uid, chat_id, key, iv)
                    await SEndPacKeT(whisper_writer, online_writer, 'ChaT', P)

                # GALi / JOKE MESSAGE
                elif inPuTMsG.strip().startswith('/gali'):
                            print('Processing /gali command')

                            try:
                                parts = inPuTMsG.strip().split(maxsplit=2)  # maxsplit=2: /p name <optional number>

                                # Minimum 2 parts: /p name
                                if len(parts) < 2:
                                    error_msg = (
                                        "[B][C][FF0000]❌ ERROR! Usage:\n"
                                        "/gali <name>\n"
                                        "Example: /gali lover"
                                    )
                                    await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                                else:
                                    name = parts[1].strip()  # second part is always name
                                    # third part (if exists) can be anything, just ignore for fun randomization
                                    # parts[2] exists only if len(parts)==3, we don't need to store/use it

                                name_lower = name.lower()

                                # BLOCK CHECK (substring, case-insensitive)
                                blocked = False
                                for blocked_name in BLOCKED_NAMES:
                                    if blocked_name.lower() in name_lower:
                                        blocked = True
                                        break

                                if blocked:
                                    block_msg = """[B][C][FF69B4]╔═══『 PROTECTED 』═══╗

[FFFFFF]˗ˏˋ » Oops! This name is special ˎˊ˗

[FF0000]✖ You can’t target this name!
[FFFF00]｡°⚠︎°｡ It’s under protection 💖

[00FFFF]Please try another name (｡•́︿•̀｡)

[FF2EEE]⊹˚‧︵‿୨ Stay Kind ୧‿︵‧˚⊹"""
                                    await safe_send_message(response.Data.chat_type, block_msg, uid, chat_id, key, iv)
                                    continue

                                # Example safe/funny messages
                                messages = [
"{Name} TƐRI SƐXY BHEN KI CHXT ME ME L0DA DAAL KAR RAAT BHAR JOR JOR SE CH0DUNGA",
"{Name} MADHERXHOD TƐRI MÁÁ KI KALI G4ND MƐ LÀND MARU",
"{Name} TƐRI BHƐN KI TIGHT CHXT KO 5G KI SPEED SE CHÒD DU",
"{Name} TƐRI BEHEN KI CHXT ME L4ND MARU",
"{Name} TƐRI MÁÁ KI CHXT 360 BAR",
"{Name} TƐRI BƐHƐN KI CHXT 720 BAR",
"{Name} BEHEN KE L0DE",
"{Name} MADARCHXD",
"{Name} BETE TƐRA BAAP HUN ME",
"{Name} G4NDU APNE BAAP KO H8 DEGA",
"{Name} KI MÀÀ KI CHXT PER NIGHT 4000",
"{Name} KI BƐHƐN KI CHXT PER NIGHT 8000",
"{Name} R4NDI KE BACHHƐ APNE BAP KO H8 DEGA",
"BANGLADESH KA NO-1 G4NDU {Name}",
"{Name} CHAPAL CH0R",
"{Name} TƐRI MÀÀ KO GB ROAD PE BETHA KE CHXDUNGA",
"{Name} BETA JHULA JHUL APNE BAAP KO MAT BHUL",
"{Name} Sade huye gobar ke sukhe huye kande me khel rahe gobraile",
"{Name} TERI MUMMY KI CHUMT ITNI GEHRI HAI KI PURA BURJ KHALIFA ANDAR SAMA SAKTA HAI 🗽🤣",
"{Name} Teri Maa Aur Teri Behn ko itna ch*dunga ki chudne ka jaga kam pad jayega",
"{Name} Ullu ke pattha madarchxd ga.ndu sale",
"{Name} খান🤫কির ছেলে !!",
"{Name} মাদার চো🤫দ, তোর মা🤫কে চু🤫দি !!",
"{Name} মাদার চো🤫দ, তোর মা🤫কে 5G স্পিডে চু🤫দি !!",
"{Name} বোকাচো🤫দা, তোর মা🤫কে কন🤫ডম লাগিয়ে চু🤫দি !!",
"{Name} বোকাচো🤫দা, তোর মা🤫কে প্রতিদিন ১০,০০০ টাকার সার্ভিস দেই !!",
"F🤫U🤫C🤫K {Name} !!",
"{Name} মাদার চো🤫দ, পো🤫দ মে🤫রে দিবো !!",
"{Name} মাদার চো🤫দ !!",
"{Name} খান🤫কি, আমি তোর বা🤫প !!",
"{Name} তোর মা🤫কে আমি চু🤫ই🤫দা তোরে জন্মায় ছি !!",
"{Name} বোকাচো🤫দা, খান🤫কির ছেলে !!",
"{Name} মাদার চো🤫দ, তোর মা🤫কে ১৮০ কি.মি. স্পিডে চু🤫দি !!",
"{Name} খা🤫ন🤫কির ছেলে বট, নুব🤫রা প্লেয়ার !!",
"বাংলাদেশের NO-1 বট PLAYER {Name}",
"{Name} জুতা চোর !!",
"{Name} মাদারচো🤫দ, ফ্রি ফায়ার খেলা বাদ দিয়ে লুডু খেল যা !!",
"{Name} যাই করিস, আমি তোর আব্বা এইডা কখনো ভুলিস না !!",
"{Name} তোর মা🤫রে উড়া🤫ইয়া ঘুরা🤫ইয়া চু🤫দি খা🤫ন🤫কির পো🤫লা "
        ]

                                for msg in messages:
                                    colored_message = f"[B][C]{get_random_color()} {msg.replace('{Name}', name.title())}"
                                    await safe_send_message(response.Data.chat_type, colored_message, uid, chat_id, key, iv)
                                    await asyncio.sleep(0.5)

                            except Exception as e:
                                error_msg = f"[B][C][FF0000]❌ ERROR! Something went wrong:\n{str(e)}"
                                await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                                
                elif inPuTMsG.strip().startswith('/love '):
                            print('Processing /love command')

                            try:
                                parts = inPuTMsG.strip().split(maxsplit=2)  # maxsplit=2: /p name <optional number>

                                # Minimum 2 parts: /p name
                                if len(parts) < 2:
                                    error_msg = (
                                        "[B][C][FF0000]❌ ERROR! Usage:\n"
                                        "/love <name>\n"
                                        "Example: /love lover"
                                    )
                                    await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                                else:
                                    name = parts[1].strip()  # second part is always name
                                    # third part (if exists) can be anything, just ignore for fun randomization
                                    # parts[2] exists only if len(parts)==3, we don't need to store/use it

            
                                    # ADD THIS CHECK - Prevent targeting yourself
                                    if name.lower() in [n.lower() for n in BLOCKED_NAMES]:
                                        error_msg = """[B][C][FF69B4]╔═══『 PROTECTED 』═══╗

[FFFFFF]˗ˏˋ » Oops! This name is special ˎˊ˗

[FF0000]✖ You can’t target this name!
[FFFF00]｡°⚠︎°｡ It’s under protection 💖

[00FFFF]Please try another name (｡•́︿•̀｡)

[FF2EEE]⊹˚‧︵‿୨ Stay Kind ୧‿︵‧˚⊹"""
                                        await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                                        continue
            
                                    # Rest of your code continues here...
                                    messages = [
                                        "{Name} আমি শুধু তোমাকেই ভালোবাসি ♡",
"{Name} তুমি আমার সবকিছু ♡",
"{Name} তোমার জন্য আমার হৃদয় সবসময় ধড়ফড় করে ♡",
"{Name} তুমি আমার জীবনের আলো ♡️",
"{Name} তুমি আমার জীবনের সবচেয়ে বড় সুখ ♡",
"{Name} তুমি আমার হৃদয়ের সবচেয়ে কাছের মানুষ ♡",
"{Name} তুমি আমার স্বপ্নের মানুষ ♡",
"{Name} তোমার মতো মানুষ খুব কমই দেখা যায়",
"{Name} তোমাকে ছাড়া আমার দিন কাটে না ♡",
"{Name} তুমি আমার স্বপ্নের মানুষ ♡",
"{Name} আমি সবসময় তোমার পাশে থাকতে চাই ♡",
"{Name} আমি তোমাকে ভালোবাসি ♡",
"{Name} তোমাকে ছাড়া আমার জীবন অসম্পূর্ণ ♡",
"{Name} তোমার হাসি আমার পৃথিবী আলোকিত করে ♡♡",
"{Name} I LOVE YOU ♡",
"{Name} তুমি আমার জান ♡",
"{Name} I LOVE YOU JAN ♡",
"{Name} তুমি আমার হৃদয়ের সবচেয়ে সুন্দর অনুভূতি... ❤️",
"{Name} তোমার সাথে কাটানো প্রতিটা মুহূর্ত আমার কাছে অমূল্য... 🤍",
"{Name} তোমাকে ভালোবাসাটা আমার জীবনের সবচেয়ে সুন্দর সিদ্ধান্ত... 🌹",
"{Name} তোমার হাসির মাঝেই আমি আমার সুখ খুঁজে পাই... 😊❤️",
"{Name} তোমাকে ছাড়া আমার প্রতিটা দিন যেন অসম্পূর্ণ... 💕",
"{Name} তোমার হাতটা সারাজীবন ধরে রাখতে চাই... 🫶",
"{Name} তোমার চোখেই আমি আমার পুরো পৃথিবী দেখি... 🌍❤️",
"{Name} তোমার পাশে থাকলেই নিজেকে সম্পূর্ণ মনে হয়... 🤍",
"{Name} ভালোবাসা যদি কাউকে বলে, তাহলে সেটা শুধু তুমি... 💖",
"{Name} তোমার সাথে বুড়ো হতে চাই... 🌸",
"{Name} তুমি আমার প্রতিটা প্রার্থনার সবচেয়ে সুন্দর উত্তর... ✨",
"{Name} আমার প্রতিটা সকাল শুরু হোক তোমার হাসি দিয়ে... ☀️❤️",
"{Name} তোমার জন্য হাজারবার প্রেমে পড়তে রাজি আছি... 💘",
"{Name} তুমি আমার জীবনের সবচেয়ে সুন্দর গল্প... 📖💕",
"{Name} তোমাকে ভালোবাসার কোনো শেষ নেই... ♾️❤️",
"{Name} তোমার জন্য আমার হৃদয়ে সবসময় একটা আলাদা জায়গা থাকবে... 🤍",
"{Name} তুমি থাকলে সবকিছুই সহজ মনে হয়... 🌹",
"{Name} তোমাকে নিয়ে হাজারটা স্বপ্ন দেখতে ভালো লাগে... 💭❤️",
"{Name} তুমি আমার হাসির কারণ, আমার শান্তির ঠিকানা... 🥹",
"{Name} তোমার সাথে কাটানো প্রতিটা সেকেন্ড আমার কাছে স্পেশাল... 💞",
"{Name} তোমাকে যত ভালোবাসি, তা ভাষায় প্রকাশ করা সম্ভব না... ❤️",
"{Name} পৃথিবী বদলে গেলেও তোমার জন্য আমার অনুভূতি বদলাবে না... 🌍🤍",
"{Name} তোমার পাশে থাকাটাই আমার সবচেয়ে বড় সুখ... 💕",
"{Name} তুমি আমার হৃদয়ের একমাত্র রানী/রাজা... 👑❤️",
"{Name} তোমাকে ছাড়া ভবিষ্যতের কথা ভাবতেই পারি না... 🌙",
"{Name} তোমার ভালো থাকাটাই আমার সবচেয়ে বড় চাওয়া... 🤍",
"{Name} আমার হৃদয়টা অনেক আগেই তোমার হয়ে গেছে... 💘",
"{Name} তোমাকে ভালোবাসার জন্য কোনো কারণ লাগে না... ❤️",
"{Name} আমার শেষ নিঃশ্বাস পর্যন্ত তোমাকেই ভালোবাসতে চাই... 🌹",
"{Name} I Love You Today, Tomorrow, Forever... ❤️∞"
                                            ]

                                    # Send each message one by one with random color
                                    for msg in messages:
                                        colored_message = f"[B][C][00FFFF] {msg.replace('{Name}', name.upper())}"
                                        await safe_send_message(response.Data.chat_type, colored_message, uid, chat_id, key, iv)
                                        await asyncio.sleep(2)

                            except Exception as e:
                                error_msg = f"[B][C][FF0000]❌ ERROR! Something went wrong:\n{str(e)}"
                                await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)


                        # Then in the /love command handler, add this check:
                elif inPuTMsG.strip().startswith('/crush '):
                            print('Processing /love command')

                            try:
                                parts = inPuTMsG.strip().split(maxsplit=2)  # maxsplit=2: /p name <optional number>

                                # Minimum 2 parts: /p name
                                if len(parts) < 2:
                                    error_msg = (
                                        "[B][C][FF0000]❌ ERROR! Usage:\n"
                                        "/love <name>\n"
                                        "Example: /love lover"
                                    )
                                    await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                                else:
                                    name = parts[1].strip()  # second part is always name
                                    # third part (if exists) can be anything, just ignore for fun randomization
                                    # parts[2] exists only if len(parts)==3, we don't need to store/use it

            
                                    # ADD THIS CHECK - Prevent targeting yourself
                                    if name.lower() in [n.lower() for n in BLOCKED_NAMES]:
                                        error_msg = """[B][C][FF69B4]╔═══『 PROTECTED 』═══╗
+
+[FFFFFF]˗ˏˋ » Oops! This name is special ˎˊ˗
+
+[FF0000]✖ You can’t target this name!
+[FFFF00]｡°⚠︎°｡ It’s under protection 💖
+
+[00FFFF]Please try another name (｡•́︿•̀｡)
+
+[FF2EEE]⊹˚‧︵‿୨ Stay Kind ୧‿︵‧˚⊹"""
                                        await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                                        continue
            
                                    # Rest of your code continues here...
                                    messages = [
"{Name} তোমার কথা বলার ধরনটা আমার ভীষণ ভালো লাগে... 🥹❤️",
"{Name} তোমার চোখ দুটোতে তাকালেই আমি হারিয়ে যাই... 👀💖",
"{Name} তোমার চুলগুলো তোমাকে আরও সুন্দর করে তোলে... 🌸",
"{Name} তোমার হাসিটা আমার দিনের সবচেয়ে সুন্দর মুহূর্ত... 😊💞",
"{Name} তোমার কণ্ঠ শুনলেই মনটা শান্ত হয়ে যায়... 🎶❤️",
"{Name} তোমার সরলতাটাই আমাকে সবচেয়ে বেশি টানে... 🤍",
"{Name} তোমার personality-টা সত্যিই অসাধারণ... ✨",
"{Name} তোমার care করার ধরনটা অনেক ভালো লাগে... 💕",
"{Name} তোমার innocence-টাই আমার সবচেয়ে প্রিয়... 🥹",
"{Name} তোমার চোখের মায়ায় বারবার আটকে যাই... 💘",
"{Name} তোমার cute expression-গুলো বারবার দেখতে ইচ্ছে করে... 😍",
"{Name} তোমার smile দেখলেই নিজের অজান্তেই হাসি চলে আসে... 🌹",
"{Name} তোমার presence-টাই আলাদা একটা শান্তি দেয়... ❤️",
"{Name} তোমাকে দেখলেই পৃথিবীটা একটু বেশি সুন্দর লাগে... 🌍💖",
"{Name} তোমার style-টা একদম unique... ✨",
"{Name} তোমার face-এর simplicity-টাই আমাকে মুগ্ধ করে... 🤍",
"{Name} তোমার ছোট ছোট অভ্যাসগুলোও আমার ভীষণ ভালো লাগে... 🥰",
"{Name} তোমার চোখের একটুখানি তাকানোতেই হৃদয় কেঁপে ওঠে... 💓",
"{Name} তোমাকে যত দেখি, ততই বেশি ভালো লাগে... 💞",
"{Name} তোমাকে প্রথম দেখার অনুভূতিটা আজও একই রকম আছে... 🌸",
"{Name} তোমার একটা হাসির জন্য সারাদিন অপেক্ষা করতে পারি... 💖",
"{Name} তুমি জানো না, কিন্তু তুমি আমার favourite person... ❤️",
"{Name} তোমার নামটা শুনলেই মনটা ভালো হয়ে যায়... 😊",
"{Name} তোমার সাথে একবার কথা বললেই পুরো দিনটা সুন্দর কেটে যায়... 💕",
"{Name} তোমাকে দেখলেই মনে হয়, এটাই তো আমার secret crush... 🤍",
"{Name} তোমার চোখ, তোমার হাসি, তোমার চুল—সবকিছুই অসম্ভব ভালো লাগে... 💘",
"{Name} তোমার মধ্যে এমন একটা মায়া আছে, যেটা আমাকে বারবার তোমার দিকে টেনে নিয়ে যায়... 🥹❤️",
"{Name} তোমাকে দেখার পর থেকেই অন্য কাউকে আর তেমন ভালো লাগে না... 💞",
"{Name} যদি crush-এর কোনো সংজ্ঞা থাকে, তাহলে সেটা শুধু তুমি... 🌹",
"{Name} হয়তো তুমি জানো না, কিন্তু আমার প্রতিটা smile-এর পেছনে তুমিই আছো... ❤️✨",
"{Name} তোমাকে দেখলেই সময়টা যেন একটু ধীরে চলে... 🤍",
"{Name} তোমাকে দেখার পর থেকেই মনটা অকারণেই ভালো থাকে... 🌸",
"{Name} জানো? তোমাকে দেখলে হৃদয়টা একটু অন্যরকম অনুভব করে... 💖",
"{Name} তোমাকে যত দেখি, ততই নতুন করে ভালো লাগে... ✨",
"{Name} তুমি পাশে থাকলে চারপাশটা আরও সুন্দর লাগে... 🤍",
"{Name} তোমাকে দেখার অপেক্ষাটাও আমার কাছে সুন্দর লাগে... 🥹",
"{Name} তোমার একটা হাসি আমার পুরো দিনটা বদলে দিতে পারে... 😊❤️",
"{Name} তোমার চোখে একটা অদ্ভুত শান্তি আছে... 💙",
"{Name} তোমার কথা ভাবলেই অজান্তেই হাসি চলে আসে... 🌹",
"{Name} তুমি বুঝতে পারো না, কিন্তু তোমাকে দেখলেই মনটা নরম হয়ে যায়... 🤍",
"{Name} তোমার উপস্থিতিই আমার কাছে অনেক কিছু... 💕",
"{Name} তোমার দিকে তাকিয়ে থাকতেও ভালো লাগে... 🫶",
"{Name} তোমাকে দেখলে মনে হয়, পৃথিবীতে এখনো সুন্দর মানুষ আছে... 🌸",
"{Name} তোমার নামটাই আমার কাছে আলাদা একটা অনুভূতি... ❤️",
"{Name} তোমার সাথে কাটানো ছোট্ট মুহূর্তগুলোও অনেক মূল্যবান... ✨",
"{Name} তোমাকে দেখার পর থেকেই অনেক গান তোমার কথা মনে করিয়ে দেয়... 🎶🤍",
"{Name} তুমি হয়তো জানো না, কিন্তু তোমাকে দেখলেই মনটা শান্ত হয়ে যায়... 🌙",
"{Name} তোমার একটা glance-ই আমার জন্য যথেষ্ট... 👀💖",
"{Name} তোমার প্রতি এই অনুভূতিটা প্রতিদিন একটু একটু করে বাড়ছে... 💞",
"{Name} তোমাকে ছুঁয়ে নয়, দূর থেকেই ভালো লাগতে শিখেছি... 🤍",
"{Name} তোমাকে নিয়ে ভাবতে কখনো ক্লান্ত লাগে না... 🌹",
"{Name} তোমার হাসির শব্দটাও আমার খুব প্রিয়... 🥹❤️",
"{Name} তুমি আমার অগোচরে আমার favourite হয়ে গেছো... 💕",
"{Name} তোমাকে দেখলেই মনে হয়, আজকের দিনটা ভালো যাবে... ☀️",
"{Name} তোমার মায়ায় পড়াটা আমার সবচেয়ে সুন্দর ভুল... 🤍",
"{Name} তোমাকে দেখার পর থেকেই 'ভালো লাগা' শব্দটার মানে বুঝেছি... 💖",
"{Name} তোমার জন্যই হয়তো অপেক্ষা করতেও ভালো লাগে... 🌸",
"{Name} তুমি কাছে থাকলে হৃদয়টা অকারণেই হাসে... 😊",
"{Name} তোমার কথা ভাবতে ভাবতেই অনেক রাত কেটে যায়... 🌙❤️",
"{Name} তুমি আমার সবচেয়ে সুন্দর অজানা অনুভূতি... 🤍✨"
]

                                    # Send each message one by one with random color
                                    for msg in messages:
                                        colored_message = f"[B][C][00FFFF] {msg.replace('{Name}', name.upper())}"
                                        await safe_send_message(response.Data.chat_type, colored_message, uid, chat_id, key, iv)
                                        await asyncio.sleep(2)

                            except Exception as e:
                                error_msg = f"[B][C][FF0000]❌ ERROR! Something went wrong:\n{str(e)}"
                                await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)

                elif inPuTMsG.strip().startswith('/gd'):
                            print('Processing /gd command')

                            try:
                                parts = inPuTMsG.strip().split(maxsplit=1)

                                if len(parts) < 2:
                                    error_msg = (
                                        "[B][C][FF0000]❌ ERROR! Usage:\n"
                                        "/gd <name>\n"
                                        "Example: /gd Maruf"
                                    )
                                    await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                                else:
                                    # Get everything after /gd
                                    words = parts[1].strip().split()

                                    # Ignore any numeric values (e.g. UIDs)
                                    name = " ".join(word for word in words if not word.isdigit()).strip()

                                    if not name:
                                        error_msg = (
                                            "[B][C][FF0000]❌ ERROR!\n"
                                            "Please provide a valid name."
                                        )
                                        await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                                        continue

                                    # Prevent targeting blocked names
                                    if name.lower() in [n.lower() for n in BLOCKED_NAMES]:
                                        error_msg = (
                                            f"[B][C][FF0000]⚠️ WARNING!\n"
                                            f"[FFFFFF]You cannot target '{name}'!\n"
                                            f"[FF0000]Bot owner protected! ⛔\n"
                                            f"[FFFFFF]Try another name."
                                        )
                                        await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                                        continue

                                    messages = [
"{Name} তুমি সত্যিই অসাধারণ একজন মানুষ!",
"{Name} তোমার পরিশ্রম একদিন বড় সফলতা এনে দেবে!",
"{Name} তুমি ইউনিক, তোমার মতো আর কেউ নেই!",
"{Name} তোমার ভবিষ্যৎ অনেক উজ্জ্বল!",
"{Name} তুমি একজন লিডার হওয়ার যোগ্য!",
"{Name} তোমার হাসি সবার দিন সুন্দর করে দেয়!",
"{Name} সবসময় এমন পজিটিভ থাকো!",
"{Name} তুমি অসাধারণ মানুষ! 🌟",
"{Name} তোমার মেহনত একদিন রঙ দেবে! 🔥",
"{Name} তুমি ইউনিক! 💎",
"{Name} তোমার ভবিষ্যৎ উজ্জ্বল! 🚀",
"{Name} তুমি লিডার হওয়ার যোগ্য! 👑",
"{Name} তোমার হাসি সবার দিন বানায়! 🌈",
"{Name} তুমি সবসময় পজিটিভ থাকো! 💖",
"{Name} তুমি যা চাও তা পাবে! 🏆",
"{Name} তুমি প্রেরণার উৎস! ✨",
"{Name} তোমার ফোকাসই তোমার শক্তি! 🎯",
"{Name} তুমি যা চাও তা অর্জন করার ক্ষমতা তোমার আছে!",
"{Name} তুমি অনুপ্রেরণার উৎস!",
"{Name} নিজের উপর বিশ্বাস রাখো, তুমি পারবে!",
"{Name} তুমি প্রতিদিন আরও ভালো হচ্ছো!",
"{Name} তোমার চিন্তাভাবনা সত্যিই প্রশংসনীয়!",
"{Name} তুমি অনেক দূর যাবে ইনশা🤫আ🤫ল্লা🤫হ!",
"{Name} পৃথিবী তোমার ট্যালেন্ট দেখার অপেক্ষায়!",
"{Name} তুমি শক্ত, আত্মবিশ্বাসী ও সাহসী!",
"{Name} তুমি সত্যিকারের চ্যাম্পিয়ন!",
"{Name} তোমার মতো মানুষ পৃথিবীতে কমই আছে! 🌍",
"{Name} তুমি হার মানো না, এটাই তোমার সবচেয়ে বড় শক্তি! 💪",
"{Name} তোমার পরিশ্রমের ফল একদিন সবার সামনে আসবেই! 🌱",
"{Name} তুমি যেকোনো কঠিন কাজ সহজে করে ফেলতে পারো! ⚡",
"{Name} তোমার উপস্থিতিই সবার মনে আনন্দ আনে! 😊",
"{Name} তুমি সবার সেরা, এটা তুমি নিজেও জানো! 🥇",
"{Name} তোমার স্বপ্নগুলো একদিন সত্যি হবে, বিশ্বাস রাখো! 🌠",
"{Name} তুমি বুদ্ধিমান, সাহসী আর দয়ালু — এই তিনটাই তোমার গুণ! 🌟",
"{Name} তোমার ভেতরে যে সম্ভাবনা আছে তা অসীম! 🚀",
"{Name} তুমি যা করো, মন দিয়ে করো — তুমি পারবেই! 🎯",
"{Name} তোমার হাসিটাই তোমার সবচেয়ে বড় অস্ত্র! 😄",
"{Name} তুমি বন্ধু হিসেবে সেরা! 🤝",
"{Name} তোমার কথায় সবাই উৎসাহ পায়! 🗣️",
"{Name} তুমি কখনো হাল ছেড়ো না, তুমি এই দুনিয়ার সেরাদের একজন! 🏅",
"{Name} তোমার নামের মতোই তোমার ভবিষ্যৎ উজ্জ্বল! ✨",
"{Name} তুমি সত্যি স্পেশাল, কেউ তোমার মতো না! 🌸",
]
                                    

                                    for msg in messages:
                                        colored_message = (
                                            f"[B][C]{get_random_color()} "
                                            f"{msg.replace('{Name}', name.title())}"
                                        )
                                        await safe_send_message(
                                            response.Data.chat_type,
                                            colored_message,
                                            uid,
                                            chat_id,
                                            key,
                                            iv
                                        )
                                        await asyncio.sleep(0.5)

                            except Exception as e:
                                error_msg = (
                                    f"[B][C][FF0000]❌ ERROR! Something went wrong:\n{str(e)}"
                                )
                                await safe_send_message(
                                    response.Data.chat_type,
                                    error_msg,
                                    uid,
                                    chat_id,
                                    key,
                                    iv
                                )
                        
                # Pickup lines MESSAGE 
                elif inPuTMsG.strip().startswith('/pick '):
                            print('Processing /p command')

                            try:
                                parts = inPuTMsG.strip().split(maxsplit=2)  # maxsplit=2: /p name <optional number>

                                # Minimum 2 parts: /p name
                                if len(parts) < 2:
                                    error_msg = (
                                        "[B][C][FF0000]❌ ERROR! Usage:\n"
                                        "/pick <name>\n"
                                        "Example: /pick lover"
                                    )
                                    await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                                else:
                                    name = parts[1].strip()  # second part is always name
                                    # third part (if exists) can be anything, just ignore for fun randomization
                                    # parts[2] exists only if len(parts)==3, we don't need to store/use it

                                    messages = [
                                        # Romantic / love
"{Name} Kya aap mere dil ki dhadkan ho kyunki jab bhi main aapko dekhta hoon mera dil tez dhadne lagta hai!",
"{Name} Aapki muskurahat ek chandni raat ki tarah hai jo mere din ko ujwal kar deti hai.",
"{Name} Aapke bina mera din adhura hai, raat adhuri hai, zindagi adhuri hai.",
"{Name} Kya main aapka number le sakta hoon kyunki mujhe lagta hai ki humare rishte mein bahut potential hai!",
"{Name} Aapki aankhen woh jaadui darwaza hain jis mein main hamesha kho jaana chahta hoon.",
"{Name} Aapke saath bitaya har pal sona hai, har lamha heera hai, har second khoobsurat hai.",
"{Name} Kya aap mere liye coffee peene aaogi kyunki main chahta hoon ki hum dono ki kahani shuru ho!",
"{Name} Aapki awaaz ek meethi geet ki tarah hai jo mere kaanon mein hamesha bajti rahti hai.",
"{Name} Main aapse itna pyar karta hoon jaise phool suraj se, jaise nadiya samundar se!",
"{Name} Kya aap mere saath dinner par aaogi kyunki main chahta hoon ki aapki khushboo mere saath rahe!",
"{Name} Aapki hansi ek barish ki boondon ki tarah hai jo mere dil ko thandak pahunchati hai.",
"{Name} Main aapko itna pyar deta hoon jaise dharti apne phoolon ko, jaise maa apne bacchon ko!",
"{Name} Kya aap mere dil ki malika banogi kyunki main aapko apne jeevan ka har hissa banana chahta hoon!",

# Funny
"{Name} Tumhare bina toh main ek incomplete WhatsApp forward ki tarah hoon.",
"{Name} Tumhare chehre pe woh smile dekh kar mere dimaag ka antivirus crash ho gaya.",
"{Name} Tum jaise khoobsurat logon ke liye hi toh mera phone gallery full hai.",
"{Name} Tumhare saath bitaya hua har second mere liye unlimited data pack ki tarah hai.",
"{Name} Tumhare pyaar mein padhna mere liye maths ki class se bhi zyada confusing hai.",
"{Name} Tumhare liye toh main apne pizza ka last slice bhi sacrifice kar sakta hoon.",
"{Name} Tumhare saamne toh main ek nervous job interviewee ki tarah stammer karta hoon.",
"{Name} Tumhare saath toh main apni favorite Netflix series bhi pause kar sakta hoon.",
"{Name} Tumhare liye main apne best friend ke birthday party se bhi bunk maar lunga.",
"{Name} Tumhare pyaar ne toh mere bank balance ki tarah mera dil bhi empty kar diya.",

# Eye related
"{Name} Tumhari aankhon mein aisa jadoo hai ki main unmein kho jana chahta hoon.",
"{Name} Tumhari nazron ne mere dil ko chura liya hai aur ab main use wapas nahi chahta.",
"{Name} Tumhari aankhen sitaron se bhari raat ki tarah hain jinmein main doobna chahta hoon.",
"{Name} Tumhari aankhon mein maine apna bhavishya dekh liya hai aur wo bahut khoobsurat hai.",

# Hair related
"{Name} Tumhare balon ki khushboo ne mere dimaag ko chura liya hai.",
"{Name} Tumhare bal aise hain jaise raat ke andhere mein chamakte hue sitare.",
"{Name} Tumhare balon ki lehron mein main doob jana chahta hoon aur kabhi bahar na aaun.",

# Hand related
"{Name} Tumhare haath dekhkar lagta hai maine janmon ki tapasya kar li thi!",
"{Name} Tumhari ungliyan mere dil ke taaron ko chhed rahi hain jaise koi sitar baja raha ho.",
"{Name} Kya tumhare haathon mein koi jadoo hai kyunki jab bhi tum mujhe chhoti ho mera dil dhadakne lagta hai!",

# Sad
"{Name} Tumhare bina mere haath soone lagte hain jaise bagiche mein bina phoolon ke paudhe.",
"{Name} Tumne mujhe chhod diya par tumhari yaadein abhi bhi meri ungliyon se chipki hui hain.",
"{Name} Mere haath tumhare haathon ko dhoondte rehte hain par ab wahan sirf hawa hai.",

# Flirting
"{Name} Kya tum meri heartbeat ho kyunki jab bhi tum paas aati ho meri saans ruk si jaati hai",
"{Name} Tumhare bina mera din koi rang nahi laata jaise phool khilne se pehle murjha jaate hain",
"{Name} Tum mere sapno ki rani ho tumhare bina meri zindagi adhuri hai",
"{Name} Kya tumhara naam Google hai kyunki tumhare paas har sawal ka jawab hai",

# Instagram / Crush
"{Name} Tumhare Instagram feed ko dekhkar lagta hai jaise maine khudka social media detox kar liya",
"{Name} Tumhari photos scroll karte hue mera phone bhi overheating karne lagta hai",
"{Name} Tumhari profile visit karna mere din ka sabse important kaam ban gaya hai",
"{Name} Tumhari DMs mein message karna mere liye lottery jeetne jaisa hai",
                                    ]

                                    import random
                                    # Pick a random message
                                    msg = random.choice(messages)
                                    colored_message = f"[B][C]{get_random_color()} {msg.replace('{Name}', name.upper())}"
                                    await safe_send_message(response.Data.chat_type, colored_message, uid, chat_id, key, iv)

                            except Exception as e:
                                error_msg = f"[B][C][FF0000]❌ ERROR! Something went wrong:\n{str(e)}"
                                await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)


                elif inPuTMsG.strip().startswith("/fun"):
                            parts = inPuTMsG.strip().split()

                            # /fun  OR  /fun <number>
                            if len(parts) == 1 or (len(parts) == 2 and parts[1].isdigit()):
                                print("Processing /fun command")

                                try:
                                    import random as rnd

                                    # 🔹 pool create (no named global variable)
                                    if "__fun_pool__" not in globals():
                                        globals()["__fun_pool__"] = [
                                        "ভালোবাসা, কান ধরছি আর না, কষ্ট আমি পাইসি, তুমি না!!",
                                        "মানে ishq, প্রেম, ভালোবাসা!!",
                                        "What is love?",
                                        "কি বললি, এই এই কু'ত্তার বাচ্চা, এই তুই কি বললি, তুই কি বললি, এই তুই কি বললি, এই এই, এই কু'ত্তার বাচ্চা, কু'ত্তাররররর বাচ্চা, এই এই এই এইইইইইই.......",
                                        "I love you 2, ummmmmmmmmmmmah",
                                        "ভাই English তো আমি ভালো বুঝি, কিন্তু আমি তো চোখে দেখিনা....!!!",
                                        "তেঁতুলের আচার টক, তোমার নানীরে পক পক....!!!",
                                        "প্রেমের জালে ফেলে ধোকা দিতে চাও, পারবে না, কারণ আমি ক্রাইম পেট্রল দেখে বড়  হয়েছি...!!",
                                        "এই শুয়োরের বাচ্চা, এই Bᴀꜱᴛᴀʀᴅ, কু'ত্তার বা'চ্চা  টেলিফোন রাখ !!!",
                                        "সবার অংক মিলে, কিন্তু আমার অংক মিলেনা!!",
                                        "খান'কির পোলা তোরে আমি খুইজা বেড়াইতাসি.....!!!",
                                        "Ishhh আবার ইংরেজি চু'দাও, ইংরেজি ঢুকাই দিবো আইতাছে তোর বা'পে",
                                        "আজ প্রত্থম বার কইসোস তাই মাফ কইরা দিলাম, কিন্তু দ্বিতীয় বার যেদিন কবি সেইদিন তোর কইলজা টারে টাইনা বাইর কইরা আমি ওজন করুম !!!",
                                        "ওই আমার বা'পে রাজা, আমার দাদায় রাজা, আমি নিজে রাজা, তুই চিনস না আমা'রে, তোর বা'পে চিনে, জিগাইস !!!",
                                        "আমার হো'গা মারা শেষ, আপনার নাম যদি হয় বাদশা, তাইলে আমার কি নাম হওয়া উচিত, আপনাগোর মতো ফকিন্নি পোলাগোর নাম বাদশা দেইখাই তো, দেশটার এই অবস্থা !!"
                                    ]
                                        

                                    pool = globals()["__fun_pool__"]

                                    # 🔁 reset when empty
                                    if not pool:
                                        pool.extend(globals()["__fun_pool__"].copy())

                                    selected_msg = rnd.choice(pool)
                                    pool.remove(selected_msg)

                                    final_msg = f"[B][C]{get_random_color()}{selected_msg}"

                                    await safe_send_message(
                                        response.Data.chat_type,
                                        final_msg,
                                        uid,
                                        chat_id,
                                        key,
                                        iv
                                    )

                                except Exception as e:
                                    error_msg = f"[B][C][FF0000]❌ ERROR:\n{str(e)}"
                                    await safe_send_message(
                                        response.Data.chat_type,
                                        error_msg,
                                        uid,
                                        chat_id,
                                        key,
                                        iv
                                    )
                elif inPuTMsG.strip().lower() == "meow":
                            try:
                                meow_msg = """[B][C][FF69B4] ╱|、
[FFFFFF](˚ˎ 。7  [FF69B4]Meow❤
[FFFFFF] |、˜〵
[FFFFFF]じしˍ,)ノ"""
                                await asyncio.sleep(1)
                                await safe_send_message(
                                    response.Data.chat_type,
                                    meow_msg,
                                    uid,
                                    chat_id,
                                    key,
                                    iv
                                )

                            except Exception as e:
                                error_msg = f"[B][C][FF0000]❌ ERROR:\n{str(e)}"
                                await safe_send_message(
                                    response.Data.chat_type,
                                    error_msg,
                                    uid,
                                    chat_id,
                                    key,
                                    iv
                                )        
                        
                elif inPuTMsG.strip().startswith('/lol'):
                            print('Processing /lol command')

                            try:
                                parts = inPuTMsG.strip().split(maxsplit=2)  # maxsplit=2: /lol name <optional number>

                                # Minimum 2 parts: /lol name
                                if len(parts) < 2:
                                    error_msg = (
                                        "[B][C][FF0000]❌ ERROR! Usage:\n"
                                        "/lol <name>\n"
                                        "Example: /lol hater"
                                    )
                                    await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                                else:
                                    name = parts[1].strip()  # second part is always name
                                    # third part (if exists) can be anything (random number), just ignore

                                    messages = [
"{Name} er confidence dekhe WiFi o insecure hoy 🤡",
"{Name} এত faltu যে background noise হিসেবেও reject",
"{Name} নিজেকে legend ভাবে, কিন্তু tutorial skip করে",
"{Name} er brain Google Lite version",
"{Name} কথা বলে এমনভাবে—নিজেই confused, অন্যরা bonus",
"{Name} কে দেখলে lag kore system hang",
"{Name} er logic calculator ছুঁলে error দেয়",
"{Name} এত expert যে ভুলটাও confidently করে",
"{Name} নিজেই নিজের biggest fan 🤣",
"{Name} er attitude flagship, skills trial version",
"{Name} er presence মানেই lag spike",
"{Name} কথা শুরু করে, point হারিয়ে ফেলে",
"{Name} এত slow যে loading circle mock করে",
"{Name} argument এ হেরে বলে: ‘network issue’",
"{Name} er IQ auto-update off",
"{Name} dekhe মনে হয় life tutorial miss করেছে",
"{Name} er brain.exe stopped unexpectedly ⚠️",
"{Name} এত random যে RNG jealous",
"{Name} vibe এমন—mute করলে শান্তি",
"{Name} নিজেকে pro ভাবে, কিন্তু controls জানে না",
"{Name} er aim mouse er দিকে না, দেয়ালের দিকে",
"{Name} er K/D ratio calculator এ error আনে",
"{Name} কে pro বললে pro রা copyright claim দেবে",
"{Name} er gameplay দেখে NPC রা sympathy দেয়",
"{Name} এত bot যে anti-cheat ও confused",
"{Name} er strategy শুনে enemy হাসতে হাসতে মরে",
"{Name} er reflexes ট্যাপ বাজির চেয়ে slow",
"{Name} kotha bole sobai 'skip' চাপে",
"{Name} er opinion এত cheap যে free sample দেয়",
"{Name} নিজের replay দেখে নিজেই unfriend করে",
"{Name} er game sense শূন্য, শুধু attitude infinite",
"{Name} er momo skills er theke hug দিতে ভালো",
"{Name} ke carry korte গেলে back pain হয়",
"{Name} er decision making coin flip er cheye random",
"{Name} er talent lock করা আছে, key হারিয়ে গেছে",
"{Name} er brain RAM 2GB, তাও swap চলছে",
"{Name} ke help chailে Google ও 'no result'",
"{Name} er confidence 100%, proof 0%",
"{Name} ke dekhe lag kore server restart দরকার",
"{Name} er thoughts এত slow যে buffering হয়",
"{Name} er personality Windows XP — obsolete",
"{Name} er name Google এ দিলে 'did you mean: failure?' আসে",
"{Name} er skill level = beginner tutorial part 1",
"{Name} কথা দেয়, রাখে না — Netflix er free trial",
"{Name} er team contribution = presence er ojana",
"{Name} ke suggestion dile reject, তারপর fail করে blame",
"{Name} er expertise শুধু excuse বানানোতে",
"{Name} ke হারানো মানে match না, blessing",
"{Name} er mic mute করলে server er ping কমে",
"{Name} er victory Royale = spectator mode",
"{Name} er logic = if (lose) blame (team)",
"{Name} ke IQ test dile answer sheet empty জমা দেয়",
"{Name} er motivation Monday-তে শেষ, Tuesday-তে excuse",
"{Name} er '1v1 me' বলে, তারপর 1v1 এ hide করে",
"{Name} er attitude Ferrari, skill rickshaw",
"{Name} er follow করলে কেউ unfollow করে না — কেউ follow-ই করে না",
"{Name} ke copy paste করলে error দেয় 'invalid content'",
"{Name} er dialog scripted, acting null",
"{Name} ke game theke bench korle team jite jay",
"{Name} er clan tag ও লজ্জা পায়",
"{Name} er winning streak = 0, losing streak = lifestyle",
"{Name} ke 'GG' bolle ভাবে 'Good Garbage'",
"{Name} er thumb rule: যা করবে, উল্টো করবে",
"{Name} er advice = free hai, isliye value zero",
"{Name} ke pro banate gele game uninstall করে দেয়",
"{Name} er report button sob cheye beshi use হয় — অন্যেরা চাপে",
"{Name} er brain WiFi er moto — connect হয়, drop হয়",
                                    ]

                                    import random
                                    # Pick a random message for each iteration (optional: shuffle for more randomness)
                                    for msg in messages:
                                        colored_message = f"[B][C]{get_random_color()} {msg.replace('{Name}', name.upper())}"
                                        await safe_send_message(response.Data.chat_type, colored_message, uid, chat_id, key, iv)
                                        await asyncio.sleep(0.5)

                            except Exception as e:
                                error_msg = f"[B][C][FF0000]❌ ERROR! Something went wrong:\n{str(e)}"
                                await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                        
                        
                        
                                
                elif inPuTMsG.strip().startswith('/rt '):
                    try:
                        name = inPuTMsG.strip()[4:].strip()
                        roast_list = [
                            "তুই তো বট, রোবট! 🤖", "তুই ট্রেনিং গ্রাউন্ডের পুতুল! 🗿",
                            "তোর হেডশট রেট মাইনাসে! 📉", "তুই এনিমি দেখলেই পালাস! 🏃",
                            "তুই ফ্রি ফায়ারের সবচেয়ে বড় নуб! 🎯", "তোর গেমপ্লে দেখে বটরাও হাসে! 😂",
                            "তুই বন্দুকের বদলে লাঠি আনিস! 🦯", "তোর K/D রেশিও শূন্য! 0️⃣",
                            "তুই পুরা জোকার! 🤡", "তুই গেমে ভুত! 👻",
                        ]
                        for r in roast_list:
                            P = await SEndMsG(XX, f"[B][C][FF0000]{name} {r}", uid, chat_id, key, iv)
                            await SEndPacKeT(whisper_writer, online_writer, 'ChaT', P)
                            await asyncio.sleep(1.5)
                    except Exception as e: print(f"RT error: {e}")

            

                elif inPuTMsG.strip().startswith('/slap '):
                    name = inPuTMsG.strip()[6:].strip()
                    P = await SEndMsG(XX, f"[B][C][FF0000]👋 {name} কে চড় দিলাম! 💥", uid, chat_id, key, iv)
                    await SEndPacKeT(whisper_writer, online_writer, 'ChaT', P)

                elif inPuTMsG.strip().startswith('/punch '):
                    name = inPuTMsG.strip()[7:].strip()
                    P = await SEndMsG(XX, f"[B][C][FF0000]👊 {name} কে ঘুষি দিলাম! 💥", uid, chat_id, key, iv)
                    await SEndPacKeT(whisper_writer, online_writer, 'ChaT', P)

                elif inPuTMsG.strip().startswith('/kick'):
                            parts = inPuTMsG.strip().split()
                            if len(parts) < 2:
                                error_msg = f"[B][C][FF0000]❌ ERROR! Usage: /kick (uid)\nExample: /kick 238🤫722🤫72🤫71\n"
                                await safe_send_message(response.Data.chat_type, error_msg, uid, chat_id, key, iv)
                            else:
                                target_uid = parts[1]
                                initial_message = f"[B][C]{get_random_color()}\nkicking {target_uid}...\n"
                                await safe_send_message(response.Data.chat_type, initial_message, uid, chat_id, key, iv)
                                
                                try:
                                    # Fast squad creation and invite for 5 players
                                    PAc = await KickTarget(target_uid, key, iv)
                                    await SEndPacKeT(whisper_writer, online_writer, 'OnLine', PAc)
                                    await asyncio.sleep(0.3)
                                except Exception as e:
                                    print(e)

                elif inPuTMsG.strip().startswith('/bite '):
                    name = inPuTMsG.strip()[6:].strip()
                    P = await SEndMsG(XX, f"[B][C][FF0000]🦷 {name} কে কামড় দিলাম! 😬", uid, chat_id, key, iv)
                    await SEndPacKeT(whisper_writer, online_writer, 'ChaT', P)

                elif inPuTMsG.strip().startswith('/lick '):
                    name = inPuTMsG.strip()[6:].strip()
                    P = await SEndMsG(XX, f"[B][C][FF69B4]👅 {name} কে চাট দিলাম! 😋", uid, chat_id, key, iv)
                    await SEndPacKeT(whisper_writer, online_writer, 'ChaT', P)

                elif inPuTMsG.strip() == '/dance':
                    P = await SEndMsG(XX, "[B][C][FF00FF]💃 আমি নাচছি! 🕺🎶", uid, chat_id, key, iv)
                    await SEndPacKeT(whisper_writer, online_writer, 'ChaT', P)

                elif inPuTMsG.strip() == '/sing':
                    P = await SEndMsG(XX, "[B][C][00FFFF]🎤 লা লা লা... 🎶🎵", uid, chat_id, key, iv)
                    await SEndPacKeT(whisper_writer, online_writer, 'ChaT', P)

                elif inPuTMsG.strip() == '/cry':
                    P = await SEndMsG(XX, "[B][C][808080]😭 আমি কাঁদছি... 😢", uid, chat_id, key, iv)
                    await SEndPacKeT(whisper_writer, online_writer, 'ChaT', P)

                elif inPuTMsG.strip() == '/laugh':
                    P = await SEndMsG(XX, "[B][C][FFFF00]😂 হা হা হা! 🤣", uid, chat_id, key, iv)
                    await SEndPacKeT(whisper_writer, online_writer, 'ChaT', P)

                elif inPuTMsG.strip() == '/scream':
                    P = await SEndMsG(XX, "[B][C][FF0000]😱 আআআআআ!!! 🤯", uid, chat_id, key, iv)
                    await SEndPacKeT(whisper_writer, online_writer, 'ChaT', P)

                elif inPuTMsG.strip() == '/pray':
                    P = await SEndMsG(XX, "[B][C][00FF00]🤲 দোয়া করছি... 🙏", uid, chat_id, key, iv)
                    await SEndPacKeT(whisper_writer, online_writer, 'ChaT', P)

                elif inPuTMsG.strip() == '/shower':
                    P = await SEndMsG(XX, "[B][C][00FFFF]🚿 গোসল করছি... 💦", uid, chat_id, key, iv)
                    await SEndPacKeT(whisper_writer, online_writer, 'ChaT', P)

                elif inPuTMsG.strip() == '/toilet':
                    P = await SEndMsG(XX, "[B][C][808080]🚽 টয়লেটে গেলাম... 💩", uid, chat_id, key, iv)
                    await SEndPacKeT(whisper_writer, online_writer, 'ChaT', P)

                elif inPuTMsG.strip() == '/meme':
                    memes = [
                        "[B][C][FFFF00]😂 মিম: আমি যখন পরীক্ষায় পাস করি — সবাই অবাক! 🤯",
                        "[B][C][FF69B4]😆 মিম: আমি ঘুমাতে যাই — চোখ খোলে সকাল! 🌅",
                        "[B][C][FF0000]🤣 মিম: ফ্রি ফায়ারে ১vs৪ — আমি জিতি! 🏆",
                        "[B][C][00FFFF]😹 মিম: খাবার দেখলে আমার অবস্থা — 🐷",
                    ]
                    P = await SEndMsG(XX, random.choice(memes), uid, chat_id, key, iv)
                    await SEndPacKeT(whisper_writer, online_writer, 'ChaT', P)

                elif inPuTMsG.strip() == '/quiz':
                    q, a = random.choice([
                        ("বাংলাদেশের রাজধানী?", "ঢাকা"), ("পৃথিবীর সবচেয়ে বড় মহাসাগর?", "প্রশান্ত মহাসাগর"),
                        ("বাংলাদেশের জাতীয় পাখি?", "দোয়েল"), ("১ কিলোমিটার = কত মিটার?", "১০০০"),
                        ("সূর্য কোন দিক থেকে ওঠে?", "পূর্ব"), ("পানির রাসায়নিক সূত্র?", "H2O"),
                        ("বাংলাদেশের জাতীয় ফল?", "কাঁঠাল"), ("মানব শরীরে কত হাড়?", "২০৬"),
                        ("ফ্রি ফায়ারে কত প্লেয়ার?", "৫০"), ("সবচেয়ে বড় গ্রহ?", "বৃহস্পতি"),
                    ])
                    P = await SEndMsG(XX, f"[B][C][FF4500]🧠 QUIZ 🧠\n\n[00FFFF]❓ {q}\n\n[FF4500]────────\n[00FF00]✅ উত্তর: {a}", uid, chat_id, key, iv)
                    await SEndPacKeT(whisper_writer, online_writer, 'ChaT', P)

                elif inPuTMsG.strip() == '/truth':
                    t = random.choice([
                        "তুই কাকে সবচেয়ে বেশি ভালোবাসিস?", "তোর সবচেয়ে বড় সিক্রেট কী?",
                        "শেষবার কবে কেঁদেছিলি?", "তোর ক্রাশ কে?", "শেষবার কবে মিথ্যা বলেছিলি?",
                        "তোর সবচেয়ে বড় ভয় কী?", "তোর সবচেয়ে লজ্জার মুহূর্ত?",
                        "তুই কখনো চুরি করেছিস?", "তোর ফোনে লুকানো অ্যাপ আছে?", "কাকে সবচেয়ে বেশি ঘৃণা করিস?",
                    ])
                    P = await SEndMsG(XX, f"[B][C][00FFFF]🤔 TRUTH 🤔\n\n{t}", uid, chat_id, key, iv)
                    await SEndPacKeT(whisper_writer, online_writer, 'ChaT', P)

                elif inPuTMsG.strip() == '/dare':
                    d = random.choice([
                        "🔥 ৫ মিনিট চোখ বন্ধ রাখ!", "😂 পরের ১০ মিনিট শুধু হাসতে থাক!",
                        "🐔 মুরগির মতো ডাক দে!", "🎤 একটা গান গা!", "💃 ৩০ সেকেন্ড নাচ!",
                        "🤪 বানরের আওয়াজ বের কর!", "😜 তোর ক্রাশকে মেসেজ দে!",
                        "🤡 ৫ মিনিট জোকার হ!", "📱 তোর ফোনের শেষ চ্যাট দেখাও!", "🍋 একটা কাঁচা লেবু খা!",
                    ])
                    P = await SEndMsG(XX, f"[B][C][FF4500]🎲 DARE 🎲\n\n{d}", uid, chat_id, key, iv)
                    await SEndPacKeT(whisper_writer, online_writer, 'ChaT', P)

                elif inPuTMsG.strip() == '/wyr':
                    a, b = random.choice([
                        ("অদৃশ্য হওয়ার শক্তি", "উড়ার শক্তি"), ("সবসময় পিজ্জা খাওয়া", "সবসময় বিরিয়ানি খাওয়া"),
                        ("অতীতে যাওয়া", "ভবিষ্যতে যাওয়া"), ("সুপারম্যান হওয়া", "ব্যাটম্যান হওয়া"),
                        ("ইন্টারনেট ছাড়া থাকা", "ফোন ছাড়া থাকা"), ("১০০ বিড়াল", "১০০ কুকুর"),
                        ("চিরকাল বাচ্চা থাকা", "চিরকাল বুড়ো থাকা"), ("সব ভাষা জানা", "সব যন্ত্র চালানো"),
                        ("ধনী কিন্তু একা", "গরিব কিন্তু বন্ধুদের সাথে"), ("চাঁদে বাড়ি", "সমুদ্রের নিচে বাড়ি"),
                    ])
                    P = await SEndMsG(XX, f"[B][C][DC143C]🤔 WOULD YOU RATHER?\n\n[00FF7F]A) {a}\n\n[DC143C]───── অথবা ─────\n\n[00FFFF]B) {b}\n\n[FF69B4]তোর উত্তর: A নাকি B?", uid, chat_id, key, iv)
                    await SEndPacKeT(whisper_writer, online_writer, 'ChaT', P)

                elif inPuTMsG.strip() == '/roll':
                    d1 = random.randint(1, 6); d2 = random.randint(1, 6)
                    P = await SEndMsG(XX, f"[B][C][FF8C00]🎲 DICE ROLL 🎲\n\n[00FFFF]🎯 ডাইস ১: {d1}\n[FF69B4]🎯 ডাইস ২: {d2}\n\n[FF8C00]────────\n[FFFF00]📊 মোট: {d1+d2}/12", uid, chat_id, key, iv)
                    await SEndPacKeT(whisper_writer, online_writer, 'ChaT', P)

                elif inPuTMsG.strip() == '/zodiac' or inPuTMsG.strip() == '/rashi':
                    s, d = random.choice(list({
                        "মেষ ♈": ("লাল", "৯", "মঙ্গলবার"), "বৃষ ♉": ("সবুজ", "৬", "শুক্রবার"),
                        "মিথুন ♊": ("হলুদ", "৫", "বুধবার"), "কর্কট ♋": ("সাদা", "২", "সোমবার"),
                        "সিংহ ♌": ("সোনালি", "১", "রবিবার"), "কন্যা ♍": ("সবুজ", "৫", "বুধবার"),
                        "তুলা ♎": ("নীল", "৬", "শুক্রবার"), "বৃশ্চিক ♏": ("লাল", "৯", "মঙ্গলবার"),
                        "ধনু ♐": ("বেগুনি", "৩", "বৃহস্পতিবার"), "মকর ♑": ("কালো", "৮", "শনিবার"),
                        "কুম্ভ ♒": ("নীল", "৪", "শনিবার"), "মীন ♓": ("সমুদ্রি", "৭", "বৃহস্পতিবার"),
                    }).items())
                    h = random.choice(["আজ তোর দিন শानदার যাবে!", "প্রেমে আজ ভালো খবর আসতে পারে!", "আর্থিক বিষয়ে সতর্ক থাক।", "আজ কিছু নতুন শিখবি!", "স্বাস্থ্যের যত্ন নে।"])
                    P = await SEndMsG(XX, f"[B][C][9370DB]🌟 রাশিফল 🌟\n\n[00FFFF]🔮 রাশি: [FF69B4]{s}\n[FFFF00]🎨 রঙ: [FFFFFF]{d[0]}\n[00FF7F]🔢 নাম্বার: [FFFFFF]{d[1]}\n[FF4500]📅 দিন: [FFFFFF]{d[2]}\n\n[DA70D6]📜 {h}", uid, chat_id, key, iv)
                    await SEndPacKeT(whisper_writer, online_writer, 'ChaT', P)

                elif inPuTMsG.strip() == '/weather' or inPuTMsG.strip() == '/abohawa':
                    city = random.choice(["ঢাকা", "চট্টগ্রাম", "খুলনা", "রাজশাহী", "সিলেট", "বরিশাল", "রংপুর", "ময়মনসিংহ", "কুমিল্লা", "নারায়ণগঞ্জ", "গাজীপুর", "বগুড়া"])
                    temp = f"{random.randint(20, 40)}°C"
                    w = random.choice(["☀️ রোদ", "🌤️ আংশিক মেঘ", "⛅ মেঘ", "🌧️ বৃষ্টি", "🌦️ হালকা বৃষ্টি", "⛈️ ভারী বৃষ্টি", "🌬️ ঠান্ডা বাতাস", "🌫️ কুয়াশা"])
                    hum = f"{random.randint(40, 95)}%"; wind = f"{random.randint(5, 40)} km/h"
                    P = await SEndMsG(XX, f"[B][C][1E90FF]🌤️ আবহাওয়া 🌤️\n\n[FF66CC]📍 শহর: [FFFFFF]{city}\n[FF69B4]🌡️ তাপমাত্রা: [FFFFFF]{temp}\n[00FF7F]☁️ আবহাওয়া: [FFFFFF]{w}\n[DA70D6]💧 আর্দ্রতা: [FFFFFF]{hum}\n[FF8C00]💨 বাতাস: [FFFFFF]{wind}", uid, chat_id, key, iv)
                    await SEndPacKeT(whisper_writer, online_writer, 'ChaT', P)

                elif inPuTMsG.strip().startswith('/luck '):
                    name = inPuTMsG.strip()[6:].strip().title()
                    p = random.choice(["🌟 তুই শীঘ্রই বড় সাফল্য পাবি!", "💰 তোর জীবনে অনেক টাকা আসবে!", "❤️ তোর সত্যিকারের প্রেম খুব কাছে!", "🏆 তুই একদিন চ্যাম্পিয়ন হবি!", "📚 তোর পরীক্ষায় ভালো নম্বর আসবে!", "🌈 তোর কঠিন দিন শেষ হচ্ছে!", "🎯 তোর স্বপ্ন পূরণ হবে!", "💎 তুই একটা অমূল্য উপহার পাবি!"])
                    P = await SEndMsG(XX, f"[B][C][FF69B4]🔮 ভাগ্য 🔮\n\n[00FFFF]👤 নাম: [FFFFFF]{name}\n\n[FFFF00]{p}\n\n[FF69B4]🔮 Powered by BUDDY MEOW", uid, chat_id, key, iv)
                    await SEndPacKeT(whisper_writer, online_writer, 'ChaT', P)

                elif inPuTMsG.strip().startswith('/8ball '):
                    q = inPuTMsG.strip()[7:].strip()
                    answers = ["হ্যাঁ, নিশ্চিত! ✅", "না, একদমই না! ❌", "হতে পারে... 🤔", "ভাগ্য ভালো থাকলে হবে! 🍀", "আমার মনে হয় না! 😕", "অবশ্যই হবে! 💯", "ধৈর্য ধর, সময় লাগবে! ⏳"]
                    P = await SEndMsG(XX, f"[B][C][9370DB]🎱 MAGIC 8BALL 🎱\n\n[00FFFF]❓ {q}\n\n[FFFF00]{random.choice(answers)}", uid, chat_id, key, iv)
                    await SEndPacKeT(whisper_writer, online_writer, 'ChaT', P)

                elif inPuTMsG.strip() == '/coinflip':
                    P = await SEndMsG(XX, f"[B][C][FFD700]🪙 COIN FLIP 🪙\n\n[FFFF00]ফলাফল: {random.choice(['হেডস 🪙', 'টেইলস 🪙'])}", uid, chat_id, key, iv)
                    await SEndPacKeT(whisper_writer, online_writer, 'ChaT', P)

                elif inPuTMsG.strip() == '/rps':
                    bot = random.choice(["পাথর 🪨", "কাগজ 📄", "কাঁচি ✂️"])
                    P = await SEndMsG(XX, f"[B][C][FF4500]✊ ROCK-PAPER-SCISSORS ✋\n\n[00FFFF]বট: {bot}\n[FFFF00]তুই কী বাছলি? লিখ!", uid, chat_id, key, iv)
                    await SEndPacKeT(whisper_writer, online_writer, 'ChaT', P)

                elif inPuTMsG.strip().startswith('/rate '):
                    name = inPuTMsG.strip()[6:].strip()
                    pct = random.randint(1, 100)
                    P = await SEndMsG(XX, f"[B][C][FF69B4]⭐ RATING ⭐\n\n[00FFFF]👤 {name}\n[FFFF00]রেটিং: {pct}/100", uid, chat_id, key, iv)
                    await SEndPacKeT(whisper_writer, online_writer, 'ChaT', P)

                elif inPuTMsG.strip().startswith('/ice '):
                    parts = inPuTMsG.strip().split()
                    if len(parts) >= 2:
                        tgt = parts[1] if parts[1].lower() not in ('me', 'self') else str(uid)
                        if freeze_task and not freeze_task.done():
                            freeze_running = False; freeze_task.cancel(); await asyncio.sleep(0.3)
                        freeze_running = True
                        freeze_task = asyncio.create_task(freeze_emote_spam(tgt, key, iv, region, XX, chat_id, uid))
                        await safe_send_message(XX, f"[B][C][00FFFF]❄️ Freeze started {tgt}", uid, chat_id, key, iv)

                elif inPuTMsG.strip().startswith('/room '):
                    parts = inPuTMsG.strip().split()
                    if len(parts) >= 3:
                        tgt = parts[1]; rid = parts[2]
                        try:
                            for i in range(3000):
                                spam_p = await Room_Spam(tgt, rid, "BUDDY MEOW", key, iv)
                                await SEndPacKeT(whisper_writer, online_writer, 'OnLine', spam_p)
                                if (i + 1) % 50 == 0: print(f"Room spam progress: {i+1}/3000")
                                await asyncio.sleep(0.05)
                            await safe_send_message(XX, f"[B][C][00FF00]✅ Room spam completed", uid, chat_id, key, iv)
                        except Exception as e: print(f"Room spam error: {e}")

                else:
                    try:
                        replies = load_json_mapping(AUTO_REPLIES_FILE)
                        auto_reply = replies.get(command_text)
                        if auto_reply:
                            await safe_send_message(XX, str(auto_reply), uid, chat_id, key, iv)
                    except (OSError, ValueError, json.JSONDecodeError) as e:
                        print(f"Auto-reply lookup error: {e}")

            writer.close(); await writer.wait_closed(); whisper_writer = None
        except Exception as e:
            print(f"Chat error: {ip}:{port} - {e}")
            whisper_writer = None
        await asyncio.sleep(reconnect_delay)
