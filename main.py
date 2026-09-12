from fastapi import FastAPI, Depends, status, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List

import models
import schemas
import auth
from database import engine, get_db

# Ensure all database tables exist in budget.db
models.Base.metadata.create_all(bind=engine)

# Initialize the application
app = FastAPI(title="Household Budget API")

# OAuth2 scheme tells FastAPI to look for the token in incoming web requests
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Mount the static folder for HTML, CSS, and JS files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Helper function to get the current authenticated user
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    username = auth.verify_token(token)
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user

# Serve the frontend interface
@app.get("/")
def serve_home():
    return FileResponse("static/index.html")

# 1. Register a new user
@app.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    # Check if the username is already taken
    existing_user = db.query(models.User).filter(models.User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    # Hash the plain-text password before saving
    hashed = auth.hash_password(user_data.password)
    new_user = models.User(username=user_data.username, hashed_password=hashed)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

# 2. Log in and receive a secure token
@app.post("/token", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Issue an access token valid for 24 hours
    access_token = auth.create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

# 3. Create a transaction (Protected)
@app.post("/transactions/", response_model=schemas.TransactionResponse, status_code=status.HTTP_201_CREATED)
def create_transaction(
    transaction: schemas.TransactionCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_transaction = models.Transaction(
        title=transaction.title,
        amount=transaction.amount,
        transaction_type=transaction.transaction_type,
        category=transaction.category,
        user_name=transaction.user_name
    )
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction

# 4. Retrieve all transactions (Protected)
@app.get("/transactions/", response_model=List[schemas.TransactionResponse])
def get_all_transactions(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return db.query(models.Transaction).all()

# 5. Update a transaction (Protected)
@app.put("/transactions/{transaction_id}", response_model=schemas.TransactionResponse)
def update_transaction(
    transaction_id: int,
    transaction_update: schemas.TransactionCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_transaction = db.query(models.Transaction).filter(models.Transaction.id == transaction_id).first()
    if not db_transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    db_transaction.title = transaction_update.title
    db_transaction.amount = transaction_update.amount
    db_transaction.transaction_type = transaction_update.transaction_type
    db_transaction.category = transaction_update.category
    db_transaction.user_name = transaction_update.user_name

    db.commit()
    db.refresh(db_transaction)
    return db_transaction

# 6. Delete a transaction (Protected)
@app.delete("/transactions/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    record = db.query(models.Transaction).filter(models.Transaction.id == transaction_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Transaction not found")

    db.delete(record)
    db.commit()
    return None