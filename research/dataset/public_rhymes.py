"""Bundled public-domain nursery rhymes (Mother Goose tradition).

Texts are long out of copyright. Illustrations in this pipeline are
procedurally drawn (not third-party images), so pages remain redistributable.
"""

from __future__ import annotations

from typing import Any

SOURCE_NAME = "Public-domain Mother Goose nursery rhymes"
SOURCE_URL = "https://www.gutenberg.org/ebooks/search/?query=mother+goose"
LICENSE_NAME = "Public Domain"
LICENSE_URL = "https://creativecommons.org/publicdomain/mark/1.0/"
LICENSE_NOTES = (
    "Classic nursery rhyme wording is public domain. "
    "Page images in this project are synthesized locally."
)

# Each rhyme: id, title, lines, objects for illustration seed labels.
PUBLIC_RHYMES: list[dict[str, Any]] = [
    {
        "rhyme_id": "humpty_dumpty",
        "title": "Humpty Dumpty",
        "lines": [
            "Humpty Dumpty sat on a wall,",
            "Humpty Dumpty had a great fall.",
            "All the king's horses and all the king's men",
            "Couldn't put Humpty together again.",
        ],
        "objects": [
            {"label": "egg", "category": "character", "relation_hint": "on wall"},
            {"label": "wall", "category": "place", "relation_hint": "under egg"},
        ],
    },
    {
        "rhyme_id": "jack_and_jill",
        "title": "Jack and Jill",
        "lines": [
            "Jack and Jill went up the hill",
            "To fetch a pail of water.",
            "Jack fell down and broke his crown,",
            "And Jill came tumbling after.",
        ],
        "objects": [
            {"label": "boy", "category": "character", "relation_hint": "on hill"},
            {"label": "girl", "category": "character", "relation_hint": "on hill"},
            {"label": "pail", "category": "object", "relation_hint": "with water"},
            {"label": "hill", "category": "place", "relation_hint": None},
        ],
    },
    {
        "rhyme_id": "twinkle_twinkle",
        "title": "Twinkle Twinkle Little Star",
        "lines": [
            "Twinkle, twinkle, little star,",
            "How I wonder what you are!",
            "Up above the world so high,",
            "Like a diamond in the sky.",
        ],
        "objects": [
            {"label": "star", "category": "sky", "relation_hint": "above world"},
            {"label": "sky", "category": "place", "relation_hint": "contains star"},
        ],
    },
    {
        "rhyme_id": "baa_baa_black_sheep",
        "title": "Baa Baa Black Sheep",
        "lines": [
            "Baa, baa, black sheep,",
            "Have you any wool?",
            "Yes sir, yes sir,",
            "Three bags full.",
        ],
        "objects": [
            {"label": "sheep", "category": "animal", "relation_hint": "has wool"},
            {"label": "bag", "category": "object", "relation_hint": "holds wool"},
        ],
    },
    {
        "rhyme_id": "mary_had_a_little_lamb",
        "title": "Mary Had a Little Lamb",
        "lines": [
            "Mary had a little lamb,",
            "Its fleece was white as snow;",
            "And everywhere that Mary went,",
            "The lamb was sure to go.",
        ],
        "objects": [
            {"label": "girl", "category": "character", "relation_hint": "with lamb"},
            {"label": "lamb", "category": "animal", "relation_hint": "follows girl"},
        ],
    },
    {
        "rhyme_id": "hey_diddle_diddle",
        "title": "Hey Diddle Diddle",
        "lines": [
            "Hey diddle diddle,",
            "The cat and the fiddle,",
            "The cow jumped over the moon;",
            "The little dog laughed to see such sport,",
            "And the dish ran away with the spoon.",
        ],
        "objects": [
            {"label": "cat", "category": "animal", "relation_hint": "with fiddle"},
            {"label": "cow", "category": "animal", "relation_hint": "over moon"},
            {"label": "moon", "category": "sky", "relation_hint": "under cow"},
            {"label": "dog", "category": "animal", "relation_hint": "laughing"},
            {"label": "dish", "category": "object", "relation_hint": "with spoon"},
        ],
    },
    {
        "rhyme_id": "itsy_bitsy_spider",
        "title": "Itsy Bitsy Spider",
        "lines": [
            "The itsy bitsy spider",
            "Climbed up the waterspout.",
            "Down came the rain",
            "And washed the spider out.",
        ],
        "objects": [
            {"label": "spider", "category": "animal", "relation_hint": "on waterspout"},
            {"label": "waterspout", "category": "place", "relation_hint": "under spider"},
            {"label": "rain", "category": "weather", "relation_hint": "falls down"},
        ],
    },
    {
        "rhyme_id": "row_your_boat",
        "title": "Row Row Row Your Boat",
        "lines": [
            "Row, row, row your boat,",
            "Gently down the stream.",
            "Merrily, merrily, merrily, merrily,",
            "Life is but a dream.",
        ],
        "objects": [
            {"label": "boat", "category": "object", "relation_hint": "on stream"},
            {"label": "stream", "category": "place", "relation_hint": "under boat"},
        ],
    },
    {
        "rhyme_id": "hickory_dickory_dock",
        "title": "Hickory Dickory Dock",
        "lines": [
            "Hickory dickory dock,",
            "The mouse ran up the clock.",
            "The clock struck one,",
            "The mouse ran down,",
            "Hickory dickory dock.",
        ],
        "objects": [
            {"label": "mouse", "category": "animal", "relation_hint": "on clock"},
            {"label": "clock", "category": "object", "relation_hint": "under mouse"},
        ],
    },
    {
        "rhyme_id": "little_miss_muffet",
        "title": "Little Miss Muffet",
        "lines": [
            "Little Miss Muffet sat on a tuffet,",
            "Eating her curds and whey;",
            "Along came a spider",
            "Who sat down beside her",
            "And frightened Miss Muffet away.",
        ],
        "objects": [
            {"label": "girl", "category": "character", "relation_hint": "on tuffet"},
            {"label": "spider", "category": "animal", "relation_hint": "beside girl"},
            {"label": "bowl", "category": "object", "relation_hint": "with food"},
        ],
    },
    {
        "rhyme_id": "old_macdonald",
        "title": "Old MacDonald Had a Farm",
        "lines": [
            "Old MacDonald had a farm,",
            "E-I-E-I-O.",
            "And on that farm he had a cow,",
            "E-I-E-I-O.",
        ],
        "objects": [
            {"label": "farmer", "category": "character", "relation_hint": "on farm"},
            {"label": "cow", "category": "animal", "relation_hint": "on farm"},
            {"label": "farm", "category": "place", "relation_hint": None},
        ],
    },
    {
        "rhyme_id": "five_little_monkeys",
        "title": "Five Little Monkeys",
        "lines": [
            "Five little monkeys jumping on the bed,",
            "One fell off and bumped his head.",
            "Mama called the doctor and the doctor said,",
            "No more monkeys jumping on the bed!",
        ],
        "objects": [
            {"label": "monkey", "category": "animal", "relation_hint": "on bed"},
            {"label": "bed", "category": "object", "relation_hint": "under monkey"},
            {"label": "tree", "category": "place", "relation_hint": "near monkey"},
        ],
    },
]


def full_text(rhyme: dict[str, Any]) -> str:
    return "\n".join(rhyme["lines"])
