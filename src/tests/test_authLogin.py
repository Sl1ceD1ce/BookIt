<<<<<<< HEAD
import os
import pytest
import data_store as ds
=======
>>>>>>> c58886ee518fd6d96d10b7cde49e291958771f97
from server import app

class TestUserLogin:
    def test_login_success(self, client):
        register = client.post(
            "/users/register", 
            json={
                "first_name":"John",
                "last_name":"Doe",
                "email":"john@example.com",
                "password":"Password123_",
                "mobile":"0412345678",
                "tutor":False
            })
        data = register.json()
        token = data["token"]
        res = client.post("/users/login", json={
                "email":"john@example.com",
                "password":"Password123_",
            })
        assert res.status_code == 200
        assert res.json().get("token") is not None
        assert isinstance(res.json()["token"], str)

        # checking token is actually usable with getUserInfo
        res = client.get("/users/", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200
        assert res.json() == {
            "email":"john@example.com",
            "mobile":"0412345678",
            "first_name":"John",
            "last_name":"Doe",
            "tutor":False
        }

    def test_login_incorrect_password(self, client):
        register = client.post(
            "/users/register", 
            json={
                "first_name":"John",
                "last_name":"Doe",
                "email":"john@example.com",
                "password":"Password123_",
                "mobile":"0412345678",
                "tutor":False
            })
        data = register.json()
        token = data["token"]
        res = client.post("/users/login", json={
                "email":"john@example.com",
                "password":"Password123",
            })
        assert res.status_code == 400

    def test_login_incorrect_email(self, client):
        register = client.post(
            "/users/register", 
            json={
                "first_name":"John",
                "last_name":"Doe",
                "email":"john@example.com",
                "password":"Password123_",
                "mobile":"0412345678",
                "tutor":False
            })
        data = register.json()
        token = data["token"]
        res = client.post("/users/login", json={
                "email":"jimmy@example.com",
                "password":"Password123_",
            })
        assert res.status_code == 400