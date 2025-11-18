"""
User service for database operations
Handles user CRUD operations with SQLAlchemy
"""

from typing import Optional
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError
from loguru import logger

from src.user_model import User, Base
from src.auth import get_password_hash, verify_password


class UserService:
    """Service for managing users in the database"""

    def __init__(self, database_url: str = "sqlite:///data/applications.db"):
        """Initialize user service with database connection"""
        self.database_url = database_url
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)

        # Create tables if they don't exist
        Base.metadata.create_all(self.engine)

        # Ensure default admin user exists
        self._ensure_default_admin()

    def _ensure_default_admin(self):
        """Ensure default admin user exists"""
        session = self.SessionLocal()
        try:
            # Check if admin user exists
            admin = session.query(User).filter(User.email == "admin@autojobapplier.com").first()

            if not admin:
                # Create default admin user
                admin_user = User(
                    email="admin@autojobapplier.com",
                    full_name="Admin User",
                    hashed_password=get_password_hash("Admin123!"),
                    is_active=True,
                    is_admin=True,
                )
                session.add(admin_user)
                session.commit()
                logger.info("Default admin user created: admin@autojobapplier.com")
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating default admin user: {e}")
        finally:
            session.close()

    def get_session(self) -> Session:
        """Get a new database session"""
        return self.SessionLocal()

    def create_user(self, email: str, password: str, full_name: Optional[str] = None, is_admin: bool = False) -> User:
        """
        Create a new user

        Args:
            email: User's email address
            password: Plain text password (will be hashed)
            full_name: User's full name
            is_admin: Whether user is an admin

        Returns:
            Created User object

        Raises:
            ValueError: If user already exists
        """
        session = self.get_session()
        try:
            # Check if user already exists
            existing_user = session.query(User).filter(User.email == email).first()
            if existing_user:
                raise ValueError("User already exists")

            # Create new user
            user = User(
                email=email,
                full_name=full_name,
                hashed_password=get_password_hash(password),
                is_active=True,
                is_admin=is_admin,
            )

            session.add(user)
            session.commit()
            session.refresh(user)

            # Expunge user from session so it can be used after session closes
            session.expunge(user)

            logger.info(f"User created: {email}")
            return user

        except IntegrityError:
            session.rollback()
            raise ValueError("User already exists")
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating user: {e}")
            raise
        finally:
            session.close()

    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email address

        Args:
            email: User's email address

        Returns:
            User object or None if not found
        """
        session = self.get_session()
        try:
            user = session.query(User).filter(User.email == email).first()
            if user:
                session.expunge(user)
            return user
        finally:
            session.close()

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        Get user by ID

        Args:
            user_id: User's ID

        Returns:
            User object or None if not found
        """
        session = self.get_session()
        try:
            user = session.query(User).filter(User.id == user_id).first()
            if user:
                session.expunge(user)
            return user
        finally:
            session.close()

    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """
        Authenticate a user by email and password

        Args:
            email: User's email address
            password: Plain text password

        Returns:
            User object if authentication successful, None otherwise
        """
        session = self.get_session()
        try:
            user = session.query(User).filter(User.email == email).first()

            if not user:
                logger.warning(f"Authentication failed: user not found - {email}")
                return None

            if not user.is_active:
                logger.warning(f"Authentication failed: user inactive - {email}")
                return None

            if not verify_password(password, user.hashed_password):
                logger.warning(f"Authentication failed: invalid password - {email}")
                return None

            # Update last login
            user.last_login = datetime.now()
            session.commit()
            session.refresh(user)

            # Expunge user from session so it can be used after session closes
            session.expunge(user)

            logger.info(f"User authenticated: {email}")
            return user

        except Exception as e:
            session.rollback()
            logger.error(f"Error authenticating user: {e}")
            return None
        finally:
            session.close()

    def update_user(self, user_id: int, **kwargs) -> Optional[User]:
        """
        Update user fields

        Args:
            user_id: User's ID
            **kwargs: Fields to update (email, full_name, is_active, is_admin)

        Returns:
            Updated User object or None if not found
        """
        session = self.get_session()
        try:
            user = session.query(User).filter(User.id == user_id).first()

            if not user:
                return None

            # Update allowed fields
            allowed_fields = ['email', 'full_name', 'is_active', 'is_admin']
            for field, value in kwargs.items():
                if field in allowed_fields:
                    setattr(user, field, value)

            user.updated_at = datetime.now()
            session.commit()
            session.refresh(user)

            # Expunge user from session so it can be used after session closes
            session.expunge(user)

            logger.info(f"User updated: {user.email}")
            return user

        except IntegrityError:
            session.rollback()
            raise ValueError("Email already exists")
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating user: {e}")
            raise
        finally:
            session.close()

    def change_password(self, user_id: int, new_password: str) -> bool:
        """
        Change user's password

        Args:
            user_id: User's ID
            new_password: New plain text password

        Returns:
            True if successful, False otherwise
        """
        session = self.get_session()
        try:
            user = session.query(User).filter(User.id == user_id).first()

            if not user:
                return False

            user.hashed_password = get_password_hash(new_password)
            user.updated_at = datetime.now()
            session.commit()

            logger.info(f"Password changed for user: {user.email}")
            return True

        except Exception as e:
            session.rollback()
            logger.error(f"Error changing password: {e}")
            return False
        finally:
            session.close()

    def delete_user(self, user_id: int) -> bool:
        """
        Delete a user (soft delete by setting is_active=False)

        Args:
            user_id: User's ID

        Returns:
            True if successful, False otherwise
        """
        session = self.get_session()
        try:
            user = session.query(User).filter(User.id == user_id).first()

            if not user:
                return False

            # Soft delete
            user.is_active = False
            user.updated_at = datetime.now()
            session.commit()

            logger.info(f"User deactivated: {user.email}")
            return True

        except Exception as e:
            session.rollback()
            logger.error(f"Error deleting user: {e}")
            return False
        finally:
            session.close()

    def list_users(self, active_only: bool = True, limit: int = 100, offset: int = 0):
        """
        List users

        Args:
            active_only: Only return active users
            limit: Maximum number of users to return
            offset: Offset for pagination

        Returns:
            List of User objects
        """
        session = self.get_session()
        try:
            query = session.query(User)

            if active_only:
                query = query.filter(User.is_active == True)

            users = query.limit(limit).offset(offset).all()

            # Expunge all users from session
            for user in users:
                session.expunge(user)

            return users

        finally:
            session.close()


# Global instance
user_service = UserService()
