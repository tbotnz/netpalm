FROM python:3.8
RUN cd /usr/local/lib/python3.8/site-packages
RUN git clone https://github.com/networktocode/ntc-templates.git
RUN mv ntc-templates ntc_templates
ADD . /code
WORKDIR /code
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt
RUN ln -sf /usr/local/lib/python3.8/site-packages/ntc_templates/templates/ backend/plugins/ntc-templates
CMD python3 netpalm.py
