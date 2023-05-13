import sqlite3

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
    id           integer not null primary key,
    template_id  integer not null,
    name         integer not null,
    image        text,
    accuracy     integer,
    school       integer,
    description  integer,

    rank         integer,
    life_pips    integer,
    x_pips       integer,
    fire_pips    integer,
    myth_pips    integer,
    balance_pips integer,
    ice_pips     integer,
    storm_pips   integer,
    shadow_pips  integer,
    death_pips   integer,

    foreign key(name)        references locale_en(id)
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


def build_db(state, items, out):
    mem = sqlite3.connect(":memory:")
    cursor = mem.cursor()

    initialize(cursor)
    insert_locale_data(cursor, state.cache)
    insert_spell_data(cursor, state.spells)
    insert_set_bonuses(cursor, state.bonuses)
    insert_items(cursor, items)
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


def insert_spell_data(cursor, cache: SpellCache):
    spells = []
    for template, spell in cache.cache.items():
        spells.append((
            template,
            spell.name.id,
            spell.image,
            spell.accuracy,
            spell.school,
            spell.description.id,
            spell.rank,
            spell.life_pips,
            spell.x_pips,
            spell.fire_pips,
            spell.myth_pips,
            spell.balance_pips,
            spell.ice_pips,
            spell.storm_pips,
            spell.shadow_pips,
            spell.death_pips,
        ))

    cursor.executemany(
        "INSERT INTO spells(template_id,name,image,accuracy,school,description,rank,life_pips,x_pips,fire_pips,myth_pips,balance_pips,ice_pips,storm_pips,shadow_pips,death_pips) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        spells
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
