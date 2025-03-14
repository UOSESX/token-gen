# main.py

import requests
import random
import string
import threading
import time
from playwright.sync_api import sync_playwright

# Load proxies from proxies.txt
def load_proxies():
    with open('proxies.txt', 'r') as file:
        proxies = file.read().splitlines()
    return proxies

# Generate a random username
def generate_username():
    adjectives = ['Crazy', 'Rebel', 'Genius', 'Wild', 'Savage', 'Epic']
    nouns = ['Hacker', 'Coder', 'Dev', 'Gamer', 'Bot', 'Legend']
    return f"{random.choice(adjectives)}_{random.choice(nouns)}_{random.randint(1000, 9999)}"

# Generate a random email
def generate_email():
    domains = ['gmail.com', 'yahoo.com', 'outlook.com', 'protonmail.com']
    return f"{''.join(random.choice(string.ascii_lowercase) for _ in range(8))}@{random.choice(domains)}"

# Generate a random password
def generate_password():
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(characters) for _ in range(12))

# Solve CAPTCHA using CapMonster
def solve_captcha(api_key, site_key, url):
    capmonster_url = "https://api.capmonster.cloud/createTask"
    task_payload = {
        "clientKey": api_key,
        "task": {
            "type": "HCaptchaTaskProxyless",
            "websiteURL": url,
            "websiteKey": site_key
        }
    }
    response = requests.post(capmonster_url, json=task_payload)
    task_id = response.json().get("taskId")
    if not task_id:
        print("Failed to create CAPTCHA task.")
        return None

    # Wait for CAPTCHA solution
    result_url = "https://api.capmonster.cloud/getTaskResult"
    while True:
        time.sleep(5)  # Wait 5 seconds before checking
        result_response = requests.post(result_url, json={"clientKey": api_key, "taskId": task_id})
        result = result_response.json()
        if result.get("status") == "ready":
            return result.get("solution", {}).get("gRecaptchaResponse")
        elif result.get("status") == "processing":
            continue
        else:
            print("CAPTCHA solving failed.")
            return None

# Extract fingerprint using Playwright
def get_fingerprint():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)  # Run in headless mode
        page = browser.new_page()
        page.goto('https://discord.com/register')
        
        # Wait for the page to load and trigger a request
        page.wait_for_timeout(5000)
        
        # Extract fingerprint from network requests
        fingerprint = page.evaluate('''() => {
            return fetch("https://discord.com/api/v9/auth/location-metadata")
                .then(response => response.headers.get("x-fingerprint"));
        }''')
        
        browser.close()
        return fingerprint

# Create a Discord account and retrieve the token
def create_discord_account(proxy, capmonster_key):
    try:
        # Generate account details
        username = generate_username()
        email = generate_email()
        password = generate_password()

        # Solve CAPTCHA
        site_key = "f5561ba9-8f1e-40ca-9b5b-a0b3f719ef34"  # Discord's hCaptcha site key
        captcha_token = solve_captcha(capmonster_key, site_key, "https://discord.com/register")
        if not captcha_token:
            print("Failed to solve CAPTCHA.")
            return

        # Get fingerprint using Playwright
        fingerprint = get_fingerprint()
        if not fingerprint:
            print("Failed to extract fingerprint.")
            return

        # Discord API endpoint for account creation
        url = 'https://discord.com/api/v9/auth/register'
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'X-Fingerprint': fingerprint
        }
        payload = {
            'username': username,
            'email': email,
            'password': password,
            'consent': True,
            'fingerprint': fingerprint,
            'captcha_key': captcha_token
        }

        # Send the request using a proxy
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            proxies={'http': proxy, 'https': proxy},
            timeout=10
        )

        if response.status_code == 200:
            # Extract the token from the response
            token = response.json().get('token')
            if token:
                print(f'Account created successfully! Token: {token}')
                save_token(token)
            else:
                print('Failed to retrieve token from response.')
        else:
            print(f'Failed to create account. Status Code: {response.status_code}, Response: {response.text}')
    except Exception as e:
        print(f'Error creating account: {e}')

# Save token to token.txt
def save_token(token):
    with open('token.txt', 'a') as file:
        file.write(token + '\n')

# Main function to create accounts
def main():
    proxies = load_proxies()
    if not proxies:
        print('No proxies found in proxies.txt')
        return

    capmonster_key = "2e02f654b44bbf4049589aefeaaebd1a"  # Replace with your CapMonster API key

    while True:
        proxy = random.choice(proxies)
        threading.Thread(target=create_discord_account, args=(proxy, capmonster_key)).start()

if __name__ == '__main__':
    main()
