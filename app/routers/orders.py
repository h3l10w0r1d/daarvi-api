from __future__ import annotations
from typing import List
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.deps import get_current_user
from app.models.order import Order, OrderItem
from app.models.user import User
from app.schemas.order import OrderIn, OrderOut

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", response_model=OrderOut, status_code=201)
async def create_order(
    body: OrderIn,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    total = sum(item.price * item.qty for item in body.items)
    order = Order(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        mode=body.mode,
        total=total,
        status="confirmed",
        shipping_name=body.shipping_name,
        shipping_address=body.shipping_address,
        shipping_city=body.shipping_city,
        shipping_country=body.shipping_country,
    )
    db.add(order)
    await db.flush()

    for item in body.items:
        db.add(OrderItem(
            order_id=order.id,
            product_id=item.product_id,
            size=item.size,
            color=item.color,
            qty=item.qty,
            price=item.price,
        ))

    await db.flush()
    result = await db.execute(
        select(Order).where(Order.id == order.id).options(selectinload(Order.items))
    )
    order = result.scalar_one()
    return OrderOut.model_validate(order)


@router.get("", response_model=List[OrderOut])
async def list_orders(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Order)
        .where(Order.user_id == current_user.id)
        .options(selectinload(Order.items))
        .order_by(Order.created_at.desc())
    )
    orders = result.scalars().all()
    return [OrderOut.model_validate(o) for o in orders]


@router.get("/{order_id}", response_model=OrderOut)
async def get_order(
    order_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Order)
        .where(Order.id == order_id, Order.user_id == current_user.id)
        .options(selectinload(Order.items))
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return OrderOut.model_validate(order)
