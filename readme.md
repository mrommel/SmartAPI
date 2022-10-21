# SmartAPI

![](https://github.com/mrommel/SmartAPI/workflows/Pylint/badge.svg)
![](https://github.com/mrommel/SmartAPI/workflows/Pytest/badge.svg)

## start postgres docker

`docker-compose up -d`

verify that database is up to date

`alembic upgrade head`

## start uvicorn server 

`uvicorn app.main:app --host localhost --port 8000 --reload`

## stop postgres docker

`docker-compose down`

# Links

* https://codevoweb.com/restful-api-with-python-fastapi-access-and-refresh-tokens/
* https://levelup.gitconnected.com/building-a-website-starter-with-fastapi-92d077092864
* https://www.w3schools.com/howto/howto_css_login_form.asp
* https://getbootstrap.com/docs/4.0/components/buttons/