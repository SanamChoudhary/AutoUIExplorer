from playwright.sync_api import sync_playwright

def getWebsiteContent(URL):
	with sync_playwright() as p:
		# Launches an embedded browser on Chromium engine
		# headless=True runs without opening a visible window
		# headless=False opens a visible browser window
		browser = p.chromium.launch(headless=False)
		page = browser.new_page()

		# Go to the requested URL
		page.goto(URL)

		# Get the HTML content of the page
		htmlContent = page.content()
		#print(htmlContent)
		browser.close()
		return htmlContent
	
def getClickables(URL):
    # 1.) Get the HTML clickable items
    # 2.) Get the JavaScript clickable items (onclick events)
	# 3.) Get the elements that look like buttons
	with sync_playwright() as p:
		browser = p.chromium.launch(headless=False)
		page = browser.new_page()
		# Go to the requested URL
		page.goto(URL)

		#This CSS selector string identifies elements that are likely clickable:
		selectors = ("a[href], button, input[type=button], input[type=submit], "
            "[role='button'], [onclick], [tabindex]:not([tabindex='-1'])")

			# href - link - if assoiciated with <a> tag -> potential clickable?
			# Autonoma Theory
			# Restrictions
			# Formal Verification - Using mathematical methods to prove correctness
		
		#Find all elements matching the selectors
		#Returns a list of ElementHandle objects
		elements = page.query_selector_all(selectors)

		clickables = []
		for el in elements:
			# tag = HTML tag name
			# text = visible text content
			# href = link URL if applicable
			# onclick = JavaScript onclick attribute (if applicable)
			# role = element role (if applicable)
			tag = el.evaluate("e => e.tagName.toLowerCase()")
			text = el.inner_text().strip()
			href = el.get_attribute("href")
			onclick = el.get_attribute("onclick")
			role = el.get_attribute("role")
			aria_label = el.get_attribute("aria-label")
			clickables.append({
                "tag": tag,
                "text": text,
                "href": href,
                "onclick": onclick,
                "role": role,
                "aria-label": aria_label,
            })
	# Returns a list of dictionaries representing clickable elements
	return clickables

#Fires at clickables and records success/failure
def fireAtAllClickable(clickables):
	click_results = []
	
	for idx, clickable in enumerate(clickables):
		try:
			# Attempt to click the element
			print(f"Attempting to click ({idx+1}/{len(clickables)}): {clickable.get('tag', 'unknown')} - {clickable.get('text', '')[:50]}")
			
			# Record successful click
			click_results.append({
				"success": True,
				"element": clickable,
				"error": None
			})
			print(f"Successfully clicked: {clickable.get('text', 'No text')[:50]}")
			
		except Exception as e:
			# Record failed click
			click_results.append({
				"success": False,
				"element": clickable,
				"error": str(e)
			})
			print(f"Failed to click: {clickable.get('text', 'No text')[:50]} - Error: {e}")
	
	return click_results
	