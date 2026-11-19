# By RAFIN

import requests , json , binascii , time , urllib3 , base64 , datetime , re ,socket , threading , random , os , asyncio , struct
from protobuf_decoder.protobuf_decoder import Parser
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad , unpad
from datetime import datetime
from google.protobuf.timestamp_pb2 import Timestamp

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

Key , Iv = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56]) , bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])

# ============================================
# HELPER / PROTOBUF ENCODING FUNCTIONS
# ============================================

def encode_varint(value):
    bits = value & 0x7f
    value >>= 7
    ret = bytes()
    while value:
        ret += struct.pack('B', 0x80 | bits)
        bits = value & 0x7f
        value >>= 7
    return ret + struct.pack('B', bits)

def create_protobuf_packet(fields):
    buffer = bytes()
    for field_number, value in fields.items():
        if isinstance(value, int):
            header = (field_number << 3) | 0
            buffer += encode_varint(header)
            buffer += encode_varint(value)
        elif isinstance(value, dict):
            nested_data = create_protobuf_packet(value)
            header = (field_number << 3) | 2
            buffer += encode_varint(header)
            buffer += encode_varint(len(nested_data))
            buffer += nested_data
        elif isinstance(value, str):
            data = value.encode('utf-8')
            header = (field_number << 3) | 2
            buffer += encode_varint(header)
            buffer += encode_varint(len(data))
            buffer += data
        elif isinstance(value, bytes):
            header = (field_number << 3) | 2
            buffer += encode_varint(header)
            buffer += encode_varint(len(value))
            buffer += value
    return buffer

def dec_to_hex(n):
    return hex(n).replace("0x", "").upper()

def encrypt_packet(packet_hex, key, iv):
    return AES.new(key, AES.MODE_CBC, iv).encrypt(pad(bytes.fromhex(packet_hex), 16)).hex()

async def EnC_AEs(HeX, K=None, V=None):
    cipher = AES.new(K if K is not None else Key, AES.MODE_CBC, V if V is not None else Iv)
    raw = bytes.fromhex(HeX) if isinstance(HeX, str) else HeX
    return cipher.encrypt(pad(raw, AES.block_size)).hex()
    
async def DEc_AEs(HeX, K=None, V=None):
    cipher = AES.new(K if K is not None else Key, AES.MODE_CBC, V if V is not None else Iv)
    raw = bytes.fromhex(HeX) if isinstance(HeX, str) else HeX
    return unpad(cipher.decrypt(raw), AES.block_size).hex()
    
async def EnC_PacKeT(HeX , K , V): 
    raw = bytes.fromhex(HeX) if isinstance(HeX, str) else HeX
    return AES.new(K , AES.MODE_CBC , V).encrypt(pad(raw ,16)).hex()
    
async def DEc_PacKeT(HeX , K , V):
    raw = bytes.fromhex(HeX) if isinstance(HeX, str) else HeX
    return unpad(AES.new(K , AES.MODE_CBC , V).decrypt(raw) , 16).hex()  

async def EnC_Uid(H , Tp):
    e , H = [] , int(H)
    if H == 0:
        return "00" if Tp == 'Uid' else None
    while H:
        e.append((H & 0x7F) | (0x80 if H > 0x7F else 0)) ; H >>= 7
    return bytes(e).hex() if Tp == 'Uid' else None

async def EnC_Vr(N):
    if N < 0: ''
    H = []
    while True:
        BesTo = N & 0x7F ; N >>= 7
        if N: BesTo |= 0x80
        H.append(BesTo)
        if not N: break
    return bytes(H)
    
def DEc_Uid(H):
    n = s = 0
    for b in bytes.fromhex(H):
        n |= (b & 0x7F) << s
        if not b & 0x80: break
        s += 7
    return n
    
async def CrEaTe_VarianT(field_number, value):
    field_header = (field_number << 3) | 0
    return await EnC_Vr(field_header) + await EnC_Vr(value)

async def CrEaTe_LenGTh(field_number, value):
    field_header = (field_number << 3) | 2
    encoded_value = value.encode() if isinstance(value, str) else value
    return await EnC_Vr(field_header) + await EnC_Vr(len(encoded_value)) + encoded_value

async def CrEaTe_ProTo(fields):
    packet = bytearray()
    for field, value in fields.items():
        if isinstance(value, dict):
            nested_packet = await CrEaTe_ProTo(value)
            packet.extend(await CrEaTe_LenGTh(field, nested_packet))
        elif isinstance(value, int):
            packet.extend(await CrEaTe_VarianT(field, value))
        elif isinstance(value, str) or isinstance(value, bytes):
            packet.extend(await CrEaTe_LenGTh(field, value))
    return packet
    
async def DecodE_HeX(H):
    R = hex(H) 
    F = str(R)[2:]
    if len(F) == 1: F = "0" + F ; return F
    else: return F

async def Fix_PackEt(parsed_results):
    result_dict = {}
    for result in parsed_results:
        field_data = {}
        field_data['wire_type'] = result.wire_type
        if result.wire_type == "varint":
            field_data['data'] = result.data
        if result.wire_type == "string":
            field_data['data'] = result.data
        if result.wire_type == "bytes":
            field_data['data'] = result.data
        elif result.wire_type == 'length_delimited':
            field_data["data"] = await Fix_PackEt(result.data.results)
        result_dict[result.field] = field_data
    return result_dict

async def DeCode_PackEt(input_text):
    try:
        parsed_results = Parser().parse(input_text)
        parsed_results_objects = parsed_results
        parsed_results_dict = await Fix_PackEt(parsed_results_objects)
        json_data = json.dumps(parsed_results_dict)
        return json_data
    except Exception as e:
        print(f"error {e}")
        return None
                      
def xMsGFixinG(n):
    return '🗿'.join(str(n)[i:i + 3] for i in range(0 , len(str(n)) , 3))
    
async def Ua():
    versions = [
        '4.0.18P6', '4.0.19P7', '4.0.20P1', '4.1.0P3', '4.1.5P2', '4.2.1P8',
        '4.2.3P1', '5.0.1B2', '5.0.2P4', '5.1.0P1', '5.2.0B1', '5.2.5P3',
        '5.3.0B1', '5.3.2P2', '5.4.0P1', '5.4.3B2', '5.5.0P1', '5.5.2P3'
    ]
    models = [
        'SM-A125F', 'SM-A225F', 'SM-A325M', 'SM-A515F', 'SM-A725F', 'SM-M215F', 'SM-M325FV',
        'Redmi 9A', 'Redmi 9C', 'POCO M3', 'POCO M4 Pro', 'RMX2185', 'RMX3085',
        'moto g(9) play', 'CPH2239', 'V2027', 'OnePlus Nord', 'ASUS_Z01QD',
    ]
    android_versions = ['9', '10', '11', '12', '13', '14']
    languages = ['en-US', 'es-MX', 'pt-BR', 'id-ID', 'ru-RU', 'hi-IN']
    countries = ['USA', 'MEX', 'BRA', 'IDN', 'RUS', 'IND']
    version = random.choice(versions)
    model = random.choice(models)
    android = random.choice(android_versions)
    lang = random.choice(languages)
    country = random.choice(countries)
    return f"GarenaMSDK/{version}({model};Android {android};{lang};{country};)"
    
async def ArA_CoLor():
    Tp = ["32CD32" , "00BFFF" , "00FA9A" , "90EE90" , "FF4500" , "FF6347" , "FF69B4" , "FF8C00" , "FF6347" , "FFD700" , "FFDAB9" , "F0F0F0" , "F0E68C" , "D3D3D3" , "A9A9A9" , "D2691E" , "CD853F" , "BC8F8F" , "6A5ACD" , "483D8B" , "4682B4", "9370DB" , "C71585" , "FF8C00" , "FFA07A"]
    return random.choice(Tp)
    
async def xBunnEr():
    bN = [902048021]
    return random.choice(bN)

async def GeneRaTePk(Pk , N , K , V):
    PkEnc = await EnC_PacKeT(Pk , K , V)
    _ = await DecodE_HeX(int(len(PkEnc) // 2))
    if len(_) == 2: HeadEr = N + "000000"
    elif len(_) == 3: HeadEr = N + "00000"
    elif len(_) == 4: HeadEr = N + "0000"
    elif len(_) == 5: HeadEr = N + "000"
    else: print('ErroR => GeneRatinG ThE PacKeT !! ')
    return bytes.fromhex(HeadEr + _ + PkEnc)

# ============================================
# CHAT & MESSAGING PACKETS
# ============================================

async def send_room_chat_enhanced(Msg, room_id, key, iv, region):
    """Send room chat message using leaked packet structure"""
    fields = {
        1: 1,
        2: {
            1: 9280892890,
            2: int(room_id),
            3: 3,
            4: f"[{await ArA_CoLor()}]{Msg}",
            5: int(datetime.now().timestamp()),
            7: 2,
            9: {
                1: "RAFIN",
                2: int(await xBunnEr()),
                4: 228,
                7: 1,
            },
            10: "en",
            13: {2: 1, 3: 1},
        },
    }
    packet = (await CrEaTe_ProTo(fields)).hex()
    return await GeneRaTePk(packet, '1215', key, iv)

async def xSEndMsg(Msg , Tp , Tp2 , id , K , V):
    feilds = {1: id , 2: Tp2 , 3: Tp, 4: Msg, 5: 1735129800, 7: 2, 9: {1: "[FFFFFF]RAFIN", 2: int(await xBunnEr()), 3: 901048020, 4: 330, 5: 1001000001, 8: "RAFIN - C4", 10: 1, 11: 1, 13: {1: 2}, 14: {1: 12484827014, 2: 8, 3: "\u0010\u0015\b\n\u000b\u0013\f\u000f\u0011\u0004\u0007\u0002\u0003\r\u000e\u0012\u0001\u0005\u0006"}, 12: 0}, 10: "en", 13: {3: 1}}    
    Pk = (await CrEaTe_ProTo(feilds)).hex()
    Pk = "080112" + await EnC_Uid(len(Pk) // 2, Tp='Uid') + Pk
    return await GeneRaTePk(Pk, '1201', K, V)
    
async def xSEndMsgsQ(Msg , id , K , V, region="BD"):
    """Send message with region 1 title included"""
    avatar = await xBunnEr()
    fields = {
        1: id, 
        2: id, 
        4: Msg,
        8: {"ShareCode":"#FFHUDT6O3j8tHQPFPo7eP","type":"HUDShare"}, 
        5: 1756580149, 
        7: 1, 
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
    
async def xSEndMsgsQq(Msg , id , K , V, region="IND"):
    """Send message with region 1 title included"""
    avatar = await xBunnEr()
    fields = {
        1: id, 
        2: id, 
        4: Msg,
        8: {"ShareCode":"#FFHUDT6O3j8tHQPFPo7eP","type":"HUDShare"}, 
        5: 1756580149, 
        7: 1, 
        8: 904990072, 
        9: {
            1: "RAFIN - C4", 
            2: avatar, 
            4: 330, 
            5: 1001000001, 
            8: "RAFIN - C4", 
            10: 1, 
            11: 1, 
            13: {1: 2}, 
            14: {
                1: 1158053040, 
                2: 8, 
                3: b"\x10\x15\x08\x0A\x0B\x15\x0C\x0F\x11\x04\x07\x02\x03\x0D\x0E\x12\x01\x05\x06"
            }
        }, 
        10: "en", 
        13: {2: 2, 3: 1},
        14: {
            1: {
                1: random.choice([1, 4]),
                2: 1,
                3: random.randint(1, 180),
                4: 1,
                5: int(datetime.now().timestamp()),
                6: region
            }
        }
    }
    Pk = (await CrEaTe_ProTo(fields)).hex()
    Pk = "080112" + await EnC_Uid(len(Pk) // 2, Tp='Uid') + Pk
    return await GeneRaTePk(Pk, '1201', K, V)

async def AutH_GlobAl(K, V):
    fields = {
        1: 3,
        2: {
            2: 5,
            3: "en"
        }
    }
    return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex() , '1215' , K , V)

async def AutH_Chat(T , uid, code , K, V):
    fields = {
        1: T,
        2: {
            1: uid,
            3: "en",
            4: str(code)
        }
    }
    return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex() , '1215' , K , V)

async def Msg_Sq(msg, owner, bot, K, V):
    fields = {
        1: 1,
        2: 2,
        2: {
            1: bot,
            2: owner,
            4: msg,
            5: 1757799182,
            7: 2,
            9: {
                1: "RAFIN",
                2: await xBunnEr(),
                3: 909000024,
                4: 330,
                5: 909000024,
                7: 2,
                10: 1,
                11: 1,
                12: 0,
                13: {1: 2},
                14: {
                    1: bot,
                    2: 8,
                    3: "\u0010\u0015\b\n\u000b\u0013\f\u000f\u0011\u0004\u0007\u0002\u0003\r\u000e\u0012\u0001\u0005\u0006"
                }
            },
            10: "ar",
            13: {3: 1},
            14: ""
        }
    }
    proto_bytes = await CrEaTe_ProTo(fields)
    return await GeneRaTePk(proto_bytes.hex(), '1215', K, V)

# ============================================
# BASIC SQUAD OPERATIONS
# ============================================

async def CreateNewSquad(K, V, region):
    fields = {
        1: 1,
        2: {
            2: '011d',
            3: 1,
            4: 3,
            5: 'ar',
            8: {
                1: 'IDC4',
                2: 145,
                3: 'ME'
            },
            9: 1,
            10: '01030407090a0b12191a201d2729',
            11: 1,
            13: 1,
            14: {
                1: {
                    6: 56
                },
                2: 731,
                3: '745d59541601024c01015f02020d0905030304570608570d57060d53540402025f5707545301060613050645775945454c18021c051e1a0306491a4760785c53477d735a53486073421b5d5841075642426f5c63610914084e1f005e721f6001467e0c51634263771f5f554642434556660104040f13050445636e74634379505365047256665e405459657766510f615a5250420d11084858416a0d7a470c720065655c5f5a0370584559584a457f43675f460c16024e477a4258430c6050417a45545c47786456597a7a7163545907714109160849667377607d0b4a07657c5c45045f5d784f5b5665096464065875620411050d4d7f7444766661406a6205545d5b5f74507e0b0b535c67580877607d0a1a0148761e795678487f7871465874697177534971666d5a7574677075550d17034503781a675e60787f4d406d7a625d57797d441b47057b026d1a685a0d1102044b0d60040d706067756547767d66777b7f46007346667e43065e5c780813074c5606764057727546596364037054674d590161467f73416209077108',
                4: 'w]ZP',
                6: 11,
                7: '140b7d71715b751011',
                8: '1.126.8',
                9: 3,
                10: 2,
                11: '0362625351363559382b505637416456324b796f566c6364724541566d46795954394b384445494d7a4b646d4b4231562f2b5a727577754a307847426c36712b38683863796b56447967524f4e3676493259347a646974684371364b73464d33724e534a4c4274594f3256565a5465786235484c324c39544a7652514c55374a525663696154544d46776e594e4b4c35353150336c5831475150635668615a77396251674b4d30395a4b6a2f4d675a38656d66757a6e4b356f5a6734367841626a7761363273366235636469637867386a6d4e4944594c383638686e756c3044316a4e445636444a4a69614758456154782b5450696c6f69476f58333638497234563266697a63783934436f5562735039765855683438356a626233356a717a5577504365554c55776374534574456d68426c3957453943524873422b76504a39704863323479517a70446c74644779536f6a6a4f573166433343413733374e617255546d734a70355431686b35635853307134557a6f7a6b75684b6d42423067354f4563634b627a68506c585943712f666a59767531624174504d766437486f4e6e39696e53767679796c6156386e315837636b7978384575626b5868414734565069425961556a75667a2b75675a474164356872324c3156615434613143485745702f6b446142364849434b756f705770706c703151373265463252744f62544957487775305a6753474659514266396f6e48744e7a5035336e72457072366f6c5349455354393839414f494858313471384d4a5763546d514267486d6c3456454c617354426d6f2b36764149525752783664617256692f345147566f4c785944593359477a366e513d3d'
            },
            19: 329,
            21: '374f5219',
            24: {
                1: 21
            }
        }
    }
    if region.lower() == "ind":
        packet = '0514'
    elif region.lower() == "bd":
        packet = "0519"
    else:
        packet = "0515"
    return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex(), packet, K, V)

async def ChangeSquadTo5(uid, K, V, region):
    fields = {
        1: 17,
        2: {
            1: int(uid),
            2: 1,
            3: 4,
            4: 1,
            5: '011d',
            8: 1
        }
    }
    if region.lower() == "ind":
        packet = '0514'
    elif region.lower() == "bd":
        packet = "0519"
    else:
        packet = "0515"
    return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex(), packet, K, V)

async def SendInvite(target_uid, K, V, region):
    fields = {
        1: 2,
        2: {
            1: int(target_uid),
            2: 'ME',
            4: 1
        }
    }
    if region.lower() == "ind":
        packet = '0514'
    elif region.lower() == "bd":
        packet = "0519"
    else:
        packet = "0515"
    return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex(), packet, K, V)

async def OpEnSq(K, V, region):
    return await CreateNewSquad(K, V, region)

async def cHSq(Nu, Uid, K, V, region):
    return await ChangeSquadTo5(Uid, K, V, region)

async def SEnd_InV(size, target_uid, key, iv, region="bd"):
    """Send squad invite to a player"""
    fields = {
        1: 2,
        2: {
            1: int(target_uid),
            2: "BD",
            3: 1,
            4: 1,
            6: "BUDDY-Meow",
            7: 330,
            8: 1000,
            9: 100,
            10: "DZ",
            12: 1,
            13: int(target_uid),
            16: 1,
            17: {
                2: 159,
                4: "y[WW",
                6: 11,
                8: "1.128.2",
                9: 3,
                10: 1
            },
            18: 306,
            19: 18,
            24: 902000306,
            26: {},
            27: {
                1: 11,
                2: int(target_uid),
                3: 99999999999
            },
            28: {},
            31: {
                1: 1,
                2: 32768
            },
            32: 32768,
            34: {
                1: int(target_uid),
                2: 8,
                3: b"\x10\x15\x08\x0A\x0B\x13\x0C\x0F\x11\x04\x07\x02\x03\x0D\x0E\x12\x01\x05\x06"
            }
        }
    }
    if region.lower() == "ind":
        p_type = '0514'
    elif region.lower() == "bd":
        p_type = '0519'
    else:
        p_type = '0515'
    return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex(), p_type, key, iv)


async def ExiT(idT , K , V):
    fields = {
        1: 7,
        2: {
            1: idT,
        }
        }
    return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex() , '0515' , K , V)


# ============================================
# ADVANCED SQUAD CREATION (BR/CS)
# ============================================

def _hex_to_bytes_recursive(obj):
    """Convert any hex string inside dict/list to bytes."""
    if isinstance(obj, dict):
        return {k: _hex_to_bytes_recursive(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_hex_to_bytes_recursive(v) for v in obj]
    elif isinstance(obj, str) and len(obj) % 2 == 0 and all(c in '0123456789abcdefABCDEF' for c in obj):
        try:
            return bytes.fromhex(obj)
        except:
            return obj
    return obj

def _get_squad_fields(squad_type):
    """Exact protobuf fields for BR or CS squad."""
    if squad_type.upper() == "BR":
        return {
            1: 1,
            2: {
                2: '01161d',
                3: 5,
                4: 5,
                5: 'ar',
                8: {1: 'IDC3', 2: 133, 3: 'ME'},
                9: 5,
                10: '01030407090a0b1216191a201d27',
                11: 1,
                13: 1,
                14: {5: 56, 2: 354, 4: '7f585855', 6: 11, 7: '16777b7f6b6e1214', 8: '1.127.1', 9: 5, 10: 5},
                19: 329,
                21: '374f5219',
                24: {1: 21}
            }
        }
    else:  # CS
        return {
            1: 1,
            2: {
                2: '010304161d',
                3: 15,
                4: 3,
                5: 'ar',
                8: {1: 'IDC3', 2: 132, 3: 'ME'},
                9: 6,
                10: '01030407090a0b1216191a201d27',
                11: 1,
                13: 1,
                14: {6: 56, 2: 250, 4: '7f585855', 6: 11, 7: '16777b7f6b6e1214', 8: '1.127.1', 9: 3, 10: 2},
                19: 324,
                20: 36,
                21: '374f5219',
                24: {1: 21}
            }
        }

async def create_squad_packet(squad_type, key, iv):
    """Create encrypted squad packet (0515)."""
    fields = _get_squad_fields(squad_type)
    fields = _hex_to_bytes_recursive(fields)
    proto_hex = (await CrEaTe_ProTo(fields)).hex()
    return await GeneRaTePk(proto_hex, '0515', key, iv)

async def Join_Squad_Packet_TC(team_code, K, V, region="bd"):
    """Join team using team code (TCP version)"""
    fields = {
        1: 4,
        2: {
            4: bytes.fromhex("01090a0b121920"),
            5: str(team_code),
            6: 6,
            8: 1,
            9: {2: 1393, 6: 11, 8: "1.120.2", 9: 5, 10: 1}
        }
    }
    p_type = '0519' if region.lower() == "bd" else '0515'
    return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex(), p_type, K, V)

async def join_teamcode_packet(team_code, key, iv, region="bd"):
    """Join team using code"""
    fields = {
        1: 4,
        2: {
            4: bytes.fromhex("01090a0b121920"),
            5: str(team_code),
            6: 6,
            8: 1,
            9: {
                2: 800,
                6: 11,
                8: "1.111.1",
                9: 5,
                10: 1
            }
        }
    }
    if region.lower() == "ind":
        packet_type = '0514'
    elif region.lower() == "bd":
        packet_type = "0519"
    else:
        packet_type = "0515"
    return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex(), packet_type, key, iv)

# ============================================
# SQUAD PROTECTION & EVENTS
# ============================================

async def rizak(uid, secret_code, key, iv):
    """Rizak packet function - creates special packet for team leave/kick events"""
    fields = {
        1: 61,
        2: {
            1: int(uid),  
            2: {
                1: int(uid), 
                2: int(datetime.now().timestamp()),
                3: "TAHMID-CODEX",
                5: 12,
                6: random.randint(11, 16),
                7: 1,
                8: {2: 1, 3: 1},
                9: 1,   
            },
            3: str(secret_code),  
        }
    }
    packet = await CrEaTe_ProTo(fields)
    packet_hex = packet.hex()
    header_lenth = len(await EnC_PacKeT(packet_hex, key, iv)) // 2
    header_lenth_final = dec_to_hex(header_lenth)
    prefix = "0515" + "0" * (6 - len(header_lenth_final))

    encrypted = await EnC_PacKeT(packet_hex, key, iv)
    final_packet = prefix + header_lenth_final + encrypted
    return bytes.fromhex(final_packet)

# ============================================
# TEAM PUBLIC / PRIVATE & DND
# ============================================

async def Team_Public(bot_uid, key, iv):
    """Team public packet"""
    fields = {1: 36, 2: {1: int(bot_uid)}}
    proto_bytes = await CrEaTe_ProTo(fields)
    packet_hex = proto_bytes.hex()

    encrypted = await EnC_PacKeT(packet_hex, key, iv)
    header_length = len(encrypted) // 2
    header_length_hex = dec_to_hex(header_length)

    prefix = "051500" + "0" * (6 - len(header_length_hex))
    final_packet = prefix + header_length_hex + encrypted
    return bytes.fromhex(final_packet)

async def Team_Private(bot_uid, key, iv):
    """Team private packet"""
    fields = {1: 37, 5: {1: int(bot_uid)}}
    proto_bytes = await CrEaTe_ProTo(fields)
    packet_hex = proto_bytes.hex()

    encrypted = await EnC_PacKeT(packet_hex, key, iv)
    header_length = len(encrypted) // 2
    header_length_hex = dec_to_hex(header_length)

    prefix = "051500" + "0" * (6 - len(header_length_hex))
    final_packet = prefix + header_length_hex + encrypted
    return bytes.fromhex(final_packet)

async def create_dnd_packet(dnd_enabled, key, iv):
    """Create Do Not Disturb packet"""
    fields = {
        1: 2,
        2: {
            1: 2 if dnd_enabled else 1
        }
    }
    proto_hex = (await CrEaTe_ProTo(fields)).hex()
    return await GeneRaTePk(proto_hex, '0f15', key, iv)

# ============================================
# LEADER TRANSFER
# ============================================

async def TransferLeaderPacket(target_uid, key, iv, region, bot_uid):
    """Transfer squad leadership to target player"""
    fields = {
        1: 57,
        2: {
            1: int(bot_uid),
            2: int(target_uid)
        }
    }
    if region.lower() == "ind":
        pkt_type = '0514'
    elif region.lower() == "bd":
        pkt_type = '0519'
    else:
        pkt_type = '0515'
    return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex(), pkt_type, key, iv)

# ============================================
# CUSTOM ROOM FUNCTIONS
# ============================================

async def join_custom_room(room_id, room_password, key, iv, region):
    """Join custom room with proper Free Fire packet structure"""
    fields = {
        1: 61,
        2: {
            1: int(room_id),
            2: {
                1: int(room_id),
                2: int(time.time()),
                3: "BOT",
                5: 12,
                6: 9999999,
                7: 1,
                8: {2: 1, 3: 1},
                9: 3,
            },
            3: str(room_password),
        }
    }
    if region.lower() == "ind":
        packet_type = '0514'
    elif region.lower() == "bd":
        packet_type = "0519"
    else:
        packet_type = "0515"
    return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex(), packet_type, key, iv)

async def create_custom_room(room_name, room_password, max_players, key, iv, region):
    """Create a custom room"""
    fields = {
        1: 3,
        2: {
            1: room_name,
            2: room_password,
            3: max_players,
            4: 1,
            5: 1,
            6: "en",
            7: {
                1: "BotHost",
                2: int(await xBunnEr()),
                3: 330,
                4: 1048576,
                5: "BOTCLAN"
            }
        }
    }
    if region.lower() == "ind":
        packet_type = '0514'
    elif region.lower() == "bd":
        packet_type = "0519"
    else:
        packet_type = "0515"
    return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex(), packet_type, key, iv)

async def RoomJoin_fields(room_id, password, key, iv):
    """Room join using fields dictionary format"""
    try:
        fields = {
            1: 3,
            2: {
                1: int(room_id),
                2: str(password),
                8: {1: "IDC3", 2: 149, 3: "IND"},
                9: b"\x01\x03\x04\x07\x09\x0a\x0b\x12\x0e\x16\x19\x20\x1d",
                10: 1,
                12: {},
                13: 1,
                14: 1,
                16: "en",
                22: {1: 21}
            }
        }
        proto_bytes = await CrEaTe_ProTo(fields)
        packet_hex = proto_bytes.hex()
        encrypted_packet = await EnC_PacKeT(packet_hex, key, iv)
        packet_length = len(encrypted_packet) // 2
        hex_length = dec_to_hex(packet_length)
        
        if len(hex_length) == 2:
            header = "0e15000000"
        elif len(hex_length) == 3:
            header = "0e1500000"
        elif len(hex_length) == 4:
            header = "0e150000"
        elif len(hex_length) == 5:
            header = "0e15000"
        else:
            header = "0e150000"
        
        final_packet_hex = header + hex_length + encrypted_packet
        return bytes.fromhex(final_packet_hex)
    except Exception as e:
        print(f"❌ Room join fields error: {e}")
        return None

# ============================================
# AUTO-ACCEPT & BADGE FUNCTIONS
# ============================================

async def request_join_with_badge(target_uid, badge_value, key, iv, region="IND"):
    """Fixed badge spam function matching craftland_badge structure"""
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
                6: "TG:[C][B][FF0000] @Beotherjk",
                7: 330,
                8: 1000,
                10: region.upper(),
                11: bytes([49, 97, 99, 52, 98, 56, 48, 101, 99, 102, 48, 52, 55, 56,
                          97, 52, 52, 50, 48, 51, 98, 102, 56, 102, 97, 99, 54, 49,
                          50, 48, 102, 53]),
                12: 1,
                13: int(target_uid),
                14: {1: 2203434355, 2: 8, 3: b"\x10\x15\x08\x0A\x0B\x13\x0C\x0F\x11\x04\x07\x02\x03\x0D\x0E\x12\x01\x05\x06"},
                16: 1,
                17: 1,
                18: 312,
                19: 46,
                23: bytes([16, 1, 24, 1]),
                24: avatar_id,
                26: {},
                27: {1: 11, 2: 12999994075, 3: 9999},
                28: {},
                31: {1: 1, 2: int(badge_value)},
                32: int(badge_value),
                34: {1: int(target_uid), 2: 8, 3: b"\x0F\x06\x15\x08\x0A\x0B\x13\x0C\x11\x04\x0E\x14\x07\x02\x01\x05\x10\x03\x0D\x12"}
            },
            10: "en",
            13: {2: 1, 3: 1}
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

async def RejectMSGtaxt(squad_owner, uid, key, iv):
    """Create reject message packet"""
    random_banner = """\n.\n.\n.\n\nTCP BOT[00FFCC]\nWELCOME TO BUDDY MEOW BOT\n """
    fields = {
        1: 5,
        2: {
            1: int(squad_owner),
            2: 1,
            3: int(uid),
            4: random_banner
        }
    }
    return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex(), '0515', key, iv)

async def MahirAccepted(uid, code, K, V, region="bd"):
    """Accept squad invite packet"""
    fields = {
        1: 4,
        2: {
            1: int(uid),
            3: int(uid),
            4: bytes.fromhex("01090a0b121920"), 
            8: 1,
            9: {
                2: 161,
                4: "y[WW",
                6: 11,
                8: "1.114.18", 
                9: 3,
                10: 1
            },
            10: str(code),
        }
    }
    if region.lower() == "ind":
        p_type = '0514'
    elif region.lower() == "bd":
        p_type = '0519'
    else:
        p_type = '0515'
    return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex(), p_type, K, V)

async def RedZed_SendInv(bot_uid, uid, key, iv):
    """Send invite packet"""
    try:
        fields = {
            1: 2, 
            2: {
                1: int(uid), 
                2: "IND", 
                3: 1, 
                4: 1, 
                6: "RedZedKing!!", 
                7: 330, 
                8: 1000, 
                9: 100, 
                10: "DZ", 
                12: 1, 
                13: int(uid), 
                16: 1, 
                17: {
                    2: 159, 
                    4: "y[WW", 
                    6: 11, 
                    8: "1.120.2", 
                    9: 3, 
                    10: 1
                }, 
                18: 306, 
                19: 18, 
                24: 902000306, 
                26: {}, 
                27: {
                    1: 11, 
                    2: int(bot_uid), 
                    3: 99999999999
                }, 
                28: {}, 
                31: {
                    1: 1, 
                    2: 32768
                }, 
                32: 32768, 
                34: {
                    1: bot_uid, 
                    2: 8, 
                    3: b"\x10\x15\x08\x0A\x0B\x13\x0C\x0F\x11\x04\x07\x02\x03\x0D\x0E\x12\x01\x05\x06"
                }
            }
        }
        packet = await CrEaTe_ProTo(fields)
        packet_hex = packet.hex()
        final_packet = await GeneRaTePk(packet_hex, '0515', key, iv)
        return final_packet
    except Exception as e:
        print(f"❌ Error in RedZed_SendInv: {e}")
        return None

# ============================================
# MISC UTILITY & BOT PACKETS
# ============================================

async def LagSquad(K,V):
    fields = {
        1: 15,
        2: {
            1: 1124759936,
            2: 1
        }
    }
    return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex() , '0515' , K , V)

async def GeT_Status(PLayer_Uid , K , V):
    PLayer_Uid = await EnC_Uid(PLayer_Uid , Tp = 'Uid')
    if len(PLayer_Uid) == 8: Pk = f'080112080a04{PLayer_Uid}1005'
    elif len(PLayer_Uid) == 10: Pk = f"080112090a05{PLayer_Uid}1005"
    return await GeneRaTePk(Pk , '0f15' , K , V)
           
async def SPam_Room(Uid , Rm , Nm , K , V):
    fields = {1: 78, 2: {1: int(Rm), 2: f"[{await ArA_CoLor()}]{Nm}", 3: {2: 1, 3: 1}, 4: 330, 5: 1, 6: 201, 10: await xBunnEr(), 11: int(Uid), 12: 1}}
    return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex() , '0e15' , K , V)

async def GenJoinSquadsPacket(code,  K , V):
    fields = {}
    fields[1] = 4
    fields[2] = {}
    fields[2][4] = bytes.fromhex("01090a0b121920")
    fields[2][5] = str(code)
    fields[2][6] = 6
    fields[2][8] = 1
    fields[2][9] = {}
    fields[2][9][2] = 800
    fields[2][9][6] = 11
    fields[2][9][8] = "1.111.1"
    fields[2][9][9] = 5
    fields[2][9][10] = 1
    return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex() , '0515' , K , V)   

async def GenJoinGlobaL(owner , code , K, V):
    fields = {
        1: 4,
        2: {
            1: owner,
            6: 1,
            8: 1,
            13: "en",
            15: code,
            16: "OR",
        }
    }
    return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex() , '0515' , K , V)

async def FS(key, iv, region="ind"):
    """Start match packet - converted from TCP version"""
    try:
        fields = {
            1: 9,
            2: {
                1: 12480598706,
            }
        }
        packet = await CrEaTe_ProTo(fields)
        packet_hex = packet.hex()
        encrypted_packet = await EnC_PacKeT(packet_hex, key, iv)
        header_length = len(encrypted_packet) // 2
        header_length_final = await DecodE_HeX(header_length)
        
        if region.lower() == "ind":
            packet_type = '0514'
        elif region.lower() == "bd":
            packet_type = "0519"
        else:
            packet_type = "0515"
        
        if len(header_length_final) == 2:
            final_packet_hex = packet_type + "000000" + header_length_final + encrypted_packet
        elif len(header_length_final) == 3:
            final_packet_hex = packet_type + "00000" + header_length_final + encrypted_packet
        elif len(header_length_final) == 4:
            final_packet_hex = packet_type + "0000" + header_length_final + encrypted_packet
        elif len(header_length_final) == 5:
            final_packet_hex = packet_type + "000" + header_length_final + encrypted_packet
        elif len(header_length_final) == 6:
            final_packet_hex = packet_type + "00" + header_length_final + encrypted_packet
        else:
            final_packet_hex = packet_type + "000000" + header_length_final + encrypted_packet
        
        return bytes.fromhex(final_packet_hex)
    except Exception as e:
        print(f"❌ Error creating start packet: {e}")
        return None

async def Emote_k(TarGeT , idT, K, V,region="bd"):
    fields = {
        1: 21,
        2: {
            1: 804266360,
            2: 909000001,
            5: {
                1: TarGeT,
                3: idT,
            }
        }
    }
    if region.lower() == "ind":
        packet = '0514'
    elif region.lower() == "bd":
        packet = "0519"
    else:
        packet = "0515"
    return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex() , packet , K , V)

async def GeTSQDaTa(D):
    try:
        uid = D.get('5', {}).get('data', {}).get('1', {}).get('data', None)
        chat_code = D.get("5", {}).get("data", {}).get("17", {}).get("data", None)
        squad_code = D.get("5", {}).get("data", {}).get("31", {}).get("data", None)
        
        if uid is None or chat_code is None or squad_code is None:
            return None, None, None
            
        return uid, chat_code, squad_code
    except Exception as e:
        return None, None, None
  
async def AuthClan(CLan_Uid, AuTh, K, V):
    fields = {1: 3, 2: {1: int(CLan_Uid), 2: 1, 4: str(AuTh)}}
    return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex() , '1201' , K , V)

def join_room_chanel(room_id, key, iv):
    fields = {
        1: 3,
        2: {
            1: int(room_id),
            2: 3,
            3: "en",
        },
    }
    packet = create_protobuf_packet(fields)
    packet = packet.hex() + "7200"
    header_lenth = len(encrypt_packet(packet, key, iv)) // 2
    header_lenth = dec_to_hex(header_lenth)
    if len(header_lenth) == 2:
        final_packet = "1215000000" + header_lenth + encrypt_packet(packet, key, iv)
        return bytes.fromhex(final_packet)
    if len(header_lenth) == 3:
        final_packet = "121500000" + header_lenth + encrypt_packet(packet, key, iv)
        return bytes.fromhex(final_packet)
    if len(header_lenth) == 4:
        final_packet = "12150000" + header_lenth + encrypt_packet(packet, key, iv)
        return bytes.fromhex(final_packet)
    if len(header_lenth) == 5:
        final_packet = "12150000" + header_lenth + encrypt_packet(packet, key, iv)
        return bytes.fromhex(final_packet)

async def ArohiRefuse(owner,uid, K,V):
    fields = {
        1: 5,
        2: {
            1: int(owner),
            2: 1,
            3: int(uid),
            4: "[FF0000][B][C] ERROR , WELCOME TO [FFFFFF] RAFIN [00FF00] BOT ! \n[FFFF00]NEW VERSION NEW FUNCTION !\n[FF0000]TELEGRAM : @juli_dvrma\n\n"
        }
    }
    return await GeneRaTePk((await CrEaTe_ProTo(fields)).hex() , '0515' , K , V)

async def bundle_packet_async(bundle_id, K, V, region="bd"):
    """Create bundle packet optimized"""
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

