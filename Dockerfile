FROM python:3.10-slim-buster
WORKDIR /app
COPY pyproject.toml pyproject.toml
RUN pip3 install -e .
COPY . .
CMD [ "python3", "-m" , "deboche-bot"]