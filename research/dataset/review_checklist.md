# RhymeTextVQA human review checklist

Use this before marking `qa_pairs.reviewed = 1`.

## Page image
- [ ] Title matches the rhyme
- [ ] Verse lines are readable and in order
- [ ] Illustration markers match intended objects (monkey, tree, etc.)

## OCR tokens
- [ ] Every visible word has a box
- [ ] Boxes do not cover the wrong word
- [ ] Punctuation stripping did not break answerability

## Objects
- [ ] Labels are child-friendly (`monkey`, not obscure synonyms)
- [ ] `relation_hint` matches the rhyme meaning (e.g. monkey on bed/tree)
- [ ] Boxes roughly cover the drawn marker

## QA pairs
- [ ] Question is understandable by a child (age ~5–8)
- [ ] All 10 answer strings agree on the canonical answer
- [ ] `answer_type` is correct: `text` / `object` / `relation`
- [ ] Answer appears in OCR text, object labels, or relation hints

## License
- [ ] Rhyme text is public domain
- [ ] Page art is project-synthesized or explicitly licensed
