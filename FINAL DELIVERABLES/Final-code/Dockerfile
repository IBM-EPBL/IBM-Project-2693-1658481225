  FROM python:3.10
  ENV APIKEY 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
  ENV FROM soumikrakshit50@gmail.com
  LABEL maintainer="Soumik Rakshit, soumikrakshit50@gmail.com"
  RUN apt-get update
  RUN mkdir /app
  WORKDIR /app
  COPY . /app
  RUN pip3 install -r requirements.txt
  EXPOSE 5000
  ENTRYPOINT [ "python" ]
  CMD [ "app.py" ]