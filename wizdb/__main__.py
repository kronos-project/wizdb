from pathlib import Path
import sqlite3

from kobold_py import KoboldError
from kobold_py import op as kobold

from .db import build_db
from .item import Item, is_item_template
from .state import State

ROOT = Path(__file__).parent.parent

ITEMS_DB = ROOT / "items.db"
ROOT_WAD = ROOT / "Root"
TYPES = ROOT / "types.json"
LOCALE = ROOT_WAD / "Locale" / "English"
STAT_EFFECTS = ROOT_WAD / "GameEffectData" / "CanonicalStatEffects.xml"
STAT_RULES = ROOT_WAD / "GameEffectRuleData"


def read_item_template(de: kobold.BinaryDeserializer, file: Path) -> dict:
    try:
        obj = de.deserialize(file.read_bytes())
    except KoboldError:
        return None

    if not is_item_template(obj):
        return None

    return obj


def deserialize_items(state: State):
    res = []
    for file in (ROOT_WAD / "ObjectData").glob("**/*.xml"):
        if obj := read_item_template(state.de, file):
            item = Item(state, obj)
            res.append(item)
    return res


def main():
    state = State(ROOT_WAD, TYPES)
    items = deserialize_items(state)

    if ITEMS_DB.exists():
        ITEMS_DB.unlink()

    db = sqlite3.connect(str(ITEMS_DB))
    build_db(state, items, db)
    db.close()

    print(f"Success! Database written to {ITEMS_DB.absolute()}")


if __name__ == "__main__":
    main()
