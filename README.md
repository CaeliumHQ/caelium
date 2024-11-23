# Caelium

**Caelium** is a multifunctional social environment app designed to build a robust social ecosystem with advanced features such as chat systems, task management, AI integrations, and more.

This repository contains the **backend code** for Caelium, which is built using **Django** and **Django REST Framework (DRF)**. It integrates with **Google Cloud** and other essential third-party services to deliver a seamless user experience.

## Project Information

- **Project Name:** Caelium
- **Tech Stack:** Django, Python, Django REST Framework (DRF)
- **Purpose:** Backend for Caelium, a social platform with AI and ML features designed to enable social interactions, task management, and more.

## Documentation

- [Organization Docs](https://github.com/CaeliumHQ)  
  For an in-depth overview of the Caelium project and its architecture, refer to the organization's documentation.

---

## Getting Started

Follow these steps to set up the backend on your local machine. This guide is suitable for both Windows and Unix-based systems (Linux/MacOS).

### 1. Fork the Repository

Start by forking the repository to your GitHub account. This allows you to freely experiment with the code and contribute back through pull requests.

```bash
git clone https://github.com/your-username/caelium.git
cd caelium
```

### 2. Set Up the Virtual Environment

A virtual environment is essential to manage project dependencies and avoid conflicts with global Python packages. Set it up using the following commands:

- **For Unix-based systems (Linux/MacOS):**

```bash
python3 -m venv venv
source venv/bin/activate
```

- **For Windows:**

```bash
python -m venv venv
.\venv\Scripts\activate
```

Once the virtual environment is activated, you'll notice the terminal prompt changes, indicating that the environment is ready for use.

### 3. Set Up Environment Variables

Next, configure the environment variables for your local setup. We’ve provided a sample `.env.sample` file containing all the necessary variables.

1. Copy `.env.sample` to `.env`:

```bash
cp .env.sample .env
```

2. Open the `.env` file and update the values for the following variables:

   - `DJANGO_SECRET_KEY`: A random secret key for your Django app.
   - `CLIENT_HOST`: The URL for your frontend client (e.g., `http://localhost:3000`).
   - `env`: Set this to `dev` during development.
   - `GOOGLE_CLIENT_ID`: Your Google Client ID for OAuth authentication.
   - `GOOGLE_CLIENT_SECRET`: Your Google Client Secret for OAuth authentication.
   - `media_url`: The base URL for media storage, typically `/media/`.
   - `DEBUG`: Set to `True` during development.

**Note:** To run the app with full functionality, you must set up the required APIs such as OAuth authentication and Google Photos APIs. Documentation on setting up these services will be provided later.

### 4. Install Dependencies

After setting up the environment, install the required dependencies:

```bash
pip install -r requirements.txt
```

This will install all the necessary packages to run the backend.

### 5. Run Migrations

Django uses migrations to apply changes made to models in the database. To set up your database schema, run the following commands:

```bash
python manage.py makemigrations accounts base chats crafts
python manage.py migrate
```

These commands will apply migrations for the **accounts**, **base**, **chats**, and **crafts** apps in your project.

### 6. Create a Superuser

To access the Django admin panel, you’ll need to create a superuser account. Run the following command and follow the prompts:

```bash
python manage.py createsuperuser
```

Enter your username, email, and password when prompted.

### 7. Run the Development Server

Finally, start the development server to see the app in action:

```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000/` in your browser to check if the backend is running.

To access the Django Admin panel, go to `http://127.0.0.1:8000/admin` and log in with the superuser credentials you created earlier.

---

## Contributing

We welcome contributions from the open-source community. To get started, follow these steps:

1. **Fork the repository** to your GitHub account.
2. **Clone your fork** to your local machine.
3. **Create a new branch** for your feature or bug fix:

   ```bash
   git checkout -b feature/my-new-feature
   ```

4. **Make changes** to the codebase and commit them:

   ```bash
   git commit -m "Add new feature"
   ```

5. **Push your changes** to your fork:

   ```bash
   git push origin feature/my-new-feature
   ```

6. **Create a pull request** with a description of what you've changed and why.

Please refer to our [contributing guidelines](https://github.com/CaeliumHQ/.github/blob/main/CONTRIBUTING.md) for more detailed instructions and best practices.

---

## License

This project is distributed under the **GNU Affero General Public License (AGPL)**. See the [LICENSE](LICENSE) file for more details.

---

## Contact

For any questions or issues related to the project, feel free to create an issue in the repository or reach out to us at [contact@caelium.co](mailto:contact@caelium.co).
