"""
Orders (read-only model)
SPDX - License - Identifier: LGPL - 3.0 - or -later
Auteurs : Gabriel C. Ullmann, Fabio Petrillo, 2025
"""
from collections import defaultdict, namedtuple
from db import get_sqlalchemy_session, get_redis_conn
from sqlalchemy import desc
from models.order import Order

def get_order_by_id(order_id):
    """Get order by ID from Redis"""
    r = get_redis_conn()
    return r.hgetall(order_id)

def get_orders_from_mysql(limit=9999):
    """Get last X orders"""
    session = get_sqlalchemy_session()
    return session.query(Order).order_by(desc(Order.id)).limit(limit).all()

def get_orders_from_redis(limit=9999):
    """Get last X orders"""
    r = get_redis_conn()

    # 1) Lister les cles de type order:* et extraire les IDs
    keys = r.keys("order:*")
    order_ids = []
    for k in keys:
        if k.endswith(":items"):
            continue
        try:
            order_ids.append(int(k.split(":")[1]))
        except:
            continue

    # 2) Trier les IDs par ordre décroissant et limiter le nombre de résultats
    order_ids.sort(reverse=True)
    order_ids = order_ids[:limit]

    # 3) Lire les hashes correspondants en pipeline
    pipe = r.pipeline()
    for oid in order_ids:
        pipe.hgetall(f"order:{oid}")
    orders = pipe.execute()

    # 4) Retourner des objets (id, total_amount) pour la vue
    OrderRow = type("OrderRow", (), {})
    result = []
    for oid, h in zip(order_ids, orders):
        if not h:
            continue
        row = OrderRow()
        row.id = oid
        row.total_amount = float(h.get('total_amount', 0))
        result.append(row)
    return result

def get_highest_spending_users(limit=10):
    """Get report of best selling products for Redis only"""
    r = get_redis_conn()

    # 1) Recuprer les cles d'ordres
    order_keys = [k for k in r.keys("order:*") if not k.endswith(":items")]

    # 2) Lire tous les hashes en pipeline
    pipe = r.pipeline()
    for k in order_keys:
        pipe.hgetall(k)
    hashes = pipe.execute()

    # 3) Agréger par user_id
    expenses_by_user = defaultdict(float)
    for h in hashes:
        if not h: continue
        try: 
            uid = int(h.get('user_id', 0))
            total = float(h.get('total_amount', 0))
        except Exception:
            continue
        expenses_by_user[uid] += total

    # 4) Trier et limiter
    get_highest_spending_users = sorted(
        expenses_by_user.items(), 
        key=lambda x: x[1], 
        reverse=True
    )[:limit]

    # 5) Retourner une liste de dicts
    Row = type("UserSpendingRow", (), {})
    result = []
    for uid, total in get_highest_spending_users:
        row = Row()
        row.user_id = uid
        row.total_spent = total
        result.append(row)

    return result

def get_best_selling_products(limit=10):
    """Get report of best selling products for Redis only"""
    ProductStat = namedtuple('ProductStat', ['product_id', 'sold_qty'])
    r = get_redis_conn()

    stats = []
    for k in r.scan_iter(match="product:*:sold_qty"):
        try:
            # Ne lire que les strings; sinon on ignore
            if r.type(k) != 'string':
                continue
            v = r.get(k) 
            pid = int(k.split(":")[1])
            qty = int(v or 0)
            stats.append(ProductStat(product_id=pid, sold_qty=qty))
        except Exception:
            continue

    stats.sort(key=lambda x: x.sold_qty, reverse=True)
    return stats[:limit]