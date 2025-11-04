FROM python:3.13

WORKDIR /bot_vpn

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY . /bot_vpn


CMD ["python3", "bot_vpn.py"]
