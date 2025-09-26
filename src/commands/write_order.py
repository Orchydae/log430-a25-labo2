"""
Orders (write-only model)
SPDX - License - Identifier: LGPL - 3.0 - or -later
Auteurs : Gabriel C. Ullmann, Fabio Petrillo, 2025
"""
import json
from models.product import Product
from models.order_item import OrderItem
from models.order import Order
from queries.read_order import get_orders_from_mysql
from db import get_sqlalchemy_session, get_redis_conn

def add_order(user_id: int, items: list):
    """Insert order with items in MySQL, keep Redis in sync"""
    if not user_id or not items:
        raise ValueError("Vous devez indiquer au moins 1 utilisateur et 1 item pour chaque commande.")

    try:
        product_ids = []
        for item in items:
            product_ids.append(int(item['product_id']))
    except Exception as e:
        print(e)
        raise ValueError(f"L'ID Article n'est pas valide: {item['product_id']}")
    session = get_sqlalchemy_session()

    try:
        products_query = session.query(Product).filter(Product.id.in_(product_ids)).all()
        price_map = {product.id: product.price for product in products_query}
        total_amount = 0
        order_items_data = []
        
        for item in items:
            pid = int(item["product_id"])
            qty = float(item["quantity"])

            if not qty or qty <= 0:
                raise ValueError(f"Vous devez indiquer une quantité superieure à zéro.")

            if pid not in price_map:
                raise ValueError(f"Article ID {pid} n'est pas dans la base de données.")

            unit_price = price_map[pid]
            total_amount += unit_price * qty
            order_items_data.append({
                'product_id': pid,
                'quantity': qty,
                'unit_price': unit_price
            })
        
        new_order = Order(user_id=user_id, total_amount=total_amount)
        session.add(new_order)
        session.flush() 
        
        order_id = new_order.id

        for item_data in order_items_data:
            order_item = OrderItem(
                order_id=order_id,
                product_id=item_data['product_id'],
                quantity=item_data['quantity'],
                unit_price=item_data['unit_price']
            )
            session.add(order_item)

        session.commit()

        # Correctif est de passer _order_items_data et non items (initialement present)
        add_order_to_redis(order_id, user_id, total_amount, order_items_data)
        increment_product_counters(order_items_data)

        return order_id

    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

def delete_order(order_id: int):
    """Delete order in MySQL, keep Redis in sync"""
    session = get_sqlalchemy_session()
    try:
        order = session.query(Order).filter(Order.id == order_id).first()
        
        if order:
            session.delete(order)
            session.commit()

            delete_order_from_redis(order_id)
            return 1  
        else:
            return 0  
            
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

def add_order_to_redis(order_id, user_id, total_amount, items):
    """Insert order to Redis
    - order:{id} -> hash (user_id, total_amount)
    - order:{id}:items -> list of JSON items (product_id, quantity, unit_price)
    """
    r = get_redis_conn()
    # Hash + list of JSON items
    order_key = f"order:{order_id}"
    items_key = f"{order_key}:items"

    # 1) Hash des metadonnees (cree ou remplace)
    r.hset(order_key, mapping={
        "user_id": int(user_id),
        "total_amount": float(total_amount)
    })

    # 2) Liste des items (reinitialise)
    r.delete(items_key)  # Supprime les items existants, s'il y en a
    for item in items:
        """ Tolerons deux formes:
        - dict: {'product_id': 1, 'quantity': 2}
        - objet SQLAlchemy: OrderItem(product_id=1, quantity=2, unit_price=9.99)
        """
        if isinstance(item, dict):
            product_id = int(item["product_id"])
            quantity = float(item["quantity"])
            unit_price = float(item["unit_price"])
        else:
            product_id = int(item.product_id)
            quantity = float(item.quantity)
            unit_price = float(item.unit_price)
        
        r.rpush(items_key, json.dumps({
            "product_id": product_id,
            "quantity": quantity,
            "unit_price": unit_price
        }))

def delete_order_from_redis(order_id):
    """Delete order from Redis"""
    r = get_redis_conn()
    r.delete(f"order:{order_id}")
    r.delete(f"order:{order_id}:items")

def sync_all_orders_to_redis():
    """ Sync orders from MySQL to Redis pm startup"""
    # redis
    r = get_redis_conn()
    orders_in_redis = r.keys(f"order:*")
    rows_added = 0
    try:
        if len(orders_in_redis) == 0:
            # Redis est vide -> on charge depuis MySQL
            orders_from_mysql = get_orders_from_mysql(limit=9999)
            for order in orders_from_mysql:
                order_id = order.id
                user_id = order.user_id
                total_amount = order.total_amount
                items = order.order_items
                add_order_to_redis(order_id, user_id, total_amount, items)    
            rows_added = len(orders_from_mysql)
            print(f"{rows_added} commandes ajoutées à Redis depuis MySQL")
        else:
            print('Redis already contains orders, no need to sync!')
    except Exception as e:
        print(e)
        return 0
    finally:
        return len(orders_in_redis) + rows_added
    
def increment_product_counters(items):
    """ Increment product counters in Redis based on order items """
    r = get_redis_conn()
    pipe = r.pipeline()
    for item in items:
        # item peut etre dict ou objet SQLAlchemy
        qty = int(item['quantity']) if isinstance(item, dict) else int(item.quantity)
        pid = int(item['product_id']) if isinstance(item, dict) else int(item.product_id)
        pipe.incrby(f"product:{pid}:sold_qty", qty) 
    pipe.execute()