# Datastore API

`datastore.py` is the Model in this program's MVC architecture. The only
consumer of `Datastore` is `Controller` (`controller.py`) — the View
(`main_window.py`) never imports `datastore.py` or calls SQL directly, it only
calls `Controller` methods, which validate input, translate any `sqlite3`
error into a friendlier `ControllerError`, and combine multiple `Datastore`
calls where needed (for example, `Controller.browse_catalogue()` filters the
result of `get_catalogue()` in Python, since the individual `get_games_*`
filters below each start from the full catalogue independently and cannot be
composed).

Every write method (`add_*`, `update_*`, `delete_game`) commits immediately
and raises the underlying `sqlite3` exception on failure — there is no
built-in validation or duplicate guard, so callers (in practice, `Controller`)
are responsible for checking preconditions first.

### `Datastore(db_file="TableTopGamers.db")`

Opens a connection to the given SQLite file, kept open for the object's
lifetime (closed in `__del__`). `Controller` accepts the same `db_file`
parameter and passes it straight through, which is how `test_datastore.py`
points at a temporary copy of the database instead of the live club data.

## Get Methods

### `get_catalogue()`

Returns details for all games, including each game's current loan status
(based on its most recent loan) and whether it is on hold.

Used by: `Controller.browse_catalogue()` (the base list every catalogue
filter narrows down), `Controller._find_game()` (looks up a single game by
id, used by `return_game()`, `toggle_hold()` and `remove_game()`).

#### Arguments

```
None
```

#### Returns

```
[(game_id:int, name:str, category:str, min_players:int, max_players:int,
  min_age:int, status:str, on_hold:bool)]
```

`status` is `"Now"` if the game is currently available, or
`f"Loaned on {date}"` if it is currently on loan.

---

### `get_game_name(name)`

Returns the details of all games which have a similar name to the provided
name (case-insensitive substring match).

Used by: `Controller.browse_catalogue()`, when a title search is provided.

#### Arguments

```
name: str
```

#### Returns

```
[(game_id:int, name:str, category:str, min_players:int, max_players:int,
  min_age:int, status:str, on_hold:bool)]
```

---

### `get_games_players(num_players)`

Returns all the games with minimum players less than or equal to the provided
`num_players`, and maximum players more than or equal to the provided
`num_players`.

Used by: `Controller.browse_catalogue()`, when a player-count filter is
provided.

#### Arguments

```
num_players: int
```

#### Returns

```
[(game_id:int, name:str, category:str, min_players:int, max_players:int,
  min_age:int, status:str, on_hold:bool)]
```

---

### `get_games_age(age)`

Returns all the games with a minimum age lower or equal to provided age.

Used by: `Controller.browse_catalogue()`, when an age filter is provided.

#### Arguments

```
age: int
```

#### Returns

```
[(game_id:int, name:str, category:str, min_players:int, max_players:int,
  min_age:int, status:str, on_hold:bool)]
```

---

### `get_games_available()`

Returns the full catalogue rows for all games that are not currently on
loan (`status == "Now"`).

Used by: `Controller.browse_catalogue()`, when the "available only" filter
is on, and `Controller.borrow_games()`, to check every requested game is
actually available before creating a loan.

#### Arguments

```
None
```

#### Returns

```
[(game_id:int, name:str, category:str, min_players:int, max_players:int,
  min_age:int, status:str, on_hold:bool)]
```

---

### `get_games_on_hold()`

Returns the full catalogue rows for all games currently on hold.

Not currently called by `Controller` — holds are instead checked and toggled
directly through `get_mem_held_games()` / `update_hold()`. Kept for parity
with the rest of the `get_games_*` filters and available for a future
"games on hold" view.

#### Arguments

```
None
```

#### Returns

```
[(game_id:int, name:str, category:str, min_players:int, max_players:int,
  min_age:int, status:str, on_hold:bool)]
```

<div style="page-break-before: always;"></div>

### `get_members()`

Returns the id and full name of all active members.

Used by: `Controller.get_active_members()` (member/owner dropdowns in the
View), `Controller.borrow_games()`'s underlying `add_annual_fees()` call.

#### Arguments

```
None
```

#### Returns

```
[(mem_id:int, name:str)]
```

---

### `get_all_members()`

Returns the id, full name, active status and admin flag for every member,
regardless of active status — added so the admin "Manage Members" tab can
list and reactivate inactive members, which `get_members()` alone cannot do.

Used by: `Controller.get_all_members()`, for the admin "Manage Members" table.

#### Arguments

```
None
```

#### Returns

```
[(mem_id:int, name:str, active:int, admin:int)]
```

---

### `get_member_by_email(email)`

Returns the full member record for the provided email, or `None` if no
member has that email — added to support login and duplicate-email checks
at registration.

Used by: `Controller.login()` and `Controller.register_member()`.

#### Arguments

```
email: str
```

#### Returns

```
(mem_id:int, first_name:str, last_name:str, email:str, password:str,
 phone:str, active:int, admin:int) | None
```

---

### `get_games()`

Returns the game id and name of all games to display in a dropdown box.

Used by: `Controller.get_games_dropdown()`.

#### Arguments

```
None
```

#### Returns

```
[(game_id:int, name:str)]
```

---

### `get_games_on_loan()`

Returns all the games *currently* on loan (return_date is still unset), and
the member who borrowed them.

Used by: `Controller.get_games_on_loan()` (not currently wired into the View,
available for a future "on loan" report).

#### Arguments

```
None
```

#### Returns

```
[(game_name:str, date_borrowed:str, member_name:str)]
```

<div style="page-break-before: always;"></div>

### `get_categories()`

Returns the category id and name of all categories to display in a dropdown
box.

Used by: `Controller.browse_catalogue()` (to resolve a chosen `category_id`
to the category name stored on each catalogue row), `Controller.get_categories()`
(category dropdowns in the View).

#### Arguments

```
None
```

#### Returns

```
[(cat_id:int, name:str)]
```

---

### `get_members_games(mem_id)`

Returns the games currently on loan to the provided member.

Used by: `Controller.get_member_loans()`, for the "My Loans" tab.

#### Arguments

```
mem_id: int
```

#### Returns

```
[(game_id:int, game_name:str)]
```

---

### `get_fees(mem_id)`

Returns the member's fees with payment status, one row per year.

Used by: `Controller.get_member_fees()`, for the "My Fees" tab and the admin
"Manage Fees" tab.

#### Arguments

```
mem_id: int
```

#### Returns

```
[(year:int, paid:bool)]
```

---

### `get_latest_loan_id()`

Returns the most recently created `loan_id`.

Not called by `Controller` directly — used internally by `Datastore.add_loan()`
to return the id of the loan it just created.

#### Arguments

```
None
```

#### Returns

```
loan_id: int
```

---

### `get_mem_held_games()`

Returns the game_id of every game currently on hold, and the mem_id holding
it.

Not called by `Controller` directly — used internally by `Datastore.update_hold()`
to decide whether a hold is being added or removed.

#### Arguments

```
None
```

#### Returns

```
[(game_id:int, mem_id:int)]
```

<div style="page-break-before: always;"></div>

## Add Methods

### `add_annual_fees(year, amt)`

Adds an annual fee row, unpaid, for every currently active member.

There is no guard against running the same year twice — doing so raises
`sqlite3.IntegrityError` (the `fees` table has a composite primary key of
`(year, mem_id)`). `Controller.run_annual_fees()` catches this and raises a
`ControllerError` with a friendly message instead.

Used by: `Controller.run_annual_fees()`.

#### Arguments

```
year: int
amt: int
```

#### Returns

```
None
```

---

### `add_loan(mem_id)`

Adds a new loan to the database for the member on today's date.

Used by: `Controller.borrow_games()`, once per borrow transaction (one loan
can cover several games via `add_game_to_loan()`).

#### Arguments

```
mem_id: int
```

#### Returns

```
loan_id: int
```

---

### `add_game_to_loan(loan_id, game_id)`

Adds the provided game to the provided loan.

Used by: `Controller.borrow_games()`, once per game being borrowed.

#### Arguments

```
loan_id: int
game_id: int
```

#### Returns

```
None
```

<div style="page-break-before: always;"></div>

### `add_members(first_name, last_name, email, password, phone, admin)`

Adds a new member's details to the datastore. Note the method name is
plural (`add_members`, not `add_member`).

Used by: `Controller.register_member()`, which hashes `password` before
calling this.

#### Arguments

```
first_name: str
last_name: str
email: str
password: str
phone: str
admin: int
```

#### Returns

```
None
```

---

### `add_game(name, cat_id, min_players, max_players, min_age, owner)`

Adds the provided game to the catalogue.

Used by: `Controller.add_game()`, which validates the arguments (e.g.
`min_players <= max_players`) before calling this.

#### Arguments

```
name: str
cat_id: int
min_players: int
max_players: int
min_age: int
owner: int | None
```

#### Returns

```
None
```

<div style="page-break-before: always;"></div>

## Update Methods

### `update_hold(mem_id, game_id)`

If the provided game currently has a hold for that member &rarr; remove the
hold.

If the provided game does not have a hold for that member &rarr; add a hold
for that member (replacing any other member's hold).

Used by: `Controller.toggle_hold()`.

#### Arguments

```
mem_id: int
game_id: int
```

#### Returns

```
None
```

---

### `update_loan(game_id)`

Sets today's date as the return date on the game's currently open loan only
— it does not touch any of that game's already-closed, historical loan
rows.

Used by: `Controller.return_game()`.

#### Arguments

```
game_id: int
```

#### Returns

```
None
```

---

### `update_member_status(mem_id)`

Toggles a member's status.

If active &rarr; inactive

If inactive &rarr; active

Used by: `Controller.toggle_member_active()`.

#### Arguments

```
mem_id: int
```

#### Returns

```
None
```

---

### `update_fees(year, mem_id)`

Records the payment of the fee amount for the year and member.

Used by: `Controller.record_fee_payment()`.

#### Arguments

```
year: int
mem_id: int
```

#### Returns

```
None
```

---

### `update_password(mem_id, password)`

Replaces the stored password value for the provided member — added to
support `Controller.login()`'s transparent upgrade of legacy plaintext
passwords to salted hashes on first successful login.

Used by: `Controller.login()`.

#### Arguments

```
mem_id: int
password: str
```

#### Returns

```
None
```

<div style="page-break-before: always;"></div>

## Delete Methods

### `delete_game(game_id)`

Removes the provided game from the datastore. Does not cascade-delete any
`games_loaned` rows referencing it.

Used by: `Controller.remove_game()`, which first checks whether the game is
currently on loan and requires explicit confirmation before deleting it in
that case.

#### Arguments

```
game_id: int
```

#### Returns

```
None
```

## Misc Methods

### `date_today()`

Returns today's date formatted `YYYY-MM-DD`.

Used internally by `Datastore.add_loan()` and `Datastore.update_loan()` to
stamp loan/return dates.

#### Arguments

```
None
```

#### Returns

```
today: str
```
