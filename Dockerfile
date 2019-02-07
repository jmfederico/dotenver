FROM python:3.7-alpine AS build
RUN apk add --no-cache curl git
RUN curl -sSL https://raw.githubusercontent.com/sdispater/poetry/master/get-poetry.py | python
WORKDIR /var/lib/dotenver/
COPY . .
RUN /root/.poetry/bin/poetry build


FROM python:3.7-alpine
COPY --from=build /var/lib/dotenver/dist/dotenver-*-py3-none-any.whl /root/dotenver/
RUN pip install /root/dotenver/*
WORKDIR /var/lib/dotenver/
CMD ["dotenver", "-r"]
