# en-patterns — English AI-flavor patterns (six groups)

Source spine: Wikipedia "Signs of AI writing" (via humanizer) + stop-slop structural taxonomy.
Density principle applies throughout: look for clusters, not isolated tokens. ⚙ = mechanically caught by `scripts/shuo_renhua check`.

## 1. Content inflation

- **Significance inflation**: stands as a testament / pivotal moment / underscores its importance / reflects broader trends / setting the stage for → state what happened, cut the halo.
- **Notability name-dropping**: cited in NYT, BBC, FT… / active social media presence → one concrete sourced claim beats a list.
- **Superficial -ing analyses**: …, highlighting / showcasing / reflecting the deep connection → cut the participle tail or make the claim with an actor and a source.
- **Promotional register**: nestled / vibrant / breathtaking / must-visit / rich cultural heritage → plain factual description.
- **Weasel attributions**: Experts argue / Observers have cited / Industry reports suggest → name the source or own the judgment.
- **Formulaic "Challenges and Future Prospects"**: Despite these challenges… continues to thrive → concrete difficulties, concrete plans.

## 2. Vocabulary

- **⚙AI-word clusters** (≥3 distinct co-occurring): delve, tapestry, testament, underscore, vibrant, pivotal, crucial, foster, showcase, intricate, landscape (abstract), boasts, nestled, groundbreaking, seamless, leverage, elevate. One is nothing; a cluster is a confession.
- **Copula avoidance**: serves as / stands as / functions as / boasts → just write "is/has".
- **Elegant variation**: protagonist → main character → central figure → hero within one paragraph → pick one term, use pronouns.
- **False ranges**: "from the Big Bang to the cosmic web, from stars to dark matter" when X and Y share no scale → list the topics plainly.
- **Hyphenated-pair uniformity**: keep attributive hyphens (a high-quality report), drop them in predicate position (the report is high quality).

## 3. Sentence shells & rhetoric (stop-slop's structural layer)

- **⚙Negative parallelism**: It's not just X, it's Y / Not because X. Because Y. — telegraphed reversal; say the claim directly.
- **Negative listing** ("a rhetorical striptease"): It's not A. It's not B. It's C. → state C.
- **Rule-of-three reflex**: forced triads everywhere → two items, or one with a concrete example.
- **Dramatic fragmentation**: "[Noun]. That's it. That's the product." / staccato runs of clipped fragments → one short sentence lands a point; a run of them is engineered drama.
- **Aphorism formulas**: X is the language/currency/architecture of Y / X becomes a trap → replace with the concrete claim it gestures at.
- **False agency** (distinctive, from stop-slop): "the data tells us / the decision emerges / a complaint becomes a fix" — data sits there; someone reads it, someone decides, someone fixed it. **Name the human.**
- **Narrator-from-a-distance**: "Nobody designed this" → pull the reader in: "You don't sit down one day and decide to…".
- **Wh-cleft starters**: What makes this hard is… / What really matters is… → "The constraint is…".
- **Persuasive authority tropes**: The real question is / at its core / fundamentally → the sentence after usually restates an ordinary point with ceremony; cut the ceremony.
- **Fake-candid openers**: Honestly? / Look, / Here's the thing — theatrical pause-and-reveal before a routine claim. A person being honest just says the thing. ("Honestly" mid-sentence is fine.)

## 4. Assistant residue (all registers)

- **⚙Chat artifacts**: I hope this helps! / Would you like me to… / Let me know if… / Certainly! → cut; content is not correspondence.
- **⚙Cutoff disclaimers & gap-filling**: As of my last update / details are scarce, she likely… / maintains a low profile → say what isn't known or cut; never dress a guess as fact.
- **Sycophancy**: Great question! You're absolutely right! → respond with substance.
- **Generic upbeat closers**: The future looks bright / Exciting times lie ahead → end on a plan, fact, or consequence.
- **⚙Signposting**: Let's dive in / Without further ado / Here's what you need to know → do the thing instead of announcing it. Any "here's what/this/that" opener is throat-clearing.

## 5. Style & formatting

- **⚙Em/en dashes**: in English visible copy treat as a near-binary tell — replace with period / comma / colon / parentheses / restructure (order of preference). Scan the final draft for `—`/`–`; hits mean it isn't done. (Register exception: if the user's own voice sample uses them deliberately, follow the sample.)
- **Boldface mechanics**: bolding every key phrase → ≤3 bolds per piece, only load-bearing.
- **Inline-header bullet lists**: `- **Performance:** Performance has been…` → fold into prose or use real headings.
- **Title Case Headings** → sentence case.
- **⚙Emoji decoration**: 🚀💡✅ on headings/bullets → remove unless the register is genuinely playful.
- **Fragmented headers**: heading + one-line restatement of the heading → delete the warm-up line.
- **Diff-anchored writing**: docs narrating the change ("this replaces the previous approach") instead of describing the thing as it is → describe as-is, unless it's a changelog.

## 6. Filler & hedging

- **Filler phrases**: in order to → to; due to the fact that → because; at this point in time → now; it is important to note that → (delete).
- **Hedging stacks**: could potentially possibly → may. One qualifier per claim.
- **Adverb pruning** (heuristic, not a ban): -ly intensifiers (really, truly, significantly) usually add nothing — cut when the sentence survives without them.

## What NOT to flag (false positives — from humanizer, keep intact)

Perfect grammar; formal vocabulary in general (AI overuses *specific* words, not all fancy words); one *however*/*additionally* in isolation; curly quotes alone (editors auto-curl); em dashes alone in a writer who uses them consistently; a single short emphatic sentence; "honestly/look" mid-sentence; unsourced claims (most of the web is unsourced); letter-style salutations; clean formatting; quoted/discussed phrases (mention, not use). **Clusters convict; tokens don't.**

## Signs of human writing (preserve, do not over-edit)

Hard-to-fabricate specifics (a weird quote, "the lawyer upstairs from my dentist"); mixed feelings left unresolved; era-bound slang and dated references; defensible first-person choices; varied sentence lengths; genuine self-interruptions and parentheticals ("(I keep wanting to say 'almost' here…)"); anything written before Nov 30, 2022.
