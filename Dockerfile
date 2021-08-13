FROM python:slim

RUN useradd math_app

WORKDIR /home/PersonalProjects/math_app

COPY requirements.txt requirements.txt
RUN python -m venv venv
RUN venv/bin/pip install -r requirements.txt
RUN venv/bin/pip install gunicorn

COPY app app
COPY migrations migrations
COPY math_app.py config.py boot.sh ./
RUN chmod a+x boot.sh

ENV FLASK_APP math_app.py

RUN chown -R math_app:math_app ./
USER math_app

EXPOSE 5000
ENTRYPOINT ["./boot.sh"]