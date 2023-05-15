from .state import State
from .utils import get_school_index


def is_mob_template(obj: dict) -> bool:
    name = obj.get("m_displayName", b"")
    aggro_sound = obj.get("m_aggroSound", b"NA")

    has_duel = False
    for behavior in filter(lambda b: b is not None, obj["m_behaviors"]):
        if behavior["m_behaviorName"] == b"DuelistBehavior":
            has_duel = True

    return name and aggro_sound != b"NA" and has_duel


class Mob:
    def __init__(self, state: State, obj: dict):
        self.template_id = obj["m_templateID"]
        self.name = state.make_lang_key(obj)

        effect_behavior = None
        for behavior in filter(lambda b: b is not None, obj["m_behaviors"]):
            if behavior["m_behaviorName"] == b'NPCBehavior':
                effect_behavior = behavior

        self.is_boss = effect_behavior["m_bossMob"]
        self.intelligence = round(effect_behavior["m_fIntelligence"], 5)
        self.selfish_factor = round(effect_behavior["m_fSelfishFactor"], 5)
        self.aggressive_factor = effect_behavior["m_nAggressiveFactor"]
        self.rank = effect_behavior["m_nLevel"]
        self.hitpoints = effect_behavior["m_nStartingHealth"]
        self.primary_school = get_school_index(effect_behavior["m_schoolOfFocus"])
        self.secondary_school = get_school_index(effect_behavior["m_secondarySchoolOfFocus"]) # May remove due to implications of dual schooling

        self.is_shadow = effect_behavior["m_maxShadowPips"] > 0

        self.stats = []
        for effect in effect_behavior["m_baseEffects"]:
            if stat := state.translate_stat(effect):
                self.stats.append(stat)

    def __repr__(self):
        return ", ".join([repr(s) for s in self.stats])
