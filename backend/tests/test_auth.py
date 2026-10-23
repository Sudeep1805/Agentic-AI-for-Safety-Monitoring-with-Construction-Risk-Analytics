def test_signup_login_profile_and_logout(client):
    client.headers.pop("Authorization")
    signup = client.post("/api/auth/signup", json={
        "email": "worker@example.com", "full_name": "Site Worker", "password": "correct horse battery"
    })
    assert signup.status_code == 201
    body = signup.json()
    assert body["user"]["email"] == "worker@example.com"
    assert body["access_token"]

    token = body["access_token"]
    profile = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert profile.status_code == 200
    assert profile.json()["full_name"] == "Site Worker"

    assert client.post("/api/auth/login", json={
        "email": "worker@example.com", "password": "wrong password"
    }).status_code == 401
    logged_in = client.post("/api/auth/login", json={
        "email": "WORKER@example.com", "password": "correct horse battery"
    })
    assert logged_in.status_code == 200

    assert client.post("/api/auth/logout", headers={"Authorization": f"Bearer {token}"}).status_code == 204
    assert client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"}).status_code == 401


def test_signup_rejects_duplicate_email(client):
    client.headers.pop("Authorization")
    payload = {"email": "duplicate@example.com", "full_name": "Worker", "password": "password123"}
    assert client.post("/api/auth/signup", json=payload).status_code == 201
    assert client.post("/api/auth/signup", json=payload).status_code == 409
    assert client.get("/api/auth/me").status_code == 401


def test_uploads_are_not_visible_across_accounts(client):
    upload = client.post("/api/uploads", files={"file": ("site.png", b"not-an-image", "image/png")})
    assert upload.status_code == 422
    # Authenticate a second account and verify the first account's list remains isolated.
    client.headers.pop("Authorization")
    first = client.post("/api/auth/signup", json={
        "email": "owner@example.com", "full_name": "Owner", "password": "owner-password"
    })
    assert first.status_code == 201
    client.headers.update({"Authorization": f"Bearer {first.json()['access_token']}"})
    from io import BytesIO
    from PIL import Image
    image = BytesIO()
    Image.new("RGB", (4, 4), "green").save(image, "PNG")
    saved = client.post("/api/uploads", files={"file": ("owned.png", image.getvalue(), "image/png")})
    assert saved.status_code == 201
    upload_id = saved.json()["id"]
    client.headers.pop("Authorization")
    second = client.post("/api/auth/signup", json={
        "email": "other@example.com", "full_name": "Other", "password": "other-password"
    })
    client.headers.update({"Authorization": f"Bearer {second.json()['access_token']}"})
    assert client.get("/api/uploads").json() == {"items": [], "total": 0}
    assert client.get(f"/api/uploads/{upload_id}").status_code == 404
    assert client.get(f"/api/uploads/{upload_id}/image").status_code == 404
