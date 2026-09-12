import datetime
from typing import Optional
from pydantic import BaseModel, Field

# -------------------------------------------------------------
# User Registration & Login Schemas
# -------------------------------------------------------------
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, description="Username must be at least 3 characters")
    password: str = Field(..., min_length=6, description="Password must be at least 6 characters")

class UserResponse(BaseModel):
    id: int
    username: str

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str


# -------------------------------------------------------------
# Transaction Schemas
# -------------------------------------------------------------
class TransactionBase(BaseModel):
    title: str = Field(..., min_length=1, description="Description of the item")
    amount: float = Field(..., gt=0, description="Amount must be greater than zero")
    transaction_type: str = Field(..., pattern="^(income|expense)$", description="Must be 'income' or 'expense'")
    category: str = Field(..., min_length=1, description="Category name")
    user_name: str = Field(..., min_length=1, description="Name of the person logging it")
    date: Optional[datetime.date] = Field(default=None, description="Date of transaction (YYYY-MM-DD)")
    account: Optional[str] = Field(default="Main Account", description="Account used")
    notes: Optional[str] = Field(default=None, description="Optional note or reference")

class TransactionCreate(TransactionBase):
    pass

class TransactionResponse(TransactionBase):
    id: int

    class Config:
        from_attributes = True


# -------------------------------------------------------------
# Budget Category Schemas
# -------------------------------------------------------------
class BudgetCategoryBase(BaseModel):
    category: str = Field(..., min_length=1, description="Category name (e.g., Food, Housing)")
    monthly_limit: float = Field(..., gt=0, description="Monthly spending limit")

class BudgetCategoryCreate(BudgetCategoryBase):
    pass

class BudgetCategoryResponse(BudgetCategoryBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True


# -------------------------------------------------------------
# Recurring Bill Schemas
# -------------------------------------------------------------
class RecurringBillBase(BaseModel):
    title: str = Field(..., min_length=1, description="Bill title (e.g., Rent, Car Insurance)")
    amount: float = Field(..., gt=0, description="Bill amount")
    due_date: datetime.date = Field(..., description="Payment due date (YYYY-MM-DD)")
    is_paid: bool = Field(default=False, description="Whether bill is paid")

class RecurringBillCreate(RecurringBillBase):
    pass

class RecurringBillResponse(RecurringBillBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True


# -------------------------------------------------------------
# Financial Goal Schemas
# -------------------------------------------------------------
class FinancialGoalBase(BaseModel):
    title: str = Field(..., min_length=1, description="Goal name (e.g., Emergency Fund)")
    target_amount: float = Field(..., gt=0, description="Target savings amount")
    current_amount: float = Field(default=0.0, ge=0, description="Current amount saved")
    target_date: Optional[datetime.date] = Field(default=None, description="Target completion date (YYYY-MM-DD)")

class FinancialGoalCreate(FinancialGoalBase):
    pass

class FinancialGoalResponse(FinancialGoalBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True


# -------------------------------------------------------------
# Financial Account Schemas
# -------------------------------------------------------------
class FinancialAccountBase(BaseModel):
    name: str = Field(..., min_length=1, description="Account name (e.g., FNB Cheque, Savings)")
    balance: float = Field(default=0.0, description="Current balance")

class FinancialAccountCreate(FinancialAccountBase):
    pass

class FinancialAccountResponse(FinancialAccountBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True