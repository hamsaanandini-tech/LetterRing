import random
import re
from typing import List, Set

import streamlit as st
from wordfreq import top_n_list
import streamlit.components.v1 as components

SEEDS = [
    "RELATES", "STREAMS", "PAINTER", "DEALERS",
    "TRACING", "SALTIER", "RETINAL", "ENTAILS",
    "SEALANT", "STAINER", "REPAINT", "TANGIER",
    "GRANTED", "TRAINED", "ARTISTS", "TEARING",
    "EARTHLY", "PLANTER", "RATINGS", "INSTEAD"
]

# public applause sound (autoplayed via HTML audio tag)
APPLAUSE_URL = "https://actions.google.com/sounds/v1/people/applause.ogg"


@st.cache_data
def load_wordlist(n: int = 200000) -> List[str]:
    """
    Load a large list of English words from wordfreq.
    Cached to avoid repeated expensive loads.
    """
    return top_n_list("en", n)


def normalize(word: str) -> str:
    return re.sub(r"[^A-Z]", "", word.upper())


def generate_valid_words(letters: Set[str], mandatory: str, wordlist: List[str]) -> List[str]:
    letters_set = set(letters)
    valid = []
    for w in wordlist:
        # wordfreq words are lowercase; normalize to uppercase letters only
        word = normalize(w)
        if len(word) < 3:
            continue
        if mandatory not in word:
            continue
        if set(word) - letters_set:
            continue
        valid.append(word)
    # dedupe and sort
    valid = sorted(set(valid))
    return valid


def start_new_game():
    # pick a seed that yields 7 unique letters when possible
    seed = random.choice(SEEDS)
    attempts = 0
    while len(set(seed)) != 7 and attempts < 50:
        seed = random.choice(SEEDS)
        attempts += 1
    # extract unique letters from the seed preserving order
    letters = list(dict.fromkeys(seed))
    # If we still don't have 7 unique letters (rare), pad with random letters
    if len(letters) != 7:
        import string

        extra = [c for c in string.ascii_uppercase if c not in letters]
        random.shuffle(extra)
        letters.extend(extra[: (7 - len(letters))])
    random.shuffle(letters)  # present letters in a jumbled order
    mandatory = random.choice(letters)
    wordlist = load_wordlist()
    valid = generate_valid_words(set(letters), mandatory, wordlist)
    # also store a fast lookup set of all normalized words from the source wordlist
    wordset = {normalize(w) for w in wordlist}
    st.session_state.update(
        seed=seed,
        letters=letters,
        mandatory=mandatory,
        valid_words=valid,
        wordset=wordset,
        found=[],
        score=0,
        guess_input="",
    )


def append_letter(letter: str):
    st.session_state["guess_input"] = st.session_state.get("guess_input", "") + letter


def handle_submit():
    guess = st.session_state.get("guess_input", "").strip().upper()
    st.session_state["guess_input"] = ""
    if not guess:
        return
    # normalize and validate
    guess_norm = normalize(guess)
    if guess_norm in st.session_state["found"]:
        st.warning(f"Already found: {guess_norm}")
        return
    # validate against source wordset and letter constraints
    if "wordset" not in st.session_state:
        st.error("Word database not loaded.")
        return
    if guess_norm not in st.session_state["wordset"]:
        st.error(f"Not a recognized word: {guess_norm}")
        return
    letters_set = set(st.session_state["letters"])
    if len(guess_norm) < 3 or set(guess_norm) - letters_set or st.session_state["mandatory"] not in guess_norm:
        st.error(f"Not valid: {guess_norm}")
        return
    st.session_state["found"].append(guess_norm)
    # simple scoring: +len(word)
    points = len(guess_norm)
    bonus = 0
    # award extra 10 points if the guess matches the original 7-letter seed
    if "seed" in st.session_state and guess_norm == normalize(st.session_state["seed"]):
        bonus = 10
    st.session_state["score"] += points + bonus
    if bonus:
        st.success(f"Pangram! +{points} +{bonus} bonus points! 🎉")
    else:
        st.success(f"Nice — +{points} points!")
    # every 5th correct word: confetti (balloons) and applause
    count = len(st.session_state["found"])
    if count % 5 == 0:
        # confetti-like effect
        st.balloons()
        # autoplay applause sound
        components.html(f"<audio autoplay><source src='{APPLAUSE_URL}' type='audio/ogg'></audio>", height=10)


def is_pangram(word: str, letters_set: Set[str]) -> bool:
    return set(word) >= letters_set


def main():
    st.set_page_config(page_title="LetterRing", layout="centered")
    # background and container styling
    st.markdown(
        """
        <style>
        html, body, .stApp {
          height: 100%;
          background: radial-gradient(circle at 10% 20%, #fef3c7, rgba(255,255,255,0) 20%),
                      linear-gradient(135deg, #f6d365 0%, #fda085 100%);
          background-attachment: fixed;
        }
        .block-container {
          background: rgba(255,255,255,0.78);
          border-radius: 12px;
          padding: 1.5rem 2rem;
          box-shadow: 0 8px 24px rgba(0,0,0,0.12);
        }
        /* Make Streamlit buttons look more clickable and tactile */
        .stButton>button {
          background: linear-gradient(180deg, #ffffff, #f3f4f6);
          border: 1px solid rgba(15, 23, 42, 0.06);
          color: #0f172a;
          padding: 10px 14px;
          border-radius: 12px;
          cursor: pointer;
          box-shadow: 0 8px 18px rgba(2,6,23,0.08);
          transition: transform 0.12s ease, box-shadow 0.12s ease, background 0.12s ease;
          min-width: 72px;
          height: 52px;
          font-weight: 700;
        }
        .stButton>button:hover {
          transform: translateY(-3px);
          box-shadow: 0 14px 30px rgba(2,6,23,0.12);
        }
        .stButton>button:active {
          transform: translateY(0);
          box-shadow: 0 6px 14px rgba(2,6,23,0.06);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.title("LetterRing")

    # handle letter clicks via query param ?add=X
    params = st.query_params
    if "add" in params:
        letter = params.get("add", [""])[0].upper()
        if letter:
            st.session_state["guess_input"] = st.session_state.get("guess_input", "") + letter
        # clear query params to avoid duplicate appends on reload
        st.experimental_set_query_params(**{})

    if "letters" not in st.session_state:
        start_new_game()

    # The seed word is kept in session state for scoring/validation but not shown to the player.
    letters = st.session_state["letters"]
    mandatory = st.session_state["mandatory"]

    # place mandatory letter in center index; show others around it
    other_letters = [l for l in letters if l != mandatory]
    n = len(letters)
    mid = n // 2
    display = []
    other_iter = iter(other_letters)
    for i in range(n):
        if i == mid:
            display.append(mandatory)
        else:
            display.append(next(other_iter))

    # render clickable letter circles (each is an anchor linking to ?add=LETTER)
    css = """
    <style>
    .letter-circle {
      display:inline-block;
      width:84px;
      height:84px;
      line-height:84px;
      border-radius:50%;
      text-align:center;
      font-weight:800;
      font-size:28px;
      color:#111827;
      background: #ffffff;
      box-shadow: 0 10px 24px rgba(2,6,23,0.08);
      margin: 6px;
      text-decoration:none;
      transition: transform 0.12s ease, box-shadow 0.12s ease;
    }
    .letter-circle:hover { transform: translateY(-6px); box-shadow: 0 20px 40px rgba(2,6,23,0.12); }
    .letter-center { background: radial-gradient(circle at 30% 30%, #fff6ea, #ffd89b); color:#b91c1c !important; width:110px; height:110px; line-height:110px; font-size:36px; box-shadow: 0 18px 42px rgba(2,6,23,0.14); }
    .letters-row { display:flex; align-items:center; justify-content:center; gap:8px; flex-wrap:nowrap; }
    </style>
    """
    parts = [css, "<div class='letters-row'>"]
    for L in display:
        cls = "letter-circle letter-center" if L == mandatory else "letter-circle"
        if L == mandatory:
            parts.append(f"<a class='{cls}' href='?add={L}' style='color:#b91c1c !important'>{L}</a>")
        else:
            parts.append(f"<a class='{cls}' href='?add={L}'>{L}</a>")
    parts.append("</div>")
    st.markdown("".join(parts), unsafe_allow_html=True)

    # New Game button
    if st.button("New Game"):
        start_new_game()

    st.markdown("Enter guesses below (minimum length 3, must include the highlighted letter).")
    st.text_input("Your guess", key="guess_input", placeholder="Type a word and press Submit")
    st.button("Submit", on_click=handle_submit)

    st.divider()
    found = st.session_state.get("found", [])
    score = st.session_state.get("score", 0)
    st.metric("Score", score)
    st.write(f"Words found: {len(found)}")

    # show pangram if any found
    letters_set = set(st.session_state["letters"])
    pangrams = [w for w in found if is_pangram(w, letters_set)]
    if pangrams:
        st.success(f"Pangram found: {', '.join(pangrams)} 🎉")

    st.expander("Found words").write(sorted(found))

    with st.expander("Show all valid words"):
        st.write(f"Total possible: {len(st.session_state['valid_words'])}")
        st.write(st.session_state["valid_words"])


if __name__ == "__main__":
    main()

