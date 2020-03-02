FROM python:3.8
ADD . /code
WORKDIR /code
RUN pip install --upgrade pip
RUN pip3 install -r requirements.txt
RUN ln -s /usr/local/lib/python3.8/site-packages/ntc_templates/templates/ backend/plugins/ntc-templates
CMD python3 netpalm.py