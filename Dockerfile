FROM python:3.10-buster

RUN mkdir -p /home/property-web

RUN apt update && apt upgrade -y

COPY requirements.txt /home/property-web/requirements.txt

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install -r /home/property-web/requirements.txt

COPY classes /home/property-web/classes/
COPY all_auth /home/property-web/all_auth/
COPY property_project /home/property-web/property_project/
COPY property_app /home/property-web/property_app/

COPY *.py /home/property-web/
COPY .env /home/property-web/.env

# Set working directory
WORKDIR /home/property-web/

EXPOSE 5000

CMD ["python", "manage.py", "runserver", "0.0.0.0:5000"]
