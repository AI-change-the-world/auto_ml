# auto_ml

![image](./readme/image.png)

### requirements

* python3.10+

### notes

* On the backend, I picked [ObjectBox](https://github.com/objectbox/objectbox-python) for my database. It's crazy fast, super light - weight, and a piece of cake to use.

> I know PostgreSQL (PG) might be better than ObjectBox, but I haven't written much Python SQL code. And I've got no idea which ORM in Python is the best.

* On the frontend, I'm using [isar](https://github.com/isar/isar) for the database, and a lot of data is stored by the frontend, which means doesn't support web currently.