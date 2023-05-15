from kobold_py import KoboldError
from struct import pack as pk
from typing import List

from .utils import SCHOOLS, SPELL_TYPES

def find_effects(d, effects, damage_types, num_rounds):
    dictionaries_to_search = []
    for k, v in d.items():
        if k == "m_effectParam":
            effects.append(v)
        if k == "m_sDamageType":
            damage_types.append(v)
        if k == "m_numRounds":
            num_rounds.append(v)
        elif isinstance(v, dict):
            dictionaries_to_search.append(v)
        elif isinstance(v, list):
            for item in v:
                if isinstance(item, dict):
                    dictionaries_to_search.append(item)

    for dictionary in dictionaries_to_search:
        find_effects(dictionary, effects, damage_types, num_rounds)



class Spell:
    def __init__(self, template_id: int, state, obj: dict):
        self.template = template_id
        self.name = state.make_lang_key(obj)
        if self.name.id is None:
            self.name.id = state.cache.add_entry(obj["m_name"], obj["m_name"].decode())
        self.real_name = obj["m_name"]
        self.image = obj["m_imageName"].decode()
        self.accuracy = obj["m_accuracy"]
        self.school = SCHOOLS.index(obj["m_sMagicSchoolName"])
        self.description = state.make_lang_key({"m_displayName": obj["m_description"]})
        self.type_name = SPELL_TYPES.index(obj["m_sTypeName"])

        rank = obj["m_spellRank"]
        self.rank = rank["m_spellRank"]
        self.x_pips = rank["m_xPipSpell"]
        self.shadow_pips = rank["m_shadowPips"]
        
        self.fire_pips = rank["m_firePips"]
        self.ice_pips = rank["m_icePips"]
        self.storm_pips = rank["m_stormPips"]
        self.myth_pips = rank["m_mythPips"]
        self.life_pips = rank["m_lifePips"]
        self.death_pips = rank["m_deathPips"]
        self.balance_pips = rank["m_balancePips"]

        raw_effects = []
        raw_damage_type = []
        raw_num_rounds = []
        find_effects(obj, raw_effects, raw_damage_type, raw_num_rounds)

        while len(raw_effects) > 26:
            raw_effects.pop()
        while len(raw_effects) < 26:
            raw_effects.append(0)
        while len(raw_damage_type) > 26:
            raw_damage_type.pop()
        while len(raw_damage_type) < 26:
            raw_damage_type.append(0)
        while len(raw_num_rounds) > 26:
            raw_num_rounds.pop()
        while len(raw_num_rounds) < 26:
            raw_num_rounds.append(0)

        index_damage_types = []
        for dt in raw_damage_type:
            try:
                index_damage_types.append(SCHOOLS.index(dt))
            except ValueError:
                index_damage_types.append(0)

        self.effect_params= raw_effects
        self.damage_types = index_damage_types
        self.num_rounds = raw_num_rounds




class SpellCache:
    def __init__(self, state):
        self.cache = {}
        self.name_to_id = {}

        for file, template in state.file_to_id.items():
            if not file.startswith("Spells/"):
                continue
            
            try:
                value = state.de.deserialize((state.root_wad / file).read_bytes())
            except KoboldError as Err:
                print(Err)
                continue

            spell = Spell(template, state, value)
            self.cache[template] = spell
            self.name_to_id[value["m_name"].decode()] = template

    def get(self, name: str) -> int:
        if tid := self.name_to_id.get(name):
            return tid
        else:
            return None
