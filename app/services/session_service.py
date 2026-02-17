"""
Session Service for managing customization sessions in ZeroDB.

This service provides all session management operations including:
- Creating sessions with crypto-secure keys
- Retrieving sessions by key or ID
- Updating session options
- Deleting sessions
- Checking session expiry

Security:
    - Crypto-secure session key generation using secrets module
    - Session expiry validation (30 days)
    - Input validation and sanitization

Performance:
    - Async operations for non-blocking I/O
    - Efficient query filters for lookups
"""
import logging
import secrets
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from uuid import uuid4

from fastapi import HTTPException, status

from app.services.zerodb_service import ZeroDBService


logger = logging.getLogger(__name__)


class SessionService:
    """
    Service for managing customization sessions in ZeroDB NoSQL.

    This service handles all session lifecycle operations:
    - create_session: Initialize new customization session
    - get_session: Retrieve session by session_key
    - get_session_state: Get session with expiry validation
    - update_session: Update session options
    - delete_session: Remove session
    """

    TABLE_NAME = "customization_sessions"
    SESSION_EXPIRY_DAYS = 30

    def __init__(self, zerodb_service: ZeroDBService):
        """
        Initialize session service.

        Args:
            zerodb_service: ZeroDB service instance for database operations
        """
        self.zerodb = zerodb_service

    @staticmethod
    def generate_session_key() -> str:
        """
        Generate a cryptographically secure session key.

        Returns:
            Session key with format: sess_{random_token}

        Security:
            Uses secrets.token_urlsafe for cryptographically secure random tokens.
            The token is 32 bytes, which becomes ~43 characters when base64url encoded.
        """
        token = secrets.token_urlsafe(32)
        return f"sess_{token}"

    async def create_session(
        self,
        product_id: str,
        template_id: str
    ) -> Dict[str, Any]:
        """
        Create a new customization session.

        Args:
            product_id: UUID of the product being customized
            template_id: UUID of the template to use

        Returns:
            Session data including session_id, session_key, product_id,
            template_id, and empty options

        Raises:
            HTTPException: If session creation fails

        Note:
            This method does NOT validate that product_id and template_id
            exist. Validation should be done at the endpoint level.
        """
        # Generate unique session key
        session_key = self.generate_session_key()

        # Check for collision (extremely unlikely but safe guard)
        collision_check = await self._check_session_key_exists(session_key)
        while collision_check:
            logger.warning(f"Session key collision detected: {session_key}")
            session_key = self.generate_session_key()
            collision_check = await self._check_session_key_exists(session_key)

        # Generate session ID
        session_id = str(uuid4())

        # Build session document
        now = datetime.utcnow().isoformat()
        session_data = {
            "id": session_id,
            "session_key": session_key,
            "product_id": product_id,
            "template_id": template_id,
            "options": {},  # Empty options to start
            "is_active": True,
            "created_at": now,
            "updated_at": now
        }

        try:
            # Create session in ZeroDB
            result = await self.zerodb.create_row(self.TABLE_NAME, session_data)
            logger.info(f"Created session {session_id} with key {session_key}")
            return result
        except HTTPException as e:
            logger.error(f"Failed to create session: {str(e)}")
            raise

    async def get_session(self, session_key: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve session by session key.

        Args:
            session_key: The session key to look up

        Returns:
            Session data or None if not found

        Raises:
            HTTPException: If query fails
        """
        try:
            # Query by session_key
            filter_query = {"session_key": {"$eq": session_key}}
            result = await self.zerodb.query_rows(
                table=self.TABLE_NAME,
                filter=filter_query,
                limit=1
            )

            # Extract first result if exists
            results = result.get("results", [])
            if results:
                return results[0]
            return None
        except HTTPException as e:
            logger.error(f"Failed to get session {session_key}: {str(e)}")
            raise

    async def get_session_state(self, session_key: str) -> Dict[str, Any]:
        """
        Retrieve session state with expiry and active status validation.

        Args:
            session_key: The session key to retrieve

        Returns:
            Session state including options and metadata

        Raises:
            HTTPException 404: If session not found, expired, or inactive
        """
        session = await self.get_session(session_key)

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found or expired"
            )

        # Check if session is active
        if not session.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found or expired"
            )

        # Check expiry (30 days)
        created_at_str = session.get("created_at")
        if created_at_str:
            try:
                created_at = datetime.fromisoformat(created_at_str)
                expiry_date = created_at + timedelta(days=self.SESSION_EXPIRY_DAYS)

                if datetime.utcnow() > expiry_date:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Session not found or expired"
                    )
            except (ValueError, TypeError) as e:
                logger.error(f"Invalid created_at format: {created_at_str} - {str(e)}")

        return session

    async def update_session(
        self,
        session_key: str,
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update session options.

        Args:
            session_key: The session key to update
            options: New options data (replaces existing options)

        Returns:
            Updated session data

        Raises:
            HTTPException 404: If session not found
        """
        # Get existing session to retrieve ID
        session = await self.get_session(session_key)

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )

        session_id = session.get("id")
        if not session_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Session ID missing from stored session"
            )

        # Prepare update data
        update_data = {
            **session,  # Keep existing fields
            "options": options,
            "updated_at": datetime.utcnow().isoformat()
        }

        try:
            # Update in ZeroDB
            result = await self.zerodb.update_row(
                table=self.TABLE_NAME,
                row_id=session_id,
                data=update_data
            )
            logger.info(f"Updated session {session_key}")
            return result
        except HTTPException as e:
            logger.error(f"Failed to update session {session_key}: {str(e)}")
            raise

    async def delete_session(self, session_key: str) -> Dict[str, Any]:
        """
        Delete a session.

        Args:
            session_key: The session key to delete

        Returns:
            Deletion confirmation

        Raises:
            HTTPException 404: If session not found
        """
        # Get existing session to retrieve ID
        session = await self.get_session(session_key)

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )

        session_id = session.get("id")
        if not session_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Session ID missing from stored session"
            )

        try:
            result = await self.zerodb.delete_row(
                table=self.TABLE_NAME,
                row_id=session_id
            )
            logger.info(f"Deleted session {session_key}")
            return result
        except HTTPException as e:
            logger.error(f"Failed to delete session {session_key}: {str(e)}")
            raise

    async def _check_session_key_exists(self, session_key: str) -> bool:
        """
        Check if a session key already exists.

        Args:
            session_key: The session key to check

        Returns:
            True if exists, False otherwise
        """
        try:
            session = await self.get_session(session_key)
            return session is not None
        except HTTPException:
            return False
