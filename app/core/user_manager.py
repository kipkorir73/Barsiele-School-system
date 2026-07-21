from .db_manager import DBManager


class UserManagementError(ValueError):
    """Raised when a user change would violate account safety rules."""


class LastAdminError(UserManagementError):
    """Raised when an operation would leave the system without an admin."""


class UserHasPaymentsError(UserManagementError):
    """Raised when deleting a user would orphan financial history."""


def delete_user(user_id: int) -> None:
    """Delete a user unless they are required for access or payment history."""
    with DBManager() as db:
        db.cursor.execute(
            """
            DELETE FROM users
            WHERE id = ?
              AND NOT EXISTS (
                  SELECT 1 FROM payments WHERE clerk_id = ?
              )
              AND (
                  role != 'admin'
                  OR EXISTS (
                      SELECT 1 FROM users AS other
                      WHERE other.role = 'admin' AND other.id != ?
                  )
              )
            """,
            (user_id, user_id, user_id),
        )

        if db.cursor.rowcount:
            return

        user = db.fetch_one("SELECT role FROM users WHERE id = ?", (user_id,))
        if not user:
            raise UserManagementError("User no longer exists.")

        payment = db.fetch_one(
            "SELECT 1 FROM payments WHERE clerk_id = ? LIMIT 1", (user_id,)
        )
        if payment:
            raise UserHasPaymentsError(
                "This user recorded payments and cannot be deleted because "
                "their financial history must be retained."
            )

        raise LastAdminError(
            "The last administrator cannot be deleted. Create another "
            "administrator first."
        )


def update_user(
    user_id: int,
    username: str,
    email: str,
    role: str,
    hashed_password: str | None = None,
) -> None:
    """Update a user while atomically preserving at least one administrator."""
    password_assignment = ""
    params = [username, email, role]
    if hashed_password is not None:
        password_assignment = ", password = ?"
        params.append(hashed_password)

    params.extend((user_id, role, user_id))
    with DBManager() as db:
        db.cursor.execute(
            f"""
            UPDATE users
            SET username = ?, email = ?, role = ?{password_assignment}
            WHERE id = ?
              AND (
                  role != 'admin'
                  OR ? = 'admin'
                  OR EXISTS (
                      SELECT 1 FROM users AS other
                      WHERE other.role = 'admin' AND other.id != ?
                  )
              )
            """,
            params,
        )

        if db.cursor.rowcount:
            return

        user = db.fetch_one("SELECT id FROM users WHERE id = ?", (user_id,))
        if not user:
            raise UserManagementError("User no longer exists.")

        raise LastAdminError(
            "The last administrator cannot be changed to a clerk. Create "
            "another administrator first."
        )
