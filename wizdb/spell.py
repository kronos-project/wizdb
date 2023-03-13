from .utils import SCHOOLS


class Spell:
    def __init__(self, template_id: int, state, obj: dict):
        self.template = template_id
        self.name = state.make_lang_key(obj)
        if self.name.id is None:
            self.name.id = state.cache.add_entry(obj["m_name"], obj["m_name"].decode())
        self.image = obj["m_imageName"].decode()
        self.accuracy = obj["m_accuracy"]
        self.school = SCHOOLS.index(obj["m_sMagicSchoolName"])
        self.description = state.make_lang_key({"m_displayName": obj["m_description"]})

        rank = obj["m_spellRank"]
        self.rank = rank["m_spellRank"]
        self.life_pips = rank["m_lifePips"]
        self.x_pips = rank["m_xPipSpell"]
        self.fire_pips = rank["m_firePips"]
        self.myth_pips = rank["m_mythPips"]
        self.balance_pips = rank["m_balancePips"]
        self.ice_pips = rank["m_icePips"]
        self.storm_pips = rank["m_spellRank"]
        self.shadow_pips = rank["m_shadowPips"]
        self.death_pips = rank["m_deathPips"]


class SpellCache:
    def __init__(self, state):
        self.cache = {}
        self.name_to_id = {}

        for file, template in state.file_to_id.items():
            if not file.startswith("Spells/"):
                continue

            # FIXME: Kobold bug
            try:
                value = state.de.deserialize(
                    (state.root_wad / file).read_bytes())
            except:
                print(f"kobold: Failed to deserialize {state.root_wad / file}!")
                continue

            spell = Spell(template, state, value)
            self.cache[template] = spell
            self.name_to_id[value["m_name"].decode()] = template

    def get(self, name: str) -> int:
        if tid := self.name_to_id.get(name):
            return tid
        else:
            return None
