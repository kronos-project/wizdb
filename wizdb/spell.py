from kobold_py import KoboldError
from struct import pack

from .utils import get_school_index, SCHOOLS, SPELL_TYPES


def find_effects(data: dict, effects, damage_types, num_rounds):
    for k, v in data.items():
        if k == "m_effectParam":
            effects.append(v)
        elif k == "m_sDamageType":
            damage_types.append(v)
        elif k == "m_numRounds":
            num_rounds.append(v)
        elif isinstance(v, dict):
            find_effects(v, effects, damage_types, num_rounds)
        elif isinstance(v, list):
            for item in filter(lambda i: isinstance(i, dict), v):
                find_effects(item, effects, damage_types, num_rounds)


class Spell:
    def __init__(self, template_id: int, state, obj: dict):
        self.template = template_id
        self.name = state.make_lang_key(obj)
        if self.name.id is None:
            self.name.id = state.cache.add_entry(obj["m_name"], obj["m_name"].decode())
        self.real_name = obj["m_name"]
        self.image = obj["m_imageName"].decode()
        self.accuracy = obj["m_accuracy"]
        self.school = get_school_index(obj["m_sMagicSchoolName"])
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

        self.effect_params = []
        self.damage_types = []
        self.num_rounds = []

        raw_damage_types = []
        find_effects(obj, self.effect_params, raw_damage_types, self.num_rounds)

        for dt in raw_damage_types:
            try:
                self.damage_types.append(get_school_index(dt))
            except ValueError:
                self.damage_types.append(0)


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
