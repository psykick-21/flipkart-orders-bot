# Flipkart Order Scraping AI Agent

All the dependencies are mentioned in the requirements.txt file.

## Setup instructions
Create a new python environment for this code. 

Creating python environment using conda:<br>
Navigate to the code directory in the terminal, and run the command `conda create -p venv python=3.11 -y`.

Install the dependencies using the command `pip install -r requirements.txt` in the terminal.

One of the dependencies of this project is Playwright. Once it is install using pip, run the command `install playwright` in the terminal.

## Setup environment variables

Setup the OPENAI_API_KEY and LANGCHAIN_API_KEY in the .env file.

## Running the Agent

Run the `app.py` file in the terminal from the project directory.<br>
One human intervention is needed to login to the Flipkart website. Reason for it is given in the challenges section of the documentation.

---
Detailed documentation including the overview, system design and diagrams can be found [here](https://docs.google.com/document/d/12VsqgyVd4iGvve78hKvJRbq5BtOAQOSOXXqgtVt4xdk/edit#heading=h.12y46exap77x)

>**The orders extracted by the AI Agent can be seen in the `flipkart-orders.json` file.**

