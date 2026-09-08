# Gemstone Notation

A self-contained notation system for gemstones and for the colour code
of a finished jewellery product. The module carries its own referential
— stones, grades, hues and shapes, each with a short code and a name —
and the grammar that turns a stone's components into a compact token and
back. It depends on `base` only: it installs on a bare Odoo, carries no
company data, and knows nothing about any particular product database
(bridge modules provide that wiring separately).

## 1. What a stone token looks like

A token describes one stone in four blocks, three of them optional:

```
PP [G] [BB] [EE]
```

| Block | Width | Character class | Meaning |
|-------|-------|-----------------|---------|
| `PP`  | 2     | letters          | stone identity |
| `G`   | 1     | digit            | quality grade |
| `BB`  | 2     | digit **then** letter | hue |
| `EE`  | 2     | letters          | cutting shape |

Examples (with an illustrative dictionary):

| Token   | Reading |
|---------|---------|
| `SA`    | sapphire, everything default |
| `SA2`   | sapphire, grade 2 |
| `SA1C`  | sapphire, hue 1C (Ceylon) |
| `SA21C` | sapphire, grade 2, hue 1C |
| `SAPS`  | sapphire, pear shape |
| `SA21CPS` | sapphire, grade 2, hue Ceylon, pear |

## 2. Why no separators are needed

The widths and character classes were chosen so that at most one way of
splitting the part after `PP` is structurally valid:

- a **lone digit** can only be a grade;
- a **digit followed by a letter** can only start a hue;
- **letters** can only be a shape (always exactly two of them).

Formally, the parser enumerates the eight combinations of block widths
(grade 0/1, hue 0/2, shape 0/2), keeps those whose widths sum to the
remaining length **and** whose characters match each block's class, and
accepts the token only when exactly one combination survives. A short
case analysis shows two combinations can never both survive: a grade and
a hue differ on their second character's class, a hue and a shape differ
on their first, and the remaining-length arithmetic separates
grade+shape (3 characters) from hue alone (2) or hue+shape (4).

## 3. Defaults keep codes short

Each stone in the dictionary declares a **default grade, default hue and
default shape**. A block equal to the stone's default is omitted from
the token, so the most frequent stones write in two characters. The
defaults are not arbitrary: they are determined from **occurrence counts
in the actual stone history** — the shade and shape most often used with
a stone become its defaults, so omission removes exactly the information
the reader would assume anyway.

## 4. Colour-bearing identities and the double-colour rule

Some commercial identities carry a colour in their name (a *Blue Topaz*
is an article of its own, not "a topaz that happens to be blue"). Such a
stone declares an **implied hue**. Two consequences:

- its tokens never write that hue (it is implied by the identity);
- writing a *different* hue on it is refused as a **double colour** —
  the same information cannot live on two axes at once.

## 5. The colour code of a product

A product's colour code joins the distinct tokens of its stones with
`+`, in a fixed, deterministic order:

1. the **center stone** first, when one is flagged;
2. the remaining stones by **heaviest single stone, descending** — the
   weight compared is the largest individual stone of that token, not a
   sum;
3. ties broken by token, ascending.

A stone type appearing on several lines is written once. Example:
`SA21CPS+BL+DI` — a pear Ceylon sapphire in the center, then a blue
topaz, then diamonds.

## 6. The dictionaries

| Model | Content |
|-------|---------|
| `gem.notation.stone` | identity code + name, implied hue, the three defaults |
| `gem.notation.grade` | grade code (digit) + name |
| `gem.notation.hue`   | hue code (digit+letter) + name |
| `gem.notation.shape` | shape code (2 letters) + name |

All codes are validated against their character class, and each
dictionary is editable in place (menu **Notation**).

## 7. Services and the wizard

The `gem.notation` abstract model exposes the logic to any caller:

- `parse_token(token)` — token to dictionary records, with a list of
  problems (unknown codes, structural errors, double colour);
- `build_token(stone, grade, hue, shape)` — records to token, defaults
  omitted;
- `order_tokens(entries)` / `transcribe(components)` — the product
  colour code from (token, weight, is_center) entries or from component
  dicts;
- `lookup(text)` — name or code to entries, both directions, all axes.

The **Transcribe & Verify** wizard (menu Notation) exposes them
interactively: *Compose* (pick components, the code answers live and
says which blocks were omitted as defaults), *Read* (type a code, get
its components), *Look up* (search by name or code).

## 8. Extending

The core never reads company data. A bridge module can link the
dictionaries to an existing stone catalogue (add relational fields via
`_inherit`), map that catalogue's own colour vocabulary onto grades and
hues, extend the wizard with new modes (`selection_add`), and tighten
the access rules — the core ships read-for-internal-users /
full-for-admins so it works out of the box.
