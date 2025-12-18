from playwright.sync_api import sync_playwright


URL = input("Enter the URL of the website: ")
# Use the synchronous context manager to start Playwright
with sync_playwright() as p:
	# Launches an embedded browser on Chromium engine
	# headless=True runs without opening a visible window
	browser = p.chromium.launch(headless=False)
	page = browser.new_page()

	# Go to the requested URL
	page.goto(URL)

	print(page.title())

	browser.close()
