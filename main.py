from webhook import app

if __name__ == "__main__":
    # Dynamically set the port using environment variable or default to 3000 for local development
    port = int(os.environ.get("PORT", 3000))  # Defaults to 3000 if not set
    app.run(host="0.0.0.0", port=port, debug=True)
