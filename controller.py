import hashlib
import secrets
import sqlite3

from datastore import Datastore


class ControllerError(Exception):
    """Raised for business-rule violations and translated datastore errors."""


class Controller:
    def __init__(self, db_file: str = "TableTopGamers.db"):
        self.db = Datastore(db_file)

    # ----- AUTH ----- #
    def login(self, email: str, password: str) -> dict | None:
        """
        Returns a dict describing the logged-in member, or None if the
        email/password combination doesn't match an active member.
        """
        member = self.db.get_member_by_email(email)

        if member is None:
            return None

        mem_id, first_name, last_name, email, stored_password, phone, active, admin = member

        if not self._verify_password(password, stored_password):
            return None

        if not active:
            raise ControllerError("This member account is inactive.")

        # legacy plaintext passwords are upgraded to a salted hash on first
        # successful login, so the database self-migrates without a separate
        # migration script.
        if "$" not in stored_password:
            self.db.update_password(mem_id, self._hash_password(password))

        return {
            "mem_id": mem_id,
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "phone": phone,
            "admin": bool(admin),
        }

    def register_member(
        self,
        first_name: str,
        last_name: str,
        email: str,
        password: str,
        phone: str,
        admin: int = 0,
    ):
        if self.db.get_member_by_email(email) is not None:
            raise ControllerError(f"A member with email '{email}' already exists.")

        self.db.add_members(
            first_name, last_name, email, self._hash_password(password), phone, admin
        )

    @staticmethod
    def _hash_password(password: str) -> str:
        salt = secrets.token_hex(16)
        digest = hashlib.sha256((salt + password).encode()).hexdigest()
        return f"{salt}${digest}"

    @staticmethod
    def _verify_password(password: str, stored: str) -> bool:
        if "$" in stored:
            salt, digest = stored.split("$", 1)
            return hashlib.sha256((salt + password).encode()).hexdigest() == digest
        # legacy plaintext value, pre-migration
        return password == stored

    # ----- CATALOGUE ----- #
    def browse_catalogue(
        self,
        search_title: str = "",
        category_id: int | None = None,
        num_players: int | None = None,
        min_age: int | None = None,
        available_only: bool = False,
    ) -> list:
        """
        Returns catalogue rows matching every provided filter. datastore.py's
        get_games_* helpers each filter the full catalogue independently and
        can't be composed, so filters are combined here in one pass.
        """
        games = self.db.get_catalogue()

        if search_title:
            needle = search_title.lower()
            games = [g for g in games if needle in g[1].lower()]

        if category_id is not None:
            category_names = dict(self.db.get_categories())
            category_name = category_names.get(category_id)
            games = [g for g in games if g[2] == category_name]

        if num_players is not None:
            games = [g for g in games if g[3] <= num_players <= g[4]]

        if min_age is not None:
            games = [g for g in games if g[5] <= min_age]

        if available_only:
            games = [g for g in games if g[6] == "Now"]

        return games

    def get_categories(self) -> list[tuple[int, str]]:
        return self.db.get_categories()

    def get_games_dropdown(self) -> list[tuple[int, str]]:
        return self.db.get_games()

    def get_games_on_loan(self) -> list[tuple[str, str, str]]:
        return self.db.get_games_on_loan()

    # ----- LOANS ----- #
    def borrow_games(self, mem_id: int, game_ids: list[int]) -> int:
        if not game_ids:
            raise ControllerError("Select at least one game to borrow.")

        available_ids = {g[0] for g in self.db.get_games_available()}
        unavailable = [gid for gid in game_ids if gid not in available_ids]

        if unavailable:
            raise ControllerError(
                f"The following games are not available to borrow: {unavailable}"
            )

        loan_id = self.db.add_loan(mem_id)

        for game_id in game_ids:
            self.db.add_game_to_loan(loan_id, game_id)

        return loan_id

    def return_game(self, game_id: int):
        game = self._find_game(game_id)

        if game[6] == "Now":
            raise ControllerError("This game is not currently on loan.")

        self.db.update_loan(game_id)

    def get_member_loans(self, mem_id: int) -> list[tuple[int, str]]:
        return self.db.get_members_games(mem_id)

    def toggle_hold(self, mem_id: int, game_id: int):
        self._find_game(game_id)
        self.db.update_hold(mem_id, game_id)

    def _find_game(self, game_id: int) -> list:
        catalogue = self.db.get_catalogue()
        match = next((g for g in catalogue if g[0] == game_id), None)

        if match is None:
            raise ControllerError(f"No game with id {game_id} exists.")

        return match

    # ----- GAME MANAGEMENT ----- #
    def add_game(
        self,
        name: str,
        cat_id: int,
        min_players: int,
        max_players: int,
        min_age: int,
        owner: int | None = None,
    ):
        if not name.strip():
            raise ControllerError("Game name cannot be empty.")
        if min_players < 1:
            raise ControllerError("Minimum players must be at least 1.")
        if max_players < min_players:
            raise ControllerError(
                "Maximum players cannot be less than minimum players."
            )
        if min_age < 0:
            raise ControllerError("Minimum age cannot be negative.")

        self.db.add_game(name.strip(), cat_id, min_players, max_players, min_age, owner)

    def remove_game(self, game_id: int, confirm_on_loan: bool = False):
        game = self._find_game(game_id)

        if game[6] != "Now" and not confirm_on_loan:
            raise ControllerError(
                "This game is currently on loan. Confirm removal to proceed anyway."
            )

        self.db.delete_game(game_id)

    # ----- MEMBERS ----- #
    def get_active_members(self) -> list[tuple[int, str]]:
        return self.db.get_members()

    def get_all_members(self) -> list[tuple[int, str, int, int]]:
        return self.db.get_all_members()

    def toggle_member_active(self, mem_id: int):
        self.db.update_member_status(mem_id)

    # ----- FEES ----- #
    def get_member_fees(self, mem_id: int) -> list[tuple[int, bool]]:
        return self.db.get_fees(mem_id)

    def record_fee_payment(self, year: int, mem_id: int):
        self.db.update_fees(year, mem_id)

    def run_annual_fees(self, year: int, amt: int):
        try:
            self.db.add_annual_fees(year, amt)
        except sqlite3.IntegrityError as exc:
            raise ControllerError(
                f"Annual fees for {year} have already been recorded."
            ) from exc
