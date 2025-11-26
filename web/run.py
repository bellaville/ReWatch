from app import create_app

# file to run the application, no configuration should be present
app = create_app()

if __name__ == "__main__":
    app.run(debug=True)


