import sqlite3
from sqlite3 import Cursor

from .lang_files import LangCache
from .set_bonus import SetBonusCache
from .spell import SpellCache

INIT_QUERIES = """CREATE TABLE locale_en (
    id   integer not null primary key,
    data text not null
);

CREATE INDEX en_name_lookup ON locale_en(data);

CREATE TABLE set_bonuses (
    id   integer not null primary key,
    name integer not null,

    foreign key(name) references locale_en(id)
);

CREATE TABLE set_stats (
    id             integer not null primary key,
    bonus_set      integer not null,
    activate_count integer not null,

    kind           integer not null,
    a              integer,
    b              integer,

    foreign key(bonus_set) references set_bonuses(id)
);

CREATE INDEX set_stat_lookup ON set_stats(bonus_set);

CREATE TABLE items (
    id                 integer not null primary key,
    name               integer not null,
    bonus_set          integer,
    rarity             integer,
    jewels             integer,
    kind               integer not null,
    extra_flags        integer,

    equip_school       integer,
    equip_level        integer,

    -- When the PetJewel bit in extra_flags is set.
    min_pet_level      integer,

    -- When deck bit in kind is set.
    max_spells         integer,
    max_copies         integer,
    max_school_copies  integer,
    deck_school        integer,
    max_tcs            integer,
    archmastery_points real,

    foreign key(name)  references locale_en(id),
    foreign key(bonus_set) references set_bonuses(id)
);

CREATE TABLE item_stats (
    id       integer not null primary key,
    item     integer not null,

    kind     integer not null,
    a        integer,
    b        integer,

    foreign key(item) references items(id)
);

CREATE INDEX item_stat_lookup ON item_stats(item);

CREATE TABLE pet_talents (
    id   integer not null primary key,
    item integer not null,
    name integer not null,

    foreign key(item) references items(id),
    foreign key(name) references locale_en(id)
);

CREATE INDEX item_talent_lookup ON pet_talents(item);

CREATE TABLE spells (
    id              integer not null primary key,
    template_id     integer not null,
    name            integer not null,
    real_name       text,
    image           text,
    accuracy        integer,
    school          integer,
    description     integer,
    form            integer,

    rank            integer,
    x_pips          bool,
    shadow_pips     integer,
    fire_pips       integer,
    ice_pips        integer,
    storm_pips      integer,
    myth_pips       integer,
    life_pips       integer,
    death_pips      integer,
    balance_pips    integer,

    foreign key(name)        references locale_en(id)
);

CREATE TABLE effects (
    id       integer not null primary key,
    spell    integer not null,
    kind     integer not null,
    a        integer,
    b        integer,
    c        integer,
    d        integer,
    e        integer,
    f        integer,
    g        integer,
    h        integer,
    i        integer,
    j        integer,
    k        integer,
    l        integer,
    m        integer,
    n        integer,
    o        integer,
    p        integer,
    q        integer,
    r        integer,
    s        integer,
    t        integer,
    u        integer,
    v        integer,
    w        integer,
    x        integer,
    y        integer,
    z        integer,

    foreign key(spell) references spells(id)
);


CREATE TABLE mobs (
    id                  integer not null primary key,
    name                integer not null,
    is_boss             bool,
    rank                integer,
    hp                  integer,
    primary_school      integer,
    secondary_school    integer,
    is_shadow           bool,
    intelligence        real,
    selfishness         real,
    aggressiveness      real,

    foreign key(name)        references locale_en(id)
);

CREATE TABLE mob_stats (
    id       integer not null primary key,
    mob      integer not null,

    kind     integer not null,
    a        integer,
    b        integer,

    foreign key(mob) references mobs(id)
);
"""


def convert_stat(stat):
    match stat.kind:
        case 1: return 1, stat.category, stat.value
        case 2: return 2, stat.pips, stat.power_pips
        case 3: return 3, stat.spell, stat.count
        case 4: return 4, stat.spell, stat.desc_key.id
        case 5: return 5, stat.multiplier, 0
        case 6: return 6, stat.count, 0

        case _: raise RuntimeError()


def convert_equip_reqs(reqs):
    level = 0
    school = 0

    for req in reqs:
        match req.id:
            case 1: level = req.level
            case 2: school = req.school

    return school, level


def _progress(_status, remaining, total):
    print(f'Copied {total-remaining} of {total} pages...')


def build_db(state, items, mobs, out):
    mem = sqlite3.connect(":memory:")
    cursor = mem.cursor()

    initialize(cursor)
    insert_locale_data(cursor, state.cache)
    insert_spell_data(cursor, state.spells)
    insert_set_bonuses(cursor, state.bonuses)
    insert_items(cursor, items)
    insert_mobs(cursor, mobs)
    mem.commit()

    with out:
        mem.backup(out, pages=1, progress=_progress)

    mem.close()


def initialize(cursor):
    cursor.executescript(INIT_QUERIES)


def insert_locale_data(cursor, cache: LangCache):
    cursor.executemany(
        "INSERT INTO locale_en(id, data) VALUES (?, ?)",
        cache.lookup.items()
    )


def insert_spell_data(cursor: Cursor, cache: SpellCache):
    spells = []
    effects = []
    damages = []
    rounds = []
    for template, spell in cache.cache.items():
        spells.append((
            template,
            spell.name.id,
            spell.real_name,
            spell.image,
            spell.accuracy,
            spell.school,
            spell.description.id,
            spell.type_name,
            spell.rank,
            spell.x_pips,
            spell.shadow_pips,
            spell.fire_pips,
            spell.ice_pips,
            spell.storm_pips,
            spell.myth_pips,
            spell.life_pips,
            spell.death_pips,
            spell.balance_pips,
        ))

        effect_params = spell.effect_params
        damage_types = spell.damage_types
        num_rounds = spell.num_rounds
        if not damage_types:
            damage_types = [0] * 33
        if not effect_params:
            effect_params = [0] * 33
        if not num_rounds:
            num_rounds = [0] * 33

        effect_params.insert(0, template)
        effect_params.insert(1, 1)
        damage_types.insert(0, template)
        damage_types.insert(1, 2)
        num_rounds.insert(0, template)
        num_rounds.insert(1, 3)

        effects.append(tuple(effect_params))
        damages.append(tuple(damage_types))
        rounds.append(tuple(num_rounds))

    cursor.executemany(
        "INSERT INTO spells(template_id,name,real_name,image,accuracy,school,description,form,rank,x_pips,shadow_pips,fire_pips,ice_pips,storm_pips,myth_pips,life_pips,death_pips,balance_pips) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        spells
    )

    cursor.executemany(
        """INSERT INTO effects (spell, kind, a, b, c, d, e, f, g, h, i, j, k, l, m, n, o, p, q, r, s, t, u, v, w, x, y, z) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        effects
    )

    cursor.executemany(
        """INSERT INTO effects (spell, kind, a, b, c, d, e, f, g, h, i, j, k, l, m, n, o, p, q, r, s, t, u, v, w, x, y, z) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        damages
    )

    cursor.executemany(
        """INSERT INTO effects (spell, kind, a, b, c, d, e, f, g, h, i, j, k, l, m, n, o, p, q, r, s, t, u, v, w, x, y, z) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        rounds
    )
    


def insert_set_bonuses(cursor, cache: SetBonusCache):
    set_bonuses = []
    set_stats = []

    for template, bonus in cache.cache.items():
        set_bonuses.append((template, bonus.name.id))
        for bonus in bonus.bonuses:
            for stat in bonus.stats:
                set_stats.append((template, bonus.activate_count, *convert_stat(stat)))

    cursor.executemany(
        "INSERT INTO set_bonuses (id,name) VALUES (?,?)",
        set_bonuses
    )
    cursor.executemany(
        """INSERT INTO set_stats (bonus_set,activate_count,kind,a,b) VALUES (?,?,?,?,?)""",
        set_stats
    )


def insert_items(cursor, items):
    values = []
    talents = []
    stats = []

    for item in items:
        values.append((
            item.template_id,
            item.name.id,
            item.set_bonus_id,
            item.rarity,
            item.jewel_sockets.value,
            item.adjectives & 0xFFFF,
            item.adjectives >> 16,
            *convert_equip_reqs(item.equip_reqs),
            item.min_pet_level,
            item.max_spells,
            item.max_copies,
            item.max_school_copies,
            item.deck_school,
            item.max_tcs,
            item.archmastery_points,
        ))

        if item.min_pet_level != 0:
            for talent in item.pet_talents:
                talents.append((item.template_id, talent.name.id))

        for stat in item.stats:
            stats.append((item.template_id, *convert_stat(stat)))

    cursor.executemany(
        "INSERT INTO items(id,name,bonus_set,rarity,jewels,kind,extra_flags,equip_school,equip_level,min_pet_level,max_spells,max_copies,max_school_copies,deck_school,max_tcs,archmastery_points) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        values
    )
    cursor.executemany(
        """INSERT INTO item_stats(item,kind,a,b) VALUES (?,?,?,?)""",
        stats
    )
    cursor.executemany("INSERT INTO pet_talents (item,name) VALUES (?,?)", talents)

def insert_mobs(cursor, mobs):
    values = []
    stats = []

    for mob in mobs:
        values.append((
            mob.template_id,
            mob.name.id,
            mob.is_boss,
            mob.rank,
            mob.hitpoints,
            mob.primarySchool,
            mob.secondarySchool,
            mob.is_shadow,
            mob.intelligence,
            mob.selfishFactor,
            mob.aggressiveFactor
        ))

        for stat in mob.stats:
            stats.append((mob.template_id, *convert_stat(stat)))

    cursor.executemany(
        "INSERT INTO mobs(id,name,is_boss,rank,hp,primary_school,secondary_school,is_shadow,intelligence,selfishness,aggressiveness) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        values
    )
    cursor.executemany(
        """INSERT INTO mob_stats(mob,kind,a,b) VALUES (?,?,?,?)""",
        stats
    )

