# Tabletop Gamers

A desktop application for the Tabletop Gamers club, built with PyQt6 following an
MVC architecture:

- **Model** — `datastore.py` (SQLite access via `TableTopGamers.db`)
- **Controller** — `controller.py` (business logic, validation, authentication)
- **View** — `main_window.ui` / `ui_main_window.py` (generated) / `main_window.py`

## Setup

```
python -m venv .venv
pip install -r requirements.txt
```

## Running the app

```
main.py
```

### Test login credentials

| Role   | Email                  | Password  |
|--------|-------------------------|-----------|
| Admin  | `admin@gmail.com`       | `testing` |
| Member | `jkaczmarek@gmail.com`  | `sadjfhkl`|

Admin accounts see the extra **Manage Games**, **Manage Members** and **Manage
Fees** tabs; regular members only see **Browse & Search**, **My Loans** and **My
Fees**. Passwords are stored as salted hashes; any legacy plaintext password is
upgraded transparently to a hash the first time that member logs in
successfully.

## Testing procedure

Automated tests focus on `Datastore` (the Model), using a `pytest` fixture that
copies `TableTopGamers.db` to a temporary file first, so running the tests
never modifies the real club data.

1. **Model tests** — correctness tests for every method on `Datastore`. A
   markdown summary (pass/fail per test) is written to
   `test_results/test_results.md` via `conftest.py`, alongside the normal
   console output:

   ```
   python -m pytest test_datastore.py -v
   ```

2. **Performance benchmark** — timed run of every `Datastore` method, printed
   as a `rich` table and also written to
   `test_results/benchmark_results.md` (kept out of normal `pytest` runs
   since it deliberately exercises each method against fresh copies of the
   database):

   ```
   python test_datastore.py --benchmark
   ```

   Both files in `test_results/` are regenerated on every run, so they
   always reflect the latest results.

3. **Manual/UI verification** — launch the app (see above), log in with the
   credentials above, and exercise the golden path: browse/search/filter the
   catalogue, borrow and return a game, and (as admin) add/remove a game,
   register a member, run an annual fee cycle and record a fee payment. This
   is also how `Controller` (the business logic layer) gets exercised, since
   it has no dedicated automated test suite.

### Regenerating the UI

If `main_window.ui` is edited, regenerate `ui_main_window.py` (do not edit that
file by hand):

```
.venv\Scripts\pyuic6.exe main_window.ui -o ui_main_window.py
```
