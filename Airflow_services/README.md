# Airflow_services сервис для парсинга данных и обучения моделей

Данный серсив является основным цикличного парсинга данных и обучение моделей для предсказанеия стоимости активов

---

## Структура сервиса

```
.
├── dags
│   ├── data_parser
│   │   ├── base_metals_parser
│   │   │   ├── base_metal_parser.py
│   │   │   └── base_metal_parser.yaml
│   │   ├── crypto_parser
│   │   │   ├── crypto_parser.py
│   │   │   └── crypto_parser.yaml
│   │   ├── metal_share_parser
│   │   │   ├── metal_share_parser.py
│   │   │   └── metal_share_parser.yaml
│   │   ├── oil_futures_parser
│   │   │   ├── oil_futures_parser.py
│   │   │   └── oil_futures_parser.yaml
│   │   ├── oil_share_parser
│   │   │   ├── oil_share_parser.py
│   │   │   └── oil_share_parser.yaml
│   ├── mlflow_dags
│   │   ├── base_metals_models
│   │   │   ├── base_metals_config.json
│   │   │   └── base_metals_dag.py
│   │   ├── crypto_models
│   │   │   ├── crypto_config.json
│   │   │   └── crypto_models_dag.py
│   │   ├── dataset_transform_func
│   │   │   └── preprocessing.py
│   │   ├── metal_share_models
│   │   │   ├── metal_share_config.json
│   │   │   └── metal_share_models_dag.py
│   │   ├── oil_futures_models
│   │   │   ├── oil_futures_config.json
│   │   │   └── oil_futures_models_dag.py
│   │   └── oil_share_models
│   │       ├── oil_share_config.json
│   │       └── oil_share_dag.py
│   └── test_services
│       ├── postgres_conn_test.py
│       ├── s3_test_dag.py
│       └── test_run_learn.py
├── docker-compose.yml
├── Dockerfile
├── .env
├── nginx
│   └── nginx.conf
├── plugins
├── README.md
└── requirements.txt

```

Описание структур: 
- docker-compose.yml, .env, Dockerfile - файлы для сборки сервиса. 
- .env - файл с секретами. Логины и пароли для входа/коннекта к PostgreSQL и бакету s3 в MinIO.
- dags/data_parser/ - папка с файлами для парсинга данных по категориям
- ```***.yaml``` - файлы с указанием группы актива и немингом актива для парсинга
- dags/mlflow_dags/ - папка с файлами для обучения моделей.
- ```***.json``` - конфигурационные файлы с информацией по каждому активу и параметрами для обучения моделей

---

## Задача сервиса Airflow_services

Основная задача, выполняемая данны серсивом - циклическое обучения моделей, и парсинг данных, с возможность добавление новых активов. Сейчас для обучения используются генератор дагов, позволяющий добавлять новые модели в json файл. Файлы для парсинга данных сделаны универсально, и парсят данные по всему направлянию актива.
