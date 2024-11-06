#!/usr/bin/env python3
from models import db, Restaurant, RestaurantPizza, Pizza
from flask_migrate import Migrate
from flask import Flask, request, make_response
from flask_restful import Api, Resource
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get("DB_URI", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.json.compact = False

migrate = Migrate(app, db)

db.init_app(app)

api = Api(app)


@app.route("/")
def index():
    return "<h1>Code challenge</h1>"

class Restaurants(Resource):
    def get(self):
        restaurants = Restaurant.query.all()
        response_body = [restaurant.to_dict(only=('id', 'name', 'address')) for restaurant in restaurants]
        return make_response(response_body, 200)
    
class RestaurantByID(Resource):
    def get(self, id):
        restaurant = Restaurant.query.filter_by(id=id).first()
        if not restaurant:
            return make_response({"error": "Restaurant not found"}, 404)
        
        response_dict = {
            "id": restaurant.id,
            "name": restaurant.name,
            "address": restaurant.address,
            "restaurant_pizzas": [{
                "id": rp.pizza.id,
                "name": rp.pizza.name,
                "ingredients": rp.pizza.ingredients,
                "price": rp.price
            } for rp in restaurant.restaurant_pizzas]
        }
        
        return make_response(response_dict, 200)

    def delete(self, id):
        restaurant = Restaurant.query.filter_by(id=id).first()
        if not restaurant:
            return make_response({"error": "Restaurant not found"}, 404)
        
        db.session.delete(restaurant)
        db.session.commit()
        
        return make_response("", 204)

class Pizzas(Resource):
    def get(self):
        pizzas = [{
            "id": p.id,
            "name": p.name,
            "ingredients": p.ingredients
        } for p in Pizza.query.all()]
        return make_response(pizzas, 200)

class RestaurantPizzas(Resource):
    def post(self):
        data = request.get_json()
        
        if not all(key in data for key in ['price', 'pizza_id', 'restaurant_id']):
            return make_response({"errors": ["validation errors"]}, 400)
        
        try:
            price = int(data.get('price'))
            pizza_id = int(data.get('pizza_id'))
            restaurant_id = int(data.get('restaurant_id'))
        except ValueError:
            return make_response({"errors": ["price must be between 1 and 30"]}, 400)
            
        restaurant = Restaurant.query.get(restaurant_id)
        pizza = Pizza.query.get(pizza_id)
        
        
        if not restaurant or not pizza:
            return make_response({"errors": ["validation errors"]}, 400)
            
        try:
            new_restaurant_pizza = RestaurantPizza(
                price=price,
                pizza_id=pizza_id,
                restaurant_id=restaurant_id
            )
            
            db.session.add(new_restaurant_pizza)
            db.session.commit()

            return make_response({
                "id": pizza.id,
                "name": pizza.name,
                "ingredients": pizza.ingredients
            }, 201)
            
        except ValueError as e:
            return make_response({"errors": ["validation errors"]}, 400)

api.add_resource(Restaurants, '/restaurants')
api.add_resource(RestaurantByID, '/restaurants/<int:id>')
api.add_resource(Pizzas, '/pizzas')
api.add_resource(RestaurantPizzas, '/restaurant_pizzas')

if __name__ == "__main__":
    app.run(port=5555, debug=True)