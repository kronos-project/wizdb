from struct import pack
from typing import List

SCHOOLS = [
    b"",
    b"Fire",
    b"Ice",
    b"Storm",
    b"Myth",
    b"Life",
    b"Death",
    b"Balance",
    b"Star",
    b"Sun",
    b"Moon",
    b"Gardening",
    b"Shadow",
    b"Fishing",
    b"Cantrips",
    b"CastleMagic",
    b"WhirlyBurly",
]

SPELL_TYPES = [
    b"",
    b"Heal",
    b"Damage",
    b"Charm",
    b"Ward",
    b"Aura",
    b"Global",
    b"AOE",
    b"Steal",
    b"Manipulation",
    b"Enchantment",
    b"Polymorph",
    b"Curse",
    b"Jinx",
    b"Mutate",
    b"Cloak",
    b"Shadow",
    b"Shadow_Creature",
    b"Shadow_Self",
]


def pack_int_blob(data: List[int]) -> bytes:
    data_len = len(data)
    return pack(f"<B{data_len}i", data_len, *data)


def get_school_index(name: bytes) -> int:
    return SCHOOLS.index(name.replace(b"None", b"").replace(b"All", b"").replace(b"Generic", b""))


def convert_rarity(obj: dict) -> int:
    rarity = obj.get("m_rarity", "r::RT_UNKNOWN").split("::")[1]
    if rarity == "RT_COMMON":
        return 0
    elif rarity == "RT_UNCOMMON":
        return 1
    elif rarity == "RT_RARE":
        return 2
    elif rarity == "RT_ULTRARARE":
        return 3
    elif rarity == "RT_EPIC":
        return 4
    else:
        return -1


def fnv_1a(data) -> int:
    if isinstance(data, str):
        data = data.encode()

    state = 0xCBF2_9CE4_8422_2325
    for b in data:
        state ^= b
        state *= 0x0000_0100_0000_01B3
        state &= 0xFFFF_FFFF_FFFF_FFFF
    return state >> 1
