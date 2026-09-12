from pydantic import BaseModel, Field

# User Registration & Login Schemas
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

# Transaction Schemas
class TransactionBase(BaseModel):
    title: str = Field(..., min_length=1, description="Description of the item")
    amount: float = Field(..., gt=0, description="Amount must be greater than zero")
    transaction_type: str = Field(..., pattern="^(income|expense)$", description="Must be 'income' or 'expense'")
    category: str = Field(..., min_length=1, description="Category name")
    user_name: str = Field(..., min_length=1, description="Name of the person logging it")

class TransactionCreate(TransactionBase):
    pass

class TransactionResponse(TransactionBase):
    id: int

    class Config:
        from_attributes = True