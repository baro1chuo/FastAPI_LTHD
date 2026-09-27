from fastapi import FastAPI
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
app = FastAPI()

class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    email: EmailStr
    age: int = Field(ge=0, le=120)

class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr

class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    price: float = Field(gt=0)
    stock: int = Field(ge=0)
    cost_price: float = Field(ge=0)

class ProductOut(BaseModel):
    id: int
    name: str
    price: float
    stock: int
    create_at: datetime
    
@app.post("/users", response_model=UserOut, status_code=201)

def create_user(user: UserCreate):
    return {"id": 1, "name": user.name, "email":user.email}

@app.post("/products", response_model=ProductOut, status_code=201)

def create_product(product: ProductCreate):
    saved = {"id": 1, 
            "name": product.name, 
            "price": product.price,
            "stock": product.stock,
            "create_at": datetime.now(),
            }
    return saved