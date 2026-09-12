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

# Create any database tables that do not exist yet in PostgreSQL
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Household Budget API")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app.mount("/static", StaticFiles(directory="static"), name="static")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> models.User:
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


@app.get("/")
def serve_home():
    return FileResponse("static/index.html")


# -------------------------------------------------------------
# Authentication
# -------------------------------------------------------------
@app.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(models.User).filter(models.User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    hashed = auth.hash_password(user_data.password)
    new_user = models.User(username=user_data.username, hashed_password=hashed)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.post("/token", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = auth.create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


# -------------------------------------------------------------
# Transactions
# -------------------------------------------------------------
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
        user_name=transaction.user_name,
        date=transaction.date,
        account=transaction.account or "Main Account",
        notes=transaction.notes
    )
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction


@app.get("/transactions/", response_model=List[schemas.TransactionResponse])
def get_all_transactions(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return db.query(models.Transaction).order_by(models.Transaction.id.desc()).all()


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
    db_transaction.date = transaction_update.date
    db_transaction.account = transaction_update.account or "Main Account"
    db_transaction.notes = transaction_update.notes

    db.commit()
    db.refresh(db_transaction)
    return db_transaction


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


# -------------------------------------------------------------
# Budgets
# -------------------------------------------------------------
@app.post("/budgets/", response_model=schemas.BudgetCategoryResponse, status_code=status.HTTP_201_CREATED)
def create_budget_category(
    budget: schemas.BudgetCategoryCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_budget = models.BudgetCategory(
        category=budget.category,
        monthly_limit=budget.monthly_limit,
        user_id=current_user.id
    )
    db.add(db_budget)
    db.commit()
    db.refresh(db_budget)
    return db_budget


@app.get("/budgets/", response_model=List[schemas.BudgetCategoryResponse])
def get_budgets(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return db.query(models.BudgetCategory).filter(models.BudgetCategory.user_id == current_user.id).all()


@app.delete("/budgets/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_budget(
    budget_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    record = db.query(models.BudgetCategory).filter(
        models.BudgetCategory.id == budget_id,
        models.BudgetCategory.user_id == current_user.id
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="Budget limit not found")

    db.delete(record)
    db.commit()
    return None


# -------------------------------------------------------------
# Recurring Bills
# -------------------------------------------------------------
@app.post("/bills/", response_model=schemas.RecurringBillResponse, status_code=status.HTTP_201_CREATED)
def create_bill(
    bill: schemas.RecurringBillCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_bill = models.RecurringBill(
        title=bill.title,
        amount=bill.amount,
        due_date=bill.due_date,
        is_paid=bill.is_paid,
        user_id=current_user.id
    )
    db.add(db_bill)
    db.commit()
    db.refresh(db_bill)
    return db_bill


@app.get("/bills/", response_model=List[schemas.RecurringBillResponse])
def get_bills(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return db.query(models.RecurringBill).filter(
        models.RecurringBill.user_id == current_user.id
    ).order_by(models.RecurringBill.due_date.asc()).all()


@app.patch("/bills/{bill_id}/toggle", response_model=schemas.RecurringBillResponse)
def toggle_bill_paid(
    bill_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_bill = db.query(models.RecurringBill).filter(
        models.RecurringBill.id == bill_id,
        models.RecurringBill.user_id == current_user.id
    ).first()
    if not db_bill:
        raise HTTPException(status_code=404, detail="Bill not found")

    db_bill.is_paid = not db_bill.is_paid
    db.commit()
    db.refresh(db_bill)
    return db_bill


@app.delete("/bills/{bill_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bill(
    bill_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    record = db.query(models.RecurringBill).filter(
        models.RecurringBill.id == bill_id,
        models.RecurringBill.user_id == current_user.id
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="Bill not found")

    db.delete(record)
    db.commit()
    return None


# -------------------------------------------------------------
# Financial Goals
# -------------------------------------------------------------
@app.post("/goals/", response_model=schemas.FinancialGoalResponse, status_code=status.HTTP_201_CREATED)
def create_goal(
    goal: schemas.FinancialGoalCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_goal = models.FinancialGoal(
        title=goal.title,
        target_amount=goal.target_amount,
        current_amount=goal.current_amount,
        target_date=goal.target_date,
        user_id=current_user.id
    )
    db.add(db_goal)
    db.commit()
    db.refresh(db_goal)
    return db_goal


@app.get("/goals/", response_model=List[schemas.FinancialGoalResponse])
def get_goals(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return db.query(models.FinancialGoal).filter(models.FinancialGoal.user_id == current_user.id).all()


@app.put("/goals/{goal_id}", response_model=schemas.FinancialGoalResponse)
def update_goal(
    goal_id: int,
    goal_update: schemas.FinancialGoalCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_goal = db.query(models.FinancialGoal).filter(
        models.FinancialGoal.id == goal_id,
        models.FinancialGoal.user_id == current_user.id
    ).first()
    if not db_goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    db_goal.title = goal_update.title
    db_goal.target_amount = goal_update.target_amount
    db_goal.current_amount = goal_update.current_amount
    db_goal.target_date = goal_update.target_date

    db.commit()
    db.refresh(db_goal)
    return db_goal


@app.delete("/goals/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_goal(
    goal_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    record = db.query(models.FinancialGoal).filter(
        models.FinancialGoal.id == goal_id,
        models.FinancialGoal.user_id == current_user.id
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="Goal not found")

    db.delete(record)
    db.commit()
    return None


# -------------------------------------------------------------
# Financial Accounts
# -------------------------------------------------------------
@app.post("/accounts/", response_model=schemas.FinancialAccountResponse, status_code=status.HTTP_201_CREATED)
def create_account(
    account: schemas.FinancialAccountCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_account = models.FinancialAccount(
        name=account.name,
        balance=account.balance,
        user_id=current_user.id
    )
    db.add(db_account)
    db.commit()
    db.refresh(db_account)
    return db_account


@app.get("/accounts/", response_model=List[schemas.FinancialAccountResponse])
def get_accounts(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return db.query(models.FinancialAccount).filter(models.FinancialAccount.user_id == current_user.id).all()


@app.delete("/accounts/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    record = db.query(models.FinancialAccount).filter(
        models.FinancialAccount.id == account_id,
        models.FinancialAccount.user_id == current_user.id
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="Account not found")

    db.delete(record)
    db.commit()
    return None