FROM python:2

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ .

CMD [ "python", "manage.py", "runserver", "0.0.0.0:8000", "--insecure" ]
