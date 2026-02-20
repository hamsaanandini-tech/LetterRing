import random
import re
from typing import List, Set

import streamlit as st
from wordfreq import top_n_list
import streamlit.components.v1 as components

SEEDS = [
    "RAINBOW", "SILENCE", "CAPTURE", "NETWORK", "ORCHARD",
    "TREASON", "BALANCE", "HARMONY", "LIBRARY", "MOUNTAIN",
    "FANTASY", "TRIANGLE", "NOTEBOOK", "FIREPLACE", "SUNLIGHT",
    "PAINTER", "CARTOON", "MIRACLE", "FOREIGN", "GLACIER",
    "WHISPER", "JOURNAL", "KITCHEN", "MONSTER", "PICTURE",
    "ROCKETS", "SCARLET", "THEATER", "VICTORY", "WEALTHY",
    "ADVENTURE", "BRILLIANT", "CREATION", "DISCOVER", "ELEGANCE",
    "FREEDOM", "GARDENS", "HORIZON", "IMAGINE", "JUNCTION",
    "KINGDOMS", "LANGUAGE", "MOMENTS", "NATURAL", "PASSION",
    "QUANTUM", "RESCUE", "SEASONS", "THOUGHT", "WONDER"
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
        show_pangram=False,
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

    st.markdown("""
    <style>
    /* Dark theme: black background, white text */
    html, body, .stApp {
      background: #000000 !important;
      color: #ffffff !important;
    }

    /* Default letter/button appearance: dark surface with white text */
    .stButton>button {
      background: linear-gradient(180deg, #111827, #0b1220) !important;
      color: #ffffff;
      border: 1px solid rgba(255,255,255,0.04) !important;
      box-shadow: 0 8px 20px rgba(0,0,0,0.6) !important;
      border-radius: 12px !important;
      min-width: 64px !important;
      height: 64px !important;
      font-size: 22px !important;
      padding: 0 12px !important;
    }

    /* Make primary letter buttons larger and circular via class applied below */
    .letter-btn {
      width: 84px !important;
      height: 84px !important;
      border-radius: 50% !important;
      font-size: 28px !important;
      padding: 0 !important;
    }
    .letter-center-btn {
      width: 110px !important;
      height: 110px !important;
      font-size: 36px !important;
      border-radius: 50% !important;
    }

    /* Mandatory center letter: ensure button and its contents are red and bold */
    .letter-center, .letter-center a { color: #ff3b30 !important; font-weight: 900 !important; }
    .letter-center-btn, .letter-center-btn * { color: #ff3b30 !important; font-weight: 900 !important; }
    .letter-center-btn { background: linear-gradient(180deg, #fff6ea, #ffd89b) !important; border-color: rgba(255,59,48,0.12) !important; }

    /* Dark translucent UI container for contrast */
    .block-container { background: rgba(0,0,0,0.6) !important; }
    </style>
    """, unsafe_allow_html=True)


    # Use native Streamlit buttons for letters (avoids full-page navigation)

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

    # Render letters as native Streamlit buttons in columns so clicks are handled server-side
    cols = st.columns(len(display))
    for i, L in enumerate(display):
        with cols[i]:
            btn_key = f"letter_{i}"
            clicked = st.button(L, key=btn_key, on_click=append_letter, args=(L,))

    # Single client-side script to style letter buttons (make them circular) and
    # mark the mandatory center letter red & bold.
    components.html(
        f"""
        <script>
        (function(){{
          const mandatory = "{mandatory}";
          function styleLetters() {{
            const buttons = Array.from(document.querySelectorAll('button'));
            for (const b of buttons) {{
              const txt = (b.textContent || '').trim();
              // consider as letter button if text is a single uppercase letter A-Z
              if (/^[A-Z]$/.test(txt)) {{
                b.classList.add('letter-btn');
                // ensure shape/size
                b.style.width = '84px';
                b.style.height = '84px';
                b.style.borderRadius = '50%';
                b.style.fontSize = '28px';
                b.style.padding = '0';
                b.style.lineHeight = '84px';
                if (txt === mandatory) {{
                  b.classList.add('letter-center-btn');
                  b.style.color = '#ff3b30';
                  b.style.fontWeight = '900';
                  // also try to color inner elements
                  try {{ const inner = b.querySelector('*'); if (inner) {{ inner.style.color = '#ff3b30'; inner.style.fontWeight='900'; }} }} catch(e){{}}
                }} else {{
                  b.style.color = '#ffffff';
                  try {{ const inner = b.querySelector('*'); if (inner) {{ inner.style.color = '#ffffff'; }} }} catch(e){{}}
                }}
              }}
            }}
          }}
          styleLetters();
          const mo = new MutationObserver(styleLetters);
          mo.observe(document.body, {{ childList: true, subtree: true }});
          // run a few times to handle late renders
          let runs = 0;
          const iv = setInterval(function(){{ styleLetters(); runs++; if (runs>20) clearInterval(iv); }}, 150);
        }})();
        </script>
        """,
        height=0,
    )

    # Extra script: ensure the mandatory (center) letter is styled red by directly setting inline styles
    components.html(
        """
        <script>
        (function(){
          const centerLabel = `%s`;
          function styleCenter(){
            const buttons = Array.from(document.querySelectorAll('button'));
            for (const b of buttons){
              try {
                const aria = (b.getAttribute('aria-label') || '').toLowerCase();
                const text = (b.textContent || '').trim();
                // match by exact text, inclusion, or aria-label containing the center label
                if (text === centerLabel || text.includes(centerLabel) || aria.includes(centerLabel.toLowerCase())) {
                  b.style.color = '#ff3b30';
                  b.style.fontWeight = '900';
                  b.style.borderColor = '#ff3b30';
                  const inner = b.querySelector('*');
                  if (inner) { inner.style.color = '#ff3b30'; inner.style.fontWeight = '900'; }
                  return;
                }
              } catch(e){}
            }
          }
          styleCenter();
          const mo = new MutationObserver(styleCenter);
          mo.observe(document.body, { childList: true, subtree: true });
          setInterval(styleCenter, 250);
        })();
        </script>
        """ % (mandatory),
        height=0,
    )

    # Visible mandatory letter indicator (always red and bold)
    st.markdown(
        f"<div style='text-align:center; margin-top:8px; font-size:22px; font-weight:900; color:#ff3b30'>Mandatory letter: {mandatory}</div>",
        unsafe_allow_html=True,
    )

    # New Game button
    if st.button("New Game"):
        start_new_game()

    st.markdown("Enter guesses below (minimum length 3, must include the highlighted letter).")
    st.text_input("Your guess", key="guess_input", placeholder="Type a word and press Submit")
    st.button("Submit", on_click=handle_submit)

    # Make the "Submit" and "New Game" buttons' text red and bold via small DOM script.
    components.html(
        """
        <script>
        (function(){
          const CSS = `.lr-red-btn { color: #ff3b30 !important; font-weight: 800 !important; border-color: #ff3b30 !important; }`;
          const style = document.createElement('style');
          style.appendChild(document.createTextNode(CSS));
          document.head.appendChild(style);

          function markButtons(){
            document.querySelectorAll('button').forEach(function(b){
              const text = (b.textContent || '').trim().toLowerCase();
              if (text.includes('submit') || text.includes('new game')) {
                b.classList.add('lr-red-btn');
              }
            });
          }

          // run periodically to catch Streamlit re-renders
          markButtons();
          const mo = new MutationObserver(markButtons);
          mo.observe(document.body, { childList: true, subtree: true });
          // also run on interval briefly to be safe
          let runs = 0;
          const iv = setInterval(function(){
            markButtons();
            runs += 1;
            if (runs > 20) { clearInterval(iv); }
          }, 200);
        })();
        </script>
        """,
        height=0,
    )

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

    # Button to reveal pangrams (words that use all 7 letters)
    if st.button("Show Pangrams"):
        st.session_state["show_pangram"] = True

    if st.session_state.get("show_pangram"):
        all_pangrams = [w for w in st.session_state.get("valid_words", []) if is_pangram(w, letters_set)]
        if all_pangrams:
            st.success(f"Pangrams ({len(all_pangrams)}): {', '.join(all_pangrams)}")
        else:
            st.info("No pangrams available for this letter set.")


if __name__ == "__main__":
    main()

