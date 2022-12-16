FROM python:3.10.0a6-buster
COPY ./requirements.txt /app/requirements.txt
WORKDIR /app
# RUN apt update
# RUN apt -qq -y install python3
# RUN apt install python3
# RUN python3 -m pip install pip
RUN pip install -r requirements.txt
COPY . /app
COPY . .
ENTRYPOINT [ "python" ]
CMD ["evaluate.py"]