# What you focused on and why
Extracting code form the main file and identifying responsibilities to group in components that could be reused, extended and interchanged.
It has the core logic, but it was (and still is) doing many things that could be delegated.

# Key design decisions you made
- Added a class with two responsibilities 
	- make the api request to a third party (helper method moved here)
	- extract the needed data from the response.
	- An interface was added to add more extraction mechanisms. 
	
- Moved the validation as a computed field in the data object.
- Tested with ChatGPT to check the result shape.
 
# What you would do next if you had more time
- Refactor the helper method moved into its component. It has a lot of nested loops that make it hard to understand and very complex. It for sure has a big big O.
- Define and add more data objects and leverage pydantic features (responses from api calls, DTOs)
- Decouple more the components.
- Separate in layers, maybe add a service layer for common operations on the data objects.
- Refactor the exceptions, maybe add the Result pattern to handle the errors. There are several antipatterns using exceptions as ctrl flow and not using sub-types.
 
# Any trade-offs or assumptions you made
An assumption was that the fixtures covered all the document data. 
The failing fixture was not complete.
Some mocks add some complexity to the tests, probably use of factory boy would make the code cleaner
The response from ChatGPT was not the expected one, so I spent some time cleaning and figuring out what was wrong when doing a live test.