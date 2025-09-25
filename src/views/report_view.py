"""
Report view
SPDX - License - Identifier: LGPL - 3.0 - or -later
Auteurs : Gabriel C. Ullmann, Fabio Petrillo, 2025
"""
from views.template_view import get_template, get_param
from queries.read_order import get_highest_spending_users, get_best_selling_products
from queries.read_user import get_users
from queries.read_product import get_products

def show_highest_spending_users():
    """ Show report of highest spending users """
    ranking = get_highest_spending_users(10)
    users = get_users()
    name_by_id = {user.id: user.name for user in users}

    rows =[]
    for r in ranking:
        name = name_by_id.get(r.user_id, f"User #{r.user_id}")
        rows.append(f"""
            <tr>
                <td>{name}</td>
                <td>${r.total_spent:.2f}</td>
            </tr> """)
    return get_template(f"""<!-- <html> -->
        <h2>Les plus gros acheteurs</h2>
        <table class='table'> 
            <tr><th>Nom</th><th>Total dépensé</th></tr>
            {''.join(rows)}
        </table> 
        """)

def show_best_sellers():
    """ Show report of best selling products """
    ranking = get_best_selling_products(10)

    rows = []
    for stat in ranking:
        rows.append(f"""
            <tr>
                <td>Produit #{stat.product_id}</td>
                <td>{stat.sold_qty} unités</td>
            </tr> """)
    return get_template(f"""<!-- <html> -->
        <h2>Les articles les plus vendus</h2>
        <table class='table'> 
            <tr><th>Produit</th><th>Quantité vendue</th></tr>
            {''.join(rows)}
        </table> 
        """)