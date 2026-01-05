"""
Database Connections API Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import time

from app.models.database import get_db, Connection
from app.models.schemas import (
    ConnectionCreate, ConnectionUpdate, ConnectionResponse, 
    ConnectionTestResponse, ErrorResponse
)
from app.core.security import security_manager
from app.core.db_manager import DatabaseManager
from loguru import logger

router = APIRouter()


@router.post("/", response_model=ConnectionResponse, status_code=status.HTTP_201_CREATED)
async def create_connection(
    connection: ConnectionCreate,
    db: Session = Depends(get_db)
):
    """Create a new database connection"""
    try:
        # Check if connection name already exists
        existing = db.query(Connection).filter(Connection.name == connection.name).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Connection with name '{connection.name}' already exists"
            )
        
        # Test connection before saving
        db_manager = DatabaseManager(
            engine=connection.engine.value,
            host=connection.host,
            port=connection.port,
            database=connection.database,
            username=connection.username,
            password=connection.password,
            ssl_enabled=connection.ssl_enabled
        )
        
        success, message = db_manager.connect()
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Connection test failed: {message}"
            )
        db_manager.disconnect()
        
        # Encrypt password
        encrypted_password = security_manager.encrypt(connection.password)
        
        # Create connection record
        db_connection = Connection(
            name=connection.name,
            engine=connection.engine.value,
            host=connection.host,
            port=connection.port,
            database=connection.database,
            username=connection.username,
            password_encrypted=encrypted_password,
            ssl_enabled=connection.ssl_enabled,
            monitoring_enabled=connection.monitoring_enabled,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(db_connection)
        db.commit()
        db.refresh(db_connection)
        
        logger.info(f"Created connection: {connection.name}")
        return db_connection
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating connection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/", response_model=List[ConnectionResponse])
async def list_connections(db: Session = Depends(get_db)):
    """List all database connections"""
    try:
        connections = db.query(Connection).all()
        return connections
    except Exception as e:
        logger.error(f"Error listing connections: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{connection_id}", response_model=ConnectionResponse)
async def get_connection(connection_id: int, db: Session = Depends(get_db)):
    """Get a specific connection"""
    connection = db.query(Connection).filter(Connection.id == connection_id).first()
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Connection with id {connection_id} not found"
        )
    return connection


@router.put("/{connection_id}", response_model=ConnectionResponse)
async def update_connection(
    connection_id: int,
    connection_update: ConnectionUpdate,
    db: Session = Depends(get_db)
):
    """Update a database connection"""
    try:
        connection = db.query(Connection).filter(Connection.id == connection_id).first()
        if not connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Connection with id {connection_id} not found"
            )
        
        # Update fields
        update_data = connection_update.dict(exclude_unset=True)
        
        # If password is being updated, encrypt it
        if "password" in update_data:
            update_data["password_encrypted"] = security_manager.encrypt(update_data.pop("password"))
        
        for field, value in update_data.items():
            setattr(connection, field, value)
        
        connection.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(connection)
        
        logger.info(f"Updated connection: {connection.name}")
        return connection
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating connection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_connection(connection_id: int, db: Session = Depends(get_db)):
    """Delete a database connection"""
    try:
        connection = db.query(Connection).filter(Connection.id == connection_id).first()
        if not connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Connection with id {connection_id} not found"
            )
        
        db.delete(connection)
        db.commit()
        
        logger.info(f"Deleted connection: {connection.name}")
        return None
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting connection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/{connection_id}/test", response_model=ConnectionTestResponse)
async def test_connection(connection_id: int, db: Session = Depends(get_db)):
    """Test a database connection"""
    try:
        connection = db.query(Connection).filter(Connection.id == connection_id).first()
        if not connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Connection with id {connection_id} not found"
            )
        
        # Decrypt password
        password = security_manager.decrypt(connection.password_encrypted)
        
        # Test connection
        start_time = time.time()
        db_manager = DatabaseManager(
            engine=connection.engine,
            host=connection.host,
            port=connection.port,
            database=connection.database,
            username=connection.username,
            password=password,
            ssl_enabled=connection.ssl_enabled
        )
        
        success, message = db_manager.connect()
        latency_ms = (time.time() - start_time) * 1000
        
        if success:
            db_manager.disconnect()
        
        return ConnectionTestResponse(
            success=success,
            message=message,
            latency_ms=latency_ms if success else None
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing connection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
