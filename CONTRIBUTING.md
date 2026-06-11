# Contributing to PocketDev

Thank you for your interest in contributing to **PocketDev**! As an open-source project, we welcome contributions of all kinds—whether it is reporting a bug, suggesting a feature, or writing code to improve the agent.

To ensure a smooth collaboration, please follow the guidelines below.

---

## 1. Code of Conduct

We expect all contributors to maintain a respectful, welcoming, and professional environment. Please be supportive and polite in all issues, merge requests, and discussion threads.

---

## 2. How to Contribute

### 2.1. Reporting Bugs & Feature Requests
* Search the existing Issues list first to see if the topic has already been discussed.
* If not, create a new GitLab Issue describing the bug or feature request in detail.
* For bugs, please include:
  * Steps to reproduce the bug.
  * Expected vs actual behavior.
  * Logs or error outputs.

### 2.2. Submitting Code Changes (Merge Requests)
1. **Fork the Repository:** Create a copy of this repository under your personal GitLab space.
2. **Create a Feature Branch:** Branch out from the `main` branch with a descriptive name:
   ```bash
   git checkout -b feature/your-awesome-feature
   # or
   git checkout -b bugfix/fix-some-bug
   ```
3. **Write and Test Code:** Apply your changes. Ensure you adhere to pythonic code style (PEP 8) and document any new functions.
4. **Run Local Tests:** Before pushing, always run the test suite to ensure everything passes:
   ```bash
   python -m unittest discover -s tests
   ```
5. **Commit and Push:** Write clear, concise commit messages. Push your branch to your GitLab fork.
6. **Open a Merge Request:** Submit a Merge Request back to the main `PocketDev` repository. Provide a thorough description of the changes and link any relevant Issues.

---

## 3. Coding Guidelines

* **Python Standard:** Write code compatible with Python 3.10+.
* **Code Style:** We follow PEP 8 formatting. Use clear, descriptive names for variables, classes, and functions.
* **Docstrings:** All new modules, tools, and endpoints must include clear Google-style docstrings describing parameters, return values, and behavior.
* **Imports:** Keep imports clean and organized. Avoid wildcard imports (`from module import *`).
