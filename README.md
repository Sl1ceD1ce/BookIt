# BookIt

BookIt is a full stack booking and scheduling platform designed to simplify resource management and appointment scheduling. The project was developed as a collaborative software engineering project with a focus on backend development, authentication, testing, CI/CD, and modern development workflows.

The platform allows users to create accounts, manage bookings, schedule resources, and interact with a secure REST API. The project was built using a scalable backend architecture with containerised services and automated testing workflows.

This is the backend repository for BookIt.
---

# Features

* User authentication and authorisation using JWT
* Secure protected API routes and middleware validation
* Booking and scheduling management system
* RESTful API architecture
* PostgreSQL database integration
* Docker containerisation for consistent development environments
* Automated testing using Pytest
* CI/CD pipelines with GitHub Actions
* Request validation and error handling
* Collaborative team based development workflow

---

# Tech Stack

## Backend

* Python
* FastAPI
* PostgreSQL
* SQLAlchemy

## DevOps and Infrastructure

* Docker
* GitHub Actions
* CI/CD Pipelines

## Testing

* Pytest

## Tools

* Git
* GitHub

---

# Architecture Overview

BookIt follows a modular backend architecture designed to separate concerns between routing, business logic, authentication, and database management.

Core components include:

* API routes for handling booking and authentication requests
* Middleware for JWT authentication and request validation
* PostgreSQL database for persistent data storage
* Docker based container setup for local development consistency
* Automated GitHub Actions workflows for testing and quality checks

---

# Testing

Automated backend testing was implemented using Pytest to improve application reliability and reduce regressions during development.

Tests include:

* Authentication flow testing
* API endpoint validation
* Request and response handling
* Database interaction testing
* Error handling validation

Testing workflows were integrated into CI/CD pipelines using GitHub Actions.

---

# Running the Project Locally

## Prerequisites

* Python 3.x
* Docker
* PostgreSQL
* Git

## Installation

Clone the repository:

```bash
git clone <repository-url>
cd bookit
```

Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

...

---

# Team Collaboration

BookIt was developed in a collaborative team environment using Git and GitHub workflows.

The project involved:

* Pull request reviews
* Collaborative debugging
* Feature branch workflows
* Agile style task coordination
* Technical discussions and feedback

---

# Future Improvements

Potential future improvements include:

* Frontend deployment and live hosting
* Real time notifications
* Role based access control
* Cloud deployment using AWS
* Monitoring and logging
* Improved scalability and performance optimisation

---

# License

This project was created for educational and portfolio purposes.
