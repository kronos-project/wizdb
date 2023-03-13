from .jewels import JewelSockets
from .requirements import parse_equip_reqs
from .state import State
from .utils import convert_rarity, SCHOOLS

ITEM_ADJECTIVES = (b"Hat", b"Robe", b"Shoes", b"Weapon", b"Athame", b"Amulet", b"Ring", b"Deck", b"Jewel", b"Mount")


def is_item_template(obj: dict) -> bool:
    name = obj.get("m_displayName", b"")
    adjectives = obj.get("m_adjectiveList", [])

    return name and not name.startswith(b"ItemTestStrings") and any(a in adjectives for a in ITEM_ADJECTIVES)


class Item:
    def __init__(self, state: State, obj: dict):
        self.template_id = obj["m_templateID"]
        self.name = state.make_lang_key(obj)
        self.set_bonus_id = state.add_set_bonus(obj["m_itemSetBonusTemplateID"])
        self.rarity = convert_rarity(obj)

        reqs = obj["m_equipRequirements"] or {}
        self.equip_reqs = parse_equip_reqs(reqs)

        self.jewel_sockets = JewelSockets()

        adj = obj["m_adjectiveList"]
        self.adjectives = 0
        for idx, entry in enumerate(ITEM_ADJECTIVES):
            if entry in adj:
                self.adjectives |= (1 << idx)

        if "PetJewel" in adj:
            self.adjectives |= (1 << 16)
        if "FLAG_NoAuction" in adj:
            self.adjectives |= (1 << 17)
        if "FLAG_CrownsOnly" in adj:
            self.adjectives |= (1 << 18)
        if "FLAG_NoGift" in adj:
            self.adjectives |= (1 << 19)
        if "FLAG_InstantEffect" in adj:
            self.adjectives |= (1 << 20)
        if "FLAG_NoCombat" in adj:
            self.adjectives |= (1 << 21)
        if "FLAG_NoDrops" in adj:
            self.adjectives |= (1 << 22)
        if "FLAG_NoDye" in adj:
            self.adjectives |= (1 << 23)
        if "FLAG_NoHatchmaking" in adj:
            self.adjectives |= (1 << 24)
        if "FLAG_NoPVP" in adj:
            self.adjectives |= (1 << 25)
        if "FLAG_NoSell" in adj:
            self.adjectives |= (1 << 26)
        if "FLAG_NoShatter" in adj:
            self.adjectives |= (1 << 27)
        if "FLAG_NoTrade" in adj:
            self.adjectives |= (1 << 28)
        if "FLAG_PVPOnly" in adj:
            self.adjectives |= (1 << 29)
        if "FLAG_ArenaPointsOnly" in adj:
            self.adjectives |= (1 << 30)
        if "FLAG_BlueArenaPointsOnly" in adj:
            self.adjectives |= (1 << 31)

        self.min_pet_level = 0
        self.pet_talents = []

        self.max_spells = 0
        self.max_copies = 0
        self.max_school_copies = 0
        self.deck_school = 0
        self.max_tcs = 0
        self.archmastery_points = 0.

        for behavior in obj["m_behaviors"]:
            name = behavior["m_behaviorName"]

            if name == b"JewelSocketBehavior":
                for idx, socket in enumerate(behavior["m_jewelSockets"]):
                    self.jewel_sockets.add_socket(idx, socket)

            elif name == b"PetJewelBehavior":
                self.min_pet_level = behavior["m_minPetLevel"]
                self.pet_talents = [state.talents.get(t.decode()) for t in behavior["m_petTalentName"]]

            elif name == b"BasicDeckBehavior":
                self.max_spells = behavior["m_maxSpells"]
                self.max_copies = behavior["m_genericMaxInstances"]
                self.max_school_copies = behavior["m_schoolMaxInstances"]
                self.deck_school = SCHOOLS.index(behavior["m_primarySchoolName"].replace(b"None", b"").replace(b"All", b"").replace(b"Generic", b""))
                self.max_tcs = behavior["m_maxTreasureCards"]
                self.archmastery_points = behavior["m_maxArchmasteryPoints"]

        self.stats = []
        for effect in obj["m_equipEffects"]:
            if stat := state.translate_stat(effect):
                self.stats.append(stat)

    def __repr__(self):
        return ", ".join([repr(s) for s in self.stats])
