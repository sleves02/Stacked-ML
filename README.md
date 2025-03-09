# Stacked-ML
DML-OpenProblem is an open-source repository of problems focused on linear algebra, machine learning, and deep learning. The problems are designed to be solved from scratch, providing a robust learning experience. This project powers the website Deep-ML.

Table of Contents
Installation
Usage
Project Structure
Contributing
How to Add an Interactive Learn for a Problem
How to Add C++ Questions
License
Installation
To get started with DML-OpenProblem, clone the repository and install the necessary dependencies.

git clone https://github.com/yourusername/DML-OpenProblem.git
cd DML-OpenProblem
pip install -r requirements.txt
Usage
You can use the repository to create, edit, and solve problems related to linear algebra, machine learning, and deep learning. The problems are structured in directories, each containing relevant files such as learn.html for the learning section and solution.py for the solution code.

Running the Streamlit App
To launch the Streamlit application for editing and viewing problems, use the following command:

streamlit run app.py
Features
Problem Editor: Edit the learn.html and solution.py files for each problem using a web-based code editor.
Preview Section: Preview the learning section with LaTeX rendering for mathematical expressions.
Save Changes: Save your edits to the corresponding files in the repository.
Project Structure
DML-OpenProblem/
│
├── Problems/
│   ├── 1_matrix_times_vector/
│   │   ├── learn.md
│   │   └── solution.py
│   ├── 2_transpose_matrix/
│   │   ├── learn.md
│   │   └── solution.py
│   └── ... (additional problem directories)
│
├── app.py
├── requirements.txt
└── README.md
Problems/: Contains directories for each problem. Each directory includes:
learn.md: markdown file containing the learning section with explanations and examples.
solution.py: Python file containing the solution to the problem along with tests.
requirements.txt: Lists the dependencies required for the project.
README.md: This file.
Contributing
We welcome contributions to improve DML-OpenProblem and deep-ml.com. If you have a new problem to add or improvements to existing problems, please fork the repository and submit a pull request. All contributions will be displayed on deep-ml.com. For example, check out this problem: Divide Dataset Based on Feature Threshold. A helpfull tool to work on the learn section and know what it would look like on the front end is https://openproblem-r4vsjwuthdl9a3qzrd4p3m.streamlit.app/. Also here is an example of a learn section writing in markdown Example Problem

Steps to Contribute
Fork the repository.
Create a new branch for your feature or bugfix.
Make your changes and commit them with clear and concise messages.
Push your changes to your fork.
Submit a pull request with a detailed description of your changes.
Steps to add a Problem
create an issue, the issue should describe the problem you would like to create and use the label "New Problem"
comment below the issue you would like to work on
We will assign the issue and let you know what number problem to make it
How to Add a Video Solution (Optional)
Create a Comprehensive Video Solution:
Your video should clearly explain the concept and provide a step-by-step solution to the problem. Feel free to include additional elements that enhance understanding, such as animations, hand-written examples, or any other visual aids that will help clarify the topic.

Upload the Video to YouTube:
Once your video is ready, upload it to YouTube. Make sure the video is accessible and properly titled.

Include a Link to the Problem:
In the video description, add a link to the corresponding problem on Deep-ML so that viewers can easily access and try solving the problem themselves.

Submit the Video Link:
In the corresponding problem folder, create a .txt file containing the link to your YouTube video. This will help us easily reference your solution.

How to Add an Interactive Learn for a Problem (Optional)
Create a Problem Folder: Navigate to the Problems/interactive_learn/ directory and create a folder named problem-N, where N is the problem number assigned to you (e.g., problem-17).

Add Learning Materials: Inside the folder, create a notebook.py file. This file should include the learning content with explanations, examples, and any required resources for the problem. You could use https://marimo.app/?slug=aojjhb to ensure the file is compatible with marimo for HTML-WASM conversion. For example, you can check problem-4's notebook.py

Submit Changes: Commit the new folder with its contents to your branch and submit a pull request. Ensure your commit messages clearly indicate the addition of the interactive learn for the problem.

Collaborate for Review: Engage with reviewers for feedback on your pull request. Make any necessary adjustments as suggested.

How to Add C++ Questions
We are adding C++ support to the problem set, and you can contribute C++ solutions following these guidelines.

Steps to Add a C++ Solution
Select a problem from the existing Python-based problems.
Create a C++ solution file inside the corresponding problem folder, naming it solution.cpp.
Follow the C++ coding guidelines:
Use C++17 or later.
Prefer Eigen for matrix operations (or xtensor-blas if necessary).
Ensure well-structured, readable, and modular code.
Keep solutions self-contained and avoid unnecessary external dependencies.
Format numerical outputs to 4 decimal places for consistency.
Test your solution to ensure correctness.
Submit a pull request with a detailed explanation of your solution.
C++ Coding Rules
Use Eigen for matrix computations where applicable.
Avoid excessive STL usage unless necessary for clarity.
Prefer pass-by-reference over pass-by-value to improve performance.
Ensure error handling without crashing the program.
Keep solutions deterministic and efficient.
If you have any questions about library choices or implementation details, feel free to start a discussion in the GitHub issues section.

License
This project is for educational reasons only. See the LICENSE file for details.
