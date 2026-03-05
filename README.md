# Tennis Court Booking App

SetPoint is a full-stack Django web application that allows users to book tennis courts online. The platform includes user authentication, real-time court availability, booking management, and Stripe payment integration.

![SetPoint Logo](core\static\core\images\SetPoint_logo.png)

## Repository Links

- GitHub Repository: [Repo](https://github.com/steff657/Hackathon-Project-2)
- Live Site: [SetPoint](https://set-point-a25bf5f77a69.herokuapp.com/)
- Project Board: [Project Board](https://github.com/users/steff657/projects/8)

## Table Of Contents:

1. [Contributors](#contributors)
2. [Overview](#overview)
3. [Key Features](#key-features)
4. [Tech Stack](#tech-stack)
5. [Design & Planning](#design--planning)

- [User Stories](#user-stories)
- [Wireframes](#wireframes)
- [Agile Methodology](#agile-methodology)
- [Typography](#typography)
- [Colour Scheme](#colour-scheme)
- [Database Diagram](#database-diagram)

6. [Features](#features)

- [Navigation](#navigation)
- [Footer](#footer)
- [Home-page](#home-page)
- [Add your pages](#add-your-pages)
- [CRUD](#crud)
- [Authentication-Authorisation](#authentication-authorisation)

7. [Technologies Used](#technologies-used)
8. [Libraries Used](#libraries-used)
9. [Testing](#testing)
10. [Bugs](#bugs)
11. [Deployment](#deployment)
12. [AI](#ai)
13. [Credits](#credits)

## Contributors

- `<Steffan>` - `<https://github.com/steff657>`
- `<Hamza>` - `<https://github.com/hamza-m1>`
- `<Hannah>` - `<https://github.com/hannahashe>`
- `<Leila>` - `<https://github.com/leilacsak>`

## Overview

SetPoint is a Django-based tennis court booking platform built for a team hackathon.  
 Users can discover available courts, book time slots, pay securely, and manage their bookings from a personal dashboard.

The app supports the full booking lifecycle:

- browse courts by date and surface
- create and edit bookings
- complete payment through Stripe Checkout
- cancel bookings
- save favourite court/date/time slots for quick rebooking
- contact support for refund-related requests

## Key Features

- **Court availability view** with date and surface filtering
- **Booking flow** with conflict prevention and maintenance-window checks
- **My Bookings dashboard** with upcoming/past sections and booking actions
- **Payment tracking** (`pending`, `paid`, `cancelled`, `refunded`)
- **Saved/Bookmarked slots** with one-click rebook links
- **Support contact form** linked to optional booking context
- **Admin tools** for booking management and refund handling

## Tech Stack

- Python 3.12
- Django 6
- django-allauth (authentication)
- Stripe (payments/webhooks)
- Bootstrap 5
- HTML/CSS
- SQLite (dev) / configurable database for deployment

## Design & Planning:

### User Stories

Write your user stories in this section.

### Wireframes

Attach wireframes in this section.

### Agile Methodology

Explain your agile approach to your project and insert screenshots of your Kanban board (iterations, user stories, tasks, acceptance criteria, labels, story points).

### Typography

Explain the font you've used for your project.

### Colour Scheme

Screenshot of the colour scheme for your project.

### Database Diagram

Image of the database diagram for your project, including your database models and how they are connected.

## Features:

Explain your features on the website (navigation, pages, links, forms, input fields, CRUD).

### Navigation

### Footer

### Home-page

### Add your pages

### CRUD

### Authentication-Authorisation

## Technologies Used

List of technologies used for your project.

Current stack:

- Python 3.12
- Django 6.0.2
- django-allauth 65.14.3
- HTML5
- CSS3
- Bootstrap 5

## Libraries Used

List all libraries/packages used for your project.

## Testing

Important part of your README.

### Google's Lighthouse Performance

Screenshots of certain pages and scores (mobile and desktop).

### Browser Compatibility

Check compatibility with different browsers.

### Responsiveness

Screenshots of the responsiveness, pick a few devices.

### Code Validation

Validate your code (HTML, CSS, JS, and Python) for all pages/files and display screenshots.

### Manual Testing user stories

Test all your user stories. You can create a table:

| User Story                 | Test                                                            |  Pass   |
| -------------------------- | --------------------------------------------------------------- | :-----: |
| paste here your user story | what is visible to the user and what action they should perform | &check; |

Attach screenshot.

### Manual Testing features

Test all your features, you can use the same approach:

|   Feature   | Action     | Status  |
| :---------: | :--------- | :------ |
| description | user steps | &check; |

Attach screenshot.

## Bugs

List bugs and how you fixed them.

## Deployment

This website is deployed to Heroku from a GitHub repository, the following steps were taken:

#### Creating Repository on GitHub

- First make sure you are signed into [GitHub](https://github.com/) and go to the Code Institute template, which can be found [here](https://github.com/Code-Institute-Org/gitpod-full-template).
- Then click on **Use this template** and select **Create a new repository** from the drop-down. Enter the name for the repository and click **Create repository from template**.
- Once the repository was created, click the green **Gitpod** button to create a workspace in Gitpod so that you can write the code for the site.

#### Creating an app on Heroku

- After creating the repository on GitHub, head over to [Heroku](https://www.heroku.com/) and sign in.
- On the home page, click **New** and **Create new app** from the drop-down.
- Give the app a name (this must be unique) and select a **region**. Then click **Create app**.

#### Create a database

- Log into [CI Database Maker](https://dbs.ci-dbs.net/).
- Add your email address in the input field and submit the form.
- Open the database link in your email.
- Paste the database URL in your `DATABASE_URL` variable in `env.py` and in Heroku config vars.

#### Deploying to Heroku

- Head back over to [Heroku](https://www.heroku.com/) and click on your **app** then go to the **Settings** tab.
- On the **Settings** page, scroll down to the **Config Vars** section and enter:
  - `DATABASE_URL`
  - `SECRET_KEY`
  - `CLOUDINARY_URL`
  - `PORT` set to `8000`
- Then scroll to the top and go to the **Deploy** tab.
- In **Deployment method**, select **GitHub** and sign into your account.
- In **Search for a repository to connect to**, enter your repository name and click **Connect**.
- In **Manual Deploy**, click **Deploy Branch**. Once deployed, click **View app**.
- Note: when deploying manually, you will need to deploy after each change.

## AI

- Explain the usage of AI in your project (features, bugs, etc.).

## Credits

List resources used for your website (text, images, code snippets, projects).

### Project Structure

```text
booking_app/                  # Django project config
core/
  forms.py                    # Booking form
  models.py                   # Booking model
  urls.py                     # App routes
  views.py                    # View functions
  templates/core/             # HTML templates
  static/core/styles.css      # Shared CSS
wireframes/                   # SVG and PNG wireframes
docs/
  kanban_user_story_template.md
```

### Setup and Run

```powershell
.\.venv\booking_app\Scripts\python.exe manage.py migrate
.\.venv\booking_app\Scripts\python.exe runserver
```

Open: `http://127.0.0.1:8000/`

### Acknowledgments

- Django documentation
- Bootstrap documentation
- Team contributors and reviewers
