FROM python:3.11

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

ENV PYHTONUNBUFFERED=1

RUN echo "Installing OS Packages"
# System installs
RUN apt-get clean && apt-get update

RUN echo "Installing Python Packages"
RUN python -m pip install pipenv

EXPOSE 80
EXPOSE 443

COPY ./app/backend/Pipfile /app/
COPY ./app/backend/Pipfile.lock /app/
WORKDIR /app
RUN pipenv install --system --deploy

COPY ./app/backend /app/

CMD ["python", "tasks.py"]