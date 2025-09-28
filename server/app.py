#!/usr/bin/env python3

from flask import request, session
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from config import app, db, api
from models import User, Recipe

class Signup(Resource):
    def post(self):
        data = request.get_json()
        try:
            user = User(
                username=data.get('username'),
                image_url=data.get('image_url'),
                bio=data.get('bio'),
            )

            # set password (hashed)
            user.password_hash = data.get('password')

            db.session.add(user)
            db.session.commit()

            session['user_id'] = user.id

            return {
                'id': user.id,
                'username': user.username,
                'image_url': user.image_url,
                'bio': user.bio,
            }, 201

        except IntegrityError:
            db.session.rollback()
            return {'errors': ['Username must be unique and present']}, 422
        except Exception as e:
            db.session.rollback()
            return {'errors': [str(e)]}, 422

class CheckSession(Resource):
    def get(self):
        user_id = session.get('user_id')
        if user_id:
            user = User.query.get(user_id)
            if user:
                return {
                    'id': user.id,
                    'username': user.username,
                    'image_url': user.image_url,
                    'bio': user.bio,
                }, 200
        return {'error': 'Not authorized'}, 401

class Login(Resource):
    def post(self):
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        user = User.query.filter(User.username == username).first()
        if user and user.authenticate(password):
            session['user_id'] = user.id
            return {
                'id': user.id,
                'username': user.username,
                'image_url': user.image_url,
                'bio': user.bio,
            }

        return {'error': 'Invalid username or password'}, 401

class Logout(Resource):
    def delete(self):
        user_id = session.get('user_id')
        if user_id:
            session.pop('user_id', None)
            return '', 204
        return {'error': 'Not authorized'}, 401

class RecipeIndex(Resource):
    def get(self):
        user_id = session.get('user_id')
        if not user_id:
            return {'error': 'Not authorized'}, 401

        recipes = Recipe.query.all()
        resp = []
        for r in recipes:
            resp.append({
                'id': r.id,
                'title': r.title,
                'instructions': r.instructions,
                'minutes_to_complete': r.minutes_to_complete,
                'user': {
                    'id': r.user.id if r.user else None,
                    'username': r.user.username if r.user else None,
                    'image_url': r.user.image_url if r.user else None,
                    'bio': r.user.bio if r.user else None,
                }
            })
        return resp, 200

    def post(self):
        user_id = session.get('user_id')
        if not user_id:
            return {'error': 'Not authorized'}, 401

        data = request.get_json()
        try:
            recipe = Recipe(
                title=data.get('title'),
                instructions=data.get('instructions'),
                minutes_to_complete=data.get('minutes_to_complete'),
            )

            # associate with current user
            recipe.user = User.query.get(user_id)

            db.session.add(recipe)
            db.session.commit()

            return {
                'id': recipe.id,
                'title': recipe.title,
                'instructions': recipe.instructions,
                'minutes_to_complete': recipe.minutes_to_complete,
                'user': {
                    'id': recipe.user.id,
                    'username': recipe.user.username,
                    'image_url': recipe.user.image_url,
                    'bio': recipe.user.bio,
                }
            }, 201

        except IntegrityError:
            db.session.rollback()
            return {'errors': ['Invalid recipe']}, 422
        except ValueError as e:
            db.session.rollback()
            return {'errors': [str(e)]}, 422
        except Exception as e:
            db.session.rollback()
            return {'errors': [str(e)]}, 422

api.add_resource(Signup, '/signup', endpoint='signup')
api.add_resource(CheckSession, '/check_session', endpoint='check_session')
api.add_resource(Login, '/login', endpoint='login')
api.add_resource(Logout, '/logout', endpoint='logout')
api.add_resource(RecipeIndex, '/recipes', endpoint='recipes')


# Ensure tables exist for tests / development
with app.app_context():
    db.create_all()


if __name__ == '__main__':
    app.run(port=5555, debug=True)