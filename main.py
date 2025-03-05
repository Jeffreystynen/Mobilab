from app import create_app
from flask import Flask
from dotenv import load_dotenv


# load_dotenv()  
app = create_app()
# app.secret_key = env.get("APP_SECRET_KEY")

if __name__ == "__main__":
    app.run(debug=True)
