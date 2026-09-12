from sqlalchemy import Column, Integer, String, Float, ForeignKey, Date, Boolean
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    transaction_type = Column(String, nullable=False)  # "income" or "expense"
    category = Column(String, nullable=False)
    user_name = Column(String, nullable=False)
    date = Column(Date, nullable=True)                 # Transaction date
    account = Column(String, default="Main Account")   # e.g., Cheque, Cash, Savings
    notes = Column(String, nullable=True)              # Optional note


class BudgetCategory(Base):
    __tablename__ = "budget_categories"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String, nullable=False)          # e.g., Housing, Food, Transport
    monthly_limit = Column(Float, nullable=False)      # Monthly budget cap
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)


class RecurringBill(Base):
    __tablename__ = "recurring_bills"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)             # e.g., Rent, Car Insurance
    amount = Column(Float, nullable=False)
    due_date = Column(Date, nullable=False)            # Next payment date
    is_paid = Column(Boolean, default=False)           # True if already paid this cycle
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)


class FinancialGoal(Base):
    __tablename__ = "financial_goals"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)             # e.g., Emergency Fund, Holiday
    target_amount = Column(Float, nullable=False)      # Total target
    current_amount = Column(Float, default=0.0)        # Amount saved so far
    target_date = Column(Date, nullable=True)          # Target completion date
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)


class FinancialAccount(Base):
    __tablename__ = "financial_accounts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)              # e.g., FNB Cheque, Savings, Cash
    balance = Column(Float, default=0.0)               # Current balance
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)