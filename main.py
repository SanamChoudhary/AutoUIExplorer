import knowledge_Graph as kg
import website_Interact as wi
from urllib.parse import urljoin

URL = input("Enter the URL of the website: ")

#print(eb.findClickables(URL))

allClickables = wi.getClickables(URL)
print(f"Found {len(allClickables)} clickable elements on {URL}")

# Create a graph node for the initial page
source_node = kg.addNode(URL, len(allClickables))

# Pick the first clickable with an href
next_clickable = next((c for c in allClickables if c.get("href")), None)

if not next_clickable:
	print("No clickable with an href found to follow.")
else:
	next_url = urljoin(URL, next_clickable.get("href"))
	next_clickables = wi.getClickables(next_url)
	print(f"After clicking, found {len(next_clickables)} clickables on {next_url}")

	# Create node for destination page and add edge
	target_node = kg.addNode(next_url, len(next_clickables))
	kg.addEdge(source_node, target_node, label=(next_clickable.get("text") or next_url))

	print("Graph updated: added nodes and edge for navigation.")