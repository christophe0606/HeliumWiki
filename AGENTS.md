Use uv to run python script : `uv run myscript.py`
Ingest the document requested by the user to extend the helium wiki:
* Apply the analyze agent to the document to identify the optimization guidelines contained in the document
* For each document extract returned by the agent, apply the extractor agent that will generate wiki pages
* For each generated page, apply the validation python scripts/validate.py 
* The script is called with `uv run validate.py <path to wiki file> <path to output error file>` The error output file is a markdown file describing in detail the errors
* stop if no error is returned
* If an error is returned, give the path to the error file to the correction agent and validate again the file once the agent has applied some corrections
* Continue until there is no more any validation error
