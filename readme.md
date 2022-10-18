# SmartAPI

![](https://github.com/mrommel/SmartAPI/workflows/Pylint/badge.svg)
![](https://github.com/mrommel/SmartAPI/workflows/Pytest/badge.svg)


## start postgres docker

`docker-compose up -d`

## start uvicorn server 

`uvicorn app.main:app --host localhost --port 8000 --reload`

## stop postgres docker

`docker-compose down`

# Links

* https://codevoweb.com/restful-api-with-python-fastapi-access-and-refresh-tokens/