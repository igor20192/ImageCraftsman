# ImageCraftsman

ImageCraftsman is a Django web application that allows users to upload images, create thumbnails, and serve images with expiring links. It includes user authentication, different subscription plans, and more.

## Features

- User registration and authentication.
- Image upload with automatic thumbnail generation.
- Expire links for sharing images securely.
- Customizable subscription plans with different features.
- API endpoints for working with images and user profiles.

## Requirements

- Python 3.11+
- Django 4.0+
- Pillow (for image processing)
- Memcached (for caching)
- Other dependencies as specified in `requirements.txt`

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/igor20192/ImageCraftsman.git
   
2. ```bash
   cd ImageCraftsman

3. Check in and activate the Python virtual environment

   ```bash
   python3 -m venv env
   . env/bin/activate

4. Install the required dependencies:

   ```bash
   pip install -r requirements.txt

5. Run the migrations:

   ```bash
   python manage.py migrate

6. Create a superuser for the admin panel:

   ```bash
   python manage.py createsuperuser

7. Start the development server:

   ```bash
   python run_uvicorn.py

8. Access the admin panel at http://localhost:8000/admin/ and log in with your superuser credentials.

9. Access the API and web views at http://localhost:8000/upload.

## Docker Installation and Quick Start

1. Install Docker and Docker Compose on your system if you haven't already. You can download them from [https://www.docker.com/](https://www.docker.com/) and [https://docs.docker.com/compose/install/](https://docs.docker.com/compose/install/).

2. Clone the repository:

   ```bash
   git clone https://github.com/igor20192/ImageCraftsman.git

1. Create a .env file for your project configurations if it doesn't already       exist. You can use .env.example as a template.

2. Create a .env.db file for your PostgreSQL database configurations if it doesn't already exist. You can use .env.db.example as a template.

3. Build and start the Docker containers using Docker Compose:

   ```bash
   docker-compose up -d

4. Run the migrations:

   ```bash
   docker-compose exec web python manage.py makemigrations
   docker-compose exec web python manage.py migrate

5. Create a superuser for the admin panel:
 
    ```bash
    docker-compose exec web python manage.py createsuperuser

6. Access the application at http://localhost:8080/upload.

7. Access the admin panel at http://localhost:8080/admin/ and log in with your superuser credentials.

## Configuration

- Create a .env file in the project root and configure your environment variables. See .env.example for reference.

- Make sure Memcached is running and properly configured.

- Customize the subscription plans, image sizes, and other settings in your Django project settings.

## URL Patterns

Here are the URL patterns used in the project:

- **Upload Image**: Allows users to upload images.

  - URL: `/upload/`
  - View: `ImageCreateView`
  - Name: `upload-image`

- **User Detail**: Displays details about a user.

  - URL: `/user/<int:pk>/`
  - View: `UserDetailView`
  - Name: `user-detail`

- **Image Detail**: Retrieves detailed information about an image.

  - URL: `/image_detail/<int:pk>/`
  - View: `ImageDetailView`
  - Name: `image-detail`

- **Serve Image**: Serves images with expiring links.

  - URL: `/serve-image/<int:pk>/`
  - View: `ServeImageView`
  - Name: `serve_image`


## Usage

1. Sign up for an account.

2. Upload images with optional thumbnails.

3. Retrieve and serve images with expiring links.

4. Customize subscription plans and image sizes in the admin panel.


## Contact

If you have any questions or need assistance, feel free to contact us at igor.udovenko2015@gmail.com.

Happy coding!
