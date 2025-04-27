# Back-end и Front-end сервисы для выдачи результатов предсказания пользователю

Данный серсив является основным для взаимодйствия между пользователей и всем проектом. Streamlit получает запрос, передаёт его в FastAPI, где модель получает прошлые данные из БД, скачивает модель с S3, и делает предсказание.


## Структура сервиса

```

.
├── docker-compose.yml
├── .env
├── fastapi_app
│   ├── core
│   │   └── config.py
│   ├── db
│   │   └── database.py
│   ├── Dockerfile
│   ├── main.py
│   ├── models
│   │   └── predict_request.py
│   ├── requirements.txt
│   ├── routers
│   │   ├── healthcheck_router.py
│   │   └── predict_router.py
│   ├── services
│   │   ├── prediction_service.py
│   │   └── s3_service.py
│   └── utils
│       └── dataset_trunsform.py
├── README.md
└── streamlit_app
    ├── app.py
    ├── Dockerfile
    └── requirements.txt

```

Описание структур: 
- docker-compose.yml, .env, Dockerfile - файлы для сборки сервиса. 
- .env - файл с секретами. Логины и пароли для входа/коннекта к PostgreSQL, pgAdmin, MinIO
- fastapi_app/ - папка с файлами работы сервсиа FastAPI
- streamlit_app/ -папка с файлами работы Streamlit


## Задача сервиса web_services

Основная задача, выполняемая данны серсивом - получение запросов от пользователя и ему предсказания по финансовым активам
