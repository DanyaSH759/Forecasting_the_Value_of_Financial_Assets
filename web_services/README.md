# Back-end и Front-end сервисы для выдачи результатов предсказания пользователю

Данный серсив является основным для взаимодйствия между пользователей и всем проектом. Streamlit получает запрос, передаёт его в FastAPI, где модель получает прошлые данные из БД, скачивает модель с S3, и делает предсказание.


## Структура сервиса

```

.
├── docker-compose.yml
├── fastapi_app
│   ├── core
│   │   └── config.py
│   ├── db
│   │   └── database.py
│   ├── Dockerfile
│   ├── main.py
│   ├── models
│   │   ├── auth_request.py
│   │   └── predict_request.py
│   ├── requirements.txt
│   ├── routers
│   │   ├── auth_login_router.py
│   │   ├── auth_register_router.py
│   │   ├── custom_predict_router.py
│   │   ├── healthcheck_router.py
│   │   └── predict_router.py
│   ├── services
│   │   ├── auth_services.py
│   │   ├── custom_predict_services.py
│   │   ├── lstm_model_definitions.py
│   │   ├── prediction_service.py
│   │   └── s3_service.py
│   └── utils
│       ├── dataset_trunsform.py
│       └── lstm_predict.py
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
