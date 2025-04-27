#!/bin/bash

# Скрипт запуска всех частей проекта

echo "Запускаем data_store..."
cd data_store || exit 1
docker compose -f docker-compose.yml up -d
cd ..

echo "Запускаем web_services..."
cd web_services || exit 1
docker compose up -d --build
cd ..

echo "Запускаем Airflow_services..."
cd Airflow_services || exit 1
docker compose -f docker-compose.yml up -d
cd ..

echo "Запускаем jupyter_app..."
cd jupyter_app || exit 1
docker compose -f docker-compose.yml up -d
cd ..

echo "Проверка запущенных сервисов"
docker ps -a 

echo "Все сервисы запущены!"
