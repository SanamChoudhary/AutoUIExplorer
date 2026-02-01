import knowledge_Graph as kg
import website_Interact as wi
from urllib.parse import urljoin

URL = input("Enter the URL of the website: ")

#print(eb.findClickables(URL))

allClickables = wi.getClickables(URL)
print(f"Found {len(allClickables)} clickable elements on {URL}")

#print(allClickables)
# Create a graph node for the initial page
source_node = kg.addNode(URL, len(allClickables))


running = True
while running:
	# Pick the first clickable with an href

	for c in allClickables:
		#link = c.get("href")
		if c.get("href") is not None:
			next_clickable = c.get("href")
		else:
			next_clickable = None

		print(f"Next clickable selected: {next_clickable}")

		if next_clickable == None:
			print("No more clickable elements with href found. Stopping navigation.")
			running = False
		else:
		#next_url = urljoin(URL, next_clickable.get("href"))
		#next_clickables = wi.getClickables(next_url)
		
			next_clickable.click()
			print(f"After clicking, found {len(next_clickables)} clickables on {next_url}")

			# Create node for destination page and add edge
			target_node = kg.addNode(next_url, len(next_clickables))
			kg.addEdge(source_node, target_node, label=(next_clickable.get("text") or next_url))

			print("Graph updated: added nodes and edge for navigation.")
